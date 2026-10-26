"""Uruchomienie fazy tf po decyzji na bramce (F4): `workflow_dispatch` szablonu fazy przez API GitHuba.

pdi nie uruchamia agentów u siebie (dokument 13, R4): stan jest w pdi, wykonanie w GitHub Actions. Błąd nie cofa
decyzji — zapisuje się w stanie zmiany, a `retry_dispatch` ponawia. Token nigdy nie trafia do wyniku.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

Post = Callable[[str, dict[str, str], bytes], int]
API = "https://api.github.com"
TIMEOUT_SECONDS = 10
_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_WORKFLOW = re.compile(r"^[A-Za-z0-9_.-]+\.ya?ml$")
_REF = re.compile(r"^[A-Za-z0-9_./-]{1,200}$")


@dataclass(frozen=True)
class DispatchConfig:
    repo: str | None
    workflow: str = "sdlc-phase.yml"
    ref: str = "main"
    token: str | None = field(default=None, repr=False)
    budget_usd: str | None = None

    @classmethod
    def from_env(cls) -> DispatchConfig:
        return cls(
            repo=os.environ.get("PDI_DISPATCH_REPO") or None,
            workflow=os.environ.get("PDI_DISPATCH_WORKFLOW") or "sdlc-phase.yml",
            ref=os.environ.get("PDI_DISPATCH_REF") or "main",
            token=os.environ.get("PDI_GITHUB_TOKEN") or None,
            budget_usd=os.environ.get("PDI_PHASE_BUDGET_USD") or None,
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
) -> dict[str, Any]:
    """Uruchamia fazę `phase` dla `change`; wynik `{"status": sent | skipped | failed, …}` do zapisu w stanie."""
    result: dict[str, Any] = {"status": "failed", "phase": phase, "rework": rework, "at": at}
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
    url = f"{API}/repos/{config.repo}/actions/workflows/{config.workflow}/dispatches"
    headers = {
        "authorization": f"Bearer {config.token}",
        "accept": "application/vnd.github+json",
        "x-github-api-version": "2022-11-28",
        "content-type": "application/json",
    }
    body = json.dumps({"ref": config.ref, "inputs": inputs}).encode()
    try:
        status = (post or _post)(url, headers, body)
    except OSError:
        # Treść wyjątku może zawierać nagłówki albo adres z tokenem — nie przepisujemy jej.
        return {**result, "error": "Nie udało się nawiązać połączenia z GitHubem."}
    if not 200 <= status < 300:
        return {**result, "error": f"GitHub odpowiedział {status} na workflow_dispatch."}
    return {**result, "status": "sent"}


def _post(url: str, headers: dict[str, str], body: bytes) -> int:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")  # noqa: S310 — stały https API
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310
            return int(response.status)
    except urllib.error.HTTPError as e:
        return int(e.code)
