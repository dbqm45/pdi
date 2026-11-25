"""DI Team T4 „Ask team” (docs/plan-t4-ask-team.md): konsultacja przy pozycji skrzynki i osoby konsoli."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from pdi import consult

T0 = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
DECIDER = consult.Person(sub="s-ola", name="Ola Test")
ADM = consult.Person(sub="s-adm", name="Adm Test")
THIRD = consult.Person(sub="s-3", name="Trzecia Osoba")
OPTIONS = ["approved", "changes_requested", "rejected"]


class Clock:
    def __init__(self) -> None:
        self.now = T0

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def store(tmp_path: Path, clock: Clock) -> consult.Consultations:
    return consult.Consultations(tmp_path, now=clock)


def ask(store: consult.Consultations, asked: list[consult.Person] | None = None, hours: int = 24) -> None:
    store.ask("evt-1", decider=DECIDER, asked=asked or [ADM, THIRD], options=OPTIONS, hours=hours)


def test_ct01_answers_stay_hidden_from_everyone_until_the_question_closes(store: consult.Consultations) -> None:
    ask(store)
    store.answer("evt-1", ADM, option="approved", reason="Plan pokrywa ryzyka.")
    for viewer in (DECIDER.sub, ADM.sub, THIRD.sub):
        view = store.view("evt-1", viewer)
        assert view is not None
        assert view["status"] == "open"
        assert (view["answered"], view["asked"]) == (1, 2)
        assert "answers" not in view, "nobody sees the answers before the close, the decider neither"
    assert store.view("evt-1", ADM.sub)["mine"] == {"option": "approved", "reason": "Plan pokrywa ryzyka."}  # type: ignore[index]
    assert store.view("evt-1", THIRD.sub)["mine"] is None  # type: ignore[index]


def test_ct02_it_closes_when_everyone_answered_and_then_shows_who_said_what(store: consult.Consultations) -> None:
    ask(store)
    store.answer("evt-1", ADM, option="approved", reason="Plan pokrywa ryzyka.")
    store.answer("evt-1", THIRD, option="approved", reason="Testy są.")
    view = store.view("evt-1", DECIDER.sub)
    assert view is not None and view["status"] == "closed"
    assert view["result"] == {"kind": "agree", "option": "approved"}
    assert view["answers"] == [
        {"name": "Adm Test", "option": "approved", "reason": "Plan pokrywa ryzyka."},
        {"name": "Trzecia Osoba", "option": "approved", "reason": "Testy są."},
    ]
    with pytest.raises(consult.ConsultError, match="closed"):
        store.answer("evt-1", ADM, option="rejected", reason="Zmiana zdania.")


def test_ct03_a_split_or_talk_live_means_discuss(store: consult.Consultations) -> None:
    ask(store)
    store.answer("evt-1", ADM, option="approved", reason="Dobrze.")
    store.answer("evt-1", THIRD, option="rejected", reason="Za duże ryzyko.")
    assert store.view("evt-1", DECIDER.sub)["result"] == {"kind": "discuss"}  # type: ignore[index]

    store.close("evt-1")
    store.ask("evt-2", decider=DECIDER, asked=[ADM, THIRD], options=OPTIONS, hours=24)
    store.answer("evt-2", ADM, option="approved", reason="Dobrze.")
    store.answer("evt-2", THIRD, option=consult.TALK_LIVE, reason="Trzeba to omówić na żywo.")
    assert store.view("evt-2", DECIDER.sub)["result"] == {"kind": "discuss"}  # type: ignore[index]


def test_ct04_the_deadline_closes_it_and_who_did_not_answer_is_recorded_with_none(
    store: consult.Consultations, clock: Clock
) -> None:
    ask(store, hours=4)
    store.answer("evt-1", ADM, option="approved", reason="Dobrze.")
    clock.now = T0 + timedelta(hours=4, seconds=1)
    view = store.view("evt-1", DECIDER.sub)
    assert view is not None and view["status"] == "closed"
    assert view["result"] == {"kind": "agree", "option": "approved"}, "agreement among those who answered"
    assert store.consulted("evt-1") == [
        {"person_id": "s-adm", "name": "Adm Test", "option": "approved", "reason": "Dobrze."},
        {"person_id": "s-3", "name": "Trzecia Osoba", "option": None, "reason": None},
    ]


def test_ct05_nobody_answered_is_no_result(store: consult.Consultations, clock: Clock) -> None:
    ask(store, hours=4)
    clock.now = T0 + timedelta(hours=5)
    assert store.view("evt-1", DECIDER.sub)["result"] == {"kind": "none"}  # type: ignore[index]


def test_ct06_only_the_asked_answer_one_option_of_the_item_with_one_sentence(store: consult.Consultations) -> None:
    ask(store, asked=[ADM])
    with pytest.raises(consult.ConsultError, match="not asked"):
        store.answer("evt-1", THIRD, option="approved", reason="Chcę się wtrącić.")
    with pytest.raises(consult.ConsultError, match="option"):
        store.answer("evt-1", ADM, option="maybe", reason="Nie wiem.")
    with pytest.raises(consult.ConsultError, match="reason"):
        store.answer("evt-1", ADM, option="approved", reason="   ")
    store.answer("evt-1", ADM, option="rejected", reason="Najpierw tak.")
    assert store.view("evt-1", ADM.sub)["status"] == "closed"  # type: ignore[index]


def test_ct07_asking_needs_someone_other_than_the_decider_and_one_open_question_per_item(
    store: consult.Consultations,
) -> None:
    with pytest.raises(consult.ConsultError, match="someone"):
        store.ask("evt-1", decider=DECIDER, asked=[DECIDER], options=OPTIONS, hours=24)
    with pytest.raises(consult.ConsultError, match="deadline"):
        store.ask("evt-1", decider=DECIDER, asked=[ADM], options=OPTIONS, hours=0)
    ask(store)
    with pytest.raises(consult.ConsultError, match="already"):
        ask(store)
    assert store.view("evt-1", DECIDER.sub)["decider"] == "Ola Test"  # type: ignore[index]


def test_ct08_the_agent_adds_effects_per_option_and_the_decider_may_close_early(store: consult.Consultations) -> None:
    ask(store)
    store.add_effects("evt-1", "changes_requested", "Dwa cięcia więcej, ok. 3 USD, testy kontraktu.")
    with pytest.raises(consult.ConsultError, match="option"):
        store.add_effects("evt-1", "maybe", "x")
    assert store.view("evt-1", ADM.sub)["effects"] == {
        "changes_requested": "Dwa cięcia więcej, ok. 3 USD, testy kontraktu."
    }  # type: ignore[index]
    store.close("evt-1")
    assert store.view("evt-1", ADM.sub)["status"] == "closed"  # type: ignore[index]
    assert store.view("evt-404", ADM.sub) is None


def test_ct09_people_of_the_console_by_their_sign_ins_without_email(tmp_path: Path, clock: Clock) -> None:
    people = consult.People(tmp_path, now=clock)
    people.seen(consult.Person(sub="s-ola", name="Ola Test"))
    people.seen(consult.Person(sub="s-adm", name="Adm Test"))
    people.seen(consult.Person(sub="s-ola", name="Ola T."))
    assert people.all() == [consult.Person(sub="s-adm", name="Adm Test"), consult.Person(sub="s-ola", name="Ola T.")]
    assert "@" not in (tmp_path / "people.json").read_text(encoding="utf-8")
