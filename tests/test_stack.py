"""`sdlc` (L4): cały stos lokalnie jednym poleceniem. Bez prawdziwego Dockera, sieci i procesów — podstawiony świat.
Plan: docs/plan-l4-sdlc.md."""

import json
import os
import stat
import subprocess
import sys
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from pdi.stack import cli, home

TOKEN = "shps_tajny_token_uslugi"  # noqa: S105 — token testowy
SIGNING = "sekret-podpisu-shipscope"  # noqa: S105 — sekret testowy
CONNECTED = {
    "workspace": {"id": "t1", "name": "Lokalnie"},
    "connection": {"state": "pending", "receiverUrl": "http://127.0.0.1:8787"},
    "env": {
        "PDI_SHIPSCOPE_URL": "http://localhost:3000",
        "PDI_SHIPSCOPE_TOKEN": TOKEN,
        "PDI_SHIPSCOPE_SIGNING_SECRET": SIGNING,
    },
}


class World:
    """Podstawiony komputer: narzędzia, polecenia, procesy, HTTP i zegar."""

    def __init__(self, tmp_path: Path) -> None:
        self.home = tmp_path / "dom"
        self.home.mkdir()
        self.projects = tmp_path / "projekty"
        for name in ("pdi", "evdt-service-shipscope/server/scripts", "ci_for_sdlc", "sklep/.git"):
            (self.projects / name).mkdir(parents=True)
        (self.projects / "evdt-service-shipscope/server/.env").write_text(
            "GITHUB_APP_CLIENT_ID=Iv1.x\nGITHUB_APP_CLIENT_SECRET=s\n", encoding="utf-8"
        )
        (self.projects / "ci_for_sdlc/node_modules").mkdir()
        self.missing: set[str] = set()
        self.answers: dict[tuple[str, ...], list[tuple[int, str, str]]] = {}
        self.hooks: dict[tuple[str, ...], Any] = {}
        self.runs: list[tuple[list[str], Path | None, dict[str, str], str | None]] = []
        self.spawned: list[tuple[str, list[str], dict[str, str]]] = []
        self.alive_pids: set[int] = set()
        self.busy_ports: set[int] = set()
        self.killed: list[int] = []
        self.next_pid = 1000
        self.down_until: dict[str, int] = {}
        self.http_calls: list[tuple[str, dict[str, str]]] = []
        self.http_answers: dict[str, tuple[int, bytes]] = {}
        self.output: list[str] = []
        self.asked: list[str] = []
        self.typed: list[str] = []
        self.opened: list[str] = []
        self.execs: list[tuple[list[str], dict[str, str]]] = []
        self.now = 0.0
        self.answer(("node", "server/scripts/local-pdi.js", "connect"), 0, json.dumps(CONNECTED))
        self.answer(
            ("node", "server/scripts/local-pdi.js", "test"),
            0,
            json.dumps({**CONNECTED, "connection": {"state": "connected"}}),
        )

    def answer(self, prefix: tuple[str, ...], code: int, out: str = "", err: str = "") -> None:
        self.answers.setdefault(prefix, []).append((code, out, err))

    # --- funkcje dla Ctx ---

    def run(self, argv: list[str], cwd: Path | None, env: Mapping[str, str], stdin: str | None) -> tuple[int, str, str]:
        self.runs.append((argv, cwd, dict(env), stdin))
        for prefix, hook in self.hooks.items():
            if tuple(argv[: len(prefix)]) == prefix:
                hook(argv, cwd, env, stdin)
        for prefix, queue in self.answers.items():
            if tuple(argv[: len(prefix)]) == prefix:
                return queue.pop(0) if len(queue) > 1 else queue[0]
        return 0, "", ""

    def spawn(self, name: str, argv: list[str], cwd: Path, env: Mapping[str, str], log: Path) -> int:
        self.spawned.append((name, argv, dict(env)))
        self.next_pid += 1
        self.alive_pids.add(self.next_pid)
        return self.next_pid

    def alive(self, pid: int) -> bool:
        return pid in self.alive_pids

    def kill(self, pid: int) -> None:
        self.killed.append(pid)
        self.alive_pids.discard(pid)

    def http(self, url: str, headers: Mapping[str, str]) -> tuple[int, bytes]:
        self.http_calls.append((url, dict(headers)))
        for prefix, left in self.down_until.items():
            if url.startswith(prefix) and left > 0:
                self.down_until[prefix] = left - 1
                raise OSError("connection refused")
        for prefix, answer in self.http_answers.items():
            if url.startswith(prefix):
                return answer
        if "/api/service/v1/connection" in url:
            body = {"workspace": {"id": "t1", "name": "Lokalnie"}, "pdi": {"state": "connected", "receiverUrl": "x"}}
            return 200, json.dumps(body).encode()
        return 200, b"{}"

    def ask(self, prompt: str, default: str) -> str:
        self.asked.append(prompt)
        if "PDI_DISPATCH_CHECKOUT" in prompt:
            return str(self.projects / "sklep")
        return default

    def type_line(self, prompt: str) -> str:
        self.output.append(prompt)
        return self.typed.pop(0) if self.typed else ""

    def sleep(self, seconds: float) -> None:
        self.now += seconds

    def exec(self, argv: list[str], env: Mapping[str, str]) -> None:
        self.execs.append((argv, dict(env)))

    def ctx(self) -> cli.Ctx:
        return cli.Ctx(
            user_home=self.home,
            cwd=self.projects / "pdi",
            environ={"PATH": "/usr/bin", "HOME": str(self.home)},
            run=self.run,
            spawn=self.spawn,
            alive=self.alive,
            kill=self.kill,
            http=self.http,
            port_free=lambda host, port: port not in self.busy_ports,
            which=lambda name: None if name in self.missing else f"/usr/local/bin/{name}",
            ask=self.ask,
            type_line=self.type_line,
            out=self.output.append,
            sleep=self.sleep,
            clock=lambda: self.now,
            open_url=self.opened.append,
            exec=self.exec,
            python_bin=Path("/venv/bin/python"),
        )

    def text(self) -> str:
        return "\n".join(self.output)

    def argv_text(self) -> str:
        return json.dumps([argv for argv, _, _, _ in self.runs] + [argv for _, argv, _ in self.spawned])


