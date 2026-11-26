"""DI Team T7 „Escalate” i OM2: decyzję o sprawie przejmuje adresat eskalacji (docs/plan-t7-escalate.md)."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from pdi import consult, escalate, team_notify
from pdi.inbox import Inbox, ItemClosed
from pdi.registry import Registry
from tests.test_ask_team import ask, sign_in
from tests.test_console_suite import Console, FakeIssuer, _write_inbox_gate
from tests.test_team_notify import CFG, FakeChannels

T0 = datetime(2026, 11, 23, 9, 0, tzinfo=UTC)
OLA = consult.Person("s-ola", "Ola Test")
ADM = consult.Person("s-adm", "Adm Test")
ED = consult.Person("s-ed", "Edi Tor")
VIEW = consult.Person("s-3", "Trzecia Osoba")


@pytest.fixture
def registry(tmp_path: Path) -> Registry:
    r = Registry(tmp_path / "registry")
    r.root.mkdir(parents=True, exist_ok=True)
    return r


@pytest.fixture
def people(registry: Registry) -> consult.People:
    p = consult.People(registry.root, now=lambda: T0)
    p.seen(OLA, decides=True)
    p.seen(ADM, decides=True, admin=True)
    p.seen(ED, decides=True)
    p.seen(VIEW, decides=False)
    return p


def gate(item_id: str = "evt-1", gate_name: str = "B2", **extra: Any) -> dict[str, Any]:
    return {"id": item_id, "kind": "gate", "status": "open", "change": "CHG-1", "gate": gate_name,
            "summary": "Prośba o bramkę", "received_at": "2026-11-20T09:00:00Z", **extra}  # fmt: skip


def test_es01_an_escalation_passes_the_decision_on_one_item_with_the_rules_of_the_plan(
    registry: Registry, people: consult.People
) -> None:
    store = escalate.Escalations(registry.root, now=lambda: T0)
    with pytest.raises(escalate.EscalationError, match="someone else"):
        store.escalate(gate(), by=OLA, to=OLA, reason="Sam do siebie.", people=people)
    with pytest.raises(escalate.EscalationError, match="editor or admin"):
        store.escalate(gate(), by=OLA, to=VIEW, reason="Nie decyduje.", people=people)
    with pytest.raises(escalate.EscalationError, match="reason"):
        store.escalate(gate(), by=OLA, to=ADM, reason="  ", people=people)
    with pytest.raises(escalate.EscalationError, match="admin"):
        store.escalate(gate(gate_name="B5"), by=OLA, to=ED, reason="Wydanie na PROD.", people=people)
    e = store.escalate(gate(), by=OLA, to=ED, reason="Dotyka płatności.", question="Czy to bezpieczne?", people=people)
    assert e["to"] == {"sub": "s-ed", "name": "Edi Tor"}
    assert store.holder("evt-1") == "s-ed"
    with pytest.raises(escalate.EscalationError, match="already escalated"):
        store.escalate(gate(), by=OLA, to=ADM, reason="Jeszcze raz.", people=people)
    assert store.escalated_to("s-ed") == ["evt-1"]
    assert store.field("evt-1") == {"by_id": "s-ola", "by_name": "Ola Test", "to_id": "s-ed", "to_name": "Edi Tor",
                                    "reason": "Dotyka płatności.", "at": "2026-11-23T09:00:00Z"}  # fmt: skip
    with pytest.raises(escalate.EscalationError, match="only the person"):
        store.give_back("evt-1", OLA, note="Biorę z powrotem.")
    store.give_back("evt-1", ED, note="To decyzja produktowa, nie moja.")
    assert store.holder("evt-1") is None
    field = store.field("evt-1")
    assert field is not None
    assert field["returned_at"] == "2026-11-23T09:00:00Z"
    assert field["return_note"] == "To decyzja produktowa, nie moja."
    e2 = store.escalate(gate(gate_name="B5"), by=OLA, to=ADM, reason="Wydanie: admin.", people=people)
    assert e2["to"]["sub"] == "s-adm", "after a give-back it can be escalated again; B5 only to an admin"


def test_es02_the_inbox_refuses_anyone_but_the_addressee_and_the_decision_carries_the_escalation(
    registry: Registry, people: consult.People
) -> None:
    item = _write_inbox_gate(registry)
    box = Inbox(registry)
    store = escalate.Escalations(registry.root, now=registry.now)
    store.escalate(item, by=OLA, to=ADM, reason="Za duże ryzyko dla zespołu.", people=people)
    draft = {"statement": "Poprawki przed B2.", "why": "Brak testów.", "decided_by": "Ola Test",
             "decided_by_id": "s-ola", "decided_at": "2026-11-23", "drafted_by": "human", "kind": "other",
             "source": {"kind": "console", "url": "http://127.0.0.1/inbox", "excerpt": "x"}}  # fmt: skip
    with pytest.raises(ItemClosed, match="escalated to Adm Test"):
        box.decide("evt-1", dict(draft), outcome="changes_requested")
    without_id = {k: v for k, v in draft.items() if k != "decided_by_id"}
    with pytest.raises(ItemClosed, match="escalated"):
        box.decide("evt-1", without_id, outcome="changes_requested")
    result = box.decide(
        "evt-1", {**draft, "decided_by": "Adm Test", "decided_by_id": "s-adm"}, outcome="changes_requested"
    )
    decision = registry.get(result["decision"]["id"])
    assert decision["escalation"]["to_id"] == "s-adm"
    assert decision["escalation"]["by_name"] == "Ola Test"
    assert decision["contract_version"] == "0.27.0"


# --- konsola ---


@pytest.fixture
def app(registry: Registry, monkeypatch: pytest.MonkeyPatch) -> Any:
    console = Console(registry, FakeIssuer(), monkeypatch)
    yield console
    console.close()


def suite_people(app: Console) -> dict[str, str]:
    return {
        "adm": sign_in(app, "s-adm", "Adm Test", ["admin"]),
        "viewer": sign_in(app, "s-3", "Trzecia Osoba", ["viewer"]),
        "ola": sign_in(app, "s-ola", "Ola Test", ["editor"]),
    }


def decide(app: Console, session: str, item: dict[str, Any]) -> int:
    form = {"loaded_at": item["received_at"], "statement": "Poprawki przed B2.", "why": "Za mało testów.",
            "outcome": "changes_requested"}  # fmt: skip
    return app.request("POST", "/inbox/evt-1/decide", cookie=session, form=form)[0]


def test_es03_escalating_in_the_console_closes_the_team_question_and_only_the_addressee_decides(
    app: Console, registry: Registry
) -> None:
    item = _write_inbox_gate(registry)
    s = suite_people(app)
    _, _, page, _ = app.request("GET", "/inbox", cookie=s["ola"])
    assert "Escalate" in page
    assert 'name="to" value="s-adm"' in page or 'value="s-adm"' in page
    assert 'value="s-3"' not in page.split("Escalate", 1)[1].split("</form>", 1)[0], "a viewer cannot be the addressee"
    assert ask(app, s["ola"], ["s-adm", "s-3"])[0] == 303
    form = {"to": "s-adm", "reason": "Dotyka płatności, zespół nie powinien sam.", "question": "Czy wydajemy?"}
    assert app.request("POST", "/inbox/evt-1/escalate", cookie=s["viewer"], form=form)[0] == 403
    assert app.request("POST", "/inbox/evt-1/escalate", cookie=s["ola"], form=form)[0] == 303
    store = consult.Consultations(registry.root, now=registry.now)
    assert store.view("evt-1", "")["status"] == "closed", "the open question closes with what was gathered"  # type: ignore[index]
    _, _, page, _ = app.request("GET", "/inbox", cookie=s["ola"])
    assert "Escalated to Adm Test" in page
    assert decide(app, s["ola"], item) == 403
    _, _, page, _ = app.request("GET", "/inbox", cookie=s["adm"])
    assert "Ola Test escalated this to you" in page and "Czy wydajemy?" in page
    assert decide(app, s["adm"], item) == 200
    decision = registry.get(Inbox(registry).items(status="decided")[0]["decision"])
    assert decision["decided_by_id"] == "s-adm"
    assert decision["escalation"]["reason"] == "Dotyka płatności, zespół nie powinien sam."


def test_es04_the_addressee_gives_it_back_and_the_escalator_decides_again(app: Console, registry: Registry) -> None:
    item = _write_inbox_gate(registry)
    s = suite_people(app)
    app.request("POST", "/inbox/evt-1/escalate", cookie=s["ola"], form={"to": "s-adm", "reason": "Pytanie o zakres."})
    assert app.request("POST", "/inbox/evt-1/give-back", cookie=s["ola"], form={"note": "x"})[0] == 403
    assert app.request("POST", "/inbox/evt-1/give-back", cookie=s["adm"], form={"note": "Decyzja zespołu."})[0] == 303
    _, _, page, _ = app.request("GET", "/inbox", cookie=s["ola"])
    assert "Adm Test gave it back: Decyzja zespołu." in page
    assert decide(app, s["ola"], item) == 200
    decision = registry.get(Inbox(registry).items(status="decided")[0]["decision"])
    assert decision["escalation"]["return_note"] == "Decyzja zespołu."
    assert decision["decided_by_id"] == "s-ola"


def test_es05_the_addressee_gets_a_slack_message_and_sees_it_in_their_digest(
    registry: Registry, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_inbox_gate(registry)
    fake = FakeChannels()
    monkeypatch.setattr(Inbox, "channels", property(lambda self: CFG))
    monkeypatch.setattr(team_notify, "_post_json", fake)
    app = Console(registry, FakeIssuer(), monkeypatch)
    try:
        s = suite_people(app)
        app.request("POST", "/inbox/evt-1/escalate", cookie=s["ola"], form={"to": "s-adm", "reason": "Za duże ryzyko."})
    finally:
        app.close()
    url, _, msg = fake.sent[-1]
    assert url.endswith("/pdi/escalated")
    expected = {"type": "team.escalated", "item": "evt-1", "by": "Ola Test", "to": "s-adm", "reason": "Za duże ryzyko."}
    assert {k: msg[k] for k in expected} == expected
    assert msg["due"] and msg["url"] == "http://127.0.0.1:8788/inbox"
    _, personal, _ = team_notify.collect(registry, CFG, now=registry.now())
    mine = next(d for d in personal if d["to"] == {"person": "s-adm"})
    assert mine["escalated_to_you"][0]["item"] == "evt-1"
    assert mine["escalated_to_you"][0]["by"] == "Ola Test"


def test_es06_the_agent_sees_the_escalation_and_cannot_decide_an_escalated_item(registry: Registry) -> None:
    from mcp.server.mcpserver.exceptions import ToolError

    from pdi.mcp_server import build_server

    item = _write_inbox_gate(registry)
    people = consult.People(registry.root, now=registry.now)
    people.seen(ADM, decides=True, admin=True)
    escalate.Escalations(registry.root, now=registry.now).escalate(
        item, by=OLA, to=ADM, reason="Ryzyko.", people=people
    )
    server = build_server(lambda: registry)
    listed = asyncio.run(server.call_tool("list_inbox", {}))
    assert listed.structured_content["items"][0]["escalation"]["to_name"] == "Adm Test"
    args = {"item_id": "evt-1", "statement": "Tak.", "why": "Bo tak.", "drafted_by": "ai", "outcome": "approved",
            "source": {"kind": "manual", "url": "http://x/inbox", "excerpt": "x"}}  # fmt: skip
    with pytest.raises(ToolError, match="escalated"):
        asyncio.run(server.call_tool("decide_inbox_item", args))
    assert json.loads((registry.root / "people.json").read_text(encoding="utf-8"))["s-adm"]["admin"] is True
