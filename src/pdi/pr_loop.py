"""Pętla PR agenta tf po fazie delivery (krok N2, plan: docs/plan-n2-petla-pr.md).

Na każdy PR cięcia: przegląd AI według `REVIEW.md` produktu → walidacja uwag drugim modelem (N1) → agent tf poprawia
tylko potwierdzone uwagi i czerwone checki → ponowny przegląd; najwyżej `max_rounds` rund poprawek (2, jak DZ6).
Pętla kończy się wcześniej, gdy zostały tylko uwagi poniżej progu (`minor`) i pytania do człowieka, a checki są
zielone. PR bez checków CI nie jest zielony. Po każdej rundzie host podmienia w opisie PR tylko sekcję
„Przewodnik dokończenia” (raport agenta tf i linia `Change:` zostają).

Kroki (`Steps`) wstrzykuje `pdi.dispatch_local`: przegląd, poprawka i lokalna weryfikacja biegną w kontenerze fazy
(Z8a), walidacja, push, odczyt checków i opis PR — na hoście. Tu jest tylko logika rund, triaż i przewodnik.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

MAX_ROUNDS = 2
BLOCKING = ("critical", "important")
STATUSES = ("reviewing", "fixing", "green", "needs_human")
TERMINAL = ("green", "needs_human")
GUIDE_HEADING = "## Przewodnik dokończenia"
GUIDE_OPEN = "<!-- pdi:przewodnik -->"
GUIDE_CLOSE = "<!-- /pdi:przewodnik -->"
_CHANGE_LINE = re.compile(r"^Change: \S+\s*$", re.MULTILINE)
_RUN_ID = re.compile(r"^https://github\.com/[^/]+/[^/]+/actions/runs/([0-9]{1,20})(?:/|$)")
TEXT_MAX = 400

Entry = dict[str, Any]


@dataclass(frozen=True)
class Cut:
    branch: str
    pr: str
    base: str


class Steps(Protocol):
    def review(self, cut: Cut, round_no: int, budget: float | None) -> dict[str, Any]: ...
    def validate(self, cut: Cut, findings: list[dict[str, Any]]) -> dict[str, Any]: ...
    def checks(self, cut: Cut) -> dict[str, Any]: ...
    def ci_log(self, cut: Cut, checks: dict[str, Any]) -> str: ...
    def verify(self, cut: Cut) -> dict[str, Any]: ...
    def fix(self, cut: Cut, round_no: int, data: dict[str, Any], budget: float | None) -> dict[str, Any]: ...
    def push(self, cut: Cut) -> None: ...
    def commits(self, cut: Cut) -> list[str]: ...
    def body(self, cut: Cut) -> str: ...
    def edit_body(self, cut: Cut, body: str) -> None: ...


def checks_state(rows: Sequence[dict[str, Any]]) -> str:
    """`gh pr checks --json bucket`: brak → none; fail/cancel → red; pending → pending; inaczej green."""
    buckets = [str(r.get("bucket") or "") for r in rows]
    if not buckets:
        return "none"
    if any(b in ("fail", "cancel") for b in buckets):
        return "red"
    if any(b not in ("pass", "skipping") for b in buckets):
        return "pending"
    return "green"


def run_id_of(link: str) -> str | None:
    """Numer przebiegu Actions z linku checku (do `gh run view <id> --log-failed`)."""
    match = _RUN_ID.match(link or "")
    return match.group(1) if match else None


def _short(text: Any) -> str:
    s = " ".join(str(text or "").split())
    return s if len(s) <= TEXT_MAX else s[: TEXT_MAX - 1] + "…"


def _where(f: dict[str, Any]) -> str:
    line = f":{f['line']}" if isinstance(f.get("line"), int) else ""
    return f"`{f.get('file') or '?'}{line}`"


def triage(findings: list[dict[str, Any]], validation: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Uwagi → `fix` (potwierdzone, blokujące), `questions` (do człowieka) i `minor` (lista w PR, bez poprawki)."""
    out: dict[str, list[dict[str, Any]]] = {"fix": [], "questions": [], "minor": []}
    verdicts = {str(c.get("id")): c for c in validation.get("comments") or [] if isinstance(c, dict)}
    unavailable = validation.get("status") != "ok"
    for f in findings:
        if f.get("severity") not in BLOCKING:
            out["minor"].append(f)
            continue
        if f.get("decision_ref"):
            text = f"[sprzeczne z {f['decision_ref']}] {_where(f)} {_short(f.get('body'))}"
            out["questions"].append({"id": f["id"], "kind": "decision", "text": text, "ref": f["decision_ref"]})
            continue
        if unavailable:
            why = validation.get("reason") or "unknown"
            text = f"[niepotwierdzone: drugi przegląd niedostępny ({why})] {_where(f)} {_short(f.get('body'))}"
            out["questions"].append({"id": f["id"], "kind": "unvalidated", "text": text})
            continue
        verdict = verdicts.get(str(f["id"]))
        if verdict and verdict.get("confirmed") is True:
            out["fix"].append(f)
            continue
        reason = _short(verdict.get("reason")) if verdict else "drugi model nie ocenił tej uwagi"
        text = f"[niepotwierdzone] {_where(f)} {_short(f.get('body'))} — {reason}"
        out["questions"].append({"id": f["id"], "kind": "rejected", "text": text})
    return out


