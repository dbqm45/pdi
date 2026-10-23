import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

from pdi.registry import CannotSupersede, DecisionNotFound, InvalidDecision, Registry

Draft = Callable[..., dict[str, Any]]


def frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    _, head, _ = text.split("---\n", 2)
    data = yaml.safe_load(head)
    assert isinstance(data, dict)
    return data


def test_record_assigns_id_status_and_timestamp(registry: Registry, make_draft: Draft) -> None:
    saved = registry.record(make_draft())

    assert saved["id"] == "DEC-0001"
    assert saved["status"] == "recorded"
    assert saved["recorded_at"] == "2026-10-23T09:30:00Z"


def test_record_writes_markdown_with_frontmatter_and_readable_body(registry: Registry, make_draft: Draft) -> None:
    saved = registry.record(make_draft())

    path = registry.root / "decisions" / "DEC-0001.md"
    assert saved["path"] == str(path)
    assert frontmatter(path)["statement"] == make_draft()["statement"]
    body = path.read_text(encoding="utf-8").split("---\n", 2)[2]
    assert "# DEC-0001" in body
    assert make_draft()["why"] in body


def test_ids_are_sequential(registry: Registry, make_draft: Draft) -> None:
    first = registry.record(make_draft(statement="Pierwsza."))
    second = registry.record(make_draft(statement="Druga."))

    assert (first["id"], second["id"]) == ("DEC-0001", "DEC-0002")


def test_get_returns_stored_decision(registry: Registry, make_draft: Draft) -> None:
    registry.record(make_draft())

    got = registry.get("DEC-0001")

    assert got["statement"] == make_draft()["statement"]
    assert got["source"]["kind"] == "claude-cli"


def test_get_unknown_id_raises(registry: Registry) -> None:
    with pytest.raises(DecisionNotFound, match="DEC-0042"):
        registry.get("DEC-0042")


def test_decided_at_defaults_to_today(registry: Registry, make_draft: Draft) -> None:
    d = make_draft()
    del d["decided_at"]

    assert registry.record(d)["decided_at"] == "2026-10-23"


