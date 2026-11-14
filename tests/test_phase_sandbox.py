"""Faza tf w kontenerze (Z8a, DZ9): obraz, argv `docker run`, sieć z listą hostów, ustawienia Claude Code.

Bez prawdziwego Dockera — podstawiony wykonawca zapisuje polecenia. Plan: docs/plan-z8a-izolacja-faz.md.
"""

import json
import os
import re
import shlex
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from pdi import dispatch_local, phase_sandbox

OAUTH = "sk-ant-oat01-tajny-token-claude"  # noqa: S105 — token testowy
API_KEY = "sk-ant-api03-tajny-klucz"  # noqa: S105 — klucz testowy
GH = "ghs_tajny_token_github"  # noqa: S105 — token testowy
PROBLEM = json.dumps({"title": "Tajny opis zgłoszenia", "reported_at": "2026-10-23"}, ensure_ascii=False)
S = ".claude/skills/pdi-decisions/scripts"
PR = "https://github.com/dbqm45/sklep/pull/7"
TAG_RE = r"^pdi-phase:2\.1\.310-[0-9a-f]{12}$"


class FakeRun:
    """Podstawiony wykonawca jak w test_dispatch_local: zapisuje polecenia, odpowiada według początku polecenia."""

    def __init__(self, responses: dict[str, Any] | None = None) -> None:
        self.responses: dict[str, Any] = {
            "git ls-remote": (2, ""),
            "git diff --cached --quiet": (1, ""),
            "gh pr view": (1, "no pull requests found"),
            "gh pr create": (0, f"Creating pull request\n{PR}\n"),
            "git config user.name": (0, "Ala Kot\n"),
            "git config user.email": (0, "ala@example.com\n"),
            "docker version": (0, "29.1.0\n"),
            "docker logs": (0, "pdi-egress: listening on 3128\npdi-egress: allowed api.anthropic.com:443\n"),
        }
        self.responses.update(responses or {})
        self.calls: list[list[str]] = []
        self.envs: list[dict[str, str]] = []

    def __call__(self, argv: list[str], cwd: Path, env: Mapping[str, str]) -> tuple[int, str]:
        assert all(isinstance(a, str) for a in argv)
        self.calls.append(argv)
        self.envs.append(dict(env))
        line = " ".join(argv)
        for prefix in sorted(self.responses, key=len, reverse=True):
            if line.startswith(prefix):
                answer = self.responses[prefix]
                if isinstance(answer, list):
                    return answer.pop(0) if len(answer) > 1 else answer[0]
                return answer
        return 0, ""

    def find(self, *prefix: str) -> list[int]:
        return [i for i, c in enumerate(self.calls) if c[: len(prefix)] == list(prefix)]

    def phase_call(self) -> tuple[list[str], dict[str, str]]:
        (i,) = [i for i, c in enumerate(self.calls) if c[:2] == ["docker", "run"] and "-d" not in c]
        return self.calls[i], self.envs[i]


def make_checkout(tmp_path: Path, *, files: tuple[str, ...] = ()) -> Path:
    repo = tmp_path / "sklep"
    (repo / ".git").mkdir(parents=True)
    (repo / S).mkdir(parents=True)
    folder = repo / "docs/project/changes/CHG-12"
    folder.mkdir(parents=True)
    for name in ("intent.md", "requirements.md", "plan.md"):
        (folder / name).write_text(f"# {name}\n", encoding="utf-8")
    for name in files:
        (repo / name).write_text("{}\n", encoding="utf-8")
    return repo


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    return make_checkout(tmp_path)


def spec(checkout: Path, tmp_path: Path, **overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "change": "CHG-12",
        "phase": "requirements",
        "gate": "B1",
        "outcome": "approved",
        "decision": "DEC-0001",
        "rework": False,
        "budget_usd": "3",
        "source": None,
        "reported_at": None,
        "ref": "main",
        "checkout": str(checkout),
        "log": str(tmp_path / "runs" / f"CHG-12-{overrides.get('phase', 'requirements')}-20261102T100000Z.log"),
    }
    base.update(overrides)
    (tmp_path / "runs").mkdir(exist_ok=True)
    return base


ENV = {
    "PATH": "/opt/homebrew/bin:/usr/bin",
    "HOME": "/Users/ala",
    "LANG": "pl_PL.UTF-8",
    "TMPDIR": "/var/folders/xy",
    "SSH_AUTH_SOCK": "/private/tmp/ssh.sock",
    "HTTPS_PROXY": "http://127.0.0.1:9999",
    "GH_TOKEN": GH,
    "CLAUDE_CODE_OAUTH_TOKEN": OAUTH,
    "PDI_CLAUDE_BIN": "/Users/ala/.local/bin/claude",
    "PDI_PROBLEM": PROBLEM,
    "PDI_TF_SIGNING_SECRET": "sekret-odbiornika",
    "PDI_EVENTS_URL": "http://127.0.0.1:8787",
    "AWS_SECRET_ACCESS_KEY": "aws-tajne",
}


