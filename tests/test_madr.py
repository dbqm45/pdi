"""Eksport decyzji technicznych do MADR 4.0.0 i 2.1.2 (DR3; plan docs/plan-eksport-madr.md)."""

from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

import pytest
import yaml

from pdi import madr
from pdi.records import main
from pdi.registry import Registry

Draft = Callable[..., dict[str, Any]]


def technical(make_draft: Draft, **fields: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "statement": "Kolejka zdarzeń na Postgresie zamiast Redisa.",
        "why": "Jedna baza mniej do utrzymania; ruch mieści się w Postgresie.",
        "kind": "technical",
        "decided_by": "Anna",
        "decided_at": "2026-11-02",
        "project": "sklep",
        "options": [
            {"option": "Postgres (SKIP LOCKED)", "chosen": True, "note": "Już jest w stosie."},
            {"option": "Redis Streams", "chosen": False, "note": "Nowa usługa do utrzymania."},
        ],
        "consequences": [
            {"text": "Mniej usług w produkcji.", "effect": "good"},
            {"text": "Większe obciążenie bazy.", "effect": "bad"},
            {"text": "Bez wpływu na API.", "effect": "neutral"},
        ],
        "confirmation": {"how": "Test obciążeniowy kolejki", "kind": "test", "ref": "load/queue.js"},
        "assumptions": [
            {"statement": "Ruch poniżej 200 zdarzeń/s.", "load_bearing": True, "invalidated_if": "ruch > 200/s"}
        ],
        "links": {"chg": "CHG-12"},
        "source": {"kind": "claude-cli", "url": "https://example.com/rozmowa"},
    }
    base.update(fields)
    return make_draft(**{k: v for k, v in base.items() if v is not None})


def split(text: str) -> tuple[dict[str, Any], str]:
    assert text.startswith("---\n")
    _, head, body = text.split("---\n", 2)
    data: dict[str, Any] = yaml.safe_load(head)
    return data, body


@pytest.fixture
def reg(registry: Registry, make_draft: Draft) -> Registry:
    registry.record(technical(make_draft))  # DEC-0001
    registry.record(make_draft(statement="Próg dostawy 199 zł.", kind="product"))  # DEC-0002, nie techniczna
    return registry


# --- wybór i nazwy ---


def test_only_technical_decisions_are_exported(reg: Registry, tmp_path: Path) -> None:
    result = madr.export(reg, tmp_path / "out")

    assert [p.name for p in result["written"]] == ["0001-kolejka-zdarzen-na-postgresie-zamiast-redisa.md"]


def test_slug_is_ascii_without_polish_marks() -> None:
    assert madr.slug("Łączenie żądań źródła — w kolejce, Ć/ś/ó!") == "laczenie-zadan-zrodla-w-kolejce-c-s-o"
    assert len(madr.slug("bardzo " * 30)) <= 50


def test_project_filter(reg: Registry, make_draft: Draft, tmp_path: Path) -> None:
    reg.record(technical(make_draft, statement="Logi w JSON.", project="inny"))

    result = madr.export(reg, tmp_path, project="inny")

    assert [p.name for p in result["written"]] == ["0003-logi-w-json.md"]


# --- MADR 4.0.0 ---


def test_madr4_front_matter_and_sections(reg: Registry, tmp_path: Path) -> None:
    path = madr.export(reg, tmp_path)["written"][0]
    head, body = split(path.read_text(encoding="utf-8"))

    assert head == {"status": "accepted", "date": date(2026, 11, 2), "decision-makers": "Anna"}
    assert "\ndate: 2026-11-02\n" in path.read_text(encoding="utf-8"), "data bez cudzysłowów, jak w szablonie"
    assert body.lstrip().startswith("# Kolejka zdarzeń na Postgresie zamiast Redisa.")
    order = [
        "## Context and Problem Statement",
        "## Considered Options",
        "## Decision Outcome",
        "### Consequences",
        "### Confirmation",
        "## Pros and Cons of the Options",
        "## More Information",
    ]
    positions = [body.index(h) for h in order]
    assert positions == sorted(positions)
    assert 'Chosen option: "Postgres (SKIP LOCKED)", because Jedna baza mniej do utrzymania' in body
    assert "* Postgres (SKIP LOCKED)\n* Redis Streams" in body
    assert "* Good, because Mniej usług w produkcji." in body
    assert "* Bad, because Większe obciążenie bazy." in body
    assert "* Neutral, because Bez wpływu na API." in body
    assert "Test obciążeniowy kolejki (test: load/queue.js)" in body
    assert "### Redis Streams\n\nNowa usługa do utrzymania." in body
    assert "DEC-0001" in body and "CHG-12" in body and "ruch > 200/s" in body
    assert body.rstrip().endswith("-->") and "<!-- pdi: DEC-0001" in body


