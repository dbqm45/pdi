"""`sdlc` (L4, decyzje DL2 i DL3): ShipScope, pdi-receiver i ci_for_sdlc lokalnie jednym poleceniem.

`sdlc up` sprawdza narzędzia, raz pyta o ścieżki klonów (`~/.sdlc/config.toml`), raz generuje sekrety
(`~/.sdlc/env`, 600), startuje ShipScope (`npm run dev`: Postgres w Dockerze, web i worker) i pdi-receiver jako
odłączone procesy, łączy ShipScope z pdi bez przeglądarki (`server/scripts/local-pdi.js` w ShipScope), wysyła gotowość
zmian z ci_for_sdlc i rejestruje serwery MCP w Claude Code. Sekrety idą do procesów tylko przez środowisko; w argv,
logach i wyjściu `sdlc` ich nie ma. Tylko biblioteka standardowa. Plan: docs/plan-l4-sdlc.md.
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pdi.stack import home

Run = Callable[[list[str], Path | None, Mapping[str, str], str | None], tuple[int, str, str]]
Spawn = Callable[[str, list[str], Path, Mapping[str, str], Path], int]
Http = Callable[[str, Mapping[str, str]], tuple[int, bytes]]

RECEIVER_URL = "http://127.0.0.1:8787"
PG_CONTAINER = "shipscope-dev-pg"  # nazwa kontenera i wolumenu z ShipScope server/scripts/dev.js
LOCAL_PDI = "server/scripts/local-pdi.js"
INSTALL = {
    "docker": "brew install --cask docker   # potem uruchom Docker Desktop",
    "gh": "brew install gh",
    "claude": "npm install -g @anthropic-ai/claude-code",
    "node": "brew install node",
    "npm": "brew install node",
    "uv": "curl -LsSf https://astral.sh/uv/install.sh | sh",
}
FIRST_RUN_WAIT = 15 * 60
START_WAIT = {"shipscope": 3 * 60, "pdi-receiver": 30}
POLL_SECONDS = 2.0
WORKSPACE_POLL_SECONDS = 5.0
DEPLOY_ENVIRONMENTS = {"prod": "production", "test": "test"}
RESET_WORD = "usuń"
SANDBOX_TEMPLATE = "dbqm45/sdlc-sandbox"
# Źródło flag repo próbnego w ShipScope (L5): config/flags.{test,prod}.json, { "<klucz>": { "enabled", "rollout" } }.
SANDBOX_FLAGS = {"file": "config/flags.{env}.json", "valuePath": "enabled", "rolloutPath": "rollout"}
TRACK_ATTEMPTS = 5


@dataclass
class Ctx:
    """Wszystko, czego `sdlc` używa z zewnątrz — w testach podstawione."""

    user_home: Path
    cwd: Path
    environ: Mapping[str, str]
    run: Run
    spawn: Spawn
    alive: Callable[[int], bool]
    kill: Callable[[int], None]
    http: Http
    port_free: Callable[[str, int], bool]
    which: Callable[[str], str | None]
    ask: Callable[[str, str], str]
    type_line: Callable[[str], str]
    out: Callable[[str], None]
    sleep: Callable[[float], None]
    clock: Callable[[], float]
    open_url: Callable[[str], Any]
    exec: Callable[[list[str], Mapping[str, str]], None]
    python_bin: Path

    @property
    def root(self) -> Path:
        return home.root(self.user_home)


class Stop(Exception):
    """Błąd, który kończy polecenie komunikatem i kodem 1."""


# --- konfiguracja i środowiska procesów ---


def config_of(ctx: Ctx) -> home.Config:
    path = ctx.root / "config.toml"
    config = home.load_config(path)
    if config is not None:
        return config
    ctx.out("Pierwsze uruchomienie: ścieżki klonów (Enter = podpowiedź). Zapiszę je w ~/.sdlc/config.toml.")
    parent = ctx.cwd.parent

    def path_of(prompt: str, default: Path | str, *, optional: bool = False) -> Path | None:
        value = ctx.ask(prompt, str(default)).strip()
        if not value:
            if optional:
                return None
            raise Stop(f"{prompt}: ścieżka jest wymagana.")
        return Path(value).expanduser()

    config = home.Config(
        pdi=path_of("Klon pdi", ctx.cwd) or ctx.cwd,
        shipscope=path_of("Klon ShipScope (evdt-service-shipscope)", parent / "evdt-service-shipscope") or parent,
        ci_for_sdlc=path_of("Klon ci_for_sdlc", parent / "ci_for_sdlc") or parent,
        registry=path_of("Rejestr decyzji (PDI_REGISTRY_PATH)", ctx.user_home / "pdi-decisions") or parent,
        checkout=path_of("Repo produktu dla faz tf (PDI_DISPATCH_CHECKOUT, puste = bez)", "", optional=True),
    )
    for name in ("pdi", "shipscope", "ci_for_sdlc"):
        if not getattr(config, name).is_dir():
            raise Stop(f"{getattr(config, name)} nie istnieje — sklonuj repo i uruchom `sdlc up` ponownie.")
    if config.checkout is not None and not (config.checkout / ".git").exists():
        raise Stop(f"{config.checkout} nie jest repozytorium git.")
    home.save_config(path, config)
    return config


def shipscope_url(config: home.Config) -> str:
    file_env = home.read_env(config.shipscope / "server/.env")
    port = file_env.get("PORT") or "3000"
    return (file_env.get("PUBLIC_BASE_URL") or f"http://localhost:{port}").rstrip("/")


def pdi_env(ctx: Ctx, config: home.Config, secrets: Mapping[str, str]) -> dict[str, str]:
    """Środowisko odbiornika i serwera MCP pdi: plik env plus ścieżki z konfiguracji."""
    env = {**ctx.environ, **secrets, "PDI_REGISTRY_PATH": str(config.registry)}
    if config.checkout is not None:
        env["PDI_DISPATCH_CHECKOUT"] = str(config.checkout)
    return env


# --- procesy ---


def pid_of(ctx: Ctx, name: str) -> int | None:
    path = ctx.root / "run" / f"{name}.pid"
    try:
        pid = int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None
    return pid if ctx.alive(pid) else None


def start(ctx: Ctx, name: str, argv: list[str], cwd: Path, env: Mapping[str, str]) -> int:
    (ctx.root / "logs").mkdir(parents=True, exist_ok=True)
    (ctx.root / "run").mkdir(parents=True, exist_ok=True)
    pid = ctx.spawn(name, argv, cwd, env, ctx.root / "logs" / f"{name}.log")
    (ctx.root / "run" / f"{name}.pid").write_text(f"{pid}\n", encoding="utf-8")
    return pid


def stop(ctx: Ctx, name: str) -> bool:
    pid = pid_of(ctx, name)
    (ctx.root / "run" / f"{name}.pid").unlink(missing_ok=True)
    if pid is None:
        return False
    ctx.kill(pid)
    return True


def wait_for(ctx: Ctx, name: str, url: str, *, seconds: float, any_status: bool) -> None:
    """Czeka, aż usługa odpowie (200, albo dowolnym kodem HTTP przy `any_status`)."""
    deadline = ctx.clock() + seconds
    while True:
        try:
            status, _ = ctx.http(url, {})
            if any_status or status == 200:
                return
        except OSError:
            pass
        pid = pid_of(ctx, name)
        if pid is None or ctx.clock() >= deadline:
            why = "zakończył się" if pid is None else f"nie odpowiada od {int(seconds)} s"
            raise Stop(f"{name} {why} — zobacz ~/.sdlc/logs/{name}.log")
        ctx.sleep(POLL_SECONDS)


def ensure_port_free(ctx: Ctx, name: str, url: str) -> None:
    """Port usługi, której `sdlc` nie uruchomił, musi być wolny: inaczej /health odpowie obcy proces."""
    parts = urllib.parse.urlsplit(url)
    host, port = parts.hostname or "localhost", parts.port or 80
    if not ctx.port_free(host, port):
        raise Stop(
            f"{name}: port {port} zajmuje inny proces, którego sdlc nie uruchomił (np. pozostałość po przerwanym "
            f"sdlc up). Sprawdź: lsof -nP -iTCP:{port} -sTCP:LISTEN, zatrzymaj go i uruchom sdlc up ponownie."
        )


def ensure_shipscope(ctx: Ctx, config: home.Config) -> str:
    url = shipscope_url(config)
    if pid_of(ctx, "shipscope") is not None:
        return url
    ensure_port_free(ctx, "ShipScope", url)
    first = not home.read_env(config.shipscope / "server/.env").get("GITHUB_APP_CLIENT_ID")
    if first:
        ctx.out(f"ShipScope: pierwsze uruchomienie — otwórz {url}/ i kliknij „Create the GitHub App” (raz).")
    env = {**ctx.environ, "SYNC_INTERVAL_MINUTES": "1"}
    start(ctx, "shipscope", ["node", "server/scripts/dev.js"], config.shipscope, env)
    ctx.out("ShipScope: start (Postgres w Dockerze, migracje, web i worker)…")
    wait_for(
        ctx,
        "shipscope",
        f"{url}/health",
        seconds=FIRST_RUN_WAIT if first else START_WAIT["shipscope"],
        any_status=False,
    )
    return url


def start_receiver(ctx: Ctx, config: home.Config, secrets: Mapping[str, str]) -> None:
    argv = ["uv", "run", "--directory", str(config.pdi), "pdi-receiver"]
    ensure_port_free(ctx, "pdi-receiver", RECEIVER_URL)
    start(ctx, "pdi-receiver", argv, config.pdi, pdi_env(ctx, config, secrets))
    wait_for(ctx, "pdi-receiver", f"{RECEIVER_URL}/", seconds=START_WAIT["pdi-receiver"], any_status=True)


# --- polecenia ---


def check_tools(ctx: Ctx) -> list[str]:
    problems = [f"brak {tool}: {INSTALL[tool]}" for tool in INSTALL if ctx.which(tool) is None]
    if ctx.which("gh") is not None:
        code, _, _ = ctx.run(["gh", "auth", "status"], None, ctx.environ, None)
        if code != 0:
            problems.append("gh nie jest zalogowany: gh auth login")
    return problems


def connect(ctx: Ctx, config: home.Config, url: str, secrets: dict[str, str]) -> dict[str, str]:
    """Łączy ShipScope z pdi (`local-pdi.js connect`), czekając na przestrzeń; zwraca env z trzema zmiennymi."""
    argv = ["node", LOCAL_PDI, "connect", "--receiver", RECEIVER_URL]
    deadline = ctx.clock() + FIRST_RUN_WAIT
    asked = False
    while True:
        code, out, err = ctx.run(argv, config.shipscope, ctx.environ, None)
        if code == 0:
            break
        if code == 4 and argv[-1] != "--replace":
            argv = [*argv, "--replace"]  # połączone, a zmiennych w ~/.sdlc/env brak — nowe
            continue
        if code == 3 and ctx.clock() < deadline:
            if not asked:
                ctx.out(f"ShipScope: zaloguj się na {url}/ przez GitHub i utwórz przestrzeń (raz). Czekam…")
                asked = True
            ctx.sleep(WORKSPACE_POLL_SECONDS)
            continue
        raise Stop(f"Połączenie ShipScope z pdi: {_first_line(err) or f'kod {code}'}")
    try:
        answer = json.loads(out)
        values = {key: str(answer["env"][key]) for key in home.SHIPSCOPE_KEYS}
        workspace = str(answer["workspace"]["name"])
    except (ValueError, KeyError, TypeError) as e:
        raise Stop("Połączenie ShipScope z pdi: nieczytelna odpowiedź local-pdi.js.") from e
    secrets = {**secrets, **values}
    home.write_env(ctx.root / "env", secrets)
    ctx.out(f"ShipScope ↔ pdi: przestrzeń {workspace} połączona; zmienne zapisane w ~/.sdlc/env.")
    return secrets


def ci_check(ctx: Ctx, config: home.Config, secrets: Mapping[str, str]) -> int:
    if config.checkout is None:
        ctx.out("ci_for_sdlc → pdi: pominięte (brak repo produktu w ~/.sdlc/config.toml).")
        return 0
    if not (config.ci_for_sdlc / "node_modules").is_dir():
        ctx.out("ci_for_sdlc: npm install (raz)…")
        code, _, err = ctx.run(["npm", "install"], config.ci_for_sdlc, ctx.environ, None)
        if code != 0:
            raise Stop(f"ci_for_sdlc: npm install — kod {code}: {_first_line(err)}")
    data = ctx.root / "ci-data"
    data.mkdir(parents=True, exist_ok=True)
    env = {
        **ctx.environ,
        "PDI_EVENTS_URL": secrets["PDI_EVENTS_URL"],
        "PDI_SIGNING_SECRET": secrets["PDI_CI_FOR_SDLC_SIGNING_SECRET"],
        "CI_DATA_DIR": str(data),
    }
    argv = ["npm", "run", "analyze", "--", "--repo", str(config.checkout), "--send-to-pdi"]
    code, out, err = ctx.run(argv, config.ci_for_sdlc, env, None)
    (ctx.root / "run").mkdir(parents=True, exist_ok=True)
    (ctx.root / "run" / "ci-check.json").write_text(json.dumps({"code": code}) + "\n", encoding="utf-8")
    if code == 2:
        raise Stop(f"ci_for_sdlc → pdi: {_first_line(err) or 'brak konfiguracji pdi'}")
    for line in out.splitlines():
        if line.strip().startswith("pdi"):
            ctx.out(f"ci_for_sdlc: {line.strip()}")
    return code


def register_mcp(ctx: Ctx, config: home.Config) -> None:
    for name in ("pdi", "shipscope"):
        ctx.run(["claude", "mcp", "remove", "--scope", "user", name], None, ctx.environ, None)
        command = ["uv", "run", "--directory", str(config.pdi), "sdlc", "mcp", name]
        code, _, err = ctx.run(
            ["claude", "mcp", "add", "--scope", "user", name, "--", *command], None, ctx.environ, None
        )
        if code != 0:
            raise Stop(f"claude mcp add {name}: {_first_line(err) or f'kod {code}'}")


def cmd_up(ctx: Ctx) -> int:
    problems = check_tools(ctx)
    if problems:
        ctx.out("Brakuje narzędzi:")
        for problem in problems:
            ctx.out(f"  {problem}")
        return 1
    config = config_of(ctx)
    config.registry.mkdir(parents=True, exist_ok=True)
    secrets, created = home.ensure_env(ctx.root)
    if created:
        ctx.out(f"~/.sdlc/env: wygenerowane {', '.join(created)}")
    url = ensure_shipscope(ctx, config)
    if pid_of(ctx, "pdi-receiver") is None:
        start_receiver(ctx, config, secrets)
    if not all(secrets.get(key) for key in home.SHIPSCOPE_KEYS):
        secrets = connect(ctx, config, url, secrets)
        stop(ctx, "pdi-receiver")
        start_receiver(ctx, config, secrets)  # czyta połączenie przy starcie: dowód „pdi czyta ShipScope”
        code, out, err = ctx.run(["node", LOCAL_PDI, "test"], config.shipscope, ctx.environ, None)
        state = _state(out) if code == 0 else f"test nieudany: {_first_line(err)}"
        ctx.out(f"ShipScope ↔ pdi: {state}")
    ci_check(ctx, config, secrets)
    register_mcp(ctx, config)
    ctx.out("")
    ctx.out(f"  ShipScope       {url}/")
    ctx.out(f"  pdi-receiver    {RECEIVER_URL}/events/<shipscope|tf|ci_for_sdlc>, formularz: sdlc open")
    ctx.out("  MCP w Claude    pdi, shipscope")
    ctx.out("  stan            uv run sdlc status")
    ctx.out("gotowe")
    return 0


def cmd_status(ctx: Ctx) -> int:
    config = home.load_config(ctx.root / "config.toml")
    if config is None:
        ctx.out("sdlc nie był jeszcze uruchomiony: uv run sdlc up")
        return 1
    secrets = home.read_env(ctx.root / "env")
    url = shipscope_url(config)
    for name, address in (("shipscope", f"{url}/"), ("pdi-receiver", f"{RECEIVER_URL}/")):
        pid = pid_of(ctx, name)
        ctx.out(f"{name}: {'działa, pid ' + str(pid) if pid else 'nie działa'} — {address}")
    code, out, _ = ctx.run(["docker", "inspect", "-f", "{{.State.Running}}", PG_CONTAINER], None, ctx.environ, None)
    ctx.out(f"Postgres ({PG_CONTAINER}): {'działa' if code == 0 and out.strip() == 'true' else 'nie działa'}")
    ctx.out(f"ShipScope ↔ pdi: {shipscope_link(ctx, secrets)}")
    ctx.out(f"ci_for_sdlc → pdi: {ci_link(ctx)}")
    for key in home.SECRET_KEYS:
        ctx.out(f"{key}: {'ustawiony' if secrets.get(key) else 'brak'}")
    log = ctx.root / "logs" / "pdi-receiver.log"
    if log.is_file():
        lines = [line for line in log.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
        ctx.out("Ostatnie wpisy odbiornika:")
        for line in lines[-5:]:
            ctx.out(f"  {line}")
    items = _open_items(config.registry)
    ctx.out(f"Skrzynka pdi: {len(items)} otwartych")
    for item in items[:5]:
        ctx.out(f"  {item.get('id')} {item.get('kind')} {str(item.get('summary') or '')[:80]}")
    return 0


def shipscope_link(ctx: Ctx, secrets: Mapping[str, str]) -> str:
    from pdi.impact import ShipScopeConfig, read_connection

    config = ShipScopeConfig(url=secrets.get("PDI_SHIPSCOPE_URL"), token=secrets.get("PDI_SHIPSCOPE_TOKEN"))

    def get(url: str, headers: dict[str, str]) -> tuple[int, bytes]:
        return ctx.http(url, headers)

    value, error = read_connection(config, get=get)
    if value is None:
        return f"nieznany ({error})"
    return str(value["state"])


def ci_link(ctx: Ctx) -> str:
    data = ctx.root / "ci-data"
    try:
        state = json.loads((data / "pdi-state.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = None
    try:
        outbox = json.loads((data / "pdi-outbox.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        outbox = []
    waiting = [e for e in outbox if isinstance(e, dict) and not e.get("failed")] if isinstance(outbox, list) else []
    if waiting:
        return f"queued {len(waiting)}"
    if isinstance(state, dict) and state.get("sent"):
        return "connected"
    if (ctx.root / "run" / "ci-check.json").is_file():
        return "configured (sprawdzenie przeszło, brak zmian CHG do wysłania)"
    return "not run (uv run sdlc check)"


def cmd_check(ctx: Ctx) -> int:
    config = home.load_config(ctx.root / "config.toml")
    if config is None:
        raise Stop("Najpierw: uv run sdlc up")
    ci_check(ctx, config, home.read_env(ctx.root / "env"))
    return 0


def cmd_deploy(ctx: Ctx, target: str, repo: str | None) -> int:
    config = home.load_config(ctx.root / "config.toml")
    repo = repo or (config.deploy_repo if config else None) or _origin_repo(ctx, config)
    if not repo or not re.match(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", repo):
        raise Stop("Podaj repo: sdlc deploy <prod|test> --repo właściciel/nazwa")
    environment = DEPLOY_ENVIRONMENTS[target]
    code, out, err = ctx.run(["gh", "api", f"repos/{repo}/commits/main", "--jq", ".sha"], None, ctx.environ, None)
    sha = out.strip()
    if code != 0 or not re.match(r"^[0-9a-f]{7,40}$", sha):
        raise Stop(f"gh api: nie ma main w {repo} ({_first_line(err) or code})")
    body = {
        "ref": sha,
        "environment": environment,
        "auto_merge": False,
        "required_contexts": [],
        "description": "sdlc deploy",
    }
    deployments = ["gh", "api", "-X", "POST", f"repos/{repo}/deployments", "--input", "-"]
    code, out, err = ctx.run(deployments, None, ctx.environ, json.dumps(body))
    try:
        deployment = int(json.loads(out)["id"])
    except (ValueError, KeyError, TypeError) as e:
        raise Stop(f"gh api: GitHub nie założył wdrożenia ({_first_line(err) or code})") from e
    statuses = ["gh", "api", "-X", "POST", f"repos/{repo}/deployments/{deployment}/statuses", "--input", "-"]
    code, _, err = ctx.run(statuses, None, ctx.environ, json.dumps({"state": "success", "environment": environment}))
    if code != 0:
        raise Stop(f"gh api: status wdrożenia {deployment} — {_first_line(err) or code}")
    ctx.out(f"Wdrożenie {deployment}: {repo}@{sha} → {environment} (success). ShipScope odczyta je w ciągu minuty.")
    return 0


def cmd_open(ctx: Ctx) -> int:
    config = home.load_config(ctx.root / "config.toml")
    if config is None:
        raise Stop("Najpierw: uv run sdlc up")
    form = home.read_env(ctx.root / "env").get("PDI_FORM_TOKEN", "")
    ctx.open_url(f"{shipscope_url(config)}/")
    ctx.open_url(f"{RECEIVER_URL}/problems/new?t={form}")
    ctx.out("Otwieram ShipScope i formularz zgłoszeń.")
    return 0


def cmd_down(ctx: Ctx) -> int:
    for name in ("pdi-receiver", "shipscope"):
        ctx.out(f"{name}: {'zatrzymany' if stop(ctx, name) else 'nie działał'}")
    ctx.run(["docker", "stop", PG_CONTAINER], None, ctx.environ, None)
    ctx.out(f"Postgres zatrzymany; dane zostają w wolumenie {PG_CONTAINER}.")
    return 0


def cmd_reset(ctx: Ctx) -> int:
    ctx.out("Usunę dane lokalnego stosu: bazę ShipScope (kontener i wolumen), ~/.sdlc/ci-data, logs i run oraz")
    ctx.out("połączenie z ShipScope w ~/.sdlc/env. Zostaną: config.toml, pozostałe sekrety i rejestr decyzji.")
    if ctx.type_line(f"Wpisz „{RESET_WORD}”, żeby potwierdzić: ").strip() != RESET_WORD:
        ctx.out("Nic nie usunięto.")
        return 1
    cmd_down(ctx)
    ctx.run(["docker", "rm", "-f", PG_CONTAINER], None, ctx.environ, None)
    ctx.run(["docker", "volume", "rm", PG_CONTAINER], None, ctx.environ, None)
    for name in ("ci-data", "logs", "run"):
        _remove_tree(ctx.root / name)
    secrets = home.read_env(ctx.root / "env")
    home.write_env(ctx.root / "env", {k: v for k, v in secrets.items() if k not in home.SHIPSCOPE_KEYS})
    ctx.out("Usunięte. Następne `sdlc up` połączy ShipScope z pdi od nowa.")
    return 0


def cmd_sandbox(ctx: Ctx, name: str, owner: str | None) -> int:
    """Repo próbne z szablonu: utworzone albo użyte ponownie, sklonowane, śledzone w ShipScope, repo faz tf (L5)."""
    config = home.load_config(ctx.root / "config.toml")
    if config is None:
        raise Stop("Najpierw: uv run sdlc up")
    if not re.match(r"^[A-Za-z0-9_.-]{1,100}$", name):
        raise Stop("Nazwa repo: litery, cyfry, . _ -")
    if owner is None:
        code, out, err = ctx.run(["gh", "api", "user", "--jq", ".login"], None, ctx.environ, None)
        owner = out.strip()
        if code != 0 or not owner:
            raise Stop(f"gh: kto jest zalogowany? ({_first_line(err) or code}) — gh auth login")
    if not re.match(r"^[A-Za-z0-9-]{1,39}$", owner):
        raise Stop("--owner: login konta GitHub")
    repo = f"{owner}/{name}"
    clone = config.pdi.parent / name
    code, _, _ = ctx.run(["gh", "repo", "view", repo, "--json", "name"], None, ctx.environ, None)
    if code != 0:
        argv = ["gh", "repo", "create", repo, "--template", SANDBOX_TEMPLATE, "--private", "--clone"]
        code, _, err = ctx.run(argv, clone.parent, ctx.environ, None)
        if code != 0:
            raise Stop(f"gh repo create: {_first_line(err) or code}")
        ctx.out(f"Repo {repo}: utworzone z szablonu {SANDBOX_TEMPLATE} (prywatne).")
    elif (clone / ".git").exists():
        code, _, err = ctx.run(["git", "-C", str(clone), "pull", "--ff-only"], None, ctx.environ, None)
        if code != 0:
            raise Stop(f"git pull w {clone}: {_first_line(err) or code}")
    else:
        code, _, err = ctx.run(["gh", "repo", "clone", repo, str(clone)], None, ctx.environ, None)
        if code != 0:
            raise Stop(f"gh repo clone: {_first_line(err) or code}")
    track(ctx, config, repo)
    updated = dataclasses.replace(config, checkout=clone, deploy_repo=repo)
    if updated != config:
        home.save_config(ctx.root / "config.toml", updated)
        if pid_of(ctx, "pdi-receiver") is not None:
            stop(ctx, "pdi-receiver")
        start_receiver(ctx, updated, home.read_env(ctx.root / "env"))
        ctx.out("pdi: repo faz tf (PDI_DISPATCH_CHECKOUT) ustawione; odbiornik uruchomiony ponownie. Serwer MCP pdi")
        ctx.out("weźmie je od następnej sesji Claude.")
    ctx.out("")
    ctx.out(f"  repo            https://github.com/{repo}")
    ctx.out(f"  klon            {clone}")
    ctx.out(
        "  pierwszy krok   uv run sdlc open, potem zgłoszenie z README repo próbnego (pdi: docs/przebieg-lokalny.md)"
    )
    ctx.out("gotowe")
    return 0


def track(ctx: Ctx, config: home.Config, repo: str) -> None:
    """Śledzenie repo i jego źródło flag w ShipScope (`local-pdi.js track`); czeka na instalację aplikacji GitHub."""
    argv = ["node", LOCAL_PDI, "track", "--repo", repo, "--flags", json.dumps(SANDBOX_FLAGS)]
    told = False
    for _ in range(TRACK_ATTEMPTS):
        code, out, err = ctx.run(argv, config.shipscope, ctx.environ, None)
        if code == 0:
            created = (_json(out).get("flagSource") or {}).get("created")
            ctx.out(
                f"ShipScope: {repo} śledzone, flagi z config/flags.{{env}}.json{' (nowe źródło)' if created else ''}."
            )
            return
        if code == 3:
            raise Stop("ShipScope nie ma jeszcze przestrzeni — najpierw: uv run sdlc up")
        if code != 5:
            raise Stop(f"ShipScope track: {_first_line(err) or f'kod {code}'}")
        if not told:
            url = shipscope_url(config)
            ctx.out(f"ShipScope nie widzi jeszcze {repo}. W przeglądarce, zalogowany w ShipScope ({url}/):")
            ctx.out("  1. Settings → GitHub → Install (aplikacja GitHub ShipScope);")
            ctx.out(f"  2. na GitHubie wybierz konto {repo.split('/')[0]} i „All repositories” (albo tylko {repo});")
            ctx.out("  3. po powrocie do ShipScope instalacja jest połączona z przestrzenią.")
            told = True
        ctx.type_line("Naciśnij Enter, gdy skończysz… ")
    raise Stop(
        f"ShipScope dalej nie widzi {repo} — sprawdź instalację aplikacji GitHub i uruchom `sdlc sandbox` ponownie."
    )


def cmd_mcp(ctx: Ctx, name: str) -> int:
    """Serwer MCP ze zmiennymi z ~/.sdlc/env — tę komendę rejestruje `sdlc up` w Claude Code."""
    config = home.load_config(ctx.root / "config.toml")
    if config is None:
        raise Stop("Najpierw: uv run sdlc up")
    secrets = home.read_env(ctx.root / "env")
    if name == "pdi":
        ctx.exec([str(ctx.python_bin.parent / "pdi-mcp")], pdi_env(ctx, config, secrets))
    else:
        env = {
            **ctx.environ,
            "SHIPSCOPE_URL": shipscope_url(config),
            "SHIPSCOPE_TOKEN": secrets.get("PDI_SHIPSCOPE_TOKEN", ""),
        }
        ctx.exec(["node", str(config.shipscope / "adapters/mcp/shipscope-mcp.js")], env)
    return 0


# --- wejście ---


def main(argv: list[str] | None = None, *, ctx: Ctx | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sdlc", description="Cały workflow lokalnie: ShipScope, pdi i ci_for_sdlc.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("up", help="startuje stos i łączy usługi (idempotentne)")
    sub.add_parser("status", help="procesy, połączenia, skrzynka pdi")
    sub.add_parser("check", help="ci_for_sdlc: gotowość zmian z repo produktu do pdi")
    deploy = sub.add_parser("deploy", help="GitHub Deployment HEAD main repo próbnego")
    deploy.add_argument("target", choices=sorted(DEPLOY_ENVIRONMENTS))
    deploy.add_argument("--repo", help="właściciel/nazwa (domyślnie z config.toml albo origin repo produktu)")
    sub.add_parser("open", help="ShipScope i formularz zgłoszeń w przeglądarce")
    sub.add_parser("down", help="zatrzymuje procesy i Postgresa; dane zostają")
    sub.add_parser("reset", help="usuwa dane po potwierdzeniu")
    sandbox = sub.add_parser("sandbox", help="repo próbne z szablonu: utworzone, sklonowane, śledzone, repo faz tf")
    sandbox.add_argument("name")
    sandbox.add_argument("--owner", help="konto GitHub (domyślnie zalogowane w gh)")
    mcp = sub.add_parser("mcp", help="(dla Claude Code) serwer MCP ze zmiennymi z ~/.sdlc/env")
    mcp.add_argument("name", choices=("pdi", "shipscope"))
    args = parser.parse_args(argv)
    ctx = ctx or real_ctx()
    try:
        if args.command == "up":
            return cmd_up(ctx)
        if args.command == "status":
            return cmd_status(ctx)
        if args.command == "check":
            return cmd_check(ctx)
        if args.command == "deploy":
            return cmd_deploy(ctx, args.target, args.repo)
        if args.command == "open":
            return cmd_open(ctx)
        if args.command == "down":
            return cmd_down(ctx)
        if args.command == "reset":
            return cmd_reset(ctx)
        if args.command == "sandbox":
            return cmd_sandbox(ctx, args.name, args.owner)
        return cmd_mcp(ctx, args.name)
    except Stop as e:
        ctx.out(f"✗ {e}")
        return 1


def real_ctx() -> Ctx:
    import shutil

    return Ctx(
        user_home=Path.home(),
        cwd=Path.cwd(),
        environ=dict(os.environ),
        run=_run,
        spawn=_spawn,
        alive=_alive,
        kill=_kill,
        http=_http,
        port_free=_port_free,
        which=shutil.which,
        ask=_ask,
        type_line=input,
        out=print,
        sleep=time.sleep,
        clock=time.monotonic,
        open_url=webbrowser.open,
        exec=_exec,
        python_bin=Path(sys.executable),
    )


def _run(argv: list[str], cwd: Path | None, env: Mapping[str, str], stdin: str | None) -> tuple[int, str, str]:
    try:
        done = subprocess.run(  # noqa: S603 — lista argumentów, bez powłoki
            argv, cwd=cwd, env=dict(env), input=stdin, capture_output=True, text=True, check=False
        )
    except FileNotFoundError:
        return 127, "", f"brak polecenia {argv[0]}"
    return done.returncode, done.stdout, done.stderr


def _spawn(name: str, argv: list[str], cwd: Path, env: Mapping[str, str], log: Path) -> int:
    with log.open("ab") as out:
        process = subprocess.Popen(  # noqa: S603 — lista argumentów, bez powłoki
            argv,
            cwd=cwd,
            env=dict(env),
            stdin=subprocess.DEVNULL,
            stdout=out,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    return process.pid


def _alive(pid: int) -> bool:
    # Własne dziecko, które już się skończyło, jest zombie, dopóki go nie odbierzemy; kill(pid, 0) widzi je jako żywe.
    with contextlib.suppress(ChildProcessError):
        if os.waitpid(pid, os.WNOHANG)[0] == pid:
            return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


KILL_GRACE_SECONDS = 10.0


def _kill(pid: int) -> None:
    """SIGTERM grupy procesów i wszystkich potomków, po KILL_GRACE_SECONDS SIGKILL tego, co jeszcze żyje.

    Potomków zbiera się przed sygnałem: `npm run dev` w ShipScope startuje web i worker we własnych grupach
    (detached) i kończy się po pół sekundy, nie czekając na nie, a osierocone dzieci nie są już jego potomkami (PRB-8).
    """
    if not _alive(pid):
        return
    tree = [pid, *_descendants(pid, _process_table())]
    try:
        os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    except PermissionError:  # macOS: grupa z samym zombie
        if not _alive(pid) and len(tree) == 1:
            return
    for child in tree[1:]:
        _signal(child, signal.SIGTERM)
    deadline = time.monotonic() + KILL_GRACE_SECONDS
    while time.monotonic() < deadline:
        if not any(_running(p) for p in tree):
            return
        time.sleep(0.2)
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(pid, signal.SIGKILL)
    for child in tree[1:]:
        _signal(child, signal.SIGKILL)


def _running(pid: int) -> bool:
    """Własne dziecko jak w _alive; cudzy proces (sierota przejęta przez init) — póki istnieje i nie jest zombie."""
    if not _alive(pid):
        return False
    try:
        done = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True, check=False)  # noqa: S603, S607
    except OSError:
        return True
    state = done.stdout.strip()
    return bool(state) and not state.startswith("Z")


def _signal(pid: int, sig: signal.Signals) -> None:
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.kill(pid, sig)


def _process_table() -> str:
    """`pid ppid` każdego procesu (ps działa tak samo na Linuksie i macOS); pusty, gdy ps nie działa."""
    try:
        done = subprocess.run(["ps", "-A", "-o", "pid=", "-o", "ppid="], capture_output=True, text=True, check=False)  # noqa: S603, S607
    except OSError:
        return ""
    return done.stdout if done.returncode == 0 else ""


def _descendants(pid: int, table: str) -> list[int]:
    """Potomkowie `pid` z tabeli `pid ppid`, wszerz (dzieci przed wnukami)."""
    children: dict[int, list[int]] = {}
    for line in table.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            children.setdefault(int(parts[1]), []).append(int(parts[0]))
    found: list[int] = []
    queue = list(children.get(pid, []))
    while queue:
        child = queue.pop(0)
        if child in found or child == pid:
            continue
        found.append(child)
        queue += children.get(child, [])
    return found


def _port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.5)
        return probe.connect_ex((host, port)) != 0


def _http(url: str, headers: Mapping[str, str]) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers=dict(headers))  # noqa: S310 — adresy localhost z konfiguracji
    try:
        with urllib.request.urlopen(request, timeout=5) as response:  # noqa: S310
            return int(response.status), response.read()
    except urllib.error.HTTPError as e:
        return int(e.code), e.read()
    except urllib.error.URLError as e:
        raise OSError(str(e.reason)) from e


def _ask(prompt: str, default: str) -> str:
    answer = input(f"{prompt} [{default}]: ").strip()
    return answer or default


def _exec(argv: list[str], env: Mapping[str, str]) -> None:
    os.execvpe(argv[0], argv, dict(env))  # noqa: S606 — stałe polecenie serwera MCP


def _state(out: str) -> str:
    try:
        return str(json.loads(out)["connection"]["state"])
    except (ValueError, KeyError, TypeError):
        return "nieznany"


def _json(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


def _first_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), "")[:200]


def _origin_repo(ctx: Ctx, config: home.Config | None) -> str | None:
    if config is None or config.checkout is None:
        return None
    code, out, _ = ctx.run(["git", "-C", str(config.checkout), "remote", "get-url", "origin"], None, ctx.environ, None)
    match = (
        re.search(r"github\.com[:/]([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?$", out.strip()) if code == 0 else None
    )
    return match.group(1) if match else None


def _open_items(registry: Path) -> list[dict[str, Any]]:
    from pdi.inbox import Inbox
    from pdi.registry import Registry

    if not registry.is_dir():
        return []
    try:
        return Inbox(Registry(registry)).items()
    except (OSError, ValueError):
        return []


def _remove_tree(path: Path) -> None:
    import shutil

    shutil.rmtree(path, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
