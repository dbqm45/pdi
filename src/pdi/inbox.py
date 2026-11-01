"""Skrzynka bramek: pliki `inbox/<ID zdarzenia>.yaml` w katalogu rejestru (G1.5, F4).

Co trafia do skrzynki: `gate.requested` z tf i ci_for_sdlc, `readiness.changed: ready` z ci_for_sdlc (bramka
„Approve for implementation”), `release.stage_changed` z ShipScope (bramka etapu flagi) i `feature.released` z
`release: R1`, który planuje ocenę skutku MVP; `open_due_reviews()` otwiera ją po terminie z danymi z ShipScope
(`pdi.impact`). Każde zdarzenie aktualizuje też stan zmiany (`pdi.changes`, reguły w `pdi.flow`). Decyzja na bramce
zapisuje się w rejestrze, przesuwa stan, zostawia `gate.decided` w `outbox/` i uruchamia następną fazę tf
(`pdi.dispatch`). Propozycje zmiany poziomu autonomii (A3, `pdi.autonomy`) też są pozycjami skrzynki; zatwierdzenie
zmienia politykę `autonomy.yaml`. `decision.recorded` z ci_for_sdlc (A2b, kontrakt 0.7.0) nie tworzy pozycji: to
decyzja już podjęta u nadawcy, więc trafia wprost do rejestru (licznik akceptacji z A3 ją liczy). Plany:
docs/plan-g15-pdi.md, docs/plan-f4-pdi.md, docs/plan-f5-ocena-skutku.md, docs/plan-a3-licznik-akceptacji.md,
docs/plan-a2b-pdi.md.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, TypeAlias

import yaml

from pdi import autonomy, capture, contract, dispatch_local, flow, forecast, impact
from pdi import pr_state as pr_state_mod
from pdi.changes import ChangeStore
from pdi.dispatch import DispatchConfig, Post, dispatch_phase
from pdi.notify import NotifyConfig, ReporterNotifyConfig, notify_ci_for_sdlc
from pdi.problems import ProblemStore
from pdi.registry import CannotSupersede, Decision, DecisionNotFound, InvalidDecision, Registry

Item: TypeAlias = dict[str, Any]

# Kto może przysłać który typ zdarzenia.
ACCEPTED = {
    "shipscope": ("release.stage_changed", "feature.released"),
    "tf": ("gate.requested", "metric.breached"),
    "ci_for_sdlc": ("gate.requested", "readiness.changed", "decision.recorded"),
}
# Typy decyzji, które nadawca zapisuje w rejestrze zdarzeniem `decision.recorded` (decyzja D-A2).
RECORDABLE = {"ci_for_sdlc": ("finding.auto_close",)}
GATE_OUTCOMES = flow.OUTCOMES
IMPACT_OUTCOMES = impact.OUTCOMES
PROBLEM_OUTCOMES = ("accepted", "rejected")
AUTONOMY_OUTCOMES = ("approved", "rejected")
CAPTURE_OUTCOMES = ("approved", "rejected")
SIGNATURE_TOLERANCE_SECONDS = 300
MVP_RELEASE = "R1"
SEEN_EVENTS_KEPT = 200
# ID zdarzenia staje się nazwą pliku, więc tylko bezpieczne znaki i bez „..”.
_EVENT_ID = re.compile(r"^(?!.*\.\.)[A-Za-z0-9._-]{1,128}$")
_DECISION_KIND = {"gate": "gate", "impact_review": "product", "problem": "triage", "autonomy": "process"}
# Typ decyzji (kontrakt 0.5.0) nadawany przez skrzynkę, gdy szkic go nie podaje; bramki: zob. _decision_type.
_DECISION_TYPE = {"impact_review": "outcome.assessment", "problem": "triage", "autonomy": autonomy.LEVEL_CHANGE_TYPE}


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
    def __init__(
        self,
        registry: Registry,
        *,
        dispatch: DispatchConfig | None = None,
        post: Post | None = None,
        notify: NotifyConfig | None = None,
        notify_post: Post | None = None,
        shipscope: impact.ShipScopeConfig | None = None,
        shipscope_get: impact.Get | None = None,
        reporters: ReporterNotifyConfig | None = None,
        reporter_post: Post | None = None,
        local_spawn: dispatch_local.Spawn | None = None,
        local_run: dispatch_local.Run | None = None,
        pr_state: pr_state_mod.Check | None = None,
    ) -> None:
        self.registry = registry
        self.changes = ChangeStore(registry)
        self._dir = registry.root / "inbox"
        self._outbox = registry.root / "outbox"
        self._dispatch = dispatch or DispatchConfig(repo=None)
        self._post = post
        self._notify = notify or NotifyConfig(url=None)
        self._notify_post = notify_post
        self._shipscope = shipscope or impact.ShipScopeConfig(url=None)
        self._shipscope_get = shipscope_get
        self._local_spawn = local_spawn
        self._local_run = local_run
        self._pr_state = pr_state
        # Zgłaszający zmiany dostaje powiadomienie o jej wydaniu i ocenie skutku (F5).
        self.problems = ProblemStore(
            registry,
            notify=reporters,
            post=reporter_post,
            dispatch=self._dispatch,
            dispatch_post=post,
            local_spawn=local_spawn,
            local_run=local_run,
        )

    # --- przyjęcie ---

    def receive(self, event: dict[str, Any]) -> dict[str, Any]:
        """Przyjmuje zdarzenie: `created` (nowa pozycja), `duplicate`, `scheduled` (zaplanowana ocena skutku MVP)
        albo `recorded` (tylko stan zmiany)."""
        _check_event(event)
        if event["type"] == "decision.recorded":
            return self._record_decision(event)
        payload = event["payload"]
        if self._known(event["id"]):
            return {"status": "duplicate", "item": self.get(event["id"])}
        if event["type"] == "metric.breached":
            return self._receive_problem(event)
        change = payload["change"]
        at = _iso(self.registry.now())
        state = self.changes.load(change)
        gate = _gate_of(event)
        if event["type"] == "readiness.changed":
            state = flow.readiness_changed(state, payload["readiness"], at=at)
        if event["type"] == "feature.released":
            state = flow.feature_released(
                state, payload.get("release"), payload["released_at"], at=at, tasks=payload.get("tasks")
            )
            state = self._settle(state, self.registry.now().date(), at)

        if gate is None:
            # Bez pozycji w skrzynce duplikat rozpoznaje się po ID zapisanym w stanie zmiany.
            seen = state.setdefault("seen_events", [])
            if event["id"] in seen:
                return {"status": "duplicate", "item": None}
            state["seen_events"] = [*seen, event["id"]][-SEEN_EVENTS_KEPT:]
            status, extra = "recorded", {}
            mvp = event["type"] == "feature.released" and payload.get("release") == MVP_RELEASE
            if mvp and "impact_review" not in state:
                state = flow.impact_scheduled(state, self._plan_review(change, payload["released_at"]), at=at)
                status, extra = "scheduled", {"impact_review": state["impact_review"]}
            path = self.changes.save(state)
            warning = self.registry.commit([path], f"{change}: {event['type']} ({event['source']})")
            if event["type"] == "feature.released":
                sent = self.problems.change_released(change, payload.get("release"), payload["released_at"])
                if sent:
                    extra["notifications"] = sent
            return {"status": status, "item": None, **extra, **({"warning": warning} if warning else {})}

        item: Item = {
            "id": event["id"],
            "kind": "gate",
            "status": "open",
            "change": change,
            "source": event["source"],
            "release": payload.get("release"),
            "summary": _summary(event),
            "received_at": at,
            "event": event,
        }
        missing = flow.missing_before(state, gate)
        item.update(gate=gate, missing_before=missing)
        for key in ("artifact", "url", "questions"):
            if key in payload:
                item[key] = payload[key]
        if missing:
            item["summary"] += f" (poza kolejnością: brak {', '.join(missing)})"
        state = flow.gate_requested(state, gate, at=at)
        touched = self._supersede(change, gate, by=item["id"])
        self._dir.mkdir(parents=True, exist_ok=True)
        try:
            self._write(item, overwrite=False)
        except FileExistsError:
            return {"status": "duplicate", "item": self.get(item["id"])}
        touched += [self._path(item["id"]), self.changes.save(state)]
        warning = self.registry.commit(touched, f"inbox {item['id']}: {item['summary']}")
        return {"status": "created", "item": item, **({"warning": warning} if warning else {})}

    def _record_decision(self, event: dict[str, Any]) -> dict[str, Any]:
        """Decyzja podjęta u nadawcy → rejestr: `recorded` albo `duplicate` (to samo zdarzenie) z numerem `DEC`."""
        p, sender = event["payload"], event["source"]
        decision_type, ref = p["decision_type"], p["ref"]
        allowed = RECORDABLE.get(sender, ())
        if decision_type not in allowed:
            raise InvalidEvent(
                f"decision_type: {sender} nie zapisuje decyzji typu {decision_type} (może: {', '.join(allowed)})."
            )
        if "automation" in p and decision_type in contract.settings()["autonomy"]["protected_types"]:
            raise InvalidEvent(f"{decision_type} to typ chroniony (DA2): decyduje człowiek, bez automation.")
        seen = self.registry.find(tags=[f"event:{event['id']}"], limit=1)
        if seen:
            return {"status": "duplicate", "item": None, "decision": seen[0]["id"]}

        tags = [sender, f"ref:{ref}", f"event:{event['id']}", f"typ:{decision_type}"]
        warnings = []
        if "automation" in p:
            policy_level = autonomy.level_of(self.registry, decision_type)
            if p["automation"]["level"] < policy_level:
                tags.append("autonomy:outside-policy")
                warnings.append(
                    f"{decision_type}: automat na poziomie {p['automation']['level']}, a polityka pdi ma poziom "
                    f"{policy_level} — zapisane ze znacznikiem autonomy:outside-policy."
                )
        draft: Decision = {
            "statement": p["statement"],
            "why": p.get("why") or f"Decyzja z {sender} ({decision_type}) dla {ref}.",
            "decided_by": p["decided_by"],
            "decided_at": event["occurred_at"][:10],
            "kind": p.get("kind", "other"),
            "decision_type": decision_type,
            "drafted_by": p["drafted_by"],
            "source": {"kind": sender, "url": p.get("url") or ref, "excerpt": ref},
            "tags": tags,
        }
        for key in ("draft_edited", "automation"):
            if key in p:
                draft[key] = p[key]
        if p.get("evidence"):
            draft["evidence"] = [{**e, "epistemic_status": "observation"} for e in p["evidence"]]
        links = {k: p[f] for k, f in (("chg", "change"), ("prb", "problem")) if f in p}
        if links:
            draft["links"] = links
        try:
            if "supersedes" in p:
                self._check_superseded(p["supersedes"], sender, ref)
                decision = self.registry.supersede(p["supersedes"], draft)
            else:
                decision = self.registry.record(draft)
        except (InvalidDecision, CannotSupersede) as e:
            raise InvalidEvent(str(e)) from e
        if decision.get("warning"):
            warnings.append(decision["warning"])
        status = "duplicate" if decision.get("duplicate") else "recorded"
        result: dict[str, Any] = {"status": status, "item": None, "decision": decision["id"]}
        return {**result, "warning": " ".join(warnings)} if warnings else result

    def _check_superseded(self, old_id: str, sender: str, ref: str) -> None:
        """Nadawca zastępuje tylko własną decyzję o tym samym `ref` (np. ponowne otwarcie pytania)."""
        try:
            old = self.registry.get(old_id)
        except DecisionNotFound as e:
            raise InvalidEvent(f"supersedes: nie ma decyzji {old_id}.") from e
        if old["source"].get("kind") != sender or f"ref:{ref}" not in old.get("tags", ()):
            raise InvalidEvent(f"supersedes: {old_id} nie jest decyzją {sender} dla {ref}.")

    def _dismiss_capture(self, item: Item, draft: Decision) -> dict[str, Any]:
        """Odrzucony szkic z rozmowy („to nie była decyzja”): pozycja zamknięta, bez wpisu w rejestrze."""
        at = _iso(self.registry.now())
        item = {**item, "status": "decided", "outcome": "rejected", "decision": None, "decided_at": at}
        if draft.get("why"):
            item["rejection_reason"] = draft["why"]
        self._write(item, overwrite=True)
        warning = self.registry.commit([self._path(item["id"])], f"inbox {item['id']}: szkic odrzucony")
        return {"item": item, "decision": None, "change": None, **({"warning": warning} if warning else {})}

    def _plan_review(self, change: str, released_at: str) -> dict[str, Any]:
        intent = impact.intent_decision(self.registry, change)
        due, basis = impact.due_date(released_at, intent)
        return {"due": due, "basis": basis, "intent": intent["id"] if intent else None, "released_at": released_at}

    # --- ocena skutku (F5) ---

    def open_due_reviews(self, *, today: date | None = None) -> list[Item]:
        """Otwiera oceny skutku, których termin minął: dane z ShipScope i szkic wniosku (`pdi.impact`)."""
        day = today or self.registry.now().astimezone(UTC).date()
        opened: list[Item] = []
        for state in self.changes.all(status=None):
            plan = state.get("impact_review") or {}
            if plan.get("status") != "scheduled" or plan["due"] > day.isoformat():
                continue
            change = state["change"]
            intent = self._decision_or_none(plan.get("intent"))
            metric = intent.get("success_metric") if intent else None
            data = impact.collect(self._shipscope, change, plan["released_at"], day, get=self._shipscope_get)
            draft = impact.draft_verdict(metric, data)
            at = _iso(self.registry.now())
            what = f"{metric['metric']}, cel {metric['target']}" if metric else "brak metryki sukcesu"
            item: Item = {
                "id": f"impact-{change}-{MVP_RELEASE}",
                "kind": "impact_review",
                "status": "open",
                "change": change,
                "source": "pdi",
                "release": MVP_RELEASE,
                "summary": (
                    f"{change}: ocena skutku MVP ({MVP_RELEASE}, u ludzi od {plan['released_at']}) — {what}; "
                    f"szkic: {draft['verdict']}."
                ),
                "received_at": at,
                "intent": intent["id"] if intent else None,
                "metric": metric,
                "draft": draft,
                "data": data,
            }
            self._dir.mkdir(parents=True, exist_ok=True)
            try:
                self._write(item, overwrite=False)
            except FileExistsError:
                continue
            state = flow.impact_opened(state, item["id"], at=at)
            paths = [self._path(item["id"]), self.changes.save(state)]
            warning = self.registry.commit(paths, f"inbox {item['id']}: {item['summary']}")
            opened.append({**item, **({"warning": warning} if warning else {})})
        return opened

    def _decision_or_none(self, decision_id: str | None) -> Decision | None:
        if not decision_id:
            return None
        try:
            return self.registry.get(decision_id)
        except DecisionNotFound:
            return None

    def _receive_problem(self, event: dict[str, Any]) -> dict[str, Any]:
        """Pasmo kontrolne tf przekroczone (F5): pozycja „nowy problem do triażu”, bez zmiany stanu żadnej zmiany."""
        p = event["payload"]
        where = f" ({p['service']})" if p.get("service") else ""
        window = f", {p['window']}" if p.get("window") else ""
        item: Item = {
            "id": event["id"],
            "kind": "problem",
            "status": "open",
            "change": p.get("change"),
            "source": event["source"],
            "release": None,
            "summary": (
                f"Metryka {p['metric']}{where}: {p['value']} wobec progu {p['threshold']}{window} — nowy problem "
                f"do triażu (przyjąć jako zgłoszenie?)."
            ),
            "received_at": _iso(self.registry.now()),
            "metric": p,
            "event": event,
        }
        self._dir.mkdir(parents=True, exist_ok=True)
        try:
            self._write(item, overwrite=False)
        except FileExistsError:
            return {"status": "duplicate", "item": self.get(item["id"])}
        warning = self.registry.commit([self._path(item["id"])], f"inbox {item['id']}: {item['summary']}")
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

    # --- autonomia (A3) ---

    def propose_captures(
        self, source: dict[str, Any], text: str, candidates: list[dict[str, Any]]
    ) -> dict[str, list[Any]]:
        """Szkice decyzji z wątku albo transkrypcji (A5) → pozycje `kind: capture`.

        Kandydatura bez cytatu obecnego w tekście wraca w `refused` z powodem; ta sama drugi raz — w `duplicates`.
        Tekst rozmowy nie jest zapisywany.
        """
        capture.check_source(source, text)
        at = _iso(self.registry.now())
        created: list[Item] = []
        refused: list[dict[str, str]] = []
        duplicates: list[str] = []
        for candidate in candidates:
            problem = capture.candidate_problem(candidate, text)
            if problem:
                refused.append({"statement": str(candidate.get("statement") or ""), "reason": problem})
                continue
            item = capture.item(source, candidate, item_id=capture.item_id(source, candidate, at[:10]), at=at)
            self._dir.mkdir(parents=True, exist_ok=True)
            try:
                self._write(item, overwrite=False)
            except FileExistsError:
                duplicates.append(item["id"])
                continue
            warning = self.registry.commit([self._path(item["id"])], f"inbox {item['id']}: {item['summary'][:60]}")
            created.append({**item, **({"warning": warning} if warning else {})})
        return {"items": created, "refused": refused, "duplicates": duplicates}

    def propose_autonomy_changes(self) -> list[Item]:
        """Pozycje „zmienić poziom autonomii typu X?” dla rekomendacji z licznika akceptacji szkiców.

        Najwyżej jedna otwarta propozycja na typ decyzji; o zmianie decyduje człowiek (`decide`).
        """
        try:
            found = autonomy.proposals(self.registry)
        except autonomy.InvalidPolicy as e:
            raise InvalidDecision(str(e)) from e
        open_types = {i.get("decision_type") for i in self.items() if i["kind"] == "autonomy"}
        at = _iso(self.registry.now())
        day = at[:10].replace("-", "")
        created: list[Item] = []
        for proposal in found:
            if proposal["decision_type"] in open_types:
                continue
            item: Item = {
                "id": f"autonomy-{proposal['decision_type']}-to{proposal['to_level']}-{day}",
                "kind": "autonomy",
                "status": "open",
                "change": None,
                "source": "pdi",
                "release": None,
                "received_at": at,
                **proposal,
            }
            self._dir.mkdir(parents=True, exist_ok=True)
            try:
                self._write(item, overwrite=False)
            except FileExistsError:
                continue
            warning = self.registry.commit([self._path(item["id"])], f"inbox {item['id']}: {item['summary']}")
            created.append({**item, **({"warning": warning} if warning else {})})
        return created

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

        Bramka wymaga `outcome` (approved / changes_requested / rejected), ocena skutku — wyniku potwierdzonego przez
        człowieka (met / not_met / unknown). Po decyzji na bramce stan zmiany się przesuwa, `gate.decided` trafia do
        `outbox/`, a następna faza tf jest uruchamiana. Decyzja z oceny skutku zależy od decyzji o intencji i dostaje
        odczyty z ShipScope jako dowody.
        """
        item = self.get(item_id)
        if item["status"] == "superseded":
            raise ItemClosed(f"Pozycję {item_id} zastąpiła nowsza prośba {item['superseded_by']}.")
        if item["status"] != "open":
            raise ItemClosed(f"Pozycja {item_id} jest już zamknięta decyzją {item.get('decision')}.")
        if item["kind"] == "gate" and outcome not in GATE_OUTCOMES:
            raise InvalidDecision(f"Bramka wymaga outcome: jednego z {', '.join(GATE_OUTCOMES)}.")
        if item["kind"] == "impact_review" and outcome not in IMPACT_OUTCOMES:
            raise InvalidDecision(f"Ocena skutku wymaga outcome: jednego z {', '.join(IMPACT_OUTCOMES)}.")
        if item["kind"] == "problem" and outcome not in PROBLEM_OUTCOMES:
            raise InvalidDecision(f"Triaż problemu wymaga outcome: jednego z {', '.join(PROBLEM_OUTCOMES)}.")
        if item["kind"] == "autonomy" and outcome not in AUTONOMY_OUTCOMES:
            raise InvalidDecision(f"Propozycja autonomii wymaga outcome: {' albo '.join(AUTONOMY_OUTCOMES)}.")
        if item["kind"] == "capture" and outcome not in CAPTURE_OUTCOMES:
            raise InvalidDecision(f"Szkic z rozmowy wymaga outcome: {' albo '.join(CAPTURE_OUTCOMES)}.")
        if item["kind"] == "capture" and outcome == "rejected":
            return self._dismiss_capture(item, draft)
        new_policy = None
        if item["kind"] == "autonomy" and outcome == "approved":
            try:  # najpierw sprawdzenie polityki, żeby nie zapisać decyzji, której kontrakt nie przyjmie
                new_policy = autonomy.policy_after(self.registry, item)
            except autonomy.InvalidPolicy as e:
                raise InvalidDecision(str(e)) from e
        links = dict(draft.get("links") or {})
        if item["change"] and links.get("chg", item["change"]) != item["change"]:
            raise InvalidDecision(f"Pozycja dotyczy {item['change']} — links.chg nie może wskazywać innej zmiany.")
        if item["change"]:
            links["chg"] = item["change"]
        state = self.changes.load(item["change"]) if item["kind"] in ("gate", "impact_review") else None
        at = _iso(self.registry.now())
        # Pozycje z G1.5 sprzed F4 nie mają pola gate — bramkę odtwarza się ze zdarzenia.
        gate: str = (item.get("gate") or _gate_of(item["event"]) or "") if item["kind"] == "gate" else ""
        if item["kind"] == "gate" and state is not None:
            try:  # najpierw sprawdzenie przejścia, żeby nie zapisać decyzji, której stan nie przyjmie
                _, planned = flow.gate_decided(state, gate, outcome or "", "DEC-0", at=at)
            except flow.InvalidTransition as e:
                raise InvalidDecision(str(e)) from e
            if planned:
                self._refuse_if_running(item["change"])
        pr_warning = self._check_pr(item) if item["kind"] == "gate" and outcome == "approved" else None
        tags = list(draft.get("tags") or [])
        tags += [t for t in _tags(item, gate, outcome) if t not in tags]
        extra: dict[str, Any] = {}
        if item["kind"] == "impact_review":
            extra = _impact_fields(item, draft)
        if item["kind"] == "problem":
            extra = _problem_fields(item, draft)
        if item["kind"] == "autonomy":
            extra = {"evidence": [*(draft.get("evidence") or []), autonomy.evidence(item)]}
        if item["kind"] == "capture":
            extra = capture.decision_fields(item, draft)
        decision_type = draft.get("decision_type") or _decision_type(item, gate)
        if item["kind"] == "autonomy":
            decision_type = autonomy.LEVEL_CHANGE_TYPE
        record = {
            **draft,
            **extra,
            "kind": _DECISION_KIND.get(item["kind"], extra.get("kind")),
            "links": links,
            "tags": tags,
        }
        if decision_type:
            record["decision_type"] = decision_type
        decision = self.registry.record(record)

        result: dict[str, Any] = {}
        touched = [self._path(item_id)]
        if item["kind"] == "gate":
            assert outcome is not None and state is not None  # noqa: S101 — zawężenie typu, sprawdzone wyżej
            state, run = flow.gate_decided(state, gate, outcome, decision["id"], at=at)
            event = _gate_decided_event(item_id, item["change"], gate, outcome, decision["id"], at)
            touched.append(self._write_outbox(event))
            result["event"] = event
            if run:
                state["dispatch"] = self._run(state["change"], run, gate, outcome, decision["id"], at)
            if gate == flow.BASELINE_GATE:
                # „Approve for implementation” ustawia baseline historyjek w ci_for_sdlc (F4).
                state["ci_for_sdlc"] = notify_ci_for_sdlc(self._notify, event, at=at, post=self._notify_post)
                if outcome == "approved" and self._shipscope.url:
                    # Baseline planu to chwila prognozy (G3): cięcia z planu × czas przepływu z ShipScope.
                    state = self._forecast(state, self.registry.now().date(), at)
        elif state is not None:
            state = flow.impact_reviewed(state, decision["id"], at=at, outcome=outcome)
            result["notifications"] = self.problems.impact_reviewed(item["change"], outcome or "", decision["id"])
        if new_policy is not None:
            touched.append(autonomy.write_policy(self.registry, new_policy, decision=decision["id"], at=at))
            result["policy"] = new_policy
        if state is not None:
            touched.append(self.changes.save(state))

        item = {**item, "status": "decided", "decision": decision["id"], "decided_at": at}
        if outcome is not None:
            item["outcome"] = outcome
        self._write(item, overwrite=True)
        warning = self.registry.commit(touched, f"inbox {item_id}: zamknięta decyzją {decision['id']}")
        warning = " ".join(w for w in (pr_warning, warning) if w) or None
        return {
            "item": item,
            "decision": decision,
            "change": state,
            **result,
            **({"warning": warning} if warning else {}),
        }

    # --- prognoza (G3) ---

    def make_forecast(self, change: str, *, today: date | None = None) -> dict[str, Any]:
        """Liczy prognozę zmiany od nowa (np. po poprawie planu) i zapisuje ją w stanie zmiany."""
        at = _iso(self.registry.now())
        state = self._forecast(self.changes.get(change), today or self.registry.now().date(), at)
        self.registry.commit([self.changes.save(state)], f"{change}: prognoza")
        return dict(state["forecast"])

    def settle_forecasts(self, *, today: date | None = None) -> list[dict[str, Any]]:
        """Przebieg dzienny (`pdi-forecast`): wynik dla dostarczonych zmian, nowa próba nieudanych prognoz."""
        if not self._shipscope.url:
            return []
        day, at = today or self.registry.now().date(), _iso(self.registry.now())
        changed, touched = [], []
        for state in self.changes.all(status=None):
            new = self._settle(state, day, at)
            if new is state:
                continue
            touched.append(self.changes.save(new))
            made = new.get("forecast") or {}
            entry = {"change": new["change"], "forecast": made.get("status"), "actual": made.get("actual")}
            if "flow" in new and "flow" not in state:
                entry["flow_days"] = new["flow"]["actual_days"]
            changed.append(entry)
        if touched:
            self.registry.commit(touched, f"prognozy: {', '.join(c['change'] for c in changed)}")
        return changed

    def _forecast(self, state: flow.State, today: date, at: str) -> flow.State:
        change = state["change"]
        tasks, error = forecast.read_tasks(self._shipscope, change, get=self._shipscope_get)
        history = None
        if tasks is not None:
            start = today - timedelta(days=forecast.HISTORY_DAYS - 1)
            history, error = forecast.read_flow(self._shipscope, start, today, get=self._shipscope_get)
        made: dict[str, Any]
        if tasks is None or history is None:
            made = {"status": "failed", "made_at": at, "error": error}
        else:
            made = {"status": "ok", "made_at": at, **forecast.estimate(tasks, history)}
        return flow.forecast_made(state, made, at=at)

    def _settle(self, state: flow.State, today: date, at: str) -> flow.State:
        """Stan z wynikiem prognozy i rzeczywistym czasem przepływu, z ponowioną nieudaną prognozą albo ten sam obiekt.

        Rzeczywisty czas przepływu (`flow`) dostaje każda wydana zmiana, także bez prognozy albo z nieudaną (PRB-22).
        """
        if not self._shipscope.url:
            return state
        raw = state.get("forecast")
        made: dict[str, Any] | None = raw if isinstance(raw, dict) else None
        # Nieudana prognoza: ponowiona, dopóki zmiana jest otwarta i niewydana. Po pierwszym wydaniu byłaby już
        # częściowo wynikiem — zostaje nieudana; zamkniętej zmiany też nie prognozuje się od nowa.
        if made is not None and made["status"] != "ok" and state["status"] == "open" and not state.get("releases"):
            return self._forecast(state, today, at)
        forecast_open = made is not None and made["status"] == "ok" and "actual" not in made
        flow_open = "flow" not in state and bool(state.get("releases"))
        if not forecast_open and not flow_open:
            return state
        history_at = [h.get("at") for h in state.get("history") or [] if isinstance(h, dict) and h.get("at")]
        since = str(made["made_at"] if made else (history_at[0] if history_at else _iso(self.registry.now())))
        start = max(date.fromisoformat(since[:10]), today - timedelta(days=impact.MAX_WINDOW_DAYS - 1))
        history, _ = forecast.read_flow(self._shipscope, min(start, today), today, get=self._shipscope_get)
        delivered = next(
            (c for c in (history or {}).get("changes", []) if isinstance(c, dict) and c.get("key") == state["change"]),
            None,
        )
        days = (delivered or {}).get("flowDays")
        if not isinstance(days, int | float) or isinstance(days, bool):
            return state
        new = state
        if forecast_open:
            assert made is not None  # noqa: S101 — zawężenie typu
            new = flow.forecast_settled(new, forecast.compare(made, float(days)), at=at)
        if "flow" not in new:
            new = flow.flow_measured(new, float(days), at=at)
        return new

    def retry_dispatch(self, change: str) -> dict[str, Any]:
        """Ponawia nieudane albo pominięte uruchomienie fazy i nieudaną wysyłkę decyzji do ci_for_sdlc."""
        state = self.changes.get(change)
        last: dict[str, Any] = state.get("dispatch") or {}
        sent_ci: dict[str, Any] = state.get("ci_for_sdlc") or {}
        if last.get("status") == "running":
            self._refuse_if_running(change)
        redo_run = bool(last) and last["status"] in ("failed", "skipped")
        redo_ci = bool(sent_ci) and sent_ci["status"] != "sent"
        if not redo_run and not redo_ci:
            raise InvalidDecision(f"{change}: nie ma uruchomienia fazy ani wysyłki do ci_for_sdlc do ponowienia.")
        at = _iso(self.registry.now())
        out: dict[str, Any] = {"change": change}
        if redo_run:
            run = {
                "phase": last["phase"],
                "rework": last["rework"],
                "source": last.get("source"),
                "problem": last.get("problem"),
            }
            if (
                self._dispatch.local and run["source"] and not run["problem"]
            ):  # lokalnie treści zgłoszenia nie ma w stanie
                run["problem"] = self.problems.phase_problem(self.problems.get(run["source"]))
            state["dispatch"] = self._run(change, run, last["gate"], last["outcome"], last["decision"], at)
            state["history"].append({"at": at, "what": "dispatch.retried", "status": state["dispatch"]["status"]})
            out["dispatch"] = state["dispatch"]
        if redo_ci:
            event = json.loads((self._outbox / f"{sent_ci['event']}.json").read_text(encoding="utf-8"))
            state["ci_for_sdlc"] = notify_ci_for_sdlc(self._notify, event, at=at, post=self._notify_post)
            state["history"].append({"at": at, "what": "ci_for_sdlc.retried", "status": state["ci_for_sdlc"]["status"]})
            out["ci_for_sdlc"] = state["ci_for_sdlc"]
        path = self.changes.save(state)
        warning = self.registry.commit([path], f"{change}: ponowione uruchomienie fazy lub wysyłka do ci_for_sdlc")
        return {**out, **({"warning": warning} if warning else {})}

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
            source=run.get("source"),
            problem=run.get("problem"),
            decision_text=self._decision_text(decision),
            runs_dir=self.registry.root / "runs",
            spawn=self._local_spawn,
            run=self._local_run,
        )
        kept = ("source",) if self._dispatch.local else ("source", "problem")
        extra = {k: run[k] for k in kept if run.get(k)}
        return {**result, "gate": gate, "outcome": outcome, "decision": decision, **extra}

    def _decision_text(self, decision: str) -> str | None:
        """Ustalenie i uzasadnienie decyzji z rejestru — dla `decisions.md` w repo produktu (PRB-3)."""
        try:
            d = self.registry.get(decision)
        except DecisionNotFound:
            return None
        return f"{d['statement'].strip()} Dlaczego: {d['why'].strip()}"

    def _check_pr(self, item: Item) -> str | None:
        """Odmawia zatwierdzenia bramki z niezmergowanym PR-em fazy (PRB-2); stan nieznany daje ostrzeżenie."""
        url = item.get("url")
        if self._pr_state is None or not isinstance(url, str) or not pr_state_mod.is_pr_url(url):
            return None
        found = self._pr_state(url)
        if found["state"] == "merged":
            return None
        if found["state"] in ("open", "closed"):
            how = "jest otwarty" if found["state"] == "open" else "zamknięto bez merge'u"
            raise InvalidDecision(
                f"PR fazy {url} {how} — następna faza startuje od aktualnego main, więc najpierw zrób merge "
                "i zatwierdź ponownie albo wybierz changes_requested."
            )
        return f"Nie sprawdzono, czy PR {url} jest zmergowany ({found.get('reason', 'brak powodu')}) — upewnij się sam."

    def _refuse_if_running(self, change: str) -> None:
        busy = dispatch_local.running(self.registry.root / "runs", change)
        if busy is not None:
            raise InvalidDecision(f"{change}: trwa poprzednia faza (log {busy}) — poczekaj na jej koniec i ponów.")

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
    where = f"{p['change']} {p['release']}" if p.get("release") else p["change"]
    step = f"z etapu {p['from_stage']} na {p['to_stage']}" if p.get("from_stage") else f"na etap {p['to_stage']}"
    rollout = f" (udostępnienie {p['rollout']}%)" if p.get("rollout") is not None else ""
    return f"{where}: flaga {p['flag']} przeszła {step}{rollout}. Przejść dalej?"


