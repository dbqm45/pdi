"""Stan PR-a fazy przed zatwierdzeniem bramki (PRB-2).

Zatwierdzona bramka uruchamia następną fazę od aktualnego `main`, więc PR poprzedniej fazy musi być już zmergowany.
Stan czyta `gh pr view` (tryb lokalny, logowanie `gh`) albo API GitHuba z `PDI_GITHUB_TOKEN`. Gdy nie da się go
sprawdzić, wynik to `unknown` z powodem — skrzynka przepuszcza wtedy decyzję z ostrzeżeniem.
"""

import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from pdi import dispatch_local
from pdi.dispatch import DispatchConfig

# Wynik: {"state": merged | open | closed | unknown, "reason"?: str}
Check = Callable[[str], dict[str, str]]
Get = Callable[[str, dict[str, str]], tuple[int, bytes]]

PR_URL = re.compile(r"^https://github\.com/([A-Za-z0-9_.-]{1,100})/([A-Za-z0-9_.-]{1,100})/pull/([0-9]{1,9})/?$")
TIMEOUT_SECONDS = 20


def is_pr_url(url: object) -> bool:
    return isinstance(url, str) and PR_URL.match(url) is not None


def check(
    url: str,
    config: DispatchConfig,
    *,
    run: dispatch_local.Run | None = None,
    get: Get | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Stan PR-a spod `url`: w trybie lokalnym przez `gh`, potem (albo poza nim) przez API z tokenem."""
    m = PR_URL.match(url)
    if m is None:
        return {"state": "unknown", "reason": "adres nie jest PR-em na github.com"}
    reasons = []
    if config.local:
        found = _from_gh(url, run or _run, environ if environ is not None else os.environ)
        if found["state"] != "unknown":
            return found
        reasons.append(found["reason"])
    if config.token:
        found = _from_api(m.group(1), m.group(2), m.group(3), config.token, get or _get)
        if found["state"] != "unknown":
            return found
        reasons.append(found["reason"])
    if not reasons:
        reasons.append("brak trybu lokalnego (gh) i PDI_GITHUB_TOKEN")
    return {"state": "unknown", "reason": "; ".join(reasons)}


def checker(config: DispatchConfig) -> Check:
    return lambda url: check(url, config)


def _from_gh(url: str, run: dispatch_local.Run, environ: Mapping[str, str]) -> dict[str, str]:
    # `gh` dostaje tylko zmienne systemowe i swoje — bez sekretów pdi.
    env = {
        k: v
        for k, v in environ.items()
        if k in dispatch_local.SYSTEM_ENV
        or k.startswith(dispatch_local.SYSTEM_PREFIXES)
        or k in dispatch_local.GITHUB_ENV
    }
    try:
        code, out = run(["gh", "pr", "view", url, "--json", "state", "-q", ".state"], Path.cwd(), env)
    except (OSError, subprocess.SubprocessError) as e:
        return {"state": "unknown", "reason": f"gh nie działa ({type(e).__name__})"}
    state = out.strip().lower()
    if code != 0 or state not in ("merged", "open", "closed"):
        return {"state": "unknown", "reason": f"gh pr view zakończone kodem {code}"}
    return {"state": state}


def _from_api(owner: str, repo: str, number: str, token: str, get: Get) -> dict[str, str]:
    headers = {
        "accept": "application/vnd.github+json",
        "authorization": f"Bearer {token}",
        "x-github-api-version": "2022-11-28",
    }
    try:
        status, body = get(f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}", headers)
    except (OSError, ValueError):
        # Treść wyjątku może zawierać nagłówki — nie przepisujemy jej.
        return {"state": "unknown", "reason": "API GitHuba nie odpowiada"}
    if status != 200:
        return {"state": "unknown", "reason": f"API GitHuba odpowiada {status}"}
    try:
        data: Any = json.loads(body)
    except ValueError:
        return {"state": "unknown", "reason": "API GitHuba zwróciło niepoprawny JSON"}
    if not isinstance(data, dict) or data.get("state") not in ("open", "closed"):
        return {"state": "unknown", "reason": "API GitHuba zwróciło nieznany stan PR-a"}
    if data.get("merged") is True:
        return {"state": "merged"}
    return {"state": str(data["state"])}


def _get(url: str, headers: dict[str, str]) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers=headers)  # noqa: S310 — stały adres https
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310
            return int(response.status), response.read(1_000_000)
    except urllib.error.HTTPError as e:
        return int(e.code), b""


def _run(argv: list[str], cwd: Path, env: Mapping[str, str]) -> tuple[int, str]:
    done = subprocess.run(  # noqa: S603 — stała lista argumentów
        argv, cwd=cwd, env=dict(env), capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=False
    )
    return done.returncode, done.stdout
