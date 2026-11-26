"""DI Team T5 „Discuss with team”: agenda spraw do rozmowy (docs/plan-t5-discuss-with-team.md)."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from pdi import agenda, consult
from pdi.inbox import Inbox
from pdi.registry import Registry
from tests.test_ask_team import answer, ask, people
from tests.test_console_suite import Console, FakeIssuer

T0 = datetime(2026, 11, 26, 9, 0, tzinfo=UTC)
ADM = consult.Person("s-adm", "Adm Test")
THIRD = consult.Person("s-3", "Trzecia Osoba")
OLA = consult.Person("s-ola", "Ola Test")


def item(item_id: str, *, received: str = "2026-11-25T09:00:00Z", **extra: Any) -> dict[str, Any]:
    summary = f"Sprawa {item_id}"
    return {"id": item_id, "kind": "gate", "status": "open", "change": "CHG-1", "gate": "B2", "summary": summary,
            "received_at": received, **extra}  # fmt: skip


def discuss(store: consult.Consultations, item_id: str, *, talk: int = 1) -> None:
    store.ask(item_id, decider=OLA, asked=[ADM, THIRD], options=["approved", "changes_requested", "rejected"], hours=24)
    store.answer(item_id, ADM, option="talk_live" if talk else "approved", reason="Trzeba to omówić.")
    store.answer(item_id, THIRD, option="talk_live" if talk > 1 else "rejected", reason="Za duże ryzyko.")


@pytest.fixture
def store(tmp_path: Path) -> consult.Consultations:
    return consult.Consultations(tmp_path, now=lambda: T0)


def test_ag01_only_open_items_whose_team_question_ended_in_discuss(store: consult.Consultations) -> None:
    items = [item("a"), item("b"), item("c", status="decided")]
    discuss(store, "a")
    discuss(store, "c")
    store.ask("b", decider=OLA, asked=[ADM], options=["approved"], hours=24)
    store.answer("b", ADM, option="approved", reason="Zgoda.")  # zgodność — nie do rozmowy
    assert [e["item_id"] for e in agenda.build(items, store, order=[], now=T0)] == ["a"]


def test_ag02_ordered_by_what_the_items_block_with_the_reason_in_words(store: consult.Consultations) -> None:
    items = [
        item("old", received="2026-11-20T09:00:00Z"),
        item("talk", received="2026-11-25T09:00:00Z"),
        item("late", received="2026-11-25T09:00:00Z", deadline_notices={"overdue": "2026-11-26T08:00:00Z"}),
        item("paused", received="2026-11-25T10:00:00Z", paused_at="2026-11-26T08:00:00Z"),
        item("free", kind="impact_review", change=None, gate=None, received="2026-11-25T08:00:00Z"),
    ]
    for i in items:
        discuss(store, i["id"], talk=2 if i["id"] == "talk" else 1)
    entries = agenda.build(items, store, order=[], now=T0)
    assert [e["item_id"] for e in entries] == ["paused", "late", "talk", "old", "free"]
    reasons = {e["item_id"]: e["reasons"] for e in entries}
    assert "the run is paused" in reasons["paused"]
    assert "past its deadline" in reasons["late"]
    assert "CHG-1 waits at B2" in reasons["old"]
    assert "2 want to talk live" in reasons["talk"]
    assert "waiting 6 days" in reasons["old"]
    assert entries[0]["answers"][0] == {"name": "Adm Test", "option": "talk_live", "reason": "Trzeba to omówić."}


def test_ag03_a_manual_order_comes_first_and_new_items_follow_by_what_they_block(store: consult.Consultations) -> None:
    items = [item("a", received="2026-11-20T09:00:00Z"), item("b"), item("c", paused_at="2026-11-26T08:00:00Z")]
    for i in items:
        discuss(store, i["id"])
    assert [e["item_id"] for e in agenda.build(items, store, order=["b", "a", "gone"], now=T0)] == ["b", "a", "c"]
    assert agenda.moved(["c", "b", "a"], "a", "up") == ["c", "a", "b"]
    assert agenda.moved(["c", "b", "a"], "c", "up") == ["c", "b", "a"]
    assert agenda.moved(["c", "b", "a"], "c", "down") == ["b", "c", "a"]


def test_ag04_markdown_for_the_invitation(store: consult.Consultations) -> None:
    items = [item("a")]
    discuss(store, "a")
    md = agenda.markdown(agenda.build(items, store, order=[], now=T0), day="2026-11-26")
    assert md.startswith("# Discuss with team — 2026-11-26")
    assert "1. **Sprawa a** (CHG-1, B2)" in md
    assert "Adm Test: talk_live — Trzeba to omówić." in md


# --- konsola ---


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


def write_gate(registry: Registry, item_id: str = "evt-1") -> dict[str, Any]:
    (registry.root / "changes").mkdir(parents=True, exist_ok=True)
    change = {"change": "CHG-1", "status": "open", "approved": {}, "waiting": ["B2"], "history": []}
    (registry.root / "changes" / "CHG-1.yaml").write_text(json.dumps(change), encoding="utf-8")
    (registry.root / "inbox").mkdir(parents=True, exist_ok=True)
    received = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    data = {"id": item_id, "kind": "gate", "status": "open", "change": "CHG-1", "source": "tf", "release": None,
            "summary": "Prośba o bramkę B2", "received_at": received, "gate": "B2", "missing_before": [],
            "event": {"id": item_id, "type": "gate.requested", "occurred_at": received, "source": "tf",
                      "contract_version": "0.26.0", "payload": {"change": "CHG-1", "gate": "B2"}}}  # fmt: skip
    (registry.root / "inbox" / f"{item_id}.yaml").write_text(json.dumps(data), encoding="utf-8")
    return data


def test_ag05_the_agenda_page_and_a_decision_from_it_is_a_meeting_decision(app: Console, registry: Registry) -> None:
    gate = write_gate(registry)
    s = people(app)
    ask(app, s["ola"], ["s-adm", "s-3"])
    answer(app, s["adm"], "talk_live", "Trzeba to omówić na żywo.")
    answer(app, s["viewer"], "rejected", "Za duże ryzyko.")
    status, _, page, _ = app.request("GET", "/discuss", cookie=s["viewer"])
    assert status == 200
    assert "Discuss with team" in page and "Prośba o bramkę B2" in page
    assert "Trzeba to omówić na żywo." in page
    assert "CHG-1 waits at B2" in page
    assert "# Discuss with team" in page, "the Markdown for the invitation"
    assert 'action="/discuss/evt-1/up"' not in page, "a viewer does not reorder"
    _, _, page, _ = app.request("GET", "/discuss", cookie=s["ola"])
    assert 'action="/discuss/evt-1/up"' in page
    form = {"t": "", "loaded_at": gate["received_at"], "statement": "Poprawki przed B2.",
            "why": "Ustalone na refinemencie.", "outcome": "changes_requested", "via": "agenda"}  # fmt: skip
    assert app.request("POST", "/inbox/evt-1/decide", cookie=s["ola"], form=form)[0] == 200
    decision = registry.get(Inbox(registry).items(status="decided")[0]["decision"])
    assert decision["source"]["kind"] == "meeting"
    assert decision["source"]["url"].endswith("/discuss")
    assert len(decision["consulted"]) == 2
    _, _, page, _ = app.request("GET", "/discuss", cookie=s["ola"])
    assert "Nothing to discuss" in page


def test_ag06_reordering_is_for_editors_and_admins_and_is_kept(app: Console, registry: Registry) -> None:
    for i in ("evt-1", "evt-2"):
        write_gate(registry, i)
    s = people(app)
    for i in ("evt-1", "evt-2"):
        form = {"hours": "24", "ask_s-adm": "1"}
        assert app.request("POST", f"/inbox/{i}/ask", cookie=s["ola"], form=form)[0] == 303
        app.request("POST", f"/inbox/{i}/answer", cookie=s["adm"], form={"option": "talk_live", "reason": "Na żywo."})
    assert app.request("POST", "/discuss/evt-2/up", cookie=s["viewer"], form={})[0] == 403
    assert app.request("POST", "/discuss/evt-2/up", cookie=s["ola"], form={})[0] == 303
    _, _, page, _ = app.request("GET", "/discuss", cookie=s["ola"])
    assert page.index("evt-2") < page.index("evt-1")
    assert json.loads((registry.root / "agenda.json").read_text(encoding="utf-8"))["order"][:2] == ["evt-2", "evt-1"]


def test_ag07_the_agent_reads_the_agenda_through_mcp(registry: Registry, tmp_path: Path) -> None:
    import asyncio

    from pdi.mcp_server import build_server

    write_gate(registry)
    store = consult.Consultations(registry.root, now=registry.now)
    discuss(store, "evt-1")
    server = build_server(lambda: registry)
    result = asyncio.run(server.call_tool("discussion_agenda", {}))
    assert result.is_error is False
    entries = result.structured_content["items"]
    assert [e["item_id"] for e in entries] == ["evt-1"]
    assert re.search(r"waiting", " ".join(entries[0]["reasons"]))


def test_ag08_without_the_suite_the_agenda_forms_carry_the_console_token(registry: Registry) -> None:
    from pdi import console
    from tests.test_console import TOKEN, _get, _post, _serve

    gate = write_gate(registry)
    store = consult.Consultations(registry.root, now=registry.now)
    discuss(store, "evt-1")
    server, url = _serve(console.Deps(registry, checkout=None))
    try:
        status, body, _ = _get(f"{url}/discuss?t={TOKEN}")
        page = body.decode()
        assert status == 200
        assert f'action="/discuss/evt-1/up?t={TOKEN}"' in page
        assert f'action="/inbox/evt-1/decide?t={TOKEN}"' in page
        # urllib follows the 303 back to the agenda.
        assert _post(f"{url}/discuss/evt-1/down?t={TOKEN}", {"t": TOKEN})[0] == 200
        assert json.loads((registry.root / "agenda.json").read_text(encoding="utf-8"))["order"] == ["evt-1"]
        form = {"t": TOKEN, "loaded_at": gate["received_at"], "statement": "Tak.", "why": "Ustalone.",
                "outcome": "approved", "via": "agenda"}  # fmt: skip
        assert _post(f"{url}/inbox/evt-1/decide?t={TOKEN}", form)[0] == 200
    finally:
        server.shutdown()
