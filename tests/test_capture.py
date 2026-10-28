"""A5: szkice decyzji z wątków Slacka i transkrypcji spotkań w skrzynce (plan-a5-decyzje-z-rozmow)."""

from typing import Any

import pytest

from pdi import capture
from pdi.inbox import Inbox, ItemClosed
from pdi.registry import InvalidDecision, Registry

THREAD = """\
[09:12] Anna: Proponuję, żeby próg darmowej dostawy został na 199 zł do końca kwartału.
[09:14] Piotr: OK, zgoda. Przewoźnik X podnosi cenę paczki od listopada, więc obniżka byłaby na minus.
[09:15] Anna: Ustalone: próg zostaje na 199 zł do końca kwartału.
[09:20] Piotr: A banner na stronie głównej zrobimy chyba w przyszłym tygodniu?
"""
SOURCE = {"kind": "slack", "url": "https://acme.slack.com/archives/C1/p1730", "title": "#sklep-ceny"}


def candidate(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "statement": "Próg darmowej dostawy zostaje na 199 zł do końca kwartału.",
        "why": "Przewoźnik X podnosi cenę paczki od listopada, więc obniżka byłaby na minus.",
        "quotes": [
            "Ustalone: próg zostaje na 199 zł do końca kwartału.",
            "Przewoźnik X podnosi cenę paczki od listopada",
        ],
        "kind": "product",
        "decided_by": "Anna, Piotr",
    }
    base.update(overrides)
    return base


@pytest.fixture
def inbox(registry: Registry) -> Inbox:
    return Inbox(registry)


# --- cytaty ---


def test_quote_found_despite_whitespace_and_quote_marks() -> None:
    text = "Anna:  „Ustalone”:\n próg   zostaje na 199 zł."

    assert capture.quote_problem('"Ustalone": próg zostaje na 199 zł.', text) is None


@pytest.mark.parametrize(
    ("quote", "reason"),
    [
        pytest.param("próg", "za krótki", id="krotki"),
        pytest.param("Ustalone: próg zostaje na 149 zł do końca kwartału.", "nie ma w tekście", id="zmyslony"),
    ],
)
def test_bad_quote_names_the_reason(quote: str, reason: str) -> None:
    problem = capture.quote_problem(quote, THREAD)

    assert problem is not None and reason in problem


# --- propozycje w skrzynce ---


def test_candidates_become_capture_items_without_the_text(inbox: Inbox, registry: Registry) -> None:
    result = inbox.propose_captures(SOURCE, THREAD, [candidate()])

    assert result["refused"] == []
    item = result["items"][0]
    assert item["kind"] == "capture" and item["status"] == "open"
    assert item["id"].startswith("capture-20261023-")
    assert item["source"] == SOURCE
    assert item["draft"]["quotes"] == candidate()["quotes"]
    assert "Próg darmowej dostawy" in item["summary"]
    assert inbox.get(item["id"])["kind"] == "capture"
    stored = (registry.root / "inbox" / f"{item['id']}.yaml").read_text(encoding="utf-8")
    assert "banner" not in stored, "pdi nie zapisuje tekstu rozmowy, tylko cytaty"
    assert registry.decisions() == []


def test_candidate_with_a_made_up_quote_is_refused(inbox: Inbox) -> None:
    bad = candidate(statement="Banner w przyszłym tygodniu.", quotes=["Banner zrobimy w poniedziałek rano."])

    result = inbox.propose_captures(SOURCE, THREAD, [candidate(), bad])

    assert len(result["items"]) == 1
    assert result["refused"][0]["statement"] == "Banner w przyszłym tygodniu."
    assert "nie ma w tekście" in result["refused"][0]["reason"]


def test_candidate_without_quotes_is_refused(inbox: Inbox) -> None:
    result = inbox.propose_captures(SOURCE, THREAD, [candidate(quotes=[])])

    assert result["items"] == [] and "cytat" in result["refused"][0]["reason"]


def test_same_candidate_twice_is_not_a_new_item(inbox: Inbox) -> None:
    first = inbox.propose_captures(SOURCE, THREAD, [candidate()])
    again = inbox.propose_captures(SOURCE, THREAD, [candidate()])

    assert again["items"] == [] and again["duplicates"] == [first["items"][0]["id"]]
    assert len(inbox.items()) == 1


@pytest.mark.parametrize(
    ("source", "text", "match"),
    [
        pytest.param({**SOURCE, "kind": "email"}, THREAD, "slack", id="zly-rodzaj"),
        pytest.param({"kind": "meeting"}, THREAD, "url", id="bez-linku"),
        pytest.param(SOURCE, "", "tekst", id="bez-tekstu"),
        pytest.param(SOURCE, "x" * (capture.MAX_TEXT + 1), "200 000", id="za-dlugi"),
    ],
)
def test_source_and_text_are_checked(inbox: Inbox, source: dict[str, Any], text: str, match: str) -> None:
    with pytest.raises(InvalidDecision, match=match):
        inbox.propose_captures(source, text, [candidate()])


