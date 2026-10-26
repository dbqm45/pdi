"""Ocena skutku decyzji (F5): po wydaniu MVP i N dniach metryka sukcesu z intencji wobec danych z ShipScope.

Czyste reguły — która decyzja jest intencją zmiany, kiedy ocenić (`due_date`), szkic wniosku (`draft_verdict`) — i
odczyt z API usług ShipScope (`collect`). pdi tylko szkicuje: `met` / `not_met` wtedy, gdy metryka pochodzi z
ShipScope, a cel ma porównanie z liczbą; w każdym innym razie `unknown` z powodem. Wynik potwierdza człowiek
(`Inbox.decide`). Plan: docs/plan-f5-ocena-skutku.md.
"""

from __future__ import annotations

import json
import os
import re
import statistics
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, TypeAlias

from pdi.registry import Decision, Registry

# (url, nagłówki) -> (status HTTP, treść)
Get: TypeAlias = Callable[[str, dict[str, str]], tuple[int, bytes]]

DEFAULT_DAYS = 30
MAX_WINDOW_DAYS = 400  # ShipScope oddaje najwyżej 400 dni szeregu
TIMEOUT_SECONDS = 10
LOCAL_HOSTS = ("127.0.0.1", "localhost", "::1")
OUTCOMES = ("met", "not_met", "unknown")

_ISO_HORIZON = re.compile(r"^P(\d+)([DWM])$")
_HORIZON = re.compile(r"^\s*(\d+)\s*([^\d\s].*)$")
# Początek jednostki → dni; miesiąc liczy się jako 30 dni.
_UNITS = (("ty", 7), ("w", 7), ("mi", 30), ("mo", 30), ("kw", 90), ("q", 90), ("d", 1))
# Kolumna szeregu ShipScope: (pole w JSON, słowa w opisie metryki). Kolejność ma znaczenie: „failed deployments”
# zawiera „deployments”.
_COLUMNS = (
    ("failed_deployments", "failedDeployments", ("failed deployments", "nieudane wdrożenia", "nieudanych wdrożeń")),
    ("rollbacks", "rollbacks", ("rollback", "wycofan")),
    ("deployments", "deployments", ("deployments", "wdrożenia", "wdrożeń")),
    ("lead_time_days_median", "leadTimeDaysMedian", ("lead time",)),
)
_TARGET = re.compile(r"^\s*(<=|>=|≤|≥|==|<|>|=)\s*(-?\d+(?:[.,]\d+)?)\s*$")
_COMPARE: dict[str, Callable[[float, float], bool]] = {
    "<=": lambda a, b: a <= b,
    "≤": lambda a, b: a <= b,
    ">=": lambda a, b: a >= b,
    "≥": lambda a, b: a >= b,
    "<": lambda a, b: a < b,
    ">": lambda a, b: a > b,
    "=": lambda a, b: a == b,
    "==": lambda a, b: a == b,
}


# --- termin ---


def parse_horizon(text: str) -> int | None:
    """Horyzont metryki w dniach („30 dni”, „4 tygodnie”, „2 months”, `P30D`); None, gdy nieczytelny albo zero."""
    iso = _ISO_HORIZON.match(text.strip().upper())
    if iso:
        days = int(iso.group(1)) * {"D": 1, "W": 7, "M": 30}[iso.group(2)]
    else:
        match = _HORIZON.match(text.lower())
        if not match:
            return None
        per = next((n for prefix, n in _UNITS if match.group(2).startswith(prefix)), None)
        if per is None:
            return None
        days = int(match.group(1)) * per
    return days or None


def intent_decision(registry: Registry, change: str) -> Decision | None:
    """Najnowsza obowiązująca decyzja o zmianie z `success_metric`; decyzje `kind: intent` mają pierwszeństwo."""
    found = [
        d
        for d in registry.decisions()
        if d.get("status") == "recorded" and (d.get("links") or {}).get("chg") == change and d.get("success_metric")
    ]
    if not found:
        return None
    return max(found, key=lambda d: (d["kind"] == "intent", d["recorded_at"], int(d["id"].split("-")[-1])))


def due_date(released_at: str, intent: Decision | None) -> tuple[str, str]:
    """Dzień oceny i jego podstawa: `review_by` (nie przed wydaniem), dzień wydania + horyzont, albo + 30 dni."""
    released = date.fromisoformat(released_at[:10])
    if intent:
        review_by = intent.get("review_by")
        if review_by and date.fromisoformat(review_by) >= released:
            return review_by, "review_by"
        days = parse_horizon(str((intent.get("success_metric") or {}).get("horizon") or ""))
        if days:
            return (released + timedelta(days=days)).isoformat(), "horizon"
    return (released + timedelta(days=DEFAULT_DAYS)).isoformat(), "default"


# --- szkic wniosku ---


