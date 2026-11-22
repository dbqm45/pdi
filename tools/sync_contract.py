"""The contract/ directory of pdi: a pinned copy of the suite contract, never edited here.

Until 0.14.0 pdi was the contract's source; since 2026-11-22 the source is dbqm45/di-contract (tools/contract-pin.json).
pdi still reads contract/ at run time (src/pdi/contract.py), so it keeps the whole directory, generated from a tag.

  python3 tools/sync_contract.py sync  [--source DIR]   # replace contract/ with contract/ of the pinned tag
  python3 tools/sync_contract.py check [--source DIR]   # compare file by file; exit 1 and the differences when they differ

--source DIR: a local contract/ directory instead of cloning the tag (tests, offline work). Updating: change "version"
in the pin, run sync, run the tests, open a PR. Exit code: 0 — consistent or written, 1 — differs, 2 — bad pin or the
tag could not be fetched. Standard library and git only.
"""

from __future__ import annotations

import argparse
import filecmp
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN = ROOT / "tools" / "contract-pin.json"
TARGET = ROOT / "contract"


def read_pin() -> dict[str, str]:
    pin = json.loads(PIN.read_text(encoding="utf-8"))
    if set(pin) != {"repo", "version"}:
        raise ValueError("the pin has exactly two keys: repo and version")
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", str(pin["repo"])) or not re.fullmatch(r"\d+\.\d+\.\d+", str(pin["version"])):
        raise ValueError("repo is owner/name and version is X.Y.Z")
    return pin


def files(root: Path) -> set[str]:
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts}


def differences(source: Path) -> list[str]:
    want, have = files(source), files(TARGET)
    out = [f"missing: contract/{f}" for f in sorted(want - have)]
    out += [f"not in the contract: contract/{f}" for f in sorted(have - want)]
    out += [f"differs: contract/{f}" for f in sorted(want & have) if not filecmp.cmp(source / f, TARGET / f, shallow=False)]
    return out


def run(cmd: str, source: Path, label: str) -> int:
    if not (source / "contract.json").is_file():
        print(f"✗ {label}: no contract.json there")
        return 2
    if cmd == "sync":
        shutil.rmtree(TARGET, ignore_errors=True)
        shutil.copytree(source, TARGET)
        print(f"✓ contract/ written from {label}")
        return 0
    diff = differences(source)
    if diff:
        print(f"✗ contract/ differs from {label} — do not edit it here (the source is the pinned repo); run sync:")
        print("\n".join(f"  - {d}" for d in diff))
        return 1
    print(f"✓ contract/ matches {label}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["sync", "check"])
    ap.add_argument("--source", type=Path, help="a contract/ directory instead of cloning the tag")
    a = ap.parse_args(argv)
    try:
        pin = read_pin()
    except (OSError, ValueError) as e:
        print(f"✗ tools/contract-pin.json: {e}")
        return 2
    if a.source:
        return run(a.cmd, a.source.resolve(), str(a.source))
    tag = f"contract-v{pin['version']}"
    label = f"tag {tag} in {pin['repo']}"
    with tempfile.TemporaryDirectory() as tmp:
        url = f"https://github.com/{pin['repo']}.git"
        r = subprocess.run(["git", "clone", "-q", "--depth", "1", "--branch", tag, url, tmp], capture_output=True, text=True)
        if r.returncode != 0:
            print(f"✗ could not fetch {label}: {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else r.returncode}")
            return 2
        return run(a.cmd, Path(tmp) / "contract", label)


if __name__ == "__main__":
    sys.exit(main())
