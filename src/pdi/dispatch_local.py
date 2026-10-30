"""Faza tf uruchamiana przez pdi na tym komputerze (`PDI_DISPATCH=local`, krok L2, decyzja DL1).

Tylko do rozwoju i prób: na produkcji fazy idą przez GitHub Actions (`sdlc-phase.yml`, R4). Przebieg robi w lokalnym
klonie repo produktu (`PDI_DISPATCH_CHECKOUT`) te same kroki i w tej samej kolejności co szablon fazy w tf: czysty
klon i świeży `main`, gałąź `pdi/<CHG>-<faza>`, dziennik zmiany ze zgłoszenia, sprawdzenie wejść, decyzja z bramki,
`phase_run.py run`, commit, push, PR przez `gh` i `gate request` do pdi.

`start()` sprawdza wejścia i klon, po czym uruchamia odłączony proces (`python -m pdi.dispatch_local`) i od razu
zwraca `running`, więc wywołanie MCP i odbiornik odpowiadają bez czekania. Jeden przebieg naraz na zmianę. Proces w
tle pisze log `runs/<CHG>-<faza>-<czas>.log` i wynik obok (`….result.json`); stanu zmiany nie zapisuje — wynik dopisuje
do niego `settle()` przy odczycie (`pdi.changes`). Każde polecenie to lista argumentów, nigdy tekst dla powłoki. Do logu
i stanu pdi nie dopisuje tokenów ani treści zgłoszenia (ta idzie do persony tylko przez `PDI_PROBLEM`).
"""

from __future__ import annotations

import copy
import json
import os
import re
import shlex
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pdi import contract, flow

Run = Callable[[list[str], Path, Mapping[str, str]], tuple[int, str]]
Spawn = Callable[[dict[str, Any], dict[str, str]], None]

PHASES = ("intent", "requirements", "architecture", "design", "delivery")
GATES = (*(g.name for g in flow.GATES), "triage")
SCRIPTS = ".claude/skills/pdi-decisions/scripts"
STEP_TIMEOUT_SECONDS = 2 * 60 * 60
# Log przebiegu zmienia się przy każdym kroku; bez zmian dłużej niż to — przebieg uznaje się za przerwany.
STALE_SECONDS = 3 * 60 * 60
LOCK_STALE_SECONDS = 60
# Sekret odbiornika potrzebny do `phase_run.py gate request`; pozostałe tokeny i sekrety pdi nie idą do przebiegu.
KEPT_SECRETS = ("PDI_TF_SIGNING_SECRET",)

_PREFIXES = contract.settings()["prefixes"]
_CHANGE = re.compile(rf"^{_PREFIXES['change']}-[0-9]{{1,9}}$")
_PROBLEM = re.compile(rf"^{_PREFIXES['problem']}-[0-9]{{1,9}}$")
_DECISION = re.compile(rf"^{_PREFIXES['decision']}-[0-9]{{1,9}}$")
_BUDGET = re.compile(r"^[0-9]{1,6}(\.[0-9]{1,2})?$")
_REF = re.compile(r"^(?!.*\.\.)[A-Za-z0-9_./-]{1,200}$")
_DAY = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


class _StepFailed(Exception):
    def __init__(self, step: str, error: str) -> None:
        super().__init__(error)
        self.step = step
        self.error = error


# --- start (w procesie pdi) ---