def replace_guide(body: str, section: str) -> str:
    """Podmienia (albo dodaje przed linią `Change:`) blok przewodnika; reszta opisu PR zostaje bez zmian."""
    block = f"{GUIDE_OPEN}\n{section.strip()}\n{GUIDE_CLOSE}"
    pattern = re.compile(rf"\n*{re.escape(GUIDE_OPEN)}[\s\S]*?{re.escape(GUIDE_CLOSE)}\n*")
    rest = pattern.sub("\n\n", body).rstrip() + "\n"
    changes = list(_CHANGE_LINE.finditer(rest))
    if changes:
        at = changes[-1].start()
        return rest[:at].rstrip() + "\n\n" + block + "\n\n" + rest[at:]
    return rest.rstrip() + "\n\n" + block + "\n"


def _outside_plan(body: str) -> list[str]:
    """Decyzje poza planem z raportu agenta tf: „Odłożone do decyzji”, `[założenie]` i odstępstwa `plan_drift`."""
    found: list[str] = []
    report = re.sub(rf"{re.escape(GUIDE_OPEN)}[\s\S]*?{re.escape(GUIDE_CLOSE)}", "", body)
    parked = re.search(r"^## Odłożone do decyzji\s*\n([\s\S]*?)(?=^## |\Z)", report, re.MULTILINE)
    for line in (parked.group(1) if parked else "").splitlines():
        item = line.strip()
        if item.startswith("- ") and item[2:].strip().lower() not in ("brak", "—"):
            found.append(item[2:].strip())
    for line in report.splitlines():
        item = line.strip().lstrip("-* ").strip()
        if ("[założenie]" in item or "odstępstw" in item.lower()) and item not in found:
            found.append(item)
    return [_short(x) for x in found]


def guide_section(entry: Entry, commits: list[str], body: str) -> str:
    """Sekcja „Przewodnik dokończenia” (wspólna z N7): stan, zrobione, co zostaje, decyzje poza planem, ryzyka."""
    status = entry["status"]
    label = {
        "green": "gotowe do Twojego przeglądu — checki zielone, uwagi zamknięte",
        "needs_human": "do Ciebie",
        "reviewing": "w toku (przegląd)",
        "fixing": "w toku (poprawki)",
    }[status]
    fixes = sum(1 for r in entry["rounds"] if r.get("fixed") or r.get("ci_fixed"))
    lines = [GUIDE_HEADING, "", "### Stan", ""]
    lines.append(f"- **{status}** — {label}")
    lines.append(f"- runda przeglądu {entry['round']}, rund poprawek {fixes} z {entry['max_rounds']}")
    if entry.get("reason"):
        lines.append(f"- powód: {_short(entry['reason'])}")
    last = entry["rounds"][-1] if entry["rounds"] else {}
    if last.get("checks"):
        lines.append(f"- checki: {last['checks'].get('summary') or last['checks'].get('state')}")
    lines.append(
        f"- koszt pętli: {entry['cost_usd']:.2f} USD"
        + (
            f" (przegląd: `REVIEW.md` {'produktu' if entry.get('review_md') == 'product' else 'z szablonu tf'})"
            if entry.get("review_md")
            else ""
        )
    )
    lines += ["", "### Zrobione", ""]
    lines += [f"- {_short(c)}" for c in commits] or ["- brak commitów"]
    if entry["fixed"]:
        lines.append(f"- poprawione uwagi przeglądu: {', '.join(entry['fixed'])}")
    lines += ["", "### Zostaje dla Ciebie", ""]
    todo = [q["text"] for q in entry["questions"]]
    todo += [f"[otwarte po limicie] {_where(f)} {_short(f.get('body'))}" for f in entry.get("open") or []]
    lines += [f"- {t}" for t in todo]
    if entry.get("review_md") == "template":
        lines.append("- dodaj `REVIEW.md` produktu: `python3 .claude/skills/pdi-decisions/scripts/pr_loop.py scaffold`")
    lines.append("- przejrzyj diff i ten przewodnik, odpowiedz na pytania w PR, potem scal (pdi nie scala)")
    lines += ["", "### Decyzje poza planem — do zatwierdzenia", ""]
    outside = _outside_plan(body)
    lines += [f"- {x} — zatwierdź albo odrzuć w PR" for x in outside] or ["- brak"]
    lines += ["", "### Ryzyka", ""]
    risks = []
    if any(q["kind"] == "unvalidated" for q in entry["questions"]):
        reason = next((r.get("validation") for r in reversed(entry["rounds"]) if r.get("validation") != "ok"), "?")
        risks.append(f"drugi przegląd niedostępny ({reason}) — uwagi nie poszły do poprawki, oceń je sam")
    if (last.get("checks") or {}).get("state") == "none":
        risks.append("PR nie ma checków CI — zielone nie jest potwierdzone przez CI")
    if entry.get("open"):
        risks.append(f"limit {entry['max_rounds']} rund poprawek — uwagi zostały otwarte")
    if entry["minor"]:
        risks.append(f"{len(entry['minor'])} drobnych uwag bez poprawki (lista niżej)")
    lines += [f"- {r}" for r in risks] or ["- brak znanych"]
    if entry["minor"]:
        lines += ["", "### Drobne uwagi (poza pętlą)", ""]
        lines += [f"- {_where(f)} {_short(f.get('body'))}" for f in entry["minor"]]
    lines += ["", "*Sekcję aktualizuje pdi po każdej rundzie pętli PR (N2); reszta opisu to raport agenta tf.*"]
    return "\n".join(lines)


