"""Przebieg zmiany (F4): bramki w kolejności planu jednego flow i przejścia stanu CHG — czyste reguły, bez plików.

Stan zmiany to słownik zapisywany przez `pdi.changes`; każde przejście zwraca nową kopię z wpisem w `history`.
Kolejność bramek się pokazuje (`missing_before`), ale nie wymusza.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, TypeAlias

State: TypeAlias = dict[str, Any]
OUTCOMES = ("approved", "changes_requested", "rejected")


class InvalidTransition(ValueError):
    """Przejście niedozwolone w obecnym stanie zmiany."""


@dataclass(frozen=True)
class Gate:
    name: str
    # Faza tf, której wynik ta bramka ocenia (ponowna praca po `changes_requested`); None = nie faza tf.
    produced_by: str | None
    # Faza uruchamiana po `approved`; None = przebieg czeka na kogoś spoza tf (ci_for_sdlc, GitHub, ShipScope).
    next_phase: str | None
    in_chain: bool = True


GATES = (
    Gate("B1", produced_by="intent", next_phase="requirements"),
    Gate("B2", produced_by="requirements", next_phase="architecture"),
    Gate("B3", produced_by="architecture", next_phase="design"),
    Gate("design-review", produced_by="design", next_phase=None),
    Gate("approve-for-implementation", produced_by=None, next_phase="delivery"),
    Gate("B4", produced_by=None, next_phase=None),
    Gate("B5", produced_by=None, next_phase=None),
    Gate("B6", produced_by=None, next_phase=None, in_chain=False),
)
_BY_NAME = {g.name: g for g in GATES}
_CHAIN = [g.name for g in GATES if g.in_chain]
BASELINE_GATE = "approve-for-implementation"


def new_state(change: str) -> State:
    return {
        "change": change,
        "status": "open",
        "approved": {},
        "waiting": [],
        "readiness": None,
        "baseline_drift": False,
        "releases": {},
        "history": [],
    }


def missing_before(state: State, gate: str) -> list[str]:
    """Bramki z łańcucha przed `gate`, które nie są jeszcze zatwierdzone (pusta lista dla bramek spoza łańcucha)."""
    if gate not in _CHAIN:
        return []
    return [g for g in _CHAIN[: _CHAIN.index(gate)] if g not in state["approved"]]


def gate_requested(state: State, gate: str, *, at: str) -> State:
    new = _copy(state)
    if gate not in new["waiting"]:
        new["waiting"].append(gate)
    new["history"].append({"at": at, "what": "gate.requested", "gate": gate})
    return new


def gate_decided(
    state: State, gate: str, outcome: str, decision: str, *, at: str
) -> tuple[State, dict[str, Any] | None]:
    """Zapisuje decyzję na bramce; zwraca nowy stan i fazę do uruchomienia (`{"phase", "rework"}`) albo None."""
    if outcome not in OUTCOMES:
        raise InvalidTransition(f"outcome musi być jednym z {', '.join(OUTCOMES)}.")
    # Odrzucona zmiana jest zamknięta; po ocenie skutku MVP (`done`) dalsze linie wydania mają jeszcze swoje bramki.
    if state["status"] == "rejected":
        raise InvalidTransition(f"{state['change']} ma status rejected — decyzje na bramkach są zamknięte.")
    new = _copy(state)
    new["waiting"] = [g for g in new["waiting"] if g != gate]
    new["history"].append({"at": at, "what": "gate.decided", "gate": gate, "outcome": outcome, "decision": decision})
    spec = _BY_NAME.get(gate)
    if outcome == "rejected":
        new["status"] = "rejected"
        new["waiting"] = []
        return new, None
    if outcome == "changes_requested":
        phase = spec.produced_by if spec else None
        return new, ({"phase": phase, "rework": True} if phase else None)
    new["approved"][gate] = decision
    if gate == BASELINE_GATE:
        new["baseline_drift"] = False
    phase = spec.next_phase if spec else None
    return new, ({"phase": phase, "rework": False} if phase else None)


def readiness_changed(state: State, readiness: str, *, at: str) -> State:
    new = _copy(state)
    new["readiness"] = readiness
    # Rozjazd po „Approve for implementation” to rozjazd z baseline; wcześniejszy to zwykły brak gotowości.
    new["baseline_drift"] = readiness == "drift" and BASELINE_GATE in new["approved"]
    new["history"].append({"at": at, "what": "readiness.changed", "readiness": readiness})
    return new


def feature_released(
    state: State, release: str | None, released_at: str, *, at: str, tasks: list[str] | None = None
) -> State:
    """Wydanie linii (`R1`…) albo całej zmiany (`release` brak → klucz `all`); `tasks` trafiają do grafu śladu."""
    new = _copy(state)
    new["releases"][release or "all"] = released_at
    if tasks:
        new.setdefault("release_tasks", {})[release or "all"] = list(tasks)
    new["history"].append({"at": at, "what": "feature.released", "release": release or "all"})
    return new


def impact_scheduled(state: State, plan: dict[str, Any], *, at: str) -> State:
    """Ocena skutku MVP zaplanowana na `plan["due"]` (F5, `pdi.impact.due_date`)."""
    new = _copy(state)
    new["impact_review"] = {"status": "scheduled", **plan}
    new["history"].append({"at": at, "what": "impact.scheduled", "due": plan["due"]})
    return new


def impact_opened(state: State, item: str, *, at: str) -> State:
    new = _copy(state)
    new["impact_review"] = {**new.get("impact_review", {}), "status": "open", "item": item}
    new["history"].append({"at": at, "what": "impact.opened", "item": item})
    return new


def impact_reviewed(state: State, decision: str, *, at: str, outcome: str | None = None) -> State:
    """Człowiek potwierdził wynik oceny skutku (`met` / `not_met` / `unknown`); zmiana jest skończona."""
    new = _copy(state)
    new["status"] = "done"
    new["waiting"] = []
    entry: dict[str, Any] = {"at": at, "what": "impact.reviewed", "decision": decision}
    if outcome is not None:
        entry["outcome"] = outcome
        review = new.get("impact_review", {})
        new["impact_review"] = {**review, "status": "decided", "outcome": outcome, "decision": decision}
    new["history"].append(entry)
    return new


def _copy(state: State) -> State:
    return copy.deepcopy(state)
