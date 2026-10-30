import json
import re
import stat
from collections.abc import Mapping
from pathlib import Path

import pytest

from pdi.stack import cli, files

KEY_RE = r"^[A-Za-z0-9+/]{43}=$"
SHIPSCOPE_ENV = {
    "PDI_SHIPSCOPE_URL": "http://localhost:3000",
    "PDI_SHIPSCOPE_TOKEN": "shps_tajny_token_uslugi",
    "PDI_SHIPSCOPE_SIGNING_SECRET": "tajny_sekret_podpisu_shipscope",
}
GITHUB_APP = "GITHUB_APP_CLIENT_ID=Iv1.abc\nGITHUB_APP_CLIENT_SECRET=tajny_sekret_aplikacji\n"


class World:
    """Podstawiony świat: polecenia, procesy w tle, HTTP i klawiatura; zapisuje kolejność zdarzeń."""

    def __init__(self, tmp_path: Path) -> None:
        self.home = tmp_path / "home"
        self.home.mkdir()
        self.code = tmp_path / "code"
        for name in ("pdi", "evdt-service-shipscope/server", "ci_for_sdlc", "pdi-decisions"):
            (self.code / name).mkdir(parents=True)
        self.server = self.code / "evdt-service-shipscope" / "server"
        (self.server / ".env").write_text(GITHUB_APP)
        (self.server / "node_modules").mkdir()
        (self.code / "ci_for_sdlc" / "node_modules").mkdir()
        self.events: list[str] = []
        self.calls: list[list[str]] = []
        self.envs: list[dict[str, str]] = []
        self.output: list[str] = []
        self.answers: list[str] = []
        self.opened: list[str] = []
        self.execs: list[tuple[list[str], dict[str, str]]] = []
        self.up: set[str] = set()  # adresy, które odpowiadają
        self.pids: dict[int, str] = {}
        self.next_pid = 100
        self.missing: set[str] = set()
        self.pg_state = ""
        self.connect: tuple[int, str] = (0, "SDLC_ENV " + json.dumps(SHIPSCOPE_ENV) + "\n")
        self.responses: dict[str, tuple[int, str]] = {}
        self.mcp: dict[str, list[str]] = {}  # rejestr serwerów MCP podstawionego `claude`
        self.connection = {"workspace": {"id": "t1", "name": "Moja"}, "pdi": {"state": "connected"}}

    # --- zależności ---

    def run(self, argv: list[str], cwd: Path, env: Mapping[str, str]) -> tuple[int, str]:
        assert all(isinstance(a, str) for a in argv)
        self.calls.append(argv)
        self.envs.append(dict(env))
        line = " ".join(argv)
        self.events.append(f"run {line[:60]}")
        for prefix in sorted(self.responses, key=len, reverse=True):
            if line.startswith(prefix):
                return self.responses[prefix]
        if line.startswith("docker ps"):
            return 0, self.pg_state + "\n"
        if line.startswith(("docker run", "docker start")):
            self.pg_state = "running"
        if line.startswith("docker stop"):
            self.pg_state = "exited"
        if line.startswith("node -e"):
            return self.connect
        if argv[:3] == ["claude", "mcp", "get"]:
            args = self.mcp.get(argv[3])
            return (0, f"{argv[3]}:\n  Command: {args[0]}\n  Args: {' '.join(args[1:])}\n") if args else (1, "")
        if argv[:3] == ["claude", "mcp", "add"]:
            self.mcp[argv[5]] = argv[argv.index("--") + 1 :]
        if argv[:3] == ["claude", "mcp", "remove"]:
            return (0, "") if self.mcp.pop(argv[5], None) else (1, "")
        return 0, ""

    def spawn(self, argv: list[str], cwd: Path, env: Mapping[str, str], log: Path) -> int:
        assert all(isinstance(a, str) for a in argv)
        self.calls.append(argv)
        self.envs.append(dict(env))
        name = log.stem
        self.events.append(f"spawn {name}")
        pid = self.next_pid
        self.next_pid += 1
        self.pids[pid] = name
        self.up.add({"shipscope-web": "3000", "pdi-receiver": "8787"}.get(name, name))
        log.write_text(f"{name}: start\n")
        return pid

    def get(self, url: str, headers: dict[str, str]) -> tuple[int, bytes]:
        self.events.append(f"get {url}")
        if "/api/service/v1/connection" in url:
            return 200, json.dumps(self.connection).encode()
        if ":3000" in url and "3000" in self.up:
            return 200, b'{"status":"ok"}'
        if ":8787" in url and "8787" in self.up:
            return 405, b""
        raise ConnectionRefusedError(url)

    def alive(self, pid: int) -> bool:
        return pid in self.pids

    def kill(self, pid: int) -> None:
        name = self.pids.pop(pid)
        self.events.append(f"kill {name}")
        self.up.discard({"shipscope-web": "3000", "pdi-receiver": "8787"}.get(name, name))

    def ask(self, prompt: str) -> str:
        self.output.append(prompt)
        return self.answers.pop(0) if self.answers else ""

    def exec(self, argv: list[str], env: Mapping[str, str]) -> None:
        self.execs.append((argv, dict(env)))

    def deps(self) -> cli.Deps:
        return cli.Deps(
            home=self.home,
            pdi_root=self.code / "pdi",
            run=self.run,
            spawn=self.spawn,
            get=self.get,
            alive=self.alive,
            kill=self.kill,
            ask=self.ask,
            out=self.output.append,
            which=lambda tool: None if tool in self.missing else f"/usr/bin/{tool}",
            open_url=self.opened.append,
            sleep=lambda _s: None,
            exec=self.exec,
            environ={"PATH": "/usr/bin", "HOME": str(self.home)},
            random=lambda n: bytes(range(n)),
        )

    # --- pomocnicze ---

    def main(self, *argv: str) -> int:
        return cli.run(list(argv), self.deps())

    def configured(self) -> None:
        sdlc = self.home / ".sdlc"
        sdlc.mkdir(mode=0o700, exist_ok=True)
        files.save_config(
            sdlc / "config.toml",
            files.Config(
                pdi=self.code / "pdi",
                shipscope=self.code / "evdt-service-shipscope",
                ci_for_sdlc=self.code / "ci_for_sdlc",
                registry=self.code / "pdi-decisions",
                checkout=self.code / "sklep",
            ),
        )

    def env(self) -> dict[str, str]:
        return files.read_env(self.home / ".sdlc" / "env")

    def text(self) -> str:
        return "\n".join(self.output)


