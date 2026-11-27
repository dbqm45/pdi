"""Pokój sprintdecka z agendy „Discuss with team” (docs/plan-pokoj-sprintdeck.md).

pdi nie zakłada pokoju sam: daje decydentowi link `<PDI_SPRINTDECK_URL>/from-pdi#d=<base64url JSON>&s=<hex HMAC>`.
Sprawy są w części `#` adresu (nie trafiają do logów serwerów), podpisane HMAC-SHA256 wspólnym sekretem
(`PDI_SPRINTDECK_SECRET`, ten sam w sprintdecku) i ważne niecałą godzinę. Sprintdeck sprawdza podpis na serwerze, wymaga
logowania przez suitę i zakłada pokój z talią „Risk”, w którym prowadzącym jest osoba, która otworzyła link. Decyzję
zapisuje się dalej na agendzie w pdi. Limity jak w sprintdecku: 30 spraw, tytuł 200 znaków, opis 2000, tytuł pokoju 120.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import urllib.parse
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

PATH = "/from-pdi"
MAX_ITEMS = 30
VALID_SECONDS = 50 * 60  # sprintdeck przyjmuje do godziny; zapas na różnicę zegarów
_LOCAL = ("127.0.0.1", "localhost", "::1")


@dataclass(frozen=True)
class SprintdeckConfig:
    url: str | None
    secret: str | None = field(default=None, repr=False)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> SprintdeckConfig:
        env = os.environ if env is None else env
        url = (env.get("PDI_SPRINTDECK_URL") or "").strip().rstrip("/") or None
        if url:
            parts = urllib.parse.urlsplit(url)
            if parts.username or not (parts.scheme == "https" or (parts.scheme == "http" and parts.hostname in _LOCAL)):
                raise ValueError("PDI_SPRINTDECK_URL musi być adresem https:// (http tylko dla localhost), bez loginu.")
        return cls(url=url, secret=(env.get("PDI_SPRINTDECK_SECRET") or "").strip() or None)

    @property
    def on(self) -> bool:
        return bool(self.url and self.secret)


def _cut(text: str, limit: int) -> str:
    text = " ".join(str(text).split()) if "\n" not in str(text) else str(text)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _description(e: dict[str, Any]) -> str:
    lines = []
    where = " · ".join(x for x in (e.get("change"), e.get("gate")) if x)
    if where:
        lines.append(where)
    if e.get("reasons"):
        lines.append("Why now: " + "; ".join(e["reasons"]))
    if e.get("options"):
        lines.append("Options: " + ", ".join(e["options"]))
    for a in e.get("answers") or []:
        said = f"{a['option']} — {a['reason']}" if a.get("option") else "no answer"
        lines.append(f"{a['name']}: {said}")
    return _cut("\n".join(lines), 2000)


def room_link(entries: list[dict[str, Any]], config: SprintdeckConfig, *, now: datetime) -> str | None:
    """Podpisany link do pokoju ze sprawami agendy; None bez ustawień albo bez spraw."""
    if not config.on or not entries:
        return None
    payload = {
        "v": 1,
        "title": f"Discuss with team — {now.date().isoformat()}"[:120],
        "exp": int(now.timestamp()) + VALID_SECONDS,
        "items": [
            {
                "title": _cut(" ".join(str(e.get("summary") or e["item_id"]).split()), 200),
                "description": _description(e),
            }
            for e in entries[:MAX_ITEMS]
        ],
    }
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    d = base64.urlsafe_b64encode(raw).decode().rstrip("=")
    s = hmac.new(str(config.secret).encode(), d.encode(), hashlib.sha256).hexdigest()
    return f"{config.url}{PATH}#{urllib.parse.urlencode({'d': d, 's': s})}"
