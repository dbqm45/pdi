"""DI Team T6: „Ask team” i dzienny skrót do Slacka przez DI Channels (docs/plan-t6-skroty-slack.md)."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from pdi import agenda, consult, team_notify
from pdi.inbox import Inbox
from pdi.registry import Registry
from pdi.waiting import ChannelsConfig
from tests.test_ask_team import ask, people
from tests.test_console_suite import Console, FakeIssuer

SECRET = "pdi-channels-test"  # noqa: S105 — sekret tylko w teście
CFG = ChannelsConfig(url="http://localhost:3100", secret=SECRET, console_url="http://127.0.0.1:8788")
OLA = consult.Person("s-ola", "Ola Test")
ADM = consult.Person("7badb004-5f2f-4791-838f-9ee86d26839d", "Adm Test")
THIRD = consult.Person("0c1d2e3f-4a5b-4c6d-8e7f-901234567890", "Trzecia Osoba")
T0 = datetime(2026, 11, 23, 9, 0, tzinfo=UTC)  # poniedziałek


class FakeChannels:
    """DI Channels: zapisuje podpisane wiadomości i odpowiada jak usługa (osoby spoza Slacka: `not_in_slack`)."""

    def __init__(self, missing: set[str] | None = None, status: int = 200) -> None:
        self.sent: list[tuple[str, dict[str, str], dict[str, Any]]] = []
        self.missing = missing or set()
        self.status = status

    def __call__(self, url: str, headers: dict[str, str], body: bytes) -> tuple[int, bytes]:
        expected = (
            "v1="
            + hmac.new(SECRET.encode(), headers["x-pdi-timestamp"].encode() + b"." + body, hashlib.sha256).hexdigest()
        )
        assert headers["x-pdi-signature"] == expected
        msg = json.loads(body)
        self.sent.append((url, headers, msg))
        if self.status != 200:
            return self.status, b"{}"
        if msg["type"] == "team.asked":
            delivered = [{"person": p, "status": "not_in_slack" if p in self.missing else "now"} for p in msg["people"]]
            return 200, json.dumps({"delivered": delivered}).encode()
        return 200, json.dumps({"delivered": "now"}).encode()


def item(item_id: str, *, received: datetime = T0 - timedelta(days=1), **extra: Any) -> dict[str, Any]:
    at = received.strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"id": item_id, "kind": "gate", "status": "open", "change": "CHG-1", "gate": "B2",
            "summary": f"Sprawa {item_id}", "received_at": at, **extra}  # fmt: skip


@pytest.fixture
def store(tmp_path: Path) -> consult.Consultations:
    return consult.Consultations(tmp_path, now=lambda: T0)


def test_tn01_asked_people_get_a_message_and_pdi_keeps_who_was_not_reachable(store: consult.Consultations) -> None:
    c = store.ask(
        "evt-1", decider=OLA, asked=[ADM, THIRD], options=["approved", "changes_requested", "rejected"], hours=4
    )
    fake = FakeChannels(missing={THIRD.sub})
    notice = team_notify.notify_asked(CFG, item("evt-1"), c, at="2026-11-23T09:00:00Z", post=fake)
    url, _, msg = fake.sent[0]
    assert url == "http://localhost:3100/pdi/asked"
    assert msg["type"] == "team.asked"
    assert msg["people"] == [ADM.sub, THIRD.sub]
    assert msg["asked_by"] == "Ola Test"
    assert msg["closes_at"] == "2026-11-23T13:00:00Z"
    assert msg["url"] == "http://127.0.0.1:8788/inbox"
    assert "t=" not in msg["url"]
    assert {"change": msg["change"], "gate": msg["gate"]} == {"change": "CHG-1", "gate": "B2"}
    assert notice == {"status": "sent", "at": "2026-11-23T09:00:00Z", "unreachable": ["Trzecia Osoba"]}
    store.record_notice("evt-1", notice)
    assert store.view("evt-1", OLA.sub)["unreachable"] == ["Trzecia Osoba"]  # type: ignore[index]
    skipped = team_notify.notify_asked(ChannelsConfig(url=None), item("evt-1"), c, at="x")
    assert skipped["status"] == "skipped"
    failed = team_notify.notify_asked(CFG, item("evt-1"), c, at="x", post=FakeChannels(status=502))
    assert failed["status"] == "failed"


def test_tn02_the_approver_digest_lists_the_most_urgent_first_and_says_what_the_team_has(
    store: consult.Consultations,
) -> None:
    items = [item(f"g{i}", received=T0 - timedelta(hours=1)) for i in range(11)]
    items.append(item("late", received=T0 - timedelta(days=7)))  # B2 (2 dni) po 5 dniach roboczych: wstrzymana
    store.ask("g1", decider=OLA, asked=[ADM, THIRD], options=["approved"], hours=4)
    store.answer("g1", ADM, option="approved", reason="Zgoda.")
    store.record_notice("g1", {"status": "sent", "at": "x", "unreachable": ["Trzecia Osoba"]})
    store.ask("late", decider=OLA, asked=[ADM], options=["approved"], hours=1)
    store.answer("late", ADM, option=consult.TALK_LIVE, reason="Na żywo.")
    entries = agenda.build(items, store, order=[], now=T0)
    d = team_notify.approver_digest(items, store, entries, now=T0, config=CFG)
    assert d is not None
    assert d["id"] == "digest-approver-2026-11-23"
    assert d["to"] == {"approver": True}
    assert d["waiting"]["total"] == 12
    assert len(d["waiting"]["items"]) == 10
    assert d["waiting"]["items"][0]["item"] == "late"
    assert d["waiting"]["items"][0]["stage"] == "paused"
    assert d["waiting"]["items"][1]["stage"] == "new"
    assert d["with_team"] == [
        {"item": "g1", "summary": "Sprawa g1", "answered": 1, "asked": 2, "closes_at": "2026-11-23T13:00:00Z"}
    ]
    assert d["to_discuss"] == {"count": 1, "url": "http://127.0.0.1:8788/discuss"}
    assert d["unreachable"] == ["Trzecia Osoba"]
    assert team_notify.approver_digest([], store, [], now=T0, config=CFG) is None


def test_tn03_a_person_gets_a_digest_only_while_a_question_waits_for_their_answer(store: consult.Consultations) -> None:
    items = [item("a"), item("b")]
    store.ask("a", decider=OLA, asked=[ADM, THIRD], options=["approved"], hours=24)
    store.ask("b", decider=OLA, asked=[ADM], options=["approved"], hours=24)
    store.answer("b", ADM, option="approved", reason="Zgoda.")
    digests = team_notify.person_digests(items, store, [OLA, ADM, THIRD], now=T0, config=CFG)
    by = {d["to"]["person"]: d for d in digests}
    assert set(by) == {ADM.sub, THIRD.sub}
    assert by[ADM.sub]["id"] == f"digest-{ADM.sub}-2026-11-23"
    assert by[ADM.sub]["asked_of_you"] == [
        {"item": "a", "summary": "Sprawa a", "asked_by": "Ola Test", "closes_at": "2026-11-24T09:00:00Z",
         "url": "http://127.0.0.1:8788/inbox"}
    ]  # fmt: skip
    assert by[ADM.sub]["waiting"] == {"total": 0, "items": []}


def test_tn04_send_digests_sends_each_once_a_day_and_says_what_happened(tmp_path: Path) -> None:
    reg = Registry(tmp_path / "registry")
    reg.root.mkdir(parents=True)
    (reg.root / "inbox").mkdir()
    (reg.root / "inbox" / "a.yaml").write_text(json.dumps(item("a")), encoding="utf-8")
    store = consult.Consultations(reg.root, now=lambda: T0)
    store.ask("a", decider=OLA, asked=[ADM], options=["approved"], hours=24)
    people = consult.People(reg.root, now=lambda: T0)
    for p in (OLA, ADM):
        people.seen(p)
    fake = FakeChannels()
    out = team_notify.send_digests(reg, CFG, now=T0, post=fake)
    assert [o["to"] for o in out] == ["approver", "Adm Test"]
    assert all(o["status"] == "sent" for o in out)
    assert [m["type"] for _, _, m in fake.sent] == ["team.digest", "team.digest"]
    assert [m["id"] for _, _, m in fake.sent] == ["digest-approver-2026-11-23", f"digest-{ADM.sub}-2026-11-23"]
    assert team_notify.send_digests(reg, ChannelsConfig(url=None), now=T0)[0]["status"] == "skipped"


# --- konsola: „Ask team” wysyła wiadomość ---


@pytest.fixture
def registry(tmp_path: Path) -> Registry:
    r = Registry(tmp_path / "registry")
    r.root.mkdir(parents=True, exist_ok=True)
    return r


def test_tn05_asking_in_the_console_messages_the_asked_and_shows_who_slack_does_not_know(
    registry: Registry, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.test_console_suite import _write_inbox_gate

    _write_inbox_gate(registry)
    fake = FakeChannels(missing={"s-3"})
    monkeypatch.setattr(Inbox, "channels", property(lambda self: CFG))
    monkeypatch.setattr(team_notify, "_post_json", fake)
    app = Console(registry, FakeIssuer(), monkeypatch)
    try:
        s = people(app)
        assert ask(app, s["ola"], ["s-adm", "s-3"])[0] == 303
        assert len(fake.sent) == 1
        assert fake.sent[0][2]["people"] == ["s-adm", "s-3"] or set(fake.sent[0][2]["people"]) == {"s-adm", "s-3"}
        _, _, page, _ = app.request("GET", "/inbox", cookie=s["ola"])
        assert "Not reachable in Slack: Trzecia Osoba" in page
    finally:
        app.close()


def test_tn06_the_agent_reads_the_digest_through_mcp(tmp_path: Path) -> None:
    from pdi.mcp_server import build_server

    reg = Registry(tmp_path / "registry")
    reg.root.mkdir(parents=True)
    (reg.root / "inbox").mkdir()
    (reg.root / "inbox" / "a.yaml").write_text(json.dumps(item("a")), encoding="utf-8")
    server = build_server(lambda: reg)
    result = asyncio.run(server.call_tool("daily_digest", {}))
    assert result.is_error is False
    out = result.structured_content
    assert out["approver"]["waiting"]["total"] == 1
    assert out["people"] == []