def start(
    *,
    runs_dir: Path,
    checkout: str | None,
    ref: str,
    budget_usd: str | None,
    change: str,
    phase: str,
    gate: str,
    outcome: str,
    decision: str,
    rework: bool,
    at: str,
    source: str | None = None,
    problem: str | None = None,
    run: Run | None = None,
    spawn: Spawn | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Uruchamia fazę w tle; wynik `{"mode": "local", "status": running | failed, …}` do zapisu w stanie zmiany."""
    result: dict[str, Any] = {"status": "failed", "mode": "local", "phase": phase, "rework": rework, "at": at}
    error = _bad_input(change, phase, gate, outcome, decision, source, budget_usd, ref) or _bad_checkout(checkout)
    if error:
        return {**result, "error": error}
    assert checkout is not None  # noqa: S101 — sprawdzone w _bad_checkout
    code, out = (run or _run)(["git", "status", "--porcelain"], Path(checkout), dict(environ or os.environ))
    if code != 0:
        return {**result, "error": f"git status w {checkout} zakończony kodem {code}."}
    if out.strip():
        return {**result, "error": f"Klon {checkout} ma niezatwierdzone zmiany — zatwierdź je albo odłóż i ponów."}

    runs_dir.mkdir(parents=True, exist_ok=True)
    lock = runs_dir / f"{change}.lock"
    if not _take(lock):
        return {**result, "error": f"{change}: inny start fazy właśnie trwa — ponów za chwilę."}
    try:
        busy = running(runs_dir, change)
        if busy is not None:
            return {**result, "error": f"{change}: trwa poprzednia faza (log {busy}) — poczekaj na jej koniec."}
        log = _new_log(runs_dir, change, phase, at)
        spec = {
            "change": change,
            "phase": phase,
            "gate": gate,
            "outcome": outcome,
            "decision": decision,
            "rework": rework,
            "budget_usd": budget_usd,
            "source": source,
            "reported_at": _reported_at(problem),
            "ref": ref,
            "checkout": checkout,
            "log": str(log),
        }
        try:
            (spawn or _spawn)(spec, child_env(environ or os.environ, source=source, problem=problem))
        except OSError as e:
            _write_result(log, {"status": "failed", "step": "start", "error": f"Nie udało się uruchomić: {e}"})
            return {
                **result,
                "log": str(log),
                "error": f"Nie udało się uruchomić przebiegu w tle ({type(e).__name__}).",
            }
    finally:
        lock.unlink(missing_ok=True)
    return {**result, "status": "running", "log": str(log)}


def child_env(environ: Mapping[str, str], *, source: str | None, problem: str | None) -> dict[str, str]:
    """Środowisko przebiegu: bez tokenów i sekretów pdi, z `PDI_SOURCE` i `PDI_PROBLEM` dla persony fazy intent."""
    env = {k: v for k, v in environ.items() if not _secret(k)}
    env.pop("PDI_PROBLEM", None)
    env.pop("PDI_SOURCE", None)
    if source:
        env["PDI_SOURCE"] = source
    if problem:
        env["PDI_PROBLEM"] = problem
    return env


def running(runs_dir: Path, change: str) -> Path | None:
    """Log trwającego przebiegu zmiany (bez wyniku, zmieniany w ostatnich STALE_SECONDS) albo None."""
    if not runs_dir.is_dir():
        return None
    for log in sorted(runs_dir.glob(f"{change}-*.log"), reverse=True):
        if not result_path(log).exists() and _fresh(log):
            return log
    return None


def result_path(log: Path) -> Path:
    return log.with_name(log.stem + ".result.json")


def settle(state: dict[str, Any]) -> dict[str, Any]:
    """Stan z wynikiem zakończonego przebiegu (`running` → `done` / `failed`) albo ten sam obiekt bez zmian."""
    dispatch = state.get("dispatch")
    if not isinstance(dispatch, dict) or dispatch.get("mode") != "local" or dispatch.get("status") != "running":
        return state
    log = Path(str(dispatch.get("log") or ""))
    outcome: dict[str, Any]
    if result_path(log).is_file():
        try:
            outcome = json.loads(result_path(log).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            outcome = {"status": "failed", "error": "Uszkodzony plik wyniku przebiegu — szczegóły w logu."}
        if not isinstance(outcome, dict) or outcome.get("status") not in ("done", "failed"):
            outcome = {"status": "failed", "error": "Uszkodzony plik wyniku przebiegu — szczegóły w logu."}
    elif _fresh(log):
        return state
    else:
        outcome = {"status": "failed", "error": "Przebieg nie zostawił wyniku (przerwany?) — szczegóły w logu."}
    new = copy.deepcopy(state)
    keep = ("status", "finished_at", "pr", "step", "error")
    new["dispatch"] = {**dispatch, **{k: outcome[k] for k in keep if outcome.get(k)}}
    entry = {"at": outcome.get("finished_at") or dispatch.get("at"), "what": f"dispatch.{new['dispatch']['status']}"}
    new.setdefault("history", []).append({**entry, "phase": dispatch.get("phase")})
    return new


def _bad_input(
    change: str,
    phase: str,
    gate: str,
    outcome: str,
    decision: str,
    source: str | None,
    budget_usd: str | None,
    ref: str,
) -> str | None:
    if not _CHANGE.match(change):
        return f"„{change}” nie jest kluczem zmiany (np. CHG-12)."
    if phase not in PHASES:
        return f"Faza musi być jedną z: {', '.join(PHASES)}."
    if gate not in GATES:
        return f"Bramka „{gate}” nie uruchamia fazy tf."
    if outcome not in flow.OUTCOMES:
        return f"Wynik bramki musi być jednym z: {', '.join(flow.OUTCOMES)}."
    if decision and not _DECISION.match(decision):
        return f"„{decision}” nie jest numerem decyzji (np. DEC-0001)."
    if source and not _PROBLEM.match(source):
        return f"„{source}” nie jest kluczem zgłoszenia (np. PRB-3)."
    if budget_usd and not _BUDGET.match(budget_usd):
        return "PDI_PHASE_BUDGET_USD musi być kwotą w USD, np. 3 albo 2.50."
    if not _REF.match(ref) or ref.startswith("-"):
        return "PDI_DISPATCH_REF nie jest poprawną nazwą gałęzi."
    return None


def _bad_checkout(checkout: str | None) -> str | None:
    if not checkout:
        return "Brak PDI_DISPATCH_CHECKOUT — ścieżki klonu repo produktu dla PDI_DISPATCH=local."
    path = Path(checkout)
    if not path.is_absolute():
        return "PDI_DISPATCH_CHECKOUT musi być ścieżką bezwzględną."
    if not path.is_dir():
        return f"PDI_DISPATCH_CHECKOUT: {checkout} nie istnieje."
    if not (path / ".git").exists():
        return f"PDI_DISPATCH_CHECKOUT: {checkout} nie jest repozytorium git."
    if not (path / SCRIPTS).is_dir():
        return f"PDI_DISPATCH_CHECKOUT: w {checkout} brak {SCRIPTS} (tf z trybem mode-pdi, skill pdi-decisions)."
    return None


def _secret(name: str) -> bool:
    return name.startswith("PDI_") and name.endswith(("_TOKEN", "_SECRET")) and name not in KEPT_SECRETS


def _reported_at(problem: str | None) -> str | None:
    """Dzień zgłoszenia z treści zgłoszenia (JSON z pdi) — do `--source-reported-at`."""
    try:
        data = json.loads(problem or "{}")
    except ValueError:
        return None
    day = data.get("reported_at") if isinstance(data, dict) else None
    return day if isinstance(day, str) and _DAY.match(day) else None


def _take(lock: Path) -> bool:
    for _ in range(2):
        try:
            os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600))
            return True
        except FileExistsError:
            try:
                if time.time() - lock.stat().st_mtime < LOCK_STALE_SECONDS:
                    return False
                lock.unlink(missing_ok=True)
            except FileNotFoundError:
                continue
    return False


def _new_log(runs_dir: Path, change: str, phase: str, at: str) -> Path:
    stamp = re.sub(r"[^0-9TZ]", "", at) or "0"
    for n in range(1, 100):
        log = runs_dir / f"{change}-{phase}-{stamp}{'' if n == 1 else f'-{n}'}.log"
        try:
            os.close(os.open(log, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600))
            return log
        except FileExistsError:
            continue
    raise FileExistsError(f"{runs_dir}: za dużo przebiegów {change}-{phase} z chwili {at}")


def _fresh(log: Path) -> bool:
    try:
        return time.time() - log.stat().st_mtime < STALE_SECONDS
    except OSError:
        return False


def _spawn(spec: dict[str, Any], env: dict[str, str]) -> None:
    """Odłączony proces `python -I -m pdi.dispatch_local`; opis przebiegu na stdin, wyjście procesu do logu."""
    log = Path(spec["log"])
    with log.open("ab") as out:
        process = subprocess.Popen(  # noqa: S603 — stała lista argumentów
            [sys.executable, "-I", "-m", "pdi.dispatch_local"],
            stdin=subprocess.PIPE,
            stdout=out,
            stderr=subprocess.STDOUT,
            cwd=log.parent,
            env=env,
            start_new_session=True,
        )
    assert process.stdin is not None  # noqa: S101 — stdin=PIPE
    process.stdin.write(json.dumps(spec).encode())
    process.stdin.close()
    # Odbiera kod wyjścia, żeby po zakończeniu nie został proces-zombie.
    threading.Thread(target=process.wait, daemon=True).start()


# --- przebieg (w procesie w tle) ---


def execute(spec: dict[str, Any], *, run: Run, env: Mapping[str, str], log: Callable[[str], None]) -> dict[str, Any]:
    """Kroki szablonu `sdlc-phase.yml`; wynik `{"status": done | failed, "step"?, "error"?, "pr"?}`."""
    cwd = Path(spec["checkout"])
    change, phase, ref = spec["change"], spec["phase"], spec["ref"]
    branch = f"pdi/{change}-{phase}"
    env = {**env, "PDI_SOURCE": spec.get("source") or ""}

    def step(name: str, argv: list[str], *, ok: tuple[int, ...] = (0,), quiet: bool = False) -> tuple[int, str]:
        log("$ " + shlex.join(argv))
        code, out = run(argv, cwd, env)
        if out.strip() and not (quiet and code in ok):
            log(out.rstrip("\n"))
        if code not in ok:
            raise _StepFailed(name, f"Krok {name}: `{shlex.join(argv)}` zakończone kodem {code} — szczegóły w logu.")
        return code, out

    def script(name: str, *args: str) -> list[str]:
        return ["python3", f"{SCRIPTS}/{name}", *args]

    try:
        _, dirty = step("checkout", ["git", "status", "--porcelain"])
        if dirty.strip():
            raise _StepFailed("checkout", "Klon ma niezatwierdzone zmiany — zatwierdź je albo odłóż i ponów.")
        step("checkout", ["git", "fetch", "origin"])
        step("checkout", ["git", "switch", ref])
        step("checkout", ["git", "pull", "--ff-only", "origin", ref])

        code, _ = step("branch", ["git", "ls-remote", "--exit-code", "--heads", "origin", branch], ok=(0, 2))
        if code == 0:  # poprawki trafiają do tego samego PR
            step("branch", ["git", "switch", "-C", branch, f"origin/{branch}"])
        else:
            step("branch", ["git", "switch", "-C", branch])

        source = spec.get("source")
        if phase == "intent" and source and not (cwd / "docs/project/changes" / change).is_dir():
            args = ["--source", source, "--author", "pdi"]
            if spec.get("reported_at"):
                args += ["--source-reported-at", spec["reported_at"]]
            step("change", script("decision_record.py", "change", "new", change, *args))

        # Wynik `prompt` zawiera treść zgłoszenia — do logu trafia tylko przy błędzie (komunikat sprawdzenia).
        step("prompt", script("phase_run.py", "prompt", "--change", change, "--phase", phase), quiet=True)
        if spec.get("decision"):
            gate_args = ["--gate", spec["gate"], "--outcome", spec["outcome"], "--id", spec["decision"]]
            step("decision", script("decision_record.py", "decision", "gate", change, *gate_args))

        args = ["--change", change, "--phase", phase]
        if spec.get("rework"):
            args += ["--rework", "--gate", spec["gate"], "--decision", spec["decision"]]
        if spec.get("budget_usd"):
            args += ["--budget-usd", spec["budget_usd"]]
        step("run", script("phase_run.py", "run", *args))

        if phase == "delivery":
            return {"status": "done"}
        step("commit", ["git", "add", "-A"])
        code, _ = step("commit", ["git", "diff", "--cached", "--quiet"], ok=(0, 1))
        if code == 1:
            step("commit", ["git", "commit", "-m", f"docs({change}): faza {phase} (pdi)", "-m", f"Change: {change}"])
        step("push", ["git", "push", "-u", "origin", branch])
        code, out = step("pr", ["gh", "pr", "view", branch, "--json", "url", "-q", ".url"], ok=(0, 1))
        url = _url(out) if code == 0 else None
        if not url:
            _, out = step("pr", ["gh", "pr", "create", "--fill", "--head", branch])
            url = _url(out)
        if not url:
            raise _StepFailed("pr", "Krok pr: gh nie podał adresu PR — szczegóły w logu.")
        step("gate", script("phase_run.py", "gate", "request", "--change", change, "--phase", phase, "--url", url))
        return {"status": "done", "pr": url}
    except _StepFailed as e:
        log(f"# błąd: {e.error}")
        return {"status": "failed", "step": e.step, "error": e.error}


def finish(spec: dict[str, Any], env: Mapping[str, str], *, run: Run) -> dict[str, Any]:
    """Wykonuje przebieg z logiem w `spec["log"]` i zapisuje wynik obok; zwraca wynik."""
    log_path = Path(spec["log"])
    with log_path.open("a", encoding="utf-8") as f:

        def log(line: str) -> None:
            f.write(line + "\n")
            f.flush()

        log(f"# pdi: {spec['change']} faza {spec['phase']} w {spec['checkout']}")
        try:
            result = execute(spec, run=run, env=env, log=log)
        except Exception as e:  # noqa: BLE001 — każdy błąd programu kończy przebieg wynikiem, nie wiszącym `running`
            result = {"status": "failed", "step": "internal", "error": f"Błąd pdi: {type(e).__name__}."}
        log(f"# koniec: {result['status']}")
    return _write_result(log_path, result)


def _write_result(log: Path, result: dict[str, Any]) -> dict[str, Any]:
    result = {**result, "finished_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")}
    tmp = log.with_name(log.stem + ".result.tmp")
    tmp.write_text(json.dumps(result, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(result_path(log))
    return result


def _url(out: str) -> str | None:
    lines = [line.strip() for line in out.splitlines() if line.strip().startswith("https://")]
    return lines[-1] if lines else None


def _run(argv: list[str], cwd: Path, env: Mapping[str, str]) -> tuple[int, str]:
    try:
        done = subprocess.run(  # noqa: S603 — lista argumentów, bez powłoki
            argv,
            cwd=cwd,
            env=dict(env),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=STEP_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError:
        return 127, f"brak polecenia {argv[0]}"
    except subprocess.TimeoutExpired:
        return 124, f"przekroczony czas kroku ({STEP_TIMEOUT_SECONDS} s)"
    return done.returncode, done.stdout or ""


def main() -> None:
    finish(json.loads(sys.stdin.read()), dict(os.environ), run=_run)


if __name__ == "__main__":
    main()