@pytest.fixture
def world(tmp_path: Path) -> World:
    return World(tmp_path)


def secrets(env: dict[str, str]) -> list[str]:
    names = [n for n in files.SECRETS if env.get(n)]
    return [env[n] for n in names] + [SHIPSCOPE_ENV["PDI_SHIPSCOPE_TOKEN"], "tajny_sekret_aplikacji"]


# --- pliki ---


def test_env_written_atomically_with_mode_600_in_dir_700(tmp_path: Path) -> None:
    path = tmp_path / ".sdlc" / "env"
    files.write_env(path, {"A": "1", "B": "dwa"})
    assert files.read_env(path) == {"A": "1", "B": "dwa"}
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert sorted(p.name for p in path.parent.iterdir()) == ["env"]  # bez pliku tymczasowego


def test_env_refuses_newline_in_value(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="B"):
        files.write_env(tmp_path / "env", {"B": "a\nC=1"})


def test_secrets_generated_once_and_never_overwritten(tmp_path: Path) -> None:
    path = tmp_path / ".sdlc" / "env"
    files.write_env(path, {"PDI_FORM_TOKEN": "moj-token", "PDI_PHASE_BUDGET_USD": "5"})
    values, changed = files.ensure_env(path, random=lambda n: b"\x01" * n, shipscope_env={})
    assert changed
    assert values["PDI_FORM_TOKEN"] == "moj-token"  # noqa: S105 — wartość testowa
    assert values["PDI_PHASE_BUDGET_USD"] == "5"
    assert values["PDI_EVENTS_URL"] == "http://127.0.0.1:8787"
    assert values["PDI_DISPATCH"] == "local"
    assert len(values["PDI_TF_SIGNING_SECRET"]) == 64
    assert re.match(KEY_RE, values["TOKEN_ENCRYPTION_KEY"])
    again, changed = files.ensure_env(path, random=lambda n: b"\x02" * n, shipscope_env={})
    assert not changed
    assert again == values


def test_encryption_key_adopted_from_shipscope_env(tmp_path: Path) -> None:
    key = "A" * 43 + "="
    values, _ = files.ensure_env(tmp_path / "env", random=bytes, shipscope_env={"TOKEN_ENCRYPTION_KEY": key})
    assert values["TOKEN_ENCRYPTION_KEY"] == key


