"""Skrzynka bramek: pliki `inbox/<ID zdarzenia>.yaml` w katalogu rejestru (G1.5, F4).

Co trafia do skrzynki: `gate.requested` z tf i ci_for_sdlc, `readiness.changed: ready` z ci_for_sdlc (bramka
„Approve for implementation”), `release.stage_changed` z ShipScope (bramka etapu flagi) i `feature.released` z
`release: R1` (ocena skutku MVP). Każde zdarzenie aktualizuje też stan zmiany (`pdi.changes`, reguły w `pdi.flow`).
Decyzja na bramce zapisuje się w rejestrze, przesuwa stan, zostawia `gate.decided` w `outbox/` i uruchamia
następną fazę tf (`pdi.dispatch`). Plany: docs/plan-g15-pdi.md, docs/plan-f4-pdi.md.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeAlias

import yaml

from pdi import contract, flow
from pdi.changes import ChangeStore
from pdi.dispatch import DispatchConfig, Post, dispatch_phase
from pdi.registry import Decision, InvalidDecision, Registry

Item: TypeAlias = dict[str, Any]

# Kto może przysłać który typ zdarzenia.
ACCEPTED = {
    "shipscope": ("release.stage_changed", "feature.released"),
    "tf": ("gate.requested",),
    "ci_for_sdlc": ("gate.requested", "readiness.changed"),
}
GATE_OUTCOMES = flow.OUTCOMES
SIGNATURE_TOLERANCE_SECONDS = 300
MVP_RELEASE = "R1"
SEEN_EVENTS_KEPT = 200
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
    def __init__(self, registry: Registry, *, dispatch: DispatchConfig | None = None, post: Post | None = None) -> None:
        self.registry = registry
        self.changes = ChangeStore(registry)
        self._dir = registry.root / "inbox"
        self._outbox = registry.root / "outbox"
        self._dispatch = dispatch or DispatchConfig(repo=None)
        self._post = post

    # --- przyjęcie ---

    def receive(self, event: dict[str, Any]) -> dict[str, Any]:
        """Przyjmuje zdarzenie: `created` (nowa pozycja), `duplicate`, albo `recorded` (tylko stan zmiany)."""
        _check_event(event)
        payload = event["payload"]
        change = payload["change"]
        if self._known(event["id"]):
            return {"status": "duplicate", "item": self.get(event["id"])}
        at = _iso(self.registry.now())
        state = self.changes.load(change)
        gate = _gate_of(event)
        if event["type"] == "readiness.changed":
            state = flow.readiness_changed(state, payload["readiness"], at=at)
        if event["type"] == "feature.released":
            state = flow.feature_released(state, payload.get("release"), payload["released_at"], at=at)

        if gate is None and not (event["type"] == "feature.released" and payload.get("release") == MVP_RELEASE):
            # Bez pozycji w skrzynce duplikat rozpoznaje się po ID zapisanym w stanie zmiany.
            seen = state.setdefault("seen_events", [])
            if event["id"] in seen:
                return {"status": "duplicate", "item": None}
            state["seen_events"] = [*seen, event["id"]][-SEEN_EVENTS_KEPT:]
            path = self.changes.save(state)
            warning = self.registry.commit([path], f"{change}: {event['type']} ({event['source']})")
            return {"status": "recorded", "item": None, **({"warning": warning} if warning else {})}

        item: Item = {
            "id": event["id"],
            "kind": "gate" if gate else "impact_review",
            "status": "open",
            "change": change,
            "source": event["source"],
            "release": payload.get("release"),
            "summary": _summary(event),
            "received_at": at,
            "event": event,
        }
        touched: list[Path] = []
        if gate:
            missing = flow.missing_before(state, gate)
            item.update(gate=gate, missing_before=missing)
            for key in ("artifact", "url", "questions"):
                if key in payload:
                    item[key] = payload[key]
            if missing:
                item["summary"] += f" (poza kolejnością: brak {', '.join(missing)})"
            state = flow.gate_requested(state, gate, at=at)
            touched += self._supersede(change, gate, by=item["id"])
        self._dir.mkdir(parents=True, exist_ok=True)
        try:
            self._write(item, overwrite=False)
        except FileExistsError:
            return {"status": "duplicate", "item": self.get(item["id"])}
        touched += [self._path(item["id"]), self.changes.save(state)]
        warning = self.registry.commit(touched, f"inbox {item['id']}: {item['summary']}")
        return {"status": "created", "item": item, **({"warning": warning} if warning else {})}

    def _known(self, item_id: str) -> bool:
        return self._path(item_id).is_file()

    def _supersede(self, change: str, gate: str, *, by: str) -> list[Path]:
        """Starsze otwarte prośby o tę samą bramkę tej zmiany ustępują nowej."""
        touched = []
        for old in self.items():
            if old["change"] == change and old.get("gate") == gate:
                self._write({**old, "status": "superseded", "superseded_by": by}, overwrite=True)
                touched.append(self._path(old["id"]))
        return touched

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

        Bramka wymaga `outcome` (approved / changes_requested / rejected); ocena skutku go nie przyjmuje. Po decyzji
        na bramce stan zmiany się przesuwa, `gate.decided` trafia do `outbox/`, a następna faza tf jest uruchamiana.
        """
        item = self.get(item_id)
        if item["status"] == "superseded":
            raise ItemClosed(f"Pozycję {item_id} zastąpiła nowsza prośba {item['superseded_by']}.")
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
        state = self.changes.load(item["change"])
        at = _iso(self.registry.now())
        # Pozycje z G1.5 sprzed F4 nie mają pola gate — bramkę odtwarza się ze zdarzenia.
        gate: str = item.get("gate") or _gate_of(item["event"]) or ""
        if item["kind"] == "gate":
            try:  # najpierw sprawdzenie przejścia, żeby nie zapisać decyzji, której stan nie przyjmie
                flow.gate_decided(state, gate, outcome or "", "DEC-0", at=at)
            except flow.InvalidTransition as e:
                raise InvalidDecision(str(e)) from e
        tags = list(draft.get("tags") or [])
        tags += [t for t in _tags(item, gate, outcome) if t not in tags]
        decision = self.registry.record({**draft, "kind": _DECISION_KIND[item["kind"]], "links": links, "tags": tags})

        result: dict[str, Any] = {}
        touched = [self._path(item_id)]
        if item["kind"] == "gate":
            assert outcome is not None  # noqa: S101 — zawężenie typu, sprawdzone wyżej
            state, run = flow.gate_decided(state, gate, outcome, decision["id"], at=at)
            event = _gate_decided_event(item_id, item["change"], gate, outcome, decision["id"], at)
            touched.append(self._write_outbox(event))
            result["event"] = event
            if run:
                state["dispatch"] = self._run(state["change"], run, gate, outcome, decision["id"], at)
        else:
            state = flow.impact_reviewed(state, decision["id"], at=at)
        touched.append(self.changes.save(state))

        item = {**item, "status": "decided", "decision": decision["id"], "decided_at": at}
        if outcome is not None:
            item["outcome"] = outcome
        self._write(item, overwrite=True)
        warning = self.registry.commit(touched, f"inbox {item_id}: zamknięta decyzją {decision['id']}")
        return {
            "item": item,
            "decision": decision,
            "change": state,
            **result,
            **({"warning": warning} if warning else {}),
        }

    def retry_dispatch(self, change: str) -> dict[str, Any]:
        """Ponawia ostatnie nieudane albo pominięte uruchomienie fazy zmiany."""
        state = self.changes.get(change)
        last = state.get("dispatch")
        if not last or last["status"] == "sent":
            raise InvalidDecision(f"{change}: nie ma uruchomienia fazy do ponowienia.")
        run = {"phase": last["phase"], "rework": last["rework"]}
        at = _iso(self.registry.now())
        state["dispatch"] = self._run(change, run, last["gate"], last["outcome"], last["decision"], at)
        state["history"].append({"at": at, "what": "dispatch.retried", "status": state["dispatch"]["status"]})
        path = self.changes.save(state)
        warning = self.registry.commit([path], f"{change}: ponowione uruchomienie fazy {run['phase']}")
        return {"change": change, "dispatch": state["dispatch"], **({"warning": warning} if warning else {})}

    def _run(self, change: str, run: dict[str, Any], gate: str, outcome: str, decision: str, at: str) -> dict[str, Any]:
        result = dispatch_phase(
            self._dispatch,
            change=change,
            phase=run["phase"],
            gate=gate,
            outcome=outcome,
            decision=decision,
            rework=run["rework"],
            at=at,
            post=self._post,
        )
        return {**result, "gate": gate, "outcome": outcome, "decision": decision}

    # --- pliki ---

    def _path(self, item_id: str) -> Path:
        return self._dir / f"{item_id}.yaml"

    def _write(self, item: Item, *, overwrite: bool) -> None:
        text = yaml.safe_dump(item, sort_keys=False, allow_unicode=True, width=1000)
        with self._path(item["id"]).open("w" if overwrite else "x", encoding="utf-8") as f:
            f.write(text)

    def _write_outbox(self, event: dict[str, Any]) -> Path:
        self._outbox.mkdir(parents=True, exist_ok=True)
        path = self._outbox / f"{event['id']}.json"
        path.write_text(json.dumps(event, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path


def _check_event(event: dict[str, Any]) -> None:
    errors = contract.rules_broken("event", event)
    if errors:
        raise InvalidEvent("Zdarzenie niezgodne z kontraktem: " + "; ".join(errors))
    allowed = ACCEPTED.get(event["source"])
    if allowed is None:
        raise InvalidEvent(f"source: skrzynka nie przyjmuje zdarzeń od {event['source']}.")
    if event["type"] not in allowed:
        raise InvalidEvent(f"type: {event['type']} nie jest przyjmowane od source {event['source']}.")
    if not _EVENT_ID.match(event["id"]):
        raise InvalidEvent("id: dozwolone litery, cyfry, „.”, „_” i „-” (do 128 znaków, bez „..”).")


def _gate_of(event: dict[str, Any]) -> str | None:
    """Bramka, o którą prosi zdarzenie, albo None."""
    p = event["payload"]
    if event["type"] == "gate.requested":
        return str(p["gate"])
    if event["type"] == "readiness.changed" and p["readiness"] == "ready":
        return flow.BASELINE_GATE
    if event["type"] == "release.stage_changed":
        return f"stage:{p['flag']}:{p['to_stage']}"
    return None


def _summary(event: dict[str, Any]) -> str:
    p = event["payload"]
    if event["type"] == "gate.requested":
        return str(p["summary"])
    if event["type"] == "readiness.changed":
        questions = p.get("open_questions")
        left = f", otwarte pytania: {questions}" if questions is not None else ""
        return f"{p['change']}: ci_for_sdlc — gotowe do implementacji{left}. Approve for implementation?"
    if event["type"] == "feature.released":
        return f"{p['change']}: MVP ({MVP_RELEASE}) u ludzi od {p['released_at']} — ocena skutku."
    where = f"{p['change']} {p['release']}" if p.get("release") else p["change"]
    step = f"z etapu {p['from_stage']} na {p['to_stage']}" if p.get("from_stage") else f"na etap {p['to_stage']}"
    rollout = f" (udostępnienie {p['rollout']}%)" if p.get("rollout") is not None else ""
    return f"{where}: flaga {p['flag']} przeszła {step}{rollout}. Przejść dalej?"


def _tags(item: Item, gate: str, outcome: str | None) -> list[str]:
    if item["kind"] != "gate":
        return ["mvp-impact"]
    tags = [f"gate:{outcome}", f"bramka:{gate}"]
    if item["event"]["type"] == "release.stage_changed":
        tags.insert(0, "release-stage")
    return tags


def _gate_decided_event(item_id: str, change: str, gate: str, outcome: str, decision: str, at: str) -> dict[str, Any]:
    event = {
        "id": f"gate.decided-{item_id}",
        "type": "gate.decided",
        "occurred_at": at,
        "source": "pdi",
        "contract_version": contract.CONTRACT_VERSION,
        "payload": {"change": change, "gate": gate, "outcome": outcome, "decision": decision},
    }
    errors = contract.errors("event", event)
    if errors:  # błąd programu, nie danych z zewnątrz
        raise RuntimeError("gate.decided niezgodne z kontraktem: " + "; ".join(errors))
    return event


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
