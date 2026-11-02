import json
from typing import Any

import pytest

from pdi.dispatch import DispatchConfig, dispatch_phase

AT = "2026-10-26T10:00:00Z"
TOKEN = "ghs_tajny_token"  # noqa: S105 — token testowy


class FakeGitHub:
    def __init__(self, status: int = 204, error: Exception | None = None) -> None:
        self.status = status
        self.error = error
        self.calls: list[tuple[str, dict[str, str], dict[str, Any]]] = []

    def __call__(self, url: str, headers: dict[str, str], body: bytes) -> int:
        self.calls.append((url, headers, json.loads(body)))
        if self.error:
            raise self.error
        return self.status


def config(**overrides: Any) -> DispatchConfig:
    base: dict[str, Any] = {"repo": "dbqm45/sklep", "token": TOKEN, "budget_usd": "5"}
    base.update(overrides)
    return DispatchConfig(**base)


def run(cfg: DispatchConfig, post: FakeGitHub, **overrides: Any) -> dict[str, Any]:
    args: dict[str, Any] = {
        "change": "CHG-12",
        "phase": "requirements",
        "gate": "B1",
        "outcome": "approved",
        "decision": "DEC-0001",
        "rework": False,
    }
    args.update(overrides)
    return dispatch_phase(cfg, post=post, at=AT, **args)


def test_sends_workflow_dispatch_with_string_inputs() -> None:
    github = FakeGitHub()

    result = run(config(), github)

    url, headers, body = github.calls[0]
    assert url == "https://api.github.com/repos/dbqm45/sklep/actions/workflows/sdlc-phase.yml/dispatches"
    assert headers["authorization"] == f"Bearer {TOKEN}"
    assert headers["accept"] == "application/vnd.github+json"
    assert body == {
        "ref": "main",
        "inputs": {
            "change": "CHG-12",
            "phase": "requirements",
            "gate": "B1",
            "outcome": "approved",
            "decision": "DEC-0001",
            "rework": "false",
            "budget_usd": "5",
        },
    }
    assert result == {
        "status": "sent",
        "phase": "requirements",
        "rework": False,
        "at": AT,
        "repo": "dbqm45/sklep",
        "workflow": "sdlc-phase.yml",
    }


def test_budget_is_left_out_when_not_set() -> None:
    github = FakeGitHub()

    run(config(budget_usd=None), github, rework=True)

    inputs = github.calls[0][2]["inputs"]
    assert "budget_usd" not in inputs
    assert inputs["rework"] == "true"


def test_without_repo_nothing_is_sent() -> None:
    github = FakeGitHub()

    result = run(config(repo=None), github)

    assert github.calls == []
    assert result["status"] == "skipped"
    assert "PDI_DISPATCH_REPO" in result["error"]


def test_without_token_nothing_is_sent() -> None:
    github = FakeGitHub()

    result = run(config(token=None), github)

    assert github.calls == []
    assert (result["status"], "PDI_GITHUB_TOKEN" in result["error"]) == ("failed", True)


@pytest.mark.parametrize(
    ("github", "fragment"),
    [(FakeGitHub(status=404), "404"), (FakeGitHub(error=OSError(f"timeout {TOKEN}")), "połączenia")],
    ids=["http-404", "siec"],
)
def test_failure_is_reported_without_the_token(github: FakeGitHub, fragment: str) -> None:
    result = run(config(), github)

    assert result["status"] == "failed"
    assert fragment in result["error"]
    assert TOKEN not in json.dumps(result)


@pytest.mark.parametrize(
    "overrides",
    [{"repo": "dbqm45/sklep/../x"}, {"repo": "bez-ukosnika"}, {"workflow": "../evil.yml"}, {"ref": ""}],
)
def test_bad_target_is_refused_before_sending(overrides: dict[str, Any]) -> None:
    github = FakeGitHub()

    result = run(config(**overrides), github)

    assert github.calls == []
    assert result["status"] == "failed"


