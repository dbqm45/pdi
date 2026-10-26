"""Mały rejestr zgłoszeń (PRB) i powiadomienia zgłaszającego (F5): pliki `problems/<PRB>.yaml` w katalogu rejestru.

Zgłoszenie ma kształt `contract/problem.schema.json` (sprawdzany przy każdym zapisie); pdi nadaje `id`, `reported_at`
i `status`. Triaż zapisuje decyzję `kind: triage` i ustawia wynik w zgłoszeniu. Zgłaszający dostaje podpisane
`problem.notification` po triażu, po wydaniu zmiany, z której wyszło zgłoszenie, i po ocenie skutku tej zmiany
(`pdi.notify.notify_reporter`); dziennik wysyłek w `notifications/<PRB>.yaml`. Pełny intake zgłoszeń to F3.
Plan: docs/plan-f5-powiadomienia.md.
"""

from __future__ import annotations

import re
from datetime import UTC
from pathlib import Path
from typing import Any, TypeAlias

import yaml

from pdi import contract
from pdi.dispatch import Post
from pdi.notify import ReporterNotifyConfig, notify_reporter
from pdi.registry import Decision, InvalidDecision, Registry

Problem: TypeAlias = dict[str, Any]

OUTCOMES = ("accepted", "rejected", "parked", "duplicate")
SET_BY_PDI = ("id", "reported_at", "status", "triage_decision", "change")
# Pole wymagane przez wynik triażu (pozostałe są opcjonalne).
REQUIRED_FOR = {"accepted": "change", "duplicate": "duplicate_of"}
IMPACT_TEXT = {"met": "cel osiągnięty", "not_met": "cel nieosiągnięty", "unknown": "nie wiadomo, czy cel osiągnięto"}
_KEY = re.compile(contract.settings()["key_pattern"])


class InvalidProblem(ValueError):
    """Szkic zgłoszenia niezgodny z kontraktem."""


class ProblemNotFound(LookupError):
    """W rejestrze nie ma zgłoszenia o tym kluczu."""


class ProblemStore:
    def __init__(
        self, registry: Registry, *, notify: ReporterNotifyConfig | None = None, post: Post | None = None
    ) -> None:
        self.registry = registry
        self._dir = registry.root / "problems"
        self._log_dir = registry.root / "notifications"
        self._notify = notify or ReporterNotifyConfig(url=None)
        self._post = post
        self._prefix = contract.settings()["prefixes"]["problem"]

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
        return {**item, **({"warning": warning} if warning else {})}

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
        updated = {**item, **{k: v for k, v in given.items() if v}, "status": outcome}
        self._check({**updated, "triage_decision": "DEC-1"}, InvalidDecision)  # zanim decyzja trafi do rejestru

        links = {**(draft.get("links") or {}), "prb": problem_id}
        if change:
            links["chg"] = change
        tags = [*(draft.get("tags") or []), f"problem:{outcome}"]
        decision = self.registry.record({**draft, "kind": "triage", "links": links, "tags": list(dict.fromkeys(tags))})
        updated["triage_decision"] = decision["id"]
        path = self._write(updated, overwrite=True)
        warning = self.registry.commit([path], f"{problem_id}: triaż {outcome} ({decision['id']})")
        notification = self._send(updated, outcome, change=updated.get("change"), decision=decision["id"])
        return {
            "problem": updated,
            "decision": decision,
            "notification": notification,
            **({"warning": warning} if warning else {}),
        }

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
        suffix = f"-{details['release']}" if what == "released" else ""
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
    result = IMPACT_TEXT.get(d["outcome"], d["outcome"])
    return f"Ocena skutku zmiany {d['change']} z Twojego zgłoszenia {item['id']}: {result}."


def _number(key: str) -> int:
    tail = key.rsplit("-", 1)[-1]
    return int(tail) if tail.isdigit() else 0
