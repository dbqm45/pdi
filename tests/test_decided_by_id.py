"""Stały identyfikator decydującego (kontrakt 0.25.0, `decided_by_id`): `sub` osoby z tożsamości suity.

Konsola zalogowana przez suitę zapisuje go z sesji (tests/test_console_suite.py); tu: rejestr go nie gubi, a
`decision.recorded` od innej aplikacji suity przenosi go do rejestru.
"""

from __future__ import annotations

from pdi.inbox import Inbox
from pdi.registry import Registry
from tests.conftest import draft
from tests.test_decision_recorded import recorded_event

SUB = "8f14e45f-ceea-467a-9b1d-6f7e2b3c4d5e"


def test_the_registry_keeps_decided_by_id(registry: Registry) -> None:
    saved = registry.record(draft(decided_by="Ola Test", decided_by_id=SUB))
    assert registry.get(saved["id"])["decided_by_id"] == SUB


def test_decision_recorded_carries_decided_by_id_into_the_registry(registry: Registry) -> None:
    result = Inbox(registry).receive(recorded_event(decided_by_id=SUB))
    assert registry.get(result["decision"])["decided_by_id"] == SUB


def test_a_decision_without_it_stays_valid(registry: Registry) -> None:
    saved = registry.record(draft(decided_by="Ola Test"))
    assert "decided_by_id" not in registry.get(saved["id"])
