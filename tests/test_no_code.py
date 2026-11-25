"""DV7: rozwiązanie bez kodu w triażu (kontrakt 0.24.0; docs/plan-dv7-bez-kodu.md)."""

import json
from typing import Any

import pytest

from pdi import console
from pdi.mcp_server import build_server
from pdi.problems import ProblemStore
from pdi.registry import InvalidDecision, Registry
from tests.test_console import TOKEN, _get, _post, _serve
from tests.test_problems import FakeHook, problem, store

HOW = "W Ustawieniach → Grupy ładowarek ustaw taryfę dla grupy; zmienia się na wszystkich naraz."


def test_nc01_a_no_code_rejection_is_stored_and_the_reporter_learns_what_to_do(
    registry: Registry, make_draft: Any
) -> None:
    hook = FakeHook()
    problems = store(registry, hook)
    problems.record(problem())
    result = problems.triage(
        "PRB-1",
        "rejected",
        make_draft(statement="PRB-1 rozwiązujemy konfiguracją grup."),
        rejection_reason="no_code",
        no_code={"kind": "configuration", "how": HOW},
    )
    stored = problems.get("PRB-1")
    assert (stored["status"], stored["rejection_reason"]) == ("rejected", "no_code")
    assert stored["no_code"] == {"kind": "configuration", "how": HOW}
    assert "problem:rejected" in result["decision"]["tags"] and "bez-kodu" in result["decision"]["tags"]
    sent = hook.bodies()[0]
    assert "bez zmian w systemie" in sent["message"] and HOW in sent["message"]


def test_nc02_no_code_needs_the_object_and_only_with_that_reason(registry: Registry, make_draft: Any) -> None:
    problems = store(registry)
    problems.record(problem())
    with pytest.raises(InvalidDecision):
        problems.triage("PRB-1", "rejected", make_draft(), rejection_reason="no_code")
    with pytest.raises(InvalidDecision):
        problems.triage(
            "PRB-1", "rejected", make_draft(), rejection_reason="other", no_code={"kind": "configuration", "how": HOW}
        )
    with pytest.raises(InvalidDecision):
        problems.triage(
            "PRB-1", "rejected", make_draft(), rejection_reason="no_code", no_code={"kind": "magic", "how": HOW}
        )
    assert problems.get("PRB-1")["status"] == "new" and registry.decisions() == []


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_nc03_mcp_triage_problem_takes_no_code(registry: Registry, make_draft: Any) -> None:
    ProblemStore(registry).record(problem())
    server = build_server(lambda: registry)
    result = await server.call_tool(
        "triage_problem",
        {
            "problem_id": "PRB-1",
            "outcome": "rejected",
            "rejection_reason": "no_code",
            "no_code": {"kind": "existing_feature", "how": "Użyj eksportu zbiorczego w menu Raporty."},
            **{k: v for k, v in make_draft().items() if k != "kind"},
        },
    )
    assert result.is_error is False
    assert ProblemStore(registry).get("PRB-1")["no_code"]["kind"] == "existing_feature"


def test_nc04_console_rejects_without_code_with_kind_and_how(registry: Registry) -> None:
    ProblemStore(registry).record(problem())
    server, url = _serve(console.Deps(registry, checkout=None))
    try:
        page = _get(f"{url}/inbox?t={TOKEN}")[1].decode()
        assert 'name="no_code_kind"' in page and 'name="no_code_how"' in page and 'value="no_code"' in page
        form = {
            "t": TOKEN,
            "statement": "Bez kodu.",
            "why": "Konfiguracja grup wystarcza.",
            "outcome": "rejected",
            "rejection_reason": "no_code",
            "no_code_kind": "configuration",
        }
        assert _post(f"{url}/problems/PRB-1/triage?t={TOKEN}", form)[0] == 409  # bez „jak”
        status, body = _post(f"{url}/problems/PRB-1/triage?t={TOKEN}", {**form, "no_code_how": HOW})
        assert status == 200, body
        stored = ProblemStore(registry).get("PRB-1")
        assert stored["no_code"] == {"kind": "configuration", "how": HOW}
        assert json.dumps(stored, ensure_ascii=False).count("no_code") >= 2
    finally:
        server.shutdown()
