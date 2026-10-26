import hashlib
import hmac
import subprocess
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
import yaml

from pdi.changes import ChangeNotFound
from pdi.contract import errors as contract_errors
from pdi.dispatch import DispatchConfig
from pdi.inbox import BadSignature, Inbox, InvalidEvent, ItemClosed, ItemNotFound, verify_signature
from pdi.registry import InvalidDecision, Registry

Draft = Callable[..., dict[str, Any]]
NOW = datetime(2026, 10, 23, 9, 30, tzinfo=UTC)
SECRET = "sekret-workspace"  # noqa: S105 — sekret testowy


def sign(timestamp: str, body: bytes, secret: str = SECRET) -> str:
    return "v1=" + hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()


def stage_event(**payload: Any) -> dict[str, Any]:
    """`release.stage_changed` w kształcie, jaki wysyła ShipScope (dbqm45/evdt-service-shipscope#109)."""
    return {
        "id": "evt-stage-1",
        "type": "release.stage_changed",
        "occurred_at": "2026-10-23T09:00:00Z",
        "source": "shipscope",
        "contract_version": "0.4.0",
        "payload": {
            "change": "CHG-12",
            "release": "R1",
            "flag": "payment-retry",
            "from_stage": "internal",
            "to_stage": "10%",
            "rollout": 10,
            **payload,
        },
    }


def gate_event(event_id: str = "evt-gate-1", source: str = "tf", **payload: Any) -> dict[str, Any]:
    """`gate.requested` z tf albo ci_for_sdlc (kontrakt 0.4.0)."""
    return {
        "id": event_id,
        "type": "gate.requested",
        "occurred_at": "2026-10-23T09:10:00Z",
        "source": source,
        "contract_version": "0.4.0",
        "payload": {
            "change": "CHG-12",
            "gate": "B1",
            "summary": "Intencja CHG-12 gotowa do akceptacji.",
            "artifact": "intent",
            "url": "https://github.com/dbqm45/sklep/pull/7",
            **payload,
        },
    }


def readiness_event(readiness: str, event_id: str = "evt-ready-1", **payload: Any) -> dict[str, Any]:
    return {
        "id": event_id,
        "type": "readiness.changed",
        "occurred_at": "2026-10-23T09:20:00Z",
        "source": "ci_for_sdlc",
        "contract_version": "0.4.0",
        "payload": {"change": "CHG-12", "readiness": readiness, **payload},
    }


def released_event(event_id: str = "evt-rel-1", **payload: Any) -> dict[str, Any]:
    return {
        "id": event_id,
        "type": "feature.released",
        "occurred_at": "2026-10-23T09:05:00Z",
        "source": "shipscope",
        "contract_version": "0.4.0",
        "payload": {
            "change": "CHG-12",
            "release": "R1",
            "tasks": ["TSK-57", "TSK-58"],
            "released_at": "2026-10-23T09:04:00Z",
            "environment": "prod",
            **payload,
        },
    }


@pytest.fixture
def inbox(registry: Registry) -> Inbox:
    return Inbox(registry)


# --- podpis ---


def test_valid_signature_passes() -> None:
    ts = str(int(NOW.timestamp()))
    body = b'{"id":"x"}'

    verify_signature(SECRET, ts, body, sign(ts, body), now=NOW)


@pytest.mark.parametrize(
    ("timestamp_shift", "signature"),
    [
        (0, "v1=" + "0" * 64),
        (0, "deadbeef"),
        (0, None),
        (-301, "ok"),
        (301, "ok"),
    ],
    ids=["zly-hmac", "bez-v1", "brak", "stary", "z-przyszlosci"],
)
def test_bad_or_stale_signature_is_refused(timestamp_shift: int, signature: str | None) -> None:
    ts = str(int((NOW + timedelta(seconds=timestamp_shift)).timestamp()))
    body = b'{"id":"x"}'
    header = sign(ts, body) if signature == "ok" else signature

    with pytest.raises(BadSignature):
        verify_signature(SECRET, ts, body, header, now=NOW)


def test_signature_with_other_secret_or_body_is_refused() -> None:
    ts = str(int(NOW.timestamp()))

    with pytest.raises(BadSignature):
        verify_signature(SECRET, ts, b"{}", sign(ts, b"{}", "inny"), now=NOW)
    with pytest.raises(BadSignature):
        verify_signature(SECRET, ts, b"{ }", sign(ts, b"{}"), now=NOW)


