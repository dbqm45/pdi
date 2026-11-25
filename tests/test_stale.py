"""DV6: zgłoszenia porzucone — odłożone i bez odpowiedzi (docs/plan-dv6-zgloszenia-porzucone.md)."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from pdi import console, stale
from pdi.mcp_server import build_server
from pdi.problems import ProblemStore
from pdi.registry import InvalidDecision, Registry
from tests.conftest import draft
from tests.test_console import TOKEN, _get, _post, _serve
from tests.test_problems import NOTIFY, FakeHook, problem

START = datetime(2026, 7, 1, 9, 0, tzinfo=UTC)


class Clock:
    def __init__(self) -> None:
        self.now = START

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def reg(tmp_path: Path, clock: Clock) -> Registry:
    return Registry(tmp_path / "rejestr", clock=clock)


def seed(reg: Registry, hook: FakeHook | None = None) -> ProblemStore:
    """PRB-1 odłożone, PRB-2 z pytaniami, PRB-3 nowe — wszystkie 1 lipca."""
    s = ProblemStore(reg, notify=NOTIFY, post=hook)
    for title in ("Odłożone", "Z pytaniami", "Nowe"):
        s.record(problem(title=title))
    s.triage("PRB-1", "parked", draft(statement="Odkładamy PRB-1.", kind="triage"), return_when="3 nowe zgłoszenia")
    s.clarify("PRB-2", ["Na ilu ładowarkach?"])
    return s


def test_st01_parked_after_90_days_and_unanswered_after_30_are_stale(reg: Registry, clock: Clock) -> None:
    s = seed(reg)
    clock.now = START + timedelta(days=31)
    assert [r["problem"] for r in stale.report(s, reg, now=clock.now)] == ["PRB-2"]
    clock.now = START + timedelta(days=91)
    rows = {r["problem"]: r for r in stale.report(s, reg, now=clock.now)}
    assert set(rows) == {"PRB-1", "PRB-2"}
    assert rows["PRB-1"]["status"] == "parked" and rows["PRB-1"]["days"] == 91
    assert rows["PRB-1"]["since"] == "2026-07-01" and "3 nowe zgłoszenia" in rows["PRB-1"]["reason"]
    assert rows["PRB-2"]["recommendation"] == "close" and rows["PRB-1"]["recommendation"] == "revalidate"


def test_st02_close_rejects_with_a_decision_and_tells_the_reporter(reg: Registry, clock: Clock) -> None:
    hook = FakeHook()
    s = seed(reg, hook)
    clock.now = START + timedelta(days=95)
    result = s.review_stale("PRB-2", "close", draft(statement="Zamykamy PRB-2: brak odpowiedzi.", kind="triage"))
    stored = s.get("PRB-2")
    assert (stored["status"], stored["rejection_reason"]) == ("rejected", "other")
    assert "brak odpowiedzi" in stored["rejection_note"]
    d = result["decision"]
    assert d["decision_type"] == "problem.stale_review" and d["links"]["prb"] == "PRB-2" and "porzucone" in d["tags"]
    assert hook.bodies()[-1]["what"] == "rejected"
    assert [r["problem"] for r in stale.report(s, reg, now=clock.now)] == ["PRB-1"]


def test_st03_revalidate_puts_it_back_in_the_triage_queue(reg: Registry, clock: Clock) -> None:
    hook = FakeHook()
    s = seed(reg, hook)
    clock.now = START + timedelta(days=95)
    s.review_stale("PRB-1", "revalidate", draft(statement="PRB-1 wraca do oceny.", kind="triage"))
    assert s.get("PRB-1")["status"] == "ready_for_triage"
    assert hook.bodies()[-1]["what"] == "returned"
    s.triage("PRB-1", "rejected", draft(kind="triage"), rejection_reason="out_of_strategy")  # triaż znowu możliwy


def test_st04_only_a_stale_problem_can_be_reviewed(reg: Registry, clock: Clock) -> None:
    s = seed(reg)
    clock.now = START + timedelta(days=10)
    with pytest.raises(InvalidDecision):
        s.review_stale("PRB-1", "close", draft(kind="triage"))
    with pytest.raises(InvalidDecision):
        s.review_stale("PRB-3", "close", draft(kind="triage"))
    clock.now = START + timedelta(days=95)
    with pytest.raises(InvalidDecision):
        s.review_stale("PRB-1", "delete", draft(kind="triage"))
    assert s.get("PRB-1")["status"] == "parked"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_st05_mcp_lists_and_reviews(reg: Registry, clock: Clock) -> None:
    seed(reg)
    clock.now = START + timedelta(days=95)
    server = build_server(lambda: reg)
    listed = (await server.call_tool("stale_problems", {})).structured_content["problems"]
    assert [r["problem"] for r in listed] == ["PRB-1", "PRB-2"]
    args = {k: v for k, v in draft(statement="Zamykamy.").items() if k != "kind"}
    done = await server.call_tool("review_stale_problem", {"problem_id": "PRB-2", "outcome": "close", **args})
    assert done.is_error is False and ProblemStore(reg).get("PRB-2")["status"] == "rejected"
    with pytest.raises(ToolError):
        await server.call_tool("review_stale_problem", {"problem_id": "PRB-3", "outcome": "close", **args})


def test_st06_console_shows_stale_problems_with_two_buttons(reg: Registry, clock: Clock) -> None:
    seed(reg)
    clock.now = START + timedelta(days=95)
    server, url = _serve(console.Deps(reg, checkout=None))
    try:
        page = _get(f"{url}/inbox?t={TOKEN}")[1].decode()
        assert "Zgłoszenia porzucone" in page and "/problems/PRB-1/stale" in page
        form = {"t": TOKEN, "statement": "PRB-1 wraca.", "why": "Nowe dane.", "outcome": "revalidate"}
        status, body = _post(f"{url}/problems/PRB-1/stale?t={TOKEN}", form)
        assert status == 200, body
        assert ProblemStore(reg).get("PRB-1")["status"] == "ready_for_triage"
        assert _post(f"{url}/problems/PRB-3/stale?t={TOKEN}", form)[0] == 409
    finally:
        server.shutdown()
