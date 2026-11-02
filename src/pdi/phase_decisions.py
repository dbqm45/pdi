"""Decyzje zmiany dla fazy tf (Z1, PRB-3): odpowiedzi na pytania bramki i decyzje powiązane z rejestru.

Faza tf dostaje oprócz decyzji, która ją uruchamia, wszystkie inne decyzje rejestru z `links.chg` = zmiana (triaż
zgłoszenia, `record_decision` z rozmowy, szkice A5, `decision.recorded` z ci_for_sdlc). tf dopisuje je do
`decisions.md` (`decision_record.py decision import`, idempotentnie po numerze) i wymienia w prompcie persony jako
dane. Zastąpione i cofnięte decyzje nie wiążą, więc nie idą.
"""

from __future__ import annotations

from typing import Any

from pdi.registry import Decision, Registry

LINKED_MAX = 30
TEXT_MAX = 1000
ANSWERS_MAX = 30


def text(decision: Decision) -> str:
    """Ustalenie i uzasadnienie decyzji — dla wpisu w `decisions.md` w repo produktu (PRB-3)."""
    return f"{decision['statement'].strip()} Dlaczego: {decision['why'].strip()}"


def answers(decision: Decision) -> list[dict[str, str]] | None:
    """Odpowiedzi decyzji na pytania bramki, przycięte do przekazania fazie, albo None."""
    found = decision.get("answers") or []
    out = [{"question": _cut(a["question"]), "answer": _cut(a["answer"])} for a in found[:ANSWERS_MAX]]
    return out or None


def linked(registry: Registry, change: str, *, exclude: str | None = None) -> list[dict[str, Any]] | None:
    """Obowiązujące decyzje zmiany (bez `exclude`), od najstarszej, najwyżej LINKED_MAX najnowszych, albo None."""
    found = [
        d
        for d in registry.decisions()
        if (d.get("links") or {}).get("chg") == change and d["status"] == "recorded" and d["id"] != exclude
    ]
    found.sort(key=lambda d: (str(d.get("recorded_at") or d["decided_at"]), d["id"]))
    return [_for_phase(d) for d in found[-LINKED_MAX:]] or None


def _for_phase(d: Decision) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": d["id"],
        "statement": _cut(d["statement"]),
        "why": _cut(d["why"]),
        "decided_at": d["decided_at"],
        "decided_by": _cut(d["decided_by"]),
        "kind": d["kind"],
        "source_kind": d["source"]["kind"],
        "drafted_by": d["drafted_by"],
    }
    if d.get("decision_type"):
        out["decision_type"] = d["decision_type"]
    found = answers(d)
    if found:
        out["answers"] = found
    return out


def _cut(text: str) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= TEXT_MAX else text[: TEXT_MAX - 1] + "…"
