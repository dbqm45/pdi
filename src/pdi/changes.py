"""Stan orkiestracji zmian (F4): pliki `changes/<CHG>.yaml` w katalogu rejestru.

To nie jest artefakt zmiany — intencja, plan i decyzje o zmianie żyją w repo produktu (D2/R1). Tu jest tylko to,
co orkiestrator wie o przebiegu: zatwierdzone bramki, na co zmiana czeka, ostatnie uruchomienie fazy. Przy odczycie
lokalne uruchomienie fazy (`PDI_DISPATCH=local`) dostaje wynik przebiegu z `runs/` (`pdi.dispatch_local.settle`).
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from pdi import contract, dispatch_local
from pdi.flow import State, new_state
from pdi.registry import Registry

_KEY = re.compile(contract.settings()["key_pattern"])


class ChangeNotFound(LookupError):
    """pdi nie ma stanu tej zmiany (żadne zdarzenie jej jeszcze nie dotyczyło)."""


class ChangeStore:
    def __init__(self, registry: Registry) -> None:
        self._dir = registry.root / "changes"

    def path(self, change: str) -> Path:
        if not _KEY.match(change):
            raise ChangeNotFound(f"„{change}” nie jest kluczem zmiany (np. CHG-12).")
        return self._dir / f"{change}.yaml"

    def get(self, change: str) -> State:
        path = self.path(change)
        if not path.is_file():
            raise ChangeNotFound(f"pdi nie zna jeszcze {change} — sprawdź list_changes.")
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ChangeNotFound(f"{path.name}: uszkodzony stan zmiany.")
        return dispatch_local.settle(data)

    def load(self, change: str) -> State:
        """Stan zmiany albo nowy, pusty — gdy to pierwsze zdarzenie o niej."""
        try:
            return self.get(change)
        except ChangeNotFound:
            self.path(change)  # zły klucz zostaje błędem
            return new_state(change)

    def save(self, state: State) -> Path:
        path = self.path(state["change"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(state, sort_keys=False, allow_unicode=True, width=1000), encoding="utf-8")
        return path

    def all(self, status: str | None = "open") -> list[State]:
        if not self._dir.is_dir():
            return []
        found = [self.get(p.stem) for p in sorted(self._dir.glob("*.yaml"))]
        return [s for s in found if not status or s["status"] == status]
