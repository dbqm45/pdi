"""tools/sync_contract.py: contract/ is a pinned copy of dbqm45/di-contract (`check` only, on local copies)."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "sync_contract.py"


def check(source: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(TOOL), "check", "--source", str(source)], capture_output=True, text=True)


def test_the_pin_names_di_contract_and_the_version_pdi_reads() -> None:
    pin = json.loads((ROOT / "tools" / "contract-pin.json").read_text(encoding="utf-8"))
    version = json.loads((ROOT / "contract" / "contract.json").read_text(encoding="utf-8"))["version"]

    assert pin == {"repo": "dbqm45/di-contract", "version": version}


def test_an_identical_source_passes(tmp_path: Path) -> None:
    shutil.copytree(ROOT / "contract", tmp_path / "contract")

    r = check(tmp_path / "contract")

    assert r.returncode == 0, r.stdout


def test_a_changed_missing_or_extra_file_is_named(tmp_path: Path) -> None:
    src = tmp_path / "contract"
    shutil.copytree(ROOT / "contract", src)
    (src / "task.schema.json").write_text("{}\n", encoding="utf-8")
    (src / "story.schema.json").unlink()
    (src / "new.schema.json").write_text("{}\n", encoding="utf-8")

    r = check(src)

    assert r.returncode == 1
    assert "differs: contract/task.schema.json" in r.stdout
    assert "not in the contract: contract/story.schema.json" in r.stdout
    assert "missing: contract/new.schema.json" in r.stdout


def test_a_source_without_contract_json_is_refused(tmp_path: Path) -> None:
    assert check(tmp_path).returncode == 2
