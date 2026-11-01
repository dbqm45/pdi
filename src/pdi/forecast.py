"""Prognoza zmiany (G3, decyzja D-E1): liczba cięć planu tf × historyczny czas przepływu z ShipScope.

Czyste reguły — prognoza z historii (`estimate`), porównanie z wynikiem (`compare`), kalibracja (`calibration`) —
i odczyt z API usług ShipScope (`read_flow`, `read_tasks`). Prognoza mówi też, kiedy jej nie ufać (`doubts`): wtedy
głosują ludzie. Plan: docs/plan-g3-prognoza.md.
"""

from __future__ import annotations

import json
import statistics
import sys
import urllib.parse
from collections.abc import Iterable
from datetime import date
from typing import Any

from pdi.impact import Get, ShipScopeConfig, _config_problem, _get, _headers, _read_json
from pdi.registry import Registry

HISTORY_DAYS = 180
MIN_HISTORY = 5  # tyle dostarczonych zmian, by prognozie ufać bez głosu ludzi


def estimate(tasks: int, flow: dict[str, Any]) -> dict[str, Any]:
    """Prognoza dla zmiany z `tasks` cięciami z odpowiedzi `/flow`: dni (oczekiwane, P25, P75), podstawa,
    historia i wątpliwości."""
    changes = [c for c in _rows(flow.get("changes")) if _positive_int(c.get("tasks")) and _days(c.get("flowDays"))]
    items = [i for i in _rows(flow.get("items")) if _days(i.get("flowDays"))]
    doubts: list[str] = []
    per_task: list[float]
    if changes:
        per_task = [float(c["flowDays"]) / int(c["tasks"]) for c in changes]
        basis: str | None = "changes"
        if len(changes) < MIN_HISTORY:
            history = _count(len(changes), "dostarczona zmiana", "dostarczone zmiany", "dostarczonych zmian")
            doubts.append(f"Mało historii: {history} w {HISTORY_DAYS} dniach (pewność od {MIN_HISTORY}).")
        largest = max(int(c["tasks"]) for c in changes)
        if tasks > largest:
            doubts.append(
                f"Plan ma {_count(tasks, 'cięcie', 'cięcia', 'cięć')}, a największa zmiana z historii {largest}."
            )
    elif items:
        per_task = [float(i["flowDays"]) for i in items]
        basis = "items"
        doubts.append(
            "Brak dostarczonych zmian w historii — prognoza z czasu pojedynczych elementów, jakby cięcia szły jedno po "
            "drugim (górne oszacowanie)."
        )
    else:
        per_task, basis = [], None
        doubts.append(f"Brak historii czasu przepływu w ShipScope z {HISTORY_DAYS} dni — prognozy nie da się policzyć.")
    expected = low = high = None
    if per_task:
        expected = _round(tasks * statistics.median(per_task))
        q1, q3 = (
            (per_task[0], per_task[0])
            if len(per_task) == 1
            else tuple(statistics.quantiles(per_task, n=4, method="inclusive")[i] for i in (0, 2))
        )
        low, high = _round(tasks * q1), _round(tasks * q3)
    return {
        "tasks": tasks,
        "expected_days": expected,
        "low_days": low,
        "high_days": high,
        "basis": basis,
        "history": {"from": flow.get("from"), "to": flow.get("to"), "changes": len(changes), "items": len(items)},
        "doubts": doubts,
    }


def compare(forecast: dict[str, Any], actual_days: float) -> dict[str, Any]:
    """Wynik wobec prognozy: `ratio` = rzeczywiste / oczekiwane dni, `within_range` = w przedziale P25–P75."""
    expected, low, high = forecast.get("expected_days"), forecast.get("low_days"), forecast.get("high_days")
    return {
        "actual_days": actual_days,
        "ratio": round(actual_days / expected, 2) if expected else None,
        "within_range": low is not None and high is not None and low <= actual_days <= high,
    }


