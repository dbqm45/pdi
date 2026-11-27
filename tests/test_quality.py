"""G7: kolejka bramek obok jakości wydań, tydzień po tygodniu (docs/plan-g7-kolejka-i-jakosc.md)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pdi import quality

NOW = datetime(2026, 11, 27, 12, 0, tzinfo=UTC)  # piątek tygodnia 2026-W48


def state(change: str, history: list[dict[str, Any]]) -> dict[str, Any]:
    return {"change": change, "status": "open", "history": history}


def req(at: str, gate: str) -> dict[str, Any]:
    return {"at": at, "what": "gate.requested", "gate": gate}


def dec(at: str, gate: str) -> dict[str, Any]:
    return {"at": at, "what": "gate.decided", "gate": gate, "outcome": "approved", "decision": "DEC-1"}


STATES = [
    # W46: poproszona i rozstrzygnięta po 4 h
    state("CHG-1", [req("2026-11-10T08:00:00Z", "B1"), dec("2026-11-10T12:00:00Z", "B1")]),
    # W46 → W47: czeka przez koniec W46, rozstrzygnięta w W47 po 48 h
    state("CHG-2", [req("2026-11-15T12:00:00Z", "B2"), dec("2026-11-17T12:00:00Z", "B2")]),
    # W47: dwie otwarte na koniec W47, jedna rozstrzygnięta dopiero w W48
    state("CHG-3", [req("2026-11-18T08:00:00Z", "B3"), dec("2026-11-25T08:00:00Z", "B3")]),
    state("CHG-4", [req("2026-11-19T08:00:00Z", "B4")]),
]
PROBLEMS = [
    {"id": "PRB-1", "reported_at": "2026-11-18T09:00:00Z"},
    {"id": "PRB-2", "reported_at": "2026-11-26T09:00:00Z"},
]
DAYS = [
    {"date": "2026-11-11", "deployments": 4, "failedDeployments": 0, "rollbacks": 0},
    {"date": "2026-11-19", "deployments": 3, "failedDeployments": 1, "rollbacks": 1},
    {"date": "2026-11-20", "deployments": 1, "failedDeployments": 0, "rollbacks": 0},
]


def week(r: dict[str, Any], name: str) -> dict[str, Any]:
    return next(w for w in r["weeks"] if w["week"] == name)


def test_q01_eight_iso_weeks_oldest_first_ending_with_the_current_one() -> None:
    r = quality.report([], [], DAYS, now=NOW)
    assert [w["week"] for w in r["weeks"]] == [f"2026-W{n}" for n in range(41, 49)]
    assert week(r, "2026-W48")["from"] == "2026-11-23" and week(r, "2026-W48")["to"] == "2026-11-29"
    assert week(r, "2026-W48")["current"] is True and week(r, "2026-W47")["current"] is False


def test_q02_the_queue_at_week_end_and_the_gates_of_each_week() -> None:
    r = quality.report(STATES, [], None, now=NOW)
    w46, w47, w48 = week(r, "2026-W46"), week(r, "2026-W47"), week(r, "2026-W48")
    assert (w46["requested"], w46["decided"], w46["queue_end"], w46["median_wait_hours"]) == (2, 1, 1, 4.0)
    assert (w47["requested"], w47["decided"], w47["queue_end"], w47["median_wait_hours"]) == (2, 1, 2, 48.0)
    assert (w48["requested"], w48["decided"], w48["queue_end"]) == (0, 1, 1)  # bieżący: kolejka teraz
    assert week(r, "2026-W41")["median_wait_hours"] is None


def test_q03_cfr_from_shipscope_and_new_problems_from_pdi() -> None:
    r = quality.report([], PROBLEMS, DAYS, now=NOW)
    w46, w47, w45 = week(r, "2026-W46"), week(r, "2026-W47"), week(r, "2026-W45")
    assert (w46["deployments"], w46["failed"], w46["rollbacks"], w46["cfr"]) == (4, 0, 0, 0.0)
    # ShipScope: deployments to udane, nieudane osobno, rollback jest udanym wdrożeniem → 2 / (4 + 1)
    assert (w47["deployments"], w47["failed"], w47["rollbacks"], w47["cfr"]) == (4, 1, 1, 0.4)
    only_failed = quality.report([], [], [{"date": "2026-11-04", "deployments": 0, "failedDeployments": 2}], now=NOW)
    assert week(only_failed, "2026-W45")["cfr"] == 1.0
    assert w45["deployments"] == 0 and w45["cfr"] is None  # bez wdrożeń nie ma odsetka
    assert w47["new_problems"] == 1 and week(r, "2026-W48")["new_problems"] == 1


def test_q04_queue_and_cfr_rising_together_is_a_hint_about_review() -> None:
    r = quality.report(STATES, PROBLEMS, DAYS, now=NOW)
    assert r["signal"] == {
        "kind": "review_may_lag",
        "week": "2026-W47",
        "text": "Kolejka bramek i odsetek nieudanych wdrożeń rosną razem — przegląd może nie nadążać.",
    }
    calm = [{**d, "failedDeployments": 0, "rollbacks": 0} for d in DAYS]
    assert quality.report(STATES, PROBLEMS, calm, now=NOW)["signal"] is None  # sama kolejka to jeszcze nie zator


def test_q05_without_shipscope_the_quality_columns_are_empty_and_the_reason_is_given() -> None:
    r = quality.report(
        STATES, PROBLEMS, None, now=NOW, shipscope_error="Brak PDI_SHIPSCOPE_URL — pdi nie czyta danych z ShipScope."
    )
    assert all(w["deployments"] is None and w["cfr"] is None for w in r["weeks"])
    assert r["shipscope"] == {"on": False, "error": "Brak PDI_SHIPSCOPE_URL — pdi nie czyta danych z ShipScope."}
    assert r["signal"] is None
    assert week(r, "2026-W47")["new_problems"] == 1  # dane pdi zostają


def test_q06_the_range_to_ask_shipscope_for() -> None:
    assert quality.window(NOW) == ("2026-10-05", "2026-11-29")