def test_decision_without_options_uses_its_statement(registry: Registry, make_draft: Draft, tmp_path: Path) -> None:
    registry.record(technical(make_draft, options=None, consequences=None, confirmation=None, assumptions=None))

    _, body = split(madr.export(registry, tmp_path)["written"][0].read_text(encoding="utf-8"))

    assert "## Considered Options\n\n* Kolejka zdarzeń na Postgresie zamiast Redisa." in body
    assert 'Chosen option: "Kolejka zdarzeń na Postgresie zamiast Redisa."' in body
    assert "### Consequences" not in body and "### Confirmation" not in body
    assert "## Pros and Cons of the Options" not in body


def test_superseded_points_to_its_successor(reg: Registry, make_draft: Draft, tmp_path: Path) -> None:
    reg.supersede("DEC-0001", technical(make_draft, statement="Kolejka na Redisie jednak."))  # DEC-0003

    written = {p.name[:4]: p for p in madr.export(reg, tmp_path)["written"]}

    assert split(written["0001"].read_text(encoding="utf-8"))[0]["status"] == "superseded by ADR-0003"
    assert split(written["0003"].read_text(encoding="utf-8"))[0]["status"] == "accepted"


def test_successor_outside_the_export_is_named_by_its_pdi_id(reg: Registry, make_draft: Draft, tmp_path: Path) -> None:
    reg.supersede("DEC-0001", technical(make_draft, statement="Inaczej.", kind="process"))  # DEC-0003, nie techniczna

    path = madr.export(reg, tmp_path)["written"][0]

    assert split(path.read_text(encoding="utf-8"))[0]["status"] == "superseded (pdi DEC-0003)"


# --- MADR 2.1.2 ---


def test_madr2_layout(reg: Registry, make_draft: Draft, tmp_path: Path) -> None:
    reg.supersede("DEC-0001", technical(make_draft, statement="Kolejka na Redisie jednak."))  # DEC-0003

    written = {p.name[:4]: p for p in madr.export(reg, tmp_path, fmt="2")["written"]}
    old = written["0001"].read_text(encoding="utf-8")
    new = written["0003"].read_text(encoding="utf-8")

    assert not old.startswith("---")
    assert old.startswith("# Kolejka zdarzeń na Postgresie zamiast Redisa.\n")
    assert "* Status: superseded by [ADR-0003](0003-kolejka-na-redisie-jednak.md)" in old
    assert "* Deciders: Anna" in new and "* Date: 2026-11-02" in new and "* Status: accepted" in new
    assert "Technical Story: CHG-12" in new
    assert "### Positive Consequences\n\n* Mniej usług w produkcji." in new
    assert "### Negative Consequences\n\n* Większe obciążenie bazy." in new
    assert "## Links" in new and "<!-- pdi: DEC-0003" in new
    assert new.count("CHG-12") == 2, "Technical Story i Links, bez powtórki w More Information"


# --- cudze pliki i powtarzalność ---


def test_hand_written_adr_with_the_same_number_is_left_alone(reg: Registry, tmp_path: Path) -> None:
    mine = tmp_path / "0001-wlasny-adr.md"
    mine.write_text("# Własny ADR\n", encoding="utf-8")

    result = madr.export(reg, tmp_path)

    assert mine.read_text(encoding="utf-8") == "# Własny ADR\n"
    assert result["written"] == [] and result["conflicts"] == [mine]


def test_second_export_writes_nothing_and_rename_removes_the_old_file(
    reg: Registry, make_draft: Draft, tmp_path: Path
) -> None:
    first = madr.export(reg, tmp_path)["written"][0]
    again = madr.export(reg, tmp_path)
    assert (again["written"], again["unchanged"]) == ([], [first])

    path = reg.root / "decisions" / "sklep" / "DEC-0001.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace("statement: Kolejka", "statement: Nowa kolejka"), encoding="utf-8"
    )
    third = madr.export(reg, tmp_path)

    assert third["removed"] == [first] and not first.exists()
    assert [p.name for p in third["written"]] == ["0001-nowa-kolejka-zdarzen-na-postgresie-zamiast-redisa.md"]


def test_reverted_decision_is_skipped(reg: Registry, tmp_path: Path) -> None:
    path = reg.root / "decisions" / "sklep" / "DEC-0001.md"
    path.write_text(path.read_text(encoding="utf-8").replace("status: recorded", "status: reverted"), encoding="utf-8")

    result = madr.export(reg, tmp_path)

    assert result["written"] == [] and result["skipped"] == [{"id": "DEC-0001", "reason": "status reverted"}]


# --- CLI ---


def test_cli_export(
    reg: Registry, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("PDI_REGISTRY_PATH", str(reg.root))
    out = tmp_path / "docs" / "decisions"

    main(["export-madr", "--out", str(out), "--format", "2"])

    assert (out / "0001-kolejka-zdarzen-na-postgresie-zamiast-redisa.md").is_file()
    assert "zapisane: 1" in capsys.readouterr().out