def execute(s: dict[str, Any], run: FakeRun, env: dict[str, str] | None = None) -> tuple[dict[str, Any], list[str]]:
    lines: list[str] = []
    result = dispatch_local.execute(s, run=run, env=ENV if env is None else env, log=lines.append)
    return result, lines


# --- tryb ---


def test_docker_is_the_default_and_none_must_be_explicit() -> None:
    assert phase_sandbox.mode({}) == "docker"
    assert phase_sandbox.mode({"PDI_DISPATCH_SANDBOX": "none"}) == "none"
    with pytest.raises(phase_sandbox.SandboxError, match="PDI_DISPATCH_SANDBOX"):
        phase_sandbox.mode({"PDI_DISPATCH_SANDBOX": "podman"})


def test_none_mode_runs_on_the_host_and_warns_in_the_log(checkout: Path, tmp_path: Path) -> None:
    run = FakeRun()
    result, lines = execute(spec(checkout, tmp_path), run, {**ENV, "PDI_DISPATCH_SANDBOX": "none"})

    assert result["status"] == "done"
    assert not run.find("docker")
    assert any(c[:2] == ["python3", f"{S}/phase_run.py"] and c[2] == "run" for c in run.calls)
    assert lines[0].startswith("# UWAGA: PDI_DISPATCH_SANDBOX=none")


def test_bad_mode_fails_before_any_step(checkout: Path, tmp_path: Path) -> None:
    run = FakeRun()
    result, _ = execute(spec(checkout, tmp_path), run, {**ENV, "PDI_DISPATCH_SANDBOX": "vm"})

    assert (result["status"], result["step"]) == ("failed", "run")
    assert run.calls == []


# --- krok run w kontenerze ---


@pytest.mark.parametrize("phase", dispatch_local.PHASES)
def test_run_step_goes_through_docker_with_only_the_clone_mounted(checkout: Path, tmp_path: Path, phase: str) -> None:
    responses = {}
    if phase == "delivery":
        responses = {
            "git for-each-ref": [(0, ""), (0, "story/a\n")],
            "git rev-list --count": (0, "2\n"),
            "git merge-base": (1, ""),
        }
    run = FakeRun(responses)
    s = spec(checkout, tmp_path, phase=phase, source="PRB-1" if phase == "intent" else None)
    result, lines = execute(s, run, {**ENV, "PDI_PR_LOOP": "off"})  # pętla PR (N2): osobny test niżej

    assert result["status"] == "done", lines
    argv, _ = run.phase_call()
    text = shlex.join(argv)
    # tylko klon, pod tą samą ścieżką, plus ustawienia Claude tylko do odczytu
    mounts = [argv[i + 1] for i, a in enumerate(argv) if a == "--mount"]
    assert mounts[0] == f"type=bind,src={checkout},dst={checkout}"
    assert len(mounts) == 2 and mounts[1].endswith(",dst=/etc/claude-code/managed-settings.json,readonly")
    assert "-v" not in argv and "--volume" not in argv
    assert "/Users/ala" not in text, "nic z katalogu domowego właściciela"
    assert ["--workdir", str(checkout)] == argv[argv.index("--workdir") : argv.index("--workdir") + 2]
    # izolacja i limity
    for flag in ("--read-only", "--rm"):
        assert flag in argv
    assert argv[argv.index("--cap-drop") : argv.index("--cap-drop") + 2] == ["--cap-drop", "ALL"]
    opts = [argv[i + 1] for i, a in enumerate(argv) if a == "--security-opt"]
    assert "no-new-privileges" in opts and any(o.startswith("seccomp=") for o in opts)
    assert argv[argv.index("--cpus") + 1] == "4"
    assert argv[argv.index("--memory") + 1] == "6g"
    assert argv[argv.index("--pids-limit") + 1] == "1024"
    assert argv[argv.index("--network") + 1] == f"pdi-phase-chg-12-{phase}-20261102t100000z"
    tmpfs = [argv[i + 1] for i, a in enumerate(argv) if a == "--tmpfs"]
    assert any(t.startswith("/home/pdi:") for t in tmpfs) and any(t.startswith("/tmp:") for t in tmpfs)  # noqa: S108
    user = argv[argv.index("--user") + 1]
    assert user.split(":")[0] != "0"
    # polecenie: limit czasu w kontenerze, potem dzisiejszy phase_run.py run
    inner = argv[argv.index("timeout") :]
    assert inner[:3] == ["timeout", "--kill-after=30", str(dispatch_local.STEP_TIMEOUT_SECONDS - 60)]
    assert inner[3:6] == ["python3", f"{S}/phase_run.py", "run"]
    assert inner[6:10] == ["--change", "CHG-12", "--phase", phase]
    assert any(re.match(TAG_RE, a) for a in argv[: argv.index("timeout")])


