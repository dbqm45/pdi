"""DV3: kontekst zmiany na start zadania (docs/plan-dv3-kontekst-zmiany.md)."""

from typing import Any

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from pdi import context
from pdi.changes import ChangeNotFound
from pdi.inbox import Inbox
from pdi.mcp_server import build_server
from pdi.problems import ProblemStore
from pdi.registry import Registry
from tests.conftest import draft
from tests.test_inbox import gate_event
from tests.test_problems import problem


def seed(registry: Registry) -> dict[str, Any]:
    prb = ProblemStore(registry).record(problem())
    intent = registry.record(
        draft(
            statement="Operator zmienia taryfę na wielu ładowarkach naraz.",
            kind="intent",
            success_metric={"metric": "czas zmiany taryfy na 200 ładowarkach", "target": "< 10 min"},
            links={"chg": "CHG-12", "prb": prb["id"]},
        )
    )
    choice = registry.record(
        draft(
            statement="Zmiany idą przez kolejkę zadań.",
            kind="technical",
            options=[
                {"option": "kolejka zadań", "chosen": True},
                {"option": "jedno żądanie synchroniczne", "chosen": False, "note": "limit czasu bramki API"},
            ],
            assumptions=[
                {"statement": "Ładowarki odpowiadają w 30 s.", "load_bearing": True, "invalidated_if": "timeouty > 5%"}
            ],
            applies_to={"paths": ["services/bulk/**"]},
            links={"chg": "CHG-12"},
        )
    )
    code = registry.record(
        draft(statement="API ładowarek wołamy tylko przez adapter OCPP.", applies_to={"paths": ["services/**"]})
    )
    other = registry.record(draft(statement="Inna zmiana.", links={"chg": "CHG-99"}))
    Inbox(registry).receive(
        gate_event(
            questions=["Czy limit to 1000 ładowarek na zadanie?"],
            default_option="1000",
            reversibility="local",
        )
    )
    return {"prb": prb, "intent": intent, "choice": choice, "code": code, "other": other}


def test_dv3_01_why_the_change_exists(registry: Registry) -> None:
    s = seed(registry)
    c = context.reconstruct(registry, "CHG-12")
    assert c["intent"]["id"] == s["intent"]["id"]
    assert c["intent"]["success_metric"]["target"] == "< 10 min"
    assert c["problem"]["id"] == s["prb"]["id"]
    assert c["problem"]["cannot"].startswith("zmienić konfiguracji")


def test_dv3_02_decisions_of_the_change_show_rejected_options(registry: Registry) -> None:
    s = seed(registry)
    c = context.reconstruct(registry, "CHG-12")
    ids = [d["id"] for d in c["decisions"]]
    assert s["choice"]["id"] in ids and s["intent"]["id"] in ids and s["other"]["id"] not in ids
    choice = next(d for d in c["decisions"] if d["id"] == s["choice"]["id"])
    assert choice["rejected_options"] == [{"option": "jedno żądanie synchroniczne", "note": "limit czasu bramki API"}]
    assert choice["load_bearing_assumptions"][0]["invalidated_if"] == "timeouty > 5%"


def test_dv3_03_decisions_for_the_files_without_repeats(registry: Registry) -> None:
    s = seed(registry)
    c = context.reconstruct(registry, "CHG-12", paths=["services/bulk/queue.py"])
    assert [d["id"] for d in c["code_decisions"]] == [s["code"]["id"]]  # choice już jest w decisions
    assert c["code_decisions"][0]["matched"]["paths"] == ["services/bulk/queue.py"]


def test_dv3_04_open_questions_and_waiting_gates(registry: Registry) -> None:
    seed(registry)
    c = context.reconstruct(registry, "CHG-12")
    q = c["open_questions"]
    assert len(q) == 1 and q[0]["gate"] == "B1" and q[0]["questions"] == ["Czy limit to 1000 ładowarek na zadanie?"]
    assert q[0]["default_option"] == "1000" and q[0]["reversibility"] == "local"
    assert c["change"]["id"] == "CHG-12" and "B1" in c["change"]["waiting"]


def test_dv3_05_prs_and_gaps_come_from_the_trace(registry: Registry) -> None:
    seed(registry)
    c = context.reconstruct(registry, "CHG-12")
    assert c["prs"] == ["https://github.com/dbqm45/sklep/pull/7"]
    assert any("TSK" in gap for gap in c["gaps"])


def test_dv3_06_without_a_change_only_the_decisions_for_the_files(registry: Registry) -> None:
    s = seed(registry)
    c = context.reconstruct(registry, paths=["services/bulk/queue.py"])
    assert c["change"] is None and c["decisions"] == [] and c["open_questions"] == []
    assert {d["id"] for d in c["code_decisions"]} == {s["code"]["id"], s["choice"]["id"]}


def test_dv3_07_an_unknown_change_is_an_error(registry: Registry) -> None:
    with pytest.raises(ChangeNotFound):
        context.reconstruct(registry, "CHG-404")


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_dv3_08_mcp_change_context(registry: Registry) -> None:
    seed(registry)
    server = build_server(lambda: registry)
    result = await server.call_tool("change_context", {"change": "CHG-12", "paths": ["services/bulk/a.py"]})
    assert result.is_error is False
    body = result.structured_content
    assert body["change"]["id"] == "CHG-12" and body["intent"] is not None and body["code_decisions"]
    with pytest.raises(ToolError, match="CHG-404"):
        await server.call_tool("change_context", {"change": "CHG-404"})