@pytest.fixture
def world(tmp_path: Path) -> World:
    return World(tmp_path)


def up(world: World) -> int:
    return cli.main(["up"], ctx=world.ctx())


def env_file(world: World) -> dict[str, str]:
    return home.read_env(world.home / ".sdlc" / "env")


# --- ~/.sdlc/env ---


def test_env_is_generated_once_private_and_never_overwritten(tmp_path: Path) -> None:
    root = tmp_path / ".sdlc"
    env, created = home.ensure_env(root)

    assert set(created) == {"PDI_TF_SIGNING_SECRET", "PDI_CI_FOR_SDLC_SIGNING_SECRET", "PDI_FORM_TOKEN"}
    assert (env["PDI_EVENTS_URL"], env["PDI_DISPATCH"], env["PDI_PHASE_BUDGET_USD"]) == (
        "http://127.0.0.1:8787",
        "local",
        "3",
    )
    assert len(env["PDI_TF_SIGNING_SECRET"]) >= 40
    assert stat.S_IMODE((root / "env").stat().st_mode) == 0o600
    assert stat.S_IMODE(root.stat().st_mode) == 0o700

    home.write_env(root / "env", {**env, "PDI_PHASE_BUDGET_USD": "5"})
    again, created_again = home.ensure_env(root)

    assert created_again == []
    assert again == {**env, "PDI_PHASE_BUDGET_USD": "5"}
    assert not list(root.glob("env.*")), "zapis atomowy nie zostawia plików tymczasowych"


# --- up ---


def test_missing_tools_are_listed_with_one_install_command_each(world: World) -> None:
    world.missing = {"docker", "claude"}
    world.answer(("gh", "auth", "status"), 1, "", "not logged in")

    assert up(world) == 1

    text = world.text()
    assert "docker" in text and "brew install --cask docker" in text
    assert "npm install -g @anthropic-ai/claude-code" in text
    assert "gh auth login" in text
    assert world.spawned == []


def test_first_up_asks_for_the_paths_once_then_starts_everything_in_order(world: World) -> None:
    world.down_until = {"http://localhost:3000/health": 3, "http://127.0.0.1:8787/": 2}

    assert up(world) == 0

    assert len(world.asked) == 5, "pdi, ShipScope, ci_for_sdlc, rejestr, repo produktu"
    config = home.load_config(world.home / ".sdlc" / "config.toml")
    assert config is not None
    assert (config.shipscope, config.checkout) == (world.projects / "evdt-service-shipscope", world.projects / "sklep")
    names = [name for name, _, _ in world.spawned]
    assert names == ["shipscope", "pdi-receiver", "pdi-receiver"], "odbiornik restartowany po połączeniu"
    shipscope_argv = world.spawned[0][1]
    assert shipscope_argv == ["node", "server/scripts/dev.js"]
    assert world.spawned[0][2]["SYNC_INTERVAL_MINUTES"] == "1"
    assert world.spawned[1][1] == ["uv", "run", "--directory", str(world.projects / "pdi"), "pdi-receiver"]
    assert world.text().rstrip().endswith("gotowe")
    assert "http://localhost:3000" in world.text() and "http://127.0.0.1:8787" in world.text()


