"""DV4: gdzie zmiana czeka — czasy na bramkach i w skrzynce z historii zmiany (docs/plan-dv4-gdzie-zmiana-czeka.md).

Czyste funkcje na stanie zmiany (`flow`: wpisy `gate.requested`, `gate.decided`, `feature.released` w `history`) i na
pozycjach skrzynki (`received_at`, `decided_at`). Każda prośba o bramkę jest sparowana z najbliższą decyzją tej samej
bramki; bramka bez decyzji czeka do `now`. Czekanie to suma przedziałów otwartych bramek bez podwójnego liczenia,
praca to reszta czasu przebiegu (od pierwszego wpisu historii do wydania albo do `now`). Godziny zegarowe.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from statistics import median
from typing import Any

from pdi import flow, waiting

Timeline = dict[str, Any]


def _at(text: Any) -> datetime | None:
    """Chwila z tekstu ISO (`…Z`) albo z samej daty (początek dnia, UTC); None, gdy się nie da."""
    raw = str(text or "")
    if not raw:
        return None
    try:
        if len(raw) == 10:
            return datetime.fromisoformat(raw).replace(tzinfo=UTC)
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def _hours(start: datetime, end: datetime) -> float:
    return round(max(0.0, (end - start).total_seconds()) / 3600, 1)


def _union_hours(spans: Iterable[tuple[datetime, datetime]]) -> float:
    total, cur_start, cur_end = 0.0, None, None
    for start, end in sorted(spans):
        if cur_end is None or start > cur_end:
            if cur_start is not None and cur_end is not None:
                total += (cur_end - cur_start).total_seconds()
            cur_start, cur_end = start, end
        elif end > cur_end:
            cur_end = end
    if cur_start is not None and cur_end is not None:
        total += (cur_end - cur_start).total_seconds()
    return round(total / 3600, 1)


def _stage(items: Sequence[dict[str, Any]], change: str, gate: str, now: datetime) -> str | None:
    """Najświeższy osiągnięty etap terminu (N3) otwartej pozycji bramki tej zmiany; None bez pozycji."""
    for item in items:
        if (
            item.get("kind") == "gate"
            and item.get("status") == "open"
            and item.get("change") == change
            and item.get("gate") == gate
            and item.get("received_at")
        ):
            reached = [s for s, when in waiting.stages(item) if when <= now]
            return reached[-1] if reached else "new"
    return None


def timeline(state: dict[str, Any], *, now: datetime, items: Sequence[dict[str, Any]] = ()) -> Timeline:
    """Oś jednej zmiany: bramki z czasem czekania i rundą, otwarta bramka, czekanie, praca i cały czas przebiegu."""
    change = str(state.get("change") or "")
    history = [h for h in state.get("history") or [] if _at(h.get("at")) is not None]
    gates: list[dict[str, Any]] = []
    pending: dict[str, int] = {}  # bramka → indeks otwartej prośby w `gates`
    rounds: dict[str, int] = {}
    released: datetime | None = None
    for h in history:
        what, gate, at = h.get("what"), str(h.get("gate") or ""), _at(h.get("at"))
        if at is None:  # odfiltrowane wyżej; dla typów
            continue
        if what == "gate.requested" and gate:
            rounds[gate] = rounds.get(gate, 0) + 1
            pending[gate] = len(gates)
            gates.append(
                {
                    "gate": gate,
                    "requested_at": h["at"],
                    "decided_at": None,
                    "outcome": None,
                    "round": rounds[gate],
                    "_start": at,
                    "_end": None,
                }
            )
        elif what == "gate.decided" and gate in pending:
            g = gates[pending.pop(gate)]
            g.update(decided_at=h["at"], outcome=h.get("outcome"), _end=at)
        elif what == "feature.released" and released is None and h.get("release") in (None, "all"):
            released = at
    end = released or now
    spans = []
    for g in gates:
        stop = g.pop("_end") or end
        start = g.pop("_start")
        g["hours"] = _hours(start, stop)
        spans.append((start, min(stop, end)))
    still = [g for g in gates if g["decided_at"] is None]
    current = max(still, key=lambda g: g["hours"]) if still and released is None else None
    first = _at(history[0]["at"]) if history else None
    total = _hours(first, end) if first else 0.0
    waited = _union_hours(spans)
    return {
        "change": change,
        "status": state.get("status"),
        "gates": gates,
        "open": None
        if current is None
        else {
            "gate": current["gate"],
            "since": current["requested_at"],
            "hours": current["hours"],
            "stage": _stage(items, change, current["gate"], now),
        },
        "released_at": None if released is None else released.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_hours": total,
        "waiting_hours": waited,
        "working_hours": round(max(0.0, total - waited), 1),
    }


def _gate_order(name: str) -> tuple[int, str]:
    order = [g.name for g in flow.GATES]
    return (order.index(name), name) if name in order else (len(order), name)


def report(states: Sequence[dict[str, Any]], items: Sequence[dict[str, Any]], *, now: datetime) -> dict[str, Any]:
    """Zestawienia DV4: zmiany, które teraz czekają (najdłużej czekająca pierwsza), bramki, rodzaje pozycji, zmiany."""
    lines = [timeline(s, now=now, items=items) for s in states]
    waiting_now = sorted(
        ({"change": t["change"], **t["open"]} for t in lines if t["open"]), key=lambda w: -float(w["hours"])
    )
    gate_hours: dict[str, list[float]] = {}
    gate_open: dict[str, int] = {}
    for t in lines:
        for g in t["gates"]:
            gate_hours.setdefault(g["gate"], [])
            gate_open.setdefault(g["gate"], 0)
            if g["decided_at"] is None:
                gate_open[g["gate"]] += 1
            else:
                gate_hours[g["gate"]].append(float(g["hours"]))
    gates = [
        {
            "gate": name,
            "decided": len(gate_hours[name]),
            "median_hours": round(median(gate_hours[name]), 1) if gate_hours[name] else None,
            "max_hours": max(gate_hours[name]) if gate_hours[name] else None,
            "open": gate_open[name],
        }
        for name in sorted(gate_hours, key=_gate_order)
    ]
    per_kind: dict[str, dict[str, Any]] = {}
    for item in items:
        slot = per_kind.setdefault(str(item.get("kind") or "?"), {"hours": [], "open": 0})
        received, decided = _at(item.get("received_at")), _at(item.get("decided_at"))
        if item.get("status") == "open":
            slot["open"] += 1
        elif received and decided:
            slot["hours"].append(_hours(received, decided))
    kinds = [
        {
            "kind": k,
            "decided": len(v["hours"]),
            "median_hours": round(median(v["hours"]), 1) if v["hours"] else None,
            "open": v["open"],
        }
        for k, v in sorted(per_kind.items())
    ]
    changes = [
        {
            "change": t["change"],
            "waiting_hours": t["waiting_hours"],
            "working_hours": t["working_hours"],
            "waiting_share": round(t["waiting_hours"] / t["total_hours"], 2) if t["total_hours"] else None,
        }
        for t in sorted(lines, key=lambda t: -float(t["waiting_hours"]))
    ]
    return {"waiting": waiting_now, "gates": gates, "items": kinds, "changes": changes}
