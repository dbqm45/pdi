"""Mały rejestr zgłoszeń (PRB) i powiadomienia zgłaszającego (F5): pliki `problems/<PRB>.yaml` w katalogu rejestru.

Zgłoszenie ma kształt `contract/problem.schema.json` (sprawdzany przy każdym zapisie); pdi nadaje `id`, `reported_at`
i `status`. Triaż zapisuje decyzję `kind: triage` i ustawia wynik w zgłoszeniu. Zgłaszający dostaje podpisane
`problem.notification` po triażu, po wydaniu zmiany, z której wyszło zgłoszenie, i po ocenie skutku tej zmiany
(`pdi.notify.notify_reporter`); dziennik wysyłek w `notifications/<PRB>.yaml`.

F3: podobne zgłoszenia przy zapisie, doprecyzowanie (pytania do zgłaszającego, notatki w `problem-notes/<PRB>.yaml`),
scalenie duplikatu z oryginałem, powrót odłożonego po progu zgłoszeń i przyjęcie do budowy — nowa zmiana CHG,
`problem.accepted` w `outbox/` i faza `intent` w tf (`pdi.dispatch`).
Plany: docs/plan-f5-powiadomienia.md, docs/plan-f3-pdi.md.
"""

from __future__ import annotations

import json
import re
from datetime import UTC
from pathlib import Path
from typing import Any, TypeAlias

import yaml

from pdi import contract, dispatch_local
from pdi.changes import ChangeStore
from pdi.dispatch import DispatchConfig, Post, dispatch_phase
from pdi.notify import ReporterNotifyConfig, notify_reporter
from pdi.registry import Decision, InvalidDecision, Registry

Problem: TypeAlias = dict[str, Any]

OUTCOMES = ("accepted", "rejected", "parked", "duplicate")
SET_BY_PDI = ("id", "reported_at", "status", "triage_decision", "change")
# Pole wymagane przez wynik triażu (pozostałe są opcjonalne).
REQUIRED_FOR = {"duplicate": "duplicate_of"}
# Zgłoszenia, które nie są już kandydatami na „podobne”.
CLOSED = ("rejected", "duplicate")
SIMILAR_MIN = 0.3
SIMILAR_MAX = 5
QUESTIONS_MAX = 5
# Opis zgłoszenia, który można poprawiać po zapisie (reszta należy do pdi albo do triażu).
EDITABLE = (
    "kind",
    "category",
    "title",
    "who",
    "cannot",
    "impact",
    "workaround",
    "frequency",
    "cost",
    "proposed_solution",
    "source_url",
    "project",
    "evidence",
)
_WORD = re.compile(r"\w{4,}")
# „3 nowe zgłoszenia”, „5 zgłoszeń”, „2 new reports”
_THRESHOLD = re.compile(r"(\d+)\s+(?:nowe|nowych|new)?\s*(?:zgłosz|report)", re.IGNORECASE)
IMPACT_TEXT = {"met": "cel osiągnięty", "not_met": "cel nieosiągnięty", "unknown": "nie wiadomo, czy cel osiągnięto"}
_KEY = re.compile(contract.settings()["key_pattern"])


class InvalidProblem(ValueError):
    """Szkic zgłoszenia niezgodny z kontraktem."""


class ProblemNotFound(LookupError):
    """W rejestrze nie ma zgłoszenia o tym kluczu."""