def test_up_stops_when_a_process_it_did_not_start_holds_the_shipscope_port(world: World) -> None:
    """Pozostałość po przerwanym `sdlc up` odpowiadała na /health, a nowy ShipScope kończył się „port in use”."""
    world.busy_ports = {3000}

    assert up(world) == 1

    assert [name for name, _, _ in world.spawned] == []
    text = world.text()
    assert "port 3000" in text and "lsof -nP -iTCP:3000" in text
    assert "gotowe" not in text


def test_up_stops_when_a_foreign_process_holds_the_receiver_port(world: World) -> None:
    world.busy_ports = {8787}

    assert up(world) == 1

    assert [name for name, _, _ in world.spawned] == ["shipscope"]
    assert "port 8787" in world.text()


def test_a_running_shipscope_started_by_sdlc_is_not_mistaken_for_a_foreign_one(world: World) -> None:
    assert up(world) == 0
    world.busy_ports = {3000, 8787}  # teraz zajmuje je nasz własny stos
    world.output.clear()

    assert up(world) == 0
    assert world.text().rstrip().endswith("gotowe")


def test_the_connection_waits_for_a_workspace_and_writes_the_three_variables(world: World) -> None:
    world.answers[("node", "server/scripts/local-pdi.js", "connect")] = [
        (3, "", "no workspace yet"),
        (3, "", "no workspace yet"),
        (0, json.dumps(CONNECTED), ""),
    ]

    assert up(world) == 0

    env = env_file(world)
    assert (env["PDI_SHIPSCOPE_URL"], env["PDI_SHIPSCOPE_TOKEN"], env["PDI_SHIPSCOPE_SIGNING_SECRET"]) == (
        "http://localhost:3000",
        TOKEN,
        SIGNING,
    )
    assert world.text().count("utwórz przestrzeń") == 1, "prośba o logowanie raz, nie przy każdej próbie"
    connects = [r for r in world.runs if r[0][:3] == ["node", "server/scripts/local-pdi.js", "connect"]]
    assert connects[0][0][3:] == ["--receiver", "http://127.0.0.1:8787"]
    restarted = world.spawned[-1]
    assert (restarted[0], restarted[2]["PDI_SHIPSCOPE_TOKEN"]) == ("pdi-receiver", TOKEN)
    tests = [r for r in world.runs if r[0][:3] == ["node", "server/scripts/local-pdi.js", "test"]]
    assert len(tests) == 1
    assert "connected" in world.text()


def test_already_connected_without_variables_is_replaced(world: World) -> None:
    world.answers[("node", "server/scripts/local-pdi.js", "connect")] = [
        (4, "", "already connected"),
        (0, json.dumps(CONNECTED), ""),
    ]

    assert up(world) == 0

    connects = [r[0] for r in world.runs if r[0][:3] == ["node", "server/scripts/local-pdi.js", "connect"]]
    assert connects[-1][-1] == "--replace"
    assert env_file(world)["PDI_SHIPSCOPE_TOKEN"] == TOKEN


def test_second_up_starts_nothing_that_runs_and_changes_nothing(world: World) -> None:
    assert up(world) == 0
    spawned, asked = len(world.spawned), len(world.asked)
    before = env_file(world)
    world.output.clear()

    assert up(world) == 0

    assert len(world.spawned) == spawned
    assert len(world.asked) == asked
    assert env_file(world) == before
    assert not [r for r in world.runs[-20:] if r[0][:3] == ["node", "server/scripts/local-pdi.js", "connect"]][1:]
    assert world.text().rstrip().endswith("gotowe")


def test_a_dead_service_is_started_again(world: World) -> None:
    assert up(world) == 0
    receiver_pid = int((world.home / ".sdlc/run/pdi-receiver.pid").read_text(encoding="utf-8"))
    world.alive_pids.discard(receiver_pid)

    assert up(world) == 0

    assert [name for name, _, _ in world.spawned][-1] == "pdi-receiver"


def test_a_service_that_never_answers_stops_up_with_its_log(world: World) -> None:
    world.down_until = {"http://127.0.0.1:8787/": 10_000}

    assert up(world) == 1

    assert "pdi-receiver" in world.text() and "pdi-receiver.log" in world.text()
    assert "gotowe" not in world.text()


def test_ci_for_sdlc_sends_readiness_with_its_secret_in_the_environment(world: World) -> None:
    assert up(world) == 0

    (argv, cwd, env, _) = next(r for r in world.runs if r[0][:3] == ["npm", "run", "analyze"])
    assert argv == ["npm", "run", "analyze", "--", "--repo", str(world.projects / "sklep"), "--send-to-pdi"]
    assert cwd == world.projects / "ci_for_sdlc"
    secrets = env_file(world)
    assert env["PDI_SIGNING_SECRET"] == secrets["PDI_CI_FOR_SDLC_SIGNING_SECRET"]
    assert (env["PDI_EVENTS_URL"], env["CI_DATA_DIR"]) == ("http://127.0.0.1:8787", str(world.home / ".sdlc/ci-data"))


