from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from pdi.registry import Registry

FIXED_NOW = datetime(2026, 10, 23, 9, 30, tzinfo=UTC)


def draft(**overrides: Any) -> dict[str, Any]:
    """Minimalny poprawny szkic decyzji, jaki przysyła klient (bez pól nadawanych przez rejestr)."""
    base: dict[str, Any] = {
        "statement": "Próg darmowej dostawy zostaje na 199 zł do końca kwartału.",
        "why": "Aneks z przewoźnikiem X podnosi koszt paczki; obniżenie progu dałoby wynik ujemny.",
        "decided_by": "właściciel",
        "decided_at": "2026-10-22",
        "kind": "product",
        "source": {"kind": "claude-cli", "excerpt": "ustalamy, że próg zostaje"},
        "drafted_by": "ai",
        "draft_edited": False,
    }
    base.update(overrides)
    if base["drafted_by"] != "ai" or base["draft_edited"] is None:  # None: szkic bez pola (pdi liczy je sam)
        del base["draft_edited"]
    return base


@pytest.fixture
def registry(tmp_path: Path) -> Registry:
    return Registry(tmp_path / "rejestr", clock=lambda: FIXED_NOW)


@pytest.fixture
def make_draft() -> Callable[..., dict[str, Any]]:
    return draft