def test_config_round_trip(tmp_path: Path) -> None:
    config = files.Config(
        pdi=tmp_path / "pdi", shipscope=tmp_path / "s s", ci_for_sdlc=tmp_path / 'c"i', registry=tmp_path / "r"
    )
    files.save_config(tmp_path / "config.toml", config)
    assert files.load_config(tmp_path / "config.toml") == config


# --- up ---


def test_missing_tools_reported_with_install_commands(world: World) -> None:
    world.missing = {"docker", "uv"}
    world.responses["gh auth status"] = (1, "not logged in")
    assert world.main("up") == 1
    text = world.text()
    assert "brew install --cask docker" in text
    assert "brew install uv" in text
    assert "gh auth login" in text
    assert "brew install gh" not in text
    assert not any(e.startswith("spawn") for e in world.events)


def test_first_up_asks_for_paths_once_and_writes_config(world: World) -> None:
    world.answers = [str(world.code), "", ""]  # katalog z klonami, rejestr domyślny, bez klonu produktu
    assert world.main("up") == 0, world.text()
    config = files.load_config(world.home / ".sdlc" / "config.toml")
    assert config.shipscope == world.code / "evdt-service-shipscope"
    assert config.registry == world.code / "pdi-decisions"
    assert config.checkout is None
    asked = len([o for o in world.output if o.endswith(": ")])
    world.output.clear()
    assert world.main("up") == 0
    assert not [o for o in world.output if o.endswith(": ")]
    assert asked == 3


def test_up_starts_in_order_with_health_checks(world: World) -> None:
    world.configured()
    assert world.main("up") == 0, world.text()
    order = [
        e
        for e in world.events
        if e.startswith(("spawn", "kill"))
        or e.startswith("run docker run")
        or e.startswith("run docker exec shipscope-dev-pg pg_isready")
        or e.startswith("run node scripts/migrate.js")
        or e.startswith("run node -e")
        or e.startswith("run claude mcp add")
    ]
    pdi = str(world.code / "pdi")
    expected = [
        "run docker run -d --name shipscope-dev-pg",
        "run docker exec shipscope-dev-pg pg_isready -U postgres",
        "run node scripts/migrate.js",
        "spawn shipscope-web",
        "spawn shipscope-worker",
        "spawn pdi-receiver",
        "run node -e ",
        "kill pdi-receiver",
        "spawn pdi-receiver",
        f"run claude mcp add --scope user pdi -- uv run --directory {pdi}"[:64],
        f"run claude mcp add --scope user shipscope -- uv run --directory {pdi}"[:64],
    ]
    assert len(order) == len(expected), order
    assert all(e.startswith(x) for e, x in zip(order, expected, strict=True)), order
    web = world.events.index("spawn shipscope-web")
    assert "get http://localhost:3000/health" in world.events[web:]
    assert world.output[-1] == "gotowe"
    assert "http://localhost:3000" in world.text()
    assert "http://127.0.0.1:8787" in world.text()


def test_up_shipscope_env_overrides_database_and_key(world: World) -> None:
    world.configured()
    assert world.main("up") == 0
    i = world.calls.index(["node", "web.js"])
    env = world.envs[i]
    assert env["DATABASE_URL"] == "postgres://shipscope_app:shipscope_app@localhost:54329/shipscope"
    assert env["DATABASE_SSL"] == "false"
    assert env["PUBLIC_BASE_URL"] == "http://localhost:3000"
    assert env["GITHUB_APP_CLIENT_ID"] == "Iv1.abc"
    assert env["TOKEN_ENCRYPTION_KEY"] == world.env()["TOKEN_ENCRYPTION_KEY"]
    assert "PDI_TF_SIGNING_SECRET" not in env


def test_receiver_gets_env_file_and_registry(world: World) -> None:
    world.configured()
    assert world.main("up") == 0
    i = max(i for i, a in enumerate(world.calls) if a[-1:] == ["pdi-receiver"])
    env = world.envs[i]
    assert env["PDI_REGISTRY_PATH"] == str(world.code / "pdi-decisions")
    assert env["PDI_DISPATCH_CHECKOUT"] == str(world.code / "sklep")
    assert env["PDI_SHIPSCOPE_TOKEN"] == SHIPSCOPE_ENV["PDI_SHIPSCOPE_TOKEN"]
    assert env["PDI_FORM_TOKEN"] == world.env()["PDI_FORM_TOKEN"]