def test_mcp_servers_are_registered_without_any_value(world: World) -> None:
    assert up(world) == 0

    claude = [r[0] for r in world.runs if r[0][0] == "claude"]
    pdi_dir = str(world.projects / "pdi")
    assert claude == [
        ["claude", "mcp", "remove", "--scope", "user", "pdi"],
        [
            "claude",
            "mcp",
            "add",
            "--scope",
            "user",
            "pdi",
            "--",
            "uv",
            "run",
            "--directory",
            pdi_dir,
            "sdlc",
            "mcp",
            "pdi",
        ],
        ["claude", "mcp", "remove", "--scope", "user", "shipscope"],
        [
            "claude",
            "mcp",
            "add",
            "--scope",
            "user",
            "shipscope",
            "--",
            "uv",
            "run",
            "--directory",
            pdi_dir,
            "sdlc",
            "mcp",
            "shipscope",
        ],  # fmt: skip
    ]


def test_sdlc_mcp_starts_the_servers_with_the_variables_from_env(world: World) -> None:
    assert up(world) == 0

    cli.main(["mcp", "pdi"], ctx=world.ctx())
    cli.main(["mcp", "shipscope"], ctx=world.ctx())

    (pdi_argv, pdi_env), (ss_argv, ss_env) = world.execs
    assert pdi_argv == ["/venv/bin/pdi-mcp"]
    assert (pdi_env["PDI_SHIPSCOPE_TOKEN"], pdi_env["PDI_DISPATCH"], pdi_env["PDI_REGISTRY_PATH"]) == (
        TOKEN,
        "local",
        str(world.home / "pdi-decisions"),
    )
    assert pdi_env["PDI_DISPATCH_CHECKOUT"] == str(world.projects / "sklep")
    assert ss_argv == ["node", str(world.projects / "evdt-service-shipscope/adapters/mcp/shipscope-mcp.js")]
    assert (ss_env["SHIPSCOPE_URL"], ss_env["SHIPSCOPE_TOKEN"]) == ("http://localhost:3000", TOKEN)


def test_no_secret_in_argv_or_output(world: World) -> None:
    assert up(world) == 0
    cli.main(["status"], ctx=world.ctx())
    cli.main(["open"], ctx=world.ctx())

    secrets = [v for k, v in env_file(world).items() if k in home.SECRET_KEYS]
    assert len(secrets) == 5
    seen = world.argv_text() + world.text()
    for value in secrets:
        assert value not in seen


# --- deploy ---


@pytest.mark.parametrize(("target", "environment"), [("prod", "production"), ("test", "test")])
def test_deploy_creates_a_github_deployment_and_a_success_status(world: World, target: str, environment: str) -> None:
    assert up(world) == 0
    world.answer(("gh", "api", "repos/dbqm45/sklep/commits/main"), 0, "abc123def\n")
    world.answer(("gh", "api", "-X", "POST", "repos/dbqm45/sklep/deployments", "--input", "-"), 0, '{"id": 77}')
    first = len(world.runs)

    assert cli.main(["deploy", target, "--repo", "dbqm45/sklep"], ctx=world.ctx()) == 0

    calls = [(argv, stdin) for argv, _, _, stdin in world.runs[first:]]
    assert calls[0] == (["gh", "api", "repos/dbqm45/sklep/commits/main", "--jq", ".sha"], None)
    argv, stdin = calls[1]
    assert argv == ["gh", "api", "-X", "POST", "repos/dbqm45/sklep/deployments", "--input", "-"]
    assert json.loads(stdin or "") == {
        "ref": "abc123def",
        "environment": environment,
        "auto_merge": False,
        "required_contexts": [],
        "description": "sdlc deploy",
    }
    argv, stdin = calls[2]
    assert argv == ["gh", "api", "-X", "POST", "repos/dbqm45/sklep/deployments/77/statuses", "--input", "-"]
    assert json.loads(stdin or "") == {"state": "success", "environment": environment}
    assert "77" in world.text() and "abc123def" in world.text()


def test_deploy_takes_the_repo_from_the_product_checkout(world: World) -> None:
    assert up(world) == 0
    world.answer(
        ("git", "-C", str(world.projects / "sklep"), "remote", "get-url", "origin"),
        0,
        "git@github.com:dbqm45/sklep.git\n",
    )
    world.answer(("gh", "api", "-X", "POST"), 0, '{"id": 5}')
    world.answer(("gh", "api", "repos/dbqm45/sklep/commits/main"), 0, "abc123def\n")

    assert cli.main(["deploy", "prod"], ctx=world.ctx()) == 0

    assert any(r[0][:3] == ["gh", "api", "repos/dbqm45/sklep/commits/main"] for r in world.runs)


