"""Kontrakt pdi (`contract/`): schematy JSON wspólne dla pdi, tf, ci_for_sdlc i ShipScope."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

CONTRACT_DIR = Path(__file__).resolve().parents[2] / "contract"
SCHEMA_NAMES = ("decision", "problem", "change", "task", "event", "story", "release_plan", "autonomy")
# Schematy plików zestawu wzorcowego kształtu historyjki (dla testów tf i ci_for_sdlc, nie dla wymiany danych).
FIXTURE_SCHEMAS = {
    "story_shape_stories": Path("fixtures/story-shape/stories.schema.json"),
    "story_shape_expected": Path("fixtures/story-shape/expected.schema.json"),
}


@cache
def settings() -> dict[str, Any]:
    """Wersja kontraktu, wzorzec klucza i domyślne prefiksy ID (`contract/contract.json`)."""
    data: dict[str, Any] = json.loads((CONTRACT_DIR / "contract.json").read_text(encoding="utf-8"))
    return data


CONTRACT_VERSION: str = settings()["version"]


def schema_path(name: str) -> Path:
    if name in FIXTURE_SCHEMAS:
        return CONTRACT_DIR / FIXTURE_SCHEMAS[name]
    if name not in SCHEMA_NAMES:
        raise KeyError(f"W kontrakcie nie ma schematu „{name}” — dostępne: {', '.join(SCHEMA_NAMES)}.")
    return CONTRACT_DIR / f"{name.replace('_', '-')}.schema.json"


@cache
def load(name: str) -> dict[str, Any]:
    schema: dict[str, Any] = json.loads(schema_path(name).read_text(encoding="utf-8"))
    return schema


@cache
def _validator(name: str) -> Draft202012Validator:
    return Draft202012Validator(load(name), format_checker=Draft202012Validator.FORMAT_CHECKER)


def errors(name: str, data: dict[str, Any]) -> list[str]:
    """Błędy walidacji obiektu względem schematu `name`, w formie `ścieżka: problem` (pusta lista = poprawny)."""
    found = sorted(_validator(name).iter_errors(data), key=lambda e: list(e.absolute_path))
    return [f"{'.'.join(str(p) for p in e.absolute_path) or '(obiekt)'}: {e.message}" for e in found]


def rules_broken(name: str, data: dict[str, Any]) -> list[str]:
    """Jak `errors`, ale bez wartości z obiektu: `ścieżka: reguła` (`payload.rollout: maximum`).

    Dla danych z zewnątrz, których treść nie powinna wracać w odpowiedzi ani w logu. Brakujące pole jest nazwane,
    bo to nazwa ze schematu, nie wartość.
    """
    found = sorted(_validator(name).iter_errors(data), key=lambda e: list(e.absolute_path))
    out = []
    for e in found:
        where = ".".join(str(p) for p in e.absolute_path) or "(obiekt)"
        rule = e.message if e.validator == "required" else str(e.validator)
        out.append(f"{where}: {rule}")
    return out
