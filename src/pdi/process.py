"""DV1: bramki do uproszczenia (docs/plan-dv1-bramki-do-uproszczenia.md).

Z osi zmian DV4 (`pdi.delays.timeline`) liczy dla każdej bramki, jak często w ostatnich decyzjach przeszła bez uwag,
a jak często zatrzymała zmianę (`changes_requested`, `rejected`). Bramka, która w pełnym oknie prawie nigdy nie
zatrzymuje zmian, dostaje rekomendację `challenge` — szkic decyzji „uprościć?” w skrzynce
(`Inbox.propose_process_changes`). Okno i próg jak licznik akceptacji szkiców (kontrakt `autonomy.lower_when`).
Decyduje człowiek.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from statistics import median
from typing import Any

from pdi import contract, delays

GATE_CHANGE_TYPE = "process.gate_change"
# Bramki, których pdi nigdy nie proponuje upraszczać: B5 to wydanie na PROD (typ chroniony release.go, DA2).
PROTECTED_GATES = ("B5",)
STOPPING = ("changes_requested", "rejected")


def _thresholds() -> tuple[int, float]:
    lower = contract.settings()["autonomy"]["lower_when"]
    return int(lower["last_decisions"]), float(lower["min_unedited_share"])


def _pct(share: float) -> str:
    value = round(share * 100, 1)
    return f"{int(value)}%" if value.is_integer() else f"{value:.1f}%".replace(".", ",")


def report(states: Sequence[dict[str, Any]], *, now: datetime) -> list[dict[str, Any]]:
    """Dla każdej bramki z historii zmian: okno ostatnich decyzji, przeszła / zatrzymała, mediana czekania
    i rekomendacja."""
    size, min_share = _thresholds()
    decided: dict[str, list[dict[str, Any]]] = {}
    for state in states:
        for g in delays.timeline(state, now=now)["gates"]:
            if g["decided_at"] is not None:
                decided.setdefault(g["gate"], []).append(g)
    rows = []
    for gate in sorted(decided, key=delays.gate_order):
        all_of = sorted(decided[gate], key=lambda g: str(g["decided_at"]))
        window = all_of[-size:]
        stopped = sum(1 for g in window if g["outcome"] in STOPPING)
        passed = len(window) - stopped
        share = passed / len(window)
        protected = gate in PROTECTED_GATES
        if protected:
            rec = {"action": "keep", "reason": "bramka chroniona (wydanie na PROD, DA2)"}
        elif len(window) < size:
            rec = {"action": "keep", "reason": f"za mało danych: {len(window)}/{size}"}
        elif share >= min_share:
            rec = {
                "action": "challenge",
                "reason": (
                    f"{passed}/{len(window)} decyzji bez uwag ({_pct(share)}) ≥ {_pct(min_share)} w ostatnich {size}"
                ),
            }
        else:
            rec = {"action": "keep", "reason": f"zatrzymała {stopped}/{len(window)} zmian — zmniejsza ryzyko"}
        rows.append(
            {
                "gate": gate,
                "protected": protected,
                "decided": len(all_of),
                "measured": len(window),
                "passed": passed,
                "stopped": stopped,
                "passed_share": round(share, 4),
                "median_hours": round(median(float(g["hours"]) for g in window), 1),
                "window": size,
                "recommendation": rec,
            }
        )
    return rows


def proposals(states: Sequence[dict[str, Any]], *, now: datetime) -> list[dict[str, Any]]:
    """Rekomendacje `challenge` w kształcie pozycji skrzynki (bez id i czasu — nadaje je skrzynka)."""
    out = []
    for r in report(states, now=now):
        if r["recommendation"]["action"] != "challenge":
            continue
        out.append(
            {
                "gate": r["gate"],
                "measurement": {
                    k: r[k] for k in ("decided", "measured", "passed", "stopped", "median_hours", "window")
                },
                "reason": r["recommendation"]["reason"],
                "summary": (
                    f"Bramka {r['gate']}: {r['passed']}/{r['measured']} bez uwag, "
                    f"mediana czekania {r['median_hours']} h — uprościć (obniżyć poziom albo usunąć krok)?"
                ),
            }
        )
    return out


def evidence(item: dict[str, Any]) -> dict[str, str]:
    """Pomiar z propozycji jako dowód decyzji o bramce."""
    m = item["measurement"]
    text = (
        f"pdi, pomiar bramki {item['gate']} (DV1): {m['passed']}/{m['measured']} decyzji bez uwag, zatrzymała "
        f"{m['stopped']}, mediana czekania {m['median_hours']} h, w ostatnich {m['window']} z {m['decided']}. "
        f"{item['reason']}."
    )
    return {"text": text, "epistemic_status": "observation"}
