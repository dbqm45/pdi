import hashlib
import hmac
import json
from datetime import date
from typing import Any

import pytest
import yaml

from pdi.inbox import Inbox
from pdi.notify import ReporterNotifyConfig
from pdi.problems import InvalidProblem, ProblemNotFound, ProblemStore
from pdi.registry import InvalidDecision, Registry
from tests.test_inbox import released_event

SECRET = "sekret-powiadomien"  # noqa: S105 — sekret testowy
NOTIFY = ReporterNotifyConfig(url="https://hooks.example.com/pdi", secret=SECRET)


def problem(**overrides: Any) -> dict[str, Any]:
    """Szkic zgłoszenia, jak podaje go człowiek albo agent (bez id, reported_at i status)."""
    base: dict[str, Any] = {
        "kind": "problem",
        "category": "enhancement",
        "title": "Brak operacji na wielu ładowarkach naraz",
        "who": "operator Control Tower",
        "cannot": "zmienić konfiguracji wielu ładowarek jedną operacją",
        "impact": "zmiana taryfy na 200 ładowarkach zajmuje dzień pracy",
        "reporter": "operator-1",
        "channel": "form",
    }
    base.update(overrides)
    return base


class FakeHook:
    def __init__(self, status: int = 202, error: Exception | None = None) -> None:
        self.status = status
        self.error = error
        self.calls: list[tuple[str, dict[str, str], bytes]] = []

    def __call__(self, url: str, headers: dict[str, str], body: bytes) -> int:
        self.calls.append((url, headers, body))
        if self.error:
            raise self.error
        return self.status

    def bodies(self) -> list[dict[str, Any]]:
        return [json.loads(b) for _, _, b in self.calls]


def store(registry: Registry, hook: FakeHook | None = None, config: ReporterNotifyConfig = NOTIFY) -> ProblemStore:
    return ProblemStore(registry, notify=config, post=hook)


# --- rejestr ---


def test_record_assigns_id_date_and_status_and_keeps_contract_shape(registry: Registry) -> None:
    problems = store(registry)

    first = problems.record(problem())
    second = problems.record(problem(title="Drugie"))

    assert (first["id"], second["id"]) == ("PRB-1", "PRB-2")
    assert (first["reported_at"], first["status"]) == ("2026-10-23", "new")
    stored = yaml.safe_load((registry.root / "problems" / "PRB-1.yaml").read_text(encoding="utf-8"))
    assert stored == first
    assert problems.get("PRB-2")["title"] == "Drugie"
    assert [p["id"] for p in problems.all()] == ["PRB-1", "PRB-2"]


@pytest.mark.parametrize(
    ("draft", "match"),
    [
        (problem(channel="gołębie"), "channel"),
        ({k: v for k, v in problem().items() if k != "who"}, "who"),
        (problem(id="PRB-9"), "id"),
        (problem(status="accepted"), "status"),
    ],
    ids=["zly-kanal", "brak-who", "wlasne-id", "wlasny-status"],
)
def test_bad_draft_is_refused(registry: Registry, draft: dict[str, Any], match: str) -> None:
    with pytest.raises(InvalidProblem, match=match):
        store(registry).record(draft)
    assert not (registry.root / "problems").exists() or list((registry.root / "problems").iterdir()) == []


def test_unknown_problem_raises_with_hint(registry: Registry) -> None:
    with pytest.raises(ProblemNotFound, match="list_problems"):
        store(registry).get("PRB-404")
    with pytest.raises(ProblemNotFound):
        store(registry).get("../decisions")


# --- triaż ---


def test_accepting_records_triage_decision_links_change_and_notifies(registry: Registry, make_draft: Any) -> None:
    hook = FakeHook()
    problems = store(registry, hook)
    problems.record(problem())

    result = problems.triage("PRB-1", "accepted", make_draft(statement="Przyjmujemy jako CHG-12."), change="CHG-12")

    decision = result["decision"]
    assert decision["kind"] == "triage"
    assert decision["links"] == {"prb": "PRB-1", "chg": "CHG-12"}
    assert "problem:accepted" in decision["tags"]
    stored = problems.get("PRB-1")
    assert (stored["status"], stored["change"], stored["triage_decision"]) == ("accepted", "CHG-12", decision["id"])
    url, headers, body = hook.calls[0]
    assert url == "https://hooks.example.com/pdi"
    assert headers["x-pdi-event"] == "problem.notification"
    mac = hmac.new(SECRET.encode(), headers["x-pdi-timestamp"].encode() + b"." + body, hashlib.sha256)
    assert headers["x-pdi-signature"] == "v1=" + mac.hexdigest()
    sent = json.loads(body)
    assert sent["id"] == "notify-PRB-1-accepted"
    assert (sent["problem"], sent["reporter"], sent["channel"], sent["what"]) == (
        "PRB-1",
        "operator-1",
        "form",
        "accepted",
    )
    assert (sent["change"], sent["decision"]) == ("CHG-12", decision["id"])
    assert "przyjęte" in sent["message"] and "CHG-12" in sent["message"]
    assert result["notification"]["status"] == "sent"


