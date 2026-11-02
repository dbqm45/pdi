"""Uruchomienie fazy tf po decyzji na bramce (F4): `workflow_dispatch` szablonu fazy przez API GitHuba.

Na produkcji pdi nie uruchamia agentów u siebie (dokument 13, R4): stan jest w pdi, wykonanie w GitHub Actions.
Jedyny wyjątek to `PDI_DISPATCH=local` (decyzja DL1, rozwój i próby): wtedy pdi wykonuje te same kroki co szablon
fazy w lokalnym klonie repo produktu (`PDI_DISPATCH_CHECKOUT`, `pdi.dispatch_local`). Bez `PDI_DISPATCH` zachowanie
jest takie jak przed L2. Błąd nie cofa decyzji — zapisuje się w stanie zmiany, a `retry_dispatch` ponawia. Token
nigdy nie trafia do wyniku.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pdi import dispatch_local

Post = Callable[[str, dict[str, str], bytes], int]
API = "https://api.github.com"
TIMEOUT_SECONDS = 10
_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_WORKFLOW = re.compile(r"^[A-Za-z0-9_.-]+\.ya?ml$")
_REF = re.compile(r"^[A-Za-z0-9_./-]{1,200}$")
# Z1: wejścia z decyzjami zmiany; szablon sprzed Z1 ich nie zna (GitHub odpowiada wtedy 422) i dostaje fazę bez nich.
Z1_INPUTS = ("decision_text", "answers", "decisions")
# Górna granica długości jednego wejścia z JSON-em (łączny limit wejść workflow_dispatch jest większy, §4 planu Z1).
INPUT_MAX = 20_000


@dataclass(frozen=True)
class DispatchConfig:
    repo: str | None
    workflow: str = "sdlc-phase.yml"
    ref: str = "main"
    token: str | None = field(default=None, repr=False)
    budget_usd: str | None = None
    # PDI_DISPATCH: brak — workflow_dispatch (Actions); "local" — przebieg w klonie PDI_DISPATCH_CHECKOUT (DL1).
    mode: str | None = None
    checkout: str | None = None

    @property
    def local(self) -> bool:
        return self.mode == "local"

    @classmethod
    def from_env(cls) -> DispatchConfig:
        return cls(
            repo=os.environ.get("PDI_DISPATCH_REPO") or None,
            workflow=os.environ.get("PDI_DISPATCH_WORKFLOW") or "sdlc-phase.yml",
            ref=os.environ.get("PDI_DISPATCH_REF") or "main",
            token=os.environ.get("PDI_GITHUB_TOKEN") or None,
            budget_usd=os.environ.get("PDI_PHASE_BUDGET_USD") or None,
            mode=os.environ.get("PDI_DISPATCH") or None,
            checkout=os.environ.get("PDI_DISPATCH_CHECKOUT") or None,
        )


def dispatch_phase(
    config: DispatchConfig,
    *,
    change: str,
    phase: str,
    gate: str,
    outcome: str,
    decision: str,
    rework: bool,
    at: str,
    post: Post | None = None,
    source: str | None = None,
    problem: str | None = None,
    decision_text: str | None = None,
    answers: list[dict[str, str]] | None = None,
    decisions: list[dict[str, Any]] | None = None,
    runs_dir: Path | None = None,
    spawn: dispatch_local.Spawn | None = None,
    run: dispatch_local.Run | None = None,
) -> dict[str, Any]:
    """Uruchamia fazę `phase` dla `change`; wynik `{"status": sent | skipped | failed, …}` do zapisu w stanie.

    `source` (PRB) i `problem` (JSON zgłoszenia) idą tylko przy przyjęciu do budowy (F3, faza `intent`); szablon fazy
    bez tych wejść ich nie dostaje. `decision_text`, `answers` (odpowiedzi na pytania bramki) i `decisions` (decyzje
    zmiany z rejestru) idą tylko, gdy są (Z1); szablon sprzed Z1 dostaje fazę bez nich, z ostrzeżeniem. W trybie
    lokalnym wynik ma `mode: local` i `status: running | failed`, a log przebiegu trafia do `runs_dir`
    (`$PDI_REGISTRY_PATH/runs`).
    """
    result: dict[str, Any] = {"status": "failed", "phase": phase, "rework": rework, "at": at}
    if config.mode and not config.local:
        return {**result, "error": f"PDI_DISPATCH: dozwolone tylko „local” (albo brak), jest „{config.mode[:40]}”."}
    if config.local:
        if runs_dir is None:
            return {**result, "mode": "local", "error": "Brak katalogu przebiegów (runs) — błąd konfiguracji pdi."}
        return dispatch_local.start(
            runs_dir=runs_dir,
            checkout=config.checkout,
            ref=config.ref,
            budget_usd=config.budget_usd,
            change=change,
            phase=phase,
            gate=gate,
            outcome=outcome,
            decision=decision,
            rework=rework,
            at=at,
            source=source,
            problem=problem,
            decision_text=decision_text,
            answers=answers,
            decisions=decisions,
            run=run,
            spawn=spawn,
        )
    if not config.repo:
        return {**result, "status": "skipped", "error": "Brak PDI_DISPATCH_REPO — faza nie została uruchomiona."}
    result.update(repo=config.repo, workflow=config.workflow)
    if not _REPO.match(config.repo) or ".." in config.repo:
        return {**result, "error": "PDI_DISPATCH_REPO musi mieć postać właściciel/repo."}
    if not _WORKFLOW.match(config.workflow) or ".." in config.workflow:
        return {**result, "error": "PDI_DISPATCH_WORKFLOW musi być nazwą pliku .yml albo .yaml."}
    if not _REF.match(config.ref):
        return {**result, "error": "PDI_DISPATCH_REF nie jest poprawną nazwą gałęzi."}
    if not config.token:
        return {**result, "error": "Brak PDI_GITHUB_TOKEN — faza nie została uruchomiona."}

    inputs = {
        "change": change,
        "phase": phase,
        "gate": gate,
        "outcome": outcome,
        "decision": decision,
        "rework": "true" if rework else "false",
    }
    if config.budget_usd:
        inputs["budget_usd"] = config.budget_usd
    if source:
        inputs["source"] = source
    if problem:
        inputs["problem"] = problem
    if decision_text:
        inputs["decision_text"] = decision_text[: dispatch_local.DECISION_TEXT_MAX]
    if answers:
        inputs["answers"] = _capped(answers)
    if decisions:
        inputs["decisions"] = _capped(decisions)
    url = f"{API}/repos/{config.repo}/actions/workflows/{config.workflow}/dispatches"
    headers = {
        "authorization": f"Bearer {config.token}",
        "accept": "application/vnd.github+json",
        "x-github-api-version": "2022-11-28",
        "content-type": "application/json",
    }
    try:
        status = _send(post or _post, url, headers, config.ref, inputs)
        if status == 422 and set(Z1_INPUTS) & set(inputs):
            older = {k: v for k, v in inputs.items() if k not in Z1_INPUTS}
            if 200 <= _send(post or _post, url, headers, config.ref, older) < 300:
                return {
                    **result,
                    "status": "sent",
                    "warning": f"{config.workflow} w {config.repo} nie zna wejść {', '.join(Z1_INPUTS)} (szablon "
                    "sprzed Z1) — faza ruszyła bez decyzji zmiany; zaktualizuj szablon: phase_run.py workflow "
                    "install --force.",
                }
    except OSError:
        # Treść wyjątku może zawierać nagłówki albo adres z tokenem — nie przepisujemy jej.
        return {**result, "error": "Nie udało się nawiązać połączenia z GitHubem."}
    if not 200 <= status < 300:
        return {**result, "error": f"GitHub odpowiedział {status} na workflow_dispatch."}
    return {**result, "status": "sent"}


def _send(post: Post, url: str, headers: dict[str, str], ref: str, inputs: dict[str, str]) -> int:
    return post(url, headers, json.dumps({"ref": ref, "inputs": inputs}).encode())


def _capped(items: list[dict[str, Any]]) -> str:
    """JSON listy nie dłuższy niż INPUT_MAX: przy nadmiarze odpadają najstarsze pozycje."""
    kept = list(items)
    text = json.dumps(kept, ensure_ascii=False)
    while len(text) > INPUT_MAX and kept:
        kept = kept[1:]
        text = json.dumps(kept, ensure_ascii=False)
    return text


def _post(url: str, headers: dict[str, str], body: bytes) -> int:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")  # noqa: S310 — stały https API
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310
            return int(response.status)
    except urllib.error.HTTPError as e:
        return int(e.code)
