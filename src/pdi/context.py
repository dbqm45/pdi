"""DV3: kontekst zmiany na start zadania (docs/plan-dv3-kontekst-zmiany.md).

Tylko odczyt, bez ShipScope: po co jest zmiana (zgłoszenie, intencja), co już zdecydowano i czego nie wybrano, które
decyzje obejmują pliki, które praca ruszy (`applies_to`, kontrakt 0.22.0), co czeka na odpowiedź, które PR-y są
i czego brakuje (graf śladu F5).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from pdi import impact
from pdi.changes import ChangeNotFound, ChangeStore
from pdi.inbox import Inbox
from pdi.problems import ProblemNotFound, ProblemStore
from pdi.registry import Decision, Registry
from pdi.trace import trace

PROBLEM_FIELDS = ("id", "title", "who", "cannot", "impact", "status")
QUESTION_FIELDS = ("gate", "summary", "questions", "default_option", "reversibility", "closes_at", "url")


def _decision(d: Decision) -> dict[str, Any]:
    out: dict[str, Any] = {k: d[k] for k in ("id", "statement", "why", "kind", "decided_at") if k in d}
    out["rejected_options"] = [
        {k: o[k] for k in ("option", "note") if k in o} for o in d.get("options") or () if not o.get("chosen")
    ]
    out["load_bearing_assumptions"] = [
        {"statement": a["statement"], "invalidated_if": a["invalidated_if"]}
        for a in d.get("assumptions") or ()
        if a.get("load_bearing")
    ]
    if d.get("applies_to"):
        out["applies_to"] = d["applies_to"]
    return out


def _problem(registry: Registry, decisions: list[Decision]) -> dict[str, Any] | None:
    prb = next((str(d["links"]["prb"]) for d in decisions if (d.get("links") or {}).get("prb")), None)
    if prb is None:
        return None
    try:
        found = ProblemStore(registry).get(prb)
    except ProblemNotFound:
        return {"id": prb}
    return {k: found[k] for k in PROBLEM_FIELDS if k in found}


def reconstruct(
    registry: Registry,
    change: str | None = None,
    *,
    paths: Iterable[str] = (),
    components: Iterable[str] = (),
) -> dict[str, Any]:
    """Kontekst `{change, problem, intent, decisions, code_decisions, open_questions, prs, gaps}`.

    Bez `change` — tylko decyzje dla plików i komponentów. ChangeNotFound, gdy pdi nie zna zmiany.
    """
    wanted_paths, wanted_components = list(paths), list(components)
    out: dict[str, Any] = {
        "change": None,
        "problem": None,
        "intent": None,
        "decisions": [],
        "code_decisions": [],
        "open_questions": [],
        "prs": [],
        "gaps": [],
    }
    seen: set[str] = set()
    if change is not None:
        graph = trace(registry, change, live=False)  # ChangeNotFound, gdy zmiany nie ma ani w stanie, ani w rejestrze
        try:
            state: dict[str, Any] = ChangeStore(registry).get(change)
        except ChangeNotFound:
            state = {}
        mine = [
            d
            for d in registry.decisions()
            if d.get("status") == "recorded" and (d.get("links") or {}).get("chg") == change
        ]
        intent = impact.intent_decision(registry, change)
        out["change"] = {
            "id": change,
            "status": state.get("status"),
            "waiting": list(state.get("waiting") or []),
            "approved": dict(state.get("approved") or {}),
        }
        out["problem"] = _problem(registry, mine)
        out["intent"] = (
            None
            if intent is None
            else {k: intent[k] for k in ("id", "statement", "why", "success_metric") if k in intent}
        )
        out["decisions"] = [_decision(d) for d in mine]
        seen = {d["id"] for d in mine}
        out["open_questions"] = [
            {k: item[k] for k in QUESTION_FIELDS if item.get(k) is not None}
            for item in Inbox(registry).items()
            if item.get("change") == change
        ]
        out["prs"] = [n.get("url") or n["label"] for n in graph["nodes"] if n["kind"] == "pr"]
        out["gaps"] = graph["gaps"]
    if wanted_paths or wanted_components:
        found = registry.find(paths=wanted_paths, components=wanted_components, limit=50)
        out["code_decisions"] = [
            {**_decision(registry.get(d["id"])), "matched": d["matched"]} for d in found if d["id"] not in seen
        ]
    return out
