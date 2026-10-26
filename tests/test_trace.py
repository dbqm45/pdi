import json
from datetime import date
from typing import Any

import pytest

from pdi.changes import ChangeNotFound
from pdi.impact import ShipScopeConfig
from pdi.inbox import Inbox
from pdi.registry import Registry
from pdi.trace import MAX_LIVE_ITEMS, mermaid, trace
from tests.test_inbox import gate_event, released_event

TOKEN = "shps_trace"  # noqa: S105 — token testowy
SHIPSCOPE = ShipScopeConfig(url="https://shipscope.example.com", token=TOKEN)


class FakeShipScope:
    def __init__(self, status: int = 200) -> None:
        self.status = status
        self.keys: list[str] = []

    def __call__(self, url: str, headers: dict[str, str]) -> tuple[int, bytes]:
        key = url.rsplit("/", 1)[-1]
        self.keys.append(key)
        if self.status != 200:
            return self.status, b"{}"
        prod = "released" if key == "CHG-12" else "deployed"
        body = {
            "key": key,
            "envs": {"test": {"status": "released"}, "qa": {"status": "released"}, "prod": {"status": prod}},
            "firstProdAt": "2026-10-22T10:00:00Z",
            "releasedOnProd": key == "CHG-12",
        }
        return 200, json.dumps(body).encode()


def full_flow(registry: Registry, make_draft: Any) -> Inbox:
    """PRB → intencja z metryką → B1 → wydanie R1 (TSK-57, TSK-58) → ocena skutku."""
    metric = {"metric": "rollbacks", "target": "<= 1"}
    registry.record(
        make_draft(
            statement="Ponawiamy płatności.",
            kind="intent",
            links={"chg": "CHG-12", "prb": "PRB-3"},
            success_metric=metric,
        )
    )
    registry.record(
        make_draft(
            statement="Kolejka ponowień w Redis.",
            kind="technical",
            links={"chg": "CHG-12", "tsk": "TSK-57", "pr": "https://github.com/dbqm45/sklep/pull/9"},
        )
    )
    inbox = Inbox(registry)
    inbox.receive(gate_event())
    inbox.decide("evt-gate-1", make_draft(statement="Intencja OK."), outcome="approved")
    inbox.receive(released_event())
    inbox.open_due_reviews(today=date(2026, 11, 22))
    inbox.decide("impact-CHG-12-R1", make_draft(statement="Cel osiągnięty."), outcome="met")
    return inbox


