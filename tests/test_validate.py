"""Walidator `pdi-validate` (specyfikacja contract/decision-record.md; plan docs/plan-spec-i-walidator-dr.md)."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

from pdi import contract
from pdi.registry import Registry
from pdi.validate import main, validate

Draft = Callable[..., dict[str, Any]]


def write_record(path: Path, head: dict[str, Any], body: str = "\n# Decyzja\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{yaml.safe_dump(head, sort_keys=False, allow_unicode=True)}---\n{body}", encoding="utf-8")
    return path


def example_head() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(
        (contract.CONTRACT_DIR / "examples" / "decision.json").read_text(encoding="utf-8")
    )
    return data


@pytest.fixture
def filled(registry: Registry, make_draft: Draft) -> Registry:
    registry.record(make_draft(project="sklep"))
    registry.record(make_draft(statement="Druga."))
    registry.supersede("DEC-0001", make_draft(statement="Trzecia.", project="sklep"))
    return registry


def problems(report: dict[str, Any]) -> list[str]:
    return [f"{e['path'].name}: {e['problem']}" for e in report["errors"]]


# --- poprawne pliki ---


def test_registry_written_by_pdi_is_valid(filled: Registry) -> None:
    report = validate([filled.root])

    assert report["errors"] == []
    assert report["records"] == 3


def test_contract_example_as_a_file_is_valid(tmp_path: Path) -> None:
    head = example_head()
    write_record(tmp_path / f"{head['id']}.md", head)

    assert validate([tmp_path])["errors"] == []


def test_other_markdown_in_a_directory_is_skipped(filled: Registry) -> None:
    (filled.root / "README.md").write_text("# Rejestr\n", encoding="utf-8")
    write_record(filled.root / "notes" / "spotkanie.md", {"title": "notatka"})

    report = validate([filled.root])

    assert (report["records"], report["skipped"], report["errors"]) == (3, 2, [])


# --- błędy w pojedynczym pliku ---


@pytest.mark.parametrize(
    ("patch", "expected"),
    [
        pytest.param({"statement": ""}, "statement", id="schemat"),
        pytest.param({"record": "adr"}, "record", id="zly-znacznik"),
        pytest.param({"contract_version": "99.0.0"}, "99.0.0", id="nowsza-wersja"),
        pytest.param({"id": "DEC-7"}, "DEC-7.md", id="nazwa-pliku"),
    ],
)
def test_single_file_problems(tmp_path: Path, patch: dict[str, Any], expected: str) -> None:
    head = {**example_head(), **patch}
    write_record(tmp_path / "DEC-41.md", head)

    found = problems(validate([tmp_path]))

    assert len(found) == 1 and expected in found[0], found


def test_unreadable_header_is_an_error(tmp_path: Path) -> None:
    (tmp_path / "DEC-1.md").write_text("---\nrecord: decision\nid: [nie zamknięte\n---\n", encoding="utf-8")

    assert "nagłówek" in problems(validate([tmp_path]))[0]


def test_file_given_directly_without_marker_is_an_error(tmp_path: Path) -> None:
    path = tmp_path / "notatka.md"
    path.write_text("# Notatka\n", encoding="utf-8")

    found = problems(validate([path]))

    assert found == ["notatka.md: to nie jest Decision Record (brak record: decision w nagłówku)"]


def test_errors_do_not_echo_decision_content(tmp_path: Path) -> None:
    head = {**example_head(), "kind": "tajne-słowo"}
    write_record(tmp_path / "DEC-41.md", head)

    assert all("tajne-słowo" not in p for p in problems(validate([tmp_path])))


# --- między plikami ---


def test_duplicate_id_is_an_error(filled: Registry) -> None:
    copy = filled.root / "decisions" / "inny" / "DEC-0002.md"
    copy.parent.mkdir(parents=True)
    copy.write_text(
        (filled.root / "decisions" / "_ogolne" / "DEC-0002.md").read_text(encoding="utf-8"), encoding="utf-8"
    )

    assert any("DEC-0002" in p and "powtórzone" in p for p in problems(validate([filled.root])))


def test_broken_supersede_chain_is_an_error(filled: Registry) -> None:
    newer = filled.root / "decisions" / "sklep" / "DEC-0003.md"
    newer.unlink()

    found = problems(validate([filled.root]))

    assert any("DEC-0001" in p and "DEC-0003" in p for p in found), found


def test_superseded_status_needs_a_successor(filled: Registry) -> None:
    path = filled.root / "decisions" / "_ogolne" / "DEC-0002.md"
    text = path.read_text(encoding="utf-8").replace("status: recorded", "status: superseded")
    path.write_text(text, encoding="utf-8")

    assert any(p.startswith("DEC-0002.md") and "superseded_by" in p for p in problems(validate([filled.root])))


# --- CLI ---


def test_cli_exit_codes(filled: Registry, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(filled.root)]) == 0
    assert "3 Decision Record" in capsys.readouterr().out

    bad = write_record(tmp_path / "zle" / "DEC-41.md", {**example_head(), "record": "adr"})
    assert main([str(bad.parent)]) == 1
    out = capsys.readouterr().out
    assert "✗" in out and "DEC-41.md" in out


def test_cli_needs_a_path(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main([])


def test_example_in_the_specification_is_valid(tmp_path: Path) -> None:
    spec = (contract.CONTRACT_DIR / "decision-record.md").read_text(encoding="utf-8")
    example = spec.split("```markdown\n", 1)[1].split("\n```", 1)[0] + "\n"
    (tmp_path / "DEC-0041.md").write_text(example, encoding="utf-8")

    report = validate([tmp_path])

    assert (report["records"], report["errors"]) == (1, [])
    assert yaml.safe_load(example.split("---\n")[1])["contract_version"] == contract.CONTRACT_VERSION
