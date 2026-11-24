"""Czego dotyczy decyzja (`applies_to`, kontrakt 0.22.0; docs/plan-applies-to.md).

Dopasowanie wzorców ścieżek wg `contract/decision-record.md` §4a: wzorzec zakotwiczony w korzeniu repo, separator
`/`, `*` — dowolne znaki w jednym segmencie, `?` — jeden znak, `**` jako cały segment — zero lub więcej segmentów;
wzorzec pasuje do pliku i do katalogu, w którym plik leży. Przypadki: `contract/fixtures/applies-to/cases.json`.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from functools import lru_cache
from typing import Any


@lru_cache(maxsize=512)
def _segment(pattern: str) -> re.Pattern[str]:
    parts = ("[^/]*" if c == "*" else "[^/]" if c == "?" else re.escape(c) for c in pattern)
    return re.compile("".join(parts) + r"\Z")


def normalize(path: str) -> str:
    """Ścieżka pliku przed dopasowaniem: `/` zamiast `\\`, bez wiodącego `./`."""
    return path.replace("\\", "/").removeprefix("./")


def matches(pattern: str, path: str) -> bool:
    """Czy wzorzec `applies_to.paths` obejmuje plik (albo katalog) `path`."""
    pat, parts = pattern.split("/"), normalize(path).split("/")

    def go(i: int, j: int) -> bool:
        if i == len(pat):
            return True  # reszta ścieżki leży pod dopasowanym katalogiem
        if pat[i] == "**":
            return any(go(i + 1, k) for k in range(j, len(parts) + 1))
        return j < len(parts) and bool(_segment(pat[i]).match(parts[j])) and go(i + 1, j + 1)

    return go(0, 0)


def matched(decision: dict[str, Any], paths: Iterable[str], components: Iterable[str]) -> dict[str, list[str]] | None:
    """Które z podanych ścieżek i komponentów obejmuje decyzja; None, gdy żadne."""
    scope = decision.get("applies_to") or {}
    patterns = scope.get("paths") or ()
    names = set(scope.get("components") or ())
    hit_paths = [p for p in paths if any(matches(pattern, p) for pattern in patterns)]
    hit_components = [c for c in components if c in names]
    if not hit_paths and not hit_components:
        return None
    return {"paths": hit_paths, "components": hit_components}
