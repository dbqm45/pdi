"""Podsumowanie rejestru do walidacji na sobie (dokument 14 §6): to, co da się policzyć bez notatek."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

from pdi.registry import Registry


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
        "superseded": sum(1 for d in decisions if d["status"] == "superseded"),
        "with_load_bearing_assumptions": sum(
            1 for d in decisions if any(a["load_bearing"] for a in d.get("assumptions", ()))
        ),
    }


def main() -> None:
    s = summarize(Registry.from_env())
    print(f"Razem: {s['total']} (zastąpione: {s['superseded']})")
    print("Zapisy w tygodniu (W1: cel ≥ 5):")
    for week, n in s["per_week"].items():
        print(f"  {week}: {n}")
    print(f"Szkic przygotował: {s['drafted_by']}")
    print(f"Rodzaje: {s['kinds']}")
    print(f"Z założeniem nośnym: {s['with_load_bearing_assumptions']}")


if __name__ == "__main__":
    main()