def test_non_numeric_timestamp_is_refused() -> None:
    with pytest.raises(BadSignature):
        verify_signature(SECRET, "wczoraj", b"{}", sign("wczoraj", b"{}"), now=NOW)


# --- przyjęcie ---


def test_stage_change_becomes_open_gate_item(inbox: Inbox, registry: Registry) -> None:
    result = inbox.receive(stage_event())

    assert result["status"] == "created"
    item = result["item"]
    assert item["id"] == "evt-stage-1"
    assert (item["kind"], item["status"], item["change"], item["release"]) == ("gate", "open", "CHG-12", "R1")
    assert "payment-retry" in item["summary"] and "10%" in item["summary"]
    assert item["received_at"] == "2026-10-23T09:30:00Z"
    stored = yaml.safe_load((registry.root / "inbox" / "evt-stage-1.yaml").read_text(encoding="utf-8"))
    assert stored["event"] == stage_event()


def test_mvp_release_becomes_impact_review_item(inbox: Inbox) -> None:
    item = inbox.receive(released_event())["item"]

    assert (item["kind"], item["change"], item["release"]) == ("impact_review", "CHG-12", "R1")
    assert "MVP" in item["summary"]


@pytest.mark.parametrize("payload", [{"release": "R2"}, {"release": None}], ids=["R2", "bez-linii"])
def test_release_other_than_mvp_only_updates_the_change(inbox: Inbox, payload: dict[str, Any]) -> None:
    event = released_event(**payload)
    if payload["release"] is None:
        del event["payload"]["release"]

    result = inbox.receive(event)

    assert result == {"status": "recorded", "item": None}
    assert inbox.items() == []
    assert inbox.changes.get("CHG-12")["releases"] == {payload["release"] or "all": "2026-10-23T09:04:00Z"}


def test_same_event_twice_keeps_one_item(inbox: Inbox) -> None:
    inbox.receive(stage_event())

    again = inbox.receive(stage_event())

    assert again["status"] == "duplicate"
    assert len(inbox.items()) == 1


@pytest.mark.parametrize(
    ("change", "match"),
    [
        ({"source": "tf"}, "source"),
        ({"type": "gate.requested", "payload": {"change": "CHG-1", "gate": "spec", "summary": "s"}}, "type"),
        ({"payload": {"change": "CHG-12", "to_stage": "10%"}}, "flag"),
        ({"id": "../../decisions/x"}, "id"),
        ({"id": "a" * 129}, "id"),
    ],
    ids=["inne-zrodlo", "inny-typ", "zly-schemat", "sciezka-w-id", "za-dlugie-id"],
)
def test_bad_events_are_refused(inbox: Inbox, registry: Registry, change: dict[str, Any], match: str) -> None:
    with pytest.raises(InvalidEvent, match=match):
        inbox.receive({**stage_event(), **change})

    assert not (registry.root / "inbox").exists() or list((registry.root / "inbox").iterdir()) == []


def test_items_lists_open_first_by_default_and_all_on_request(inbox: Inbox, make_draft: Draft) -> None:
    inbox.receive(stage_event())
    inbox.receive(released_event())
    inbox.decide("evt-rel-1", make_draft(kind="other"))

    assert [i["id"] for i in inbox.items()] == ["evt-stage-1"]
    assert {i["id"] for i in inbox.items(status=None)} == {"evt-stage-1", "evt-rel-1"}
    assert [i["id"] for i in inbox.items(status="decided")] == ["evt-rel-1"]


# --- decyzja ---


def test_deciding_gate_records_gate_decision_linked_to_change(
    inbox: Inbox, registry: Registry, make_draft: Draft
) -> None:
    inbox.receive(stage_event())

    result = inbox.decide(
        "evt-stage-1",
        make_draft(statement="CHG-12: payment-retry przechodzi na 100%.", kind="product"),
        outcome="approved",
    )

    decision = result["decision"]
    assert decision["id"] == "DEC-0001"
    assert decision["kind"] == "gate"
    assert decision["links"]["chg"] == "CHG-12"
    assert "gate:approved" in decision["tags"]
    item = result["item"]
    assert (item["status"], item["decision"], item["outcome"]) == ("decided", "DEC-0001", "approved")
    assert registry.get("DEC-0001")["links"] == {"chg": "CHG-12"}
    assert inbox.get("evt-stage-1")["status"] == "decided"


