"""Decyzje przypięte do ścieżek (`applies_to`, kontrakt 0.22.0; docs/plan-applies-to.md)."""

import json
from typing import Any

import pytest

from pdi import applies_to, contract
from pdi.inbox import Inbox
from pdi.mcp_server import build_server
from pdi.registry import InvalidDecision, Registry
from tests.conftest import draft
from tests.drafting import record_via_draft
from tests.test_decision_recorded import recorded_event

CASES = json.loads((contract.CONTRACT_DIR / "fixtures/applies-to/cases.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CASES["cases"], ids=lambda c: f"{c['pattern']}~{c['path']}")
def test_at01_every_contract_case_matches_as_stated(case: dict[str, Any]) -> None:
    assert applies_to.matches(case["pattern"], case["path"]) is case["match"]


def seed(registry: Registry) -> dict[str, str]:
    docs = registry.record(
        draft(statement="Przetwarzanie dokumentów idzie przez kolejkę.", applies_to={"paths": ["services/docs/**"]})
    )
    billing = registry.record(draft(statement="Faktury liczymy w groszach.", applies_to={"components": ["billing"]}))
    loose = registry.record(draft(statement="Decyzja bez przypięcia do kodu."))
    return {"docs": docs["id"], "billing": billing["id"], "loose": loose["id"]}


def test_at02_find_by_paths_returns_only_matching_decisions_with_what_matched(registry: Registry) -> None:
    ids = seed(registry)
    found = registry.find(paths=["services/docs/api/handler.py", "README.md"])
    assert [d["id"] for d in found] == [ids["docs"]]
    assert found[0]["applies_to"] == {"paths": ["services/docs/**"]}
    assert found[0]["matched"] == {"paths": ["services/docs/api/handler.py"], "components": []}
    assert "why" in found[0] and "load_bearing_assumptions" in found[0]


def test_at03_find_by_components_and_paths_together(registry: Registry) -> None:
    ids = seed(registry)
    found = registry.find(paths=["services/docs/a.py"], components=["billing"])
    assert {d["id"] for d in found} == {ids["docs"], ids["billing"]}
    billing = next(d for d in found if d["id"] == ids["billing"])
    assert billing["matched"] == {"paths": [], "components": ["billing"]}
    assert registry.find(paths=["src/other.py"]) == []


def test_at04_superseded_decisions_are_left_out_unless_asked(registry: Registry) -> None:
    ids = seed(registry)
    new = registry.supersede(
        ids["docs"], draft(statement="Dokumenty przetwarzamy synchronicznie.", applies_to={"paths": ["services/docs"]})
    )
    assert [d["id"] for d in registry.find(paths=["services/docs/a.py"])] == [new["id"]]
    old = registry.find(paths=["services/docs/a.py"], status="superseded")
    assert [d["id"] for d in old] == [ids["docs"]]


def test_at05_query_words_still_filter_path_matches(registry: Registry) -> None:
    ids = seed(registry)
    assert [d["id"] for d in registry.find("kolejkę", paths=["services/docs/a.py"])] == [ids["docs"]]
    assert registry.find("groszach", paths=["services/docs/a.py"]) == []


def test_at06_an_invalid_pattern_is_rejected_by_the_contract(registry: Registry) -> None:
    with pytest.raises(InvalidDecision):
        registry.record(draft(applies_to={"paths": ["../secrets"]}))


def test_at07_applies_to_is_kept_in_the_decision_file(registry: Registry) -> None:
    ids = seed(registry)
    assert registry.get(ids["docs"])["applies_to"] == {"paths": ["services/docs/**"]}


def test_at08_decision_recorded_carries_applies_to_into_the_registry(registry: Registry) -> None:
    result = Inbox(registry).receive(recorded_event(applies_to={"paths": ["packages/core/**"]}))
    assert registry.get(result["decision"])["applies_to"] == {"paths": ["packages/core/**"]}


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_at09_mcp_record_and_find_by_paths(registry: Registry) -> None:
    server = build_server(lambda: registry)
    rec = await record_via_draft(
        server, registry, draft(statement="Moduł inbox nie importuje konsoli.", applies_to={"paths": ["src/pdi"]})
    )
    dec_id = rec["id"]
    found = await server.call_tool("find_decisions", {"paths": ["src/pdi/inbox.py"]})
    assert found.is_error is False
    hits = found.structured_content["decisions"]
    assert [d["id"] for d in hits] == [dec_id] and hits[0]["matched"]["paths"] == ["src/pdi/inbox.py"]
    none = await server.call_tool("find_decisions", {"components": ["billing"]})
    assert none.structured_content["decisions"] == []
