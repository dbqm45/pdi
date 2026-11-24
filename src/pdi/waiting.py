"""„Czeka na Ciebie” (krok 17 planu budowy suity, CH2): nowa pozycja skrzynki idzie do DI Channels.

Terminy z operating modelu przyjętego jako OM1 (`docs/16-operating-model.md` §3–§4): dni robocze od wpływu pozycji,
weekendy pominięte (święta nie). Wiadomość: `POST <PDI_CHANNELS_URL>/pdi/waiting`, podpis jak w pozostałych
kierunkach (`X-PDI-Signature: v1=HMAC-SHA256(PDI_CHANNELS_SIGNING_SECRET, "<ts>.<body>")`). To nie jest zdarzenie
kontraktu: odbiorcą jest osoba, nie aplikacja (jak `problem.notification` z F5).

Link do konsoli tylko z `PDI_CONSOLE_URL` i **bez tokenu sesji**: konsola lokalna wymaga tokenu w adresie, a token
nie może trafić do komunikatora. Bez adresu wiadomość mówi, gdzie znaleźć pozycję (`sdlc open` → Skrzynka).
Błąd wysyłki nie cofa pozycji; wynik zostaje w pozycji (`waiting_notice`).

Terminy i przypomnienia (N3, OM1 §4–§5): `stages()` daje chwile kolejnych etapów pozycji — przypomnienie (bramka
2-dniowa po 1 dniu roboczym, 5-dniowa po 3, 1-dniowa w połowie), „termin dziś” (początek dnia terminu, UTC; DI Channels
i tak wstrzyma wiadomość do 8:00), „po terminie”, „wstrzymana” (2 × termin) i „do przeglądu” (4 × termin).
`Inbox.check_deadlines()` wysyła najświeższy osiągnięty etap i zapisuje go w pozycji (`deadline_notices`).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any

from pdi.dispatch import Post
from pdi.notify import _send

PATH = "/pdi/waiting"

# OM1 §3: bramki trudne do cofnięcia i wydanie mają inne terminy niż reszta.
_GATE_DAYS = {"B3": 5, "B5": 1}
_KIND_DAYS = {"impact_review": 5, "autonomy": 5}
DEFAULT_DAYS = 2
_STAGE_PROD = "prod"


@dataclass(frozen=True)
class ChannelsConfig:
    url: str | None
    secret: str | None = field(default=None, repr=False)
    console_url: str | None = None

    @classmethod
    def from_env(cls) -> ChannelsConfig:
        return cls(
            url=os.environ.get("PDI_CHANNELS_URL") or None,
            secret=os.environ.get("PDI_CHANNELS_SIGNING_SECRET") or None,
            console_url=os.environ.get("PDI_CONSOLE_URL") or None,
        )


def business_days(kind: str, gate: str | None) -> int:
    """Termin w dniach roboczych dla pozycji (OM1 §3); etap flagi na PROD: 1 dzień."""
    if kind == "gate" and gate:
        if gate.startswith("stage:"):
            return 1 if gate.rsplit(":", 1)[-1].lower() == _STAGE_PROD else DEFAULT_DAYS
        return _GATE_DAYS.get(gate, DEFAULT_DAYS)
    return _KIND_DAYS.get(kind, DEFAULT_DAYS)


_HARD_DAYS = 5  # OM1 §3: bramka trudna do cofnięcia (B3)


def deadline_days(item: dict[str, Any]) -> int:
    """Termin pozycji w dniach roboczych: OM1, a `reversibility: one_way` z bramki (kontrakt 0.19.0) daje bramce
    bez własnego terminu w OM1 tyle, co bramka trudna do cofnięcia."""
    kind, gate = str(item["kind"]), item.get("gate")
    days = business_days(kind, gate)
    has_own = kind == "gate" and gate and (gate in _GATE_DAYS or str(gate).startswith("stage:"))
    if item.get("reversibility") == "one_way" and kind == "gate" and not has_own:
        return max(days, _HARD_DAYS)
    return days


def _moment(text: str) -> datetime:
    return datetime.fromisoformat(str(text).replace("Z", "+00:00")).astimezone(UTC)


def _closes_at(item: dict[str, Any], received: datetime) -> datetime | None:
    """`closes_at` z bramki (kontrakt 0.19.0), gdy jest późniejszy niż wpływ; inaczej None (termin z OM1)."""
    raw = item.get("closes_at")
    if not raw:
        return None
    try:
        when = _moment(str(raw))
    except ValueError:
        return None
    return when if when > received else None


STAGES = ("new", "reminder", "due_today", "overdue", "paused", "review")


def add_business_days(moment: datetime, days: int) -> datetime:
    """`days` dni roboczych później, o tej samej godzinie (sobota i niedziela się nie liczą)."""
    d, left = moment, days
    while left > 0:
        d += timedelta(days=1)
        if d.weekday() < 5:
            left -= 1
    return d


def _half_business_day(moment: datetime) -> datetime:
    """12 godzin później; wypadające w weekend przesuwa na poniedziałek o tej samej godzinie."""
    d = moment + timedelta(hours=12)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def stages(item: dict[str, Any]) -> list[tuple[str, datetime]]:
    """Etapy pozycji po „new” z chwilami (UTC), rosnąco (OM1 §4–§5)."""
    received = _moment(str(item["received_at"]))
    closes = _closes_at(item, received)
    if closes is not None:  # termin z bramki: te same proporcje co OM1 (połowa, 2 ×, 4 ×)
        span = closes - received
        out = [("reminder", received + span / 2)]
        start_of_due_day = closes.replace(hour=0, minute=0, second=0, microsecond=0)
        if start_of_due_day > out[-1][1]:
            out.append(("due_today", start_of_due_day))
        return [*out, ("overdue", closes), ("paused", received + 2 * span), ("review", received + 4 * span)]
    days = deadline_days(item)
    due = add_business_days(received, days)
    out = []
    if days == 1:
        out.append(("reminder", _half_business_day(received)))
    else:
        out.append(("reminder", add_business_days(received, 3 if days >= 5 else max(1, days // 2))))
        start_of_due_day = due.replace(hour=0, minute=0, second=0, microsecond=0)
        if start_of_due_day > out[-1][1]:
            out.append(("due_today", start_of_due_day))
    out += [
        ("overdue", due),
        ("paused", add_business_days(received, 2 * days)),
        ("review", add_business_days(received, 4 * days)),
    ]
    return out


def due_date(received: date, days: int) -> date:
    """`days` dni roboczych po dniu wpływu (sobota i niedziela się nie liczą)."""
    d = received
    left = days
    while left > 0:
        d += timedelta(days=1)
        if d.weekday() < 5:
            left -= 1
    return d


def message(item: dict[str, Any], config: ChannelsConfig, stage: str = "new") -> dict[str, Any]:
    """Treść „czeka na Ciebie”: co, przy jakiej zmianie, do kiedy i gdzie zdecydować. Bez treści artefaktów.

    `stage` ≠ „new” (N3) dokleja etap do `id`, więc każdy etap to osobna wiadomość, a ponowiony — ta sama."""
    received = date.fromisoformat(str(item["received_at"])[:10])
    days = deadline_days(item)
    closes = _closes_at(item, _moment(str(item["received_at"])))
    out: dict[str, Any] = {
        "id": (f"waiting-{item['id']}" if stage == "new" else f"waiting-{item['id']}-{stage}")[:128],
        "type": "gate.waiting",
        "stage": stage,
        "source": "pdi",
        "item": item["id"],
        "kind": item["kind"],
        "summary": str(item.get("summary") or item["id"])[:300],
        "received_at": item["received_at"],
        "due": (closes.date() if closes else due_date(received, days)).isoformat(),
        "business_days": days,
        "where": "sdlc open → Skrzynka",
    }
    if item.get("change"):
        out["change"] = item["change"]
    if item.get("gate"):
        out["gate"] = item["gate"]
    # kontrakt 0.19.0 (N2): co obowiązuje po terminie i jak trudno to cofnąć
    for key in ("default_option", "reversibility"):
        if item.get(key):
            out[key] = item[key]
    if config.console_url:
        out["url"] = f"{config.console_url.rstrip('/')}/inbox/{item['id']}"
    return out


def notify(
    config: ChannelsConfig,
    item: dict[str, Any],
    *,
    at: str,
    post: Post | None = None,
    now: int | None = None,
    stage: str = "new",
) -> dict[str, Any]:
    """Wysyła „czeka na Ciebie” (albo etap N3); wynik `{"status": sent | skipped | failed, …}` do zapisu w pozycji."""
    msg = message(item, config, stage)
    result: dict[str, Any] = {"status": "failed", "at": at, "id": msg["id"], "due": msg["due"]}
    if not config.url:
        return {**result, "status": "skipped", "error": "Brak PDI_CHANNELS_URL — „czeka na Ciebie” nie wysłane."}
    sent = _send(
        config.url,
        config.url.rstrip("/") + PATH,
        config.secret,
        msg,
        names=("PDI_CHANNELS_URL", "PDI_CHANNELS_SIGNING_SECRET"),
        who="DI Channels",
        post=post,
        now=now,
    )
    return {**result, **sent}


def main() -> None:
    """`pdi-deadlines`: przypomnienia i skutki terminów otwartych pozycji (do uruchamiania z crona co godzinę)."""
    import json
    import sys

    from pdi.inbox import Inbox  # skrzynka importuje ten moduł
    from pdi.registry import Registry

    done = Inbox(Registry.from_env(), channels=ChannelsConfig.from_env()).check_deadlines()
    stages_done = [{k: d[k] for k in ("item", "change", "stage")} for d in done]
    json.dump({"stages": stages_done}, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