def test_gate_needs_an_outcome(inbox: Inbox, make_draft: Draft) -> None:
    inbox.receive(stage_event())

    with pytest.raises(InvalidDecision, match="outcome"):
        inbox.decide("evt-stage-1", make_draft())
    with pytest.raises(InvalidDecision, match="outcome"):
        inbox.decide("evt-stage-1", make_draft(), outcome="maybe")


def test_impact_review_records_product_decision(inbox: Inbox, make_draft: Draft) -> None:
    inbox.receive(released_event())

    result = inbox.decide(
        "evt-rel-1",
        make_draft(statement="MVP CHG-12 zostaje; wracamy po 30 dniach.", kind="gate", links={"tsk": "TSK-57"}),
    )

    decision = result["decision"]
    assert decision["kind"] == "product"
    assert decision["links"] == {"tsk": "TSK-57", "chg": "CHG-12"}
    assert "outcome" not in result["item"]


def test_link_to_another_change_is_refused(inbox: Inbox, make_draft: Draft) -> None:
    inbox.receive(released_event())

    with pytest.raises(InvalidDecision, match="CHG-12"):
        inbox.decide("evt-rel-1", make_draft(links={"chg": "CHG-99"}))


def test_decided_item_cannot_be_decided_again(inbox: Inbox, make_draft: Draft) -> None:
    inbox.receive(released_event())
    inbox.decide("evt-rel-1", make_draft())

    with pytest.raises(ItemClosed, match="DEC-0001"):
        inbox.decide("evt-rel-1", make_draft(statement="Inna."))


def test_unknown_item_raises(inbox: Inbox, make_draft: Draft) -> None:
    with pytest.raises(ItemNotFound, match="list_inbox"):
        inbox.decide("evt-nie-ma", make_draft())
    with pytest.raises(ItemNotFound):
        inbox.get("../decisions")


def test_invalid_decision_leaves_item_open(inbox: Inbox, make_draft: Draft) -> None:
    inbox.receive(released_event())

    with pytest.raises(InvalidDecision):
        inbox.decide("evt-rel-1", make_draft(success_metric={"metric": "marża"}))

    assert inbox.get("evt-rel-1")["status"] == "open"


def test_receive_and_decide_commit_in_git_registry(
    tmp_path: Path, make_draft: Draft, monkeypatch: pytest.MonkeyPatch
) -> None:
    for var in ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"):
        monkeypatch.setenv(var, "t")
    for var in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"):
        monkeypatch.setenv(var, "t@example.com")
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    inbox = Inbox(Registry(root, clock=lambda: NOW))

    inbox.receive(stage_event())
    inbox.decide("evt-stage-1", make_draft(), outcome="changes_requested")

    log = subprocess.run(
        ["git", "-C", str(root), "log", "--format=%s"], check=True, capture_output=True, text=True
    ).stdout.splitlines()
    assert log[0] == "inbox evt-stage-1: zamknięta decyzją DEC-0001"
    assert log[1].startswith("DEC-0001:")
    assert log[2].startswith("inbox evt-stage-1: CHG-12")
    status = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain"], check=True, capture_output=True, text=True
    )
    assert status.stdout == ""


# --- F4: bramki z tf i ci_for_sdlc, stan zmiany, uruchomienie fazy ---


class FakeGitHub:
    def __init__(self, status: int = 204) -> None:
        self.status = status
        self.calls: list[dict[str, Any]] = []

    def __call__(self, url: str, headers: dict[str, str], body: bytes) -> int:
        import json

        self.calls.append({"url": url, **json.loads(body)})
        return self.status


def dispatching(registry: Registry, github: FakeGitHub) -> Inbox:
    cfg = DispatchConfig(repo="dbqm45/sklep", token="ghs_t")  # noqa: S106 — token testowy
    return Inbox(registry, dispatch=cfg, post=github)