def _new_entry(cut: Cut, max_rounds: int) -> Entry:
    return {
        "branch": cut.branch,
        "base": cut.base,
        "round": 0,
        "max_rounds": max_rounds,
        "status": "reviewing",
        "reason": None,
        "cost_usd": 0.0,
        "rounds": [],
        "questions": [],
        "minor": [],
        "fixed": [],
        "open": [],
        "review_md": None,
    }


def _cost(result: dict[str, Any]) -> float:
    value = result.get("cost_usd")
    return float(value) if isinstance(value, (int, float)) and value > 0 else 0.0


def run_loop(
    cuts: Sequence[Cut],
    steps: Steps,
    *,
    max_rounds: int = MAX_ROUNDS,
    budget_usd: float | None = None,
    on_update: Callable[[dict[str, Entry]], None] | None = None,
) -> dict[str, Entry]:
    """Pętla dla każdego PR po kolei; zwraca `{url PR: wpis}` (status, runda, powód, rundy z kosztem)."""
    state: dict[str, Entry] = {}
    spent = [0.0]

    def left() -> float | None:
        return None if budget_usd is None else round(budget_usd - spent[0], 4)

    def update() -> None:
        if on_update is not None:
            on_update(state)

    for cut in cuts:
        entry = _new_entry(cut, max_rounds)
        state[cut.pr] = entry
        _one(cut, entry, steps, spent, left, update)
        update()
    return state