def draft_verdict(metric: dict[str, Any] | None, data: dict[str, Any]) -> dict[str, Any]:
    """Szkic wniosku `{verdict, reason, observed}`; `unknown`, gdy pdi nie może porównać metryki z danymi."""

    def unknown(reason: str) -> dict[str, Any]:
        return {"verdict": "unknown", "reason": reason, "observed": None}

    if not metric:
        return unknown("Brak decyzji o intencji z success_metric dla tej zmiany — oceń ręcznie.")
    text = str(metric["metric"]).lower().replace("_", " ")
    column = next((c for c in _COLUMNS if any(word in text for word in (c[0].replace("_", " "), *c[2]))), None)
    if column is None:
        names = ", ".join(c[0] for c in _COLUMNS)
        return unknown(f"Metryka „{metric['metric']}” nie pochodzi z ShipScope ({names}) — oceń ręcznie.")
    target = _TARGET.match(str(metric["target"]))
    if target is None:
        return unknown(f"Cel „{metric['target']}” nie ma porównania z liczbą (np. <= 1) — oceń ręcznie.")
    days = (data.get("metrics") or {}).get("days")
    if not days:
        errors = "; ".join(data.get("errors") or []) or "pusty szereg"
        return unknown(f"Brak danych z ShipScope: {errors}.")
    name, key, _ = column
    observed: float
    if name == "lead_time_days_median":
        medians = [d[key] for d in days if isinstance(d.get(key), int | float)]
        if not medians:
            return unknown("Brak danych o lead time w oknie oceny (nic nie trafiło na PROD).")
        observed = float(statistics.median(medians))
    else:
        observed = sum(d[key] for d in days if isinstance(d.get(key), int))
    op, number = target.group(1), float(target.group(2).replace(",", "."))
    verdict = "met" if _COMPARE[op](observed, number) else "not_met"
    how = "mediana median dziennych" if name == "lead_time_days_median" else "suma"
    reason = f"{name} ({how}) od {days[0]['date']} do {days[-1]['date']}: {observed} (cel {metric['target']})."
    item = data.get("item") or {}
    if item.get("releasedOnProd") is False:
        reason += " Uwaga: ShipScope nie widzi zmiany jako wydanej na PROD."
    return {"verdict": verdict, "reason": reason, "observed": observed}


# --- odczyt ShipScope ---


@dataclass(frozen=True)
class ShipScopeConfig:
    url: str | None
    token: str | None = field(default=None, repr=False)

    @classmethod
    def from_env(cls) -> ShipScopeConfig:
        return cls(
            url=os.environ.get("PDI_SHIPSCOPE_URL") or None,
            token=os.environ.get("PDI_SHIPSCOPE_TOKEN") or None,
        )


def collect(
    config: ShipScopeConfig, change: str, released_at: str, today: date, *, get: Get | None = None
) -> dict[str, Any]:
    """Status zmiany i dzienny szereg PROD od dnia wydania do `today` (najwyżej 400 dni); błędy bez tokenu."""
    released = date.fromisoformat(released_at[:10])
    start = min(max(released, today - timedelta(days=MAX_WINDOW_DAYS - 1)), today)
    out: dict[str, Any] = {
        "item": None,
        "metrics": None,
        "window": {"from": start.isoformat(), "to": today.isoformat()},
        "errors": [],
    }
    problem = _config_problem(config)
    if problem:
        out["errors"].append(problem)
        return out
    assert config.url is not None and config.token is not None  # noqa: S101 — sprawdzone wyżej
    base = config.url.rstrip("/") + "/api/service/v1"
    headers = {"authorization": f"Bearer {config.token}", "accept": "application/json"}
    query = urllib.parse.urlencode({"from": start.isoformat(), "to": today.isoformat(), "format": "json"})
    reads = (
        ("item", f"{base}/items/{urllib.parse.quote(change, safe='')}", "status zmiany"),
        ("metrics", f"{base}/metrics?{query}", "metryki PROD"),
    )
    for key, url, what in reads:
        value, error = _read_json(get or _get, url, headers, what)
        if error:
            out["errors"].append(error)
        elif key == "metrics":
            days = value.get("days")
            if isinstance(days, list) and all(isinstance(d, dict) and isinstance(d.get("date"), str) for d in days):
                out["metrics"] = {"days": days}
            else:
                out["errors"].append("ShipScope zwrócił metryki w nieznanym kształcie.")
        else:
            out["item"] = value
    return out


def _config_problem(config: ShipScopeConfig) -> str | None:
    if not config.url:
        return "Brak PDI_SHIPSCOPE_URL — pdi nie czyta danych z ShipScope."
    url = urllib.parse.urlsplit(config.url)
    if (
        url.username
        or url.password
        or not (url.scheme == "https" or (url.scheme == "http" and url.hostname in LOCAL_HOSTS))
    ):
        return "PDI_SHIPSCOPE_URL musi być adresem https:// (http tylko dla localhost), bez loginu."
    if not config.token:
        return "Brak PDI_SHIPSCOPE_TOKEN (token usługi shps_… z ShipScope Settings → General)."
    return None


def _read_json(get: Get, url: str, headers: dict[str, str], what: str) -> tuple[dict[str, Any], str | None]:
    try:
        status, body = get(url, headers)
    except OSError:
        return {}, f"Nie udało się połączyć z ShipScope ({what})."
    if status != 200:
        return {}, f"ShipScope odpowiedział {status} na {what}."
    try:
        value = json.loads(body)
    except ValueError:
        value = None
    if not isinstance(value, dict):
        return {}, f"ShipScope zwrócił nieczytelną odpowiedź na {what}."
    return value, None


def _get(url: str, headers: dict[str, str]) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers=headers)  # noqa: S310 — adres sprawdzony w _config_problem
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310
            return int(response.status), response.read()
    except urllib.error.HTTPError as e:
        return int(e.code), b""


def main() -> None:
    """`pdi-impact-review`: otwiera oceny skutku, których termin minął (do uruchamiania z crona raz dziennie)."""
    from pdi.inbox import Inbox  # skrzynka importuje ten moduł

    inbox = Inbox(Registry.from_env(), shipscope=ShipScopeConfig.from_env())
    opened = inbox.open_due_reviews()
    report = [{"id": i["id"], "change": i["change"], "verdict": i["draft"]["verdict"]} for i in opened]
    json.dump({"opened": report}, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
