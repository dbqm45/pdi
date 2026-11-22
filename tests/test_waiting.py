"""„Czeka na Ciebie” (krok 17, CH2): nowa pozycja skrzynki → podpisana wiadomość do DI Channels, terminy z OM1."""

import hashlib
import hmac
import json
from datetime import date
from typing import Any

from pdi.inbox import Inbox
from pdi.registry import Registry
from pdi.waiting import ChannelsConfig, business_days, due_date, message, notify
from tests.test_inbox import gate_event, stage_event

SECRET = "sekret-kanalow"  # noqa: S105 — sekret testowy
CONFIG = ChannelsConfig(url="https://channels.example.com", secret=SECRET)


class Recorder:
    def __init__(self, status: int = 200) -> None:
        self.calls: list[tuple[str, dict[str, str], bytes]] = []
        self.status = status

    def __call__(self, url: str, headers: dict[str, str], body: bytes) -> int:
        self.calls.append((url, headers, body))
        return self.status


def test_w01_deadlines_follow_om1() -> None:
    assert business_days("gate", "B1") == 2
    assert business_days("gate", "B3") == 5
    assert business_days("gate", "B5") == 1
    assert business_days("gate", "approve-for-implementation") == 2
    assert business_days("gate", "stage:payment-retry:prod") == 1
    assert business_days("gate", "stage:payment-retry:10%") == 2
    assert business_days("impact_review", None) == 5
    assert business_days("autonomy", None) == 5
    assert business_days("problem", None) == 2


def test_w02_weekends_do_not_count() -> None:
    assert due_date(date(2026, 11, 20), 1) == date(2026, 11, 23)  # piątek + 1 → poniedziałek
    assert due_date(date(2026, 11, 22), 2) == date(2026, 11, 24)  # niedziela + 2 → wtorek
    assert due_date(date(2026, 11, 23), 5) == date(2026, 11, 30)


def test_w03_message_has_what_when_where_and_no_token() -> None:
    item = {
        "id": "evt-gate-1",
        "kind": "gate",
        "gate": "B3",
        "change": "CHG-12",
        "summary": "Plan CHG-12",
        "received_at": "2026-11-23T09:00:00Z",
    }
    msg = message(item, ChannelsConfig(url=None, console_url="http://127.0.0.1:8788"))
    assert msg["type"] == "gate.waiting"
    assert msg["due"] == "2026-11-30" and msg["business_days"] == 5
    assert msg["url"] == "http://127.0.0.1:8788/inbox/evt-gate-1"
    assert "?t=" not in json.dumps(msg)
    assert "url" not in message(item, ChannelsConfig(url=None))


def test_w04_signed_post_to_channels() -> None:
    post = Recorder()
    item = {"id": "evt-gate-1", "kind": "gate", "gate": "B1", "received_at": "2026-11-23T09:00:00Z"}
    result = notify(CONFIG, item, at="2026-11-23T09:00:00Z", post=post, now=1_700_000_000)
    assert result["status"] == "sent" and result["due"] == "2026-11-25"
    url, headers, body = post.calls[0]
    assert url == "https://channels.example.com/pdi/waiting"
    expected = "v1=" + hmac.new(SECRET.encode(), b"1700000000." + body, hashlib.sha256).hexdigest()
    assert headers["x-pdi-signature"] == expected and headers["x-pdi-event"] == "gate.waiting"


def test_w05_failure_is_recorded_not_raised() -> None:
    item = {"id": "x", "kind": "gate", "gate": "B1", "received_at": "2026-11-23T09:00:00Z"}
    assert notify(CONFIG, item, at="t", post=Recorder(500))["status"] == "failed"
    assert notify(ChannelsConfig(url=None), item, at="t")["status"] == "skipped"


def test_w06_new_gate_item_notifies_once(registry: Registry) -> None:
    post = Recorder()
    inbox = Inbox(registry, channels=CONFIG, channels_post=post)
    first = inbox.receive(gate_event())
    assert first["status"] == "created"
    assert first["item"]["waiting_notice"]["status"] == "sent"
    assert inbox.get("evt-gate-1")["waiting_notice"]["status"] == "sent"
    again = inbox.receive(gate_event())
    assert again["status"] == "duplicate"
    assert len(post.calls) == 1
    sent: dict[str, Any] = json.loads(post.calls[0][2])
    assert sent["item"] == "evt-gate-1" and sent["change"] == "CHG-12" and sent["gate"] == "B1"


def test_w07_stage_gate_to_prod_is_one_day(registry: Registry) -> None:
    post = Recorder()
    Inbox(registry, channels=CONFIG, channels_post=post).receive(stage_event(to_stage="prod", rollout=100))
    assert json.loads(post.calls[0][2])["business_days"] == 1


