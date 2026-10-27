from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from pdi.registry import Registry
from pdi.stats import main, summarize

Draft = Callable[..., dict[str, Any]]


def registry_at(root: Path, *moments: datetime) -> Registry:
    clock = iter(moments)
    return Registry(root, clock=lambda: next(clock))


def test_summary_counts_decisions_per_iso_week(tmp_path: Path, make_draft: Draft) -> None:
    reg = registry_at(
        tmp_path,
        datetime(2026, 10, 26, 9, tzinfo=UTC),  # poniedziałek, tydzień 44
        datetime(2026, 10, 30, 9, tzinfo=UTC),
        datetime(2026, 11, 2, 9, tzinfo=UTC),  # tydzień 45
    )
    reg.record(make_draft(statement="A."))
    reg.record(make_draft(statement="B.", drafted_by="human", kind="technical"))
    reg.record(make_draft(statement="C."))

    s = summarize(reg)

    assert s["total"] == 3
    assert s["per_week"] == {"2026-W44": 2, "2026-W45": 1}
    assert s["drafted_by"] == {"ai": 2, "human": 1}
    assert s["kinds"] == {"product": 2, "technical": 1}


def test_summary_counts_superseded_and_assumptions(tmp_path: Path, make_draft: Draft) -> None:
    reg = registry_at(tmp_path, *[datetime(2026, 10, 26, 9, tzinfo=UTC)] * 2)
    reg.record(make_draft(assumptions=[{"statement": "x", "load_bearing": True, "invalidated_if": "y"}]))
    reg.supersede("DEC-0001", make_draft(statement="Zmiana."))

    s = summarize(reg)

    assert s["superseded"] == 1
    assert s["with_load_bearing_assumptions"] == 1


def test_cli_prints_summary(
    tmp_path: Path, make_draft: Draft, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    registry_at(tmp_path, datetime(2026, 10, 26, 9, tzinfo=UTC)).record(make_draft())
    monkeypatch.setenv("PDI_REGISTRY_PATH", str(tmp_path))

    main()

    out = capsys.readouterr().out
    assert "2026-W44: 1" in out
    assert "Razem: 1" in out
    assert "Autonomia" in out and "finding.auto_close: poziom 3" in out
    assert "Prognozy (G3): 0, z wynikiem 0" in out


def test_summary_counts_per_project(tmp_path: Path, make_draft: Draft) -> None:
    reg = registry_at(tmp_path, *[datetime(2026, 10, 26, 9, tzinfo=UTC)] * 3)
    reg.record(make_draft(statement="A.", project="sklep"))
    reg.record(make_draft(statement="B.", project="sklep"))
    reg.record(make_draft(statement="C."))

    assert summarize(reg)["projects"] == {"sklep": 2, "_ogolne": 1}
