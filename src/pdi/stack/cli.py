"""Polecenie `sdlc`: `up`, `status`, `deploy`, `open`, `down`, `reset`, `check`, `mcp` (plan L4, docs/plan-l4-sdlc.md).

Sekrety z `~/.sdlc/env` idą do procesów potomnych wyłącznie przez środowisko; `sdlc` nigdy ich nie wypisuje ani nie
podaje w argv. Wszystko, co dotyka świata (polecenia, procesy w tle, HTTP, klawiatura), przychodzi w `Deps`.
"""

from __future__ import annotations

import contextlib
import html
import json
import os
import shutil
import signal
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import NoReturn

from pdi import impact
from pdi.stack import connect, files

PG_CONTAINER = "shipscope-dev-pg"  # te same nazwy co ShipScope `npm run dev`, więc obie drogi dzielą bazę
PG_IMAGE = "postgres:16-alpine"
PG_PORT = "54329"
APP_DATABASE_URL = f"postgres://shipscope_app:shipscope_app@localhost:{PG_PORT}/shipscope"
ADMIN_DATABASE_URL = f"postgres://postgres:postgres@localhost:{PG_PORT}/shipscope"
SHIPSCOPE_URL = "http://localhost:3000"
RECEIVER_URL = "http://127.0.0.1:8787"
WEB, WORKER, RECEIVER = "shipscope-web", "shipscope-worker", "pdi-receiver"
SERVICES = (WEB, WORKER, RECEIVER)
SERVICE_URLS = {WEB: SHIPSCOPE_URL, RECEIVER: RECEIVER_URL}
MCP_SERVERS = ("pdi", "shipscope")

TOOLS = {
    "docker": "brew install --cask docker",
    "gh": "brew install gh",
    "claude": "npm install -g @anthropic-ai/claude-code",
    "node": "brew install node",
    "npm": "brew install node",
    "uv": "brew install uv",
}
CREATE_ROLE = (
    "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'shipscope_app') THEN "
    "CREATE ROLE shipscope_app LOGIN PASSWORD 'shipscope_app'; END IF; END $$"
)
GITHUB_APP_VARS = ("GITHUB_APP_CLIENT_ID", "GITHUB_APP_CLIENT_SECRET")
USAGE = (
    "Użycie: sdlc up | status | deploy <prod|test> [--repo owner/nazwa] | open | down | reset"
    " | check [--repo ścieżka] | mcp <pdi|shipscope>"
)


@dataclass
class Deps:
    home: Path
    pdi_root: Path
    run: Callable[[list[str], Path, Mapping[str, str]], tuple[int, str]]
    spawn: Callable[[list[str], Path, Mapping[str, str], Path], int]
    get: impact.Get
    alive: Callable[[int], bool]
    kill: Callable[[int], None]
    ask: Callable[[str], str]
    out: Callable[[str], None]
    which: Callable[[str], str | None]
    open_url: Callable[[str], None]
    sleep: Callable[[float], None]
    exec: Callable[[list[str], Mapping[str, str]], None]
    environ: Mapping[str, str]
    random: Callable[[int], bytes]
    err: Callable[[str], None] = field(default=lambda text: print(text, file=sys.stderr))
    attempts: int = 60
    interval: float = 0.5


class Stop(Exception):
    """Przerwanie polecenia z kodem wyjścia; komunikat został już wypisany."""

    def __init__(self, code: int = 1) -> None:
        super().__init__(code)
        self.code = code