def test_connection_step_writes_three_variables(world: World) -> None:
    world.configured()
    assert world.main("up") == 0
    env = world.env()
    for name, value in SHIPSCOPE_ENV.items():
        assert env[name] == value
    i = next(i for i, a in enumerate(world.calls) if a[:2] == ["node", "-e"])
    assert world.envs[i]["SDLC_RECEIVER_URL"] == "http://127.0.0.1:8787"
    assert world.envs[i]["SDLC_ADMIN_DATABASE_URL"].startswith("postgres://postgres:")
    assert stat.S_IMODE((world.home / ".sdlc" / "env").stat().st_mode) == 0o600


def test_connection_waits_for_workspace_then_retries(world: World) -> None:
    world.configured()
    results = [(3, ""), world.connect]
    world.responses = {}
    original = world.run

    def run(argv: list[str], cwd: Path, env: Mapping[str, str]) -> tuple[int, str]:
        if argv[:2] == ["node", "-e"]:
            original(argv, cwd, env)
            return results.pop(0)
        return original(argv, cwd, env)

    world.run = run  # type: ignore[method-assign]
    assert world.main("up") == 0, world.text()
    assert "Sign in with GitHub" in world.text() or "zaloguj" in world.text().lower()
    assert world.env()["PDI_SHIPSCOPE_TOKEN"] == SHIPSCOPE_ENV["PDI_SHIPSCOPE_TOKEN"]


def test_connection_already_connected_explains_disconnect(world: World) -> None:
    world.configured()
    world.connect = (4, "")
    assert world.main("up") == 1
    assert "Disconnect" in world.text()
    assert "PDI_SHIPSCOPE_TOKEN" not in world.env()


def test_github_app_missing_waits_for_one_time_step(world: World) -> None:
    world.configured()
    (world.server / ".env").write_text("")
    original = world.ask

    def ask(prompt: str) -> str:
        (world.server / ".env").write_text(GITHUB_APP)
        return original(prompt)

    world.ask = ask  # type: ignore[method-assign]
    assert world.main("up") == 0, world.text()
    assert "npm run dev" in world.text()
    assert "Create the GitHub App" in world.text()


def test_health_timeout_points_to_log(world: World) -> None:
    world.configured()
    original = world.spawn

    def spawn(argv: list[str], cwd: Path, env: Mapping[str, str], log: Path) -> int:
        pid = original(argv, cwd, env, log)
        world.up.discard("3000")
        return pid

    world.spawn = spawn  # type: ignore[method-assign]
    assert world.main("up") == 1
    assert str(world.home / ".sdlc" / "logs" / "shipscope-web.log") in world.text()
    assert "gotowe" not in world.output


def test_second_up_changes_nothing(world: World) -> None:
    world.configured()
    assert world.main("up") == 0
    env_before = (world.home / ".sdlc" / "env").read_text()
    world.events.clear()
    assert world.main("up") == 0
    assert not [e for e in world.events if e.startswith(("spawn", "kill"))]
    assert not [
        e
        for e in world.events
        if e.startswith(("run docker run", "run docker start", "run node", "run claude mcp add"))
    ]
    assert (world.home / ".sdlc" / "env").read_text() == env_before
    assert world.output[-1] == "gotowe"


def test_up_restarts_only_what_stopped(world: World) -> None:
    world.configured()
    assert world.main("up") == 0
    receiver = next(p for p, n in world.pids.items() if n == "pdi-receiver")
    world.kill(receiver)
    world.events.clear()
    assert world.main("up") == 0
    assert [e for e in world.events if e.startswith("spawn")] == ["spawn pdi-receiver"]


def test_mcp_registration_replaces(world: World) -> None:
    world.configured()
    assert world.main("up") == 0
    pdi = str(world.code / "pdi")
    for name in ("pdi", "shipscope"):
        remove = ["claude", "mcp", "remove", "--scope", "user", name]
        add = [
            "claude",
            "mcp",
            "add",
            "--scope",
            "user",
            name,
            "--",
            "uv",
            "run",
            "--directory",
            pdi,
            "sdlc",
            "mcp",
            name,
        ]
        assert remove in world.calls
        assert world.calls.index(remove) < world.calls.index(add)


