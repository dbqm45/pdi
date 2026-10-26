import json
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.server.mcpserver.exceptions import ToolError

from pdi.inbox import Inbox
from pdi.mcp_server import build_server
from pdi.registry import Registry
from tests.test_inbox import stage_event

Draft = Callable[..., dict[str, Any]]
pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def server(registry: Registry):  # type: ignore[no-untyped-def]
    return build_server(lambda: registry)


async def call(server: Any, name: str, args: dict[str, Any]) -> Any:
    result = await server.call_tool(name, args)
    assert result.is_error is False
    return result.structured_content


async def test_exposes_task_oriented_tools(server: Any) -> None:
    tools = {t.name: t for t in await server.list_tools()}

    assert set(tools) == {
        "record_decision",
        "find_decisions",
        "get_decision",
        "supersede_decision",
        "list_inbox",
        "decide_inbox_item",
    }
    assert tools["list_inbox"].annotations.read_only_hint is True
    assert tools["decide_inbox_item"].annotations.read_only_hint is False
    assert tools["find_decisions"].annotations.read_only_hint is True
    assert tools["record_decision"].annotations.read_only_hint is False
    record_params = tools["record_decision"].input_schema["properties"]
    assert {"statement", "why", "kind", "source", "drafted_by", "assumptions", "project"} <= set(record_params)
    assert "project" in tools["find_decisions"].input_schema["properties"]


async def test_record_then_find_and_get(server: Any, make_draft: Draft) -> None:
    saved = await call(server, "record_decision", make_draft())

    found = await call(server, "find_decisions", {"query": "próg dostawy"})
    got = await call(server, "get_decision", {"decision_id": saved["id"]})

    assert saved["id"] == "DEC-0001"
    assert [d["id"] for d in found["decisions"]] == ["DEC-0001"]
    assert got["why"] == make_draft()["why"]


async def test_supersede_through_tool(server: Any, make_draft: Draft) -> None:
    await call(server, "record_decision", make_draft())

    new = await call(
        server,
        "supersede_decision",
        {"old_decision_id": "DEC-0001", **make_draft(statement="Próg obniżamy do 149 zł.")},
    )

    assert new["supersedes"] == "DEC-0001"


async def test_contract_violation_returns_fix_hint(server: Any, make_draft: Draft) -> None:
    with pytest.raises(ToolError, match="success_metric"):
        await server.call_tool("record_decision", make_draft(success_metric={"metric": "marża"}))


async def test_unknown_id_returns_hint(server: Any) -> None:
    with pytest.raises(ToolError, match="find_decisions"):
        await server.call_tool("get_decision", {"decision_id": "DEC-0404"})


async def test_missing_registry_path_returns_setup_hint(monkeypatch: pytest.MonkeyPatch, make_draft: Draft) -> None:
    monkeypatch.delenv("PDI_REGISTRY_PATH", raising=False)
    server = build_server()

    with pytest.raises(ToolError, match="PDI_REGISTRY_PATH"):
        await server.call_tool("record_decision", make_draft())


async def test_stdio_end_to_end(tmp_path: Path, make_draft: Draft) -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "pdi.mcp_server"],
        env={**os.environ, "PDI_REGISTRY_PATH": str(tmp_path / "rejestr")},
    )
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        listed = await session.list_tools()
        result = await session.call_tool("record_decision", make_draft())

    assert len(listed.tools) == 6
    assert json.loads(result.content[0].text)["id"] == "DEC-0001"
    assert (tmp_path / "rejestr" / "decisions" / "_ogolne" / "DEC-0001.md").is_file()


async def test_inbox_list_and_decide_through_tools(server: Any, registry: Registry, make_draft: Draft) -> None:
    Inbox(registry).receive(stage_event())

    listed = await call(server, "list_inbox", {})
    decided = await call(server, "decide_inbox_item", {"item_id": "evt-stage-1", "outcome": "approved", **make_draft()})

    assert [i["id"] for i in listed["items"]] == ["evt-stage-1"]
    assert decided["decision"]["kind"] == "gate"
    assert decided["decision"]["links"] == {"chg": "CHG-12"}
    assert (await call(server, "list_inbox", {}))["items"] == []


async def test_decide_inbox_item_errors_return_hints(server: Any, registry: Registry, make_draft: Draft) -> None:
    Inbox(registry).receive(stage_event())

    with pytest.raises(ToolError, match="list_inbox"):
        await server.call_tool("decide_inbox_item", {"item_id": "evt-nie-ma", **make_draft()})
    with pytest.raises(ToolError, match="outcome"):
        await server.call_tool("decide_inbox_item", {"item_id": "evt-stage-1", **make_draft()})