class Stack:
    def __init__(self, deps: Deps) -> None:
        self.deps = deps
        self.root = deps.home / ".sdlc"
        self.config_path = self.root / "config.toml"
        self.env_path = self.root / "env"
        self.logs = self.root / "logs"
        self.runs = self.root / "run"
        self.ci_data = self.root / "ci-data"
        self._config: files.Config | None = None

    @property
    def config(self) -> files.Config:
        assert self._config is not None  # noqa: S101 — ustawiane przed każdym poleceniem
        return self._config

    @property
    def server(self) -> Path:
        return self.config.shipscope / "server"

    def out(self, text: str) -> None:
        self.deps.out(text)

    def fail(self, *lines: str) -> NoReturn:
        for line in lines:
            self.out(line)
        raise Stop(1)

    # --- konfiguracja i środowiska ---

    def load(self) -> bool:
        if not self.config_path.exists():
            return False
        self._config = files.load_config(self.config_path)
        return True

    def ask_config(self) -> None:
        self.out("Pierwsze uruchomienie: trzy pytania o ścieżki (Enter = wartość w nawiasie).")
        default = self.deps.pdi_root.parent
        base = self._path(self.deps.ask(f"Katalog z klonami pdi, evdt-service-shipscope i ci_for_sdlc [{default}]: "))
        base = base or default
        registry_default = base / "pdi-decisions"
        registry = self._path(self.deps.ask(f"Rejestr decyzji pdi (PDI_REGISTRY_PATH) [{registry_default}]: "))
        checkout = self._path(self.deps.ask("Klon repo produktu (PDI_DISPATCH_CHECKOUT, Enter = brak): "))
        config = files.Config(
            pdi=self.deps.pdi_root,
            shipscope=base / "evdt-service-shipscope",
            ci_for_sdlc=base / "ci_for_sdlc",
            registry=registry or registry_default,
            checkout=checkout,
        )
        missing = [str(p) for p in (config.shipscope, config.ci_for_sdlc) if not p.is_dir()]
        if missing:
            self.fail(*(f"Brak klonu: {p}" for p in missing))
        files.save_config(self.config_path, config)
        self._config = config
        self.out(f"Zapisano {self.config_path}")

    @staticmethod
    def _path(answer: str) -> Path | None:
        answer = answer.strip()
        return Path(answer).expanduser() if answer else None

    def env(self) -> dict[str, str]:
        return files.read_env(self.env_path)

    def shipscope_dotenv(self) -> dict[str, str]:
        return files.read_dotenv(self.server / ".env")

    def web_env(self) -> dict[str, str]:
        return {
            **self.deps.environ,
            **self.shipscope_dotenv(),
            "DATABASE_URL": APP_DATABASE_URL,
            "DATABASE_SSL": "false",
            "PUBLIC_BASE_URL": SHIPSCOPE_URL,
            "PORT": "3000",
            "TOKEN_ENCRYPTION_KEY": self.env().get("TOKEN_ENCRYPTION_KEY", ""),
        }

    def pdi_env(self) -> dict[str, str]:
        return {**self.deps.environ, **self.config.service_vars(), **self.env()}

    # --- procesy ---

    def pid_file(self, name: str) -> Path:
        return self.runs / f"{name}.pid"

    def pid(self, name: str) -> int | None:
        try:
            return int(self.pid_file(name).read_text().strip())
        except (OSError, ValueError):
            return None

    def own_pid(self, name: str) -> int | None:
        pid = self.pid(name)
        return pid if pid is not None and self.deps.alive(pid) else None

    def healthy(self, name: str) -> bool:
        if name == WEB:
            return self._http(f"{SHIPSCOPE_URL}/health") == 200
        if name == RECEIVER:
            return self._http(f"{RECEIVER_URL}/") is not None  # odbiornik nie ma /health: każda odpowiedź = słucha
        return self.own_pid(name) is not None

    def _http(self, url: str) -> int | None:
        try:
            status, _ = self.deps.get(url, {})
        except OSError:
            return None
        return status

    def running(self, name: str) -> bool:
        return self.own_pid(name) is not None or (name in SERVICE_URLS and self.healthy(name))

    def wait(self, check: Callable[[], bool]) -> bool:
        for _ in range(self.deps.attempts):
            if check():
                return True
            self.deps.sleep(self.deps.interval)
        return False

    def start(self, name: str, argv: list[str], cwd: Path, env: Mapping[str, str]) -> None:
        self.logs.mkdir(mode=0o700, parents=True, exist_ok=True)
        log = self.logs / f"{name}.log"
        pid = self.deps.spawn(argv, cwd, env, log)
        files.write_private(self.pid_file(name), f"{pid}\n")
        self.out(f"{name}: uruchomiony (pid {pid})")
        if not self.wait(lambda: self.healthy(name)):
            self.fail(f"{name} nie odpowiada. Log: {log}")

    def stop(self, name: str) -> None:
        pid = self.own_pid(name)
        if pid is not None:
            self.deps.kill(pid)
            if not self.wait(lambda: not self.deps.alive(pid)):
                self.fail(f"{name} (pid {pid}) nie zakończył się.")
            self.out(f"{name}: zatrzymany")
        self.pid_file(name).unlink(missing_ok=True)

    def run_ok(self, argv: list[str], cwd: Path, env: Mapping[str, str] | None = None) -> str:
        code, output = self.deps.run(argv, cwd, self.deps.environ if env is None else env)
        if code != 0:
            self.fail(f"Polecenie {' '.join(argv[:3])} zakończyło się kodem {code}:", output.rstrip())
        return output

    # --- up ---

    def up(self) -> None:
        self.check_tools()
        if not self.load():
            self.ask_config()
        _, changed = files.ensure_env(self.env_path, random=self.deps.random, shipscope_env=self.shipscope_dotenv())
        if changed:
            self.out(f"Zapisano zmienne i sekrety w {self.env_path} (tryb 600)")
        self.postgres()
        self.github_app()
        self.npm_ci()
        self.shipscope()
        self.receiver()
        if not self.env().get("PDI_SHIPSCOPE_TOKEN"):
            self.connect()
        self.mcp_register()
        self.out(f"ShipScope: {SHIPSCOPE_URL}")
        self.out(f"pdi-receiver: {RECEIVER_URL} (formularz zgłoszenia: sdlc open)")
        self.out("gotowe")

    def check_tools(self) -> None:
        problems = [f"Brak {tool}: {install}" for tool, install in TOOLS.items() if not self.deps.which(tool)]
        root = self.deps.home
        if self.deps.which("gh") and self.deps.run(["gh", "auth", "status"], root, self.deps.environ)[0] != 0:
            problems.append("gh nie jest zalogowany: gh auth login")
        if self.deps.which("docker") and self.deps.run(["docker", "info"], root, self.deps.environ)[0] != 0:
            problems.append("Docker nie działa: uruchom Docker Desktop")
        if problems:
            self.fail(*problems)

    def postgres(self) -> None:
        home = self.deps.home
        state = self.run_ok(
            ["docker", "ps", "-a", "--filter", f"name=^/{PG_CONTAINER}$", "--format", "{{.State}}"], home
        ).strip()
        if not state:
            self.run_ok(
                [
                    "docker",
                    "run",
                    "-d",
                    "--name",
                    PG_CONTAINER,
                    "-e",
                    "POSTGRES_PASSWORD=postgres",
                    "-p",
                    f"127.0.0.1:{PG_PORT}:5432",
                    "-v",
                    f"{PG_CONTAINER}:/var/lib/postgresql/data",
                    PG_IMAGE,
                ],
                home,
            )
            self.out(f"Postgres: utworzony kontener {PG_CONTAINER}")
        elif state != "running":
            self.run_ok(["docker", "start", PG_CONTAINER], home)
            self.out(f"Postgres: uruchomiony kontener {PG_CONTAINER}")
        ready = ["docker", "exec", PG_CONTAINER, "pg_isready", "-U", "postgres"]
        if not self.wait(lambda: self.deps.run(ready, home, self.deps.environ)[0] == 0):
            self.fail(f"Postgres nie odpowiada. Sprawdź: docker logs {PG_CONTAINER}")
        psql = ["docker", "exec", PG_CONTAINER, "psql", "-U", "postgres"]
        self.run_ok([*psql, "-v", "ON_ERROR_STOP=1", "-c", CREATE_ROLE], home)
        exists = self.run_ok([*psql, "-tAc", "SELECT 1 FROM pg_database WHERE datname='shipscope'"], home)
        if not exists.strip():
            self.run_ok([*psql, "-c", "CREATE DATABASE shipscope OWNER shipscope_app"], home)

    def github_app(self) -> None:
        if all(self.shipscope_dotenv().get(name) for name in GITHUB_APP_VARS):
            return
        self.out("Jednorazowo: aplikacja GitHub ShipScope (klucze trafią do server/.env).")
        self.out(f"  1. W drugim terminalu: cd {self.server} && npm run dev")
        self.out(f"  2. Otwórz {SHIPSCOPE_URL} i kliknij „Create the GitHub App on GitHub”, potwierdź na GitHubie.")
        self.out("  3. Zatrzymaj npm run dev (Ctrl+C).")
        self.deps.ask("Naciśnij Enter, gdy aplikacja GitHub będzie gotowa.")
        if not all(self.shipscope_dotenv().get(name) for name in GITHUB_APP_VARS):
            self.fail(f"Nadal brak {' i '.join(GITHUB_APP_VARS)} w {self.server / '.env'}; uruchom sdlc up ponownie.")

    def npm_ci(self) -> None:
        for directory in (self.server, self.config.ci_for_sdlc):
            if not (directory / "node_modules").exists():
                self.out(f"npm ci w {directory}")
                self.run_ok(["npm", "ci"], directory)

    def shipscope(self) -> None:
        if not self.running(WEB):
            code, output = self.deps.run(["node", "scripts/migrate.js"], self.server, self.web_env())
            if code != 0:
                self.logs.mkdir(mode=0o700, parents=True, exist_ok=True)
                log = self.logs / "shipscope-migrate.log"
                files.write_private(log, output)
                self.fail(f"Migracje ShipScope nie przeszły (kod {code}). Log: {log}")
            self.start(WEB, ["node", "web.js"], self.server, self.web_env())
        if not self.running(WORKER):
            self.start(WORKER, ["node", "worker.js"], self.server, self.web_env())

    def receiver(self) -> None:
        if not self.running(RECEIVER):
            self.start_receiver()

    def start_receiver(self) -> None:
        argv = ["uv", "run", "--directory", str(self.config.pdi), "pdi-receiver"]
        self.start(RECEIVER, argv, self.config.pdi, self.pdi_env())

    def connect(self) -> None:
        env = {**self.web_env(), "SDLC_ADMIN_DATABASE_URL": ADMIN_DATABASE_URL, "SDLC_RECEIVER_URL": RECEIVER_URL}
        while True:
            code, output = self.deps.run(["node", "-e", connect.CONNECT_JS], self.server, env)
            if code != connect.NO_WORKSPACE:
                break
            self.out("Jednorazowo: przestrzeń w ShipScope.")
            self.out(f"  1. Otwórz {SHIPSCOPE_URL} i kliknij „Sign in with GitHub”.")
            self.out("  2. Załóż przestrzeń (workspace).")
            self.deps.ask("Naciśnij Enter, gdy przestrzeń będzie gotowa.")
        if code == connect.ALREADY_CONNECTED:
            self.fail(
                "Przestrzeń ShipScope jest już połączona z pdi, a tokenu nie da się odczytać ponownie.",
                f"Rozłącz ją w {SHIPSCOPE_URL} → Settings → Integrations → pdi → Disconnect",
                "i uruchom sdlc up ponownie.",
            )
        values = self._connect_values(output) if code == 0 else None
        if values is None:
            # Przy błędzie skrypt pisze na wyjście tylko komunikat błędu; wyjścia z sekretami (kod 0) nie wypisujemy.
            details = [] if code == 0 else [output.rstrip()]
            self.fail(f"Połączenie ShipScope ↔ pdi nie powiodło się (kod {code}).", *details)
        files.write_env(self.env_path, {**self.env(), **values})
        self.out(f"ShipScope ↔ pdi: połączono, zmienne {', '.join(files.SHIPSCOPE_VARS)} zapisane w {self.env_path}")
        if self.own_pid(RECEIVER) is None:
            self.out(f"{RECEIVER} działa poza sdlc: uruchom go ponownie, żeby wczytał nowe zmienne.")
            return
        self.stop(RECEIVER)
        self.start_receiver()

    @staticmethod
    def _connect_values(output: str) -> dict[str, str] | None:
        for line in output.splitlines():
            if line.startswith(connect.MARKER):
                try:
                    data = json.loads(line.removeprefix(connect.MARKER))
                except ValueError:
                    return None
                if isinstance(data, dict) and all(isinstance(data.get(n), str) for n in files.SHIPSCOPE_VARS):
                    return {n: data[n] for n in files.SHIPSCOPE_VARS}
        return None

    def mcp_register(self) -> None:
        pdi = str(self.config.pdi)
        for name in MCP_SERVERS:
            command = ["uv", "run", "--directory", pdi, "sdlc", "mcp", name]
            code, output = self.deps.run(["claude", "mcp", "get", name], self.deps.home, self.deps.environ)
            if code == 0 and " ".join(command[1:]) in output:
                continue
            self.deps.run(["claude", "mcp", "remove", "--scope", "user", name], self.deps.home, self.deps.environ)
            self.run_ok(["claude", "mcp", "add", "--scope", "user", name, "--", *command], self.deps.home)
            self.out(f"MCP {name}: zarejestrowany w Claude Code (sdlc mcp {name})")

    # --- status ---

    def status(self) -> None:
        home = self.deps.home
        code, state = self.deps.run(
            ["docker", "ps", "-a", "--filter", f"name=^/{PG_CONTAINER}$", "--format", "{{.State}}"],
            home,
            self.deps.environ,
        )
        self.out(f"Postgres: {'działa' if code == 0 and state.strip() == 'running' else 'zatrzymany'}")
        for name in SERVICES:
            url = SERVICE_URLS.get(name)
            pid = self.own_pid(name)
            if pid is not None:
                self.out(f"{name}: działa (pid {pid}{', ' + url if url else ''})")
            elif url and self.healthy(name):
                self.out(f"{name}: działa poza sdlc ({url})")
            else:
                self.out(f"{name}: zatrzymany")
        env = self.env()
        connection, problem = impact.read_connection(
            impact.ShipScopeConfig(env.get("PDI_SHIPSCOPE_URL") or None, env.get("PDI_SHIPSCOPE_TOKEN") or None),
            get=self.deps.get,
        )
        self.out(f"ShipScope ↔ pdi: {connection['state'] if connection else problem}")
        self.out(f"ci_for_sdlc → pdi: {self.ci_state()}")
        for name in files.SECRETS:
            self.out(f"{name}: {'ustawiony' if env.get(name) else 'brak'}")
        log = self.logs / f"{RECEIVER}.log"
        if log.exists():
            self.out(f"Ostatnie linie {log}:")
            for line in log.read_text(errors="replace").splitlines()[-5:]:
                self.out(f"  {line}")
        self.out(f"skrzynka pdi: {self.inbox_count()}")

    def ci_state(self) -> str:
        try:
            outbox = json.loads((self.ci_data / "pdi-outbox.json").read_text())
        except (OSError, ValueError):
            outbox = []
        try:
            state = json.loads((self.ci_data / "pdi-state.json").read_text())
        except (OSError, ValueError):
            state = {}
        entries = [e for e in outbox if isinstance(e, dict)] if isinstance(outbox, list) else []
        failed = [e for e in entries if e.get("failed")]
        if failed:
            return f"błąd ({failed[-1]['failed']}); sprawdź PDI_CI_FOR_SDLC_SIGNING_SECRET i odbiornik"
        if entries:
            return f"w kolejce {len(entries)} ({entries[-1].get('lastError') or 'czeka na wysyłkę'})"
        if isinstance(state, dict) and state.get("sent"):
            return "connected"
        return "nic jeszcze nie wysłano (sdlc check)"

    def inbox_count(self) -> str:
        try:
            from pdi.inbox import Inbox
            from pdi.registry import Registry

            return f"{len(Inbox(Registry(self.config.registry)).items())} otwartych"
        except Exception as e:  # noqa: BLE001 — status ma się wypisać mimo błędu rejestru
            return f"nie udało się odczytać ({e})"

    # --- pozostałe polecenia ---

    def open(self) -> None:
        token = self.env().get("PDI_FORM_TOKEN")
        if not token:
            self.fail("Brak PDI_FORM_TOKEN w ~/.sdlc/env; uruchom sdlc up.")
        self.deps.open_url(SHIPSCOPE_URL)
        # Token formularza nie trafia do argv przeglądarki: strona w pliku 600 przekierowuje na formularz.
        url = f"{RECEIVER_URL}/problems/new?t={urllib.parse.quote(token, safe='')}"
        page = self.runs / "form.html"
        files.write_private(
            page,
            f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url={html.escape(url)}">'
            "<title>pdi</title>\n",
        )
        self.deps.open_url(f"file://{page}")
        self.out(f"Otwarto {SHIPSCOPE_URL} i formularz zgłoszenia pdi.")

    def mcp(self, name: str) -> int:
        if name == "shipscope":
            env = self.env()
            url, token = env.get("PDI_SHIPSCOPE_URL"), env.get("PDI_SHIPSCOPE_TOKEN")
            if not (url and token):
                self.deps.err("Brak PDI_SHIPSCOPE_URL albo PDI_SHIPSCOPE_TOKEN w ~/.sdlc/env; uruchom sdlc up.")
                return 1
            script = self.config.shipscope / "adapters" / "mcp" / "shipscope-mcp.js"
            self.deps.exec(["node", str(script)], {**self.deps.environ, "SHIPSCOPE_URL": url, "SHIPSCOPE_TOKEN": token})
            return 0
        if name == "pdi":
            self.deps.exec([str(Path(sys.executable).parent / "pdi-mcp")], self.pdi_env())
            return 0
        self.deps.err("Użycie: sdlc mcp <pdi|shipscope>")
        return 2

    def deploy(self, target: str, repo: str | None) -> None:
        environment = {"prod": "production", "test": "test"}[target]
        if repo is None:
            if self.config.checkout is None:
                self.fail("Brak klonu produktu w konfiguracji: podaj --repo owner/nazwa.")
            view = ["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"]
            repo = self.run_ok(view, self.config.checkout).strip()
        cwd = self.config.checkout or self.deps.home
        sha = self.run_ok(["gh", "api", f"repos/{repo}/commits/main", "--jq", ".sha"], cwd).strip()
        deployment = self.run_ok(
            [
                "gh",
                "api",
                "--method",
                "POST",
                f"repos/{repo}/deployments",
                "-f",
                f"ref={sha}",
                "-f",
                f"environment={environment}",
                "-f",
                "description=sdlc deploy",
                "-F",
                "auto_merge=false",
                "-F",
                "required_contexts[]",
                "--jq",
                ".id",
            ],
            cwd,
        ).strip()
        status = ["gh", "api", "--method", "POST", f"repos/{repo}/deployments/{deployment}/statuses"]
        self.run_ok([*status, "-f", "state=success", "--jq", ".state"], cwd)
        self.out(f"Deployment {deployment}: {repo} main@{sha} → {environment} (success)")

    def down(self) -> None:
        for name in SERVICES:
            self.stop(name)
        code, output = self.deps.run(["docker", "stop", PG_CONTAINER], self.deps.home, self.deps.environ)
        self.out("Postgres: zatrzymany (dane zostają)" if code == 0 else f"docker stop: {output.strip()}")

    def reset(self) -> None:
        answer = self.deps.ask(
            f"Reset usunie bazę ShipScope (kontener i wolumen {PG_CONTAINER}), ~/.sdlc/ci-data, logs i run oraz "
            f"połączenie z pdi. Wpisz {PG_CONTAINER}, żeby potwierdzić: "
        )
        if answer.strip() != PG_CONTAINER:
            self.fail("Przerwano: nic nie zostało usunięte.")
        self.down()
        self.deps.run(["docker", "rm", "-f", PG_CONTAINER], self.deps.home, self.deps.environ)
        self.deps.run(["docker", "volume", "rm", PG_CONTAINER], self.deps.home, self.deps.environ)
        for directory in (self.ci_data, self.logs, self.runs):
            shutil.rmtree(directory, ignore_errors=True)
        env = self.env()
        if self.env_path.exists():
            files.write_env(self.env_path, {k: v for k, v in env.items() if k not in files.SHIPSCOPE_VARS})
        self.out("Usunięto dane; sekrety w ~/.sdlc/env zostały (bez połączenia ShipScope ↔ pdi).")

    def check(self, repo: str | None) -> int:
        env = self.env()
        secret = env.get("PDI_CI_FOR_SDLC_SIGNING_SECRET")
        if not secret:
            self.fail("Brak PDI_CI_FOR_SDLC_SIGNING_SECRET w ~/.sdlc/env; uruchom sdlc up.")
        path = repo or (str(self.config.checkout) if self.config.checkout else None)
        if not path:
            self.fail("Podaj --repo ścieżka (albo ustaw klon produktu w ~/.sdlc/config.toml).")
        self.ci_data.mkdir(mode=0o700, parents=True, exist_ok=True)
        code, output = self.deps.run(
            ["npm", "run", "analyze", "--", "--repo", path, "--send-to-pdi"],
            self.config.ci_for_sdlc,
            {
                **self.deps.environ,
                "PDI_EVENTS_URL": env.get("PDI_EVENTS_URL", files.CONSTANTS["PDI_EVENTS_URL"]),
                "PDI_SIGNING_SECRET": secret,
                "CI_DATA_DIR": str(self.ci_data),
            },
        )
        self.out(output.rstrip())
        return code