def test_no_secret_in_argv_output_or_logs(world: World) -> None:
    world.configured()
    assert world.main("up") == 0
    assert world.main("status") == 0
    assert world.main("open") == 0
    values = secrets(world.env())
    assert len(values) >= 8
    logs = "".join(p.read_text() for p in (world.home / ".sdlc" / "logs").glob("*"))
    for value in values:
        for argv in world.calls:
            assert all(value not in a for a in argv), argv
        assert value not in world.text()
        assert value not in logs
        assert all(value not in u for u in world.opened)


# --- status, open, mcp ---


def test_status_shows_processes_connections_and_secret_presence_only(world: World) -> None:
    world.configured()
    assert world.main("up") == 0
    data = world.home / ".sdlc" / "ci-data"
    data.mkdir()
    (data / "pdi-state.json").write_text(json.dumps({"sent": {"CHG-1": "ready"}, "seen": []}))
    (data / "pdi-outbox.json").write_text("[]")
    world.output.clear()
    assert world.main("status") == 0
    text = world.text()
    assert "shipscope-web: działa" in text
    assert "pdi-receiver: działa" in text
    assert "Postgres: działa" in text
    assert "ShipScope ↔ pdi: connected" in text
    assert "ci_for_sdlc → pdi: connected" in text
    assert "PDI_SHIPSCOPE_TOKEN: ustawiony" in text
    assert "pdi-receiver: start" in text  # ostatnie linie logu odbiornika
    assert "skrzynka pdi: 0 otwartych" in text


def test_status_ci_queue_and_failure(world: World) -> None:
    world.configured()
    data = world.home / ".sdlc" / "ci-data"
    data.mkdir(parents=True)
    (data / "pdi-state.json").write_text(json.dumps({"sent": {}, "seen": []}))
    outbox = [{"event": {}, "attempts": 2, "nextAt": "2026-10-30T10:00:00Z", "lastError": "ECONNREFUSED"}]
    (data / "pdi-outbox.json").write_text(json.dumps(outbox))
    assert world.main("status") == 0
    assert "ci_for_sdlc → pdi: w kolejce 1" in world.text()
    assert "ECONNREFUSED" in world.text()


def test_open_uses_file_not_token_in_argv(world: World) -> None:
    world.configured()
    files.write_env(world.home / ".sdlc" / "env", {"PDI_FORM_TOKEN": "tajny-formularz"})
    assert world.main("open") == 0
    assert world.opened[0] == "http://localhost:3000"
    page = Path(world.opened[1].removeprefix("file://"))
    assert "tajny-formularz" in page.read_text()
    assert "tajny-formularz" not in world.opened[1]
    assert stat.S_IMODE(page.stat().st_mode) == 0o600


def test_mcp_shipscope_maps_variables_through_env(world: World) -> None:
    world.configured()
    files.write_env(world.home / ".sdlc" / "env", dict(SHIPSCOPE_ENV))
    assert world.main("mcp", "shipscope") == 0
    argv, env = world.execs[0]
    assert argv == ["node", str(world.code / "evdt-service-shipscope" / "adapters" / "mcp" / "shipscope-mcp.js")]
    assert env["SHIPSCOPE_URL"] == "http://localhost:3000"
    assert env["SHIPSCOPE_TOKEN"] == SHIPSCOPE_ENV["PDI_SHIPSCOPE_TOKEN"]
    assert world.output == []  # stdout należy do protokołu MCP


def test_mcp_pdi_gets_env_and_registry(world: World) -> None:
    world.configured()
    files.write_env(world.home / ".sdlc" / "env", dict(SHIPSCOPE_ENV))
    assert world.main("mcp", "pdi") == 0
    argv, env = world.execs[0]
    assert argv[-1].endswith("pdi-mcp")
    assert env["PDI_REGISTRY_PATH"] == str(world.code / "pdi-decisions")
    assert env["PDI_SHIPSCOPE_TOKEN"] == SHIPSCOPE_ENV["PDI_SHIPSCOPE_TOKEN"]


# --- deploy ---


