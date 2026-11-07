"""Eksport decyzji technicznych z rejestru do MADR 4.0.0 albo 2.1.2 (DR3; plan docs/plan-eksport-madr.md).

Plik `NNNN-<slug>.md` na decyzję `kind: technical` (status `recorded` albo `superseded`). Każdy wyeksportowany plik
kończy komentarz `<!-- pdi: DEC-n … -->`; eksport nadpisuje i usuwa tylko takie pliki, ADR-y napisane ręcznie
zostają nietknięte. Stałe nagłówki szablonu po angielsku (tak je czytają narzędzia ADR), treść decyzji bez zmian.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

import yaml

from pdi.registry import Decision, Registry

FORMATS = ("4", "2")
EXPORTED_STATUSES = ("recorded", "superseded")
SLUG_MAX = 50
_MARK = re.compile(r"<!-- pdi: ([A-Z][A-Z0-9]+-[0-9]+) ")
_NUMBER = re.compile(r"-0*([0-9]+)$")
_EFFECT = {"good": "Good", "bad": "Bad", "neutral": "Neutral"}


def number(decision_id: str) -> str:
    """Numer ADR z numeru decyzji: DEC-0041 → 0041."""
    found = _NUMBER.search(decision_id)
    return f"{int(found.group(1)) if found else 0:04d}"


def slug(text: str) -> str:
    """Małe litery ASCII i myślniki, polskie znaki bez ogonków, do 50 znaków (na granicy słowa)."""
    plain = unicodedata.normalize("NFKD", text.replace("ł", "l").replace("Ł", "L"))
    words = re.sub(r"[^a-z0-9]+", " ", plain.encode("ascii", "ignore").decode().lower()).split()
    out = ""
    for word in words:
        candidate = f"{out}-{word}" if out else word
        if len(candidate) > SLUG_MAX:
            break
        out = candidate
    return out or "decyzja"


def file_name(decision: Decision) -> str:
    return f"{number(decision['id'])}-{slug(decision['statement'])}.md"


def _status(d: Decision, exported: dict[str, Decision], fmt: str) -> str:
    if d["status"] == "recorded":
        return "accepted"
    successor = d.get("superseded_by")
    if successor in exported:
        adr = f"ADR-{number(successor)}"
        return f"superseded by [{adr}]({file_name(exported[successor])})" if fmt == "2" else f"superseded by {adr}"
    return f"superseded (pdi {successor})"


def _chosen(d: Decision) -> str:
    chosen = next((o["option"] for o in d.get("options", ()) if o["chosen"]), None)
    return str(chosen or d["statement"])


def _context(d: Decision) -> str:
    where = f"projekt {d['project']}" if d.get("project") else "decyzja ogólna"
    problem = d.get("links", {}).get("prb")
    return f"Decyzja {d['id']} z rejestru pdi ({where})." + (f" Problem: {problem}." if problem else "")


def _more(d: Decision, *, links: bool = True) -> list[str]:
    lines = [f"* Rejestr pdi: {d['id']} (rodzaj {d['kind']}, zdecydował(a) {d['decided_by']})"]
    source = d.get("source", {})
    if source.get("url"):
        lines.append(f"* Źródło: {source['url']}")
    if links:
        lines += [f"* {key.upper()}: {value}" for key, value in d.get("links", {}).items()]
    for a in d.get("assumptions", ()):
        bearing = "założenie nośne" if a["load_bearing"] else "założenie"
        lines.append(f"* {bearing.capitalize()}: {a['statement']} Rozważ ponownie, gdy: {a['invalidated_if']}")
    if d.get("review_by"):
        lines.append(f"* Przegląd do: {d['review_by']}")
    lines += [f"* Dowód ({e['epistemic_status']}): {e['text']}" for e in d.get("evidence", ())]
    return lines


def _confirmation(d: Decision) -> str:
    c = d["confirmation"]
    detail = ": ".join(x for x in (c.get("kind"), c.get("ref")) if x)
    return str(c["how"]) + (f" ({detail})" if detail else "")


def render(d: Decision, exported: dict[str, Decision], fmt: str = "4") -> str:
    """Plik MADR (`fmt` 4 = 4.0.0, 2 = 2.1.2) dla jednej decyzji; `exported` — decyzje z tego eksportu (po id)."""
    options = [o["option"] for o in d.get("options", ())] or [d["statement"]]
    consequences = d.get("consequences", [])
    out: list[str] = []
    if fmt == "4":
        # Data bez cudzysłowów, jak w szablonie MADR; pozostałe wartości przez YAML (cudzysłów, gdy trzeba).
        head = {"status": _status(d, exported, fmt), "decision-makers": d["decided_by"]}
        lines = yaml.safe_dump(head, sort_keys=False, allow_unicode=True).rstrip().splitlines()
        out += ["---", lines[0], f"date: {d['decided_at']}", *lines[1:], "---", ""]
        out += [f"# {d['statement']}", ""]
    else:
        out += [f"# {d['statement']}", ""]
        out += [
            f"* Status: {_status(d, exported, fmt)}",
            f"* Deciders: {d['decided_by']}",
            f"* Date: {d['decided_at']}",
        ]
        story = d.get("links", {}).get("chg") or d.get("links", {}).get("prb")
        out += ["", f"Technical Story: {story}"] if story else []
        out.append("")
    out += ["## Context and Problem Statement", "", _context(d), ""]
    out += ["## Considered Options", "", *(f"* {o}" for o in options), ""]
    out += ["## Decision Outcome", "", f'Chosen option: "{_chosen(d)}", because {d["why"]}', ""]
    if fmt == "4":
        if consequences:
            out += ["### Consequences", ""]
            out += [f"* {_EFFECT[c['effect']]}, because {c['text']}" for c in consequences]
            out.append("")
        if d.get("confirmation"):
            out += ["### Confirmation", "", _confirmation(d), ""]
    else:
        for title, effect in (("Positive", "good"), ("Negative", "bad"), ("Neutral", "neutral")):
            items = [c["text"] for c in consequences if c["effect"] == effect]
            if items:
                out += [f"### {title} Consequences", "", *(f"* {t}" for t in items), ""]
    notes = [o for o in d.get("options", ()) if o.get("note")]
    if notes:
        out += ["## Pros and Cons of the Options", ""]
        for o in notes:
            out += [f"### {o['option']}", "", o["note"], ""]
    more = _more(d, links=fmt == "4")
    if fmt == "2":
        links = [f"* {k.upper()}: {v}" for k, v in d.get("links", {}).items()]
        if links:
            out += ["## Links", "", *links, ""]
        if d.get("confirmation"):
            more.insert(0, f"* Jak sprawdzić: {_confirmation(d)}")
    out += ["## More Information", "", *more, ""]
    out.append(
        f"<!-- pdi: {d['id']} · wygenerowane przez pdi-records export-madr; zmiany wprowadzaj w rejestrze pdi -->"
    )
    return "\n".join(out) + "\n"


def _owner(path: Path) -> str | None:
    """Id decyzji pdi, z której wygenerowano plik, albo None (plik napisany ręcznie)."""
    found = _MARK.search(path.read_text(encoding="utf-8"))
    return found.group(1) if found else None


def export(registry: Registry, out_dir: Path, *, project: str | None = None, fmt: str = "4") -> dict[str, Any]:
    """Zapisuje decyzje techniczne jako pliki MADR w `out_dir`; zwraca `written`, `unchanged`, `removed`,
    `skipped` (`{id, reason}`) i `conflicts` (ADR napisany ręcznie pod tym samym numerem)."""
    if fmt not in FORMATS:
        raise ValueError(f"format: {' albo '.join(FORMATS)}")
    chosen: dict[str, Decision] = {}
    skipped: list[dict[str, str]] = []
    for d in registry.decisions():
        if d["kind"] != "technical" or (project and d.get("project") != project):
            continue
        if d["status"] not in EXPORTED_STATUSES:
            skipped.append({"id": d["id"], "reason": f"status {d['status']}"})
            continue
        chosen[d["id"]] = d
    out_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {"written": [], "unchanged": [], "removed": [], "skipped": skipped, "conflicts": []}
    for decision_id, d in chosen.items():
        target = out_dir / file_name(d)
        others = [p for p in sorted(out_dir.glob(f"{number(decision_id)}-*.md")) if p != target]
        foreign = [p for p in [*others, target] if p.exists() and _owner(p) != decision_id]
        if foreign:
            result["conflicts"] += foreign
            continue
        for old in others:
            old.unlink()
            result["removed"].append(old)
        text = render(d, chosen, fmt)
        if target.exists() and target.read_text(encoding="utf-8") == text:
            result["unchanged"].append(target)
            continue
        target.write_text(text, encoding="utf-8")
        result["written"].append(target)
    return result
