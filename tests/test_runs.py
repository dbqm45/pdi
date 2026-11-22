"""Przebiegi agentów (DI Team T1, kontrakt 0.15.0): run.started / run.progress / run.finished od tf."""

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from pdi.contract import errors as contract_errors
from pdi.contract import load as contract_load
from pdi.inbox import Inbox, InvalidEvent
from pdi.registry import Registry
from pdi.runs import RunStore

CONTRACT = Path(__file__).resolve().parents[1] / "contract" / "examples"
OLA = {"name": "Ola", "kind": "human"}


def event(kind: str, event_id: str, at: str, **payload: Any) -> dict[str, Any]:
    return {
        "id": event_id,
        "type": f"run.{kind}",
        "occurred_at": at,
        "source": "tf",
        "contract_version": "0.15.1",
        "payload": {"run": "run-1", "phase": "delivery", **payload},
    }


def started(**payload: Any) -> dict[str, Any]:
    base = {"started_by": OLA, "trigger": "manual", "agent": "jan", "change": "CHG-12", "task": "TSK-57"}
    return event("started", "evt-run-start", "2026-11-22T09:00:00Z", **{**base, **payload})


def progress(event_id: str = "evt-run-p1", at: str = "2026-11-22T09:10:00Z", **payload: Any) -> dict[str, Any]:
    return event("progress", event_id, at, **{"status": "in_progress", "activity": "uruchamia testy", **payload})


def finished(**payload: Any) -> dict[str, Any]:
    review = {"url": "https://github.com/acme/pay/pull/88", "status": "open", "ai_verdict": "approved", "risk": "low"}
    base = {"outcome": "done", "cost_usd": 3.1, "duration_s": 2520, "message": "cięcie gotowe", "review": review}
    return event("finished", "evt-run-end", "2026-11-22T09:42:00Z", **{**base, **payload})


@pytest.fixture
def inbox(registry: Registry) -> Inbox:
    return Inbox(registry)


def test_the_test_events_follow_the_contract() -> None:
    for e in (started(), progress(), finished()):
        assert contract_errors("event", e) == []
    for name in ("run.started", "run.progress", "run.finished"):
        assert contract_errors("event", json.loads((CONTRACT / f"event-{name}.json").read_text(encoding="utf-8"))) == []
    assert "run.started" in contract_load("event")["properties"]["type"]["enum"]


def test_a_run_from_start_to_finish_is_one_record(inbox: Inbox, registry: Registry) -> None:
    assert inbox.receive(started())["status"] == "recorded"
    assert inbox.receive(progress())["run"]["activity"] == "uruchamia testy"
    result = inbox.receive(finished())

    run = RunStore(registry).get("run-1")
    assert result["status"] == "recorded" and result["item"] is None
    assert run is not None
    assert {k: run[k] for k in ("change", "task", "phase", "agent", "trigger", "started_by", "status")} == {
        "change": "CHG-12",
        "task": "TSK-57",
        "phase": "delivery",
        "agent": "jan",
        "trigger": "manual",
        "started_by": OLA,
        "status": "done",
    }
    assert (run["started_at"], run["finished_at"], run["cost_usd"], run["result"]) == (
        "2026-11-22T09:00:00Z",
        "2026-11-22T09:42:00Z",
        3.1,
        "cięcie gotowe",
    )
    assert run["review"]["ai_verdict"] == "approved"
    assert inbox.items() == []  # przebieg nie jest pozycją skrzynki


def test_a_manual_session_needs_no_change(inbox: Inbox, registry: Registry) -> None:
    e = started()
    del e["payload"]["change"], e["payload"]["task"]

    inbox.receive(e)

    run = RunStore(registry).get("run-1")
    assert run is not None and "change" not in run and run["status"] == "running"


def test_the_same_event_twice_is_a_duplicate(inbox: Inbox) -> None:
    inbox.receive(started())

    again = inbox.receive(started())

    assert again["status"] == "duplicate"


def test_late_progress_does_not_reopen_a_finished_run(inbox: Inbox, registry: Registry) -> None:
    inbox.receive(finished())
    inbox.receive(progress(status="in_progress", activity="spóźniony postęp"))

    run = RunStore(registry).get("run-1")
    assert run is not None
    assert run["status"] == "done"
    assert run["updated_at"] == "2026-11-22T09:42:00Z"
    assert "started_at" not in run  # start jeszcze nie przyszedł; przyjdzie i uzupełni


def test_progress_without_run_is_refused(inbox: Inbox) -> None:
    e = progress()
    del e["payload"]["run"]

    with pytest.raises(InvalidEvent, match="run"):
        inbox.receive(e)


def test_only_tf_may_send_run_events(inbox: Inbox) -> None:
    with pytest.raises(InvalidEvent, match="source"):
        inbox.receive({**started(), "source": "shipscope"})


def test_runs_are_listed_newest_first_and_by_status(inbox: Inbox, registry: Registry) -> None:
    inbox.receive(started())
    other = event("started", "evt-run2-start", "2026-11-22T10:00:00Z", started_by=OLA, trigger="pdi")
    other["payload"]["run"] = "run-2"
    inbox.receive(other)
    inbox.receive(finished())

    store = RunStore(registry)
    assert [r["run"] for r in store.list()] == ["run-2", "run-1"]
    assert [r["run"] for r in store.list(status="running")] == ["run-2"]


def test_start_and_finish_are_committed_progress_is_not(tmp_path: Path) -> None:
    root = tmp_path / "rejestr"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    for k, v in (("user.email", "t@example.com"), ("user.name", "t")):
        subprocess.run(["git", "-C", str(root), "config", k, v], check=True)
    inbox = Inbox(Registry(root))

    inbox.receive(started())
    inbox.receive(progress())
    inbox.receive(finished())

    log = subprocess.run(["git", "-C", str(root), "log", "--format=%s"], capture_output=True, text=True, check=True)
    assert log.stdout.splitlines() == ["run run-1 run.finished (done)", "run run-1 run.started"]