def test_w08_without_channels_url_items_are_unchanged(registry: Registry) -> None:
    result = Inbox(registry).receive(gate_event())
    assert "waiting_notice" not in result["item"]


# --- terminy (N3, OM1 §4–§5); FIXED_NOW z conftest: piątek 2026-10-23 09:30 UTC ---

from datetime import UTC, datetime  # noqa: E402

from pdi.changes import ChangeStore  # noqa: E402
from pdi.waiting import stages  # noqa: E402
from tests.conftest import draft  # noqa: E402


def at(text: str) -> datetime:
    return datetime.fromisoformat(text).replace(tzinfo=UTC)


def test_w09_stages_of_a_two_day_gate_skip_the_weekend() -> None:
    item = {"kind": "gate", "gate": "B1", "received_at": "2026-10-23T09:30:00Z"}
    assert stages(item) == [
        ("reminder", at("2026-10-26T09:30:00")),
        ("due_today", at("2026-10-27T00:00:00")),
        ("overdue", at("2026-10-27T09:30:00")),
        ("paused", at("2026-10-29T09:30:00")),
        ("review", at("2026-11-04T09:30:00")),
    ]


def test_w10_a_one_day_item_is_reminded_at_half_the_deadline() -> None:
    item = {"kind": "gate", "gate": "B5", "received_at": "2026-10-23T09:30:00Z"}
    assert [s for s, _ in stages(item)] == ["reminder", "overdue", "paused", "review"]
    assert stages(item)[0][1] == at("2026-10-23T21:30:00")
    late = {"kind": "gate", "gate": "B5", "received_at": "2026-10-23T15:00:00Z"}
    assert stages(late)[0][1] == at("2026-10-26T03:00:00")  # wypada w sobotę → poniedziałek


def test_w11_only_the_latest_stage_is_sent_and_only_once(registry: Registry) -> None:
    post = Recorder()
    inbox = Inbox(registry, channels=CONFIG, channels_post=post)
    inbox.receive(gate_event())
    assert inbox.check_deadlines(now=at("2026-10-26T08:00:00")) == []
    done = inbox.check_deadlines(now=at("2026-10-27T10:00:00"))
    assert [d["stage"] for d in done] == ["overdue"]
    notices = inbox.get("evt-gate-1")["deadline_notices"]
    assert notices["reminder"]["status"] == "superseded" and notices["due_today"]["status"] == "superseded"
    assert notices["overdue"]["status"] == "sent"
    assert inbox.check_deadlines(now=at("2026-10-27T11:00:00")) == []
    stages_sent = [json.loads(body)["stage"] for _, _, body in post.calls]
    assert stages_sent == ["new", "overdue"]
    assert json.loads(post.calls[-1][2])["id"] == "waiting-evt-gate-1-overdue"


def test_w12_twice_the_deadline_pauses_the_change_and_the_decision_resumes_it(registry: Registry) -> None:
    inbox = Inbox(registry)
    inbox.receive(gate_event())
    done = inbox.check_deadlines(now=at("2026-10-29T10:00:00"))
    assert [d["stage"] for d in done] == ["paused"]
    assert done[0]["notice"]["status"] == "recorded"  # bez PDI_CHANNELS_URL: tylko zapis
    assert ChangeStore(registry).get("CHG-12")["paused"]["item"] == "evt-gate-1"
    assert inbox.get("evt-gate-1")["paused_at"]
    result = inbox.decide("evt-gate-1", draft(kind="product"), outcome="approved")
    assert "paused" not in result["change"]
    assert "paused" not in ChangeStore(registry).get("CHG-12")


def test_w13_four_times_the_deadline_puts_the_item_on_the_review_list(registry: Registry) -> None:
    inbox = Inbox(registry)
    inbox.receive(gate_event())
    done = inbox.check_deadlines(now=at("2026-11-05T10:00:00"))
    assert [d["stage"] for d in done] == ["review"]
    item = inbox.get("evt-gate-1")
    assert item["needs_review"] is True and item["paused_at"]
    assert item["status"] == "open"  # bramka nigdy nie zatwierdza się sama


def test_w14_a_paused_change_starts_no_next_phase_until_its_item_is_decided(registry: Registry) -> None:
    inbox = Inbox(registry)
    inbox.receive(gate_event())
    store = ChangeStore(registry)
    state = store.get("CHG-12")
    state["paused"] = {"since": "2026-10-22T09:00:00Z", "item": "other-item", "reason": "test"}
    store.save(state)
    result = inbox.decide("evt-gate-1", draft(kind="product"), outcome="approved")
    assert result["change"]["dispatch"]["status"] == "skipped"
    assert "other-item" in result["change"]["dispatch"]["error"]
    assert result["change"]["paused"]["item"] == "other-item"
