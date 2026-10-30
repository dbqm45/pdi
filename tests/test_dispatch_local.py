import json
import os
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from pdi import dispatch_local
from pdi.dispatch import DispatchConfig, dispatch_phase

AT = "2026-10-30T10:00:00Z"
TOKEN = "ghs_tajny_token"  # noqa: S105 — token testowy
PROBLEM = json.dumps({"title": "Tajny opis zgłoszenia", "reported_at": "2026-10-23"}, ensure_ascii=False)
S = ".claude/skills/pdi-decisions/scripts"
PR = "https://github.com/dbqm45/sklep/pull/7"


class FakeRun:
    """Podstawiony wykonawca: zapisuje polecenia, odpowiada według początku polecenia."""

    def __init__(self, responses: dict[str, tuple[int, str]] | None = None) -> None:
        self.responses = {
            "git ls-remote": (2, ""),
            "git diff --cached --quiet": (1, ""),
            "gh pr view": (1, "no pull requests found"),
            "gh pr create": (0, f"Creating pull request\n{PR}\n"),
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
                return self.responses[prefix]
        return 0, ""


class FakeSpawn:
    """Podstawiony start procesu w tle: zapisuje opis i środowisko, opcjonalnie od razu wykonuje przebieg."""

    def __init__(self, run: FakeRun | None = None) -> None:
        self.run = run
        self.specs: list[dict[str, Any]] = []
        self.envs: list[dict[str, str]] = []

    def __call__(self, spec: dict[str, Any], env: dict[str, str]) -> None:
        self.specs.append(spec)
        self.envs.append(env)
        if self.run is not None:
            dispatch_local.finish(spec, env, run=self.run)


def make_checkout(tmp_path: Path) -> Path:
    """Klon repo produktu na potrzeby testów: katalog z `.git` i skryptami pdi-decisions."""
    repo = tmp_path / "sklep"
    (repo / ".git").mkdir(parents=True)
    (repo / S).mkdir(parents=True)
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
        "budget_usd": None,
        "source": None,
        "reported_at": None,
        "ref": "main",
        "checkout": str(checkout),
        "log": str(tmp_path / "runs" / "CHG-12-requirements-20261030T100000Z.log"),
    }
    base.update(overrides)
    return base


def execute(s: dict[str, Any], run: FakeRun, env: dict[str, str] | None = None) -> tuple[dict[str, Any], list[str]]:
    lines: list[str] = []
    result = dispatch_local.execute(s, run=run, env=env or {}, log=lines.append)
    return result, lines


def test_intent_with_source_runs_the_workflow_steps_in_order(checkout: Path, tmp_path: Path) -> None:
    run = FakeRun()
    s = spec(
        checkout,
        tmp_path,
        phase="intent",
        gate="triage",
        decision="DEC-0003",
        source="PRB-1",
        reported_at="2026-10-23",
        budget_usd="3",
    )

    result, _ = execute(s, run)

    assert run.calls == [
        ["git", "status", "--porcelain"],
        ["git", "fetch", "origin"],
        ["git", "switch", "main"],
        ["git", "pull", "--ff-only", "origin", "main"],
        ["git", "ls-remote", "--exit-code", "--heads", "origin", "pdi/CHG-12-intent"],
        ["git", "switch", "-C", "pdi/CHG-12-intent"],
        [
            "python3",
            f"{S}/decision_record.py",
            "change",
            "new",
            "CHG-12",
            "--source",
            "PRB-1",
            "--author",
            "pdi",
            "--source-reported-at",
            "2026-10-23",
        ],
        ["python3", f"{S}/phase_run.py", "prompt", "--change", "CHG-12", "--phase", "intent"],
        [
            "python3",
            f"{S}/decision_record.py",
            "decision",
            "gate",
            "CHG-12",
            "--gate",
            "triage",
            "--outcome",
            "approved",
            "--id",
            "DEC-0003",
        ],
        ["python3", f"{S}/phase_run.py", "run", "--change", "CHG-12", "--phase", "intent", "--budget-usd", "3"],
        ["git", "add", "-A"],
        ["git", "diff", "--cached", "--quiet"],
        ["git", "commit", "-m", "docs(CHG-12): faza intent (pdi)", "-m", "Change: CHG-12"],
        ["git", "push", "-u", "origin", "pdi/CHG-12-intent"],
        ["gh", "pr", "view", "pdi/CHG-12-intent", "--json", "url", "-q", ".url"],
        ["gh", "pr", "create", "--fill", "--head", "pdi/CHG-12-intent"],
        ["python3", f"{S}/phase_run.py", "gate", "request", "--change", "CHG-12", "--phase", "intent", "--url", PR],
    ]
    assert result["status"] == "done"
    assert result["pr"] == PR