def test_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PDI_DISPATCH_REPO", "dbqm45/sklep")
    monkeypatch.setenv("PDI_DISPATCH_WORKFLOW", "phase.yaml")
    monkeypatch.setenv("PDI_DISPATCH_REF", "trunk")
    monkeypatch.setenv("PDI_GITHUB_TOKEN", TOKEN)
    monkeypatch.delenv("PDI_PHASE_BUDGET_USD", raising=False)

    cfg = DispatchConfig.from_env()

    assert (cfg.repo, cfg.workflow, cfg.ref, cfg.token, cfg.budget_usd) == (
        "dbqm45/sklep",
        "phase.yaml",
        "trunk",
        TOKEN,
        None,
    )
    assert TOKEN not in repr(cfg)


def test_config_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("PDI_DISPATCH_REPO", "PDI_DISPATCH_WORKFLOW", "PDI_DISPATCH_REF", "PDI_GITHUB_TOKEN"):
        monkeypatch.delenv(var, raising=False)

    cfg = DispatchConfig.from_env()

    assert (cfg.repo, cfg.workflow, cfg.ref, cfg.token) == (None, "sdlc-phase.yml", "main", None)


def test_source_and_problem_are_sent_only_when_given() -> None:
    github = FakeGitHub()

    run(config(), github, phase="intent", source="PRB-3", problem='{"title": "T"}')
    run(config(), github)

    with_problem, plain = (c[2]["inputs"] for c in github.calls)
    assert (with_problem["source"], with_problem["problem"]) == ("PRB-3", '{"title": "T"}')
    assert "source" not in plain and "problem" not in plain


# --- Z1: treść decyzji, odpowiedzi i decyzje zmiany jako wejścia szablonu fazy ---

ANSWERS = [{"question": "Czy build.json zostaje w repo?", "answer": "Nie."}]
LINKED = [{"id": "DEC-0003", "statement": "build.json generuje build.", "why": "Powtarzalność."}]


def test_decision_text_answers_and_linked_decisions_go_as_json_inputs() -> None:
    github = FakeGitHub()

    result = run(config(), github, decision_text="Zatwierdzone. Dlaczego: ok.", answers=ANSWERS, decisions=LINKED)

    inputs = github.calls[0][2]["inputs"]
    assert inputs["decision_text"] == "Zatwierdzone. Dlaczego: ok."
    assert json.loads(inputs["answers"]) == ANSWERS
    assert json.loads(inputs["decisions"]) == LINKED
    assert all(isinstance(v, str) for v in inputs.values())
    assert result["status"] == "sent" and "warning" not in result


def test_without_them_the_inputs_are_as_before() -> None:
    github = FakeGitHub()

    run(config(), github, decision_text=None, answers=None, decisions=None)

    assert not {"decision_text", "answers", "decisions"} & set(github.calls[0][2]["inputs"])


class OldTemplate(FakeGitHub):
    """Szablon sdlc-phase.yml sprzed Z1: nieznane wejścia → 422."""

    def __call__(self, url: str, headers: dict[str, str], body: bytes) -> int:
        super().__call__(url, headers, body)
        return 422 if "decisions" in json.loads(body)["inputs"] else 204


def test_old_template_gets_the_phase_without_the_new_inputs_and_a_warning() -> None:
    github = OldTemplate()

    result = run(config(), github, decision_text="x", answers=ANSWERS, decisions=LINKED)

    assert len(github.calls) == 2
    assert not {"decision_text", "answers", "decisions"} & set(github.calls[1][2]["inputs"])
    assert result["status"] == "sent"
    assert "sdlc-phase.yml" in result["warning"]


def test_other_422_is_still_a_failure() -> None:
    github = FakeGitHub(status=422)

    result = run(config(), github)

    assert len(github.calls) == 1
    assert result["status"] == "failed"


def test_inputs_are_capped() -> None:
    from pdi import dispatch

    github = FakeGitHub()
    many = [{"id": f"DEC-{n}", "statement": "x" * 900, "why": "y" * 900} for n in range(60)]

    run(config(), github, decisions=many)

    sent = json.loads(github.calls[0][2]["inputs"]["decisions"])
    assert len(github.calls[0][2]["inputs"]["decisions"]) <= dispatch.INPUT_MAX
    assert sent[-1]["id"] == "DEC-59"  # zostają najnowsze
