"""Graf śladu jednej zmiany (F5): PRB → CHG → bramki i decyzje → TSK → PR → wdrożenia → wydania → skutek.

Tylko odczyt: składa to, co pdi już ma (rejestr decyzji, stan zmiany, skrzynka), i — gdy `live` — status wdrożeń z API
usług ShipScope (`pdi.impact.read_item`). Luki (`gaps`) się pokazuje, nie naprawia. Plan: docs/plan-f5-graf-sladu.md.
"""

from __future__ import annotations

import re
from typing import Any

from pdi import impact
from pdi.changes import ChangeNotFound, ChangeStore
from pdi.inbox import Inbox
from pdi.registry import Registry

Graph = dict[str, Any]

ENVIRONMENTS = ("test", "qa", "prod")
MAX_LIVE_ITEMS = 20  # odczytów ShipScope na graf: zmiana i jej cięcia
LABEL_LENGTH = 60
_MERMAID_ID = re.compile(r"[^A-Za-z0-9]")


class _Builder:
    def __init__(self) -> None:
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: list[dict[str, str]] = []

    def node(self, node_id: str, kind: str, label: str, status: str | None = None, **extra: Any) -> None:
        current = self.nodes.setdefault(node_id, {"id": node_id, "kind": kind, "label": label, "status": status})
        if status is not None:
            current["status"] = status
        current.update(extra)

    def edge(self, source: str, target: str, kind: str) -> None:
        edge = {"from": source, "to": target, "kind": kind}
        if edge not in self.edges:
            self.edges.append(edge)


def trace(
    registry: Registry,
    change: str,
    *,
    shipscope: impact.ShipScopeConfig | None = None,
    get: impact.Get | None = None,
    live: bool = True,
) -> Graph:
    """Graf `{change, nodes, edges, gaps, mermaid}`.

    ChangeNotFound, gdy pdi nie zna zmiany ani ze stanu, ani z rejestru.
    """
    store = ChangeStore(registry)
    decisions = [d for d in registry.decisions() if (d.get("links") or {}).get("chg") == change]
    try:
        state: dict[str, Any] | None = store.get(change)
    except ChangeNotFound:
        if not decisions:
            raise
        state = None
    items = [i for i in Inbox(registry).items(status=None) if i["change"] == change]
    g = _Builder()
    gaps: list[str] = []

    g.node(
        change,
        "change",
        change,
        state["status"] if state else None,
        data={"readiness": state.get("readiness"), "baseline_drift": state.get("baseline_drift")} if state else {},
    )
    _gates(g, change, state, items)
    _releases(g, change, state)
    tasks = _decisions(g, change, decisions)
    for line, keys in ((state or {}).get("release_tasks") or {}).items():
        for key in keys:
            tasks.setdefault(key, None)
            g.edge(key, f"release:{line}", "released_in")
    for key in tasks:
        g.node(key, "task", key)
        g.edge(change, key, "contains")
    if live:
        _live(g, change, list(tasks), shipscope or impact.ShipScopeConfig(url=None), get, gaps)

    kinds = {n["kind"] for n in g.nodes.values()}
    if "problem" not in kinds:
        gaps.insert(0, "Brak PRB: żadna decyzja o tej zmianie nie ma links.prb.")
    if impact.intent_decision(registry, change) is None:
        gaps.insert(1 if "problem" not in kinds else 0, "Brak decyzji o intencji z metryką sukcesu (success_metric).")
    if not tasks:
        gaps.append("Brak cięć (TSK): ani decyzje (links.tsk), ani feature.released ich nie podały.")
    if "pr" not in kinds:
        gaps.append("Brak PR: żadna decyzja o tej zmianie nie ma links.pr.")
    review = (state or {}).get("impact_review") or {}
    if (state or {}).get("releases", {}).get("R1") and review.get("status") != "decided":
        gaps.append(f"R1 wydane, ocena skutku jeszcze nie zamknięta (termin {review.get('due', '?')}).")

    graph: Graph = {"change": change, "nodes": list(g.nodes.values()), "edges": g.edges, "gaps": gaps}
    graph["mermaid"] = mermaid(graph)
    return graph


def _gates(g: _Builder, change: str, state: dict[str, Any] | None, items: list[dict[str, Any]]) -> None:
    approved: dict[str, str] = (state or {}).get("approved") or {}
    for gate in (state or {}).get("waiting") or []:
        g.node(f"gate:{gate}", "gate", gate, "requested")
    for item in items:
        gate = item.get("gate")
        if item["kind"] != "gate" or not gate or item["status"] == "superseded":
            continue
        status = "requested" if item["status"] == "open" else item.get("outcome", item["status"])
        g.node(f"gate:{gate}", "gate", gate, status, url=item.get("url"))
        if item.get("decision"):
            g.edge(item["decision"], f"gate:{gate}", "decides")
    for gate, decision in approved.items():
        g.node(f"gate:{gate}", "gate", gate, "approved")
        g.edge(decision, f"gate:{gate}", "decides")
    for node in [n for n in g.nodes.values() if n["kind"] == "gate"]:
        g.edge(change, node["id"], "gate")