def test_existing_change_folder_skips_change_new(checkout: Path, tmp_path: Path) -> None:
    (checkout / "docs/project/changes/CHG-12").mkdir(parents=True)
    run = FakeRun()

    execute(spec(checkout, tmp_path, phase="intent", source="PRB-1"), run)

    assert not any("change" in c and "new" in c for c in run.calls)


def test_rework_reuses_remote_branch_and_existing_pr(checkout: Path, tmp_path: Path) -> None:
    run = FakeRun({"git ls-remote": (0, "abc\trefs/heads/pdi/CHG-12-requirements"), "gh pr view": (0, f"{PR}\n")})
    run.responses["git diff --cached --quiet"] = (0, "")  # nic do zatwierdzenia

    result, _ = execute(spec(checkout, tmp_path, gate="B2", outcome="changes_requested", rework=True), run)

    calls = [" ".join(c) for c in run.calls]
    assert "git switch -C pdi/CHG-12-requirements origin/pdi/CHG-12-requirements" in calls
    assert (
        f"python3 {S}/phase_run.py run --change CHG-12 --phase requirements --rework --gate B2 --decision DEC-0001"
        in calls
    )
    assert not any(c.startswith("git commit") or c.startswith("gh pr create") for c in calls)
    assert not any("change new" in c for c in calls)
    assert calls[-1] == f"python3 {S}/phase_run.py gate request --change CHG-12 --phase requirements --url {PR}"
    assert result["pr"] == PR


def test_delivery_opens_no_pr_and_requests_no_gate(checkout: Path, tmp_path: Path) -> None:
    run = FakeRun()

    result, _ = execute(spec(checkout, tmp_path, phase="delivery", gate="approve-for-implementation"), run)

    assert run.calls[-1] == ["python3", f"{S}/phase_run.py", "run", "--change", "CHG-12", "--phase", "delivery"]
    assert result["status"] == "done"
    assert "pr" not in result


def test_source_and_problem_reach_phase_run_through_env(checkout: Path, tmp_path: Path) -> None:
    run = FakeRun()

    execute(spec(checkout, tmp_path, phase="intent", source="PRB-1"), run, env={"PDI_PROBLEM": PROBLEM, "X": "1"})

    phase_run = run.calls.index(["python3", f"{S}/phase_run.py", "run", "--change", "CHG-12", "--phase", "intent"])
    env = run.envs[phase_run]
    assert (env["PDI_SOURCE"], env["PDI_PROBLEM"], env["X"]) == ("PRB-1", PROBLEM, "1")


@pytest.mark.parametrize(
    ("failing", "step"),
    [
        ("git fetch", "checkout"),
        ("git ls-remote", "branch"),
        (f"python3 {S}/phase_run.py prompt", "prompt"),
        (f"python3 {S}/decision_record.py decision", "decision"),
        (f"python3 {S}/phase_run.py run", "run"),
        ("git commit", "commit"),
        ("git push", "push"),
        ("gh pr create", "pr"),
        (f"python3 {S}/phase_run.py gate", "gate"),
    ],
)
def test_stops_at_first_failing_step_and_names_it(checkout: Path, tmp_path: Path, failing: str, step: str) -> None:
    run = FakeRun()
    run.responses[failing] = (128, "fatal: coś poszło nie tak")

    result, _ = execute(spec(checkout, tmp_path), run)

    assert (result["status"], result["step"]) == ("failed", step)
    assert "128" in result["error"]
    assert " ".join(run.calls[-1]).startswith(failing)


