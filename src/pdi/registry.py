"""Rejestr decyzji: pliki `decisions/DEC-nnnn.md`.

Frontmatter YAML jest źródłem prawdy; treść pod nim to widok dla człowieka, generowany przy każdym zapisie. Każdy
zapisany plik jest Decision Record (DR1, kontrakt 0.14.0): nagłówek zaczyna się od `record: decision`, `schema`
i `contract_version`, które nadaje rejestr.
"""

from __future__ import annotations

import os
import re
import subprocess
import unicodedata
from collections.abc import Callable, Iterable
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, TypeAlias

import yaml

from pdi import contract

SCHEMA_PATH = contract.schema_path("decision")

MARKER_FIELDS = ("record", "schema", "contract_version")
REGISTRY_FIELDS = (*MARKER_FIELDS, "id", "status", "recorded_at", "supersedes", "superseded_by")
FIELD_ORDER = (
    "record",
    "schema",
    "contract_version",
    "id",
    "statement",
    "why",
    "decided_at",
    "decided_by",
    "recorded_at",
    "kind",
    "decision_type",
    "project",
    "status",
    "drafted_by",
    "draft_edited",
    "automation",
    "source",
    "origin",
    "options",
    "evidence",
    "assumptions",
    "dependencies",
    "answers",
    "success_metric",
    "consequences",
    "confirmation",
    "review_by",
    "reversibility",
    "provisional",
    "supersedes",
    "superseded_by",
    "links",
    "tags",
)
_ID = re.compile(r"^DEC-(\d+)$")
_CURSOR = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)(?:/([A-Z][A-Z0-9]+-[0-9]+))?$")
_WORD = re.compile(r"\w{2,}")
_MAX_ID_RETRIES = 5
GENERAL_PROJECT_DIR = "_ogolne"

Decision: TypeAlias = dict[str, Any]


class DecisionNotFound(LookupError):
    """W rejestrze nie ma decyzji o podanym ID."""


class InvalidDecision(ValueError):
    """Szkic decyzji nie spełnia kontraktu; komunikat mówi, co poprawić."""


class CannotSupersede(ValueError):
    """Zastąpić można tylko decyzję o statusie `recorded`."""


def schema_errors(decision: Decision) -> list[str]:
    """Błędy walidacji względem `contract/decision.schema.json`, w formie `ścieżka: problem`."""
    return [e.replace("(obiekt)", "(decyzja)", 1) for e in contract.errors("decision", decision)]


def _utc_now() -> datetime:
    return datetime.now(UTC)


