"""D7: odczyt przyrostowy indeksu decyzji (plan docs/plan-d7-odczyt-przyrostowy.md)."""

import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from pdi.records import main
from pdi.registry import InvalidDecision, Registry

Draft = Callable[..., dict[str, Any]]
T0 = datetime(2026, 11, 23, 10, 0, tzinfo=UTC)


class Clock:
    def __init__(self) -> None:
        self.now = T0

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def reg(tmp_path: Path, clock: Clock) -> Registry:
    return Registry(tmp_path / "rejestr", clock=clock)


def ids(result: dict[str, Any]) -> list[str]:
    return [d["id"] for d in result["decisions"]]


def test_first_read_returns_everything_as_decision_records(reg: Registry, make_draft: Draft, clock: Clock) -> None:
    reg.record(make_draft(statement="A."))
    clock.now += timedelta(minutes=1)
    reg.record(make_draft(statement="B."))

    result = reg.changes_since()

    assert ids(result) == ["DEC-0001", "DEC-0002"]
    first = result["decisions"][0]
    assert first["changed_at"] == "2026-11-23T10:00:00Z"
    assert first["text"] == (reg.root / "decisions" / "_ogolne" / "DEC-0001.md").read_text(encoding="utf-8")
    assert first["text"].startswith("---\nrecord: decision\n")
    assert (result["next"], result["complete"]) == ("2026-11-23T10:01:00Z/DEC-0002", True)


def test_next_read_returns_only_what_changed(reg: Registry, make_draft: Draft, clock: Clock) -> None:
    reg.record(make_draft(statement="A."))
    cursor = reg.changes_since()["next"]
    assert reg.changes_since(cursor)["decisions"] == []

    clock.now += timedelta(minutes=5)
    reg.record(make_draft(statement="B."))
    result = reg.changes_since(cursor)

    assert ids(result) == ["DEC-0002"]
    assert reg.changes_since(result["next"])["decisions"] == []
    assert reg.changes_since(result["next"])["next"] == result["next"], "bez zmian znacznik zostaje"


def test_superseding_also_returns_the_old_decision(reg: Registry, make_draft: Draft, clock: Clock) -> None:
    reg.record(make_draft(statement="A."))
    cursor = reg.changes_since()["next"]
    clock.now += timedelta(hours=1)

    reg.supersede("DEC-0001", make_draft(statement="A2."))
    result = reg.changes_since(cursor)

    assert ids(result) == ["DEC-0001", "DEC-0002"]
    old = result["decisions"][0]
    assert (old["status"], old["superseded_by"], old["changed_at"]) == (
        "superseded",
        "DEC-0002",
        "2026-11-23T11:00:00Z",
    )
    assert "status: superseded" in old["text"]


def test_paging_within_one_second_loses_and_repeats_nothing(reg: Registry, make_draft: Draft) -> None:
    for n in range(5):
        reg.record(make_draft(statement=f"Decyzja {n}."))  # ta sama sekunda

    seen: list[str] = []
    cursor = None
    while True:
        page = reg.changes_since(cursor, limit=2)
        seen += ids(page)
        cursor = page["next"]
        if page["complete"]:
            break

    assert seen == [f"DEC-{n:04d}" for n in range(1, 6)]


def test_since_as_a_moment_is_inclusive(reg: Registry, make_draft: Draft, clock: Clock) -> None:
    reg.record(make_draft(statement="A."))
    clock.now += timedelta(minutes=1)
    reg.record(make_draft(statement="B."))

    assert ids(reg.changes_since("2026-11-23T10:01:00Z")) == ["DEC-0002"]


@pytest.mark.parametrize("since", ["wczoraj", "2026-11-23", "2026-11-23T10:00:00Z/dec-1"])
def test_bad_since_is_refused(reg: Registry, since: str) -> None:
    with pytest.raises(InvalidDecision, match="since"):
        reg.changes_since(since)


def test_scope_filters(reg: Registry, make_draft: Draft) -> None:
    origin = {"app": "tf", "scope": "dbqm45/sklep", "local_id": "D-1"}
    reg.record(make_draft(statement="Z pdi.", project="sklep"))
    reg.record(make_draft(statement="Z tf.", origin=origin, source={"kind": "tf"}))
    reg.record(
        make_draft(statement="Z tf, inne repo.", origin={**origin, "scope": "dbqm45/inny"}, source={"kind": "tf"})
    )

    assert ids(reg.changes_since(project="sklep")) == ["DEC-0001"]
    assert ids(reg.changes_since(app="tf")) == ["DEC-0002", "DEC-0003"]
    assert ids(reg.changes_since(scope="dbqm45/sklep")) == ["DEC-0002"]


def test_cli_prints_json(
    reg: Registry, make_draft: Draft, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    reg.record(make_draft(statement="A."))
    monkeypatch.setenv("PDI_REGISTRY_PATH", str(reg.root))

    main(["changes"])
    first = json.loads(capsys.readouterr().out)
    main(["changes", "--since", first["next"]])
    second = json.loads(capsys.readouterr().out)

    assert ids(first) == ["DEC-0001"] and first["complete"] is True
    assert second["decisions"] == []
