"""Podsumowanie rejestru do walidacji na sobie (dokument 14 §6): to, co da się policzyć bez notatek."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

from pdi import autonomy, forecast
from pdi.changes import ChangeStore
from pdi.registry import GENERAL_PROJECT_DIR, Registry


def summarize(registry: Registry) -> dict[str, Any]:
    decisions = registry.decisions()
    weeks: Counter[str] = Counter()
    for d in decisions:
        year, week, _ = datetime.strptime(d["recorded_at"], "%Y-%m-%dT%H:%M:%SZ").isocalendar()
        weeks[f"{year}-W{week:02d}"] += 1
    return {
        "total": len(decisions),
        "per_week": dict(sorted(weeks.items())),
        "drafted_by": dict(Counter(d["drafted_by"] for d in decisions)),
        "kinds": dict(Counter(d["kind"] for d in decisions)),
        "projects": dict(Counter(d.get("project", GENERAL_PROJECT_DIR) for d in decisions)),
        "superseded": sum(1 for d in decisions if d["status"] == "superseded"),
        "with_load_bearing_assumptions": sum(
            1 for d in decisions if any(a["load_bearing"] for a in d.get("assumptions", ()))
        ),
        "forecasts": forecast.calibration(ChangeStore(registry).all(status=None)),
    }


def main() -> None:
    registry = Registry.from_env()
    s = summarize(registry)
    print(f"Razem: {s['total']} (zastąpione: {s['superseded']})")
    print("Zapisy w tygodniu (W1: cel ≥ 5):")
    for week, n in s["per_week"].items():
        print(f"  {week}: {n}")
    print(f"Szkic przygotował: {s['drafted_by']}")
    print(f"Rodzaje: {s['kinds']}")
    print(f"Projekty: {s['projects']}")
    print(f"Z założeniem nośnym: {s['with_load_bearing_assumptions']}")
    f = s["forecasts"]
    print(
        f"Prognozy (G3): {len(f['changes'])}, z wynikiem {f['count']}, mediana rzeczywiste/prognoza "
        f"{f['ratio_median']}, w przedziale {f['within_range_share']}"
    )
    print("Autonomia (szkice AI bez poprawek w oknie):")
    for row in autonomy.report(registry):
        rec = row["recommendation"]
        print(
            f"  {row['decision_type']}: poziom {row['level']}, {row['unedited']}/{row['measured']} "
            f"(okno {row['window']}) — {rec['action']}: {rec['reason']}"
        )


if __name__ == "__main__":
    main()
