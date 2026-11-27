"""Pokój sprintdecka z agendy „Discuss with team” (docs/plan-pokoj-sprintdeck.md) i jego wyniki z powrotem
(docs/plan-wyniki-sprintdecka.md).

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
import re
import urllib.parse
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
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
                "ref": e["item_id"],  # wyniki pokoju wracają do tej pozycji (plan-wyniki-sprintdecka.md)
            }
            for e in entries[:MAX_ITEMS]
        ],
    }
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    d = base64.urlsafe_b64encode(raw).decode().rstrip("=")
    s = hmac.new(str(config.secret).encode(), d.encode(), hashlib.sha256).hexdigest()
    return f"{config.url}{PATH}#{urllib.parse.urlencode({'d': d, 's': s})}"


# --- wyniki pokoju z powrotem (docs/plan-wyniki-sprintdecka.md) ---

RESULTS_DIR = "sprintdeck-results"
_REF = re.compile(r"[A-Za-z0-9._-]{1,128}")
_MAX_AGE = 3600


class ResultsRefused(ValueError):
    """Wyniki nie do przyjęcia: `off`, `signature`, `expired` albo `malformed` (powód w komunikacie)."""


def _text(v: Any, limit: int) -> bool:
    return isinstance(v, str) and len(v.strip()) > 0 and len(v) <= limit


def verify_results(config: SprintdeckConfig, d: str, s: str, *, now: datetime) -> dict[str, Any]:
    """Wyniki z linku sprintdecka po sprawdzeniu podpisu (wspólny sekret), terminu (do godziny) i kształtu."""
    if not config.on:
        raise ResultsRefused("off")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,60000}", d or "") or not re.fullmatch(r"[0-9a-f]{64}", s or ""):
        raise ResultsRefused("signature")
    expected = hmac.new(str(config.secret).encode(), d.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, s):
        raise ResultsRefused("signature")
    try:
        p = json.loads(base64.urlsafe_b64decode(d + "=" * (-len(d) % 4)))
    except ValueError as e:
        raise ResultsRefused("malformed") from e
    stamp = int(now.timestamp())
    if not isinstance(p, dict) or not isinstance(p.get("exp"), int) or not stamp <= p["exp"] <= stamp + _MAX_AGE:
        raise ResultsRefused("expired")
    room = p.get("room")
    items = p.get("items")
    if (
        p.get("v") != 1
        or not isinstance(room, dict)
        or not _text(room.get("title"), 120)
        or not (isinstance(room.get("url"), str) and re.fullmatch(r"https?://\S{1,500}", room["url"]))
        or not isinstance(items, list)
        or not 0 < len(items) <= MAX_ITEMS
    ):
        raise ResultsRefused("malformed")
    for it in items:
        ok = (
            isinstance(it, dict)
            and isinstance(it.get("ref"), str)
            and _REF.fullmatch(it["ref"])
            and _text(it.get("title"), 200)
            and (it.get("final") is None or _text(it.get("final"), 40))
            and isinstance(it.get("rounds"), int)
            and isinstance(it.get("votes"), dict)
            and all(_text(k, 40) and isinstance(v, int) for k, v in it["votes"].items())
            and (it.get("consensus") is None or _text(it.get("consensus"), 120))
            and isinstance(it.get("notes"), list)
            and len(it["notes"]) <= 3
            and all(_text(n, 400) for n in it["notes"])
        )
        if not ok:
            raise ResultsRefused("malformed")
    return p


class ResultsStore:
    """Wyniki pokoju przy sprawach agendy: `sprintdeck-results/<pozycja>.json` w rejestrze (ostatnie wygrywają)."""

    def __init__(self, root: Path) -> None:
        self.dir = root / RESULTS_DIR

    def save(self, results: dict[str, Any], *, now: datetime, open_items: set[str]) -> tuple[list[str], list[str]]:
        """Zapisuje wyniki spraw, które są otwarte na agendzie; zwraca (zapisane, pominięte tytuły)."""
        saved, skipped = [], []
        self.dir.mkdir(parents=True, exist_ok=True)
        for it in results["items"]:
            if it["ref"] not in open_items:
                skipped.append(it["title"])
                continue
            entry = {k: it[k] for k in ("title", "status", "final", "rounds", "votes", "consensus", "notes")}
            entry["room"] = {k: results["room"].get(k) for k in ("title", "url", "deck")}
            entry["received_at"] = now.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            (self.dir / f"{it['ref']}.json").write_text(
                json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            saved.append(it["ref"])
        return saved, skipped

    def get(self, item_id: str) -> dict[str, Any] | None:
        if not _REF.fullmatch(item_id):
            return None
        path = self.dir / f"{item_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
