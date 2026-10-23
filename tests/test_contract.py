import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from pdi import contract

EXAMPLES = sorted((contract.CONTRACT_DIR / "examples").glob("*.json"))
EVENT_TYPES = [
    "problem.accepted",
    "gate.requested",
    "gate.decided",
    "readiness.changed",
    "feature.released",
    "metric.breached",
    "decision.basis_invalidated",
]


def example(name: str) -> dict[str, Any]:
    data = json.loads((contract.CONTRACT_DIR / "examples" / f"{name}.json").read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def schema_for(path: Path) -> str:
    return path.stem.split("-", 1)[0]


@pytest.mark.parametrize("name", contract.SCHEMA_NAMES)
def test_schema_is_valid_json_schema_2020_12(name: str) -> None:
    Draft202012Validator.check_schema(contract.load(name))


def test_settings_define_version_key_pattern_and_default_prefixes() -> None:
    settings = contract.settings()

    assert settings["version"] == contract.CONTRACT_VERSION == "0.3.0"
    assert settings["prefixes"] == {"problem": "PRB", "change": "CHG", "task": "TSK", "decision": "DEC"}
    assert settings["key_pattern"] == "^[A-Z][A-Z0-9]+-[0-9]+$"


def test_every_schema_and_event_type_has_an_example() -> None:
    names = {p.stem for p in EXAMPLES}

    assert set(contract.SCHEMA_NAMES) - {"event"} <= names
    assert {f"event-{t}" for t in EVENT_TYPES} <= names


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.stem)
def test_examples_are_valid(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))

    assert contract.errors(schema_for(path), data) == []


def test_event_examples_carry_current_contract_version() -> None:
    for t in EVENT_TYPES:
        assert example(f"event-{t}")["contract_version"] == contract.CONTRACT_VERSION


def test_unknown_schema_name_is_reported() -> None:
    with pytest.raises(KeyError, match="nie ma schematu"):
        contract.load("invoice")


# --- zgłoszenie (PRB) ---


@pytest.mark.parametrize(
    "patch",
    [
        pytest.param({"status": "rejected"}, id="odrzucone-bez-powodu"),
        pytest.param({"status": "rejected", "rejection_reason": "bo-tak"}, id="powod-spoza-listy"),
        pytest.param({"status": "parked"}, id="odlozone-bez-progu"),
        pytest.param({"status": "duplicate"}, id="duplikat-bez-oryginalu"),
        pytest.param({"status": "accepted"}, id="przyjete-bez-zmiany"),
        pytest.param({"status": "needs-triage"}, id="stan-tf-zamiast-pdi"),
        pytest.param({"id": "prb-12"}, id="klucz-malymi-literami"),
        pytest.param({"channel": "fax"}, id="kanal-spoza-listy"),
    ],
)
def test_invalid_problems_are_rejected(patch: dict[str, Any]) -> None:
    base = {**{k: v for k, v in example("problem").items() if k not in {"change", "triage_decision"}}, "status": "new"}
    assert contract.errors("problem", base) == []  # każdy przypadek psuje dokładnie jedną rzecz

    assert contract.errors("problem", {**base, **patch}) != []


@pytest.mark.parametrize(
    "patch",
    [
        pytest.param({"status": "rejected", "rejection_reason": "out_of_strategy"}, id="odrzucone"),
        pytest.param({"status": "parked", "return_when": "3 nowe zgłoszenia albo incydent"}, id="odlozone"),
        pytest.param({"status": "duplicate", "duplicate_of": "PRB-7"}, id="duplikat"),
        pytest.param({"status": "clarifying"}, id="doprecyzowanie"),
    ],
)
def test_problem_states_with_required_details_are_valid(patch: dict[str, Any]) -> None:
    base = {k: v for k, v in example("problem").items() if k not in {"change", "status"}}

    assert contract.errors("problem", {**base, **patch}) == []


# --- artefakt zmiany (CHG) ---


def test_change_header_is_flat_yaml_compatible_with_tf() -> None:
    header = example("change")

    assert all(
        isinstance(v, str | int) or (isinstance(v, list) and all(isinstance(i, str) for i in v))
        for v in header.values()
    )


@pytest.mark.parametrize(
    "patch",
    [
        pytest.param({"artifact": "spec"}, id="artefakt-spoza-listy"),
        pytest.param({"change": "chg12"}, id="zmiana-z-kluczem-niepoprawnym"),
        pytest.param({"status": "approved"}, id="status-spoza-tf"),
        pytest.param({"version": 0}, id="wersja-od-1"),
        pytest.param({"tasks": [{"id": "TSK-1"}]}, id="zagniezdzone-obiekty"),
    ],
)
def test_invalid_change_headers_are_rejected(patch: dict[str, Any]) -> None:
    assert contract.errors("change", {**example("change"), **patch}) != []


def test_change_header_requires_change_id() -> None:
    header = {k: v for k, v in example("change").items() if k != "change"}

    assert any("change" in e for e in contract.errors("change", header))


# --- cięcie (TSK) ---


def test_task_requires_parent_change() -> None:
    task = {k: v for k, v in example("task").items() if k != "parent"}

    assert any("parent" in e for e in contract.errors("task", task))


# --- zdarzenia ---


def test_event_type_outside_list_is_rejected() -> None:
    assert contract.errors("event", {**example("event-gate.decided"), "type": "gate.closed"}) != []


@pytest.mark.parametrize("event_type", EVENT_TYPES)
def test_event_payload_must_match_its_type(event_type: str) -> None:
    other = "metric.breached" if event_type != "metric.breached" else "gate.decided"
    mismatched = {**example(f"event-{event_type}"), "payload": example(f"event-{other}")["payload"]}

    assert contract.errors("event", mismatched) != []


def test_event_requires_contract_version_and_utc_timestamp() -> None:
    event = example("event-feature.released")

    assert contract.errors("event", {k: v for k, v in event.items() if k != "contract_version"}) != []
    assert contract.errors("event", {**event, "occurred_at": "2026-10-23 10:00"}) != []


def test_basis_invalidated_attention_level_is_0_to_3() -> None:
    event = example("event-decision.basis_invalidated")

    assert contract.errors("event", {**event, "payload": {**event["payload"], "attention_level": 4}}) != []


# --- decyzja: wspólny wzorzec klucza ---


def test_decision_schema_uses_shared_key_pattern() -> None:
    assert contract.load("decision")["properties"]["id"]["pattern"] == contract.settings()["key_pattern"]