def test_dirty_checkout_fails_the_checkout_step(checkout: Path, tmp_path: Path) -> None:
    run = FakeRun({"git status --porcelain": (0, " M README.md\n")})

    result, _ = execute(spec(checkout, tmp_path), run)

    assert (result["status"], result["step"]) == ("failed", "checkout")
    assert run.calls == [["git", "status", "--porcelain"]]


def test_prompt_output_with_the_problem_stays_out_of_the_log(checkout: Path, tmp_path: Path) -> None:
    run = FakeRun()
    run.responses[f"python3 {S}/phase_run.py prompt"] = (0, "Treść: Tajny opis zgłoszenia")

    _, lines = execute(spec(checkout, tmp_path, phase="intent", source="PRB-1"), run, env={"PDI_PROBLEM": PROBLEM})

    log = "\n".join(lines)
    assert "Tajny opis" not in log
    assert "$ git fetch origin" in log


# --- start ---


def start(checkout: Path | None, tmp_path: Path, **overrides: Any) -> tuple[dict[str, Any], FakeSpawn, FakeRun]:
    run = overrides.pop("run", None) or FakeRun()
    spawn = overrides.pop("spawn", None) or FakeSpawn()
    args: dict[str, Any] = {
        "change": "CHG-12",
        "phase": "requirements",
        "gate": "B1",
        "outcome": "approved",
        "decision": "DEC-0001",
        "rework": False,
        "at": AT,
    }
    args.update(overrides)
    result = dispatch_local.start(
        runs_dir=tmp_path / "rejestr" / "runs",
        checkout=str(checkout) if checkout else None,
        ref="main",
        budget_usd="3",
        run=run,
        spawn=spawn,
        **args,
    )
    return result, spawn, run


def test_start_spawns_a_background_run_and_reports_running(checkout: Path, tmp_path: Path) -> None:
    result, spawn, run = start(checkout, tmp_path)

    log = tmp_path / "rejestr" / "runs" / "CHG-12-requirements-20261030T100000Z.log"
    assert result == {
        "status": "running",
        "mode": "local",
        "phase": "requirements",
        "rework": False,
        "at": AT,
        "log": str(log),
    }
    assert log.is_file()
    assert run.calls == [["git", "status", "--porcelain"]]
    (sent,) = spawn.specs
    assert (sent["change"], sent["phase"], sent["budget_usd"], sent["log"]) == ("CHG-12", "requirements", "3", str(log))
    assert dispatch_local.running(tmp_path / "rejestr" / "runs", "CHG-12") == log


def test_start_passes_reported_day_and_keeps_problem_only_in_env(checkout: Path, tmp_path: Path) -> None:
    result, spawn, _ = start(checkout, tmp_path, phase="intent", gate="triage", source="PRB-1", problem=PROBLEM)

    (sent,), (env,) = spawn.specs, spawn.envs
    assert (sent["source"], sent["reported_at"]) == ("PRB-1", "2026-10-23")
    assert "Tajny opis" not in json.dumps(sent) + json.dumps(result)
    assert env["PDI_PROBLEM"] == PROBLEM
    assert env["PDI_SOURCE"] == "PRB-1"


