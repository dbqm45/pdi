from collections.abc import Callable
from typing import Any

from pdi import phase_decisions
from pdi.registry import Registry

Draft = Callable[..., dict[str, Any]]


def test_linked_selects_recorded_decisions_of_the_change(registry: Registry, make_draft: Draft) -> None:
    a = registry.record(make_draft(statement="A.", links={"chg": "CHG-1"}))
    old = registry.record(make_draft(statement="Stara.", links={"chg": "CHG-1"}))
    new = registry.supersede(old["id"], make_draft(statement="Nowa.", links={"chg": "CHG-1"}))
    registry.record(make_draft(statement="Inna zmiana.", links={"chg": "CHG-2"}))
    registry.record(make_draft(statement="Bez zmiany."))
    gate = registry.record(make_draft(statement="Bramka.", links={"chg": "CHG-1"}))

    found = phase_decisions.linked(registry, "CHG-1", exclude=gate["id"])

    assert found is not None
    assert [d["id"] for d in found] == [a["id"], new["id"]]
    assert set(found[0]) >= {"id", "statement", "why", "decided_at", "decided_by", "kind", "source_kind", "drafted_by"}


def test_linked_is_none_without_decisions(registry: Registry) -> None:
    assert phase_decisions.linked(registry, "CHG-1") is None


def test_linked_keeps_the_newest_and_cuts_long_texts(registry: Registry, make_draft: Draft) -> None:
    for n in range(phase_decisions.LINKED_MAX + 3):
        registry.record(make_draft(statement=f"Decyzja {n}.", why="w" * 3000, links={"chg": "CHG-1"}))

    found = phase_decisions.linked(registry, "CHG-1")

    assert found is not None and len(found) == phase_decisions.LINKED_MAX
    assert found[-1]["statement"] == f"Decyzja {phase_decisions.LINKED_MAX + 2}."
    assert len(found[0]["why"]) == phase_decisions.TEXT_MAX


def test_linked_carries_answers_of_earlier_gates(registry: Registry, make_draft: Draft) -> None:
    answers = [{"question": "Q?", "answer": "A.\nDruga linia."}]
    registry.record(make_draft(answers=answers, links={"chg": "CHG-1"}))

    found = phase_decisions.linked(registry, "CHG-1")

    assert found is not None
    assert found[0]["answers"] == [{"question": "Q?", "answer": "A. Druga linia."}]