class Registry:
    def __init__(self, root: Path, clock: Callable[[], datetime] = _utc_now) -> None:
        self.root = root
        self._dir = root / "decisions"
        self._clock = clock

    @classmethod
    def from_env(cls) -> Registry:
        path = os.environ.get("PDI_REGISTRY_PATH")
        if not path:
            raise RuntimeError(
                "Brak zmiennej PDI_REGISTRY_PATH — ustaw ją na katalog rejestru decyzji "
                "(np. klon prywatnego repo pdi-decisions)."
            )
        return cls(Path(path).expanduser())

    # --- zapis ---

    def record(self, draft: Decision) -> Decision:
        """Zapisuje nową decyzję. Ponowienie tego samego zapisu zwraca istniejący wpis (`duplicate: true`)."""
        self._reject_registry_fields(draft)
        decision = self._record(dict(draft), supersedes=None)
        if decision.get("duplicate"):
            return decision
        return self._commit(decision, [self._path(decision)], f"{decision['id']}: {decision['statement'][:60]}")

    def supersede(self, old_id: str, draft: Decision) -> Decision:
        """Zapisuje nową decyzję zastępującą `old_id`; stara dostaje status `superseded`."""
        self._reject_registry_fields(draft)
        old = self.get(old_id)
        if old["status"] != "recorded":
            successor = old.get("superseded_by")
            hint = f" — zastąp aktualną decyzję {successor}" if successor else ""
            raise CannotSupersede(f"{old_id} ma status {old['status']}{hint}.")
        old_file = self._locate(old_id)
        new = self._record(dict(draft), supersedes=old_id)
        old["status"] = "superseded"
        old["superseded_by"] = new["id"]
        self._write(old, overwrite=True)
        touched = [self._path(new), self._path(old)]
        if old_file is not None and old_file != self._path(old):
            # Plik przeniesiony ręcznie: wraca do katalogu z pola `project`, bez kopii w starym miejscu.
            old_file.unlink()
            touched.append(old_file)
        return self._commit(new, touched, f"{new['id']}: zastępuje {old_id}")

    def _reject_registry_fields(self, draft: Decision) -> None:
        # Bez draft_edited szkic AI nie wchodzi do pomiaru autonomii (DA2, PRB-21); automat szkicu nie ma.
        if draft.get("drafted_by") == "ai" and "draft_edited" not in draft and "automation" not in draft:
            raise InvalidDecision(
                "drafted_by: ai wymaga draft_edited — false, gdy człowiek zatwierdził szkic bez zmian, true, gdy "
                "cokolwiek w nim zmienił."
            )
        set_by_registry = [f for f in REGISTRY_FIELDS if f in draft]
        if set_by_registry:
            raise InvalidDecision(
                f"Pola {', '.join(set_by_registry)} nadaje rejestr — usuń je ze szkicu "
                "(do zastępowania decyzji służy supersede_decision)."
            )

    def _record(self, draft: Decision, *, supersedes: str | None) -> Decision:
        now = self._clock()
        if "project" in draft:
            draft["project"] = project_slug(draft["project"])
        draft.setdefault("decided_at", now.date().isoformat())
        if "decided_by" not in draft:
            decider = os.environ.get("PDI_DECIDED_BY")
            if not decider:
                raise InvalidDecision("Brak decided_by — podaj, kto zdecydował, albo ustaw zmienną PDI_DECIDED_BY.")
            draft["decided_by"] = decider

        existing = None if supersedes else self._find_same(draft)
        if existing is not None:
            return {**existing, "path": str(self._path(existing)), "duplicate": True}

        if supersedes:
            draft["supersedes"] = supersedes
        draft["status"] = "recorded"
        draft["recorded_at"] = now.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        errors = schema_errors({**draft, "id": "DEC-1"})
        if errors:
            raise InvalidDecision("Szkic decyzji niezgodny z kontraktem: " + "; ".join(errors))

        for _ in range(_MAX_ID_RETRIES):
            decision = {**draft, "id": self._next_id()}
            try:
                self._write(decision, overwrite=False)
            except FileExistsError:
                continue
            break
        else:
            raise RuntimeError("Nie udało się nadać ID decyzji — równoległe zapisy; ponów.")
        return {**decision, "path": str(self._path(decision))}

    # --- odczyt ---

    def get(self, decision_id: str) -> Decision:
        path = self._locate(decision_id) if _ID.match(decision_id) else None
        if path is None:
            raise DecisionNotFound(f"Nie ma decyzji {decision_id} — sprawdź ID przez find_decisions.")
        return _read(path)

    def find(
        self,
        query: str = "",
        *,
        tags: Iterable[str] | None = None,
        since: str | None = None,
        status: str | None = None,
        kind: str | None = None,
        project: str | None = None,
        app: str | None = None,
        limit: int = 10,
    ) -> list[Decision]:
        """Szuka decyzji po słowach zapytania (także fragmentach słów) i filtrach.

        Kolejność: najwięcej trafionych słów, potem najnowsze.
        """
        words = [w.lower() for w in _WORD.findall(query)]
        wanted_tags = set(tags or ())
        wanted_project = project_slug(project) if project else None
        hits: list[tuple[int, Decision]] = []
        for decision in self._all():
            if wanted_tags and not wanted_tags <= set(decision.get("tags", ())):
                continue
            if since and decision["decided_at"] < since:
                continue
            if status and decision["status"] != status:
                continue
            if kind and decision["kind"] != kind:
                continue
            if wanted_project and decision.get("project") != wanted_project:
                continue
            if app and source_app(decision) != app:
                continue
            haystack = _searchable_text(decision)
            score = sum(1 for w in words if w in haystack)
            if words and score == 0:
                continue
            hits.append((score, decision))
        hits.sort(key=lambda h: (h[0], h[1]["decided_at"], _number(h[1]["id"])), reverse=True)
        return [_summary(d) for _, d in hits[:limit]]

    def decisions(self) -> list[Decision]:
        """Wszystkie pełne wpisy rejestru, w kolejności ID."""
        return self._all()

    def changes_since(
        self,
        since: str | None = None,
        *,
        project: str | None = None,
        app: str | None = None,
        scope: str | None = None,
        limit: int = 200,
    ) -> dict[str, Any]:
        """Decyzje zmienione po znaczniku `since` (D7; plan docs/plan-d7-odczyt-przyrostowy.md), razem z zastąpionymi.

        `since`: znacznik `<changed_at>/<id>` z poprzedniej odpowiedzi (to, co po nim) albo chwila UTC
        `RRRR-MM-DDTGG:MM:SSZ` (od niej włącznie); brak — wszystko. Wpis dostaje `changed_at` (zapis; dla zastąpionej
        — zapis następczyni) i `text` (plik Decision Record). Zwraca `decisions`, `next` i `complete`.
        """
        after: tuple[str, int] | None = None
        start: str | None = None
        if since is not None:
            found = _CURSOR.match(since)
            if not found:
                raise InvalidDecision(
                    "since: znacznik <RRRR-MM-DDTGG:MM:SSZ>/<DEC-n> z poprzedniej odpowiedzi "
                    "albo chwila RRRR-MM-DDTGG:MM:SSZ."
                )
            if found.group(2):
                after = (found.group(1), _number(found.group(2)))
            else:
                start = found.group(1)
        files = {p: _read(p) for p in self._files()}
        recorded = {d["id"]: _recorded_at(d) for d in files.values()}
        wanted_project = project_slug(project) if project else None
        rows: list[tuple[tuple[str, int], Path, Decision]] = []
        for path, d in files.items():
            changed = max(_recorded_at(d), recorded.get(d.get("superseded_by", ""), ""))
            key = (changed, _number(d["id"]))
            if (after and key <= after) or (start and changed < start):
                continue
            if wanted_project and d.get("project") != wanted_project:
                continue
            if app and source_app(d) != app:
                continue
            if scope and (d.get("origin") or {}).get("scope") != scope:
                continue
            rows.append((key, path, d))
        rows.sort(key=lambda r: r[0])
        page = rows[:limit]
        out = [{**d, "changed_at": key[0], "text": path.read_text(encoding="utf-8")} for key, path, d in page]
        nxt = f"{page[-1][0][0]}/{page[-1][2]['id']}" if page else since
        return {"decisions": out, "next": nxt, "complete": len(rows) <= limit}

    # --- pliki ---

    def _path(self, decision: Decision) -> Path:
        """Plik decyzji: katalog projektu wynika z pola `project` (bez projektu: `_ogolne`)."""
        project: str = decision.get("project", GENERAL_PROJECT_DIR)
        return self._dir / project / f"{decision['id']}.md"

    def _files(self) -> list[Path]:
        if not self._dir.is_dir():
            return []
        return sorted(self._dir.glob("*/DEC-*.md"), key=lambda p: _number(p.stem))

    def _locate(self, decision_id: str) -> Path | None:
        number = _number(decision_id)
        return next((p for p in self._files() if _number(p.stem) == number), None)

    def _all(self) -> list[Decision]:
        return [_read(p) for p in self._files()]

    def _next_id(self) -> str:
        numbers = [_number(p.stem) for p in self._files()]
        return f"DEC-{max(numbers, default=0) + 1:04d}"

    def _find_same(self, draft: Decision) -> Decision | None:
        """Ten sam zapis ponowiony: ta sama treść, dzień, link źródła i pochodzenie (decyzje z innych aplikacji suity
        o tym samym numerze w różnych repo to różne decyzje)."""

        def key(d: Decision) -> tuple[Any, ...]:
            origin = d.get("origin") or {}
            where = (origin.get("app"), origin.get("scope"), origin.get("local_id"))
            return (d["statement"].strip(), d["decided_at"], d.get("source", {}).get("url"), where)

        wanted = key(draft)
        return next((d for d in self._all() if key(d) == wanted), None)

    def add_record_markers(self) -> dict[str, Any]:
        """Dopisuje znacznik Decision Record w plikach, które go nie mają (rejestry sprzed kontraktu 0.14.0).

        Plik zostaje tam, gdzie leży; pola decyzji bez zmian. Jeden commit; ponowne wywołanie niczego nie zmienia.
        """
        marked = []
        for path in self._files():
            decision = _read(path)
            if all(decision.get(k) is not None for k in MARKER_FIELDS):
                continue
            self._write(decision, overwrite=True, path=path)
            marked.append(path)
        warning = self.commit(marked, f"znacznik Decision Record w {len(marked)} decyzjach") if marked else None
        return {"marked": marked, **({"warning": warning} if warning else {})}

    def _write(self, decision: Decision, *, overwrite: bool, path: Path | None = None) -> None:
        """Zapisuje plik decyzji; uzupełnia w `decision` znacznik Decision Record (bieżąca wersja kontraktu)."""
        decision.update(record_marker())
        path = path or self._path(decision)
        path.parent.mkdir(parents=True, exist_ok=True)
        ordered = {k: decision[k] for k in FIELD_ORDER if k in decision}
        head = yaml.safe_dump(ordered, sort_keys=False, allow_unicode=True, width=1000)
        text = f"---\n{head}---\n{_render_body(ordered)}"
        with path.open("w" if overwrite else "x", encoding="utf-8") as f:
            f.write(text)

    def _commit(self, decision: Decision, paths: list[Path], message: str) -> Decision:
        """Commit w repo rejestru (jeśli to repo git). Porażka gita nie cofa zapisu — wraca jako ostrzeżenie."""
        failure = self.commit(paths, message)
        if failure is None:
            return decision
        return {**decision, "warning": f"Decyzja zapisana, ale commit git się nie udał: {failure}"}

    def commit(self, paths: list[Path], message: str) -> str | None:
        """Commituje pliki z katalogu rejestru, gdy to repo git; zwraca opis błędu gita albo None."""
        if not (self.root / ".git").exists():
            return None
        git = ["git", "-C", str(self.root)]
        try:
            subprocess.run([*git, "add", "--", *map(str, paths)], check=True, capture_output=True)  # noqa: S603
            subprocess.run([*git, "commit", "-q", "-m", message], check=True, capture_output=True)  # noqa: S603
        except subprocess.CalledProcessError as e:
            return (e.stderr or b"").decode("utf-8", "replace").strip()
        return None

    def now(self) -> datetime:
        """Bieżący moment według zegara rejestru (w testach — stały)."""
        return self._clock()


