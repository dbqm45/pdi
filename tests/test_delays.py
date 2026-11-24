"""DV4: gdzie zmiana czeka — czasy na bramkach i w skrzynce z historii zmiany (docs/plan-dv4-gdzie-zmiana-czeka.md)."""

from datetime import UTC, datetime
from typing import Any

from pdi import delays

NOW = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)


def state(change: str, history: list[dict[str, Any]], status: str = "open") -> dict[str, Any]:
    return {"change": change, "status": status, "history": history}


def req(at: str, gate: str) -> dict[str, Any]:
    return {"at": at, "what": "gate.requested", "gate": gate}


def dec(at: str, gate: str, outcome: str = "approved") -> dict[str, Any]:
    return {"at": at, "what": "gate.decided", "gate": gate, "outcome": outcome, "decision": "DEC-1"}


CHG12 = state(
    "CHG-12",
    [
        req("2026-11-20T08:00:00Z", "B1"),
        dec("2026-11-20T12:00:00Z", "B1"),  # 4 h czekania
        req("2026-11-21T08:00:00Z", "B2"),
        dec("2026-11-21T20:00:00Z", "B2", "changes_requested"),  # 12 h, runda 1
        req("2026-11-22T08:00:00Z", "B2"),
        dec("2026-11-22T10:00:00Z", "B2"),  # 2 h, runda 2
        req("2026-11-23T12:00:00Z", "B3"),  # otwarta: 24 h do NOW
    ],
)


def test_dv01_requests_are_paired_with_the_next_decision_of_the_same_gate() -> None:
    t = delays.timeline(CHG12, now=NOW)
    assert [(g["gate"], g["hours"], g["outcome"], g["round"]) for g in t["gates"]] == [
        ("B1", 4.0, "approved", 1),
        ("B2", 12.0, "changes_requested", 1),
        ("B2", 2.0, "approved", 2),
        ("B3", 24.0, None, 1),
    ]
    assert t["open"] == {"gate": "B3", "since": "2026-11-23T12:00:00Z", "hours": 24.0, "stage": None, "risk": None}


def test_dv02_waiting_is_the_union_of_open_gates_and_work_is_the_rest() -> None:
    t = delays.timeline(CHG12, now=NOW)
    assert t["total_hours"] == 100.0  # 2026-11-20T08:00 → 2026-11-24T12:00
    assert t["waiting_hours"] == 42.0  # 4 + 12 + 2 + 24
    assert t["working_hours"] == 58.0
    overlap = state("CHG-13", [req("2026-11-24T00:00:00Z", "B4"), req("2026-11-24T06:00:00Z", "B5")])
    o = delays.timeline(overlap, now=NOW)
    assert o["waiting_hours"] == 12.0 and o["working_hours"] == 0.0  # nakładające się bramki liczone raz


def test_dv03_a_released_change_ends_at_the_release() -> None:
    done = state(
        "CHG-14",
        [
            req("2026-11-20T00:00:00Z", "B5"),
            dec("2026-11-20T06:00:00Z", "B5"),
            {"at": "2026-11-21T00:00:00Z", "what": "feature.released", "release": "all"},
        ],
        status="released",
    )
    t = delays.timeline(done, now=NOW)
    assert t["released_at"] == "2026-11-21T00:00:00Z" and t["total_hours"] == 24.0 and t["open"] is None


def test_dv04_the_open_gate_shows_its_deadline_stage_from_the_inbox() -> None:
    item = {
        "id": "evt-1",
        "kind": "gate",
        "status": "open",
        "change": "CHG-12",
        "gate": "B3",
        "received_at": "2026-11-16T12:00:00Z",
    }
    t = delays.timeline(CHG12, now=NOW, items=[item])
    assert t["open"]["stage"] == "overdue"  # B3: 5 dni roboczych od pon. 16.11 → pon. 23.11


def test_dv05_report_lists_waiting_changes_gates_and_inbox_kinds() -> None:
    other = state("CHG-20", [req("2026-11-24T10:00:00Z", "B1")])
    items = [
        {
            "id": "a",
            "kind": "gate",
            "status": "decided",
            "received_at": "2026-11-20T08:00:00Z",
            "decided_at": "2026-11-20T12:00:00Z",
        },
        {
            "id": "b",
            "kind": "gate",
            "status": "decided",
            "received_at": "2026-11-21T08:00:00Z",
            "decided_at": "2026-11-21T10:00:00Z",
        },
        {
            "id": "c",
            "kind": "problem",
            "status": "decided",
            "received_at": "2026-11-21T08:00:00Z",
            "decided_at": "2026-11-23",
        },  # sama data — początek dnia
        {"id": "d", "kind": "problem", "status": "open", "received_at": "2026-11-24T08:00:00Z"},
    ]
    r = delays.report([CHG12, other], items, now=NOW)
    assert [(w["change"], w["gate"], w["hours"]) for w in r["waiting"]] == [
        ("CHG-12", "B3", 24.0),
        ("CHG-20", "B1", 2.0),
    ]
    by_gate = {g["gate"]: g for g in r["gates"]}
    assert by_gate["B2"] == {"gate": "B2", "decided": 2, "median_hours": 7.0, "max_hours": 12.0, "open": 0}
    assert by_gate["B1"]["open"] == 1 and by_gate["B3"]["decided"] == 0
    assert [g["gate"] for g in r["gates"]] == ["B1", "B2", "B3"]  # kolejność łańcucha
    kinds = {k["kind"]: k for k in r["items"]}
    assert kinds["gate"] == {"kind": "gate", "decided": 2, "median_hours": 3.0, "open": 0}
    assert kinds["problem"] == {"kind": "problem", "decided": 1, "median_hours": 40.0, "open": 1}
    assert r["changes"][0] == {"change": "CHG-12", "waiting_hours": 42.0, "working_hours": 58.0, "waiting_share": 0.42}


def test_dv06_an_empty_history_gives_an_empty_timeline() -> None:
    t = delays.timeline(state("CHG-1", []), now=NOW)
    assert t["gates"] == [] and t["open"] is None and t["total_hours"] == 0.0 and t["waiting_hours"] == 0.0
