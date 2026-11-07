"""`pdi-records migrate`: znacznik Decision Record (DR1, kontrakt 0.14.0) w plikach rejestru, które go nie mają.

Rejestr z `PDI_REGISTRY_PATH`. Plan: docs/plan-zapis-decision-record.md.
"""

from __future__ import annotations

import argparse
import sys

from pdi.registry import Registry


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="pdi-records", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("migrate", help="dopisz znacznik Decision Record w starych plikach (jeden commit)")
    parser.parse_args(sys.argv[1:] if argv is None else argv)
    result = Registry.from_env().add_record_markers()
    print(f"Znacznik Decision Record dopisany w {len(result['marked'])} plikach.")
    for path in result["marked"]:
        print(f"  {path}")
    if result.get("warning"):
        print(result["warning"], file=sys.stderr)


if __name__ == "__main__":
    main()