@pytest.mark.parametrize(
    ("outcome", "extra", "fields", "word"),
    [
        (
            "rejected",
            {"rejection_reason": "out_of_strategy", "rejection_note": "Nie w tym roku."},
            {"rejection_reason": "out_of_strategy"},
            "odrzucone",
        ),
        ("parked", {"return_when": "3 nowe zgłoszenia"}, {"return_when": "3 nowe zgłoszenia"}, "odłożone"),
        ("duplicate", {"duplicate_of": "PRB-7"}, {"duplicate_of": "PRB-7"}, "duplikat"),
    ],
)
def test_other_outcomes_set_their_fields_and_say_so(
    registry: Registry, make_draft: Any, outcome: str, extra: dict[str, str], fields: dict[str, str], word: str
) -> None:
    hook = FakeHook()
    problems = store(registry, hook)
    problems.record(problem())

    problems.triage("PRB-1", outcome, make_draft(), **extra)

    stored = problems.get("PRB-1")
    assert stored["status"] == outcome
    assert {k: stored[k] for k in fields} == fields
    assert word in hook.bodies()[0]["message"]


@pytest.mark.parametrize(
    ("outcome", "extra", "match"),
    [
        ("approved", {}, "accepted"),
        ("accepted", {}, "change"),
        ("duplicate", {}, "duplicate_of"),
        ("rejected", {"rejection_reason": "bo tak"}, "rejection_reason"),
    ],
)
def test_bad_triage_is_refused_before_recording(
    registry: Registry, make_draft: Any, outcome: str, extra: dict[str, str], match: str
) -> None:
    problems = store(registry, FakeHook())
    problems.record(problem())

    with pytest.raises(InvalidDecision, match=match):
        problems.triage("PRB-1", outcome, make_draft(), **extra)
    assert registry.decisions() == []
    assert problems.get("PRB-1")["status"] == "new"


def test_triaged_problem_cannot_be_triaged_again(registry: Registry, make_draft: Any) -> None:
    problems = store(registry, FakeHook())
    problems.record(problem())
    problems.triage("PRB-1", "accepted", make_draft(), change="CHG-12")

    with pytest.raises(InvalidDecision, match="accepted"):
        problems.triage("PRB-1", "rejected", make_draft(), rejection_reason="other")


# --- wysyłka ---


def test_without_url_notification_is_skipped_and_kept(registry: Registry, make_draft: Any) -> None:
    problems = store(registry, FakeHook(), ReporterNotifyConfig(url=None))
    problems.record(problem())

    result = problems.triage("PRB-1", "accepted", make_draft(), change="CHG-12")

    assert result["notification"]["status"] == "skipped"
    log = yaml.safe_load((registry.root / "notifications" / "PRB-1.yaml").read_text(encoding="utf-8"))
    assert [(n["id"], n["status"]) for n in log] == [("notify-PRB-1-accepted", "skipped")]


def test_failed_notification_is_retried_once_fixed_and_never_doubled(registry: Registry, make_draft: Any) -> None:
    broken = FakeHook(status=500)
    store(registry, broken).record(problem())
    result = store(registry, broken).triage("PRB-1", "accepted", make_draft(), change="CHG-12")
    assert result["notification"]["status"] == "failed"
    assert "500" in result["notification"]["error"]
    assert SECRET not in json.dumps(result)

    fixed = FakeHook()
    retried = store(registry, fixed).retry("PRB-1")

    assert [n["status"] for n in retried["notifications"]] == ["sent"]
    assert store(registry, fixed).retry("PRB-1") == {"problem": "PRB-1", "notifications": []}
    assert len(fixed.calls) == 1


def test_http_or_login_in_url_is_refused(registry: Registry, make_draft: Any) -> None:
    hook = FakeHook()
    problems = store(registry, hook, ReporterNotifyConfig(url="http://hooks.example.com", secret=SECRET))
    problems.record(problem())

    result = problems.triage("PRB-1", "accepted", make_draft(), change="CHG-12")

    assert result["notification"]["status"] == "failed" and "https" in result["notification"]["error"]
    assert hook.calls == []


# --- wydanie i ocena skutku zmiany z tego zgłoszenia ---


def test_release_and_impact_review_of_its_change_notify_the_reporter(registry: Registry, make_draft: Any) -> None:
    hook = FakeHook()
    problems = store(registry, hook)
    problems.record(problem())
    problems.triage("PRB-1", "accepted", make_draft(), change="CHG-12")
    inbox = Inbox(registry, reporters=NOTIFY, reporter_post=hook)

    inbox.receive(released_event())
    inbox.receive(released_event())  # duplikat zdarzenia: bez drugiego powiadomienia
    inbox.receive(released_event("evt-rel-2", release="R2", released_at="2026-11-02T10:00:00Z"))
    inbox.open_due_reviews(today=date(2026, 11, 22))
    inbox.decide("impact-CHG-12-R1", make_draft(statement="Cel osiągnięty."), outcome="met")

    sent = hook.bodies()
    assert [s["id"] for s in sent] == [
        "notify-PRB-1-accepted",
        "notify-PRB-1-released-R1",
        "notify-PRB-1-released-R2",
        "notify-PRB-1-impact_reviewed",
    ]
    assert "u ludzi" in sent[1]["message"] and sent[1]["release"] == "R1"
    assert sent[3]["outcome"] == "met" and "osiągnięty" in sent[3]["message"]


def test_changes_without_a_problem_notify_nobody(registry: Registry) -> None:
    hook = FakeHook()

    Inbox(registry, reporters=NOTIFY, reporter_post=hook).receive(released_event())

    assert hook.calls == []
