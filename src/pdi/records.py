"""`pdi-records`: polecenia na plikach Decision Record w rejestrze (`PDI_REGISTRY_PATH`).

- `migrate` — znacznik Decision Record (DR1, kontrakt 0.14.0) w plikach, które go nie mają
  (plan: docs/plan-zapis-decision-record.md);
- `export-madr --out <katalog> [--project P] [--format 4|2]` — decyzje techniczne jako MADR 4.0.0 albo 2.1.2
  (DR3, plan: docs/plan-eksport-madr.md).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pdi import madr
from pdi.registry import Registry


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="pdi-records", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("migrate", help="dopisz znacznik Decision Record w starych plikach (jeden commit)")
    export = sub.add_parser("export-madr", help="zapisz decyzje techniczne jako pliki MADR")
    export.add_argument("--out", type=Path, required=True, help="katalog ADR, np. docs/decisions w repo projektu")
    export.add_argument("--project", help="tylko decyzje tego projektu")
    export.add_argument("--format", choices=madr.FORMATS, default="4", help="4 = MADR 4.0.0 (domyślnie), 2 = 2.1.2")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    registry = Registry.from_env()
    if args.command == "export-madr":
        _export(registry, args.out, args.project, args.format)
        return
    result = registry.add_record_markers()
    print(f"Znacznik Decision Record dopisany w {len(result['marked'])} plikach.")
    for path in result["marked"]:
        print(f"  {path}")
    if result.get("warning"):
        print(result["warning"], file=sys.stderr)


def _export(registry: Registry, out: Path, project: str | None, fmt: str) -> None:
    r = madr.export(registry, out, project=project, fmt=fmt)
    print(
        f"MADR {'4.0.0' if fmt == '4' else '2.1.2'} w {out}: zapisane: {len(r['written'])}, bez zmian: "
        f"{len(r['unchanged'])}, usunięte: {len(r['removed'])}, pominięte: {len(r['skipped'])}, "
        f"konflikty: {len(r['conflicts'])}"
    )
    for path in r["conflicts"]:
        print(f"  ✗ {path}: ADR napisany ręcznie pod tym numerem — zostawiony, decyzja nie wyeksportowana")
    for s in r["skipped"]:
        print(f"  – {s['id']}: {s['reason']}")


if __name__ == "__main__":
    main()
