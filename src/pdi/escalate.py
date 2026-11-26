"""DI Team T7 „Escalate” (docs/plan-t7-escalate.md) i OM2: decyzję o sprawie przejmuje osoba, do której eskalowano.

Inaczej niż „Ask team” (zespół doradza) eskalacja zmienia decydenta tej jednej sprawy: od niej decyduje tylko adresat,
dopóki nie odda sprawy z notatką. Adresat to osoba z suity z rolą `editor` albo `admin` w DI Decision, która logowała
się do konsoli (`people.json`); przy typach chronionych (triaż, ocena skutku, wydanie B5) tylko `admin`. Termin sprawy
z OM1 się nie zmienia.

Zapis: `escalations/<pozycja>.json` w rejestrze (bieżąca eskalacja, wcześniejsze w `history`). Decyzja dostaje pole
`escalation` (kontrakt 0.27.0) z ostatniej eskalacji, także oddanej.
"""

from __future__ import annotations

import json
import re
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pdi.consult import People, Person, _write_json

ITEM_ID = re.compile(r"[A-Za-z0-9._-]{1,128}")
MAX_TEXT = 1000


class EscalationError(ValueError):
    """Eskalacja niedozwolona albo niemożliwa; komunikat dla osoby w konsoli."""


def _iso(at: datetime) -> str:
    return at.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def protected(item: dict[str, Any]) -> bool:
    """Typy chronione z OM1 (§2): triaż, ocena skutku, wydanie na PROD (B5) — eskalacja tylko do roli admin."""
    return item.get("kind") in ("problem", "impact_review") or (item.get("kind") == "gate" and item.get("gate") == "B5")


def _text(value: str) -> str:
    return " ".join(str(value or "").split())


class Escalations:
    def __init__(self, root: Path, *, now: Callable[[], datetime] = lambda: datetime.now(UTC)) -> None:
        self.dir = root / "escalations"
        self.now = now
        self._lock = threading.Lock()

    def _path(self, item_id: str) -> Path:
        if not ITEM_ID.fullmatch(item_id):
            raise EscalationError("no such item")
        return self.dir / f"{item_id}.json"

    def _load(self, item_id: str) -> dict[str, Any] | None:
        try:
            path = self._path(item_id)
        except EscalationError:
            return None
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None

    def escalate(
        self, item: dict[str, Any], *, by: Person, to: Person, reason: str, people: People, question: str = ""
    ) -> dict[str, Any]:
        reason, question = _text(reason), _text(question)
        if to.sub == by.sub:
            raise EscalationError("escalate to someone else, not yourself")
        target = people.get(to.sub)
        if target is None or not target.get("decides"):
            raise EscalationError("escalate only to a person with the editor or admin role who signed in here")
        if protected(item) and not target.get("admin"):
            raise EscalationError("this is a protected decision: escalate only to a person with the admin role")
        if not reason or len(reason) > MAX_TEXT:
            raise EscalationError(f"give the reason (up to {MAX_TEXT} characters)")
        if len(question) > MAX_TEXT:
            raise EscalationError(f"the question is too long (up to {MAX_TEXT} characters)")
        with self._lock:
            old = self._load(item["id"])
            if old is not None and not old.get("returned_at"):
                raise EscalationError("this item is already escalated")
            e: dict[str, Any] = {
                "item": item["id"],
                "by": {"sub": by.sub, "name": by.name},
                "to": {"sub": to.sub, "name": target.get("name") or to.name},
                "reason": reason,
                "at": _iso(self.now()),
            }
            if question:
                e["question"] = question
            if old is not None:
                e["history"] = [*old.pop("history", []), old]
            _write_json(self._path(item["id"]), e)
            return e

    def give_back(self, item_id: str, person: Person, *, note: str) -> None:
        note = _text(note)
        if not note or len(note) > MAX_TEXT:
            raise EscalationError(f"say why you give it back (up to {MAX_TEXT} characters)")
        with self._lock:
            e = self._load(item_id)
            if e is None or e.get("returned_at"):
                raise EscalationError("this item is not escalated")
            if e["to"]["sub"] != person.sub:
                raise EscalationError("only the person it was escalated to can give it back")
            e["returned_at"] = _iso(self.now())
            e["return_note"] = note
            _write_json(self._path(item_id), e)

    def record_notice(self, item_id: str, notice: dict[str, Any]) -> None:
        """Wynik wiadomości do adresata (DI Channels): `status`, `at`, `delivered`, `error`."""
        with self._lock:
            e = self._load(item_id)
            if e is None:
                return
            e["notice"] = {k: notice[k] for k in ("status", "at", "delivered", "error") if k in notice}
            _write_json(self._path(item_id), e)

    def view(self, item_id: str) -> dict[str, Any] | None:
        e = self._load(item_id)
        if e is None:
            return None
        return {k: v for k, v in e.items() if k != "history"}

    def holder(self, item_id: str) -> str | None:
        """`sub` osoby, która jedyna może teraz zdecydować; None, gdy sprawa nie jest eskalowana (albo oddana)."""
        e = self._load(item_id)
        return None if e is None or e.get("returned_at") else str(e["to"]["sub"])

    def escalated_to(self, sub: str) -> list[str]:
        out = []
        for path in sorted(self.dir.glob("*.json")) if self.dir.exists() else []:
            if self.holder(path.stem) == sub:
                out.append(path.stem)
        return out

    def field(self, item_id: str) -> dict[str, Any] | None:
        """`escalation` do decyzji (kontrakt 0.27.0)."""
        e = self._load(item_id)
        if e is None:
            return None
        out = {"by_id": e["by"]["sub"], "by_name": e["by"]["name"], "to_id": e["to"]["sub"], "to_name": e["to"]["name"],
               "reason": e["reason"], "at": e["at"]}  # fmt: skip
        for key in ("returned_at", "return_note"):
            if e.get(key):
                out[key] = e[key]
        return out
