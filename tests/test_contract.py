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
    "release.stage_changed",
    "decision.proposed",
    "decision.auto_applied",
    "decision.vetoed",
    "run.progress",
]


def example(name: str) -> dict[str, Any]:
    data = json.loads((contract.CONTRACT_DIR / "examples" / f"{name}.json").read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def schema_for(path: Path) -> str:
    if path.stem.startswith("event-"):
        return "event"
    return path.stem.replace("-", "_")


@pytest.mark.parametrize("name", contract.SCHEMA_NAMES)
def test_schema_is_valid_json_schema_2020_12(name: str) -> None:
    Draft202012Validator.check_schema(contract.load(name))


def test_settings_define_version_key_pattern_and_default_prefixes() -> None:
    settings = contract.settings()

    assert settings["version"] == contract.CONTRACT_VERSION == "0.5.0"
    assert settings["prefixes"] == {"problem": "PRB", "change": "CHG", "task": "TSK", "decision": "DEC"}
    assert settings["key_pattern"] == "^[A-Z][A-Z0-9]+-[0-9]+$"


def test_every_schema_and_event_type_has_an_example() -> None:
    names = {schema_for(p) for p in EXAMPLES if not p.stem.startswith("event-")}
    stems = {p.stem for p in EXAMPLES}

    assert set(contract.SCHEMA_NAMES) - {"event"} == names
    assert {"story", "release_plan", "autonomy"} <= set(contract.SCHEMA_NAMES)
    assert {f"event-{t}" for t in EVENT_TYPES} <= stems


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


# --- kontrakt 0.4.0: historyjka (story) ---


def story_with_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    return {**example("story"), "scenarios": [scenario]}


@pytest.mark.parametrize(
    "scenario",
    [
        pytest.param({"id": "AC-1", "format": "gwt", "given": ["x"], "when": "y"}, id="gwt-bez-then"),
        pytest.param({"id": "AC-1", "format": "gwt", "then": ["z"]}, id="gwt-bez-when"),
        pytest.param({"id": "AC-1", "format": "ears", "when": "y"}, id="ears-bez-then"),
        pytest.param({"id": "AC-1", "format": "free"}, id="wolny-tekst-bez-tresci"),
        pytest.param({"id": "1", "format": "free", "text": "x"}, id="id-nie-ac"),
        pytest.param({"id": "AC-1", "format": "bdd", "text": "x"}, id="format-spoza-listy"),
    ],
)
def test_invalid_story_scenarios_are_rejected(scenario: dict[str, Any]) -> None:
    assert contract.errors("story", story_with_scenario(scenario)) != []


@pytest.mark.parametrize(
    "scenario",
    [
        pytest.param({"id": "AC-2", "format": "gwt", "when": "y", "then": ["z"]}, id="gwt-bez-given"),
        pytest.param({"id": "AC-2", "format": "ears", "then": ["the system shall log out"]}, id="ears-wszechobecne"),
        pytest.param({"id": "AC-2", "format": "free", "text": "Klient widzi potwierdzenie."}, id="wolny-tekst"),
    ],
)
def test_valid_story_scenarios(scenario: dict[str, Any]) -> None:
    assert contract.errors("story", story_with_scenario(scenario)) == []


def test_story_requires_actor_and_capability() -> None:
    for field in ("actor", "capability"):
        story = {k: v for k, v in example("story").items() if k != field}
        assert any(field in e for e in contract.errors("story", story))


# --- kontrakt 0.4.0: plan wydania ---


@pytest.mark.parametrize(
    "patch",
    [
        pytest.param({"releases": [{"id": "MVP", "tasks": ["TSK-1"]}]}, id="linia-nie-rn"),
        pytest.param({"change": "chg12"}, id="zly-klucz-zmiany"),
        pytest.param({"flags": [{"key": "x", "remove_by": "31.12.2026"}]}, id="data-usuniecia-nie-iso"),
        pytest.param({"flags": [{"key": "x", "rollout": [{"stage": "10%", "min_days": -1}]}]}, id="ujemne-dni"),
        pytest.param({"mvp": {"release": "R1", "metric": {"name": "x"}}}, id="metryka-bez-celu"),
    ],
)
def test_invalid_release_plans_are_rejected(patch: dict[str, Any]) -> None:
    assert contract.errors("release_plan", {**example("release-plan"), **patch}) != []


def test_release_plan_requires_change_and_releases() -> None:
    for field in ("change", "releases"):
        plan = {k: v for k, v in example("release-plan").items() if k != field}
        assert any(field in e for e in contract.errors("release_plan", plan))


def test_flag_without_rollout_plan_is_valid_schema_but_rule_material() -> None:
    plan = {**example("release-plan"), "flags": [{"key": "payment-retry"}]}

    assert contract.errors("release_plan", plan) == []  # brak etapów wykrywa REL-007, nie schemat


# --- kontrakt 0.4.0: nowe pola cięcia i zdarzeń ---


@pytest.mark.parametrize(
    "patch",
    [
        pytest.param({"kind": "layer"}, id="rodzaj-spoza-listy"),
        pytest.param({"release": "MVP"}, id="linia-nie-rn"),
        pytest.param({"unblocks": ["tsk-1"]}, id="zly-klucz-odblokowania"),
        pytest.param({"skeleton": "tak"}, id="szkielet-nie-bool"),
    ],
)
def test_invalid_task_extensions_are_rejected(patch: dict[str, Any]) -> None:
    assert contract.errors("task", {**example("task"), **patch}) != []


def test_task_extensions_are_optional_and_valid() -> None:
    task = {
        **example("task"),
        "kind": "slice",
        "release": "R1",
        "flag": "payment-retry",
        "unblocks": [],
        "skeleton": True,
    }

    assert contract.errors("task", task) == []


def test_feature_released_may_name_release_line() -> None:
    event = example("event-feature.released")
    with_line = {**event, "payload": {**event["payload"], "release": "R1"}}

    assert contract.errors("event", with_line) == []
    assert contract.errors("event", {**event, "payload": {**event["payload"], "release": "MVP"}}) != []


def test_stage_changed_rollout_is_percent() -> None:
    event = example("event-release.stage_changed")

    assert contract.errors("event", {**event, "payload": {**event["payload"], "rollout": 120}}) != []


def test_conventions_hold_defaults_for_undecided_choices() -> None:
    conventions = contract.settings()["conventions"]

    assert conventions["acceptance_criteria"]["default_format"] == "gwt"
    assert conventions["jira"]["release_line"] == {"mode": "label", "prefix": "release:"}
    assert conventions["repo"]["release_plan_file"] == "release.yaml"


# --- kontrakt 0.5.0: poziomy autonomii (A0, decyzje DA1 i DA2) ---

PROTECTED = ["triage", "scope.r1", "release.go", "outcome.assessment", "review.sensitive", "migration"]
CANDIDATES = [
    "finding.auto_close",
    "ac.format_rewrite",
    "flag.stage_advance",
    "flag.removal_pr",
    "dependency.update",
    "review.light",
]


def test_autonomy_defaults_follow_da2() -> None:
    autonomy = contract.settings()["autonomy"]

    assert autonomy["default_level"] == 3
    assert autonomy["lower_when"] == {"last_decisions": 30, "min_unedited_share": 0.95}
    assert autonomy["raise_when"] == {"max_edited_share": 0.10}
    assert autonomy["protected_types"] == PROTECTED
    assert [t["decision_type"] for t in autonomy["decision_types"]] == CANDIDATES + PROTECTED
    assert all(t["default_level"] == 3 for t in autonomy["decision_types"])


def test_catalog_types_match_decision_type_pattern() -> None:
    pattern = contract.load("decision")["properties"]["decision_type"]["pattern"]
    for t in contract.settings()["autonomy"]["decision_types"]:
        assert contract.errors("decision", {**example("decision"), "decision_type": t["decision_type"]}) == [], pattern


def test_protected_types_in_policy_schema_match_catalog() -> None:
    schema = contract.load("autonomy")
    rule = schema["$defs"]["entry"]["allOf"][0]

    assert rule["if"]["properties"]["decision_type"]["enum"] == contract.settings()["autonomy"]["protected_types"]


def policy_with(entry: dict[str, Any]) -> dict[str, Any]:
    return {**example("autonomy"), "policy": [entry]}


@pytest.mark.parametrize("decision_type", PROTECTED)
def test_protected_type_cannot_be_lowered(decision_type: str) -> None:
    assert (
        contract.errors("autonomy", policy_with({"decision_type": decision_type, "level": 2, "veto_window": "PT4H"}))
        != []
    )
    assert contract.errors("autonomy", policy_with({"decision_type": decision_type, "level": 3})) == []


@pytest.mark.parametrize(
    "entry",
    [
        pytest.param({"decision_type": "flag.stage_advance", "level": 2}, id="poziom-2-bez-okna-weta"),
        pytest.param({"decision_type": "flag.stage_advance", "level": 4}, id="poziom-spoza-0-3"),
        pytest.param({"decision_type": "Flag Stage", "level": 3}, id="typ-nie-klucz"),
        pytest.param({"decision_type": "flag.stage_advance", "level": 2, "veto_window": "4h"}, id="okno-nie-iso-8601"),
        pytest.param(
            {
                "decision_type": "review.light",
                "level": 3,
                "lower_when": {"last_decisions": 30, "min_unedited_share": 1.5},
            },
            id="udzial-ponad-1",
        ),
    ],
)
def test_invalid_policy_entries_are_rejected(entry: dict[str, Any]) -> None:
    assert contract.errors("autonomy", policy_with(entry)) != []


@pytest.mark.parametrize(
    "patch",
    [
        pytest.param({"automation": {"level": 3}}, id="poziom-3-to-czlowiek-nie-automat"),
        pytest.param({"automation": {"level": 2, "rule": "x"}}, id="poziom-2-bez-veto-until"),
        pytest.param({"drafted_by": "human", "draft_edited": True}, id="draft-edited-bez-szkicu-ai"),
        pytest.param({"decision_type": "Flag.Stage"}, id="typ-z-wielkimi-literami"),
        pytest.param({"source": {"kind": "teams"}}, id="zrodlo-spoza-listy"),
    ],
)
def test_invalid_decision_autonomy_fields_are_rejected(patch: dict[str, Any]) -> None:
    assert contract.errors("decision", {**example("decision"), **patch}) != []


@pytest.mark.parametrize(
    "patch",
    [
        pytest.param(
            {"decision_type": "flag.stage_advance", "automation": {"level": 1, "rule": "kryteria wyjścia spełnione"}},
            id="automat-z-logiem",
        ),
        pytest.param(
            {"automation": {"level": 2, "rule": "x", "veto_until": "2026-10-27T10:00:00Z", "vetoed_by": "dbqm45"}},
            id="zawetowane",
        ),
        pytest.param({"drafted_by": "ai", "draft_edited": False}, id="szkic-ai-bez-zmian"),
        pytest.param({"source": {"kind": "console"}}, id="zrodlo-konsola"),
    ],
)
def test_valid_decision_autonomy_fields(patch: dict[str, Any]) -> None:
    assert contract.errors("decision", {**example("decision"), **patch}) == []


def test_decision_without_autonomy_fields_stays_valid() -> None:
    plain = {k: v for k, v in example("decision").items() if k not in {"decision_type", "automation", "draft_edited"}}

    assert contract.errors("decision", plain) == []


def test_proposed_level_2_requires_veto_until() -> None:
    event = example("event-decision.proposed")
    payload = {k: v for k, v in event["payload"].items() if k != "veto_until"}

    assert contract.errors("event", {**event, "payload": {**payload, "level": 2}}) != []
    assert contract.errors("event", {**event, "payload": {**payload, "level": 3}}) == []


def test_auto_applied_cannot_be_level_3() -> None:
    event = example("event-decision.auto_applied")

    assert contract.errors("event", {**event, "payload": {**event["payload"], "level": 3}}) != []


def test_run_progress_status_and_cost() -> None:
    event = example("event-run.progress")

    assert contract.errors("event", {**event, "payload": {**event["payload"], "status": "paused"}}) != []
    assert contract.errors("event", {**event, "payload": {**event["payload"], "cost_usd": -1}}) != []


def test_events_from_contract_0_4_0_are_still_valid() -> None:
    for t in EVENT_TYPES[:8]:  # typy istniejące w 0.4.0
        assert contract.errors("event", {**example(f"event-{t}"), "contract_version": "0.4.0"}) == []
