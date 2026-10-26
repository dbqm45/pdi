"""Licznik akceptacji szkiców i poziomy autonomii (A3; kontrakt 0.5.0, decyzje DA1 i DA2).

Dla każdego typu decyzji (`decision_type`) liczy, jak często człowiek zatwierdza szkic AI bez zmian, i rekomenduje
zmianę poziomu. Poziomy żyją w polityce organizacji `autonomy.yaml` w katalogu rejestru
(`contract/autonomy.schema.json`); zmienia ją tylko decyzja człowieka w skrzynce (`Inbox.propose_autonomy_changes`,
`Inbox.decide`). Plan: docs/plan-a3-licznik-akceptacji.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from pdi import contract
from pdi.registry import Decision, Registry

POLICY_FILE = "autonomy.yaml"
LEVEL_CHANGE_TYPE = "autonomy.level_change"
DEFAULT_VETO_WINDOW = "PT4H"  # przykład z planu automatyzacji §3; człowiek może go zmienić w polityce
LOWEST_PROPOSED_LEVEL = 1  # poziom 0 (automat po cichu) ustawia człowiek wprost, nigdy propozycja


class InvalidPolicy(ValueError):
    """Polityka autonomii niezgodna z kontraktem albo zmiana, której kontrakt nie dopuszcza."""


def _settings() -> dict[str, Any]:
    autonomy: dict[str, Any] = contract.settings()["autonomy"]
    return autonomy


def policy_path(registry: Registry) -> Path:
    return registry.root / POLICY_FILE


def load_policy(registry: Registry) -> dict[str, Any]:
    """Polityka organizacji; brak pliku = każdy typ na poziomie domyślnym (3)."""
    path = policy_path(registry)
    if not path.is_file():
        return {"policy": []}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise InvalidPolicy(f"{POLICY_FILE}: oczekiwany obiekt z listą policy.")
    errors = contract.errors("autonomy", data)
    if errors:
        raise InvalidPolicy(f"{POLICY_FILE} niezgodny z kontraktem: " + "; ".join(errors))
    return data


def _entry(policy: dict[str, Any], decision_type: str) -> dict[str, Any]:
    entry: dict[str, Any] = next((e for e in policy["policy"] if e["decision_type"] == decision_type), {})
    return entry


def report(registry: Registry) -> list[dict[str, Any]]:
    """Dla każdego znanego typu: poziom, pomiar szkiców AI i rekomendacja (lower / raise / keep)."""
    settings = _settings()
    policy = load_policy(registry)
    decisions = registry.decisions()
    catalog = [t["decision_type"] for t in settings["decision_types"]]
    seen = {d["decision_type"] for d in decisions if d.get("decision_type")} | {
        e["decision_type"] for e in policy["policy"]
    }
    types = catalog + sorted(seen - set(catalog))
    return [_row(t, decisions, _entry(policy, t), settings) for t in types]


def _row(
    decision_type: str, decisions: list[Decision], entry: dict[str, Any], settings: dict[str, Any]
) -> dict[str, Any]:
    of_type = [d for d in decisions if d.get("decision_type") == decision_type]
    ai = [d for d in of_type if d["drafted_by"] == "ai"]
    known = [d for d in ai if "draft_edited" in d]
    lower = entry.get("lower_when", settings["lower_when"])
    size = int(lower["last_decisions"])
    window = known[-size:]
    unedited = sum(1 for d in window if not d["draft_edited"])
    level = int(entry.get("level", settings["default_level"]))
    protected = decision_type in settings["protected_types"]
    return {
        "decision_type": decision_type,
        "level": level,
        "protected": protected,
        "decisions": len(of_type),
        "ai_drafted": len(ai),
        "measured": len(window),
        "unedited": unedited,
        "unedited_share": round(unedited / len(window), 4) if window else None,
        "unknown": len(ai) - len(known),
        "window": size,
        "recommendation": _recommend(
            level=level,
            protected=protected,
            measured=len(window),
            unedited=unedited,
            size=size,
            min_share=float(lower["min_unedited_share"]),
            max_edited=float(entry.get("raise_when", settings["raise_when"])["max_edited_share"]),
        ),
    }


def _recommend(
    *, level: int, protected: bool, measured: int, unedited: int, size: int, min_share: float, max_edited: float
) -> dict[str, Any]:
    edited = measured - unedited
    if level < 3 and measured and edited / measured > max_edited:
        # Powrót do człowieka bez wymogu pełnego okna: to kierunek bezpieczny.
        why = f"{edited}/{measured} szkiców poprawionych ({_pct(edited / measured)}) > {_pct(max_edited)}"
        return {"action": "raise", "to_level": 3, "reason": why}
    if protected:
        return {"action": "keep", "to_level": None, "reason": "typ chroniony (DA2) — zostaje na poziomie 3"}
    if level <= LOWEST_PROPOSED_LEVEL:
        why = f"poziom {level} — niżej tylko ręcznie w polityce (poziom 0: czynności bez skutków dla produktu)"
        return {"action": "keep", "to_level": None, "reason": why}
    if measured < size:
        return {"action": "keep", "to_level": None, "reason": f"za mało danych: {measured}/{size}"}
    share = unedited / measured
    if share >= min_share:
        why = f"{unedited}/{measured} szkiców bez poprawek ({_pct(share)}) ≥ {_pct(min_share)} w ostatnich {size}"
        return {"action": "lower", "to_level": level - 1, "reason": why}
    why = f"{unedited}/{measured} szkiców bez poprawek ({_pct(share)}) < {_pct(min_share)}"
    return {"action": "keep", "to_level": None, "reason": why}


def _pct(share: float) -> str:
    value = round(share * 100, 1)
    return f"{int(value)}%" if value.is_integer() else f"{value:.1f}%".replace(".", ",")


def proposals(registry: Registry) -> list[dict[str, Any]]:
    """Rekomendacje zmiany poziomu w kształcie pozycji skrzynki (bez id i czasu — nadaje je skrzynka)."""
    out = []
    for row in report(registry):
        rec = row["recommendation"]
        if rec["action"] == "keep":
            continue
        verb = "obniżyć" if rec["action"] == "lower" else "przywrócić do człowieka"
        item: dict[str, Any] = {
            "decision_type": row["decision_type"],
            "from_level": row["level"],
            "to_level": rec["to_level"],
            "measurement": {k: row[k] for k in ("measured", "unedited", "unedited_share", "unknown", "window")},
            "reason": rec["reason"],
            "summary": (
                f"Autonomia {row['decision_type']}: {verb} poziom {row['level']} → {rec['to_level']}? {rec['reason']}."
            ),
        }
        if rec["to_level"] == 2:
            item["veto_window"] = DEFAULT_VETO_WINDOW
        out.append(item)
    return out


def policy_after(registry: Registry, item: dict[str, Any]) -> dict[str, Any]:
    """Polityka po zatwierdzeniu propozycji; rzuca InvalidPolicy, gdy kontrakt nie dopuszcza zmiany."""
    settings = _settings()
    decision_type = str(item["decision_type"])
    level = int(item["to_level"])
    if level < 3 and decision_type in settings["protected_types"]:
        raise InvalidPolicy(f"{decision_type} jest typem chronionym (DA2) — zostaje na poziomie 3.")
    policy = load_policy(registry)
    entry = {**_entry(policy, decision_type), "decision_type": decision_type, "level": level}
    if level == 2:
        entry["veto_window"] = item.get("veto_window") or entry.get("veto_window") or DEFAULT_VETO_WINDOW
    others = [e for e in policy["policy"] if e["decision_type"] != decision_type]
    updated = {**policy, "policy": [*others, entry]}
    errors = contract.errors("autonomy", updated)
    if errors:
        raise InvalidPolicy(f"Zmiana poziomu {decision_type} niezgodna z kontraktem: " + "; ".join(errors))
    return updated


def write_policy(registry: Registry, policy: dict[str, Any], *, decision: str, at: str) -> Path:
    """Zapisuje politykę z decyzją, która ją ustaliła."""
    path = policy_path(registry)
    path.parent.mkdir(parents=True, exist_ok=True)
    document = {**policy, "decision": decision, "updated_at": at}
    path.write_text(yaml.safe_dump(document, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path


def evidence(item: dict[str, Any]) -> dict[str, str]:
    """Pomiar z propozycji jako dowód decyzji o zmianie poziomu."""
    m = item["measurement"]
    text = (
        f"pdi, licznik akceptacji szkiców ({item['decision_type']}): {m['unedited']}/{m['measured']} bez poprawek "
        f"w ostatnich {m['window']}; szkice AI bez informacji o poprawkach: {m['unknown']}. {item['reason']}."
    )
    return {"text": text, "epistemic_status": "observation"}
