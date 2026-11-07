"""`pdi-validate <plik|katalog>...`: sprawdza pliki Decision Record wg contract/decision-record.md (kontrakt 0.14.0).

Katalog: wszystkie pliki `.md` rekurencyjnie; pliki bez pola `record` w nagłówku to nie Decision Record i są
pomijane. Plik podany wprost musi być Decision Record. Komunikaty nie powtarzają treści decyzji, tylko plik
i regułę. Kod wyjścia 1 przy błędzie (dla CI). Plan: docs/plan-spec-i-walidator-dr.md.
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from pdi import contract

RECORD = "decision"
NOT_A_RECORD = "to nie jest Decision Record (brak record: decision w nagłówku)"


def _version(text: str) -> tuple[int, ...] | None:
    parts = text.split(".")
    return tuple(int(p) for p in parts) if len(parts) == 3 and all(p.isdigit() for p in parts) else None


def _header(path: Path) -> tuple[str, dict[str, Any] | None]:
    """(surowy nagłówek, dane) — dane None, gdy nagłówka nie ma albo YAML jest nieczytelny."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return "", None
    raw, sep, _ = text[4:].partition("\n---\n")
    if not sep:
        return raw, None
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return raw, None
    if not isinstance(data, dict):
        return raw, None
    # Data bez cudzysłowów to dla YAML obiekt daty; kontrakt trzyma daty jako tekst ISO (jak rejestr pdi).
    return raw, {k: v.isoformat() if isinstance(v, date) else v for k, v in data.items()}


def _check_file(path: Path) -> list[str]:
    _, head = _header(path)
    assert head is not None  # noqa: S101 — wywoływane tylko dla plików z czytelnym nagłówkiem
    if head.get("record") != RECORD:
        return [f"record: oczekiwane {RECORD} (jedyny rodzaj zapisu w kontrakcie)"]
    current = contract.CONTRACT_VERSION
    written = str(head.get("contract_version", ""))
    found, mine = _version(written), _version(current)
    if found is not None and mine is not None and found > mine:
        return [f"zapisany wg kontraktu {written}, nowszego niż walidator ({current}) — zaktualizuj pdi"]
    problems = [f"schemat: {e}" for e in contract.rules_broken("decision", head)]
    decision_id = head.get("id")
    if isinstance(decision_id, str) and path.name != f"{decision_id}.md":
        problems.append(f"nazwa pliku powinna być {decision_id}.md (z pola id)")
    return problems


def validate(paths: list[Path]) -> dict[str, Any]:
    """Sprawdza pliki i katalogi: liczba Decision Record, pominiętych plików i błędy `{path, problem}`."""
    errors: list[dict[str, Any]] = []
    records: dict[Path, dict[str, Any]] = {}
    skipped = 0
    for given in paths:
        files = sorted(given.rglob("*.md")) if given.is_dir() else [given]
        for path in files:
            raw, head = _header(path)
            claims = "record:" in raw
            if head is None and raw and (claims or not given.is_dir()):
                errors.append({"path": path, "problem": "nagłówek YAML nieczytelny"})
                continue
            if head is None or "record" not in head:
                if not given.is_dir():
                    errors.append({"path": path, "problem": NOT_A_RECORD})
                else:
                    skipped += 1
                continue
            records[path] = head
            errors += [{"path": path, "problem": p} for p in _check_file(path)]
    errors += _check_links(records, complete=all(p.is_dir() for p in paths))
    return {"records": len(records), "skipped": skipped, "errors": errors}


def _check_links(records: dict[Path, dict[str, Any]], *, complete: bool) -> list[dict[str, Any]]:
    """Powtórzone id, łańcuch zastąpień i status `superseded`. Brak wskazanej decyzji — tylko dla całych katalogów."""
    errors: list[dict[str, Any]] = []
    by_id: dict[str, Path] = {}
    for path, head in records.items():
        decision_id = head.get("id")
        if not isinstance(decision_id, str):
            continue
        if decision_id in by_id:
            errors.append({"path": path, "problem": f"id {decision_id} powtórzone (też w {by_id[decision_id]})"})
        else:
            by_id[decision_id] = path
    for path, head in records.items():
        own = head.get("id")
        successor, predecessor = head.get("superseded_by"), head.get("supersedes")
        if (head.get("status") == "superseded") != bool(successor):
            errors.append({"path": path, "problem": "status superseded wymaga superseded_by (i odwrotnie)"})
        for field, target, back in (
            ("superseded_by", successor, "supersedes"),
            ("supersedes", predecessor, "superseded_by"),
        ):
            if not isinstance(target, str):
                continue
            if target not in by_id:
                if complete:
                    errors.append({"path": path, "problem": f"{field} {target}: brak takiej decyzji ({own})"})
                continue
            if records[by_id[target]].get(back) != own:
                problem = f"{field} {target}: tamta decyzja nie ma {back} {own}"
                errors.append({"path": path, "problem": problem})
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pdi-validate", description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="pliki Decision Record albo katalogi z nimi")
    args = parser.parse_args(argv)
    report = validate(args.paths)
    for e in report["errors"]:
        print(f"✗ {e['path']}: {e['problem']}")
    mark = "✓" if not report["errors"] else "✗"
    print(
        f"{mark} {report['records']} Decision Record, błędów: {len(report['errors'])}, "
        f"pominięte pliki bez znacznika: {report['skipped']}"
    )
    return 1 if report["errors"] else 0


def cli() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    cli()
