"""A3: licznik akceptacji szkiców, rekomendacje poziomu autonomii i propozycje w skrzynce (plan-a3)."""

from collections.abc import Callable
from typing import Any

import pytest
import yaml

from pdi import autonomy
from pdi.inbox import Inbox, ItemClosed
from pdi.registry import InvalidDecision, Registry

Draft = Callable[..., dict[str, Any]]
_seq = iter(range(1, 100_000))


def decide_many(
    registry: Registry, make_draft: Draft, decision_type: str, edited: list[bool | None], **extra: Any
) -> None:
    """Zapisuje decyzje danego typu ze szkicem AI; `None` = szkic AI bez informacji o poprawkach."""
    for flag in edited:
        fields: dict[str, Any] = {"decision_type": decision_type, **extra}
        if flag is not None:
            fields["draft_edited"] = flag
        registry.record(make_draft(statement=f"Decyzja {next(_seq)}.", **fields))


def row(report: list[dict[str, Any]], decision_type: str) -> dict[str, Any]:
    return next(r for r in report if r["decision_type"] == decision_type)


def write_policy(registry: Registry, entries: list[dict[str, Any]]) -> None:
    registry.root.mkdir(parents=True, exist_ok=True)
    (registry.root / "autonomy.yaml").write_text(yaml.safe_dump({"policy": entries}), encoding="utf-8")


# --- pomiar i rekomendacje ---


def test_catalog_types_start_at_level_3_without_data(registry: Registry) -> None:
    report = autonomy.report(registry)

    r = row(report, "finding.auto_close")
    assert (r["level"], r["measured"], r["window"]) == (3, 0, 30)
    assert r["recommendation"]["action"] == "keep"
    assert "0/30" in r["recommendation"]["reason"]
    assert row(report, "triage")["protected"] is True


def test_full_window_of_unedited_drafts_recommends_lowering_one_level(registry: Registry, make_draft: Draft) -> None:
    decide_many(registry, make_draft, "finding.auto_close", [True] + [False] * 30)

    r = row(autonomy.report(registry), "finding.auto_close")

    assert (r["measured"], r["unedited"], r["unedited_share"]) == (30, 30, 1.0)  # okno: ostatnie 30
    assert r["recommendation"] == {
        "action": "lower",
        "to_level": 2,
        "reason": "30/30 szkiców bez poprawek (100%) ≥ 95% w ostatnich 30",
    }


@pytest.mark.parametrize(
    ("edited_in_window", "action"),
    [pytest.param(1, "lower", id="29-z-30-to-96.7%"), pytest.param(2, "keep", id="28-z-30-to-93.3%")],
)
def test_threshold_of_95_percent(registry: Registry, make_draft: Draft, edited_in_window: int, action: str) -> None:
    decide_many(
        registry, make_draft, "ac.format_rewrite", [True] * edited_in_window + [False] * (30 - edited_in_window)
    )

    assert row(autonomy.report(registry), "ac.format_rewrite")["recommendation"]["action"] == action


def test_window_not_full_is_not_enough_data(registry: Registry, make_draft: Draft) -> None:
    decide_many(registry, make_draft, "review.light", [False] * 29)

    rec = row(autonomy.report(registry), "review.light")["recommendation"]
    assert rec["action"] == "keep"
    assert "29/30" in rec["reason"]


def test_human_drafts_are_ignored_and_unknown_edits_are_counted_apart(registry: Registry, make_draft: Draft) -> None:
    decide_many(registry, make_draft, "dependency.update", [False] * 3)
    decide_many(registry, make_draft, "dependency.update", [None] * 2)
    registry.record(make_draft(statement="Ręcznie.", decision_type="dependency.update", drafted_by="human"))

    r = row(autonomy.report(registry), "dependency.update")
    assert (r["decisions"], r["ai_drafted"], r["measured"], r["unknown"]) == (6, 5, 3, 2)


def test_protected_type_is_never_recommended_lower(registry: Registry, make_draft: Draft) -> None:
    decide_many(registry, make_draft, "triage", [False] * 30)

    rec = row(autonomy.report(registry), "triage")["recommendation"]
    assert rec["action"] == "keep"
    assert "chroniony" in rec["reason"]


def test_lowered_type_with_too_many_edits_goes_back_to_human(registry: Registry, make_draft: Draft) -> None:
    write_policy(registry, [{"decision_type": "flag.stage_advance", "level": 2, "veto_window": "PT4H"}])
    decide_many(registry, make_draft, "flag.stage_advance", [False] * 8 + [True] * 2)

    r = row(autonomy.report(registry), "flag.stage_advance")
    assert r["level"] == 2
    assert r["recommendation"]["action"] == "raise"
    assert r["recommendation"]["to_level"] == 3


def test_level_2_can_go_to_1_but_never_to_0(registry: Registry, make_draft: Draft) -> None:
    write_policy(
        registry,
        [
            {"decision_type": "flag.removal_pr", "level": 2, "veto_window": "PT4H"},
            {"decision_type": "dependency.update", "level": 1},
        ],
    )
    decide_many(registry, make_draft, "flag.removal_pr", [False] * 30)
    decide_many(registry, make_draft, "dependency.update", [False] * 30)

    report = autonomy.report(registry)
    assert row(report, "flag.removal_pr")["recommendation"]["to_level"] == 1
    assert row(report, "dependency.update")["recommendation"]["action"] == "keep"


