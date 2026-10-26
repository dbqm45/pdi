"""Zestaw wzorcowy kształtu historyjki (contract/fixtures/story-shape): spójność danych, etykiet i słownika."""

import json
import re
from collections import Counter
from typing import Any

import pytest

from pdi import contract

FIXTURES = contract.CONTRACT_DIR / "fixtures" / "story-shape"
RULES = {"STORY-001", "STORY-002", "STORY-003", "AC-001", "AC-002", "AC-003", "AC-004"}


def load(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


STORIES: list[dict[str, Any]] = load("stories.json")["stories"]
EXPECTED: dict[str, Any] = load("expected.json")
VOCAB: dict[str, Any] = load("vocabulary.json")
CASES: dict[str, dict[str, Any]] = EXPECTED["cases"]


def fires(story_id: str, rule: str) -> bool:
    return rule in CASES[story_id]["fire"]


def test_files_are_valid_against_fixture_schemas() -> None:
    assert contract.errors("story_shape_stories", load("stories.json")) == []
    assert contract.errors("story_shape_expected", EXPECTED) == []


def test_expected_matches_current_contract_version_and_default_policy() -> None:
    # Zestaw ma wersję kontraktu, w której ostatnio się zmienił (0.4.0); nie może być nowszy niż bieżący kontrakt.
    def ver(v: str) -> tuple[int, ...]:
        return tuple(int(x) for x in v.split("."))

    assert EXPECTED["contract_version"] == "0.4.0"
    assert ver(EXPECTED["contract_version"]) <= ver(contract.CONTRACT_VERSION)
    assert EXPECTED["policy"] == {"acFormat": "gwt", "maxScenarios": 6, "maxActions": 3, "maxStoryPoints": 13}
    assert set(EXPECTED["rules"]) == RULES


def test_every_story_has_expectation_and_vice_versa() -> None:
    ids = [s["id"] for s in STORIES]

    assert len(ids) == len(set(ids))
    assert set(ids) == set(CASES)


def test_size_and_language_balance() -> None:
    langs = Counter(s["lang"] for s in STORIES)

    assert len(STORIES) >= 40
    assert langs["pl"] >= 15 and langs["en"] >= 15
    assert sum(1 for c in CASES.values() if not c["fire"]) >= 10  # historyjki bez uwag — miara precyzji


@pytest.mark.parametrize("rule", sorted(RULES))
def test_each_rule_has_positive_cases_in_both_languages(rule: str) -> None:
    langs = Counter(s["lang"] for s in STORIES if fires(s["id"], rule))

    assert sum(langs.values()) >= 3
    assert langs["pl"] >= 1 and langs["en"] >= 1


def test_only_known_rules_are_expected() -> None:
    for case in CASES.values():
        assert set(case["fire"]) <= RULES


# --- zgodność etykiet ze słownikiem (reguły oparte na słowniku) ---


def implementation_hit(text: str) -> bool:
    for term in VOCAB["implementation_terms"]:
        flags = 0 if term.get("case_sensitive") else re.IGNORECASE
        if re.search(term["pattern"], text, flags):
            return True
    return False


def weak_result_hit(text: str, lang: str) -> bool:
    low = text.lower()
    return any(phrase in low for phrase in VOCAB["weak_results"][lang])


def layer_hit(title: str) -> bool:
    tokens = re.findall(r"[\w/.-]+", title)
    exact = set(VOCAB["layer_terms"]["case_sensitive"])
    loose = {t.lower() for t in VOCAB["layer_terms"]["case_insensitive"]}
    return any(t.rstrip(":") in exact or t.rstrip(":").lower() in loose for t in tokens)


@pytest.mark.parametrize("story", STORIES, ids=lambda s: s["id"])
def test_ac_003_label_agrees_with_implementation_terms(story: dict[str, Any]) -> None:
    assert fires(story["id"], "AC-003") == implementation_hit(story["acceptance_criteria"])


@pytest.mark.parametrize("story", STORIES, ids=lambda s: s["id"])
def test_ac_002_label_agrees_with_weak_results(story: dict[str, Any]) -> None:
    assert fires(story["id"], "AC-002") == weak_result_hit(story["acceptance_criteria"], story["lang"])


@pytest.mark.parametrize("story", STORIES, ids=lambda s: s["id"])
def test_story_003_label_agrees_with_layer_terms_in_title(story: dict[str, Any]) -> None:
    assert fires(story["id"], "STORY-003") == layer_hit(story["title"])


def test_story_002_story_points_boundary() -> None:
    limit = EXPECTED["policy"]["maxStoryPoints"]
    pointed = [s for s in STORIES if "story_points" in s]

    assert any(s["story_points"] == limit - 1 for s in pointed)  # brzeg: tuż pod progiem
    for s in pointed:
        if s["story_points"] >= limit:
            assert fires(s["id"], "STORY-002")


def test_scenario_count_boundary_is_covered() -> None:
    limit = EXPECTED["policy"]["maxScenarios"]
    counts = {sid: c["scenarios"] for sid, c in CASES.items()}

    assert any(n == limit and not fires(sid, "STORY-002") for sid, n in counts.items())
    assert any(n == limit + 1 and fires(sid, "STORY-002") for sid, n in counts.items())


def test_policy_overrides_are_exercised() -> None:
    formats = {c.get("policy", {}).get("acFormat") for c in CASES.values()}

    assert {"ears", "any"} <= formats


# --- słownik ---


def test_gherkin_keywords_match_cucumber_languages() -> None:
    kw = VOCAB["keywords"]

    assert kw["en"] == {"given": ["Given"], "when": ["When"], "then": ["Then"], "and": ["And"], "but": ["But"]}
    assert kw["pl"]["given"] == ["Zakładając, że", "Zakładając", "Mając"]
    assert kw["pl"]["when"] == ["Jeżeli", "Jeśli", "Gdy", "Kiedy"]
    assert kw["pl"]["then"] == ["Wtedy"]
    assert kw["pl"]["and"] == ["Oraz", "I"]
    assert kw["pl"]["but"] == ["Ale"]


def test_regexes_use_portable_syntax() -> None:
    for term in VOCAB["implementation_terms"]:
        pattern = term["pattern"]
        re.compile(pattern)
        assert "(?<" not in pattern and "(?P" not in pattern  # bez lookbehind i grup nazwanych (JS)
        assert not re.search(
            r"\\b[^\x00-\x7f]|[^\x00-\x7f]\\b", pattern
        )  # \b przy literach spoza ASCII nie działa w JS