def _decisions(g: _Builder, change: str, decisions: list[dict[str, Any]]) -> dict[str, None]:
    """Węzły decyzji, PRB i PR; zwraca cięcia (TSK) w kolejności pierwszego wystąpienia."""
    tasks: dict[str, None] = {}
    decided = {e["from"] for e in g.edges if e["kind"] == "decides"}
    for d in decisions:
        g.node(
            d["id"], "decision", d["statement"], d["status"], data={"kind": d["kind"], "decided_at": d["decided_at"]}
        )
        links = d.get("links") or {}
        if d["id"] not in decided:
            g.edge(d["id"], change, "about")
        if links.get("prb"):
            g.node(links["prb"], "problem", links["prb"])
            g.edge(links["prb"], change, "leads_to")
        if links.get("tsk"):
            tasks.setdefault(links["tsk"], None)
        if links.get("pr"):
            pr = str(links["pr"])
            url = pr if pr.startswith("https://") else None
            g.node(f"pr:{pr}", "pr", _pr_label(pr), url=url)
            g.edge(links["tsk"] if links.get("tsk") else change, f"pr:{pr}", "implemented_by")
    return tasks


def _releases(g: _Builder, change: str, state: dict[str, Any] | None) -> None:
    for line, released_at in ((state or {}).get("releases") or {}).items():
        g.node(f"release:{line}", "release", line, "released", data={"released_at": released_at})
        g.edge(change, f"release:{line}", "released")
    review = (state or {}).get("impact_review")
    if review:
        g.node("impact:R1", "impact", "ocena skutku R1", review["status"], data=review)
        g.edge("release:R1", "impact:R1", "reviewed_by")
        if review.get("decision"):
            g.edge(review["decision"], "impact:R1", "decides")


def _live(
    g: _Builder,
    change: str,
    tasks: list[str],
    config: impact.ShipScopeConfig,
    get: impact.Get | None,
    gaps: list[str],
) -> None:
    keys = [change, *tasks]
    if len(keys) > MAX_LIVE_ITEMS:
        gaps.append(f"ShipScope: przeczytano status {MAX_LIVE_ITEMS} z {len(keys)} elementów (limit na graf).")
    errors: list[str] = []
    for key in keys[:MAX_LIVE_ITEMS]:
        item, error = impact.read_item(config, key, get=get)
        if error:
            errors.append(error)
            if not config.url or not config.token:
                break  # brak konfiguracji: jeden komunikat wystarczy
            continue
        assert item is not None  # noqa: S101 — read_item zwraca element albo błąd
        raw_envs = item.get("envs")
        envs: dict[str, Any] = raw_envs if isinstance(raw_envs, dict) else {}
        if key == change:
            g.nodes[change]["data"] = {
                **g.nodes[change].get("data", {}),
                "firstProdAt": item.get("firstProdAt"),
                "releasedOnProd": item.get("releasedOnProd"),
            }
            for env in ENVIRONMENTS:
                info = envs.get(env)
                if isinstance(info, dict) and isinstance(info.get("status"), str):
                    g.node(f"env:{env}", "environment", env.upper(), info["status"], data=info)
                    g.edge(change, f"env:{env}", "deployed_to")
        else:
            prod = envs.get("prod")
            if isinstance(prod, dict) and isinstance(prod.get("status"), str):
                g.node(key, "task", key, prod["status"])
    gaps += [f"ShipScope: {e}" for e in dict.fromkeys(errors)]


def _pr_label(pr: str) -> str:
    match = re.search(r"/pull/(\d+)", pr)
    return f"PR #{match.group(1)}" if match else pr


def mermaid(graph: Graph) -> str:
    """`flowchart LR` grafu; etykiety bez cudzysłowów i nowych linii, najwyżej 60 znaków."""
    lines = ["flowchart LR"]
    for n in graph["nodes"]:
        text = f"{n['id']}: {n['label']}" if n["kind"] == "decision" else n["label"]
        if n.get("status"):
            text += f" ({n['status']})"
        text = " ".join(text.replace('"', "'").split())
        if len(text) > LABEL_LENGTH:
            text = text[: LABEL_LENGTH - 1] + "…"
        lines.append(f'  {_MERMAID_ID.sub("_", n["id"])}["{text}"]')
    for e in graph["edges"]:
        lines.append(f"  {_MERMAID_ID.sub('_', e['from'])} -->|{e['kind']}| {_MERMAID_ID.sub('_', e['to'])}")
    return "\n".join(lines) + "\n"