def test_decided_by_defaults_to_env(registry: Registry, make_draft: Draft, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PDI_DECIDED_BY", "dbqm45")
    d = make_draft()
    del d["decided_by"]

    assert registry.record(d)["decided_by"] == "dbqm45"


def test_missing_decided_by_without_env_explains_fix(
    registry: Registry, make_draft: Draft, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("PDI_DECIDED_BY", raising=False)
    d = make_draft()
    del d["decided_by"]

    with pytest.raises(InvalidDecision, match="PDI_DECIDED_BY"):
        registry.record(d)


def test_invalid_draft_is_rejected_and_nothing_written(registry: Registry, make_draft: Draft) -> None:
    with pytest.raises(InvalidDecision, match="kind"):
        registry.record(make_draft(kind="whim"))

    assert not list((registry.root / "decisions").glob("*.md")) if (registry.root / "decisions").exists() else True


def test_client_cannot_set_registry_fields(registry: Registry, make_draft: Draft) -> None:
    with pytest.raises(InvalidDecision, match="id"):
        registry.record(make_draft(id="DEC-0099"))


def test_repeated_record_returns_existing_instead_of_duplicate(registry: Registry, make_draft: Draft) -> None:
    first = registry.record(make_draft())
    again = registry.record(make_draft())

    assert again["id"] == first["id"]
    assert again["duplicate"] is True
    assert len(list((registry.root / "decisions").glob("*.md"))) == 1


def test_find_matches_words_case_insensitively_and_ranks(registry: Registry, make_draft: Draft) -> None:
    registry.record(make_draft(statement="Zostajemy przy PostgreSQL.", why="Zespół zna bazę.", kind="technical"))
    registry.record(make_draft())
    registry.record(make_draft(statement="Przewoźnik Y dla dostaw ekspresowych.", why="Szybszy na trasie dostawy."))

    found = registry.find("dostaw przewoźnik")

    assert [f["id"] for f in found] == ["DEC-0003", "DEC-0002"]


def test_find_summary_includes_load_bearing_assumptions_only(registry: Registry, make_draft: Draft) -> None:
    registry.record(
        make_draft(
            assumptions=[
                {"statement": "udział X ok. 65%", "load_bearing": True, "invalidated_if": "udział X < 40%"},
                {"statement": "pogoda bez znaczenia", "load_bearing": False, "invalidated_if": "nigdy"},
            ]
        )
    )

    (hit,) = registry.find("próg")

    assert set(hit) >= {"id", "statement", "why", "decided_at", "status", "kind"}
    assert hit["load_bearing_assumptions"] == [{"statement": "udział X ok. 65%", "invalidated_if": "udział X < 40%"}]


def test_find_filters(registry: Registry, make_draft: Draft) -> None:
    registry.record(make_draft(statement="A.", tags=["dostawa"], decided_at="2026-09-01"))
    registry.record(make_draft(statement="B.", tags=["dostawa", "ceny"], kind="process"))
    registry.record(make_draft(statement="C.", tags=["ceny"]))

    assert [f["id"] for f in registry.find(tags=["dostawa"])] == ["DEC-0002", "DEC-0001"]
    assert [f["id"] for f in registry.find(kind="process")] == ["DEC-0002"]
    assert [f["id"] for f in registry.find(since="2026-10-01")] == ["DEC-0003", "DEC-0002"]
    assert len(registry.find(limit=1)) == 1


def test_find_on_empty_registry_returns_nothing(registry: Registry) -> None:
    assert registry.find("cokolwiek") == []


def test_supersede_links_both_decisions(registry: Registry, make_draft: Draft) -> None:
    registry.record(make_draft())

    new = registry.supersede("DEC-0001", make_draft(statement="Próg darmowej dostawy obniżamy do 149 zł."))

    old = registry.get("DEC-0001")
    assert new["supersedes"] == "DEC-0001"
    assert old["status"] == "superseded"
    assert old["superseded_by"] == new["id"]
    assert [f["id"] for f in registry.find(status="recorded")] == [new["id"]]


def test_supersede_only_active_decision(registry: Registry, make_draft: Draft) -> None:
    registry.record(make_draft())
    registry.supersede("DEC-0001", make_draft(statement="Nowa."))

    with pytest.raises(CannotSupersede, match="DEC-0002"):
        registry.supersede("DEC-0001", make_draft(statement="Jeszcze nowsza."))


def test_supersede_unknown_decision(registry: Registry, make_draft: Draft) -> None:
    with pytest.raises(DecisionNotFound):
        registry.supersede("DEC-0007", make_draft())


def test_record_commits_when_registry_is_git_repo(
    tmp_path: Path, make_draft: Draft, monkeypatch: pytest.MonkeyPatch
) -> None:
    for var, val in {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.com",
    }.items():
        monkeypatch.setenv(var, val)
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)

    Registry(root).record(make_draft())

    log = subprocess.run(
        ["git", "-C", str(root), "log", "--format=%s"], check=True, capture_output=True, text=True
    ).stdout
    assert log.startswith("DEC-0001:")


def test_from_env_requires_registry_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PDI_REGISTRY_PATH", raising=False)

    with pytest.raises(RuntimeError, match="PDI_REGISTRY_PATH"):
        Registry.from_env()


def test_hand_edited_unquoted_dates_are_read_as_text(registry: Registry, make_draft: Draft) -> None:
    registry.record(make_draft())
    path = registry.root / "decisions" / "DEC-0001.md"
    path.write_text(path.read_text(encoding="utf-8").replace("'2026-10-22'", "2026-10-22"), encoding="utf-8")

    assert registry.get("DEC-0001")["decided_at"] == "2026-10-22"
    assert [f["id"] for f in registry.find(since="2026-10-01")] == ["DEC-0001"]


def test_failed_commit_keeps_decision_and_warns(
    tmp_path: Path, make_draft: Draft, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "nie-ma"))  # każde polecenie git zawiedzie

    saved = Registry(root).record(make_draft())

    assert saved["id"] == "DEC-0001"
    assert "git" in saved["warning"]
    assert (root / "decisions" / "DEC-0001.md").is_file()