class ProblemStore:
    def __init__(
        self,
        registry: Registry,
        *,
        notify: ReporterNotifyConfig | None = None,
        post: Post | None = None,
        dispatch: DispatchConfig | None = None,
        dispatch_post: Post | None = None,
        local_spawn: dispatch_local.Spawn | None = None,
        local_run: dispatch_local.Run | None = None,
    ) -> None:
        self.registry = registry
        self._dir = registry.root / "problems"
        self._log_dir = registry.root / "notifications"
        self._notes_dir = registry.root / "problem-notes"
        self._notify = notify or ReporterNotifyConfig(url=None)
        self._post = post
        self._dispatch = dispatch or DispatchConfig(repo=None)
        self._dispatch_post = dispatch_post
        self._local_spawn = local_spawn
        self._local_run = local_run
        self._prefix = contract.settings()["prefixes"]["problem"]
        self._change_prefix = contract.settings()["prefixes"]["change"]

    # --- rejestr ---

    def record(self, draft: Problem) -> Problem:
        """Zapisuje nowe zgłoszenie (status `new`); id i datę nadaje pdi."""
        own = [f for f in SET_BY_PDI if f in draft]
        if own:
            raise InvalidProblem(f"Pola {', '.join(own)} nadaje pdi — usuń je ze szkicu.")
        item = {"id": self._next_id(), **draft, "reported_at": self.registry.now().astimezone(UTC).date().isoformat()}
        item["status"] = "new"
        self._check(item)
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self._write(item, overwrite=False)
        warning = self.registry.commit([path], f"{item['id']}: {item['title'][:60]}")
        return {**item, "similar": self.similar(item["id"]), **({"warning": warning} if warning else {})}

    def similar(self, problem_id: str) -> list[dict[str, Any]]:
        """Zgłoszenia podobne do `problem_id` (słowa tytułu i opisu), najbardziej podobne pierwsze."""
        item = self.get(problem_id)
        mine = _words(item)
        found = []
        for other in self.all():
            if other["id"] == problem_id or other["status"] in CLOSED:
                continue
            theirs = _words(other)
            score = len(mine & theirs) / len(mine | theirs) if mine | theirs else 0.0
            if score >= SIMILAR_MIN:
                found.append(
                    {"id": other["id"], "title": other["title"], "status": other["status"], "score": round(score, 2)}
                )
        return sorted(found, key=lambda s: (-s["score"], _number(s["id"])))[:SIMILAR_MAX]

    # --- doprecyzowanie ---

    def clarify(self, problem_id: str, questions: list[str]) -> dict[str, Any]:
        """Pytania do zgłaszającego (1–5): status `clarifying`, pytania w notatkach i w powiadomieniu."""
        item = self.get(problem_id)
        asked = [q.strip() for q in questions if q.strip()]
        if not 1 <= len(asked) <= QUESTIONS_MAX:
            raise InvalidProblem(f"Podaj 1–{QUESTIONS_MAX} pytań do zgłaszającego.")
        if item["status"] in OUTCOMES:
            raise InvalidProblem(f"{problem_id} ma już wynik triażu: {item['status']}.")
        updated = {**item, "status": "clarifying"}
        notes = self._notes(problem_id)
        notes.setdefault("questions", []).append({"at": self._at(), "questions": asked})
        paths = [self._write(updated, overwrite=True), self._save_notes(problem_id, notes)]
        self.registry.commit(paths, f"{problem_id}: pytania do zgłaszającego")
        notification = self._send(updated, "questions", questions=asked, round=len(notes["questions"]))
        return {"problem": updated, "notification": notification}

    def update(self, problem_id: str, fields: dict[str, Any], *, ready: bool = False) -> Problem:
        """Poprawia opis zgłoszenia (np. rozwiązanie przeformułowane na problem); `ready` → `ready_for_triage`."""
        item = self.get(problem_id)
        own = [f for f in fields if f not in EDITABLE]
        if own:
            raise InvalidProblem(f"Pól {', '.join(own)} nie poprawia się tutaj (status i wynik nadaje triaż).")
        if item["status"] in OUTCOMES:
            raise InvalidProblem(f"{problem_id} ma już wynik triażu: {item['status']}.")
        updated = {**item, **fields}
        if ready:
            updated["status"] = "ready_for_triage"
        self._check(updated)
        path = self._write(updated, overwrite=True)
        self.registry.commit([path], f"{problem_id}: opis poprawiony")
        return updated

    def get(self, problem_id: str) -> Problem:
        path = self._path(problem_id) if _KEY.match(problem_id) else None
        if path is None or not path.is_file():
            raise ProblemNotFound(f"Nie ma zgłoszenia {problem_id} — sprawdź list_problems.")
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ProblemNotFound(f"{path.name}: uszkodzone zgłoszenie.")
        return data

    def all(self, status: str | None = None) -> list[Problem]:
        if not self._dir.is_dir():
            return []
        found = [self.get(p.stem) for p in self._dir.glob("*.yaml")]
        return sorted([p for p in found if not status or p["status"] == status], key=lambda p: _number(p["id"]))

    # --- triaż ---

    def triage(
        self,
        problem_id: str,
        outcome: str,
        draft: Decision,
        *,
        change: str | None = None,
        rejection_reason: str | None = None,
        rejection_note: str | None = None,
        return_when: str | None = None,
        duplicate_of: str | None = None,
    ) -> dict[str, Any]:
        """Decyzja z triażu (`kind: triage`, `links.prb`), jej wynik w zgłoszeniu, potem powiadomienie zgłaszającego."""
        item = self.get(problem_id)
        if outcome not in OUTCOMES:
            raise InvalidDecision(f"outcome: jeden z {', '.join(OUTCOMES)}.")
        if item["status"] in OUTCOMES:
            raise InvalidDecision(
                f"{problem_id} ma już wynik triażu: {item['status']} ({item.get('triage_decision')})."
            )
        given = {
            "change": change,
            "rejection_reason": rejection_reason,
            "rejection_note": rejection_note,
            "return_when": return_when,
            "duplicate_of": duplicate_of,
        }
        needed = REQUIRED_FOR.get(outcome)
        if needed and not given[needed]:
            raise InvalidDecision(f"Wynik {outcome} wymaga {needed}.")
        if outcome == "accepted" and not change:
            given["change"] = change = self._next_change()
        if outcome == "duplicate":
            if duplicate_of == problem_id:
                raise InvalidDecision("duplicate_of: zgłoszenie nie może być duplikatem samego siebie.")
            if duplicate_of and not _KEY.match(duplicate_of):
                raise InvalidDecision("duplicate_of: klucz zgłoszenia, np. PRB-7.")
        updated = {**item, **{k: v for k, v in given.items() if v}, "status": outcome}
        self._check({**updated, "triage_decision": "DEC-1"}, InvalidDecision)  # zanim decyzja trafi do rejestru
        busy = dispatch_local.running(self.registry.root / "runs", change) if self._dispatch.local and change else None
        if outcome == "accepted" and busy is not None:
            raise InvalidDecision(f"{change}: trwa poprzednia faza (log {busy}) — poczekaj na jej koniec.")

        links = {**(draft.get("links") or {}), "prb": problem_id}
        if change:
            links["chg"] = change
        tags = [*(draft.get("tags") or []), f"problem:{outcome}"]
        decision = self.registry.record(
            {
                **draft,
                "kind": "triage",
                "decision_type": draft.get("decision_type") or "triage",
                "links": links,
                "tags": list(dict.fromkeys(tags)),
            }
        )
        updated["triage_decision"] = decision["id"]
        paths = [self._write(updated, overwrite=True)]
        result: dict[str, Any] = {}
        if outcome == "parked":
            notes = self._notes(problem_id)
            notes["parked_reports"] = int(updated.get("reports_count") or 1)
            paths.append(self._save_notes(problem_id, notes))
        if outcome == "duplicate" and duplicate_of:
            merged = self._merge(updated, duplicate_of)
            if merged:
                paths += merged["paths"]
                result["original"] = merged["original"]
        if outcome == "accepted":
            assert change is not None  # noqa: S101 — nadane wyżej
            accepted = self._accept(updated, change, decision["id"])
            paths += accepted["paths"]
            result.update(dispatch=accepted["dispatch"], event=accepted["event"])
        warning = self.registry.commit(paths, f"{problem_id}: triaż {outcome} ({decision['id']})")
        notification = self._send(updated, outcome, change=updated.get("change"), decision=decision["id"])
        if result.get("original", {}).get("returned"):
            original = result["original"]["problem"]
            result["original"]["notification"] = self._send(original, "returned", round=original["reports_count"])
        return {
            "problem": updated,
            "decision": decision,
            "notification": notification,
            **result,
            **({"warning": warning} if warning else {}),
        }

    def _merge(self, duplicate: Problem, original_id: str) -> dict[str, Any] | None:
        """Duplikat to dowód: oryginał dostaje liczbę zgłoszeń, dowód i powiązanie; odłożony może wrócić."""
        try:
            original = self.get(original_id)
        except ProblemNotFound:
            return None
        count = int(original.get("reports_count") or 1) + int(duplicate.get("reports_count") or 1)
        note = (
            f"Duplikat {duplicate['id']} od {duplicate['reporter']} z {duplicate['reported_at']}: {duplicate['title']}"
        )
        merged = {
            **original,
            "reports_count": count,
            "evidence": [*(original.get("evidence") or []), {"text": note, "epistemic_status": "observation"}],
            "related": list(dict.fromkeys([*(original.get("related") or []), duplicate["id"]])),
        }
        returned = False
        if original["status"] == "parked":
            threshold = _THRESHOLD.search(str(original.get("return_when") or ""))
            parked_at = int(self._notes(original_id).get("parked_reports") or 1)
            if threshold and count - parked_at >= int(threshold.group(1)):
                merged["status"] = "ready_for_triage"
                returned = True
        self._check(merged)
        return {"paths": [self._write(merged, overwrite=True)], "original": {"problem": merged, "returned": returned}}

    def _accept(self, item: Problem, change: str, decision: str) -> dict[str, Any]:
        """Przyjęcie do budowy: stan zmiany, `problem.accepted` w outbox i faza `intent` w tf."""
        at = self._at()
        changes = ChangeStore(self.registry)
        state = changes.load(change)
        state["source"] = item["id"]
        state.setdefault("history", []).append({"at": at, "what": "problem.accepted", "problem": item["id"]})
        payload: dict[str, Any] = {"problem": item["id"], "change": change, "decision": decision}
        if item.get("project"):
            payload["project"] = item["project"]
        event: dict[str, Any] = {
            "id": f"problem.accepted-{item['id']}",
            "type": "problem.accepted",
            "occurred_at": at,
            "source": "pdi",
            "contract_version": contract.CONTRACT_VERSION,
            "payload": payload,
        }
        errors = contract.errors("event", event)
        if errors:  # błąd programu, nie danych z zewnątrz
            raise RuntimeError("problem.accepted niezgodne z kontraktem: " + "; ".join(errors))
        outbox = self.registry.root / "outbox"
        outbox.mkdir(parents=True, exist_ok=True)
        event_path = outbox / f"{event['id']}.json"
        event_path.write_text(json.dumps(event, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        problem = self.phase_problem(item)
        sent = dispatch_phase(
            self._dispatch,
            change=change,
            phase="intent",
            gate="triage",
            outcome="approved",
            decision=decision,
            rework=False,
            at=at,
            post=self._dispatch_post,
            source=item["id"],
            problem=problem,
            runs_dir=self.registry.root / "runs",
            spawn=self._local_spawn,
            run=self._local_run,
        )
        state["dispatch"] = {
            **sent,
            "gate": "triage",
            "outcome": "approved",
            "decision": decision,
            "source": item["id"],
        }
        if not self._dispatch.local:  # lokalnie treść zgłoszenia nie trafia do stanu; ponowienie czyta ją ze zgłoszenia
            state["dispatch"]["problem"] = problem
        return {"paths": [event_path, changes.save(state)], "dispatch": sent, "event": event}

    def phase_problem(self, item: Problem) -> str:
        """Treść zgłoszenia dla persony fazy intent (JSON z polami tekstowymi i dniem zgłoszenia)."""
        fields = (
            "title",
            "kind",
            "who",
            "cannot",
            "impact",
            "workaround",
            "frequency",
            "proposed_solution",
            "reported_at",
        )
        return json.dumps({k: item[k] for k in fields if item.get(k)}, ensure_ascii=False)

    def _next_change(self) -> str:
        """Kolejny wolny klucz zmiany ponad znane stany zmian i zgłoszenia."""
        changes_dir = self.registry.root / "changes"
        taken = [_number(p.stem) for p in changes_dir.glob("*.yaml")] if changes_dir.is_dir() else []
        taken += [_number(p["change"]) for p in self.all() if p.get("change")]
        return f"{self._change_prefix}-{max(taken, default=0) + 1}"

    # --- powiadomienia ---

    def change_released(self, change: str, release: str | None, released_at: str) -> list[dict[str, Any]]:
        """Powiadamia zgłaszających zgłoszeń, z których wyszła `change`, że linia jest u ludzi."""
        return [
            self._send(p, "released", change=change, release=release or "all", released_at=released_at)
            for p in self._of_change(change)
        ]

    def impact_reviewed(self, change: str, outcome: str, decision: str) -> list[dict[str, Any]]:
        """Powiadamia zgłaszających o wyniku oceny skutku zmiany."""
        return [
            self._send(p, "impact_reviewed", change=change, outcome=outcome, decision=decision)
            for p in self._of_change(change)
        ]

    def retry(self, problem_id: str) -> dict[str, Any]:
        """Ponawia nieudane i pominięte powiadomienia zgłoszenia (np. po ustawieniu PDI_NOTIFY_URL)."""
        self.get(problem_id)
        log = self._log(problem_id)
        out = []
        for entry in [e for e in log if e["status"] != "sent"]:
            result = notify_reporter(self._notify, entry["message"], at=self._at(), post=self._post)
            entry.update(status=result["status"], at=result["at"], error=result.get("error"))
            out.append({k: v for k, v in entry.items() if k != "message"})
        if out:
            self._save_log(problem_id, log)
        return {"problem": problem_id, "notifications": out}

    def _of_change(self, change: str) -> list[Problem]:
        return [p for p in self.all() if p.get("change") == change]

    def _send(self, item: Problem, what: str, **details: Any) -> dict[str, Any]:
        suffix = (
            f"-{details['release']}" if what == "released" else f"-{details['round']}" if "round" in details else ""
        )
        message: dict[str, Any] = {
            "id": f"notify-{item['id']}-{what}{suffix}",
            "type": "problem.notification",
            "occurred_at": self._at(),
            "source": "pdi",
            "problem": item["id"],
            "title": item["title"],
            "reporter": item["reporter"],
            "channel": item["channel"],
            "what": what,
            "message": _message(item, what, details),
            **{k: v for k, v in details.items() if v is not None},
        }
        log = self._log(item["id"])
        known = next((e for e in log if e["id"] == message["id"]), None)
        if known and known["status"] == "sent":
            return {k: v for k, v in known.items() if k != "message"}
        result = notify_reporter(self._notify, message, at=message["occurred_at"], post=self._post)
        entry = {"id": message["id"], "what": what, "status": result["status"], "at": result["at"]}
        if result.get("error"):
            entry["error"] = result["error"]
        log = [e for e in log if e["id"] != message["id"]] + [{**entry, "message": message}]
        self._save_log(item["id"], log)
        return entry

    # --- pliki ---

    def _check(self, item: Problem, error: type[Exception] = InvalidProblem) -> None:
        errors = contract.rules_broken("problem", item)
        if errors:
            raise error("Zgłoszenie niezgodne z kontraktem: " + "; ".join(errors))

    def _next_id(self) -> str:
        taken = [_number(p.stem) for p in self._dir.glob("*.yaml")] if self._dir.is_dir() else []
        return f"{self._prefix}-{max(taken, default=0) + 1}"

    def _path(self, problem_id: str) -> Path:
        return self._dir / f"{problem_id}.yaml"

    def _write(self, item: Problem, *, overwrite: bool) -> Path:
        path = self._path(item["id"])
        text = yaml.safe_dump(item, sort_keys=False, allow_unicode=True, width=1000)
        with path.open("w" if overwrite else "x", encoding="utf-8") as f:
            f.write(text)
        return path

    def _log(self, problem_id: str) -> list[dict[str, Any]]:
        path = self._log_dir / f"{problem_id}.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else None
        return data if isinstance(data, list) else []

    def _save_log(self, problem_id: str, log: list[dict[str, Any]]) -> None:
        self._log_dir.mkdir(parents=True, exist_ok=True)
        path = self._log_dir / f"{problem_id}.yaml"
        path.write_text(yaml.safe_dump(log, sort_keys=False, allow_unicode=True, width=1000), encoding="utf-8")
        self.registry.commit([path], f"{problem_id}: powiadomienia")

    def _notes(self, problem_id: str) -> dict[str, Any]:
        path = self._notes_dir / f"{problem_id}.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else None
        return data if isinstance(data, dict) else {}

    def _save_notes(self, problem_id: str, notes: dict[str, Any]) -> Path:
        self._notes_dir.mkdir(parents=True, exist_ok=True)
        path = self._notes_dir / f"{problem_id}.yaml"
        path.write_text(yaml.safe_dump(notes, sort_keys=False, allow_unicode=True, width=1000), encoding="utf-8")
        return path

    def _at(self) -> str:
        return self.registry.now().astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _message(item: Problem, what: str, d: dict[str, Any]) -> str:
    """Zdanie po polsku dla zgłaszającego."""
    head = f"Twoje zgłoszenie {item['id']} „{item['title']}”"
    if what == "accepted":
        return f"{head} zostało przyjęte do realizacji jako zmiana {d['change']}."
    if what == "rejected":
        note = f" {item['rejection_note']}" if item.get("rejection_note") else ""
        return f"{head} zostało odrzucone.{note}"
    if what == "parked":
        when = f" Wrócimy do niego, gdy: {item['return_when']}." if item.get("return_when") else ""
        return f"{head} zostało odłożone.{when}"
    if what == "duplicate":
        return f"{head} to duplikat {item['duplicate_of']} — dalej śledzimy tamto zgłoszenie."
    if what == "released":
        line = "" if d["release"] == "all" else f" (linia {d['release']})"
        return f"Zmiana {d['change']} z Twojego zgłoszenia {item['id']} jest u ludzi{line} od {d['released_at']}."
    if what == "questions":
        return f"{head}: mamy pytania, zanim je ocenimy — odpowiedz, proszę, na kanale, którym przyszło."
    if what == "returned":
        return f"{head} wraca do oceny: zgłosiło je już {d['round']} osób."
    result = IMPACT_TEXT.get(d["outcome"], d["outcome"])
    return f"Ocena skutku zmiany {d['change']} z Twojego zgłoszenia {item['id']}: {result}."


def _words(item: Problem) -> set[str]:
    text = " ".join(str(item.get(k) or "") for k in ("title", "who", "cannot", "impact"))
    return {w.lower() for w in _WORD.findall(text)}


def _number(key: str) -> int:
    tail = key.rsplit("-", 1)[-1]
    return int(tail) if tail.isdigit() else 0