def project_slug(name: str) -> str:
    """Nazwa projektu jako nazwa katalogu: małe litery ASCII, cyfry i myślniki („Zamówienia B2B” → „zamowienia-b2b”)."""
    ascii_name = unicodedata.normalize("NFKD", name.replace("ł", "l").replace("Ł", "L"))
    ascii_name = ascii_name.encode("ascii", "ignore").decode().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name).strip("-")
    if not slug:
        raise InvalidDecision(f"project: „{name}” nie zawiera liter ani cyfr — podaj nazwę projektu, np. nazwę repo.")
    return slug


def _read(path: Path) -> Decision:
    _, head, _ = path.read_text(encoding="utf-8").split("---\n", 2)
    data = yaml.safe_load(head)
    if not isinstance(data, dict):
        raise InvalidDecision(f"{path.name}: uszkodzony frontmatter.")
    # Ręcznie wyedytowana data bez cudzysłowów to dla YAML obiekt daty; kontrakt trzyma daty jako tekst ISO.
    return {k: v.isoformat() if isinstance(v, date) else v for k, v in data.items()}


def _number(decision_id: str) -> int:
    match = _ID.match(decision_id)
    return int(match.group(1)) if match else 0


def _searchable_text(d: Decision) -> str:
    parts: list[str] = [d["statement"], d["why"], d["kind"]]
    parts += [o["option"] for o in d.get("options", ())]
    parts += [a["statement"] for a in d.get("assumptions", ())]
    parts += d.get("dependencies", [])
    parts += d.get("tags", [])
    # D4: także to, co decyzję uzasadnia i jej skutki, oraz numer u właściciela (np. D-012).
    parts += [e["text"] for e in d.get("evidence", ())]
    parts += [c["text"] for c in d.get("consequences", ())]
    parts += [f"{a['question']} {a['answer']}" for a in d.get("answers", ())]
    if d.get("confirmation"):
        parts.append(d["confirmation"]["how"])
    if d.get("source", {}).get("excerpt"):
        parts.append(d["source"]["excerpt"])
    if d.get("origin"):
        parts.append(d["origin"]["local_id"])
    return " ".join(parts).lower()