@pytest.mark.parametrize(("target", "environment"), [("prod", "production"), ("test", "test")])
def test_deploy_exact_gh_api_calls(world: World, target: str, environment: str) -> None:
    world.configured()
    world.responses = {
        "gh api repos/dbqm45/sklep/commits/main": (0, "abc123\n"),
        "gh api --method POST repos/dbqm45/sklep/deployments ": (0, "42\n"),
        "gh api --method POST repos/dbqm45/sklep/deployments/42/statuses": (0, "success\n"),
    }
    assert world.main("deploy", target, "--repo", "dbqm45/sklep") == 0, world.text()
    assert world.calls == [
        ["gh", "api", "repos/dbqm45/sklep/commits/main", "--jq", ".sha"],
        [
            "gh",
            "api",
            "--method",
            "POST",
            "repos/dbqm45/sklep/deployments",
            "-f",
            "ref=abc123",
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
        [
            "gh",
            "api",
            "--method",
            "POST",
            "repos/dbqm45/sklep/deployments/42/statuses",
            "-f",
            "state=success",
            "--jq",
            ".state",
        ],
    ]
    assert "42" in world.text()
    assert "abc123" in world.text()


def test_deploy_repo_from_checkout(world: World) -> None:
    world.configured()
    world.responses = {
        "gh repo view": (0, "dbqm45/sklep\n"),
        "gh api repos/dbqm45/sklep/commits/main": (0, "abc123\n"),
        "gh api --method POST repos/dbqm45/sklep/deployments ": (0, "7\n"),
    }
    assert world.main("deploy", "test") == 0
    assert world.calls[0] == ["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"]


def test_deploy_failure_exits_1(world: World) -> None:
    world.configured()
    world.responses = {"gh api repos/x/y/commits/main": (1, "HTTP 404")}
    assert world.main("deploy", "prod", "--repo", "x/y") == 1
    assert "HTTP 404" in world.text()


# --- down, reset ---


def test_down_stops_processes_and_keeps_volume(world: World) -> None:
    world.configured()
    assert world.main("up") == 0
    world.calls.clear()
    assert world.main("down") == 0
    assert world.pids == {}
    assert ["docker", "stop", "shipscope-dev-pg"] in world.calls
    assert not [c for c in world.calls if c[:2] in (["docker", "rm"], ["docker", "volume"])]
    assert not list((world.home / ".sdlc" / "run").glob("*.pid"))


def test_reset_refuses_without_typed_name(world: World) -> None:
    world.configured()
    files.write_env(world.home / ".sdlc" / "env", dict(SHIPSCOPE_ENV))
    world.answers = ["tak"]
    assert world.main("reset") == 1
    assert not [c for c in world.calls if c[:2] in (["docker", "rm"], ["docker", "volume"])]
    assert world.env()["PDI_SHIPSCOPE_TOKEN"]


def test_reset_with_typed_name_deletes_data(world: World) -> None:
    world.configured()
    files.write_env(world.home / ".sdlc" / "env", {**SHIPSCOPE_ENV, "PDI_FORM_TOKEN": "zostaje"})
    world.answers = ["shipscope-dev-pg"]
    assert world.main("reset") == 0
    assert ["docker", "rm", "-f", "shipscope-dev-pg"] in world.calls
    assert ["docker", "volume", "rm", "shipscope-dev-pg"] in world.calls
    assert world.env() == {"PDI_FORM_TOKEN": "zostaje"}


# --- check ---


def test_check_runs_ci_for_sdlc_with_secret_in_env(world: World) -> None:
    world.configured()
    files.write_env(world.home / ".sdlc" / "env", {"PDI_CI_FOR_SDLC_SIGNING_SECRET": "tajny-ci"})
    world.responses = {
        "npm run analyze": (0, "pdi: http://127.0.0.1:8787\n  pdi readiness.changed CHG-1 ready delivered\n")
    }
    assert world.main("check", "--repo", "/srv/repo") == 0
    assert world.calls == [["npm", "run", "analyze", "--", "--repo", "/srv/repo", "--send-to-pdi"]]
    env = world.envs[0]
    assert env["PDI_SIGNING_SECRET"] == "tajny-ci"  # noqa: S105 — wartość testowa
    assert env["PDI_EVENTS_URL"] == "http://127.0.0.1:8787"
    assert env["CI_DATA_DIR"] == str(world.home / ".sdlc" / "ci-data")
    assert "delivered" in world.text()


def test_commands_need_config_except_up(world: World) -> None:
    assert world.main("status") == 1
    assert "sdlc up" in world.text()
