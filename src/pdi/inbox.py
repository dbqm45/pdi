"""Skrzynka bramek dla zdarzeń ShipScope (G1.5): pliki `inbox/<ID zdarzenia>.yaml` w katalogu rejestru.

`release.stage_changed` staje się bramką („przejść do następnego etapu?”), `feature.released` z `release: R1` —
oceną skutku MVP. Pozycję zamyka decyzja zapisana w rejestrze (`kind: gate` albo `product`, z `links.chg`).
Maszyna stanów per CHG i bramki z innych źródeł należą do F4 (docs/plan-g15-pdi.md).
"""

from __future__ import annotations

import hashlib
import hmac
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeAlias

import yaml

from pdi import contract
from pdi.registry import Decision, InvalidDecision, Registry

Item: TypeAlias = dict[str, Any]

ACCEPTED_TYPES = ("release.stage_changed", "feature.released")
GATE_OUTCOMES = ("approved", "changes_requested", "rejected")
SIGNATURE_TOLERANCE_SECONDS = 300
MVP_RELEASE = "R1"
# ID zdarzenia staje się nazwą pliku, więc tylko bezpieczne znaki i bez „..”.
_EVENT_ID = re.compile(r"^(?!.*\.\.)[A-Za-z0-9._-]{1,128}$")
_DECISION_KIND = {"gate": "gate", "impact_review": "product"}


class BadSignature(ValueError):
    """Podpis ShipScope się nie zgadza albo znacznik czasu jest za stary."""


class InvalidEvent(ValueError):
    """Zdarzenie niezgodne z kontraktem albo spoza tego, co skrzynka przyjmuje."""


class ItemNotFound(LookupError):
    """W skrzynce nie ma pozycji o podanym ID."""


class ItemClosed(ValueError):
    """Pozycja jest już zamknięta decyzją."""


def verify_signature(
    secret: str,
    timestamp: str | None,
    body: bytes,
    signature: str | None,
    *,
    now: datetime,
    tolerance: int = SIGNATURE_TOLERANCE_SECONDS,
) -> None:
    """Sprawdza `X-ShipScope-Signature: v1=<hex HMAC-SHA256(secret, "<timestamp>.<body>")>`; rzuca BadSignature.

    Znacznik czasu (sekundy Unix) może się różnić od `now` najwyżej o `tolerance` sekund, w obie strony.
    """
    if not timestamp or not timestamp.isdigit():
        raise BadSignature("Brak albo zły nagłówek X-ShipScope-Timestamp.")
    if abs(now.timestamp() - int(timestamp)) > tolerance:
        raise BadSignature("Znacznik czasu podpisu jest za stary albo z przyszłości.")
    if not signature or not signature.startswith("v1="):
        raise BadSignature("Brak podpisu v1= w nagłówku X-ShipScope-Signature.")
    expected = hmac.new(secret.encode(), timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature[3:].encode(), expected.encode()):
        raise BadSignature("Podpis się nie zgadza.")