def run(argv: list[str], deps: Deps) -> int:
    stack = Stack(deps)
    command, args = (argv[0], argv[1:]) if argv else ("", [])
    try:
        if command == "up" and not args:
            stack.up()
            return 0
        if command not in ("status", "deploy", "open", "down", "reset", "check", "mcp"):
            deps.out(USAGE)
            return 2
        if not stack.load():
            (deps.err if command == "mcp" else deps.out)("Brak ~/.sdlc/config.toml: uruchom najpierw sdlc up.")
            return 1
        if command == "mcp" and len(args) == 1:
            return stack.mcp(args[0])
        if command == "deploy" and args[:1] in (["prod"], ["test"]):
            valid, repo = _option(args[1:], "--repo")
            if valid:
                stack.deploy(args[0], repo)
                return 0
        if command == "check":
            valid, repo = _option(args, "--repo")
            if valid:
                return stack.check(repo)
        if not args and command in ("status", "open", "down", "reset"):
            getattr(stack, command)()
            return 0
        deps.out(USAGE)
        return 2
    except Stop as stop:
        return stop.code


def _option(args: list[str], name: str) -> tuple[bool, str | None]:
    """(czy argumenty to co najwyżej jedna opcja `name` z wartością, jej wartość albo `None`)."""
    if not args:
        return True, None
    if len(args) == 2 and args[0] == name:
        return True, args[1]
    return False, None