def test_deploy_refuses_an_unknown_target(world: World) -> None:
    with pytest.raises(SystemExit):
        cli.main(["deploy", "staging"], ctx=world.ctx())


# --- status, open, down, reset ---


def test_status_shows_processes_connections_and_ci_delivery(world: World) -> None:
    assert up(world) == 0
    ci = world.home / ".sdlc/ci-data"
    ci.mkdir(parents=True, exist_ok=True)
    (ci / "pdi-state.json").write_text(json.dumps({"sent": {"CHG-1": "ready"}, "seen": []}), encoding="utf-8")
    (ci / "pdi-outbox.json").write_text("[]", encoding="utf-8")
    world.answer(("docker", "inspect"), 0, "true\n")
    world.output.clear()

    assert cli.main(["status"], ctx=world.ctx()) == 0

    text = world.text()
    assert "shipscope" in text and "pdi-receiver" in text and "Postgres" in text
    assert "ShipScope ↔ pdi: connected" in text
    assert "ci_for_sdlc → pdi: connected" in text
    assert "PDI_SHIPSCOPE_TOKEN: ustawiony" in text


def test_status_says_queued_for_undelivered_readiness(world: World) -> None:
    assert up(world) == 0
    ci = world.home / ".sdlc/ci-data"
    ci.mkdir(parents=True, exist_ok=True)
    (ci / "pdi-state.json").write_text(json.dumps({"sent": {}, "seen": []}), encoding="utf-8")
    (ci / "pdi-outbox.json").write_text(json.dumps([{"attempts": 2, "nextAt": "x", "event": {}}]), encoding="utf-8")
    world.output.clear()

    cli.main(["status"], ctx=world.ctx())

    assert "ci_for_sdlc → pdi: queued 1" in world.text()


def test_open_opens_shipscope_and_the_form(world: World) -> None:
    assert up(world) == 0

    cli.main(["open"], ctx=world.ctx())

    assert world.opened[0] == "http://localhost:3000/"
    assert world.opened[1].startswith("http://127.0.0.1:8787/problems/new?t=")


def test_down_stops_processes_and_postgres_but_keeps_the_volume(world: World) -> None:
    assert up(world) == 0
    pids = {int(p.read_text(encoding="utf-8")) for p in (world.home / ".sdlc/run").glob("*.pid")}

    assert cli.main(["down"], ctx=world.ctx()) == 0

    assert set(world.killed) >= pids
    docker = [r[0] for r in world.runs if r[0][0] == "docker"]
    assert ["docker", "stop", "shipscope-dev-pg"] in docker
    assert not any("rm" in argv or "volume" in argv for argv in docker)


def test_reset_needs_the_typed_word_and_keeps_config_and_secrets(world: World) -> None:
    assert up(world) == 0
    world.typed = ["nie"]
    first = len(world.runs)

    assert cli.main(["reset"], ctx=world.ctx()) == 1
    assert not [r for r in world.runs[first:] if r[0][:2] == ["docker", "volume"]]
    assert "PDI_SHIPSCOPE_TOKEN" in env_file(world)

    world.typed = ["usuń"]
    assert cli.main(["reset"], ctx=world.ctx()) == 0
    docker = [r[0] for r in world.runs[first:] if r[0][0] == "docker"]
    assert ["docker", "rm", "-f", "shipscope-dev-pg"] in docker
    assert ["docker", "volume", "rm", "shipscope-dev-pg"] in docker
    env = env_file(world)
    assert "PDI_SHIPSCOPE_TOKEN" not in env and "PDI_TF_SIGNING_SECRET" in env
    assert (world.home / ".sdlc/config.toml").is_file()


def test_real_helpers_keep_mode_and_pid_files(tmp_path: Path) -> None:
    root = tmp_path / ".sdlc"
    home.write_env(root / "env", {"A": "1"})
    assert os.stat(root / "env").st_mode & 0o077 == 0
    assert home.read_env(root / "env") == {"A": "1"}
    config = home.Config(
        pdi=tmp_path / "pdi",
        shipscope=tmp_path / "ss",
        ci_for_sdlc=tmp_path / "ci",
        registry=tmp_path / "rej",
        checkout=None,
    )
    home.save_config(root / "config.toml", config)
    assert home.load_config(root / "config.toml") == config
    assert isinstance(home.load_config(root / "config.toml"), home.Config)
    assert home.load_config(root / "brak.toml") is None


# --- sandbox (L5) ---

