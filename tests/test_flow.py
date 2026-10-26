from typing import Any

import pytest

from pdi.flow import (
    GATES,
    InvalidTransition,
    feature_released,
    gate_decided,
    gate_requested,
    impact_opened,
    impact_reviewed,
    impact_scheduled,
    missing_before,
    new_state,
    readiness_changed,
)

AT = "2026-10-26T10:00:00Z"


def approved(*gates: str) -> dict[str, Any]:
    state = new_state("CHG-12")
    for n, gate in enumerate(gates, start=1):
        state = gate_requested(state, gate, at=AT)
        state, _ = gate_decided(state, gate, "approved", f"DEC-{n}", at=AT)
    return state


def test_chain_follows_the_one_flow_plan() -> None:
    chain = [g.name for g in GATES if g.in_chain]

    assert chain == ["B1", "B2", "B3", "design-review", "approve-for-implementation", "B4", "B5"]


def test_new_state_is_open_and_empty() -> None:
    state = new_state("CHG-12")

    assert state == {
        "change": "CHG-12",
        "status": "open",
        "approved": {},
        "waiting": [],
        "readiness": None,
        "baseline_drift": False,
        "releases": {},
        "history": [],
    }


def test_request_marks_gate_as_waiting_and_logs_it() -> None:
    state = gate_requested(new_state("CHG-12"), "B1", at=AT)

    assert state["waiting"] == ["B1"]
    assert state["history"] == [{"at": AT, "what": "gate.requested", "gate": "B1"}]


def test_repeated_request_keeps_one_waiting_entry() -> None:
    state = gate_requested(gate_requested(new_state("CHG-12"), "B1", at=AT), "B1", at=AT)

    assert state["waiting"] == ["B1"]


def test_missing_before_names_unapproved_earlier_gates() -> None:
    state = approved("B1")

    assert missing_before(state, "B3") == ["B2"]
    assert missing_before(state, "B2") == []
    assert missing_before(state, "B6") == []
    assert missing_before(state, "stage:payment-retry") == []


@pytest.mark.parametrize(
    ("gate", "outcome", "phase", "rework"),
    [
        ("B1", "approved", "requirements", False),
        ("B2", "approved", "architecture", False),
        ("B3", "approved", "design", False),
        ("design-review", "approved", None, False),
        ("approve-for-implementation", "approved", "delivery", False),
        ("B4", "approved", None, False),
        ("B5", "approved", None, False),
        ("B1", "changes_requested", "intent", True),
        ("B2", "changes_requested", "requirements", True),
        ("B3", "changes_requested", "architecture", True),
        ("design-review", "changes_requested", "design", True),
        ("approve-for-implementation", "changes_requested", None, True),
        ("B6", "approved", None, False),
        ("stage:payment-retry", "approved", None, False),
    ],
)
def test_decision_returns_phase_to_run(gate: str, outcome: str, phase: str | None, rework: bool) -> None:
    state = gate_requested(new_state("CHG-12"), gate, at=AT)

    state, run = gate_decided(state, gate, outcome, "DEC-7", at=AT)

    assert run == ({"phase": phase, "rework": rework} if phase else None)
    assert gate not in state["waiting"]
    assert state["history"][-1] == {
        "at": AT,
        "what": "gate.decided",
        "gate": gate,
        "outcome": outcome,
        "decision": "DEC-7",
    }


def test_approval_is_recorded_and_changes_requested_is_not() -> None:
    state = gate_requested(new_state("CHG-12"), "B1", at=AT)
    state, _ = gate_decided(state, "B1", "changes_requested", "DEC-1", at=AT)
    assert state["approved"] == {}

    state = gate_requested(state, "B1", at=AT)
    state, _ = gate_decided(state, "B1", "approved", "DEC-2", at=AT)
    assert state["approved"] == {"B1": "DEC-2"}


def test_rejection_closes_the_change() -> None:
    state = gate_requested(new_state("CHG-12"), "B2", at=AT)

    state, run = gate_decided(state, "B2", "rejected", "DEC-3", at=AT)

    assert run is None
    assert state["status"] == "rejected"
    assert state["waiting"] == []


def test_closed_change_refuses_further_decisions() -> None:
    state = gate_requested(new_state("CHG-12"), "B2", at=AT)
    state, _ = gate_decided(state, "B2", "rejected", "DEC-3", at=AT)

    with pytest.raises(InvalidTransition, match="rejected"):
        gate_decided(state, "B3", "approved", "DEC-4", at=AT)