def test_gate_request_from_tf_becomes_gate_item_and_waits_on_change(inbox: Inbox) -> None:
    result = inbox.receive(gate_event())

    item = result["item"]
    assert (item["kind"], item["gate"], item["source"]) == ("gate", "B1", "tf")
    assert item["summary"] == "Intencja CHG-12 gotowa do akceptacji."
    assert (item["artifact"], item["url"]) == ("intent", "https://github.com/dbqm45/sklep/pull/7")
    assert item["missing_before"] == []
    state = inbox.changes.get("CHG-12")
    assert state["waiting"] == ["B1"]


def test_out_of_order_request_is_shown_not_refused(inbox: Inbox) -> None:
    item = inbox.receive(gate_event(gate="B3", summary="Plan cięć."))["item"]

    assert item["missing_before"] == ["B1", "B2"]
    assert "poza kolejnością: brak B1, B2" in item["summary"]


def test_newer_request_for_same_gate_supersedes_open_item(inbox: Inbox) -> None:
    inbox.receive(gate_event("evt-gate-1"))

    inbox.receive(gate_event("evt-gate-2", summary="Intencja po poprawkach."))

    assert [i["id"] for i in inbox.items()] == ["evt-gate-2"]
    old = inbox.get("evt-gate-1")
    assert (old["status"], old["superseded_by"]) == ("superseded", "evt-gate-2")


def test_superseded_item_cannot_be_decided(inbox: Inbox, make_draft: Draft) -> None:
    inbox.receive(gate_event("evt-gate-1"))
    inbox.receive(gate_event("evt-gate-2"))

    with pytest.raises(ItemClosed, match="evt-gate-2"):
        inbox.decide("evt-gate-1", make_draft(), outcome="approved")


def test_approving_gate_moves_change_writes_gate_decided_and_dispatches(registry: Registry, make_draft: Draft) -> None:
    github = FakeGitHub()
    inbox = dispatching(registry, github)
    inbox.receive(gate_event())

    result = inbox.decide("evt-gate-1", make_draft(), outcome="approved")

    assert result["decision"]["kind"] == "gate"
    assert {"gate:approved", "bramka:B1"} <= set(result["decision"]["tags"])
    state = result["change"]
    assert (state["approved"], state["waiting"]) == ({"B1": "DEC-0001"}, [])
    assert state["dispatch"]["status"] == "sent"
    assert (state["dispatch"]["phase"], state["dispatch"]["gate"]) == ("requirements", "B1")
    assert github.calls[0]["inputs"]["phase"] == "requirements"
    assert github.calls[0]["inputs"]["decision"] == "DEC-0001"
    event = result["event"]
    assert contract_errors("event", event) == []
    assert (event["type"], event["source"]) == ("gate.decided", "pdi")
    assert event["payload"] == {"change": "CHG-12", "gate": "B1", "outcome": "approved", "decision": "DEC-0001"}
    assert (registry.root / "outbox" / f"{event['id']}.json").is_file()


def test_changes_requested_dispatches_rework_of_same_phase(registry: Registry, make_draft: Draft) -> None:
    github = FakeGitHub()
    inbox = dispatching(registry, github)
    inbox.receive(gate_event(gate="B2", summary="Wymagania."))

    inbox.decide("evt-gate-1", make_draft(), outcome="changes_requested")

    assert (github.calls[0]["inputs"]["phase"], github.calls[0]["inputs"]["rework"]) == ("requirements", "true")


def test_gate_without_next_phase_dispatches_nothing(registry: Registry, make_draft: Draft) -> None:
    github = FakeGitHub()
    inbox = dispatching(registry, github)
    inbox.receive(gate_event(gate="B4", summary="Gotowość do wydania."))

    result = inbox.decide("evt-gate-1", make_draft(), outcome="approved")

    assert github.calls == []
    assert "dispatch" not in result["change"]


def test_failed_dispatch_keeps_decision_and_can_be_retried(registry: Registry, make_draft: Draft) -> None:
    github = FakeGitHub(status=500)
    inbox = dispatching(registry, github)
    inbox.receive(gate_event())

    result = inbox.decide("evt-gate-1", make_draft(), outcome="approved")

    assert registry.get("DEC-0001")["kind"] == "gate"
    assert result["change"]["dispatch"]["status"] == "failed"
    assert "500" in result["change"]["dispatch"]["error"]

    github.status = 204
    retried = inbox.retry_dispatch("CHG-12")

    assert retried["dispatch"]["status"] == "sent"
    assert github.calls[-1]["inputs"]["phase"] == "requirements"
    assert inbox.changes.get("CHG-12")["dispatch"]["status"] == "sent"


