from typing import Any

import pytest

from pdi.registry import SCHEMA_PATH, schema_errors

VALID: dict[str, Any] = {
    "id": "DEC-0001",
    "statement": "Próg darmowej dostawy zostaje na 199 zł.",
    "why": "Koszt paczki wzrósł po aneksie.",
    "decided_at": "2026-10-22",
    "decided_by": "właściciel",
    "recorded_at": "2026-10-23T09:30:00Z",
    "kind": "product",
    "source": {"kind": "slack", "url": "https://example.slack.com/archives/C1/p1", "excerpt": "zostaje"},
    "status": "recorded",
    "drafted_by": "ai",
    "options": [{"option": "199 zł", "chosen": True}, {"option": "149 zł", "chosen": False}],
    "evidence": [{"text": "koszt paczki 13,28 zł", "epistemic_status": "observation"}],
    "assumptions": [
        {
            "statement": "udział przewoźnika X ok. 65%",
            "load_bearing": True,
            "invalidated_if": "udział X < 40%",
        }
    ],
    "dependencies": ["przewoźnik X"],
    "success_metric": {"metric": "marża na zamówieniu", "target": ">= 0", "horizon": "Q4 2026"},
    "review_by": "2026-12-31",
    "links": {"chg": "CHG-12"},
    "tags": ["dostawa"],
}


def without(key: str) -> dict[str, Any]:
    return {k: v for k, v in VALID.items() if k != key}


def test_schema_file_lives_in_contract() -> None:
    assert SCHEMA_PATH.parts[-2:] == ("contract", "decision.schema.json")
    assert SCHEMA_PATH.is_file()


def test_full_decision_is_valid() -> None:
    assert schema_errors(VALID) == []


@pytest.mark.parametrize(
    "key", ["id", "statement", "why", "decided_at", "decided_by", "kind", "source", "status", "drafted_by"]
)
def test_required_field_missing_is_reported(key: str) -> None:
    errors = schema_errors(without(key))
    assert any(key in e for e in errors), errors


@pytest.mark.parametrize(
    "patch",
    [
        pytest.param({"kind": "whim"}, id="kind-spoza-listy"),
        pytest.param({"status": "deleted"}, id="status-spoza-listy"),
        pytest.param({"drafted_by": "robot"}, id="drafted-by-spoza-listy"),
        pytest.param({"id": "D-001"}, id="id-nie-dec"),
        pytest.param({"decided_at": "22.10.2026"}, id="data-nie-iso"),
        pytest.param({"source": {"kind": "teams"}}, id="zrodlo-spoza-listy"),
        pytest.param({"evidence": [{"text": "x", "epistemic_status": "fact"}]}, id="status-epistemiczny"),
        pytest.param({"assumptions": [{"statement": "x"}]}, id="zalozenie-bez-pol"),
        pytest.param({"statment": "literówka"}, id="nieznane-pole"),
        pytest.param({"statement": ""}, id="pusta-tresc"),
    ],
)
def test_invalid_values_are_rejected(patch: dict[str, Any]) -> None:
    assert schema_errors({**VALID, **patch}) != []
