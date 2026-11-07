"""Zapis decyzji jako Decision Record (DR1–DR4, kontrakt 0.14.0; plan docs/plan-zapis-decision-record.md)."""

import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

from pdi import contract
from pdi.records import main
from pdi.registry import InvalidDecision, Registry

Draft = Callable[..., dict[str, Any]]
MARKER = {
    "record": "decision",
    "schema": "https://github.com/dbqm45/pdi/contract/decision.schema.json",
    "contract_version": contract.CONTRACT_VERSION,
}


def head(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8").split("---\n", 2)[1])
    return data


def file_of(registry: Registry, decision_id: str, project: str = "_ogolne") -> Path:
    return registry.root / "decisions" / project / f"{decision_id}.md"


def strip_marker(path: Path) -> None:
    """Plik sprzed kontraktu 0.14.0: ten sam nagłówek bez znacznika."""
    _, h, body = path.read_text(encoding="utf-8").split("---\n", 2)
    data = {k: v for k, v in yaml.safe_load(h).items() if k not in MARKER}
    path.write_text(f"---\n{yaml.safe_dump(data, sort_keys=False, allow_unicode=True)}---\n{body}", encoding="utf-8")


def git_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"):
        monkeypatch.setenv(var, "t")
    for var in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"):
        monkeypatch.setenv(var, "t@example.com")


# --- znacznik przy zapisie ---


def test_new_decision_file_is_a_decision_record(registry: Registry, make_draft: Draft) -> None:
    saved = registry.record(make_draft())

    h = head(file_of(registry, saved["id"]))
    assert {k: h[k] for k in MARKER} == MARKER
    assert list(h)[:3] == ["record", "schema", "contract_version"], "znacznik na początku nagłówka"
    assert {k: saved[k] for k in MARKER} == MARKER
    assert MARKER["schema"] == contract.load("decision")["$id"]
    assert contract.errors("decision", h) == []


def test_superseding_marks_both_files(registry: Registry, make_draft: Draft) -> None:
    registry.record(make_draft())
    strip_marker(file_of(registry, "DEC-0001"))

    registry.supersede("DEC-0001", make_draft(statement="Nowa."))

    assert head(file_of(registry, "DEC-0001"))["record"] == "decision"
    assert head(file_of(registry, "DEC-0002"))["record"] == "decision"


@pytest.mark.parametrize("field", ["record", "schema", "contract_version"])
def test_client_cannot_set_the_marker(registry: Registry, make_draft: Draft, field: str) -> None:
    with pytest.raises(InvalidDecision, match=field):
        registry.record(make_draft(**{field: MARKER[field]}))


# --- treść pliku ---


def test_body_shows_consequences_and_confirmation(registry: Registry, make_draft: Draft) -> None:
    saved = registry.record(
        make_draft(
            consequences=[
                {"text": "Marża dostawy zostaje dodatnia.", "effect": "good"},
                {"text": "Część klientów porzuci koszyk.", "effect": "bad"},
                {"text": "Bez wpływu na zwroty.", "effect": "neutral"},
            ],
            confirmation={"how": "Raport marży co miesiąc", "kind": "metric", "ref": "marza_dostawy"},
        )
    )

    body = file_of(registry, saved["id"]).read_text(encoding="utf-8").split("---\n", 2)[2]
    assert "## Skutki" in body
    assert "- [dobry] Marża dostawy zostaje dodatnia." in body
    assert "- [zły] Część klientów porzuci koszyk." in body
    assert "- [neutralny] Bez wpływu na zwroty." in body
    assert "## Jak sprawdzić" in body
    assert "Raport marży co miesiąc (metric: marza_dostawy)" in body


def test_body_without_new_fields_has_no_new_sections(registry: Registry, make_draft: Draft) -> None:
    saved = registry.record(make_draft())

    body = file_of(registry, saved["id"]).read_text(encoding="utf-8")
    assert "## Skutki" not in body and "## Jak sprawdzić" not in body


# --- migracja istniejących rejestrów ---


def test_migration_marks_old_files_in_place_and_commits(
    tmp_path: Path, make_draft: Draft, monkeypatch: pytest.MonkeyPatch
) -> None:
    git_env(monkeypatch)
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    reg = Registry(root)
    reg.record(make_draft(project="sklep"))
    reg.record(make_draft(statement="Druga."))
    old = file_of(reg, "DEC-0001", "sklep")
    moved = root / "decisions" / "inny" / "DEC-0001.md"
    moved.parent.mkdir(parents=True)
    strip_marker(old)
    old.rename(moved)  # przeniesiony ręcznie: migracja zostawia go tam, gdzie leży
    strip_marker(file_of(reg, "DEC-0002"))
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "stare pliki"], check=True)

    result = reg.add_record_markers()

    assert sorted(p.name for p in result["marked"]) == ["DEC-0001.md", "DEC-0002.md"]
    assert head(moved)["record"] == "decision" and not old.exists()
    assert head(moved)["project"] == "sklep", "pola decyzji bez zmian"
    log = subprocess.run(
        ["git", "-C", str(root), "log", "-1", "--format=%s"], check=True, capture_output=True, text=True
    )
    assert "Decision Record" in log.stdout
    assert reg.add_record_markers()["marked"] == [], "druga migracja niczego nie zmienia"


def test_cli_migrate_prints_the_count(
    tmp_path: Path, make_draft: Draft, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    reg = Registry(tmp_path)
    reg.record(make_draft())
    strip_marker(file_of(reg, "DEC-0001"))
    monkeypatch.setenv("PDI_REGISTRY_PATH", str(tmp_path))

    main(["migrate"])

    assert "1" in capsys.readouterr().out
    assert head(file_of(reg, "DEC-0001"))["record"] == "decision"
