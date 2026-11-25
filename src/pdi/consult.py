"""DI Team T4 „Ask team” (docs/plan-t4-ask-team.md): konsultacja zespołu przy pozycji skrzynki.

Decydent pyta wybrane osoby o zdanie. Każda wybiera jedną opcję (wynik pozycji albo `talk_live`) i dopisuje zdanie.
Odpowiedzi są ukryte dla wszystkich, także dla decydenta, aż pytanie się zamknie: w terminie, gdy odpowiedzą
wszyscy, albo gdy decydent zamknie je wcześniej. Po zamknięciu wynik to zgodność (`agree`, jedna opcja wśród tych,
którzy odpowiedzieli, bez `talk_live`), rozbieżność (`discuss`) albo brak odpowiedzi (`none`). Zespół doradza;
decyzję podejmuje decydent zwykłą ścieżką skrzynki, a decyzja dostaje `consulted` (kontrakt 0.26.0).

Stan leży w rejestrze: `consultations/<pozycja>.json` i `people.json` (osoby, które logowały się do konsoli przez
suitę: `sub` i nazwa, bez e-maila — DI3). Termin liczy się przy odczycie, bez osobnego procesu.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

TALK_LIVE = "talk_live"
MAX_ASKED = 20
MAX_HOURS = 24 * 7
MAX_REASON = 300
MAX_EFFECTS = 1000
ITEM_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


class ConsultError(ValueError):
    """Pytanie albo odpowiedź, której konsultacja nie przyjmuje (powód po angielsku, jak w konsoli)."""


@dataclass(frozen=True)
class Person:
    sub: str
    name: str


def _iso(at: datetime) -> str:
    return at.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


class Consultations:
    def __init__(self, root: Path, *, now: Callable[[], datetime] = lambda: datetime.now(UTC)) -> None:
        self.dir = root / "consultations"
        self.now = now
        self._lock = threading.Lock()

    def _path(self, item_id: str) -> Path:
        if not ITEM_ID.fullmatch(item_id):
            raise ConsultError("no such item")
        return self.dir / f"{item_id}.json"

    def _load(self, item_id: str) -> dict[str, Any] | None:
        path = self._path(item_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None

    def _closed(self, c: dict[str, Any]) -> bool:
        if c.get("closed_at"):
            return True
        if self.now() >= _parse(c["closes_at"]):
            return True
        return all(a.get("option") for a in c["asked"])

    def ask(
        self, item_id: str, *, decider: Person, asked: list[Person], options: list[str], hours: int
    ) -> dict[str, Any]:
        others = {p.sub: p for p in asked if p.sub != decider.sub}
        if not others:
            raise ConsultError("ask someone other than yourself")
        if len(others) > MAX_ASKED:
            raise ConsultError(f"ask at most {MAX_ASKED} people")
        if not 1 <= hours <= MAX_HOURS:
            raise ConsultError("choose a deadline between 1 hour and 7 days")
        with self._lock:
            old = self._load(item_id)
            if old is not None and not self._closed(old):
                raise ConsultError("this item is already with the team")
            now = self.now()
            c = {
                "item": item_id,
                "decider": {"sub": decider.sub, "name": decider.name},
                "options": list(options),
                "asked": [{"sub": p.sub, "name": p.name, "option": None, "reason": None} for p in others.values()],
                "effects": {},
                "asked_at": _iso(now),
                "closes_at": _iso(now + timedelta(hours=hours)),
                "closed_at": None,
            }
            _write_json(self._path(item_id), c)
            return c

    def answer(self, item_id: str, person: Person, *, option: str, reason: str) -> None:
        reason = " ".join(reason.split())
        with self._lock:
            c = self._load(item_id)
            if c is None:
                raise ConsultError("this item is not with the team")
            if self._closed(c):
                raise ConsultError("the question is closed")
            mine = next((a for a in c["asked"] if a["sub"] == person.sub), None)
            if mine is None:
                raise ConsultError("you were not asked about this item")
            if option not in (*c["options"], TALK_LIVE):
                raise ConsultError("choose one of the item's options")
            if not reason or len(reason) > MAX_REASON:
                raise ConsultError(f"give one sentence as the reason (up to {MAX_REASON} characters)")
            mine.update({"option": option, "reason": reason, "name": person.name})
            _write_json(self._path(item_id), c)

    def close(self, item_id: str) -> None:
        with self._lock:
            c = self._load(item_id)
            if c is None:
                raise ConsultError("this item is not with the team")
            if not c.get("closed_at"):
                c["closed_at"] = _iso(self.now())
                _write_json(self._path(item_id), c)

    def add_effects(self, item_id: str, option: str, text: str) -> None:
        """Agent dopisuje, co się stanie przy opcji (plan, koszt, testy); nie głosuje."""
        text = " ".join(text.split())
        with self._lock:
            c = self._load(item_id)
            if c is None:
                raise ConsultError("this item is not with the team")
            if option not in (*c["options"], TALK_LIVE):
                raise ConsultError("choose one of the item's options")
            if not text or len(text) > MAX_EFFECTS:
                raise ConsultError(f"describe the effects in up to {MAX_EFFECTS} characters")
            c["effects"][option] = text
            _write_json(self._path(item_id), c)

    @staticmethod
    def _result(c: dict[str, Any]) -> dict[str, Any]:
        chosen = [a["option"] for a in c["asked"] if a.get("option")]
        if not chosen:
            return {"kind": "none"}
        if TALK_LIVE in chosen or len(set(chosen)) > 1:
            return {"kind": "discuss"}
        return {"kind": "agree", "option": chosen[0]}

    def view(self, item_id: str, viewer_sub: str) -> dict[str, Any] | None:
        """Co widzi osoba `viewer_sub`: odpowiedzi innych dopiero po zamknięciu; własną zawsze."""
        try:
            c = self._load(item_id)
        except ConsultError:
            return None
        if c is None:
            return None
        closed = self._closed(c)
        mine = next((a for a in c["asked"] if a["sub"] == viewer_sub), None)
        view: dict[str, Any] = {
            "status": "closed" if closed else "open",
            "decider": c["decider"]["name"],
            "decider_sub": c["decider"]["sub"],
            "options": c["options"],
            "asked": len(c["asked"]),
            "answered": sum(1 for a in c["asked"] if a.get("option")),
            "asked_names": [a["name"] for a in c["asked"]],
            "closes_at": c["closes_at"],
            "effects": dict(c.get("effects") or {}),
            "is_asked": mine is not None,
            "mine": {"option": mine["option"], "reason": mine["reason"]} if mine and mine.get("option") else None,
        }
        if closed:
            view["result"] = self._result(c)
            view["answers"] = [{"name": a["name"], "option": a["option"], "reason": a["reason"]} for a in c["asked"]]
        return view

    def consulted(self, item_id: str) -> list[dict[str, Any]] | None:
        """`consulted` do decyzji (kontrakt 0.26.0): wszyscy zapytani, `None` w polach bez odpowiedzi."""
        c = self._load(item_id)
        if c is None:
            return None
        return [
            {"person_id": a["sub"], "name": a["name"], "option": a.get("option"), "reason": a.get("reason")}
            for a in c["asked"]
        ]

    def asked_of(self, viewer_sub: str) -> list[str]:
        """Pozycje z otwartym pytaniem do tej osoby, bez jej odpowiedzi („Asked of you”)."""
        out = []
        for path in sorted(self.dir.glob("*.json")) if self.dir.exists() else []:
            view = self.view(path.stem, viewer_sub)
            if view and view["status"] == "open" and view["is_asked"] and view["mine"] is None:
                out.append(path.stem)
        return out


class People:
    """Osoby, które logowały się do tej konsoli przez suitę — lista do wyboru w „Ask team”."""

    def __init__(self, root: Path, *, now: Callable[[], datetime] = lambda: datetime.now(UTC)) -> None:
        self.path = root / "people.json"
        self.now = now
        self._lock = threading.Lock()

    def _load(self) -> dict[str, dict[str, str]]:
        if not self.path.exists():
            return {}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}

    def seen(self, person: Person) -> None:
        with self._lock:
            people = self._load()
            people[person.sub] = {"name": person.name[:200], "last_sign_in": _iso(self.now())}
            _write_json(self.path, people)

    def all(self) -> list[Person]:
        return sorted((Person(sub=s, name=p["name"]) for s, p in self._load().items()), key=lambda p: p.name)