def _impact_fields(item: Item, draft: Decision) -> dict[str, Any]:
    """Zależność od decyzji o intencji i odczyt z ShipScope jako dowód (tylko gdy pdi coś zmierzył)."""
    out: dict[str, Any] = {}
    intent = item.get("intent")
    deps = list(draft.get("dependencies") or [])
    if intent and intent not in deps:
        out["dependencies"] = [*deps, intent]
    observed = (item.get("draft") or {}).get("observed")
    if observed is not None:
        reading = {"text": f"ShipScope: {item['draft']['reason']}", "epistemic_status": "observation"}
        out["evidence"] = [*(draft.get("evidence") or []), reading]
    return out


def _problem_fields(item: Item, draft: Decision) -> dict[str, Any]:
    """Odczyt pasma kontrolnego tf jako dowód decyzji z triażu."""
    p = item["metric"]
    text = f"tf, pasma kontrolne: {p['metric']} = {p['value']} wobec progu {p['threshold']}"
    text += f" ({p['window']})" if p.get("window") else ""
    text += f". {p['diagnosis']}" if p.get("diagnosis") else "."
    return {"evidence": [*(draft.get("evidence") or []), {"text": text, "epistemic_status": "observation"}]}


def _decision_type(item: Item, gate: str) -> str | None:
    """Typ decyzji z pozycji skrzynki: bramka etapu flagi → flag.stage_advance, inna bramka → gate.<bramka>.

    Szkic z rozmowy (A5) nie ma typu, chyba że poda go człowiek."""
    if item["kind"] != "gate":
        return _DECISION_TYPE.get(item["kind"])
    if item["event"]["type"] == "release.stage_changed":
        return "flag.stage_advance"
    slug = re.sub(r"[^a-z0-9]+", "_", gate.lower()).strip("_")
    return f"gate.{slug}" if slug[:1].isalpha() else f"gate.g{slug}"


def _tags(item: Item, gate: str, outcome: str | None) -> list[str]:
    if item["kind"] == "capture":
        return ["capture", f"capture:{item['source']['kind']}"]
    if item["kind"] == "autonomy":
        return ["autonomy", f"autonomy:{outcome}", f"typ:{item['decision_type']}"]
    if item["kind"] == "problem":
        return ["metric-breached", f"problem:{outcome}", f"metric:{item['metric']['metric']}"]
    if item["kind"] != "gate":
        return ["mvp-impact", f"impact:{outcome}"]
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
