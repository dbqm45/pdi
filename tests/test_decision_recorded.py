"""A2b: decyzja podjęta w ci_for_sdlc (`decision.recorded`, kontrakt 0.7.0) w rejestrze pdi (plan-a2b-pdi, D-A2)."""

from typing import Any

import pytest
import yaml

from pdi import autonomy
from pdi import inbox as inbox_module
from pdi.inbox import Inbox, InvalidEvent
from pdi.registry import Registry


def recorded_event(event_id: str = "evt-dec-1", **payload: Any) -> dict[str, Any]:
    """`decision.recorded` z ci_for_sdlc: człowiek zatwierdził bez zmian propozycję zamknięcia pytania."""
    base: dict[str, Any] = {
        "decision_type": "finding.auto_close",
        "ref": "PAY-12/COV-001",
        "url": "http://localhost:4317/items/PAY-12#COV-001",
        "statement": "Pytanie o format daty zamknięte odpowiedzią z Confluence.",
        "decided_by": "anna.po",
        "drafted_by": "ai",
        "draft_edited": False,
        "evidence": [{"text": "Daty w API zapisujemy w ISO 8601 (UTC).", "source_url": "https://wiki/x/API"}],
        "change": "CHG-12",
    }
    base.update(payload)
    return {
        "id": event_id,
        "type": "decision.recorded",
        "occurred_at": "2026-10-23T09:25:00Z",
        "source": "ci_for_sdlc",
        "contract_version": "0.7.0",
        "payload": {k: v for k, v in base.items() if v is not None},
    }


@pytest.fixture
def inbox(registry: Registry) -> Inbox:
    return Inbox(registry)


def test_recorded_decision_lands_in_registry_without_inbox_item(inbox: Inbox, registry: Registry) -> None:
    result = inbox.receive(recorded_event())

    assert (result["status"], result["item"]) == ("recorded", None)
    d = registry.get(result["decision"])
    assert (d["decision_type"], d["drafted_by"], d["draft_edited"]) == ("finding.auto_close", "ai", False)
    assert d["statement"].startswith("Pytanie o format daty")
    assert d["decided_by"] == "anna.po"
    assert d["source"] == {
        "kind": "ci_for_sdlc",
        "url": "http://localhost:4317/items/PAY-12#COV-001",
        "excerpt": "PAY-12/COV-001",
    }
    assert d["evidence"] == [
        {
            "text": "Daty w API zapisujemy w ISO 8601 (UTC).",
            "source_url": "https://wiki/x/API",
            "epistemic_status": "observation",
        }
    ]
    assert d["links"] == {"chg": "CHG-12"}
    assert {"ci_for_sdlc", "ref:PAY-12/COV-001", "event:evt-dec-1", "typ:finding.auto_close"} <= set(d["tags"])
    assert "finding.auto_close" in d["why"] and "PAY-12/COV-001" in d["why"]
    assert inbox.items() == []


def test_same_event_twice_is_duplicate_with_the_same_decision(inbox: Inbox, registry: Registry) -> None:
    first = inbox.receive(recorded_event())
    again = inbox.receive(recorded_event())

    assert again["status"] == "duplicate"
    assert again["decision"] == first["decision"]
    assert len(registry.decisions()) == 1


def test_ref_without_url_is_the_source(inbox: Inbox, registry: Registry) -> None:
    d = registry.get(inbox.receive(recorded_event(url=None))["decision"])

    assert d["source"]["url"] == "PAY-12/COV-001"


def test_sender_records_only_its_decision_types(inbox: Inbox, registry: Registry) -> None:
    with pytest.raises(InvalidEvent, match="flag.stage_advance"):
        inbox.receive(recorded_event(decision_type="flag.stage_advance"))

    assert registry.decisions() == []


def test_protected_type_is_never_recorded_as_automation(inbox: Inbox, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(inbox_module.RECORDABLE, "ci_for_sdlc", ("triage",))  # nawet gdyby lista nadawcy go miała
    auto = {"level": 1, "rule": "x"}

    with pytest.raises(InvalidEvent, match="chroniony"):
        inbox.receive(recorded_event(decision_type="triage", automation=auto, draft_edited=None))


def test_automation_below_policy_is_recorded_but_flagged(inbox: Inbox, registry: Registry) -> None:
    auto = {"level": 1, "rule": "odpowiedź znaleziona w źródle, z cytatem"}

    result = inbox.receive(recorded_event(automation=auto, draft_edited=None, decided_by="ci_for_sdlc"))

    d = registry.get(result["decision"])
    assert d["automation"] == auto
    assert "draft_edited" not in d
    assert "autonomy:outside-policy" in d["tags"]
    assert "poziom 3" in result["warning"]
    assert not (registry.root / "autonomy.yaml").exists(), "zapis nie zmienia polityki"


def test_automation_within_policy_has_no_flag(inbox: Inbox, registry: Registry) -> None:
    registry.root.mkdir(parents=True, exist_ok=True)
    policy = {"policy": [{"decision_type": "finding.auto_close", "level": 1}]}
    (registry.root / autonomy.POLICY_FILE).write_text(yaml.safe_dump(policy), encoding="utf-8")
    auto = {"level": 1, "rule": "x"}

    result = inbox.receive(recorded_event(automation=auto, draft_edited=None, decided_by="ci_for_sdlc"))

    assert "autonomy:outside-policy" not in registry.get(result["decision"])["tags"]
    assert "warning" not in result or "poziom" not in result["warning"]


def test_reopening_supersedes_the_decision_of_the_same_ref(inbox: Inbox, registry: Registry) -> None:
    first = inbox.receive(recorded_event())["decision"]

    result = inbox.receive(
        recorded_event(
            "evt-dec-2",
            statement="Pytanie o format daty otwarte ponownie: cytat dotyczy innego API.",
            draft_edited=True,
            supersedes=first,
        )
    )

    new = registry.get(result["decision"])
    assert new["supersedes"] == first
    assert registry.get(first)["status"] == "superseded"


def test_superseding_another_ref_or_foreign_decision_is_refused(
    inbox: Inbox, registry: Registry, make_draft: Any
) -> None:
    first = inbox.receive(recorded_event())["decision"]
    foreign = registry.record(make_draft(statement="Decyzja z Claude."))["id"]

    with pytest.raises(InvalidEvent, match="PAY-12/COV-002"):
        inbox.receive(recorded_event("evt-dec-2", ref="PAY-12/COV-002", supersedes=first))
    with pytest.raises(InvalidEvent, match=foreign):
        inbox.receive(recorded_event("evt-dec-3", supersedes=foreign))
    with pytest.raises(InvalidEvent, match="DEC-99"):
        inbox.receive(recorded_event("evt-dec-4", supersedes="DEC-99"))
    assert registry.get(first)["status"] == "recorded"


def test_acceptance_counter_counts_recorded_decisions(inbox: Inbox, registry: Registry) -> None:
    for n in range(30):
        inbox.receive(recorded_event(f"evt-{n}", ref=f"PAY-12/COV-{n:03d}", statement=f"Zamknięte {n}."))

    row = next(r for r in autonomy.report(registry) if r["decision_type"] == "finding.auto_close")
    assert (row["measured"], row["unedited"]) == (30, 30)
    assert row["recommendation"]["action"] == "lower"


def test_other_senders_cannot_record_decisions(inbox: Inbox) -> None:
    event = {**recorded_event(), "source": "shipscope"}

    with pytest.raises(InvalidEvent, match="shipscope"):
        inbox.receive(event)
