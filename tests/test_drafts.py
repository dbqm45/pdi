"""Zapis decyzji tylko po zatwierdzeniu szkicu w konsoli (docs/plan-zapis-decyzji-po-zatwierdzeniu.md)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from pdi.drafts import DecisionDrafts, DraftNotFound, DraftRefused
from pdi.registry import InvalidDecision, Registry

Draft = Callable[..., dict[str, Any]]
T0 = datetime(2026, 11, 27, 10, 0, tzinfo=UTC)


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


def test_dr01_a_draft_is_checked_stored_with_its_hash_and_waits(reg: Registry, make_draft: Draft) -> None:
    drafts = DecisionDrafts(reg)
    shown = drafts.present(make_draft(), presented_by={"name": "agent"})
    assert shown["id"] == "DRF-1" and shown["status"] == "pending" and len(shown["sha256"]) == 64
    assert (reg.root / "decision-drafts" / "DRF-1.yaml").is_file()
    assert drafts.present(make_draft(statement="Inna treść."))["sha256"] != shown["sha256"]
    with pytest.raises(InvalidDecision, match="success_metric"):
        drafts.present(make_draft(success_metric={"metric": "marża"}))
    assert reg.decisions() == [], "nic nie trafia do rejestru przed zatwierdzeniem"


def test_dr02_record_needs_an_approval_of_that_very_content(reg: Registry, make_draft: Draft) -> None:
    drafts = DecisionDrafts(reg)
    d = drafts.present(make_draft())
    with pytest.raises(DraftRefused, match="czeka na zatwierdzenie"):
        drafts.record(d["id"], d["sha256"])
    with pytest.raises(DraftRefused, match="skrót"):
        drafts.approve(d["id"], "0" * 64, by={"name": "Ola"})
    drafts.approve(d["id"], d["sha256"], by={"name": "Ola", "sub": "s-ola"})
    with pytest.raises(DraftRefused, match="skrót"):
        drafts.record(d["id"], "0" * 64)
    saved = drafts.record(d["id"], d["sha256"])
    assert saved["id"] == "DEC-0001" and saved["statement"] == make_draft()["statement"]
    with pytest.raises(DraftRefused, match="już zapisany"):
        drafts.record(d["id"], d["sha256"])
    entry = drafts.get(d["id"])
    assert entry["status"] == "recorded" and entry["decision_id"] == "DEC-0001"
    assert entry["approved_by"] == {"name": "Ola", "sub": "s-ola"}
    with pytest.raises(DraftNotFound):
        drafts.get("DRF-404")


def test_dr03_the_approver_is_who_decided_when_the_draft_does_not_say(reg: Registry, make_draft: Draft) -> None:
    drafts = DecisionDrafts(reg)
    args = make_draft()
    args.pop("decided_by", None)
    d = drafts.present(args)
    drafts.approve(d["id"], d["sha256"], by={"name": "Ola Test", "sub": "s-ola"})
    saved = drafts.record(d["id"], d["sha256"])
    assert saved["decided_by"] == "Ola Test" and saved["decided_by_id"] == "s-ola"


def test_dr04_a_rejection_reason_goes_back_to_the_agent(reg: Registry, make_draft: Draft) -> None:
    drafts = DecisionDrafts(reg)
    d = drafts.present(make_draft())
    drafts.reject(d["id"], d["sha256"], by={"name": "Ola"}, reason="Uzasadnienie pomija koszt dostawy.")
    with pytest.raises(DraftRefused, match="odrzucony.*koszt dostawy"):
        drafts.record(d["id"], d["sha256"])
    with pytest.raises(DraftRefused, match="odrzucony"):
        drafts.approve(d["id"], d["sha256"], by={"name": "Ola"})
    with pytest.raises(DraftRefused, match="powód"):
        drafts.reject(drafts.present(make_draft(statement="B."))["id"], "x", by={"name": "Ola"}, reason=" ")


def test_dr05_approval_lasts_an_hour_and_a_draft_a_week(reg: Registry, clock: Clock, make_draft: Draft) -> None:
    drafts = DecisionDrafts(reg)
    d = drafts.present(make_draft())
    drafts.approve(d["id"], d["sha256"], by={"name": "Ola"})
    clock.now = T0 + timedelta(minutes=61)
    with pytest.raises(DraftRefused, match="wygasła"):
        drafts.record(d["id"], d["sha256"])
    old = drafts.present(make_draft(statement="Stary szkic."))
    clock.now = T0 + timedelta(days=8)
    with pytest.raises(DraftRefused, match="wygasł"):
        drafts.approve(old["id"], old["sha256"], by={"name": "Ola"})


def test_dr06_a_draft_may_supersede_a_recorded_decision(reg: Registry, make_draft: Draft) -> None:
    drafts = DecisionDrafts(reg)
    first = drafts.present(make_draft())
    drafts.approve(first["id"], first["sha256"], by={"name": "Ola"})
    drafts.record(first["id"], first["sha256"])
    with pytest.raises(LookupError):
        drafts.present(make_draft(statement="Nowa."), supersedes="DEC-0404")
    d = drafts.present(make_draft(statement="Próg obniżamy do 149 zł."), supersedes="DEC-0001")
    drafts.approve(d["id"], d["sha256"], by={"name": "Ola"})
    new = drafts.record(d["id"], d["sha256"])
    assert new["supersedes"] == "DEC-0001" and reg.get("DEC-0001")["status"] == "superseded"


# --- konsola: strona szkicu i przyciski ---


def test_dr07_the_console_shows_the_raw_draft_and_a_decider_approves_it(
    registry: Registry, make_draft: Draft, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.test_ask_team import people
    from tests.test_console_suite import Console, FakeIssuer

    d = DecisionDrafts(registry).present(make_draft(statement="Próg <b>199 zł</b> zostaje."))
    app = Console(registry, FakeIssuer(), monkeypatch)
    try:
        s = people(app)
        status, _, page, _ = app.request("GET", "/drafts", cookie=s["viewer"])
        assert status == 200 and d["id"] in page
        status, _, page, _ = app.request("GET", f"/drafts/{d['id']}", cookie=s["viewer"])
        assert status == 200
        assert "Próg &lt;b&gt;199 zł&lt;/b&gt; zostaje." in page and "<b>199" not in page
        assert d["sha256"] in page
        assert "Approve" not in page, "viewer widzi szkic, ale go nie zatwierdza"
        form = {"sha256": d["sha256"]}
        assert app.request("POST", f"/drafts/{d['id']}/approve", cookie=s["viewer"], form=form)[0] == 403
        assert app.request("POST", f"/drafts/{d['id']}/approve", cookie=s["ola"], form=form, origin=False)[0] == 403
        _, _, page, _ = app.request("GET", f"/drafts/{d['id']}", cookie=s["ola"])
        assert "Approve" in page and "Reject" in page
        status, _, page, _ = app.request("POST", f"/drafts/{d['id']}/approve", cookie=s["ola"], form=form)
        assert status == 200 and "record_decision" in page
        entry = DecisionDrafts(registry).get(d["id"])
        assert entry["status"] == "approved" and entry["approved_by"] == {"name": "Ola Test", "sub": "s-ola"}
        other = DecisionDrafts(registry).present(make_draft(statement="Drugi."))
        bad = {"sha256": other["sha256"], "reason": ""}
        assert app.request("POST", f"/drafts/{other['id']}/reject", cookie=s["ola"], form=bad)[0] == 400
        bad["reason"] = "Brakuje kosztu."
        assert app.request("POST", f"/drafts/{other['id']}/reject", cookie=s["ola"], form=bad)[0] == 200
        assert DecisionDrafts(registry).get(other["id"])["rejected_reason"] == "Brakuje kosztu."
        assert app.request("GET", "/drafts/DRF-404", cookie=s["ola"])[0] == 404
    finally:
        app.close()