def test_retry_without_failed_dispatch_is_refused(inbox: Inbox, make_draft: Draft) -> None:
    inbox.receive(gate_event())

    with pytest.raises(InvalidDecision, match="nie ma"):
        inbox.retry_dispatch("CHG-12")
    with pytest.raises(ChangeNotFound):
        inbox.retry_dispatch("CHG-99")


def test_without_dispatch_config_phase_is_skipped(inbox: Inbox, make_draft: Draft) -> None:
    inbox.receive(gate_event())

    result = inbox.decide("evt-gate-1", make_draft(), outcome="approved")

    assert result["change"]["dispatch"]["status"] == "skipped"


def test_rejected_change_refuses_next_gate_before_recording(
    inbox: Inbox, registry: Registry, make_draft: Draft
) -> None:
    inbox.receive(gate_event())
    inbox.decide("evt-gate-1", make_draft(), outcome="rejected")
    inbox.receive(gate_event("evt-gate-2", gate="B2", summary="Wymagania."))

    with pytest.raises(InvalidDecision, match="rejected"):
        inbox.decide("evt-gate-2", make_draft(statement="Inna."), outcome="approved")

    assert len(registry.decisions()) == 1
    assert inbox.changes.get("CHG-12")["status"] == "rejected"


def test_readiness_ready_asks_for_approve_for_implementation(inbox: Inbox) -> None:
    result = inbox.receive(readiness_event("ready", open_questions=0))

    item = result["item"]
    assert (item["gate"], item["source"]) == ("approve-for-implementation", "ci_for_sdlc")
    assert "Approve for implementation" in item["summary"]
    assert inbox.changes.get("CHG-12")["readiness"] == "ready"


@pytest.mark.parametrize("readiness", ["not_ready", "drift"])
def test_readiness_other_than_ready_only_updates_the_change(inbox: Inbox, readiness: str) -> None:
    result = inbox.receive(readiness_event(readiness))

    assert result == {"status": "recorded", "item": None}
    assert inbox.changes.get("CHG-12")["readiness"] == readiness


def test_ci_for_sdlc_may_ask_for_a_gate_too(inbox: Inbox) -> None:
    item = inbox.receive(gate_event(source="ci_for_sdlc", gate="approve-for-implementation", summary="Gotowe."))["item"]

    assert item["source"] == "ci_for_sdlc"


@pytest.mark.parametrize(
    ("event", "match"),
    [
        (lambda: {**gate_event(), "source": "shipscope"}, "source"),
        (lambda: {**readiness_event("ready"), "source": "tf"}, "source"),
        (lambda: {**gate_event(), "source": "pdi"}, "source"),
    ],
    ids=["shipscope-bramka", "tf-gotowosc", "od-siebie"],
)
def test_types_are_accepted_only_from_their_senders(
    inbox: Inbox, event: Callable[[], dict[str, Any]], match: str
) -> None:
    with pytest.raises(InvalidEvent, match=match):
        inbox.receive(event())


def test_impact_review_finishes_the_change(inbox: Inbox, make_draft: Draft) -> None:
    inbox.receive(released_event())

    result = inbox.decide("evt-rel-1", make_draft())

    assert result["change"]["status"] == "done"
    assert result["change"]["releases"] == {"R1": "2026-10-23T09:04:00Z"}


def test_stage_gate_is_logged_on_the_change_without_moving_the_chain(inbox: Inbox, make_draft: Draft) -> None:
    inbox.receive(stage_event())

    result = inbox.decide("evt-stage-1", make_draft(), outcome="approved")

    assert result["change"]["approved"] == {"stage:payment-retry:10%": "DEC-0001"}
    assert result["event"]["payload"]["gate"] == "stage:payment-retry:10%"


def test_repeated_recorded_event_is_a_duplicate(inbox: Inbox) -> None:
    inbox.receive(readiness_event("drift"))

    again = inbox.receive(readiness_event("drift"))

    assert again == {"status": "duplicate", "item": None}
    assert len(inbox.changes.get("CHG-12")["history"]) == 1