TRACKED = {"workspace": {"id": "t1", "name": "Lokalnie"}, "repo": {"repoId": 9, "fullName": "dbqm45/sdlc-proba"}}
FLAGS_CONFIG = {"file": "config/flags.{env}.json", "valuePath": "enabled", "rolloutPath": "rollout"}


def sandbox(world: World, *args: str) -> int:
    return cli.main(["sandbox", "sdlc-proba", *args], ctx=world.ctx())


def prepare_sandbox(world: World, *, exists: bool) -> None:
    world.answer(("gh", "api", "user", "--jq", ".login"), 0, "dbqm45\n")
    world.answer(("gh", "repo", "view", "dbqm45/sdlc-proba"), 0 if exists else 1, "", "" if exists else "not found")
    world.answer(
        ("node", "server/scripts/local-pdi.js", "track"),
        0,
        json.dumps({**TRACKED, "flagSource": {"id": "s1", "created": True}}),
    )

    def created(argv: list[str], cwd: Path | None, env: Mapping[str, str], stdin: str | None) -> tuple[int, str, str]:
        (world.projects / "sdlc-proba" / ".git").mkdir(parents=True, exist_ok=True)
        return 0, "", ""

    world.hooks[("gh", "repo", "create")] = created
    world.hooks[("gh", "repo", "clone")] = created


def test_sandbox_creates_the_repo_from_the_template_tracks_it_and_sets_the_checkout(world: World) -> None:
    assert up(world) == 0
    prepare_sandbox(world, exists=False)
    env_before = env_file(world)
    first = len(world.runs)
    receivers = [name for name, _, _ in world.spawned].count("pdi-receiver")

    assert sandbox(world) == 0

    calls = [(argv, cwd) for argv, cwd, _, _ in world.runs[first:]]
    create = next(c for c in calls if c[0][:3] == ["gh", "repo", "create"])
    assert create == (
        ["gh", "repo", "create", "dbqm45/sdlc-proba", "--template", "dbqm45/sdlc-sandbox", "--private", "--clone"],
        world.projects,
    )
    track = next(c for c in calls if c[0][:3] == ["node", "server/scripts/local-pdi.js", "track"])
    assert track[0][3:5] == ["--repo", "dbqm45/sdlc-proba"]
    assert json.loads(track[0][6]) == FLAGS_CONFIG and track[0][5] == "--flags"
    assert track[1] == world.projects / "evdt-service-shipscope"
    config = home.load_config(world.home / ".sdlc/config.toml")
    assert config is not None
    assert (config.checkout, config.deploy_repo) == (world.projects / "sdlc-proba", "dbqm45/sdlc-proba")
    assert (config.pdi, config.shipscope, config.registry) == (
        world.projects / "pdi",
        world.projects / "evdt-service-shipscope",
        world.home / "pdi-decisions",
    )
    assert env_file(world) == env_before, "~/.sdlc/env nietknięty"
    assert [name for name, _, _ in world.spawned].count("pdi-receiver") == receivers + 1
    assert world.spawned[-1][2]["PDI_DISPATCH_CHECKOUT"] == str(world.projects / "sdlc-proba")
    text = world.text()
    assert "https://github.com/dbqm45/sdlc-proba" in text and str(world.projects / "sdlc-proba") in text
    assert "sdlc open" in text and text.rstrip().endswith("gotowe")
    secrets = [v for k, v in env_before.items() if k in home.SECRET_KEYS]
    for value in secrets:
        assert value not in world.argv_text() + text


def test_sandbox_reuses_an_existing_repo_and_a_second_run_changes_nothing(world: World) -> None:
    assert up(world) == 0
    prepare_sandbox(world, exists=True)

    assert sandbox(world) == 0
    first = len(world.runs)
    spawned = len(world.spawned)
    config = (world.home / ".sdlc/config.toml").read_text(encoding="utf-8")

    assert sandbox(world) == 0

    calls = [argv for argv, _, _, _ in world.runs[first:]]
    assert not any(c[:3] == ["gh", "repo", "create"] for c in calls)
    assert ["git", "-C", str(world.projects / "sdlc-proba"), "pull", "--ff-only"] in calls
    assert len(world.spawned) == spawned, "bez restartu odbiornika, gdy repo produktu się nie zmieniło"
    assert (world.home / ".sdlc/config.toml").read_text(encoding="utf-8") == config


def test_sandbox_clones_an_existing_repo_that_is_not_here_yet(world: World) -> None:
    assert up(world) == 0
    prepare_sandbox(world, exists=True)

    assert sandbox(world, "--owner", "dbqm45") == 0

    calls = [(argv, cwd) for argv, cwd, _, _ in world.runs]
    assert (["gh", "repo", "clone", "dbqm45/sdlc-proba", str(world.projects / "sdlc-proba")], None) in calls
    assert not any(argv[:3] == ["gh", "api", "user"] for argv, _ in calls), "--owner bez pytania GitHuba"