def _one(
    cut: Cut,
    entry: Entry,
    steps: Steps,
    spent: list[float],
    left: Callable[[], float | None],
    update: Callable[[], None],
) -> None:
    fixes = 0

    def finish(status: str, reason: str) -> None:
        entry.update(status=status, reason=reason)
        _guide(cut, entry, steps)

    def add(rnd: dict[str, Any], cost: float) -> None:
        rnd["cost_usd"] = round(rnd["cost_usd"] + cost, 6)
        entry["cost_usd"] = round(entry["cost_usd"] + cost, 6)
        spent[0] += cost

    while True:
        remaining = left()
        if remaining is not None and remaining <= 0:
            return finish("needs_human", f"budget: budżet fazy wyczerpany przed rundą {entry['round'] + 1}")
        entry["round"] += 1
        entry["status"] = "reviewing"
        rnd: dict[str, Any] = {"round": entry["round"], "cost_usd": 0.0}
        entry["rounds"].append(rnd)
        update()
        review = steps.review(cut, entry["round"], remaining)
        add(rnd, _cost(review))
        entry["review_md"] = review.get("review_md") or entry["review_md"]
        if review.get("status") != "ok":
            rnd["review"] = "failed"
            return finish("needs_human", f"przegląd AI nie powiódł się ({review.get('reason') or 'unknown'})")
        findings = [f for f in review.get("findings") or [] if isinstance(f, dict)]
        blocking = [f for f in findings if f.get("severity") in BLOCKING and not f.get("decision_ref")]
        validation: dict[str, Any] = {"status": "ok", "comments": []}
        if blocking:
            validation = steps.validate(cut, blocking)
            add(rnd, _cost(validation))
        tri = triage(findings, validation)
        rnd.update(
            findings=len(findings),
            fixed=[f["id"] for f in tri["fix"]],
            minor=len(tri["minor"]),
            questions=[q["id"] for q in tri["questions"]],
            validation=validation.get("status")
            if validation.get("status") == "ok"
            else validation.get("reason") or validation.get("status") or "unknown",
        )
        # Pytania z wcześniejszych rund zostają (rozstrzyga je człowiek, nie ponowny przegląd); drobne — z ostatniej.
        known = {q["text"] for q in entry["questions"]}
        entry["questions"] += [q for q in tri["questions"] if q["text"] not in known]
        entry["minor"] = tri["minor"]

        checks = steps.checks(cut)
        state = checks.get("state") or checks_state(checks.get("checks") or [])
        rows = checks.get("checks") or []
        summary = {
            "green": f"{len(rows)} zielone",
            "red": "czerwone",
            "pending": "nie skończyły się",
            "none": "brak checków CI",
        }.get(state, state)
        rnd["checks"] = {"state": state, "summary": summary}
        ci_log, ci_source = None, None
        if state == "red":
            failing = [str(r.get("name") or "?") for r in rows if r.get("bucket") in ("fail", "cancel")]
            ci_source = ", ".join(failing) or "ci"
            rnd["checks"]["failing"] = failing
            ci_log = steps.ci_log(cut, checks) or f"check {ci_source} czerwony — log niedostępny"
        elif state == "none":
            local = steps.verify(cut)
            rnd["checks"]["local_verify"] = local.get("status")
            if local.get("status") == "fail":
                ci_log, ci_source = str(local.get("log") or ""), "verify.sh (lokalnie, N3)"

        if not tri["fix"] and not ci_log:
            rnd["fixed"] = []
            if state == "green":
                if entry["questions"]:
                    return finish(
                        "needs_human", f"questions: {len(entry['questions'])} pytań do Ciebie, checki zielone"
                    )
                return finish(
                    "green",
                    "checki zielone, uwagi zamknięte"
                    + (f" ({len(tri['minor'])} drobnych na liście)" if tri["minor"] else ""),
                )
            if state == "none":
                return finish(
                    "needs_human",
                    "no_ci_checks: PR nie ma checków CI"
                    + (
                        " (weryfikacja N3 lokalnie przeszła)"
                        if rnd["checks"]["local_verify"] == "pass"
                        else " i nie ma ./verify.sh"
                    ),
                )
            return finish("needs_human", "checks_timeout: checki nie skończyły się w czasie oczekiwania")
        if fixes >= entry["max_rounds"]:
            entry["open"] = tri["fix"]
            rnd["fixed"] = []
            what = [f"{len(tri['fix'])} uwag"] if tri["fix"] else []
            what += [f"czerwone checki ({ci_source})"] if ci_log else []
            return finish("needs_human", f"nie udało się po {entry['max_rounds']} rundach: zostały {' i '.join(what)}")
        remaining = left()
        if remaining is not None and remaining <= 0:
            entry["open"] = tri["fix"]
            rnd["fixed"] = []
            return finish("needs_human", "budget: budżet fazy wyczerpany przed poprawką")
        entry["status"] = "fixing"
        update()
        data: dict[str, Any] = {"comments": tri["fix"]}
        if ci_log:
            data.update(ci_log=ci_log, ci_source=ci_source)
            rnd["ci_fixed"] = True
        fixed = steps.fix(cut, entry["round"], data, remaining)
        add(rnd, _cost(fixed))
        if fixed.get("status") != "ok":
            entry["open"] = tri["fix"]
            return finish("needs_human", f"poprawka agenta tf nie powiodła się ({fixed.get('reason') or 'unknown'})")
        steps.push(cut)
        fixes += 1
        entry["fixed"] += [f["id"] for f in tri["fix"]]
        _guide(cut, entry, steps)


def _guide(cut: Cut, entry: Entry, steps: Steps) -> None:
    """Podmiana sekcji w opisie PR; błąd zapisu nie przerywa pętli, tylko trafia do wpisu."""
    try:
        body = steps.body(cut)
        steps.edit_body(cut, replace_guide(body, guide_section(entry, steps.commits(cut), body)))
        entry.pop("guide_error", None)
    except Exception as e:  # noqa: BLE001 — opis PR to dodatek; stan pętli ma zostać zapisany
        entry["guide_error"] = f"{type(e).__name__}: {_short(e)}"
