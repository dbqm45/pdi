"""G7: kolejka bramek obok jakości wydań, tydzień po tygodniu (docs/plan-g7-kolejka-i-jakosc.md).

Wskaźniki wyprzedzające z pdi (prośby o bramkę, decyzje, mediana czekania, kolejka na koniec tygodnia) w parze
z opóźnionymi: z ShipScope wdrożenia na PROD (udane), nieudane, rollbacki
i CFR = (nieudane + rollbacki) / (udane + nieudane), z pdi nowe zgłoszenia (PRB). Tygodnie ISO
(poniedziałek–niedziela, UTC). Miary dla systemu, nigdy dla osoby; sygnał to podpowiedź do rozmowy, nie alarm.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from statistics import median
from typing import Any

from pdi import delays

WEEKS = 8
SIGNAL_TEXT = "Kolejka bramek i odsetek nieudanych wdrożeń rosną razem — przegląd może nie nadążać."


def _monday(now: datetime) -> date:
    today = now.astimezone(UTC).date()
    return today - timedelta(days=today.weekday())


def window(now: datetime) -> tuple[str, str]:
    """Zakres dni (od, do włącznie) ostatnich WEEKS tygodni — o tyle pytać ShipScope."""
    last = _monday(now)
    return (last - timedelta(weeks=WEEKS - 1)).isoformat(), (last + timedelta(days=6)).isoformat()


def _gates(states: Sequence[dict[str, Any]], now: datetime) -> list[dict[str, Any]]:
    out = []
    for s in states:
        t = delays.timeline(s, now=now)
        released = delays.parse_at(t.get("released_at"))
        for g in t["gates"]:
            out.append(
                {
                    "requested": delays.parse_at(g["requested_at"]),
                    "decided": delays.parse_at(g["decided_at"]),
                    "hours": float(g["hours"]),
                    "released": released,
                }
            )
    return out


def _open_at(g: dict[str, Any], moment: datetime) -> bool:
    return (
        g["requested"] is not None
        and g["requested"] < moment
        and (g["decided"] is None or g["decided"] >= moment)
        and (g["released"] is None or g["released"] > moment)
    )


def report(
    states: Sequence[dict[str, Any]],
    problems: Sequence[dict[str, Any]],
    days: Sequence[dict[str, Any]] | None,
    *,
    now: datetime,
    shipscope_error: str | None = None,
) -> dict[str, Any]:
    """Tygodnie od najstarszego: bramki pdi, wdrożenia i CFR z ShipScope (`days` z `/metrics`; None — brak danych)
    i nowe PRB, oraz sygnał „przegląd może nie nadążać” dla ostatniego pełnego tygodnia."""
    gates = _gates(states, now)
    by_day = {str(d.get("date")): d for d in days or []}
    first = _monday(now) - timedelta(weeks=WEEKS - 1)
    weeks = []
    for i in range(WEEKS):
        start_day = first + timedelta(weeks=i)
        start = datetime(start_day.year, start_day.month, start_day.day, tzinfo=UTC)
        end = start + timedelta(weeks=1)
        current = start <= now < end
        moment = min(end, now)
        decided = [g["hours"] for g in gates if g["decided"] is not None and start <= g["decided"] < end]
        row: dict[str, Any] = {
            "week": f"{start_day.isocalendar().year}-W{start_day.isocalendar().week:02d}",
            "from": start_day.isoformat(),
            "to": (start_day + timedelta(days=6)).isoformat(),
            "current": current,
            "requested": sum(1 for g in gates if g["requested"] is not None and start <= g["requested"] < end),
            "decided": len(decided),
            "median_wait_hours": round(median(decided), 1) if decided else None,
            "queue_end": sum(1 for g in gates if _open_at(g, moment)),
            "new_problems": sum(
                1 for p in problems if (at := delays.parse_at(p.get("reported_at"))) is not None and start <= at < end
            ),
        }
        if days is None:
            row.update(deployments=None, failed=None, rollbacks=None, cfr=None)
        else:
            week_days = [by_day.get((start_day + timedelta(days=n)).isoformat(), {}) for n in range(7)]
            deployed = sum(int(d.get("deployments") or 0) for d in week_days)
            failed = sum(int(d.get("failedDeployments") or 0) for d in week_days)
            rollbacks = sum(int(d.get("rollbacks") or 0) for d in week_days)
            attempts = deployed + failed  # ShipScope: `deployments` to udane, nieudane osobno, rollbacki wśród udanych
            cfr = round((failed + rollbacks) / attempts, 2) if attempts else None
            row.update(deployments=deployed, failed=failed, rollbacks=rollbacks, cfr=cfr)
        weeks.append(row)
    return {
        "weeks": weeks,
        "signal": _signal(weeks),
        "shipscope": {"on": days is not None, "error": shipscope_error},
    }


def _signal(weeks: list[dict[str, Any]]) -> dict[str, str] | None:
    full = [w for w in weeks if not w["current"]]
    if len(full) < 2:
        return None
    before, last = full[-2], full[-1]
    if before["cfr"] is None or last["cfr"] is None:
        return None
    if last["queue_end"] > before["queue_end"] and last["cfr"] > before["cfr"]:
        return {"kind": "review_may_lag", "week": last["week"], "text": SIGNAL_TEXT}
    return None