SUITE_APPS = ("pdi", "tf", "ci_for_sdlc", "shipscope")  # wartości `source` zdarzenia w kontrakcie


def source_app(d: Decision) -> str:
    """Aplikacja, z której pochodzi decyzja: `origin.app`; bez niego aplikacja suity z `source.kind` (decyzje
    ci_for_sdlc sprzed kontraktu 0.16.0); inaczej `pdi` — decyzja podjęta w DI Decision."""
    if d.get("origin"):
        return str(d["origin"]["app"])
    kind = d.get("source", {}).get("kind")
    return str(kind) if kind in SUITE_APPS else "pdi"


def _link(d: Decision) -> str | None:
    url = (d.get("origin") or {}).get("url") or d.get("source", {}).get("url")
    return str(url) if isinstance(url, str) and url.startswith(("https://", "http://")) else None


def _summary(d: Decision) -> Decision:
    summary: Decision = {
        k: d[k] for k in ("id", "statement", "why", "decided_at", "kind", "project", "status") if k in d
    }
    for k in ("tags", "superseded_by"):
        if k in d:
            summary[k] = d[k]
    summary["app"] = source_app(d)
    link = _link(d)
    if link:
        summary["link"] = link
    if d.get("origin"):
        summary["origin"] = {k: d["origin"][k] for k in ("app", "scope", "local_id")}
    summary["load_bearing_assumptions"] = [
        {"statement": a["statement"], "invalidated_if": a["invalidated_if"]}
        for a in d.get("assumptions", ())
        if a["load_bearing"]
    ]
    return summary