# --- decyzja człowieka ---


def proposed(inbox: Inbox, **overrides: Any) -> dict[str, Any]:
    item: dict[str, Any] = inbox.propose_captures(SOURCE, THREAD, [candidate(**overrides)])["items"][0]
    return item


def approve(inbox: Inbox, item: dict[str, Any], make_draft: Any, **fields: Any) -> dict[str, Any]:
    draft = make_draft(statement=item["draft"]["statement"], why=item["draft"]["why"], **fields)
    result: dict[str, Any] = inbox.decide(item["id"], draft, outcome="approved")
    return result


def test_approved_draft_is_recorded_with_quotes_and_link(inbox: Inbox, make_draft: Any) -> None:
    item = proposed(inbox, change="CHG-12")

    decision = approve(inbox, item, make_draft)["decision"]

    assert decision["kind"] == "product"
    assert decision["drafted_by"] == "ai" and decision["draft_edited"] is False
    assert decision["source"]["kind"] == "slack"
    assert decision["source"]["url"] == SOURCE["url"]
    assert "Ustalone: próg zostaje" in decision["source"]["excerpt"]
    assert [e["text"] for e in decision["evidence"]] == candidate()["quotes"]
    assert {e["epistemic_status"] for e in decision["evidence"]} == {"observation"}
    assert decision["links"] == {"chg": "CHG-12"}
    assert {"capture", "capture:slack"} <= set(decision["tags"])
    assert inbox.get(item["id"])["status"] == "decided"


def test_edited_statement_counts_as_edited_draft(inbox: Inbox, make_draft: Any) -> None:
    item = proposed(inbox)

    decision = inbox.decide(
        item["id"],
        make_draft(statement="Próg zostaje na 199 zł do 31 grudnia.", why=item["draft"]["why"]),
        outcome="approved",
    )["decision"]

    assert decision["draft_edited"] is True


def test_explicit_draft_edited_wins(inbox: Inbox, make_draft: Any) -> None:
    item = proposed(inbox)

    decision = approve(inbox, item, make_draft, draft_edited=True)["decision"]

    assert decision["draft_edited"] is True


def test_rejected_draft_closes_the_item_without_a_decision(inbox: Inbox, registry: Registry, make_draft: Any) -> None:
    item = proposed(inbox)

    result = inbox.decide(
        item["id"], make_draft(why="To była tylko propozycja, nikt nie zdecydował."), outcome="rejected"
    )

    assert result["decision"] is None
    closed = inbox.get(item["id"])
    assert (closed["status"], closed["outcome"]) == ("decided", "rejected")
    assert closed["rejection_reason"] == "To była tylko propozycja, nikt nie zdecydował."
    assert registry.decisions() == []


def test_capture_needs_approved_or_rejected_and_closes_once(inbox: Inbox, make_draft: Any) -> None:
    item = proposed(inbox)
    for outcome in (None, "met", "changes_requested"):
        with pytest.raises(InvalidDecision, match="approved"):
            inbox.decide(item["id"], make_draft(), outcome=outcome)

    approve(inbox, item, make_draft)

    with pytest.raises(ItemClosed):
        approve(inbox, item, make_draft)


def test_meeting_transcript_records_meeting_source(inbox: Inbox, make_draft: Any) -> None:
    source = {"kind": "meeting", "url": "https://zoom.us/rec/share/abc", "title": "Planowanie Q4"}
    item = inbox.propose_captures(source, THREAD, [candidate()])["items"][0]

    decision = approve(inbox, item, make_draft)["decision"]

    assert decision["source"]["kind"] == "meeting"
    assert "capture:meeting" in decision["tags"]


def test_capture_stats(inbox: Inbox, make_draft: Any, registry: Registry) -> None:
    from pdi.stats import summarize

    a = proposed(inbox)
    b = proposed(inbox, statement="Druga decyzja: próg 199 zł obowiązuje do końca kwartału.")
    c = proposed(inbox, statement="Trzecia: próg 199 zł.")
    approve(inbox, a, make_draft)
    inbox.decide(b["id"], make_draft(statement="Poprawiona.", why=b["draft"]["why"]), outcome="approved")
    inbox.decide(c["id"], make_draft(why="Nie decyzja."), outcome="rejected")

    assert summarize(registry)["captures"] == {"proposed": 3, "open": 0, "approved": 2, "edited": 1, "rejected": 1}