class Inbox:
    def __init__(self, registry: Registry) -> None:
        self.registry = registry
        self._dir = registry.root / "inbox"

    # --- przyjęcie ---

    def receive(self, event: dict[str, Any]) -> dict[str, Any]:
        """Przyjmuje zdarzenie ShipScope: `created` (nowa pozycja), `duplicate` albo `ignored` (bez pozycji)."""
        _check_event(event)
        payload = event["payload"]
        if event["type"] == "feature.released" and payload.get("release") != MVP_RELEASE:
            return {"status": "ignored", "item": None}
        item: Item = {
            "id": event["id"],
            "kind": "gate" if event["type"] == "release.stage_changed" else "impact_review",
            "status": "open",
            "change": payload["change"],
            "release": payload.get("release"),
            "summary": _summary(event),
            "received_at": _iso(self.registry.now()),
            "event": event,
        }
        path = self._path(item["id"])
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._write(item, overwrite=False)
        except FileExistsError:
            return {"status": "duplicate", "item": self.get(item["id"])}
        warning = self.registry.commit([path], f"inbox {item['id']}: {item['summary']}")
        return {"status": "created", "item": item, **({"warning": warning} if warning else {})}

    # --- odczyt ---

    def get(self, item_id: str) -> Item:
        path = self._path(item_id) if _EVENT_ID.match(item_id) else None
        if path is None or not path.is_file():
            raise ItemNotFound(f"W skrzynce nie ma pozycji {item_id} — sprawdź ID przez list_inbox.")
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ItemNotFound(f"{path.name}: uszkodzona pozycja skrzynki.")
        return data

    def items(self, status: str | None = "open") -> list[Item]:
        """Pozycje skrzynki (domyślnie otwarte), od najstarszej."""
        if not self._dir.is_dir():
            return []
        found = [self.get(p.stem) for p in self._dir.glob("*.yaml")]
        if status:
            found = [i for i in found if i["status"] == status]
        return sorted(found, key=lambda i: (i["received_at"], i["id"]))

    # --- decyzja ---

    def decide(self, item_id: str, draft: Decision, *, outcome: str | None = None) -> dict[str, Any]:
        """Zamyka pozycję decyzją zapisaną w rejestrze; rodzaj i `links.chg` nadaje skrzynka.

        Bramka wymaga `outcome` (approved / changes_requested / rejected); ocena skutku go nie przyjmuje.
        """
        item = self.get(item_id)
        if item["status"] != "open":
            raise ItemClosed(f"Pozycja {item_id} jest już zamknięta decyzją {item.get('decision')}.")
        if item["kind"] == "gate" and outcome not in GATE_OUTCOMES:
            raise InvalidDecision(f"Bramka wymaga outcome: jednego z {', '.join(GATE_OUTCOMES)}.")
        if item["kind"] != "gate" and outcome is not None:
            raise InvalidDecision("outcome dotyczy tylko bramek; ocenę skutku zamyka sama decyzja.")
        links = dict(draft.get("links") or {})
        if links.get("chg", item["change"]) != item["change"]:
            raise InvalidDecision(f"Pozycja dotyczy {item['change']} — links.chg nie może wskazywać innej zmiany.")
        links["chg"] = item["change"]
        tags = list(draft.get("tags") or [])
        tags += [t for t in _tags(item, outcome) if t not in tags]
        decision = self.registry.record({**draft, "kind": _DECISION_KIND[item["kind"]], "links": links, "tags": tags})

        item = {**item, "status": "decided", "decision": decision["id"], "decided_at": _iso(self.registry.now())}
        if outcome is not None:
            item["outcome"] = outcome
        self._write(item, overwrite=True)
        warning = self.registry.commit([self._path(item_id)], f"inbox {item_id}: zamknięta decyzją {decision['id']}")
        return {"item": item, "decision": decision, **({"warning": warning} if warning else {})}

    # --- pliki ---

    def _path(self, item_id: str) -> Path:
        return self._dir / f"{item_id}.yaml"

    def _write(self, item: Item, *, overwrite: bool) -> None:
        text = yaml.safe_dump(item, sort_keys=False, allow_unicode=True, width=1000)
        with self._path(item["id"]).open("w" if overwrite else "x", encoding="utf-8") as f:
            f.write(text)


def _check_event(event: dict[str, Any]) -> None:
    errors = contract.rules_broken("event", event)
    if errors:
        raise InvalidEvent("Zdarzenie niezgodne z kontraktem: " + "; ".join(errors))
    if event["source"] != "shipscope":
        raise InvalidEvent(f"source: skrzynka przyjmuje tu tylko zdarzenia ShipScope, nie {event['source']}.")
    if event["type"] not in ACCEPTED_TYPES:
        raise InvalidEvent(f"type: skrzynka przyjmuje tylko {', '.join(ACCEPTED_TYPES)}.")
    if not _EVENT_ID.match(event["id"]):
        raise InvalidEvent("id: dozwolone litery, cyfry, „.”, „_” i „-” (do 128 znaków, bez „..”).")


def _summary(event: dict[str, Any]) -> str:
    p = event["payload"]
    if event["type"] == "feature.released":
        return f"{p['change']}: MVP ({MVP_RELEASE}) u ludzi od {p['released_at']} — ocena skutku."
    where = f"{p['change']} {p['release']}" if p.get("release") else p["change"]
    step = f"z etapu {p['from_stage']} na {p['to_stage']}" if p.get("from_stage") else f"na etap {p['to_stage']}"
    rollout = f" (udostępnienie {p['rollout']}%)" if p.get("rollout") is not None else ""
    return f"{where}: flaga {p['flag']} przeszła {step}{rollout}. Przejść dalej?"


def _tags(item: Item, outcome: str | None) -> list[str]:
    if item["kind"] == "gate":
        return ["release-stage", f"gate:{outcome}"]
    return ["mvp-impact"]


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
