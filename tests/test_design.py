"""Kontrakt 0.9.0: format `design.md` (etap 07, F6) — konwencje, schemat odczytanej tabeli, parser referencyjny."""

import json
from typing import Any

import pytest

from pdi import contract
from pdi.design import DesignFormatError, parse_design_md

EXAMPLES = contract.CONTRACT_DIR / "examples"
UI_STATES = [
    "idle",
    "loading",
    "processing",
    "success",
    "validation_error",
    "server_error",
    "timeout",
    "retry",
    "empty",
    "confirmation",
    "session_expired",
    "network_failure",
    "permission_denied",
]
HEADER = "| Wymaganie | Ścieżka | Stan | Ramka | Uwagi |\n|---|---|---|---|---|\n"
LINK = "https://www.figma.com/design/AbC123xyz/Taryfy?node-id=12-34"


def example_json() -> dict[str, Any]:
    data: dict[str, Any] = json.loads((EXAMPLES / "design-links.json").read_text(encoding="utf-8"))
    return data


def test_design_conventions_list_ci_for_sdlc_ui_states() -> None:
    design = contract.settings()["conventions"]["design"]

    assert design["states"] == UI_STATES
    assert design["columns"]["pl"] == ["Wymaganie", "Ścieżka", "Stan", "Ramka", "Uwagi"]
    assert design["columns"]["en"] == ["Requirement", "Journey", "State", "Frame", "Notes"]
    assert "design_links" in contract.SCHEMA_NAMES


def test_example_links_are_valid_and_use_contract_states() -> None:
    data = example_json()

    assert contract.errors("design_links", data) == []
    assert {r["status"] for r in data["rows"]} == {"linked", "missing", "not_applicable"}
    assert enum_states() == UI_STATES


def enum_states() -> list[str]:
    schema = contract.load("design_links")
    states: list[str] = schema["$defs"]["row"]["properties"]["state"]["enum"]
    return states


def test_reference_parser_turns_example_md_into_example_json() -> None:
    text = (EXAMPLES / "design.md").read_text(encoding="utf-8")

    assert parse_design_md(text) == example_json()


def test_english_header_and_frame_link_variants() -> None:
    md = (
        "| Requirement | Journey | State | Frame | Notes |\n|---|---|---|---|---|\n"
        "| US-3/AC-2 | bulk tariff | success | https://figma.com/file/K9/x?node-id=1%3A2 | |\n"
        "| US-3 | bulk tariff | empty | n/a | no list in this journey |\n"
    )

    rows = parse_design_md(md)["rows"]

    assert rows[0]["frame"] == {"file_key": "K9", "node_id": "1:2", "url": "https://figma.com/file/K9/x?node-id=1%3A2"}
    assert rows[1]["status"] == "not_applicable" and rows[1]["note"] == "no list in this journey"


@pytest.mark.parametrize(
    ("row", "message"),
    [
        pytest.param("| US-3 | zmiana | busy | " + LINK + " | |", "stan", id="nieznany-stan"),
        pytest.param("| US-3 | zmiana | idle | https://example.com/x | |", "link", id="link-spoza-figmy"),
        pytest.param("| US-3 | zmiana | idle | https://www.figma.com/design/K/x | |", "node-id", id="link-bez-node-id"),
        pytest.param("| US-3 | zmiana | idle | brak | |", "uwag", id="brak-bez-uwagi"),
        pytest.param("| us3 | zmiana | idle | " + LINK + " | |", "wymagani", id="zly-klucz"),
    ],
)
def test_invalid_rows_name_the_row(row: str, message: str) -> None:
    with pytest.raises(DesignFormatError, match=rf"wiersz 1:.*{message}"):
        parse_design_md(HEADER + row + "\n")


def test_file_without_frame_table_is_an_error() -> None:
    with pytest.raises(DesignFormatError, match="tabel"):
        parse_design_md("# Projekt\n\n| A | B |\n|---|---|\n| 1 | 2 |\n")


def test_contract_version_is_0_9_0() -> None:
    assert contract.CONTRACT_VERSION == "0.9.0"