def calibration(states: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Jak trafne były prognozy: liczba z wynikiem, mediana `ratio`, odsetek w przedziale i lista zmian.

    `without_forecast`: zmiany z rzeczywistym czasem przepływu (`flow`), ale bez udanej prognozy.
    """
    rows = []
    states_list = list(states)
    for state in states_list:
        f = state.get("forecast")
        if not isinstance(f, dict) or f.get("status") != "ok":
            continue
        actual = f.get("actual") or {}
        rows.append(
            {
                "change": state["change"],
                "tasks": f.get("tasks"),
                "expected_days": f.get("expected_days"),
                "low_days": f.get("low_days"),
                "high_days": f.get("high_days"),
                "actual_days": actual.get("actual_days"),
                "ratio": actual.get("ratio"),
                "within_range": actual.get("within_range"),
            }
        )
    settled = [r for r in rows if r["actual_days"] is not None]
    ratios = [r["ratio"] for r in settled if r["ratio"] is not None]
    # Dostarczone bez użytecznej prognozy: rzeczywisty czas jest, porównać nie ma z czym (PRB-22).
    without = []
    for state in states_list:
        f = state.get("forecast")
        measured = state.get("flow")
        if isinstance(measured, dict) and not (isinstance(f, dict) and f.get("status") == "ok"):
            status = f.get("status") if isinstance(f, dict) else None
            without.append({"change": state["change"], "actual_days": measured.get("actual_days"), "forecast": status})
    return {
        "count": len(settled),
        "ratio_median": round(statistics.median(ratios), 2) if ratios else None,
        "within_range_share": round(sum(1 for r in settled if r["within_range"]) / len(settled), 2)
        if settled
        else None,
        "changes": rows,
        "without_forecast": without,
    }


# --- odczyt ShipScope ---


def read_flow(
    config: ShipScopeConfig, start: date, end: date, *, get: Get | None = None
) -> tuple[dict[str, Any] | None, str | None]:
    """Czas przepływu z ShipScope (`GET /api/service/v1/flow`): `(odpowiedź, None)` albo `(None, błąd bez tokenu)`."""
    problem = _config_problem(config)
    if problem:
        return None, problem
    assert config.url is not None and config.token is not None  # noqa: S101 — sprawdzone wyżej
    query = urllib.parse.urlencode({"from": start.isoformat(), "to": end.isoformat()})
    url = f"{config.url.rstrip('/')}/api/service/v1/flow?{query}"
    value, error = _read_json(get or _get, url, _headers(config.token), "czas przepływu")
    if error:
        return None, error
    if not (isinstance(value.get("changes"), list) and isinstance(value.get("items"), list)):
        return None, "ShipScope zwrócił czas przepływu w nieznanym kształcie."
    return value, None


def read_tasks(config: ShipScopeConfig, change: str, *, get: Get | None = None) -> tuple[int | None, str | None]:
    """Liczba cięć zmiany z ShipScope (`GET /api/service/v1/changes`, bez `dropped`): `(liczba, None)` albo
    `(None, błąd)`."""
    problem = _config_problem(config)
    if problem:
        return None, problem
    assert config.url is not None and config.token is not None  # noqa: S101 — sprawdzone wyżej
    url = f"{config.url.rstrip('/')}/api/service/v1/changes"
    value, error = _read_json(get or _get, url, _headers(config.token), "zmiany")
    if error:
        return None, error
    changes = value.get("changes")
    if not isinstance(changes, list):
        return None, "ShipScope zwrócił zmiany w nieznanym kształcie."
    found = next((c for c in _rows(changes) if c.get("key") == change), None)
    if found is None:
        return None, f"ShipScope nie zna jeszcze {change} — plan zmiany nie trafił na gałąź domyślną repo?"
    tasks = found.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        return None, f"{change} nie ma cięć w ShipScope — plan.md bez zadań?"
    return len(tasks), None


def _rows(value: Any) -> list[dict[str, Any]]:
    return [r for r in value if isinstance(r, dict)] if isinstance(value, list) else []


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _days(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and value >= 0


def _round(value: float) -> float:
    return round(value, 1)


def _count(n: int, one: str, few: str, many: str) -> str:
    """Liczebnik z rzeczownikiem po polsku: 1 zmiana, 2 zmiany, 5 zmian, 22 zmiany."""
    if n == 1:
        return f"{n} {one}"
    return f"{n} {few if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else many}"


def main() -> None:
    """`pdi-forecast`: wynik prognoz dostarczonych zmian i nowa próba nieudanych (z crona raz dziennie)."""
    from pdi.inbox import Inbox  # skrzynka importuje ten moduł

    inbox = Inbox(Registry.from_env(), shipscope=ShipScopeConfig.from_env())
    json.dump({"settled": inbox.settle_forecasts()}, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