# --- prawdziwy świat ---


def _run(argv: list[str], cwd: Path, env: Mapping[str, str]) -> tuple[int, str]:
    try:
        done = subprocess.run(  # noqa: S603 — argv bez powłoki, sekrety tylko w env
            argv, cwd=cwd, env=dict(env), capture_output=True, text=True, check=False
        )
    except FileNotFoundError as e:
        return 127, str(e)
    return done.returncode, done.stdout + done.stderr


def _spawn(argv: list[str], cwd: Path, env: Mapping[str, str], log: Path) -> int:
    fd = os.open(log, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        process = subprocess.Popen(  # noqa: S603 — argv bez powłoki, sekrety tylko w env
            argv,
            cwd=cwd,
            env=dict(env),
            stdin=subprocess.DEVNULL,
            stdout=fd,
            stderr=fd,
            start_new_session=True,
        )
    finally:
        os.close(fd)
    return process.pid


def _get(url: str, headers: dict[str, str]) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers=headers)  # noqa: S310 — adresy localhost z kodu sdlc
    try:
        with urllib.request.urlopen(request, timeout=2) as response:  # noqa: S310 — jw.
            return int(response.status), response.read()
    except urllib.error.HTTPError as e:
        return e.code, b""


def _alive(pid: int) -> bool:
    with contextlib.suppress(ChildProcessError):
        os.waitpid(pid, os.WNOHANG)  # sprząta zombie własnego dziecka
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _kill(pid: int) -> None:
    with contextlib.suppress(ProcessLookupError):
        os.killpg(pid, signal.SIGTERM)  # grupa: `uv run` i `node` razem z dziećmi


def _exec(argv: list[str], env: Mapping[str, str]) -> None:
    os.execvpe(argv[0], argv, dict(env))  # noqa: S606 — zastępuje proces `sdlc mcp` serwerem MCP


def main() -> None:
    deps = Deps(
        home=Path.home(),
        pdi_root=Path(__file__).resolve().parents[3],
        run=_run,
        spawn=_spawn,
        get=_get,
        alive=_alive,
        kill=_kill,
        ask=input,
        out=print,
        which=shutil.which,
        open_url=lambda url: None if webbrowser.open(url) else print(f"Otwórz: {url}"),
        sleep=__import__("time").sleep,
        exec=_exec,
        environ=dict(os.environ),
        random=os.urandom,
    )
    try:
        sys.exit(run(sys.argv[1:], deps))
    except (KeyboardInterrupt, EOFError):
        print("\nPrzerwano.", file=sys.stderr)
        sys.exit(130)
