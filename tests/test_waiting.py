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
