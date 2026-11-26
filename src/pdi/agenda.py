"""DI Team T5 „Discuss with team” (docs/plan-t5-discuss-with-team.md): agenda spraw do rozmowy.

Na agendę trafiają otwarte pozycje skrzynki, których konsultacja „Ask team” (T4) zamknęła się rozbieżnością albo
prośbą o rozmowę na żywo. Kolejność według tego, co sprawa blokuje:
1. wstrzymany przebieg (`paused_at`, `needs_review`);
2. termin minął;
3. bramka trzyma zmianę;
4. ile osób chce rozmawiać na żywo;
5. od kiedy czeka.

Ręczna kolejność decydenta (`agenda.json`) idzie przed resztą. Czyste funkcje: dane wchodzą, lista wychodzi; zapis
kolejności robi konsola.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pdi import consult


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError:
        return None


def _waiting(received: datetime | None, now: datetime) -> str:
    if received is None:
        return ""
    days = (now - received).days
    if days >= 1:
        return f"waiting {days} day{'s' if days != 1 else ''}"
    hours = max(1, int((now - received).total_seconds() // 3600))
    return f"waiting {hours} h"


def build(
    items: list[dict[str, Any]], consults: consult.Consultations, *, order: list[str], now: datetime
) -> list[dict[str, Any]]:
    """Sprawy do rozmowy w kolejności agendy, każda z powodami miejsca słowami i odpowiedziami zespołu."""
    entries = []
    for item in items:
        if item.get("status") != "open":
            continue
        view = consults.view(item["id"], "")
        if view is None or view["status"] != "closed" or view["result"]["kind"] != "discuss":
            continue
        paused = bool(item.get("needs_review") or item.get("paused_at"))
        overdue = "overdue" in (item.get("deadline_notices") or {})
        holds = item.get("kind") == "gate" and bool(item.get("change")) and bool(item.get("gate"))
        talk = sum(1 for a in view["answers"] if a["option"] == consult.TALK_LIVE)
        received = _parse(item.get("received_at"))
        reasons = []
        if item.get("needs_review"):
            reasons.append("the run needs review")
        elif item.get("paused_at"):
            reasons.append("the run is paused")
        if overdue:
            reasons.append("past its deadline")
        if holds:
            reasons.append(f"{item['change']} waits at {item['gate']}")
        if talk:
            reasons.append(f"{talk} want{'s' if talk == 1 else ''} to talk live")
        waiting = _waiting(received, now)
        if waiting:
            reasons.append(waiting)
        entries.append({
            "item_id": item["id"],
            "kind": item.get("kind"),
            "change": item.get("change"),
            "gate": item.get("gate"),
            "summary": item.get("summary") or item["id"],
            "received_at": item.get("received_at"),
            "reasons": reasons,
            "options": view["options"],
            "answers": view["answers"],
            "effects": view["effects"],
            "decider": view["decider"],
            "_key": (not paused, not overdue, not holds, -talk, item.get("received_at") or "", item["id"]),
        })  # fmt: skip
    entries.sort(key=lambda e: e["_key"])
    pinned = {item_id: i for i, item_id in enumerate(order)}
    entries.sort(key=lambda e: (0, pinned[e["item_id"]]) if e["item_id"] in pinned else (1, 0))
    for e in entries:
        del e["_key"]
    return entries


def moved(current: list[str], item_id: str, direction: str) -> list[str]:
    """Kolejność po przesunięciu jednej sprawy o jedno miejsce w górę albo w dół."""
    order = list(current)
    if item_id not in order:
        return order
    i = order.index(item_id)
    j = i - 1 if direction == "up" else i + 1
    if 0 <= j < len(order):
        order[i], order[j] = order[j], order[i]
    return order


def markdown(entries: list[dict[str, Any]], *, day: str) -> str:
    """Agenda do zaproszenia albo notatki: sprawy w kolejności, powód miejsca, odpowiedzi zespołu."""
    lines = [f"# Discuss with team — {day}", ""]
    if not entries:
        return "\n".join([*lines, "Nothing to discuss."])
    for n, e in enumerate(entries, 1):
        where = ", ".join(x for x in (e.get("change"), e.get("gate")) if x)
        lines.append(f"{n}. **{e['summary']}**" + (f" ({where})" if where else ""))
        lines.append(f"   - why now: {'; '.join(e['reasons'])}")
        lines.append(f"   - options: {', '.join(e['options'])}")
        for a in e["answers"]:
            answered = f"{a['option']} — {a['reason']}" if a["option"] else "no answer"
            lines.append(f"   - {a['name']}: {answered}")
    return "\n".join(lines)


class Order:
    """Ręczna kolejność agendy w rejestrze (`agenda.json`)."""

    def __init__(self, root: Path) -> None:
        self.path = root / "agenda.json"

    def get(self) -> list[str]:
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        order = data.get("order") if isinstance(data, dict) else None
        return [x for x in order if isinstance(x, str)] if isinstance(order, list) else []

    def set(self, order: list[str]) -> None:
        self.path.write_text(json.dumps({"order": order}, ensure_ascii=False, indent=2), encoding="utf-8")
