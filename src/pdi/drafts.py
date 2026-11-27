"""Zapis decyzji tylko po zatwierdzeniu szkicu w konsoli (docs/plan-zapis-decyzji-po-zatwierdzeniu.md).

Zgoda związana z argumentami (tf, `sec-llm-security/references/agent-design-patterns.md` §4): agent przez MCP
zapisuje szkic (`present_decision_draft`) w `decision-drafts/DRF-n.yaml` razem z SHA-256 jego kanonicznej treści;
człowiek z prawem decyzji widzi w konsoli surową treść i zatwierdza albo odrzuca z powodem; `record_decision` zapisuje
w rejestrze dokładnie zatwierdzoną treść — przy zgodnym skrócie, najwyżej godzinę po zatwierdzeniu i tylko raz.
Szkic można zatwierdzić do 7 dni od wystawienia. Inna treść to nowy szkic.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from pdi.registry import Decision, Registry

DIR = "decision-drafts"
APPROVE_WITHIN = timedelta(days=7)
USE_WITHIN = timedelta(hours=1)
_ID = re.compile(r"^DRF-([0-9]{1,9})$")
_SHA = re.compile(r"^[0-9a-f]{64}$")
MAX_REASON = 1000


class DraftRefused(ValueError):
    """Szkicu nie da się teraz zatwierdzić, odrzucić ani zapisać; powód w komunikacie (bez sekretów)."""


class DraftNotFound(LookupError):
    """Nie ma takiego szkicu."""


def digest(decision: Decision, supersedes: str | None) -> str:
    """SHA-256 kanonicznej treści szkicu: posortowany JSON decyzji i decyzji zastępowanej."""
    canonical = json.dumps(
        {"decision": decision, "supersedes": supersedes}, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _stamp(at: datetime) -> str:
    return at.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _at(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


class DecisionDrafts:
    def __init__(self, registry: Registry) -> None:
        self.registry = registry
        self.dir = registry.root / DIR

    # --- wystawienie i odczyt ---

    def present(
        self, decision: Decision, *, supersedes: str | None = None, presented_by: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """Sprawdza szkic z kontraktem (bez zapisu do rejestru) i odkłada go do zatwierdzenia jako DRF-n."""
        self.registry.check(decision, supersedes=supersedes)
        self.dir.mkdir(parents=True, exist_ok=True)
        entry: dict[str, Any] = {
            "status": "pending",
            "sha256": digest(decision, supersedes),
            "decision": decision,
            "supersedes": supersedes,
            "presented_at": _stamp(self.registry.now()),
            "presented_by": presented_by,
        }
        for _ in range(20):
            entry["id"] = f"DRF-{self._next()}"
            try:
                fd = os.open(self._path(entry["id"]), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError:
                continue
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(yaml.safe_dump(entry, allow_unicode=True, sort_keys=False))
            return entry
        raise RuntimeError("Nie udało się nadać numeru szkicu — równoległe zapisy; ponów.")

    def get(self, draft_id: str) -> dict[str, Any]:
        if not _ID.match(draft_id or "") or not self._path(draft_id).is_file():
            raise DraftNotFound(f"Nie ma szkicu {draft_id}.")
        data = yaml.safe_load(self._path(draft_id).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise DraftNotFound(f"Nie ma szkicu {draft_id}.")
        return data

    def all(self) -> list[dict[str, Any]]:
        """Szkice od najnowszego."""
        if not self.dir.is_dir():
            return []
        ids = sorted((int(m.group(1)) for p in self.dir.glob("DRF-*.yaml") if (m := _ID.match(p.stem))), reverse=True)
        return [self.get(f"DRF-{n}") for n in ids]

    # --- decyzja człowieka ---

    def approve(self, draft_id: str, sha256: str, *, by: dict[str, str]) -> dict[str, Any]:
        entry = self._pending(draft_id, sha256)
        entry.update(status="approved", approved_by=by, approved_at=_stamp(self.registry.now()))
        self._save(entry)
        return entry

    def reject(self, draft_id: str, sha256: str, *, by: dict[str, str], reason: str) -> dict[str, Any]:
        reason = " ".join(str(reason or "").split())[:MAX_REASON]
        if not reason:
            raise DraftRefused("Podaj powód odrzucenia — wróci do agenta, żeby poprawił szkic.")
        entry = self._pending(draft_id, sha256)
        entry.update(status="rejected", rejected_by=by, rejected_at=_stamp(self.registry.now()), rejected_reason=reason)
        self._save(entry)
        return entry

    # --- zapis w rejestrze ---

    def record(self, draft_id: str, sha256: str) -> Decision:
        """Zapisuje w rejestrze zatwierdzoną treść szkicu (raz, przy zgodnym skrócie, do godziny od zgody)."""
        entry = self.get(draft_id)
        self._same(entry, sha256)
        status = entry.get("status")
        if status == "pending":
            raise DraftRefused(f"Szkic {draft_id} czeka na zatwierdzenie przez człowieka w konsoli pdi.")
        if status == "rejected":
            raise DraftRefused(f"Szkic {draft_id} odrzucony: {entry.get('rejected_reason')} Przygotuj nowy szkic.")
        if status == "recorded":
            raise DraftRefused(f"Szkic {draft_id} już zapisany jako {entry.get('decision_id')}.")
        if self.registry.now() - _at(str(entry["approved_at"])) > USE_WITHIN:
            raise DraftRefused(f"Zgoda na szkic {draft_id} wygasła (ważna godzinę) — wystaw szkic ponownie.")
        lock = self._path(draft_id).with_suffix(".lock")
        try:
            os.close(os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600))
        except FileExistsError as e:
            raise DraftRefused(f"Szkic {draft_id} już zapisany.") from e
        try:
            decision: Decision = dict(entry["decision"])
            approver = entry.get("approved_by") or {}
            if "decided_by" not in decision and approver.get("name"):
                decision["decided_by"] = approver["name"]
                if approver.get("sub"):
                    decision["decided_by_id"] = approver["sub"]
            supersedes = entry.get("supersedes")
            saved = self.registry.supersede(supersedes, decision) if supersedes else self.registry.record(decision)
        except Exception:
            lock.unlink()
            raise
        entry.update(status="recorded", decision_id=saved["id"], recorded_at=_stamp(self.registry.now()))
        self._save(entry)
        return saved

    # --- pomocnicze ---

    def _pending(self, draft_id: str, sha256: str) -> dict[str, Any]:
        entry = self.get(draft_id)
        self._same(entry, sha256)
        if entry.get("status") == "rejected":
            raise DraftRefused(f"Szkic {draft_id} już odrzucony.")
        if entry.get("status") != "pending":
            raise DraftRefused(f"Szkic {draft_id} już rozstrzygnięty ({entry.get('status')}).")
        if self.registry.now() - _at(str(entry["presented_at"])) > APPROVE_WITHIN:
            raise DraftRefused(f"Szkic {draft_id} wygasł (7 dni) — agent musi wystawić go ponownie.")
        return entry

    @staticmethod
    def _same(entry: dict[str, Any], sha256: str) -> None:
        if not _SHA.match(sha256 or "") or sha256 != entry.get("sha256"):
            raise DraftRefused(f"Inny skrót treści niż szkicu {entry.get('id')} — zgoda dotyczy tylko tej treści.")

    def _next(self) -> int:
        nums = [int(m.group(1)) for p in self.dir.glob("DRF-*.yaml") if (m := _ID.match(p.stem))]
        return max(nums, default=0) + 1

    def _path(self, draft_id: str) -> Path:
        return self.dir / f"{draft_id}.yaml"

    def _save(self, entry: dict[str, Any]) -> None:
        tmp = self._path(entry["id"]).with_suffix(".tmp")
        tmp.write_text(yaml.safe_dump(entry, allow_unicode=True, sort_keys=False), encoding="utf-8")
        with contextlib.suppress(OSError):
            os.chmod(tmp, 0o600)
        tmp.replace(self._path(entry["id"]))