def test_container_gets_only_the_run_step_environment_and_values_never_in_argv(checkout: Path, tmp_path: Path) -> None:
    run = FakeRun()
    env_in = {
        **ENV,
        "LC_ALL": "pl_PL.UTF-8",
        "GIT_TRACE": "0",
        "MY_DB_URL": "postgres://x",
        "PDI_DISPATCH_ENV_PASS": "",
    }
    result, lines = execute(spec(checkout, tmp_path, source="PRB-1"), run, env_in)

    assert result["status"] == "done"
    argv, env = run.phase_call()
    names = [argv[i + 1] for i, a in enumerate(argv) if a in ("-e", "--env")]
    bare = {n for n in names if "=" not in n}
    fixed = dict(n.split("=", 1) for n in names if "=" in n)
    assert bare == {"LANG", "LC_ALL", "GIT_TRACE", "PDI_SOURCE", "PDI_PROBLEM", "CLAUDE_CODE_OAUTH_TOKEN"} | {
        "GIT_AUTHOR_NAME",
        "GIT_AUTHOR_EMAIL",
        "GIT_COMMITTER_NAME",
        "GIT_COMMITTER_EMAIL",
    }
    assert fixed["HOME"] == "/home/pdi"
    assert fixed["HTTPS_PROXY"] == fixed["HTTP_PROXY"] == "http://pdi-egress-chg-12-requirements-20261102t100000z:3128"
    assert fixed["PDI_CLAUDE_SETTINGS"] == "/etc/claude-code/managed-settings.json"
    assert fixed["DISABLE_AUTOUPDATER"] == "1" and fixed["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] == "1"
    assert fixed["TMPDIR"] == phase_sandbox.TMP and "TMPDIR" not in bare, "tmpfs kontenera, nie TMPDIR hosta"
    for name in ("PATH", "SSH_AUTH_SOCK", "GH_TOKEN", "PDI_CLAUDE_BIN", "PDI_TF_SIGNING_SECRET", "MY_DB_URL"):
        assert name not in bare and name not in fixed, name
    # wartości idą tylko przez środowisko procesu docker
    assert env["CLAUDE_CODE_OAUTH_TOKEN"] == OAUTH and env["PDI_PROBLEM"] == PROBLEM
    assert env["GIT_AUTHOR_NAME"] == "Ala Kot" and env["GIT_COMMITTER_EMAIL"] == "ala@example.com"
    assert "GH_TOKEN" not in env and "PDI_TF_SIGNING_SECRET" not in env
    every = json.dumps(run.calls) + "\n".join(lines)
    for secret in (OAUTH, GH, "Tajny opis", "sekret-odbiornika"):
        assert secret not in every, secret


def test_named_pass_variables_reach_the_container_by_name(checkout: Path, tmp_path: Path) -> None:
    run = FakeRun()
    execute(spec(checkout, tmp_path), run, {**ENV, "PDI_DISPATCH_ENV_PASS": "MY_DB_URL", "MY_DB_URL": "postgres://x"})

    argv, env = run.phase_call()
    assert "MY_DB_URL" in [argv[i + 1] for i, a in enumerate(argv) if a == "-e"]
    assert env["MY_DB_URL"] == "postgres://x"


def test_steps_with_credentials_stay_on_the_host(checkout: Path, tmp_path: Path) -> None:
    run = FakeRun()
    execute(spec(checkout, tmp_path), run)

    docker_runs = [c for c in run.calls if c[:2] == ["docker", "run"]]
    assert len(docker_runs) == 2, "proxy wyjścia i faza"
    for argv in docker_runs:
        assert "push" not in argv and "gh" not in argv and "gate" not in argv
    assert run.find("git", "push", "-u", "origin", "pdi/CHG-12-requirements")
    assert run.find("python3", f"{S}/phase_run.py", "gate", "request")


def test_network_is_internal_with_an_egress_proxy_and_is_cleaned_up(checkout: Path, tmp_path: Path) -> None:
    run = FakeRun(
        {"docker logs": (0, "pdi-egress: blocked evil.example:443\npdi-egress: allowed api.anthropic.com:443\n")}
    )
    result, lines = execute(spec(checkout, tmp_path), run)

    assert result["status"] == "done"
    name = "chg-12-requirements-20261102t100000z"
    create = run.find("docker", "network", "create")
    assert run.calls[create[0]] == ["docker", "network", "create", "--internal", f"pdi-phase-{name}"]
    (egress,) = [i for i, c in enumerate(run.calls) if c[:3] == ["docker", "run", "-d"]]
    proxy = run.calls[egress]
    assert ["--name", f"pdi-egress-{name}"] == proxy[proxy.index("--name") : proxy.index("--name") + 2]
    assert "--read-only" in proxy and proxy[proxy.index("--cap-drop") :][:2] == ["--cap-drop", "ALL"]
    assert proxy[-3:-1] == ["-I", "/opt/pdi/egress.py"]
    assert "api.anthropic.com" in proxy[-1].split(",")
    connect = run.find("docker", "network", "connect")
    phase = [i for i, c in enumerate(run.calls) if c[:2] == ["docker", "run"] and "-d" not in c][0]
    logs = run.find("docker", "logs")
    removed = run.find("docker", "rm", "-f")
    net_rm = run.find("docker", "network", "rm")
    assert create[0] < egress < connect[0] < phase < logs[0] < removed[0] < net_rm[0]
    assert run.calls[removed[0]][3:] == [f"pdi-phase-{name}", f"pdi-egress-{name}"]
    assert "# sieć: krok run — zablokowany host evil.example:443" in lines
    assert not any("api.anthropic.com:443" in line and "zablokowany" in line for line in lines)


def test_cleanup_runs_when_the_phase_fails(checkout: Path, tmp_path: Path) -> None:
    run = FakeRun({"docker run --rm": (1, "błąd persony")})
    result, _ = execute(spec(checkout, tmp_path), run)

    assert (result["status"], result["step"]) == ("failed", "run")
    assert run.find("docker", "rm", "-f") and run.find("docker", "network", "rm")
    assert not run.find("git", "push")


def test_worktree_mounts_the_common_git_dir_too(tmp_path: Path) -> None:
    main = tmp_path / "glowny"
    (main / ".git").mkdir(parents=True)
    wt = make_checkout(tmp_path / "wt")
    (wt / ".git").rmdir()
    (wt / ".git").write_text(f"gitdir: {main}/.git/worktrees/sklep\n", encoding="utf-8")
    run = FakeRun({"git rev-parse --path-format=absolute --git-common-dir": (0, f"{main}/.git\n")})
    result, _ = execute(spec(wt, tmp_path), run)

    assert result["status"] == "done"
    argv, _ = run.phase_call()
    mounts = [argv[i + 1] for i, a in enumerate(argv) if a == "--mount"]
    assert f"type=bind,src={main}/.git,dst={main}/.git" in mounts


# --- token Claude ---


def test_without_a_claude_token_the_run_step_refuses_with_instructions(checkout: Path, tmp_path: Path) -> None:
    env = {k: v for k, v in ENV.items() if k != "CLAUDE_CODE_OAUTH_TOKEN"}
    run = FakeRun()
    result, _ = execute(spec(checkout, tmp_path), run, env)

    assert (result["status"], result["step"]) == ("failed", "run")
    assert "claude setup-token" in result["error"] and "CLAUDE_CODE_OAUTH_TOKEN" in result["error"]
    assert not [c for c in run.calls if c[:2] == ["docker", "run"]]


def test_two_claude_tokens_at_once_are_refused(checkout: Path, tmp_path: Path) -> None:
    run = FakeRun()
    result, _ = execute(spec(checkout, tmp_path), run, {**ENV, "ANTHROPIC_API_KEY": API_KEY})

    assert (result["status"], result["step"]) == ("failed", "run")
    assert "tylko jedną" in result["error"]
    assert API_KEY not in json.dumps(result) and OAUTH not in json.dumps(result)


def test_an_api_key_alone_is_enough(checkout: Path, tmp_path: Path) -> None:
    env = {k: v for k, v in ENV.items() if k != "CLAUDE_CODE_OAUTH_TOKEN"}
    run = FakeRun()
    result, _ = execute(spec(checkout, tmp_path), run, {**env, "ANTHROPIC_API_KEY": API_KEY})

    assert result["status"] == "done"
    argv, docker_env = run.phase_call()
    assert "ANTHROPIC_API_KEY" in argv and API_KEY not in argv
    assert docker_env["ANTHROPIC_API_KEY"] == API_KEY


# --- obraz i Docker ---


def test_missing_image_refuses_and_points_at_sdlc_image(checkout: Path, tmp_path: Path) -> None:
    run = FakeRun({"docker image inspect": (1, "No such image")})
    result, _ = execute(spec(checkout, tmp_path), run)

    assert (result["status"], result["step"]) == ("failed", "run")
    assert "sdlc image" in result["error"]
    assert not run.find("docker", "network", "create")


def test_start_refuses_without_docker(checkout: Path, tmp_path: Path) -> None:
    run = FakeRun({"git status": (0, ""), "docker version": (1, "Cannot connect to the Docker daemon")})
    result = dispatch_local.start(
        runs_dir=tmp_path / "runs",
        checkout=str(checkout),
        ref="main",
        budget_usd=None,
        change="CHG-12",
        phase="requirements",
        gate="B1",
        outcome="approved",
        decision="DEC-0001",
        rework=False,
        at="2026-11-02T10:00:00Z",
        run=run,
        spawn=lambda spec, env: None,
        environ=ENV,
    )

    assert result["status"] == "failed"
    assert "Docker" in result["error"] and "PDI_DISPATCH_SANDBOX=none" in result["error"]


def test_start_without_docker_is_fine_in_none_mode(checkout: Path, tmp_path: Path) -> None:
    run = FakeRun({"git status": (0, ""), "docker version": (127, "brak polecenia docker")})
    started: list[dict[str, Any]] = []
    result = dispatch_local.start(
        runs_dir=tmp_path / "runs",
        checkout=str(checkout),
        ref="main",
        budget_usd=None,
        change="CHG-12",
        phase="requirements",
        gate="B1",
        outcome="approved",
        decision="DEC-0001",
        rework=False,
        at="2026-11-02T10:00:00Z",
        run=run,
        spawn=lambda spec, env: started.append(spec),
        environ={**ENV, "PDI_DISPATCH_SANDBOX": "none"},
    )

    assert result["status"] == "running" and started
    assert not run.find("docker")


def test_dockerfile_is_pinned_non_root_and_has_no_secrets(checkout: Path) -> None:
    text = phase_sandbox.dockerfile("2.1.310", [])

    first = text.splitlines()[0]
    assert first.startswith("FROM node:22-bookworm-slim@sha256:") and len(first.split("@sha256:")[1]) == 64
    assert "@anthropic-ai/claude-code@2.1.310" in text
    for package in ("python3", "git", "bubblewrap", "socat", "ca-certificates"):
        assert package in text
    assert "\nUSER pdi" in text
    assert "COPY egress.py /opt/pdi/egress.py" in text
    assert "COPY entrypoint.py /opt/pdi/entrypoint.py" in text
    assert 'ENTRYPOINT ["python3", "-I", "/opt/pdi/entrypoint.py"]' in text
    for word in ("TOKEN", "API_KEY", "SECRET", "ARG "):
        assert word not in text


def run_entrypoint(tmp_path: Path, home: Path) -> subprocess.CompletedProcess[str]:
    script = tmp_path / "entrypoint.py"
    script.write_text(phase_sandbox.ENTRYPOINT_SOURCE, encoding="utf-8")
    work = tmp_path / "klon"
    work.mkdir(exist_ok=True)
    env = {"PATH": os.environ["PATH"], "HOME": str(home)}
    return subprocess.run(
        [sys.executable, "-I", str(script), "sh", "-c", 'echo "$PWD"'],
        cwd=work, env=env, capture_output=True, text=True, check=True,
    )  # fmt: skip


def test_entrypoint_marks_onboarding_and_trusts_the_clone(tmp_path: Path) -> None:
    """claude -p w niezaufanym folderze pomija permissions.allow repo (PRB-32); onboarding — claude-code#73403."""
    home = tmp_path / "home"
    home.mkdir()

    done = run_entrypoint(tmp_path, home)

    work = str(tmp_path / "klon")
    assert done.stdout.strip() == work, "polecenie fazy dostaje exec w katalogu klonu"
    config = json.loads((home / ".claude.json").read_text(encoding="utf-8"))
    assert config == {"hasCompletedOnboarding": True, "projects": {work: {"hasTrustDialogAccepted": True}}}


def test_entrypoint_leaves_an_existing_or_read_only_config_alone(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    (home / ".claude.json").write_text("{}", encoding="utf-8")
    run_entrypoint(tmp_path, home)
    assert (home / ".claude.json").read_text(encoding="utf-8") == "{}"

    missing = tmp_path / "brak"  # kontener egress: HOME bez zapisu
    run_entrypoint(tmp_path, missing)
    assert not missing.exists()


def test_dockerfile_installs_pinned_semgrep_only_when_asked() -> None:
    """PRB-29: talos z Z8c-2 skanuje kawałek semgrepem; bez binarki w obrazie delivery w kontenerze staje."""
    plain = phase_sandbox.dockerfile("2.1.310", [])
    with_scanner = phase_sandbox.dockerfile("2.1.310", [], semgrep="1.183.0")

    assert "semgrep" not in plain
    assert "python3-venv" in with_scanner
    assert "/opt/semgrep/bin/pip install --no-cache-dir semgrep==1.183.0" in with_scanner
    assert "ln -s /opt/semgrep/bin/semgrep /usr/local/bin/semgrep" in with_scanner
    assert with_scanner.index("semgrep==") < with_scanner.index("\nUSER pdi"), "instalacja jako root, przed USER"


@pytest.mark.parametrize(
    "scanner_path",
    [
        ".claude/skills/tf/scripts/security_scan.py",  # tf 10.0.0+: pętla w rdzeniu fabryki
        ".claude/skills/talos-story-run/scripts/security_scan.py",  # tf 9.x: ścieżka sprzed przeniesienia pętli
    ],
)
def test_image_gets_semgrep_when_the_clone_has_the_loop_scanner(tmp_path: Path, scanner_path: str) -> None:
    repo = make_checkout(tmp_path)
    plain = phase_sandbox.image_for(repo)
    scanner = repo / scanner_path
    scanner.parent.mkdir(parents=True)
    scanner.write_text("# security_scan.py\n", encoding="utf-8")
    with_scanner = phase_sandbox.image_for(repo)

    assert scanner_path in phase_sandbox.LOOP_SCANNERS
    assert "semgrep" not in plain.dockerfile
    assert f"semgrep=={phase_sandbox.SEMGREP_VERSION}" in with_scanner.dockerfile
    assert with_scanner.tag != plain.tag, "nowy tag, więc sdlc up zbuduje obraz sam"


def test_ensure_image_checks_semgrep_in_a_freshly_built_image(tmp_path: Path) -> None:
    repo = make_checkout(tmp_path)
    scanner = repo / phase_sandbox.LOOP_SCANNERS[0]
    scanner.parent.mkdir(parents=True)
    scanner.write_text("# security_scan.py\n", encoding="utf-8")

    run = FakeRun({"docker image inspect": (1, ""), "docker run --rm": (0, "1.183.0\n")})
    tag, built = phase_sandbox.ensure_image(repo, run=run, env={})
    assert built
    (check,) = run.find("docker", "run", "--rm", tag)
    assert run.calls[check][4:] == ["semgrep", "--version"]

    run = FakeRun({"docker image inspect": (1, ""), "docker run --rm": (127, "semgrep: not found")})
    with pytest.raises(phase_sandbox.SandboxError, match="semgrep"):
        phase_sandbox.ensure_image(repo, run=run, env={})


def test_ensure_image_skips_the_semgrep_check_without_the_loop_scanner(tmp_path: Path) -> None:
    repo = make_checkout(tmp_path)
    run = FakeRun({"docker image inspect": (1, "")})
    phase_sandbox.ensure_image(repo, run=run, env={})
    assert not run.find("docker", "run")


def test_claude_version_comes_from_the_installed_workflow_template(tmp_path: Path) -> None:
    repo = make_checkout(tmp_path)
    assert phase_sandbox.claude_version(repo) == phase_sandbox.CLAUDE_VERSION
    template = repo / ".claude/skills/pdi-decisions/templates/sdlc-phase.yml"
    template.parent.mkdir(parents=True)
    template.write_text("      - run: npm install -g @anthropic-ai/claude-code@2.1.399\n", encoding="utf-8")
    assert phase_sandbox.claude_version(repo) == "2.1.399"


def test_product_tools_and_hosts_are_detected_from_the_clone(tmp_path: Path) -> None:
    repo = make_checkout(tmp_path, files=("package.json", "pyproject.toml"))

    assert phase_sandbox.build_tools(repo) == ["python3-pip", "python3-venv"]
    hosts = phase_sandbox.allowed_hosts(repo, {"PDI_DISPATCH_ALLOW_HOSTS": "api.example.com, *.cdn.example.com"})
    assert hosts[0] == "api.anthropic.com"
    for host in ("registry.npmjs.org", "pypi.org", "files.pythonhosted.org", "semgrep.dev", "api.example.com"):
        assert host in hosts
    assert "*.cdn.example.com" in hosts
    assert "github.com" not in hosts


def test_bad_extra_hosts_are_left_out(tmp_path: Path) -> None:
    repo = make_checkout(tmp_path)
    hosts = phase_sandbox.allowed_hosts(repo, {"PDI_DISPATCH_ALLOW_HOSTS": "*,bad host,ok.example.com,-x"})
    assert "ok.example.com" in hosts and "*" not in hosts and "bad host" not in hosts and "-x" not in hosts


def test_image_tag_depends_on_the_dockerfile(tmp_path: Path) -> None:
    repo = make_checkout(tmp_path)
    plain = phase_sandbox.image_for(repo)
    (repo / "go.mod").write_text("module x\n", encoding="utf-8")
    with_go = phase_sandbox.image_for(repo)

    assert plain.tag != with_go.tag
    assert "golang-go" in with_go.dockerfile
    assert re.match(TAG_RE, plain.tag)


def test_ensure_image_builds_only_when_missing(tmp_path: Path) -> None:
    repo = make_checkout(tmp_path)
    contexts: list[set[str]] = []

    def on_build(argv: list[str]) -> None:
        contexts.append({p.name for p in Path(argv[-1]).iterdir()})

    class Recorder(FakeRun):
        def __call__(self, argv: list[str], cwd: Path, env: Mapping[str, str]) -> tuple[int, str]:
            if argv[:2] == ["docker", "build"]:
                on_build(argv)
            return super().__call__(argv, cwd, env)

    run = Recorder()
    tag, built = phase_sandbox.ensure_image(repo, run=run, env={"PATH": "/usr/bin"})
    assert not built and not run.find("docker", "build")

    run = Recorder({"docker image inspect": (1, "")})
    tag2, built = phase_sandbox.ensure_image(repo, run=run, env={"PATH": "/usr/bin"})
    assert built and tag2 == tag
    (build,) = run.find("docker", "build")
    assert run.calls[build][2:4] == ["-t", tag]
    assert contexts == [{"Dockerfile", "egress.py", "entrypoint.py"}]

    run = Recorder({"docker image inspect": (1, ""), "docker build": (1, "no space left")})
    with pytest.raises(phase_sandbox.SandboxError, match="docker build"):
        phase_sandbox.ensure_image(repo, run=run, env={})


# --- ustawienia Claude Code ---


def test_claude_settings_turn_on_the_strict_sandbox_with_the_host_list() -> None:
    settings = phase_sandbox.claude_settings(["api.anthropic.com", "registry.npmjs.org"], ["CLAUDE_CODE_OAUTH_TOKEN"])
    sandbox = settings["sandbox"]

    assert sandbox["enabled"] is True and sandbox["failIfUnavailable"] is True
    assert sandbox["allowUnsandboxedCommands"] is False
    assert sandbox["autoAllowBashIfSandboxed"] is False, "sandbox nie poszerza uprawnień persony"
    assert sandbox["enableWeakerNestedSandbox"] is True
    assert sandbox["network"] == {
        "allowedDomains": ["api.anthropic.com", "registry.npmjs.org"],
        "allowManagedDomainsOnly": True,
    }
    assert "~/.ssh" in sandbox["filesystem"]["denyRead"] and "~/.sdlc" in sandbox["filesystem"]["denyRead"]
    assert sandbox["filesystem"]["allowRead"] == ["~/.claude/projects"], "transkrypty dla run_report.py finish (PRB-34)"
    denied = {e["name"] for e in sandbox["credentials"]["envVars"] if e["mode"] == "deny"}
    assert {"CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"} <= denied
    assert "Read(//proc/**)" in settings["permissions"]["deny"]


def test_settings_and_seccomp_files_sit_next_to_the_log_without_secrets(checkout: Path, tmp_path: Path) -> None:
    run = FakeRun()
    execute(spec(checkout, tmp_path), run)

    runs = tmp_path / "runs"
    settings = runs / "CHG-12-requirements-20261102T100000Z.claude-settings.json"
    seccomp = runs / "CHG-12-requirements-20261102T100000Z.seccomp.json"
    data = json.loads(settings.read_text(encoding="utf-8"))
    assert data["sandbox"]["network"]["allowedDomains"][0] == "api.anthropic.com"
    profile = json.loads(seccomp.read_text(encoding="utf-8"))
    assert profile["defaultAction"] == "SCMP_ACT_ALLOW"
    blocked = {n for rule in profile["syscalls"] for n in rule["names"]}
    assert {"bpf", "kexec_load", "ptrace", "keyctl", "init_module"} <= blocked
    for text in (settings.read_text(encoding="utf-8"), seccomp.read_text(encoding="utf-8")):
        assert OAUTH not in text and "Tajny" not in text
    argv, _ = run.phase_call()
    assert f"seccomp={seccomp}" in argv
    assert f"type=bind,src={settings},dst=/etc/claude-code/managed-settings.json,readonly" in argv


def test_docker_commands_get_path_and_home_to_find_docker_and_its_context(tmp_path: Path) -> None:
    """Na Macu `docker` jest w /usr/local/bin, a kontekst Docker Desktop w ~/.docker — bez PATH i HOME go nie ma."""
    env = {"PATH": "/usr/local/bin:/usr/bin", "HOME": "/Users/ala", "DOCKER_CONTEXT": "desktop-linux", "GH_TOKEN": GH}
    run = FakeRun()
    assert phase_sandbox.docker_problem(run, tmp_path, env) is None
    repo = make_checkout(tmp_path)
    phase_sandbox.ensure_image(repo, run=run, env=env)

    for call_env in run.envs:
        assert call_env["PATH"] == "/usr/local/bin:/usr/bin" and call_env["HOME"] == "/Users/ala"
        assert call_env["DOCKER_CONTEXT"] == "desktop-linux"
        assert "GH_TOKEN" not in call_env


# --- pętla PR po delivery (N2) ---

CUT_PR = "https://github.com/dbqm45/sklep/pull/8"
REVIEW_1 = {
    "status": "ok",
    "review_md": "product",
    "cost_usd": 0.05,
    "findings": [{"id": "R1", "severity": "important", "file": "src/a.js", "line": 2, "body": "brak null"}],
}
REVIEW_2 = {"status": "ok", "review_md": "product", "cost_usd": 0.04, "findings": []}


def test_pr_loop_runs_review_and_fix_in_the_container_without_github_tokens(checkout: Path, tmp_path: Path) -> None:
    persona = {"status": "done", "cost_usd": 0.5}
    run = FakeRun(
        {
            "git for-each-ref": [(0, ""), (0, "story/tsk-1-a\n")],
            "git rev-list --count": (0, "2\n"),
            "git merge-base": (1, ""),
            "gh pr create": (0, CUT_PR + "\n"),
            "docker run --rm": [
                (0, json.dumps(persona)),
                (0, json.dumps(REVIEW_1)),
                (0, json.dumps({"status": "ok", "cost_usd": 0.2})),
                (0, json.dumps(REVIEW_2)),
            ],
            f"python3 {S}/second_review.py comments": (
                0,
                json.dumps(
                    {"status": "ok", "cost_usd": 0.01, "comments": [{"id": "R1", "confirmed": True, "reason": "tak"}]}
                ),
            ),
            "gh pr checks": (0, json.dumps([{"name": "check", "bucket": "pass", "state": "SUCCESS"}])),
            f"gh pr view {CUT_PR}": (0, "# Raport TSK-1\n\nChange: CHG-12\n"),
        }
    )
    env = {**ENV, "OPENAI_API_KEY": "sk-drugi-model"}
    result, lines = execute(spec(checkout, tmp_path, phase="delivery", gate="approve-for-implementation"), run, env)

    assert result["status"] == "done", lines
    entry = result["pr_loop"][CUT_PR]
    assert entry["status"] == "green" and entry["round"] == 2 and entry["fixed"] == ["R1"], entry
    assert result["pr_loop_cost_usd"] == pytest.approx(0.05 + 0.01 + 0.2 + 0.04)
    phase_calls = [i for i, c in enumerate(run.calls) if c[:3] == ["docker", "run", "--rm"]]
    loop_calls = [i for i in phase_calls if any("pr_loop.py" in a for a in run.calls[i])]
    assert len(loop_calls) == 3  # review, fix, review
    for i in loop_calls:
        argv, step_env = run.calls[i], run.envs[i]
        assert GH not in shlex.join(argv) and "GH_TOKEN" not in argv and "GITHUB_TOKEN" not in argv
        assert "GH_TOKEN" not in step_env and "OPENAI_API_KEY" not in step_env
    fix = next(i for i in loop_calls if "fix" in run.calls[i])
    assert "PDI_PR_LOOP_INPUT" in run.calls[fix] and "brak null" in run.envs[fix]["PDI_PR_LOOP_INPUT"]
    assert "--budget-usd" in run.calls[fix]  # budżet fazy minus koszt persony i wcześniejszych kroków
    # poświadczenia tylko na hoście: walidacja z kluczem drugiego modelu, push i gh z tokenem
    validate = next(i for i, c in enumerate(run.calls) if "second_review.py" in " ".join(c))
    assert run.envs[validate].get("OPENAI_API_KEY") == "sk-drugi-model" and "GH_TOKEN" not in run.envs[validate]
    push = run.find("git", "push", "origin", "story/tsk-1-a")
    assert push and run.envs[push[0]].get("GH_TOKEN") == GH
    assert run.envs[run.find("gh", "pr", "checks")[0]].get("GH_TOKEN") == GH
    edits = run.find("gh", "pr", "edit", CUT_PR)
    assert len(edits) == 2 and run.calls[edits[0]][4] == "--body-file"