def test_sandbox_waits_for_the_github_app_installation(world: World) -> None:
    assert up(world) == 0
    prepare_sandbox(world, exists=True)
    world.answers[("node", "server/scripts/local-pdi.js", "track")] = [
        (5, "", "Install the ShipScope GitHub App on dbqm45"),
        (5, "", "Install the ShipScope GitHub App on dbqm45"),
        (0, json.dumps({**TRACKED, "flagSource": {"id": "s1", "created": True}}), ""),
    ]
    world.typed = ["", ""]

    assert sandbox(world) == 0

    text = world.text()
    assert text.count("Settings → GitHub") == 1, "kliknięcia raz"
    assert "Enter" in text
    assert len([r for r in world.runs if r[0][:3] == ["node", "server/scripts/local-pdi.js", "track"]]) == 3


def test_sandbox_needs_sdlc_up_first(world: World) -> None:
    assert sandbox(world) == 1
    assert "sdlc up" in world.text()


def test_a_finished_child_is_not_alive_and_stopping_it_does_not_fail(tmp_path: Path) -> None:
    """Proces startowany i zatrzymywany w tym samym `sdlc up` zostaje zombie, dopóki nikt go nie odbierze.

    Na macOS `killpg` na grupę z samym zombie daje EPERM (sdlc up po połączeniu z ShipScope padał z PermissionError).
    """
    pid = cli._spawn("krotki", ["true"], tmp_path, dict(os.environ), tmp_path / "krotki.log")
    for _ in range(50):
        if not cli._alive(pid):
            break
        time.sleep(0.1)
    assert cli._alive(pid) is False
    cli._kill(pid)  # już odebrany: nic do zrobienia, bez wyjątku


# Jak `npm run dev` w ShipScope: rodzic na SIGTERM kończy się od razu, a dziecko we własnej grupie procesów (detached)
# zamyka się wolno albo wcale — po `sdlc down` zostawało sierotą (PRB-8).
TREE = """
import os, signal, subprocess, sys, time
child = subprocess.Popen([sys.executable, "-c", CHILD], start_new_session=True)
open(sys.argv[1], "w").write(str(child.pid))
signal.signal(signal.SIGTERM, lambda *a: os._exit(0))
while True:
    time.sleep(0.1)
"""
CHILD = "import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)"