def _recorded_at(d: Decision) -> str:
    """Chwila zapisu; wpisy sprzed pola `recorded_at` liczą się od początku dnia decyzji."""
    return str(d.get("recorded_at") or f"{d['decided_at']}T00:00:00Z")


def record_marker() -> dict[str, str]:
    """Znacznik Decision Record (DR1): rozpoznanie pliku decyzji po nagłówku, wersja kontraktu zapisu."""
    return {
        "record": "decision",
        "schema": str(contract.load("decision")["$id"]),
        "contract_version": contract.CONTRACT_VERSION,
    }


_EFFECT = {"good": "dobry", "bad": "zły", "neutral": "neutralny"}


def _render_body(d: Decision) -> str:
    lines = [f"\n# {d['id']}: {d['statement']}\n", f"**Dlaczego:** {d['why']}\n"]
    project = d.get("project", "ogólna (bez projektu)")
    lines.append(
        f"Zdecydował(a): {d['decided_by']}, {d['decided_at']} · projekt: {project} · rodzaj: {d['kind']}"
        f" · status: {d['status']}\n"
    )
    if d.get("options"):
        lines.append("## Opcje\n")
        lines += [f"- {'**[wybrana]** ' if o['chosen'] else ''}{o['option']}" for o in d["options"]]
        lines.append("")
    if d.get("assumptions"):
        lines.append("## Założenia\n")
        lines += [
            f"- {'**nośne:** ' if a['load_bearing'] else ''}{a['statement']} — nieaktualne, gdy: {a['invalidated_if']}"
            for a in d["assumptions"]
        ]
        lines.append("")
    if d.get("answers"):
        lines.append("## Odpowiedzi na pytania\n")
        lines += [f"- {a['question']} → {a['answer']}" for a in d["answers"]]
        lines.append("")
    if d.get("consequences"):
        lines.append("## Skutki\n")
        lines += [f"- [{_EFFECT[c['effect']]}] {c['text']}" for c in d["consequences"]]
        lines.append("")
    if d.get("confirmation"):
        c = d["confirmation"]
        detail = ": ".join(x for x in (c.get("kind"), c.get("ref")) if x)
        lines.append("## Jak sprawdzić\n")
        lines.append(f"- {c['how']}" + (f" ({detail})" if detail else ""))
        lines.append("")
    if d.get("evidence"):
        lines.append("## Dowody\n")
        lines += [f"- [{e['epistemic_status']}] {e['text']}" for e in d["evidence"]]
        lines.append("")
    source = d["source"]
    lines.append(f"Źródło: {source['kind']}" + (f" — {source['url']}" if source.get("url") else ""))
    return "\n".join(lines) + "\n"
