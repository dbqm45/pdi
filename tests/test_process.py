"""DV1: bramki do uproszczenia — pomiar z osi zmian DV4 i szkice decyzji w skrzynce (docs/plan-dv1-…)."""

from datetime import UTC, datetime
from typing import Any

from pdi import process
from pdi.changes import ChangeStore
from pdi.inbox import Inbox
from pdi.registry import Registry
from tests.conftest import draft

NOW = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)


def change(n: int, gate: str, outcomes: list[str], day: int = 1) -> dict[str, Any]:
    """Zmiana CHG-n z kolejnymi rundami bramki `gate`: prośba o 8:00, decyzja o 12:00 kolejnych dni listopada."""
    history: list[dict[str, Any]] = []
    for i, outcome in enumerate(outcomes):
        d = f"2026-11-{day + i:02d}"
        history.append({"at": f"{d}T08:00:00Z", "what": "gate.requested", "gate": gate})
        history.append(
            {"at": f"{d}T12:00:00Z", "what": "gate.decided", "gate": gate, "outcome": outcome, "decision": "DEC-1"}
        )
    return {"change": f"CHG-{n}", "status": "open", "history": history}


def clean(gate: str, count: int) -> list[dict[str, Any]]:
    return [change(n, gate, ["approved"]) for n in range(1, count + 1)]


def row(rows: list[dict[str, Any]], gate: str) -> dict[str, Any]:
    return next(r for r in rows if r["gate"] == gate)


def test_dv1_01_a_gate_that_never_stops_a_change_is_challenged() -> None:
    r = row(process.report(clean("B1", 30), now=NOW), "B1")
    assert r["measured"] == 30 and r["passed"] == 30 and r["stopped"] == 0 and r["passed_share"] == 1.0
    assert r["median_hours"] == 4.0
    assert r["recommendation"]["action"] == "challenge" and "30/30" in r["recommendation"]["reason"]


def test_dv1_02_too_few_decisions_or_a_gate_that_stops_changes_is_kept() -> None:
    few = row(process.report(clean("B1", 12), now=NOW), "B1")
    assert few["recommendation"] == {"action": "keep", "reason": "za mało danych: 12/30"}
    stopping = clean("B2", 26) + [change(100 + n, "B2", ["changes_requested", "approved"]) for n in range(2)]
    r = row(process.report(stopping, now=NOW), "B2")
    assert r["measured"] == 30 and r["stopped"] == 2 and r["recommendation"]["action"] == "keep"


def test_dv1_03_the_window_takes_the_latest_decisions() -> None:
    old = [change(200 + n, "B1", ["changes_requested"], day=1) for n in range(5)]
    recent = [change(n, "B1", ["approved"], day=10) for n in range(1, 31)]
    r = row(process.report(old + recent, now=NOW), "B1")
    assert r["measured"] == 30 and r["stopped"] == 0 and r["decided"] == 35


def test_dv1_04_a_protected_gate_is_never_challenged() -> None:
    r = row(process.report(clean("B5", 30), now=NOW), "B5")
    assert r["protected"] is True and r["recommendation"]["action"] == "keep"


def seed(registry: Registry, states: list[dict[str, Any]]) -> None:
    store = ChangeStore(registry)
    for s in states:
        store.save(s)


def test_dv1_05_inbox_opens_one_proposal_per_gate_and_records_the_decision(registry: Registry) -> None:
    seed(registry, clean("B1", 30))
    inbox = Inbox(registry)
    first = inbox.propose_process_changes()
    assert [i["gate"] for i in first] == ["B1"] and first[0]["kind"] == "process"
    assert "B1" in first[0]["summary"] and "uprości" in first[0]["summary"]
    assert inbox.propose_process_changes() == []  # otwarta już jest
    result = inbox.decide(first[0]["id"], draft(statement="B1 zostaje.", kind="process"), outcome="rejected")
    d = result["decision"]
    assert d["kind"] == "process" and d["decision_type"] == process.GATE_CHANGE_TYPE
    assert "process" in d["tags"] and "bramka:B1" in d["tags"]
    assert any("30/30" in e["text"] for e in d["evidence"])
    assert inbox.propose_process_changes() == []  # po decyzji: dopiero po nowym pełnym oknie


def test_dv1_06_a_new_full_window_after_the_decision_opens_a_new_proposal(registry: Registry) -> None:
    seed(registry, clean("B1", 30))
    inbox = Inbox(registry)
    item = inbox.propose_process_changes()[0]
    inbox.decide(item["id"], draft(statement="B1 zostaje.", kind="process"), outcome="rejected")
    seed(registry, [change(n, "B1", ["approved"], day=10) for n in range(31, 61)])
    again = inbox.propose_process_changes()
    assert [i["gate"] for i in again] == ["B1"] and again[0]["id"] != item["id"]