def _gone(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    # Sierota odebrana przez init może przez chwilę być zombie — w `ps` ma stan Z.
    state = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()
    return not state or state.startswith("Z")


def test_stopping_stops_children_in_their_own_process_group(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "KILL_GRACE_SECONDS", 1.0)
    child_file = tmp_path / "child.pid"
    script = tmp_path / "tree.py"
    script.write_text(f"CHILD = {CHILD!r}\n{TREE}", encoding="utf-8")
    pid = cli._spawn(
        "drzewo", [sys.executable, str(script), str(child_file)], tmp_path, dict(os.environ), tmp_path / "d.log"
    )
    for _ in range(100):
        if child_file.is_file() and child_file.read_text():
            break
        time.sleep(0.05)
    child = int(child_file.read_text())
    assert cli._alive(pid) and not _gone(child)

    started = time.monotonic()
    cli._kill(pid)

    for _ in range(50):
        if _gone(child):
            break
        time.sleep(0.1)
    assert cli._alive(pid) is False
    assert _gone(child), "dziecko w osobnej grupie procesów zostało sierotą"
    assert time.monotonic() - started < 5


def test_descendants_come_from_the_process_table() -> None:
    table = "  1     0\n 10     1\n 11    10\n 12    11\n 13    10\n 20     1\n bad line\n"

    assert cli._descendants(10, table) == [11, 13, 12]
    assert cli._descendants(99, table) == []


def test_port_free_sees_a_listening_socket() -> None:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", 0))
        server.listen()
        port = server.getsockname()[1]
        assert cli._port_free("127.0.0.1", port) is False
    assert cli._port_free("127.0.0.1", port) is True


# --- sdlc check mówi, co sprawdził i dlaczego nic nie wysłał (PRB-7) ---

ANALYZE = ("npm", "run", "analyze")
SENT = "\npdi: http://127.0.0.1:8787\n  pdi readiness.changed CHG-1 ready delivered\n"


def check(world: World) -> int:
    return cli.main(["check"], ctx=world.ctx())


def checked(world: World, *, code: int, out: str, err: str = "", changes: bool = True) -> int:
    assert up(world) == 0
    world.output.clear()
    if changes:
        (world.projects / "sklep/docs/project/changes/CHG-1").mkdir(parents=True)
    world.answer(("git", "-C", str(world.projects / "sklep"), "rev-parse"), 0, "main\n")
    world.answers[ANALYZE] = [(code, out, err)]
    return check(world)


def test_check_names_the_checkout_and_branch_it_analysed(world: World) -> None:
    assert checked(world, code=0, out=SENT) == 0

    text = world.text()
    assert f"ci_for_sdlc: analiza {world.projects / 'sklep'} (main)" in text
    assert "ci_for_sdlc: pdi readiness.changed CHG-1 ready delivered" in text


def test_check_without_changes_on_the_checkout_says_why_nothing_was_sent(world: World) -> None:
    assert checked(world, code=0, out="\npdi: http://127.0.0.1:8787\n", changes=False) == 0

    text = world.text()
    assert "nic nie wysłano do pdi" in text
    assert "docs/project/changes" in text and "git pull" in text


def test_check_with_only_unchanged_readiness_says_so(world: World) -> None:
    out = "\npdi: http://127.0.0.1:8787\n  pdi readiness.changed CHG-1 not_ready unchanged\n"

    assert checked(world, code=1, out=out, err="\n✗ Quality gate failed: CHG-1\n") == 0

    text = world.text()
    assert "unchanged" in text and "bez zmian od ostatniej wysyłki" in text
    assert "Quality gate failed: CHG-1" in text


def test_check_reports_an_analysis_that_did_not_run(world: World) -> None:
    assert checked(world, code=3, out="", err="Error: Cannot find module tsx\n") == 1

    assert "kodem 3" in world.text() and "Cannot find module tsx" in world.text()


def test_up_goes_on_when_the_analysis_does_not_run(world: World) -> None:
    world.answer(ANALYZE, 3, "", "Error: Cannot find module tsx\n")

    assert up(world) == 0
    assert "kodem 3" in world.text() and "gotowe" in world.text()


# --- stan powiadomień ci_for_sdlc → pdi w sdlc status (PRB-10) ---


def ci_status(world: World, *, state: Any, outbox: Any) -> str:
    assert up(world) == 0
    ci = world.home / ".sdlc/ci-data"
    ci.mkdir(parents=True, exist_ok=True)
    (ci / "pdi-state.json").write_text(json.dumps(state), encoding="utf-8")
    (ci / "pdi-outbox.json").write_text(json.dumps(outbox), encoding="utf-8")
    world.output.clear()
    assert cli.main(["status"], ctx=world.ctx()) == 0
    return world.text()


def event(change: str, kind: str = "readiness.changed") -> dict[str, Any]:
    return {"type": kind, "payload": {"change": change}}


def test_status_lists_the_readiness_already_sent(world: World) -> None:
    text = ci_status(world, state={"sent": {"CHG-1": "ready", "CHG-2": "not_ready"}, "seen": []}, outbox=[])

    assert "ci_for_sdlc → pdi: connected" in text
    assert "  wysłana gotowość: CHG-1 ready, CHG-2 not_ready" in text
    assert "  ostatnie sdlc check: kod 0" in text


def test_status_shows_why_events_wait_and_when_they_retry(world: World) -> None:
    queued = [
        {"attempts": 3, "nextAt": "2026-11-01T10:05:00Z", "lastError": "connection refused", "event": event("CHG-1")}
    ]

    text = ci_status(world, state={"sent": {"CHG-1": "ready"}, "seen": []}, outbox=queued)

    assert "ci_for_sdlc → pdi: queued 1" in text
    assert (
        "  w kolejce: readiness.changed CHG-1 — prób 3, następna 2026-11-01T10:05:00Z, błąd: connection refused" in text
    )


def test_status_does_not_call_refused_events_connected(world: World) -> None:
    refused = [{"attempts": 1, "nextAt": "x", "failed": "unknown change CHG-9", "event": event("CHG-9")}]

    text = ci_status(world, state={"sent": {"CHG-9": "ready"}, "seen": []}, outbox=refused)

    assert "ci_for_sdlc → pdi: refused 1" in text
    assert "  odrzucone przez pdi (bez ponowień): readiness.changed CHG-9 — unknown change CHG-9" in text
    assert "connected" not in text.split("ci_for_sdlc → pdi:")[1].splitlines()[0]


def test_status_shortens_long_errors_and_lists_at_most_five(world: World) -> None:
    queued = [{"attempts": 1, "nextAt": "x", "lastError": "x" * 500, "event": event(f"CHG-{n}")} for n in range(8)]

    text = ci_status(world, state={"sent": {}, "seen": []}, outbox=queued)

    lines = [line for line in text.splitlines() if line.startswith("  w kolejce:")]
    assert len(lines) == 5 and all(len(line) < 260 for line in lines)
    assert "  … i 3 więcej" in text
