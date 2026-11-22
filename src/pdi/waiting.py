"""„Czeka na Ciebie” (krok 17 planu budowy suity, CH2): nowa pozycja skrzynki idzie do DI Channels.

Terminy z operating modelu przyjętego jako OM1 (`docs/16-operating-model.md` §3–§4): dni robocze od wpływu pozycji,
weekendy pominięte (święta nie). Wiadomość: `POST <PDI_CHANNELS_URL>/pdi/waiting`, podpis jak w pozostałych
kierunkach (`X-PDI-Signature: v1=HMAC-SHA256(PDI_CHANNELS_SIGNING_SECRET, "<ts>.<body>")`). To nie jest zdarzenie
kontraktu: odbiorcą jest osoba, nie aplikacja (jak `problem.notification` z F5).

Link do konsoli tylko z `PDI_CONSOLE_URL` i **bez tokenu sesji**: konsola lokalna wymaga tokenu w adresie, a token
nie może trafić do komunikatora. Bez adresu wiadomość mówi, gdzie znaleźć pozycję (`sdlc open` → Skrzynka).
Błąd wysyłki nie cofa pozycji; wynik zostaje w pozycji (`waiting_notice`).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date, timedelta
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


def due_date(received: date, days: int) -> date:
    """`days` dni roboczych po dniu wpływu (sobota i niedziela się nie liczą)."""
    d = received
    left = days
    while left > 0:
        d += timedelta(days=1)
        if d.weekday() < 5:
            left -= 1
    return d


def message(item: dict[str, Any], config: ChannelsConfig) -> dict[str, Any]:
    """Treść „czeka na Ciebie”: co, przy jakiej zmianie, do kiedy i gdzie zdecydować. Bez treści artefaktów."""
    received = date.fromisoformat(str(item["received_at"])[:10])
    days = business_days(str(item["kind"]), item.get("gate"))
    out: dict[str, Any] = {
        "id": f"waiting-{item['id']}"[:128],
        "type": "gate.waiting",
        "source": "pdi",
        "item": item["id"],
        "kind": item["kind"],
        "summary": str(item.get("summary") or item["id"])[:300],
        "received_at": item["received_at"],
        "due": due_date(received, days).isoformat(),
        "business_days": days,
        "where": "sdlc open → Skrzynka",
    }
    if item.get("change"):
        out["change"] = item["change"]
    if item.get("gate"):
        out["gate"] = item["gate"]
    if config.console_url:
        out["url"] = f"{config.console_url.rstrip('/')}/inbox/{item['id']}"
    return out


def notify(
    config: ChannelsConfig, item: dict[str, Any], *, at: str, post: Post | None = None, now: int | None = None
) -> dict[str, Any]:
    """Wysyła „czeka na Ciebie”; wynik `{"status": sent | skipped | failed, …}` do zapisu w pozycji."""
    msg = message(item, config)
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
