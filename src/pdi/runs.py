"""Przebiegi agentów (DI Team T1, kontrakt 0.15.0): pliki `agent-runs/<run>.yaml` w katalogu rejestru.

Fabryka (tf) zgłasza każdy przebieg trzema zdarzeniami z tym samym `run`: `run.started` (kto uruchomił, jak, który
agent), `run.progress` (co robi teraz, koszt) i `run.finished` (wynik, koszt, czas, stan przeglądu PR). Także przebiegi
spoza pdi, np. sesję uruchomioną ręcznie w terminalu, więc przebieg nie musi mieć zmiany (`change`).

To widok dla tablicy „Now”, nie źródło prawdy o zmianie: stan zmiany i bramki zostają w `pdi.changes`. Zdarzenia
mogą przyjść w innej kolejności (postęp przed startem): każde uzupełnia ten sam plik, a znany już `id` zdarzenia jest
duplikatem. Inny katalog niż `runs/`, w którym lokalne uruchomienie fazy (`pdi.dispatch_local`) trzyma logi.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, TypeAlias

import yaml

from pdi.registry import Registry

Run: TypeAlias = dict[str, Any]

EVENT_TYPES = ("run.started", "run.progress", "run.finished")
# Pola, które przebieg przejmuje z treści zdarzenia (ostatnia wartość wygrywa).
_FROM_STARTED = ("change", "task", "phase", "slice", "started_by", "trigger", "agent", "repo", "budget_usd", "url")
_FROM_PROGRESS = ("change", "task", "phase", "slice", "started_by", "activity", "cost_usd", "budget_usd", "url")
_FROM_FINISHED = ("change", "task", "phase", "slice", "started_by", "cost_usd", "budget_usd", "duration_s", "url")
_PROGRESS_STATE = {"started": "running", "in_progress": "running", "waiting_gate": "waiting_gate", "done": "done"}
_PROGRESS_STATE["failed"] = "failed"
SEEN_EVENTS_KEPT = 50
# ID przebiegu staje się nazwą pliku: te same znaki co w kontrakcie, bez „..”.
_RUN_ID = re.compile(r"^(?!.*\.\.)[A-Za-z0-9._-]{1,128}$")


class RunStore:
    def __init__(self, registry: Registry) -> None:
        self._dir = registry.root / "agent-runs"

    def path(self, run_id: str) -> Path:
        if not _RUN_ID.match(run_id):
            raise ValueError(f"run: „{run_id}” nie jest identyfikatorem przebiegu.")
        return self._dir / f"{run_id}.yaml"

    def get(self, run_id: str) -> Run | None:
        path = self.path(run_id)
        if not path.is_file():
            return None
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None

    def list(self, *, status: str | None = None) -> list[Run]:
        """Przebiegi od ostatnio zmienionego; `status`: `running`, `waiting_gate`, `done`, `failed`, `cancelled`."""
        if not self._dir.is_dir():
            return []
        runs = [r for p in self._dir.glob("*.yaml") if (r := self.get(p.stem)) is not None]
        if status is not None:
            runs = [r for r in runs if r.get("status") == status]
        return sorted(runs, key=lambda r: str(r.get("updated_at", "")), reverse=True)

    def apply(self, event: dict[str, Any]) -> tuple[str, Run, Path]:
        """Dopisuje zdarzenie przebiegu; zwraca (`recorded` albo `duplicate`, przebieg, ścieżka pliku).

        Przebieg bez `run` (postęp fazy sprzed 0.15.0) nie ma pliku — to rozstrzyga wywołujący.
        """
        payload = event["payload"]
        run_id = str(payload["run"])
        run: Run = self.get(run_id) or {"run": run_id, "status": "running", "seen_events": []}
        path = self.path(run_id)
        if event["id"] in run.get("seen_events", []):
            return "duplicate", run, path
        at = event["occurred_at"]
        if event["type"] == "run.started":
            _take(run, payload, _FROM_STARTED)
            run["started_at"] = at
            run.setdefault("source", event["source"])
        elif event["type"] == "run.progress":
            _take(run, payload, _FROM_PROGRESS)
            # Postęp nie cofa przebiegu, który już się skończył (zdarzenia mogą przyjść w innej kolejności).
            if "finished_at" not in run:
                run["status"] = _PROGRESS_STATE[payload["status"]]
        else:
            _take(run, payload, _FROM_FINISHED)
            run["status"] = payload["outcome"]
            run["finished_at"] = at
            if "message" in payload:
                run["result"] = payload["message"]
            if "review" in payload:
                run["review"] = payload["review"]
        run["updated_at"] = max(str(run.get("updated_at", "")), at)
        run["seen_events"] = [*run.get("seen_events", []), event["id"]][-SEEN_EVENTS_KEPT:]
        self._dir.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(run, allow_unicode=True, sort_keys=False), encoding="utf-8")
        return "recorded", run, path


def _take(run: Run, payload: dict[str, Any], fields: tuple[str, ...]) -> None:
    for key in fields:
        if key in payload:
            run[key] = payload[key]
