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

Krok `run` (persona, talos) działa domyślnie w kontenerze Docker, który widzi tylko klon i listę hostów sieci
(`pdi.phase_sandbox`, krok Z8a, decyzja DZ9); pozostałe kroki — z poświadczeniami — zostają na tym komputerze.
"""

from __future__ import annotations

import contextlib
import copy
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Iterator, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pdi import contract, flow, phase_sandbox, pr_loop

Run = Callable[[list[str], Path, Mapping[str, str]], tuple[int, str]]
# Jak Run, ale każdą linię wyjścia oddaje od razu (do logu), zanim krok się skończy (PRB-6).
StreamRun = Callable[[list[str], Path, Mapping[str, str], Callable[[str], None]], tuple[int, str]]
Spawn = Callable[[dict[str, Any], dict[str, str]], None]

PHASES = ("intent", "requirements", "architecture", "design", "delivery")
GATES = (*(g.name for g in flow.GATES), "triage")
SCRIPTS = ".claude/skills/pdi-decisions/scripts"
STEP_TIMEOUT_SECONDS = 2 * 60 * 60
# Co tyle sekund długi krok zostawia w logu znak życia (persona pracuje bez wyjścia nawet kilkadziesiąt minut).
HEARTBEAT_SECONDS = 60.0
# Artefakt poprzedniej fazy, który musi być na `ref` przed startem fazy (PRB-2).
PRIOR_ARTIFACT = {
    "requirements": "intent.md",
    "architecture": "requirements.md",
    "design": "plan.md",
    "delivery": "plan.md",
}
DECISION_TEXT_MAX = 2000
# Gałęzie cięć talosa (`talos-story-run`: story/<slug>); persona w trybie --print nie może ich wypchnąć (PRB-4).
CUT_REFS = "refs/heads/story/"
_CUT = re.compile(r"^story/[A-Za-z0-9_][A-Za-z0-9._/-]{0,199}$")
_CUT_TASK = re.compile(r"^story/(tsk-[0-9]+)(?:-|$)", re.IGNORECASE)  # klucz cięcia z nazwy gałęzi Talosa
# Log przebiegu zmienia się przy każdym kroku; bez zmian dłużej niż to — przebieg uznaje się za przerwany.
STALE_SECONDS = 3 * 60 * 60
LOCK_STALE_SECONDS = 60
# Sekret odbiornika potrzebny do `phase_run.py gate request`; pozostałe tokeny i sekrety pdi nie idą do przebiegu.
KEPT_SECRETS = ("PDI_TF_SIGNING_SECRET",)
# Jak w sdlc-phase.yml: sekret i adres odbiornika ma tylko krok `gate request`, a treść zgłoszenia tylko kroki, które
# ją czytają (`phase_run.py prompt` i `run`). Persona fazy nie może więc sama podpisać zdarzenia dla pdi.
GATE_ENV = ("PDI_TF_SIGNING_SECRET", "PDI_EVENTS_URL")
PROBLEM_ENV = ("PDI_SOURCE", "PDI_PROBLEM")
# Reszty środowiska pdi kroki nie dostają: tylko zmienne systemowe, a logowanie narzędzi tam, gdzie narzędzie działa.
# Inne klucze z powłoki (chmura, bazy danych, API) do persony nie trafiają; świadomie przepuszcza się je przez
# PDI_DISPATCH_ENV_PASS (nazwy po przecinku), do każdego kroku.
SYSTEM_ENV = (
    "PATH", "HOME", "USER", "LOGNAME", "SHELL", "LANG", "LANGUAGE", "TERM", "TMPDIR", "TZ", "SSH_AUTH_SOCK",
    "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME", "XDG_RUNTIME_DIR", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY",
    "http_proxy", "https_proxy", "no_proxy", "SSL_CERT_FILE", "SSL_CERT_DIR", "NODE_EXTRA_CA_CERTS",
)  # fmt: skip
SYSTEM_PREFIXES = ("LC_", "GIT_")
GITHUB_ENV = ("GH_TOKEN", "GITHUB_TOKEN", "GH_HOST", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN", "GH_CONFIG_DIR")
CLAUDE_PREFIXES = ("ANTHROPIC_", "CLAUDE_")
# Claude Code przez Bedrock albo Vertex: dane chmury tylko z włączonym przełącznikiem.
CLOUD_PREFIXES = {"CLAUDE_CODE_USE_BEDROCK": ("AWS_",), "CLAUDE_CODE_USE_VERTEX": ("GOOGLE_", "CLOUD_ML_", "GCLOUD_")}
EXTRA_ENV_NAMES = "PDI_DISPATCH_ENV_PASS"  # noqa: S105 — nazwa zmiennej, nie hasło
# Drugi przegląd (pdi plan-zespol-jednoosobowy §8.3 N1, DZ12): klucz dostawcy widoczny TYLKO dla kroku „second-review"
# na hoście, nigdy w kontenerze persony (Z8g). PDI_SECOND_MODEL* — konfiguracja, OPENAI_API_KEY/ANTHROPIC_API_KEY —
# klucze. Gdy żadnego klucza nie ma, second_review.py zapisze `status: unavailable, reason: no_api_key`, a phase_run.py
# gate request pokaże to w prośbie o bramkę — niedostępność drugiego przeglądu zawsze jest widoczna, nigdy cichego OK.
SECOND_REVIEW_PHASES = ("requirements", "architecture")
SECOND_REVIEW_ENV = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "PDI_SECOND_MODEL",
    "PDI_SECOND_MODEL_PRICE_IN",
    "PDI_SECOND_MODEL_PRICE_OUT",
)

# Pętla PR talosa po delivery (N2, docs/plan-n2-petla-pr.md): przegląd, poprawki i lokalna weryfikacja w kontenerze
# fazy, walidacja uwag drugim modelem, push, checki i opis PR na hoście. PDI_PR_LOOP=off wyłącza pętlę.
PR_LOOP_ENV = "PDI_PR_LOOP"
PR_LOOP_ROUNDS_ENV = "PDI_PR_LOOP_ROUNDS"
CHECKS_WAIT_ENV, CHECKS_GRACE_ENV, CHECKS_INTERVAL_ENV = (
    "PDI_PR_LOOP_CHECKS_WAIT",
    "PDI_PR_LOOP_CHECKS_GRACE",
    "PDI_PR_LOOP_CHECKS_INTERVAL",
)
CHECKS_WAIT_SECONDS, CHECKS_GRACE_SECONDS, CHECKS_INTERVAL_SECONDS = 1200, 120, 30
CI_LOG_LINES, CI_LOG_MAX = 200, 20_000
CONTEXT_LINES = 12  # wiersze kodu wokół uwagi dla drugiego modelu (walidacja ma widzieć, czego uwaga dotyczy)
_PR_NUMBER = re.compile(r"/pull/([0-9]{1,9})/?$")
ANY_CODE = tuple(range(256))

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
        self.persona: dict[str, Any] | None = None  # co persona zgłosiła, gdy faza padła po kroku run (PRB-32)
        self.pr: str | None = None  # PR fazy, gdy padła dopiero prośba o bramkę (retry ponawia tylko ją)


PERSONA_KEYS = ("status", "cost_usd", "detail", "permission_denials")
# Linia postępu fazy (Z3-lokalnie, A7): tf wypisuje `PDI-PROGRESS: {json}` na stdout kroku `run`.
# pdi po stronie hosta łapie je i zapisuje obok logu — konsola czyta je strumieniem (SSE).
PROGRESS_PREFIX = "PDI-PROGRESS: "
PROGRESS_STATUSES = ("started", "in_progress", "waiting_gate", "done", "failed")


def _persona_report(output: str) -> dict[str, Any] | None:
    """Wynik `phase_run.py run` (ostatni obiekt JSON w wyjściu kroku, pomijając linie `PDI-PROGRESS:`): status, koszt,
    końcówka odpowiedzi persony i odmowy uprawnień. Bez tego `result.json` nieudanego delivery nie mówi, dlaczego Talos
    nie zostawił cięć. Linie postępu nigdy nie zaczynają się od `{` — rzetelnie je pomijamy przy wyszukiwaniu końcowego
    obiektu JSON."""
    lines = [ln for ln in output.splitlines() if not ln.startswith(PROGRESS_PREFIX)]
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].startswith("{"):
            try:
                data = json.loads("\n".join(lines[i:]))
            except ValueError:
                continue
            if isinstance(data, dict):
                kept = {k: data[k] for k in PERSONA_KEYS if data.get(k) is not None}
                return kept or None
    return None


def progress_path(log: Path) -> Path:
    """Plik linii postępu obok logu przebiegu (jedna linia = jeden słownik JSON)."""
    return log.with_name(log.stem + ".progress.jsonl")


def _valid_progress(row: Any) -> bool:
    """Minimalny checker linii postępu (`run_progress`): wymagane `phase`, `status`; typy pól opcjonalnych."""
    if not isinstance(row, dict):
        return False
    if not isinstance(row.get("phase"), str) or not row["phase"]:
        return False
    if row.get("status") not in PROGRESS_STATUSES:
        return False
    for key in ("cost_usd", "budget_usd"):
        value = row.get(key)
        if value is not None and (not isinstance(value, (int, float)) or value < 0):
            return False
    for key in ("change", "task", "slice", "message", "url"):
        value = row.get(key)
        if value is not None and not isinstance(value, str):
            return False
    return True


def last_progress_of(log: Path) -> dict[str, Any] | None:
    """Ostatnia poprawna linia z `<log>.progress.jsonl` (słownik), albo None."""
    path = progress_path(log)
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    for line in reversed(text.splitlines()):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if _valid_progress(row):
            return dict(row)  # mypy: _valid_progress gwarantuje dict[str, Any]
    return None


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
    decision_text: str | None = None,
    answers: list[dict[str, str]] | None = None,
    decisions: list[dict[str, Any]] | None = None,
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
    environ = environ or os.environ
    try:
        sandbox = phase_sandbox.mode(environ)  # Z8a: krok run w kontenerze; bez Dockera odmowa, nie cichy powrót
    except phase_sandbox.SandboxError as e:
        return {**result, "error": str(e)}
    if sandbox == "docker":
        problem_text = phase_sandbox.docker_problem(run or _run, Path(checkout), dict(environ))
        if problem_text:
            return {**result, "error": problem_text}

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
            "decision_text": (decision_text or "")[:DECISION_TEXT_MAX] or None,
            # Z1: odpowiedzi na pytania bramki i decyzje zmiany z rejestru (pdi.phase_decisions, już przycięte).
            "answers": answers or None,
            "decisions": decisions or None,
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
    loop = read_pr_loop(log)
    outcome: dict[str, Any]
    if result_path(log).is_file():
        try:
            outcome = json.loads(result_path(log).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            outcome = {"status": "failed", "error": "Uszkodzony plik wyniku przebiegu — szczegóły w logu."}
        if not isinstance(outcome, dict) or outcome.get("status") not in ("done", "failed"):
            outcome = {"status": "failed", "error": "Uszkodzony plik wyniku przebiegu — szczegóły w logu."}
    elif _fresh(log):
        if not loop:
            return state
        live = copy.deepcopy(state)  # pętla PR w toku — runda i status widać na tablicy przed końcem przebiegu
        live["pr_loop"] = {**(state.get("pr_loop") or {}), **loop}
        return live
    else:
        outcome = {"status": "failed", "error": "Przebieg nie zostawił wyniku (przerwany?) — szczegóły w logu."}
    new = copy.deepcopy(state)
    keep = ("status", "finished_at", "pr", "prs", "cuts", "step", "error", "persona", "pr_loop_cost_usd")
    new["dispatch"] = {**dispatch, **{k: outcome[k] for k in keep if outcome.get(k)}}
    final_loop = outcome.get("pr_loop") if isinstance(outcome.get("pr_loop"), dict) else loop
    if final_loop:
        new["pr_loop"] = {**(state.get("pr_loop") or {}), **final_loop}
    progress = last_progress_of(log)  # Z3-lokalnie: ostatnia linia postępu dla panelu konsoli (DZ18).
    if progress is not None:
        new["dispatch"]["last_progress"] = progress
    entry = {"at": outcome.get("finished_at") or dispatch.get("at"), "what": f"dispatch.{new['dispatch']['status']}"}
    # PR-y w historii zostają, gdy następne uruchomienie fazy nadpisze `dispatch` (ślad zmiany, PRB-5).
    prs = {k: outcome[k] for k in ("pr", "cuts") if outcome.get(k)}
    new.setdefault("history", []).append({**entry, "phase": dispatch.get("phase"), **prs})
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


def execute(
    spec: dict[str, Any],
    *,
    run: Run,
    env: Mapping[str, str],
    log: Callable[[str], None],
    stream: StreamRun | None = None,
) -> dict[str, Any]:
    """Kroki szablonu `sdlc-phase.yml`; wynik `{"status": done | failed, "step"?, "error"?, "pr"?, "prs"?}`.

    Po fazie `delivery` pdi wypycha gałęzie cięć talosa (`story/*`) i otwiera ich PR-y (`prs`), bo persona w trybie
    --print nie ma zgody na `git push` ani `gh pr create`.
    """
    cwd = Path(spec["checkout"])
    change, phase, ref = spec["change"], spec["phase"], spec["ref"]
    branch = f"pdi/{change}-{phase}"
    passed = {name.strip() for name in (env.get(EXTRA_ENV_NAMES) or "").split(",") if name.strip()}
    base = {k: v for k, v in env.items() if k in SYSTEM_ENV or k.startswith(SYSTEM_PREFIXES) or k in passed}
    gate_env = {k: env[k] for k in GATE_ENV if k in env}
    github_env = {k: env[k] for k in GITHUB_ENV if k in env}
    problem_env = {"PDI_SOURCE": spec.get("source") or "", "PDI_PROBLEM": env.get("PDI_PROBLEM") or ""}
    cloud = tuple(p for switch, prefixes in CLOUD_PREFIXES.items() if env.get(switch) for p in prefixes)
    claude_env = {
        k: v
        for k, v in env.items()
        if k.startswith(CLAUDE_PREFIXES) or k == "PDI_CLAUDE_BIN" or (cloud and k.startswith(cloud))
    }

    def step(
        name: str,
        argv: list[str],
        *,
        ok: tuple[int, ...] = (0,),
        quiet: bool = False,
        extra: Mapping[str, str] | None = None,
    ) -> tuple[int, str]:
        log("$ " + shlex.join(argv))
        step_env = {**base, **(extra or {})}
        with _heartbeat(name, log):
            if stream is not None and not quiet:
                code, out = stream(argv, cwd, step_env, log)
            else:
                code, out = run(argv, cwd, step_env)
                if out.strip() and not (quiet and code in ok):
                    log(out.rstrip("\n"))
        if code not in ok:
            raise _StepFailed(name, f"Krok {name}: `{shlex.join(argv)}` zakończone kodem {code} — szczegóły w logu.")
        return code, out

    def script(name: str, *args: str) -> list[str]:
        return ["python3", f"{SCRIPTS}/{name}", *args]

    try:
        try:
            sandbox = phase_sandbox.mode(env)
        except phase_sandbox.SandboxError as e:
            raise _StepFailed("run", str(e)) from e
        if sandbox == "none":
            log(phase_sandbox.NONE_WARNING)
        _, dirty = step("checkout", ["git", "status", "--porcelain"])
        if dirty.strip():
            raise _StepFailed("checkout", "Klon ma niezatwierdzone zmiany — zatwierdź je albo odłóż i ponów.")
        step("checkout", ["git", "fetch", "origin"], extra=github_env)
        step("checkout", ["git", "switch", ref])
        step("checkout", ["git", "pull", "--ff-only", "origin", ref], extra=github_env)
        prior = PRIOR_ARTIFACT.get(phase)
        if prior and not (cwd / "docs/project/changes" / change / prior).is_file():
            raise _StepFailed(
                "inputs",
                f"Na {ref} nie ma docs/project/changes/{change}/{prior} — faza {phase} potrzebuje artefaktu "
                "poprzedniej fazy. Zmerguj PR poprzedniej fazy i ponów (retry_dispatch).",
            )

        code, _ = step(
            "branch", ["git", "ls-remote", "--exit-code", "--heads", "origin", branch], ok=(0, 2), extra=github_env
        )
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
        step(
            "prompt",
            script("phase_run.py", "prompt", "--change", change, "--phase", phase),
            quiet=True,
            extra=problem_env,
        )
        if spec.get("decisions"):
            # Decyzje zmiany z rejestru pdi (Z1) — tylko do tf, który zna `decision import`; idempotentne po DEC.
            code, usage = step(
                "decision", script("decision_record.py", "decision", "import", "--help"), ok=(0, 2), quiet=True
            )
            if code == 0 and "--json" in usage:
                path = _data_file(spec, "decisions", spec["decisions"])
                step("decision", script("decision_record.py", "decision", "import", change, "--json", str(path)))
        if spec.get("decision"):
            gate_args = ["--gate", spec["gate"], "--outcome", spec["outcome"], "--id", spec["decision"]]
            if spec.get("decision_text") or spec.get("answers"):
                # Treść decyzji (PRB-3) i odpowiedzi na pytania (Z1) idą tylko do tf, który zna `--why`/`--answers`.
                code, usage = step(
                    "decision", script("decision_record.py", "decision", "gate", "--help"), ok=(0, 2), quiet=True
                )
                if code == 0 and spec.get("decision_text") and "--why" in usage:
                    gate_args += ["--why", spec["decision_text"]]
                if code == 0 and spec.get("answers") and "--answers" in usage:
                    gate_args += ["--answers", str(_data_file(spec, "answers", spec["answers"]))]
            step("decision", script("decision_record.py", "decision", "gate", change, *gate_args))

        if phase == "delivery":
            # Talos zaczyna od czystego drzewa (talos-story-run §0) — decyzje dopisane wyżej idą do commita od razu.
            step("commit", ["git", "add", "-A", f"docs/project/changes/{change}"])
            code, _ = step("commit", ["git", "diff", "--cached", "--quiet"], ok=(0, 1))
            if code == 1:
                message = f"docs({change}): decyzje przed realizacją (pdi)"
                step("commit", ["git", "commit", "-m", message, "-m", f"Change: {change}"])
        cuts_before = _cuts(step) if phase == "delivery" else set()
        args = ["--change", change, "--phase", phase]
        if spec.get("rework"):
            args += ["--rework", "--gate", spec["gate"], "--decision", spec["decision"]]
        if spec.get("budget_usd"):
            args += ["--budget-usd", spec["budget_usd"]]
        if sandbox == "docker":
            ran = _run_in_container(spec, step, log, env, base, passed, script("phase_run.py", "run", *args),
                                    {**problem_env, **claude_env})  # fmt: skip
        else:
            _, ran = step("run", script("phase_run.py", "run", *args), extra={**problem_env, **claude_env})

        # Drugi przegląd (N1, DZ12): osobny krok na hoście, tylko dla requirements/architecture; klucz dostawcy nie
        # wchodzi do kontenera fazy (Z8g). Krok sam nie zawodzi fazy — second_review.py zawsze kończy 0; niedostępność
        # trafia do sidecara i stąd do prośby o bramkę jako `second_review: {status: unavailable, reason: …}`.
        if phase in SECOND_REVIEW_PHASES:
            review_env = {k: env[k] for k in SECOND_REVIEW_ENV if env.get(k)}
            step(
                "second-review",
                script("second_review.py", "artifact", "--change", change, "--phase", phase),
                extra=review_env,
            )

        if phase == "delivery":
            try:
                cuts = _publish_cuts(step, cuts_before, ref, branch, github_env, change)
            except _StepFailed as e:
                e.persona = _persona_report(ran)
                raise
            done: dict[str, Any] = {"status": "done", "prs": [c["pr"] for c in cuts], "cuts": cuts}
            if (env.get(PR_LOOP_ENV) or "").strip().lower() not in ("off", "0", "false", "no"):
                persona = _persona_report(ran) or {}
                spent = persona.get("cost_usd") if isinstance(persona.get("cost_usd"), (int, float)) else 0.0
                budget = float(spec["budget_usd"]) - float(spent or 0.0) if spec.get("budget_usd") else None
                steps = _LoopSteps(spec, step, log, env, base, passed, claude_env, github_env, sandbox, branch)
                loop = steps.run([pr_loop.Cut(c["branch"], c["pr"], branch) for c in cuts], budget)
                done["pr_loop"] = loop
                done["pr_loop_cost_usd"] = round(sum(e.get("cost_usd") or 0.0 for e in loop.values()), 6)
            return done
        step("commit", ["git", "add", "-A"])
        code, _ = step("commit", ["git", "diff", "--cached", "--quiet"], ok=(0, 1))
        if code == 1:
            step("commit", ["git", "commit", "-m", f"docs({change}): faza {phase} (pdi)", "-m", f"Change: {change}"])
        step("push", ["git", "push", "-u", "origin", branch], extra=github_env)
        code, out = step("pr", ["gh", "pr", "view", branch, "--json", "url", "-q", ".url"], ok=(0, 1), extra=github_env)
        url = _url(out) if code == 0 else None
        if not url:
            _, out = step("pr", ["gh", "pr", "create", "--fill", "--head", branch], extra=github_env)
            url = _url(out)
        if not url:
            raise _StepFailed("pr", "Krok pr: gh nie podał adresu PR — szczegóły w logu.")
        gate_args = ["--change", change, "--phase", phase, "--url", url]
        try:
            step("gate", script("phase_run.py", "gate", "request", *gate_args), extra=gate_env)
        except _StepFailed as e:
            e.pr = url
            raise
        return {"status": "done", "pr": url}
    except _StepFailed as e:
        log(f"# błąd: {e.error}")
        failed: dict[str, Any] = {"status": "failed", "step": e.step, "error": e.error}
        if e.persona:
            failed["persona"] = e.persona
        if e.pr:
            failed["pr"] = e.pr
        return failed


def request_gate(
    *, checkout: Path, change: str, phase: str, url: str, env: Mapping[str, str], run: Run, log: Path
) -> dict[str, Any]:
    """Ponawia sam krok `gate` (prośbę o bramkę dla gotowego PR fazy), bez ponownego uruchamiania persony.

    Gdy przy końcu fazy odbiornik pdi nie działał (np. `sdlc down`/`up`), PR fazy już jest, a brakuje tylko
    `gate.requested`; ponowienie całej fazy napisałoby artefakt od nowa i otworzyło drugi PR.
    """
    passed = {name.strip() for name in (env.get(EXTRA_ENV_NAMES) or "").split(",") if name.strip()}
    base = {k: v for k, v in env.items() if k in SYSTEM_ENV or k.startswith(SYSTEM_PREFIXES) or k in passed}
    step_env = {**base, **{k: env[k] for k in GATE_ENV if k in env}}
    argv = ["python3", f"{SCRIPTS}/phase_run.py", "gate", "request", "--change", change, "--phase", phase, "--url", url]
    code, out = run(argv, checkout, step_env)
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(f"# pdi: ponowienie samej prośby o bramkę ({change} {phase})\n$ {shlex.join(argv)}\n")
        if out.strip():
            f.write(out.rstrip("\n") + "\n")
        f.write(f"# koniec: {'done' if code == 0 else 'failed'}\n")
    if code != 0:
        error = f"Krok gate: `{shlex.join(argv)}` zakończone kodem {code} — szczegóły w logu."
        return {"status": "failed", "step": "gate", "error": error, "pr": url}
    return {"status": "done", "pr": url}


Step = Callable[..., tuple[int, str]]


def _data_file(spec: dict[str, Any], name: str, data: Any) -> Path:
    """Dane dla tf w pliku obok logu (poza klonem, więc klon zostaje czysty); treść nie trafia do logu."""
    log = Path(spec["log"])
    path = log.with_name(f"{log.stem}.{name}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _run_in_container(
    spec: Mapping[str, Any],
    step: Step,
    log: Callable[[str], None],
    env: Mapping[str, str],
    base: Mapping[str, str],
    passed: set[str],
    run_argv: list[str],
    run_env: Mapping[str, str],
) -> str:
    """Krok `run` w kontenerze (Z8a, `pdi.phase_sandbox`); zwraca wyjście kroku, sieć i kontenery sprząta zawsze."""
    box = phase_sandbox.Box.of(spec["log"])
    try:
        phase_sandbox.prepare(
            box,
            checkout=Path(spec["checkout"]),
            log_path=Path(spec["log"]),
            env=env,
            base=base,
            passed=passed,
            run_argv=run_argv,
            run_env=run_env,
            timeout=STEP_TIMEOUT_SECONDS,
            step=step,
        )
        return step("run", box.argv, extra=box.env)[1]
    except phase_sandbox.SandboxError as e:
        raise _StepFailed("run", str(e)) from e
    finally:
        phase_sandbox.cleanup(box, step=step, log=log, env=env)


def _cuts(step: Step) -> set[str]:
    _, out = step("cuts", ["git", "for-each-ref", "--format=%(refname:short)", CUT_REFS], quiet=True)
    return {b for b in out.split() if _CUT.match(b) and ".." not in b}


def _cut_pr_text(step: Step, branch: str, start: str, change: str) -> tuple[str, str]:
    """Tytuł i opis PR cięcia (PRB-34): tytuł z pierwszego commitu Talosa (Conventional Commits), opis z raportu
    przebiegu `docs/project/changes/<CHG>/runs/<TSK>.md` z gałęzi cięcia, a bez niego lista commitów."""
    _, out = step("pr", ["git", "log", "--reverse", "--format=%s", f"{start}..{branch}"], quiet=True)
    subjects = [line for line in out.splitlines() if line.strip()]
    title = subjects[0] if subjects else branch
    match = _CUT_TASK.match(branch)
    report = f"docs/project/changes/{change}/runs/{match.group(1).upper()}.md" if match else None
    body = ""
    if report:
        code, text = step("pr", ["git", "show", f"{branch}:{report}"], ok=(0, 128), quiet=True)
        body = text.strip() if code == 0 else ""
    if not body:
        missing = f" (raportu `{report}` nie ma na gałęzi)" if report else ""
        body = "Commity cięcia" + missing + ":\n\n" + "\n".join(f"- {s}" for s in subjects)
    return title, f"{body}\n\nChange: {change}\n"


def _publish_cuts(
    step: Step, before: set[str], ref: str, start: str, github_env: Mapping[str, str], change: str
) -> list[dict[str, str]]:
    """Wypycha nowe gałęzie cięć z commitami ponad `start` (gałąź fazy z decyzjami) i otwiera dla każdej PR do `ref`.

    Zwraca `[{branch, pr}]`.
    """
    cuts = []
    for branch in sorted(_cuts(step) - before):
        _, count = step("cuts", ["git", "rev-list", "--count", f"{start}..{branch}"], quiet=True)
        if count.strip().isdigit() and int(count) > 0:
            cuts.append(branch)
    if not cuts:
        raise _StepFailed(
            "cuts",
            f"Talos nie zostawił gałęzi story/* z commitami ponad {ref} — cięcia nie powstały; szczegóły w logu.",
        )

    def ancestor(a: str, b: str) -> bool:
        return step("cuts", ["git", "merge-base", "--is-ancestor", a, b], ok=(0, 1), quiet=True)[0] == 0

    for branch in cuts:
        step("push", ["git", "push", "-u", "origin", branch], extra=github_env)
    prs = []
    for branch in cuts:
        # Cięcie zbudowane na innym cięciu dostaje PR do niego (GitHub przestawi bazę po merge'u poprzedniego).
        under = [o for o in cuts if o != branch and ancestor(o, branch)]
        base = next((o for o in under if all(p == o or ancestor(p, o) for p in under)), ref)
        code, out = step("pr", ["gh", "pr", "view", branch, "--json", "url", "-q", ".url"], ok=(0, 1), extra=github_env)
        url = _url(out) if code == 0 else None
        if not url:
            title, body = _cut_pr_text(step, branch, start, change)
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as f:
                f.write(body)
            try:
                argv = ["gh", "pr", "create", "--head", branch, "--base", base, "--title", title, "--body-file", f.name]
                _, out = step("pr", argv, extra=github_env)
            finally:
                os.unlink(f.name)
            url = _url(out)
        if not url:
            raise _StepFailed("pr", f"Krok pr: gh nie podał adresu PR dla {branch} — szczegóły w logu.")
        prs.append({"branch": branch, "pr": url})
    return prs


def pr_loop_path(log: Path) -> Path:
    """Stan pętli PR na żywo obok logu przebiegu (konsola widzi rundę przed końcem przebiegu)."""
    return log.with_name(log.stem + ".pr_loop.json")


def read_pr_loop(log: Path) -> dict[str, Any] | None:
    path = pr_loop_path(log)
    try:
        data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) and data else None


def _last_json(out: str) -> dict[str, Any] | None:
    for line in reversed(out.splitlines()):
        if line.startswith("{"):
            try:
                data = json.loads(line)
            except ValueError:
                continue
            if isinstance(data, dict):
                return data
    return None


def _seconds(env: Mapping[str, str], name: str, default: int) -> int:
    value = (env.get(name) or "").strip()
    return int(value) if value.isdigit() and int(value) <= 24 * 3600 else default


class _LoopSteps:
    """Prawdziwe kroki pętli PR (`pr_loop.Steps`): co wykonuje kod produktu — w kontenerze fazy (Z8a), bez tokenów
    GitHuba; co potrzebuje poświadczeń (walidacja kluczem drugiego modelu, push, `gh`) — na hoście."""

    def __init__(
        self,
        spec: Mapping[str, Any],
        step: Step,
        log: Callable[[str], None],
        env: Mapping[str, str],
        base: Mapping[str, str],
        passed: set[str],
        claude_env: Mapping[str, str],
        github_env: Mapping[str, str],
        sandbox: str,
        phase_branch: str,
        *,
        sleep: Callable[[float], None] | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.spec, self.step, self.log, self.env, self.base, self.passed = spec, step, log, env, base, passed
        self.claude_env, self.github_env, self.sandbox, self.phase_branch = (
            claude_env,
            github_env,
            sandbox,
            phase_branch,
        )
        self.review_env = {k: env[k] for k in SECOND_REVIEW_ENV if env.get(k)}
        self.change = str(spec["change"])
        self.sleep, self.clock = sleep or time.sleep, clock or time.monotonic
        self.wait = _seconds(env, CHECKS_WAIT_ENV, CHECKS_WAIT_SECONDS)
        self.grace = _seconds(env, CHECKS_GRACE_ENV, CHECKS_GRACE_SECONDS)
        self.interval = max(_seconds(env, CHECKS_INTERVAL_ENV, CHECKS_INTERVAL_SECONDS), 1)
        rounds = (env.get(PR_LOOP_ROUNDS_ENV) or "").strip()
        self.rounds = int(rounds) if rounds.isdigit() and int(rounds) <= 5 else pr_loop.MAX_ROUNDS

    def run(self, cuts: list[pr_loop.Cut], budget: float | None) -> dict[str, Any]:
        path = pr_loop_path(Path(self.spec["log"]))

        def update(state: dict[str, Any]) -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(state, ensure_ascii=False) + "\n", encoding="utf-8")
            tmp.replace(path)
            for url, entry in state.items():
                row = {
                    "phase": "delivery",
                    "status": "in_progress",
                    "change": self.change,
                    "url": url,
                    "message": f"PR {url.rsplit('/', 1)[-1]}: runda {entry['round']}, {entry['status']}",
                }
                self.log(PROGRESS_PREFIX + json.dumps(row, ensure_ascii=False))

        self.log(f"# pdi: pętla PR (N2) dla {len(cuts)} PR, najwyżej {self.rounds} rundy poprawek")
        try:
            return pr_loop.run_loop(cuts, self, max_rounds=self.rounds, budget_usd=budget, on_update=update)
        finally:
            self.step("pr-loop", ["git", "switch", self.phase_branch], ok=ANY_CODE, quiet=True)

    # --- w kontenerze fazy ---

    def _container(self, argv: list[str], extra: Mapping[str, str] | None = None) -> dict[str, Any]:
        run_env = {**self.claude_env, **(extra or {})}  # bez GH_TOKEN/GITHUB_TOKEN i kluczy drugiego modelu
        try:
            if self.sandbox == "docker":
                out = _run_in_container(self.spec, self.step, self.log, self.env, self.base, self.passed, argv, run_env)
            else:
                out = self.step("pr-loop", argv, extra=run_env, ok=ANY_CODE)[1]
        except _StepFailed as e:
            return {"status": "failed", "reason": e.error}
        return _last_json(out) or {"status": "failed", "reason": "brak wyniku JSON kroku pętli PR"}

    def _switch(self, cut: pr_loop.Cut) -> bool:
        return self.step("pr-loop", ["git", "switch", cut.branch], ok=ANY_CODE, quiet=True)[0] == 0

    def _script(self, name: str, *args: str) -> list[str]:
        return ["python3", f"{SCRIPTS}/{name}", *args]

    @staticmethod
    def _budget(budget: float | None) -> list[str]:
        return ["--budget-usd", f"{max(budget, 0.01):.2f}"] if budget is not None else []

    def review(self, cut: pr_loop.Cut, round_no: int, budget: float | None) -> dict[str, Any]:
        if not self._switch(cut):
            return {"status": "failed", "reason": f"git switch {cut.branch}"}
        argv = self._script(
            "pr_loop.py",
            "review",
            "--change",
            self.change,
            "--branch",
            cut.branch,
            "--base",
            cut.base,
            *self._budget(budget),
        )
        return self._container(argv)

    def fix(self, cut: pr_loop.Cut, round_no: int, data: dict[str, Any], budget: float | None) -> dict[str, Any]:
        if not self._switch(cut):
            return {"status": "failed", "reason": f"git switch {cut.branch}"}
        argv = self._script(
            "pr_loop.py",
            "fix",
            "--change",
            self.change,
            "--branch",
            cut.branch,
            "--round",
            str(round_no),
            *self._budget(budget),
        )
        return self._container(argv, {"PDI_PR_LOOP_INPUT": json.dumps(data, ensure_ascii=False)})

    def verify(self, cut: pr_loop.Cut) -> dict[str, Any]:
        if not self._switch(cut):
            return {"status": "failed", "reason": f"git switch {cut.branch}"}
        return self._container(self._script("pr_loop.py", "verify", "--base", cut.base))

    # --- na hoście ---

    def validate(self, cut: pr_loop.Cut, findings: list[dict[str, Any]]) -> dict[str, Any]:
        comments = []
        for f in findings:
            comment: dict[str, Any] = {k: f[k] for k in ("id", "severity", "file", "line", "body") if k in f}
            context = self._context(cut, f)
            if context:
                comment["context"] = context
            comments.append(comment)
        match = _PR_NUMBER.search(cut.pr)
        name = f"pr-loop-{match.group(1) if match else 'x'}-comments"
        path = _data_file(dict(self.spec), name, comments)
        argv = self._script(
            "second_review.py", "comments", "--pr", match.group(1) if match else "0", "--input", str(path)
        )
        try:
            _, out = self.step("pr-loop", argv, extra=self.review_env, ok=ANY_CODE, quiet=True)
        except _StepFailed as e:
            return {"status": "unavailable", "reason": e.error}
        return _last_json(out) or {"status": "unavailable", "reason": "brak wyniku second_review.py"}

    def _context(self, cut: pr_loop.Cut, f: dict[str, Any]) -> str:
        file, line = str(f.get("file") or ""), f.get("line")
        if not file or ".." in file or file.startswith(("/", "-")):
            return ""
        code, text = self.step("pr-loop", ["git", "show", f"{cut.branch}:{file}"], ok=ANY_CODE, quiet=True)
        if code != 0:
            return ""
        rows = text.splitlines()
        at = line - 1 if isinstance(line, int) and 0 < line <= len(rows) else 0
        lo, hi = max(at - CONTEXT_LINES, 0), min(at + CONTEXT_LINES + 1, len(rows))
        return "\n".join(f"{i + 1}: {rows[i]}" for i in range(lo, hi))

    def checks(self, cut: pr_loop.Cut) -> dict[str, Any]:
        argv = ["gh", "pr", "checks", cut.pr, "--json", "name,state,bucket,link,workflow"]
        started = self.clock()
        while True:
            _, out = self.step("pr-loop", argv, ok=ANY_CODE, quiet=True, extra=self.github_env)
            try:
                rows = json.loads(out) if out.strip().startswith("[") else []
            except ValueError:
                rows = []
            rows = [r for r in rows if isinstance(r, dict)]
            state = pr_loop.checks_state(rows)
            elapsed = self.clock() - started
            if state in ("green", "red") or (state == "none" and elapsed >= self.grace) or elapsed >= self.wait:
                return {"state": state, "checks": rows}
            self.sleep(self.interval)

    def ci_log(self, cut: pr_loop.Cut, checks: dict[str, Any]) -> str:
        parts = []
        for row in checks.get("checks") or []:
            run_id = pr_loop.run_id_of(str(row.get("link") or "")) if row.get("bucket") in ("fail", "cancel") else None
            if not run_id:
                continue
            code, out = self.step(
                "pr-loop", ["gh", "run", "view", run_id, "--log-failed"], ok=ANY_CODE, quiet=True, extra=self.github_env
            )
            if code == 0 and out.strip():
                parts.append(
                    f"== {row.get('workflow') or ''} / {row.get('name') or ''}\n"
                    + "\n".join(out.splitlines()[-CI_LOG_LINES:])
                )
        return "\n\n".join(parts)[-CI_LOG_MAX:]

    def push(self, cut: pr_loop.Cut) -> None:
        self.step("push", ["git", "push", "origin", cut.branch], extra=self.github_env)

    def commits(self, cut: pr_loop.Cut) -> list[str]:
        _, out = self.step(
            "pr-loop", ["git", "log", "--reverse", "--format=%s", f"{cut.base}..{cut.branch}"], ok=ANY_CODE, quiet=True
        )
        return [line for line in out.splitlines() if line.strip()]

    def body(self, cut: pr_loop.Cut) -> str:
        _, out = self.step(
            "pr", ["gh", "pr", "view", cut.pr, "--json", "body", "-q", ".body"], quiet=True, extra=self.github_env
        )
        return out

    def edit_body(self, cut: pr_loop.Cut, body: str) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as f:
            f.write(body)
        try:
            self.step("pr", ["gh", "pr", "edit", cut.pr, "--body-file", f.name], quiet=True, extra=self.github_env)
        finally:
            os.unlink(f.name)


@contextlib.contextmanager
def _heartbeat(name: str, log: Callable[[str], None]) -> Iterator[None]:
    """Co HEARTBEAT_SECONDS wpis „krok … trwa N min”, dopóki krok trwa."""
    done = threading.Event()
    started = time.monotonic()

    def beat() -> None:
        while not done.wait(HEARTBEAT_SECONDS):
            minutes = int((time.monotonic() - started) // 60)
            log(f"# … krok {name} trwa {minutes} min")

    thread = threading.Thread(target=beat, daemon=True)
    thread.start()
    try:
        yield
    finally:
        done.set()
        thread.join()


def finish(spec: dict[str, Any], env: Mapping[str, str], *, run: Run) -> dict[str, Any]:
    """Wykonuje przebieg z logiem w `spec["log"]` i zapisuje wynik obok; zwraca wynik.

    Linie postępu fazy (`PDI-PROGRESS: {json}`, Z3-lokalnie A7) idą do `<log>.progress.jsonl`
    po walidacji (`_valid_progress`), a reszta wyjścia — do logu. Linie błędne są pomijane,
    żeby nie hałasować ani w logu, ani w strumieniu konsoli.
    """
    log_path = Path(spec["log"])
    progress = progress_path(log_path)
    lock = threading.Lock()
    with log_path.open("a", encoding="utf-8") as f, progress.open("a", encoding="utf-8") as pf:

        def _write_log(text: str) -> None:
            f.write(text + "\n")
            f.flush()

        def _write_progress(row: dict[str, Any]) -> None:
            pf.write(json.dumps(row, ensure_ascii=False) + "\n")
            pf.flush()

        def log(line: str) -> None:
            with lock:  # wpisy znaku życia przychodzą z innego wątku
                # Kompozytowe linie (FakeRun w testach, `_stream_run` przekazuje po jednej) rozbij na wiersze.
                for part in line.split("\n"):
                    if part.startswith(PROGRESS_PREFIX):
                        try:
                            row = json.loads(part[len(PROGRESS_PREFIX) :])
                        except ValueError:
                            continue
                        if _valid_progress(row):
                            _write_progress(row)
                        continue
                    _write_log(part)

        log(f"# pdi: {spec['change']} faza {spec['phase']} w {spec['checkout']}")
        try:
            stream = _stream_run if run is _run else None
            result = execute(spec, run=run, env=env, log=log, stream=stream)
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


def _stream_run(argv: list[str], cwd: Path, env: Mapping[str, str], on_line: Callable[[str], None]) -> tuple[int, str]:
    """Jak _run, ale każda linia wyjścia idzie do `on_line` od razu; po STEP_TIMEOUT_SECONDS proces jest zabijany."""
    try:
        process = subprocess.Popen(  # noqa: S603 — lista argumentów, bez powłoki
            argv,
            cwd=cwd,
            env=dict(env),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except FileNotFoundError:
        return 127, f"brak polecenia {argv[0]}"
    lines: list[str] = []

    def read() -> None:
        assert process.stdout is not None  # noqa: S101 — stdout=PIPE
        for line in process.stdout:
            lines.append(line)
            on_line(line.rstrip("\n"))

    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    try:
        code = process.wait(timeout=STEP_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        reader.join(timeout=5)
        return 124, "".join(lines) + f"przekroczony czas kroku ({STEP_TIMEOUT_SECONDS} s)"
    reader.join()
    return code, "".join(lines)


def main() -> None:
    finish(json.loads(sys.stdin.read()), dict(os.environ), run=_run)


if __name__ == "__main__":
    main()
default_run = _run  # domyślny wykonawca kroków (subprocess), dla wywołań spoza przebiegu
is_fresh = _fresh  # „log zmieniany niedawno” — dla `sdlc down` (ostrzeżenie o fazie w toku)
