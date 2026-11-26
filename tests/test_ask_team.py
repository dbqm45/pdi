"""DI Team T4 „Ask team” w konsoli z logowaniem przez suitę (docs/plan-t4-ask-team.md)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from pdi.inbox import Inbox
from pdi.registry import Registry
from tests.test_console_suite import Console, FakeIssuer, _person, _write_inbox_gate


@pytest.fixture
def registry(tmp_path: Path) -> Registry:
    r = Registry(tmp_path / "registry")
    r.root.mkdir(parents=True, exist_ok=True)
    return r


@pytest.fixture
def app(registry: Registry, monkeypatch: pytest.MonkeyPatch) -> Any:
    console = Console(registry, FakeIssuer(), monkeypatch)
    yield console
    console.close()


def sign_in(app: Console, sub: str, name: str, roles: list[str]) -> str:
    app.fake.claims = _person(roles, sub=sub, name=name)
    back, _, session = app.sign_in()
    assert back == 302 and session
    return session


def people(app: Console) -> dict[str, str]:
    """Trzy osoby, które logowały się już do konsoli: decydentka, admin i ktoś z rolą viewer."""
    return {
        "adm": sign_in(app, "s-adm", "Adm Test", ["admin"]),
        "viewer": sign_in(app, "s-3", "Trzecia Osoba", ["viewer"]),
        "ola": sign_in(app, "s-ola", "Ola Test", ["editor"]),
    }


def ask(app: Console, session: str, asked: list[str], hours: str = "24") -> tuple[int, str]:
    form = {"hours": hours, **{f"ask_{sub}": "1" for sub in asked}}
    status, _, body, _ = app.request("POST", "/inbox/evt-1/ask", cookie=session, form=form)
    return status, body


def answer(app: Console, session: str, option: str, reason: str) -> int:
    status, _, _, _ = app.request(
        "POST", "/inbox/evt-1/answer", cookie=session, form={"option": option, "reason": reason}
    )
    return status


def inbox(app: Console, session: str) -> str:
    status, _, page, _ = app.request("GET", "/inbox", cookie=session)
    assert status == 200
    return page


def test_at01_the_decider_asks_people_who_signed_in_here_not_themselves(app: Console, registry: Registry) -> None:
    _write_inbox_gate(registry)
    s = people(app)
    page = inbox(app, s["ola"])
    assert "Ask team" in page
    assert 'name="ask_s-adm"' in page and 'name="ask_s-3"' in page
    assert 'name="ask_s-ola"' not in page, "not yourself"
    assert ask(app, s["ola"], ["s-adm", "s-3"])[0] == 303
    page = inbox(app, s["ola"])
    assert re.search(r"With team · 0/2 · closes", page)
    assert ask(app, s["ola"], ["s-adm"])[0] == 409, "one open question per item"
    assert ask(app, s["adm"], [])[0] == 409


def test_at02_a_viewer_who_is_asked_answers_and_nobody_sees_answers_before_the_close(
    app: Console, registry: Registry
) -> None:
    _write_inbox_gate(registry)
    s = people(app)
    ask(app, s["ola"], ["s-adm", "s-3"])
    assert "Asked of you" in inbox(app, s["viewer"])
    assert answer(app, s["viewer"], "changes_requested", "Brakuje testu kontraktu.") == 303
    for who in ("ola", "adm"):
        page = inbox(app, s[who])
        assert "Brakuje testu kontraktu" not in page, f"{who} must not see the answer yet"
        assert "With team · 1/2" in page
    assert "Brakuje testu kontraktu" in inbox(app, s["viewer"]), "their own answer, to change it"
    assert answer(app, s["ola"], "approved", "Ja też.") == 403, "the decider is not asked"


def test_at03_agreement_gives_a_one_click_decision_with_consulted(app: Console, registry: Registry) -> None:
    item = _write_inbox_gate(registry)
    s = people(app)
    ask(app, s["ola"], ["s-adm", "s-3"])
    answer(app, s["adm"], "approved", "Plan pokrywa ryzyka.")
    answer(app, s["viewer"], "approved", "Testy są.")
    page = inbox(app, s["ola"])
    assert "Team agrees: approved" in page
    assert "Plan pokrywa ryzyka." in page and "Testy są." in page
    form = {
        "t": "",
        "loaded_at": item["received_at"],
        "statement": "Zatwierdzam B2.",
        "why": "Zespół zgodny.",
        "outcome": "approved",
    }
    status, _, _, _ = app.request("POST", "/inbox/evt-1/decide", cookie=s["ola"], form=form)
    assert status == 200
    decided = Inbox(registry).items(status="decided")
    decision = registry.get(decided[0]["decision"])
    assert decision["decided_by_id"] == "s-ola"
    assert decision["consulted"] == [
        {"person_id": "s-adm", "name": "Adm Test", "option": "approved", "reason": "Plan pokrywa ryzyka."},
        {"person_id": "s-3", "name": "Trzecia Osoba", "option": "approved", "reason": "Testy są."},
    ]


def test_at04_a_split_is_marked_to_discuss_and_deciding_early_records_who_did_not_answer(
    app: Console, registry: Registry
) -> None:
    item = _write_inbox_gate(registry)
    s = people(app)
    ask(app, s["ola"], ["s-adm", "s-3"])
    answer(app, s["adm"], "talk_live", "To trzeba omówić na żywo.")
    status, _, _, _ = app.request("POST", "/inbox/evt-1/close-ask", cookie=s["ola"], form={})
    assert status == 303
    assert "To discuss" in inbox(app, s["ola"])
    form = {
        "t": "",
        "loaded_at": item["received_at"],
        "statement": "Poprawki.",
        "why": "Po rozmowie.",
        "outcome": "changes_requested",
    }
    assert app.request("POST", "/inbox/evt-1/decide", cookie=s["ola"], form=form)[0] == 200
    decision = registry.get(Inbox(registry).items(status="decided")[0]["decision"])
    assert decision["consulted"][1] == {"person_id": "s-3", "name": "Trzecia Osoba", "option": None, "reason": None}


def test_at05_closing_early_is_only_for_the_decider(app: Console, registry: Registry) -> None:
    _write_inbox_gate(registry)
    s = people(app)
    ask(app, s["ola"], ["s-adm"])
    assert app.request("POST", "/inbox/evt-1/close-ask", cookie=s["adm"], form={})[0] == 403


def test_at06_agreement_fills_in_the_decision_draft_and_now_shows_the_team(app: Console, registry: Registry) -> None:
    _write_inbox_gate(registry)
    s = people(app)
    ask(app, s["ola"], ["s-adm"])
    status, _, now_page, _ = app.request("GET", "/now", cookie=s["ola"])
    assert status == 200 and "With team · 0/1" in now_page
    answer(app, s["adm"], "approved", "Plan pokrywa ryzyka.")
    page = inbox(app, s["ola"])
    assert re.search(r'<textarea name="statement"[^>]*>[^<]*approved \(the team agrees\)', page)
    assert re.search(r'<textarea name="why"[^>]*>[^<]*Adm Test: Plan pokrywa ryzyka\.', page)
    status, _, now_page, _ = app.request("GET", "/now", cookie=s["ola"])
    assert "Team agrees: approved" in now_page


def test_at07_the_agent_adds_effects_through_mcp_and_list_inbox_hides_answers_until_the_close(
    app: Console, registry: Registry
) -> None:
    import asyncio

    from pdi.mcp_server import build_server

    _write_inbox_gate(registry)
    s = people(app)
    ask(app, s["ola"], ["s-adm", "s-3"])
    answer(app, s["adm"], "approved", "Plan pokrywa ryzyka.")
    server = build_server(lambda: registry)

    async def run() -> tuple[Any, Any]:
        added = await server.call_tool(
            "add_option_effects",
            {"item_id": "evt-1", "option": "changes_requested", "effects": "Jedno cięcie więcej, ok. 2 USD."},
        )
        listed = await server.call_tool("list_inbox", {})
        return added, listed

    added, listed = asyncio.run(run())
    assert added.is_error is False, added.content
    item = listed.structured_content["items"][0]
    assert item["consultation"]["answered"] == 1
    assert "answers" not in item["consultation"], "the agent does not see answers before the close either"
    assert "Jedno cięcie więcej" in inbox(app, s["viewer"])