def test_background_env_has_no_pdi_tokens(checkout: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PDI_GITHUB_TOKEN", TOKEN)
    monkeypatch.setenv("PDI_SHIPSCOPE_TOKEN", TOKEN)
    monkeypatch.setenv("PDI_SHIPSCOPE_SIGNING_SECRET", TOKEN)
    monkeypatch.setenv("PDI_TF_SIGNING_SECRET", "tf-sekret")
    monkeypatch.setenv("PDI_EVENTS_URL", "http://127.0.0.1:8787")
    run = FakeRun()

    result, spawn, _ = start(checkout, tmp_path, spawn=FakeSpawn(run))

    (env,) = spawn.envs
    assert TOKEN not in env.values()
    assert (env["PDI_TF_SIGNING_SECRET"], env["PDI_EVENTS_URL"]) == ("tf-sekret", "http://127.0.0.1:8787")
    log = Path(result["log"]).read_text(encoding="utf-8")
    outcome = Path(result["log"]).with_name(Path(result["log"]).stem + ".result.json").read_text(encoding="utf-8")
    assert TOKEN not in log + outcome + json.dumps(result)


@pytest.mark.parametrize(
    ("make", "fragment"),
    [
        (lambda c: None, "PDI_DISPATCH_CHECKOUT"),
        (lambda c: Path("wzgledna/sciezka"), "bezwzględn"),
        (lambda c: c / "brak", "nie istnieje"),
        (lambda c: c / S, "git"),
    ],
    ids=["brak", "wzgledna", "nie-istnieje", "nie-repo"],
)
def test_start_refuses_without_a_usable_checkout(checkout: Path, tmp_path: Path, make: Any, fragment: str) -> None:
    result, spawn, _ = start(make(checkout), tmp_path)

    assert (result["status"], result["mode"]) == ("failed", "local")
    assert fragment in result["error"]
    assert spawn.specs == []


def test_start_refuses_checkout_without_pdi_scripts(checkout: Path, tmp_path: Path) -> None:
    (checkout / S).rmdir()

    result, spawn, _ = start(checkout, tmp_path)

    assert "pdi-decisions" in result["error"] and spawn.specs == []


def test_start_refuses_a_dirty_checkout(checkout: Path, tmp_path: Path) -> None:
    result, spawn, _ = start(checkout, tmp_path, run=FakeRun({"git status --porcelain": (0, "?? nowy.txt\n")}))

    assert result["status"] == "failed"
    assert "niezatwierdzone" in result["error"]
    assert spawn.specs == []


def test_start_refuses_while_a_phase_of_the_change_runs(checkout: Path, tmp_path: Path) -> None:
    first, _, _ = start(checkout, tmp_path)

    second, spawn, _ = start(checkout, tmp_path, phase="architecture", at="2026-10-30T10:05:00Z")

    assert second["status"] == "failed"
    assert "trwa" in second["error"] and first["log"] in second["error"]
    assert spawn.specs == []


def test_finished_or_stale_run_does_not_block(checkout: Path, tmp_path: Path) -> None:
    runs = tmp_path / "rejestr" / "runs"
    done, _, _ = start(checkout, tmp_path, spawn=FakeSpawn(FakeRun()))
    assert dispatch_local.running(runs, "CHG-12") is None

    stale, _, _ = start(checkout, tmp_path, at="2026-10-30T11:00:00Z")
    old = time.time() - dispatch_local.STALE_SECONDS - 60
    os.utime(stale["log"], (old, old))

    assert dispatch_local.running(runs, "CHG-12") is None
    assert dispatch_local.running(runs, "CHG-1") is None


@pytest.mark.parametrize(
    "overrides",
    [
        {"change": "CHG-12; rm -rf /"},
        {"change": "../CHG-1"},
        {"phase": "deploy"},
        {"gate": "B1 --evil"},
        {"outcome": "maybe"},
        {"decision": "DEC-x"},
        {"source": "PRB-1 x"},
    ],
)
def test_start_refuses_bad_inputs(checkout: Path, tmp_path: Path, overrides: dict[str, Any]) -> None:
    result, spawn, run = start(checkout, tmp_path, **overrides)

    assert result["status"] == "failed"
    assert spawn.specs == [] and run.calls == []


def test_bad_budget_is_refused(checkout: Path, tmp_path: Path) -> None:
    result = dispatch_local.start(
        runs_dir=tmp_path / "runs",
        checkout=str(checkout),
        ref="main",
        budget_usd="5; echo",
        change="CHG-12",
        phase="requirements",
        gate="B1",
        outcome="approved",
        decision="DEC-0001",
        rework=False,
        at=AT,
        run=FakeRun(),
        spawn=FakeSpawn(),
    )

    assert result["status"] == "failed" and "PDI_PHASE_BUDGET_USD" in result["error"]


# --- settle ---


def test_settle_turns_running_into_done_with_pr(checkout: Path, tmp_path: Path) -> None:
    dispatch, _, _ = start(checkout, tmp_path, spawn=FakeSpawn(FakeRun()))
    state = {"change": "CHG-12", "history": [], "dispatch": {**dispatch, "gate": "B1"}}

    settled = dispatch_local.settle(state)

    assert settled["dispatch"]["status"] == "done"
    assert settled["dispatch"]["pr"] == PR
    assert settled["dispatch"]["gate"] == "B1"
    assert settled["history"][-1]["what"] == "dispatch.done"
    assert state["dispatch"]["status"] == "running", "settle zwraca kopię"


def test_settle_records_failed_step(checkout: Path, tmp_path: Path) -> None:
    run = FakeRun()
    run.responses["git push"] = (1, "rejected")
    dispatch, _, _ = start(checkout, tmp_path, spawn=FakeSpawn(run))

    settled = dispatch_local.settle({"change": "CHG-12", "history": [], "dispatch": dispatch})

    assert (settled["dispatch"]["status"], settled["dispatch"]["step"]) == ("failed", "push")
    assert settled["history"][-1]["what"] == "dispatch.failed"


def test_settle_fails_a_stale_run_without_result(checkout: Path, tmp_path: Path) -> None:
    dispatch, _, _ = start(checkout, tmp_path)
    old = time.time() - dispatch_local.STALE_SECONDS - 60
    os.utime(dispatch["log"], (old, old))

    settled = dispatch_local.settle({"change": "CHG-12", "history": [], "dispatch": dispatch})

    assert settled["dispatch"]["status"] == "failed"
    assert "wyniku" in settled["dispatch"]["error"]


def test_settle_leaves_other_states_alone(checkout: Path, tmp_path: Path) -> None:
    remote = {"change": "CHG-12", "history": [], "dispatch": {"status": "sent", "phase": "intent"}}
    running, _, _ = start(checkout, tmp_path)
    still = {"change": "CHG-12", "history": [], "dispatch": running}

    assert dispatch_local.settle(remote) is remote
    assert dispatch_local.settle(still) is still
    assert dispatch_local.settle({"change": "CHG-1", "history": []})["change"] == "CHG-1"


# --- dispatch_phase ---


def test_dispatch_phase_in_local_mode_needs_no_repo_or_token(checkout: Path, tmp_path: Path) -> None:
    spawn = FakeSpawn()
    cfg = DispatchConfig(repo=None, mode="local", checkout=str(checkout), budget_usd="3")

    result = dispatch_phase(
        cfg,
        change="CHG-12",
        phase="requirements",
        gate="B1",
        outcome="approved",
        decision="DEC-0001",
        rework=False,
        at=AT,
        runs_dir=tmp_path / "runs",
        spawn=spawn,
        run=FakeRun(),
    )

    assert (result["status"], result["mode"]) == ("running", "local")
    assert spawn.specs[0]["budget_usd"] == "3"


def test_unknown_dispatch_mode_is_refused(tmp_path: Path) -> None:
    cfg = DispatchConfig(repo="dbqm45/sklep", token=TOKEN, mode="cloud")

    result = dispatch_phase(
        cfg,
        change="CHG-12",
        phase="requirements",
        gate="B1",
        outcome="approved",
        decision="DEC-0001",
        rework=False,
        at=AT,
        post=lambda *_: pytest.fail("nie wysyła"),  # type: ignore[arg-type,return-value]
    )

    assert result["status"] == "failed" and "PDI_DISPATCH" in result["error"]


def test_config_reads_local_mode_from_env(monkeypatch: pytest.MonkeyPatch, checkout: Path) -> None:
    monkeypatch.setenv("PDI_DISPATCH", "local")
    monkeypatch.setenv("PDI_DISPATCH_CHECKOUT", str(checkout))

    cfg = DispatchConfig.from_env()

    assert (cfg.mode, cfg.checkout, cfg.local) == ("local", str(checkout), True)


def test_config_without_mode_is_todays(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PDI_DISPATCH", raising=False)
    monkeypatch.delenv("PDI_DISPATCH_CHECKOUT", raising=False)

    cfg = DispatchConfig.from_env()

    assert (cfg.mode, cfg.checkout, cfg.local) == (None, None, False)