def test_unknown_outcome_is_refused() -> None:
    with pytest.raises(InvalidTransition, match="outcome"):
        gate_decided(new_state("CHG-12"), "B1", "maybe", "DEC-1", at=AT)


def test_readiness_is_kept_and_drift_after_approval_is_flagged() -> None:
    state = readiness_changed(new_state("CHG-12"), "not_ready", at=AT)
    assert (state["readiness"], state["baseline_drift"]) == ("not_ready", False)

    state = approved("approve-for-implementation")
    state = readiness_changed(state, "drift", at=AT)

    assert (state["readiness"], state["baseline_drift"]) == ("drift", True)
    assert state["history"][-1] == {"at": AT, "what": "readiness.changed", "readiness": "drift"}


def test_drift_before_approval_is_not_a_baseline_drift() -> None:
    state = readiness_changed(new_state("CHG-12"), "drift", at=AT)

    assert state["baseline_drift"] is False


def test_new_approval_clears_baseline_drift() -> None:
    state = readiness_changed(approved("approve-for-implementation"), "drift", at=AT)
    state = gate_requested(state, "approve-for-implementation", at=AT)

    state, _ = gate_decided(state, "approve-for-implementation", "approved", "DEC-9", at=AT)

    assert state["baseline_drift"] is False
    assert state["approved"]["approve-for-implementation"] == "DEC-9"


def test_feature_released_records_each_line() -> None:
    state = feature_released(new_state("CHG-12"), "R2", "2026-11-05T12:00:00Z", at=AT)
    state = feature_released(state, None, "2026-11-06T12:00:00Z", at=AT)

    assert state["releases"] == {"R2": "2026-11-05T12:00:00Z", "all": "2026-11-06T12:00:00Z"}
    assert state["status"] == "open"


def test_released_tasks_are_kept_per_line() -> None:
    state = feature_released(new_state("CHG-12"), "R1", "2026-11-05T12:00:00Z", at=AT, tasks=["TSK-57"])

    assert state["release_tasks"] == {"R1": ["TSK-57"]}
    assert "release_tasks" not in feature_released(new_state("CHG-12"), "R2", "2026-11-05T12:00:00Z", at=AT)


def test_impact_review_finishes_the_change() -> None:
    state = feature_released(new_state("CHG-12"), "R1", "2026-11-05T12:00:00Z", at=AT)

    state = impact_reviewed(state, "DEC-10", at=AT)

    assert state["status"] == "done"
    assert state["history"][-1] == {"at": AT, "what": "impact.reviewed", "decision": "DEC-10"}


def test_impact_review_is_scheduled_opened_and_decided() -> None:
    plan = {"due": "2026-12-05", "basis": "default", "intent": None, "released_at": "2026-11-05T12:00:00Z"}

    state = impact_scheduled(new_state("CHG-12"), plan, at=AT)
    assert state["impact_review"] == {"status": "scheduled", **plan}
    state = impact_opened(state, "impact-CHG-12-R1", at=AT)
    assert (state["impact_review"]["status"], state["impact_review"]["item"]) == ("open", "impact-CHG-12-R1")
    state = impact_reviewed(state, "DEC-10", at=AT, outcome="not_met")

    assert state["impact_review"]["status"] == "decided"
    assert (state["impact_review"]["outcome"], state["impact_review"]["decision"]) == ("not_met", "DEC-10")
    assert state["history"][-1] == {"at": AT, "what": "impact.reviewed", "decision": "DEC-10", "outcome": "not_met"}
    assert [h["what"] for h in state["history"]] == ["impact.scheduled", "impact.opened", "impact.reviewed"]


def test_transitions_do_not_mutate_their_input() -> None:
    before = new_state("CHG-12")

    gate_requested(before, "B1", at=AT)

    assert before == new_state("CHG-12")


def test_done_change_still_takes_stage_gates_of_later_lines() -> None:
    state = impact_reviewed(new_state("CHG-12"), "DEC-10", at=AT)
    state = gate_requested(state, "stage:payment-retry:100%", at=AT)

    state, run = gate_decided(state, "stage:payment-retry:100%", "approved", "DEC-11", at=AT)

    assert run is None
    assert state["status"] == "done"