def test_policy_can_override_thresholds_per_type(registry: Registry, make_draft: Draft) -> None:
    write_policy(
        registry,
        [
            {
                "decision_type": "review.light",
                "level": 3,
                "lower_when": {"last_decisions": 10, "min_unedited_share": 0.9},
            }
        ],
    )
    decide_many(registry, make_draft, "review.light", [True] + [False] * 9)

    r = row(autonomy.report(registry), "review.light")
    assert r["window"] == 10
    assert r["recommendation"]["action"] == "lower"


def test_types_seen_only_in_decisions_are_reported(registry: Registry, make_draft: Draft) -> None:
    decide_many(registry, make_draft, "deploy.restart", [False])

    assert row(autonomy.report(registry), "deploy.restart")["level"] == 3


def test_invalid_policy_file_is_refused(registry: Registry) -> None:
    write_policy(registry, [{"decision_type": "triage", "level": 1}])

    with pytest.raises(autonomy.InvalidPolicy, match="autonomy.yaml"):
        autonomy.report(registry)


# --- propozycje w skrzynce i decyzja człowieka ---


def ready_to_lower(registry: Registry, make_draft: Draft, decision_type: str = "finding.auto_close") -> Inbox:
    decide_many(registry, make_draft, decision_type, [False] * 30)
    return Inbox(registry)


def test_proposal_opens_one_autonomy_item_per_type(registry: Registry, make_draft: Draft) -> None:
    inbox = ready_to_lower(registry, make_draft)

    first = inbox.propose_autonomy_changes()
    again = inbox.propose_autonomy_changes()

    assert len(first) == 1 and again == []
    item = first[0]
    assert item["kind"] == "autonomy"
    assert (item["decision_type"], item["from_level"], item["to_level"], item["veto_window"]) == (
        "finding.auto_close",
        3,
        2,
        "PT4H",
    )
    assert item["change"] is None
    assert "finding.auto_close" in item["summary"] and "3 → 2" in item["summary"]
    assert inbox.get(item["id"])["status"] == "open"


def test_approving_lowers_the_level_in_policy_as_a_process_decision(registry: Registry, make_draft: Draft) -> None:
    inbox = ready_to_lower(registry, make_draft)
    item = inbox.propose_autonomy_changes()[0]

    result = inbox.decide(item["id"], make_draft(statement="Zamykanie pytań z cytatem: poziom 2."), outcome="approved")

    decision = result["decision"]
    assert (decision["kind"], decision["decision_type"]) == ("process", "autonomy.level_change")
    assert "autonomy:approved" in decision["tags"]
    assert any("30/30" in e["text"] for e in decision["evidence"])
    policy = yaml.safe_load((registry.root / "autonomy.yaml").read_text(encoding="utf-8"))
    entry = next(e for e in policy["policy"] if e["decision_type"] == "finding.auto_close")
    assert (entry["level"], entry["veto_window"]) == (2, "PT4H")
    assert policy["decision"] == decision["id"]
    assert row(autonomy.report(registry), "finding.auto_close")["level"] == 2


def test_rejecting_keeps_the_policy(registry: Registry, make_draft: Draft) -> None:
    inbox = ready_to_lower(registry, make_draft)
    item = inbox.propose_autonomy_changes()[0]

    inbox.decide(item["id"], make_draft(statement="Jeszcze nie."), outcome="rejected")

    assert not (registry.root / "autonomy.yaml").exists()
    assert row(autonomy.report(registry), "finding.auto_close")["level"] == 3


def test_autonomy_item_needs_approved_or_rejected(registry: Registry, make_draft: Draft) -> None:
    inbox = ready_to_lower(registry, make_draft)
    item_id = inbox.propose_autonomy_changes()[0]["id"]

    for outcome in (None, "met", "changes_requested"):
        with pytest.raises(InvalidDecision, match="approved"):
            inbox.decide(item_id, make_draft(), outcome=outcome)


def test_protected_type_cannot_be_lowered_even_from_a_hand_made_item(registry: Registry, make_draft: Draft) -> None:
    inbox = ready_to_lower(registry, make_draft)
    item = inbox.propose_autonomy_changes()[0]
    forged = {**item, "decision_type": "triage"}
    (registry.root / "inbox" / f"{item['id']}.yaml").write_text(yaml.safe_dump(forged), encoding="utf-8")
    before = len(registry.decisions())

    with pytest.raises(InvalidDecision, match="triage"):
        inbox.decide(item["id"], make_draft(statement="Triaż automatem."), outcome="approved")

    assert len(registry.decisions()) == before
    assert not (registry.root / "autonomy.yaml").exists()
    assert inbox.get(item["id"])["status"] == "open"


def test_decided_autonomy_item_is_closed(registry: Registry, make_draft: Draft) -> None:
    inbox = ready_to_lower(registry, make_draft)
    item_id = inbox.propose_autonomy_changes()[0]["id"]
    inbox.decide(item_id, make_draft(statement="Tak."), outcome="approved")

    with pytest.raises(ItemClosed):
        inbox.decide(item_id, make_draft(statement="Jeszcze raz."), outcome="approved")