def by_id(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {n["id"]: n for n in graph["nodes"]}


def edges(graph: dict[str, Any]) -> set[tuple[str, str, str]]:
    return {(e["from"], e["to"], e["kind"]) for e in graph["edges"]}


def test_full_flow_gives_whole_trace(registry: Registry, make_draft: Any) -> None:
    full_flow(registry, make_draft)
    shipscope = FakeShipScope()

    graph = trace(registry, "CHG-12", shipscope=SHIPSCOPE, get=shipscope)

    nodes = by_id(graph)
    assert {
        "PRB-3",
        "CHG-12",
        "gate:B1",
        "DEC-0001",
        "DEC-0002",
        "DEC-0003",
        "DEC-0004",
        "TSK-57",
        "TSK-58",
        "pr:https://github.com/dbqm45/sklep/pull/9",
        "env:test",
        "env:qa",
        "env:prod",
        "release:R1",
        "impact:R1",
    } == set(nodes)
    assert nodes["gate:B1"]["status"] == "approved"
    assert nodes["impact:R1"]["status"] == "decided" and nodes["impact:R1"]["data"]["outcome"] == "met"
    assert nodes["env:prod"]["status"] == "released"
    assert nodes["TSK-58"]["status"] == "deployed"
    assert nodes["CHG-12"]["status"] == "done"
    assert {
        ("PRB-3", "CHG-12", "leads_to"),
        ("CHG-12", "gate:B1", "gate"),
        ("DEC-0003", "gate:B1", "decides"),
        ("DEC-0001", "CHG-12", "about"),
        ("CHG-12", "TSK-57", "contains"),
        ("TSK-57", "pr:https://github.com/dbqm45/sklep/pull/9", "implemented_by"),
        ("CHG-12", "env:prod", "deployed_to"),
        ("TSK-58", "release:R1", "released_in"),
        ("CHG-12", "release:R1", "released"),
        ("release:R1", "impact:R1", "reviewed_by"),
        ("DEC-0004", "impact:R1", "decides"),
    } <= edges(graph)
    assert graph["gaps"] == []
    assert shipscope.keys == ["CHG-12", "TSK-57", "TSK-58"]
    assert TOKEN not in json.dumps(graph)


def test_offline_trace_reads_nothing_and_says_so(registry: Registry, make_draft: Any) -> None:
    full_flow(registry, make_draft)
    shipscope = FakeShipScope()

    graph = trace(registry, "CHG-12", shipscope=SHIPSCOPE, get=shipscope, live=False)

    assert shipscope.keys == []
    assert not any(n["kind"] == "environment" for n in graph["nodes"])
    assert graph["gaps"] == []


def test_bare_change_shows_its_gaps(registry: Registry) -> None:
    Inbox(registry).receive(gate_event())

    graph = trace(registry, "CHG-12", shipscope=ShipScopeConfig(url=None))

    gaps = " ".join(graph["gaps"])
    for word in ("PRB", "intencji", "cięć", "PR", "PDI_SHIPSCOPE_URL"):
        assert word in gaps
    assert by_id(graph)["gate:B1"]["status"] == "requested"


def test_released_change_without_review_is_a_gap(registry: Registry) -> None:
    Inbox(registry).receive(released_event())

    graph = trace(registry, "CHG-12", live=False)

    assert by_id(graph)["impact:R1"]["status"] == "scheduled"
    assert any("ocen" in g for g in graph["gaps"])


def test_shipscope_error_is_a_gap(registry: Registry, make_draft: Any) -> None:
    full_flow(registry, make_draft)

    graph = trace(registry, "CHG-12", shipscope=SHIPSCOPE, get=FakeShipScope(401))

    assert any("401" in g for g in graph["gaps"])
    assert TOKEN not in json.dumps(graph)


def test_live_reads_are_capped(registry: Registry, make_draft: Any) -> None:
    for n in range(MAX_LIVE_ITEMS + 5):
        registry.record(
            make_draft(statement=f"Cięcie {n}.", kind="technical", links={"chg": "CHG-12", "tsk": f"TSK-{n}"})
        )
    shipscope = FakeShipScope()

    graph = trace(registry, "CHG-12", shipscope=SHIPSCOPE, get=shipscope)

    assert len(shipscope.keys) == MAX_LIVE_ITEMS
    assert any(str(MAX_LIVE_ITEMS) in g for g in graph["gaps"])


def test_change_known_only_from_registry_is_traced(registry: Registry, make_draft: Any) -> None:
    registry.record(make_draft(kind="intent", links={"chg": "CHG-40"}))

    graph = trace(registry, "CHG-40", live=False)

    assert by_id(graph)["CHG-40"]["status"] is None


def test_unknown_change_raises(registry: Registry) -> None:
    with pytest.raises(ChangeNotFound, match="list_changes"):
        trace(registry, "CHG-404", live=False)


def test_mermaid_escapes_labels() -> None:
    graph = {
        "nodes": [
            {"id": "CHG-1", "kind": "change", "label": 'Zmiana "x"\nnowa linia ' + "a" * 80, "status": "open"},
            {"id": "pr:https://x/pull/1", "kind": "pr", "label": "PR 1", "status": None},
        ],
        "edges": [{"from": "CHG-1", "to": "pr:https://x/pull/1", "kind": "implemented_by"}],
    }

    text = mermaid(graph)

    assert text.startswith("flowchart LR\n")
    assert '"' not in text.split("\n", 1)[1].replace('["', "").replace('"]', "")
    assert "\nnowa" not in text
    assert "CHG_1 -->|implemented_by| pr_https___x_pull_1" in text
    assert "a" * 61 not in text
