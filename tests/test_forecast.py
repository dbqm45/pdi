import json
from datetime import date
from typing import Any

import pytest

from pdi.forecast import calibration, compare, estimate, read_flow, read_tasks
from pdi.impact import ShipScopeConfig

TOKEN = "shps_test"  # noqa: S105 — token testowy
CONFIG = ShipScopeConfig(url="https://shipscope.example.com/", token=TOKEN)


def flow(changes: list[tuple[int, float]], items: list[float] | None = None) -> dict[str, Any]:
    """Odpowiedź `/flow` ShipScope z dostarczonymi zmianami (cięcia, dni) i elementami (dni)."""
    return {
        "from": "2026-05-01",
        "to": "2026-10-27",
        "items": [{"key": f"TSK-{i}", "flowDays": d} for i, d in enumerate(items or [])],
        "changes": [{"key": f"CHG-{i}", "tasks": t, "flowDays": d} for i, (t, d) in enumerate(changes)],
    }


class FakeShipScope:
    def __init__(self, routes: dict[str, tuple[int, Any]]) -> None:
        self.routes = routes
        self.calls: list[tuple[str, dict[str, str]]] = []

    def __call__(self, url: str, headers: dict[str, str]) -> tuple[int, bytes]:
        self.calls.append((url, headers))
        for part, (status, body) in self.routes.items():
            if part in url:
                return status, json.dumps(body).encode()
        return 404, b"{}"


# --- prognoza ---


def test_estimate_multiplies_tasks_by_median_days_per_task() -> None:
    history = flow([(2, 4.0), (4, 4.0), (3, 6.0), (1, 3.0), (2, 1.0)])  # tempo 2, 1, 2, 3, 0.5

    f = estimate(3, history)

    assert (f["tasks"], f["basis"], f["expected_days"]) == (3, "changes", 6.0)
    assert (f["low_days"], f["high_days"]) == (3.0, 6.0)
    assert f["history"] == {"from": "2026-05-01", "to": "2026-10-27", "changes": 5, "items": 0}
    assert f["doubts"] == []


def test_estimate_doubts_short_history_and_a_bigger_plan_than_seen() -> None:
    f = estimate(6, flow([(2, 4.0), (3, 3.0)]))

    assert f["expected_days"] == 9.0  # 6 × mediana(2, 1)
    assert any("2 dostarczone zmiany" in d for d in f["doubts"])
    assert any("6 cięć" in d and "3" in d for d in f["doubts"])


def test_estimate_falls_back_to_item_flow_time() -> None:
    f = estimate(2, flow([], items=[1.0, 3.0, 2.0]))

    assert (f["basis"], f["expected_days"], f["low_days"], f["high_days"]) == ("items", 4.0, 3.0, 5.0)
    assert any("jedno po drugim" in d for d in f["doubts"])


def test_estimate_without_history_has_no_number() -> None:
    f = estimate(2, flow([]))

    assert (f["basis"], f["expected_days"], f["low_days"], f["high_days"]) == (None, None, None, None)
    assert any("Brak historii" in d for d in f["doubts"])


def test_estimate_skips_broken_history_rows() -> None:
    history = flow([(2, 4.0)])
    history["changes"] += [{"key": "CHG-x", "tasks": 0, "flowDays": 3}, {"key": "CHG-y", "tasks": "2"}, "zle"]

    assert estimate(1, history)["history"]["changes"] == 1


# --- porównanie i kalibracja ---


def test_compare_gives_ratio_and_range() -> None:
    f = {"expected_days": 6.0, "low_days": 3.0, "high_days": 6.0}

    assert compare(f, 9.0) == {"actual_days": 9.0, "ratio": 1.5, "within_range": False}
    assert compare(f, 4.5)["within_range"] is True
    assert compare({"expected_days": None, "low_days": None, "high_days": None}, 2.0)["ratio"] is None


def test_calibration_over_settled_forecasts() -> None:
    def state(change: str, expected: float | None, actual: float | None, within: bool) -> dict[str, Any]:
        forecast: dict[str, Any] = {"status": "ok", "expected_days": expected, "low_days": 1, "high_days": 9}
        if actual is not None:
            forecast["actual"] = {"actual_days": actual, "ratio": actual / expected, "within_range": within}
        return {"change": change, "forecast": forecast}

    states = [
        state("CHG-1", 4.0, 2.0, True),
        state("CHG-2", 4.0, 8.0, False),
        state("CHG-3", 2.0, 2.0, True),
        state("CHG-4", 3.0, None, False),
        {"change": "CHG-5"},
    ]

    report = calibration(states)

    assert (report["count"], report["ratio_median"], report["within_range_share"]) == (3, 1.0, 0.67)
    assert [c["change"] for c in report["changes"]] == ["CHG-1", "CHG-2", "CHG-3", "CHG-4"]
    assert report["changes"][3]["actual_days"] is None


def test_calibration_without_results() -> None:
    assert calibration([]) == {
        "count": 0,
        "ratio_median": None,
        "within_range_share": None,
        "changes": [],
        "without_forecast": [],
    }


def test_calibration_lists_delivered_changes_without_a_usable_forecast() -> None:
    states = [
        {"change": "CHG-1", "forecast": {"status": "failed", "error": "brak historii"}, "flow": {"actual_days": 2.5}},
        {"change": "CHG-2", "flow": {"actual_days": 4.0}},
        {"change": "CHG-3", "forecast": {"status": "ok", "expected_days": 2.0}, "flow": {"actual_days": 3.0}},
        {"change": "CHG-4", "forecast": {"status": "failed"}},
    ]

    report = calibration(states)

    assert report["without_forecast"] == [
        {"change": "CHG-1", "actual_days": 2.5, "forecast": "failed"},
        {"change": "CHG-2", "actual_days": 4.0, "forecast": None},
    ]
    assert report["count"] == 0, "bez prognozy nie ma czego kalibrować"


# --- odczyt z ShipScope ---


def test_read_flow_asks_for_the_range_with_the_token() -> None:
    shipscope = FakeShipScope({"/flow": (200, flow([(2, 4.0)]))})

    value, error = read_flow(CONFIG, date(2026, 5, 1), date(2026, 10, 27), get=shipscope)

    assert error is None and value is not None and len(value["changes"]) == 1
    url, headers = shipscope.calls[0]
    assert url == "https://shipscope.example.com/api/service/v1/flow?from=2026-05-01&to=2026-10-27"
    assert headers["authorization"] == f"Bearer {TOKEN}"


@pytest.mark.parametrize(
    ("routes", "match"),
    [
        ({"/flow": (404, {})}, "404"),
        ({"/flow": (200, {"changes": "x", "items": []})}, "kształcie"),
    ],
    ids=["404", "zly-ksztalt"],
)
def test_read_flow_errors(routes: dict[str, tuple[int, Any]], match: str) -> None:
    value, error = read_flow(CONFIG, date(2026, 5, 1), date(2026, 10, 27), get=FakeShipScope(routes))

    assert value is None and error is not None and match in error and TOKEN not in error


def test_read_tasks_counts_the_changes_slices() -> None:
    body = {"changes": [{"key": "CHG-11", "tasks": [{"key": "TSK-1"}]}, {"key": "CHG-12", "tasks": [{}, {}, {}]}]}
    shipscope = FakeShipScope({"/changes": (200, body)})

    assert read_tasks(CONFIG, "CHG-12", get=shipscope) == (3, None)
    assert shipscope.calls[0][0] == "https://shipscope.example.com/api/service/v1/changes"


@pytest.mark.parametrize(
    ("body", "match"),
    [
        ({"changes": [{"key": "CHG-11", "tasks": []}]}, "nie zna"),
        ({"changes": [{"key": "CHG-12", "tasks": []}]}, "nie ma cięć"),
        ({"changes": "x"}, "kształcie"),
    ],
    ids=["brak-zmiany", "bez-ciec", "zly-ksztalt"],
)
def test_read_tasks_errors(body: dict[str, Any], match: str) -> None:
    count, error = read_tasks(CONFIG, "CHG-12", get=FakeShipScope({"/changes": (200, body)}))

    assert count is None and error is not None and match in error


def test_read_without_config_is_an_error() -> None:
    assert (
        read_tasks(ShipScopeConfig(url=None), "CHG-12")[1]
        == "Brak PDI_SHIPSCOPE_URL — pdi nie czyta danych z ShipScope."
    )


# --- skrzynka: prognoza przy baseline, wynik po dostarczeniu ---

SHIPSCOPE = ShipScopeConfig(url="https://shipscope.example.com", token=TOKEN)
HISTORY = flow([(2, 4.0), (4, 4.0), (3, 6.0), (1, 3.0), (2, 1.0)])
DELIVERED = {**HISTORY, "changes": [*HISTORY["changes"], {"key": "CHG-12", "tasks": 3, "flowDays": 7.5}]}
CHANGES = {"changes": [{"key": "CHG-12", "tasks": [{"key": "TSK-1"}, {"key": "TSK-2"}, {"key": "TSK-3"}]}]}


def approve(inbox: Any, make_draft: Any) -> dict[str, Any]:
    from tests.test_inbox import gate_event

    inbox.receive(gate_event(gate="approve-for-implementation", source="ci_for_sdlc"))
    return inbox.decide("evt-gate-1", make_draft(statement="CHG-12 do implementacji."), outcome="approved")


def test_approval_for_implementation_makes_a_forecast(registry: Any, make_draft: Any) -> None:
    from pdi.inbox import Inbox

    shipscope = FakeShipScope({"/changes": (200, CHANGES), "/flow": (200, HISTORY)})
    inbox = Inbox(registry, shipscope=SHIPSCOPE, shipscope_get=shipscope)

    result = approve(inbox, make_draft)

    f = result["change"]["forecast"]
    assert (f["status"], f["tasks"], f["expected_days"], f["low_days"], f["high_days"]) == ("ok", 3, 6.0, 3.0, 6.0)
    assert f["made_at"] == "2026-10-23T09:30:00Z"
    assert "from=2026-04-27&to=2026-10-23" in shipscope.calls[-1][0]  # 180 dni wstecz
    assert inbox.changes.get("CHG-12")["history"][-1]["what"] == "forecast.made"


def test_failed_forecast_does_not_block_the_decision(registry: Any, make_draft: Any) -> None:
    from pdi.inbox import Inbox

    inbox = Inbox(registry, shipscope=SHIPSCOPE, shipscope_get=FakeShipScope({"/changes": (200, {"changes": []})}))

    result = approve(inbox, make_draft)

    assert result["decision"]["id"] == "DEC-0001"
    f = result["change"]["forecast"]
    assert f["status"] == "failed" and "nie zna jeszcze CHG-12" in f["error"]


def test_no_forecast_without_shipscope(registry: Any, make_draft: Any) -> None:
    from pdi.inbox import Inbox

    assert "forecast" not in approve(Inbox(registry), make_draft)["change"]


def test_release_settles_the_forecast_once_the_change_is_delivered(registry: Any, make_draft: Any) -> None:
    from pdi.inbox import Inbox
    from tests.test_inbox import released_event

    routes: dict[str, tuple[int, Any]] = {"/changes": (200, CHANGES), "/flow": (200, HISTORY)}
    inbox = Inbox(registry, shipscope=SHIPSCOPE, shipscope_get=FakeShipScope(routes))
    approve(inbox, make_draft)

    inbox.receive(released_event())  # R1 — zmiana jeszcze niedostarczona
    assert "actual" not in inbox.changes.get("CHG-12")["forecast"]

    routes["/flow"] = (200, DELIVERED)
    inbox.receive(released_event("evt-rel-2", release="R2"))

    actual = inbox.changes.get("CHG-12")["forecast"]["actual"]
    assert actual == {"actual_days": 7.5, "ratio": 1.25, "within_range": False}


def test_daily_run_settles_and_retries_failed_forecasts(registry: Any, make_draft: Any) -> None:
    from pdi.inbox import Inbox

    routes: dict[str, tuple[int, Any]] = {"/changes": (500, {}), "/flow": (200, HISTORY)}
    inbox = Inbox(registry, shipscope=SHIPSCOPE, shipscope_get=FakeShipScope(routes))
    approve(inbox, make_draft)
    assert inbox.changes.get("CHG-12")["forecast"]["status"] == "failed"

    routes["/changes"] = (200, CHANGES)
    assert inbox.settle_forecasts() == [{"change": "CHG-12", "forecast": "ok", "actual": None}]

    routes["/flow"] = (200, DELIVERED)
    settled = inbox.settle_forecasts(today=date(2026, 10, 30))
    assert settled[0]["actual"] == {"actual_days": 7.5, "ratio": 1.25, "within_range": False}
    assert inbox.settle_forecasts() == []  # z wynikiem nie ma już czego liczyć


def test_failed_forecast_is_not_retried_after_a_release(registry: Any, make_draft: Any) -> None:
    from pdi.inbox import Inbox
    from tests.test_inbox import released_event

    routes: dict[str, tuple[int, Any]] = {"/changes": (500, {}), "/flow": (200, HISTORY)}
    inbox = Inbox(registry, shipscope=SHIPSCOPE, shipscope_get=FakeShipScope(routes))
    approve(inbox, make_draft)
    inbox.receive(released_event())
    routes["/changes"] = (200, CHANGES)

    assert inbox.settle_forecasts() == []
    assert inbox.changes.get("CHG-12")["forecast"]["status"] == "failed"


def test_forecast_on_request_replaces_the_previous_one(registry: Any, make_draft: Any) -> None:
    from pdi.inbox import Inbox

    routes: dict[str, tuple[int, Any]] = {"/changes": (200, CHANGES), "/flow": (200, HISTORY)}
    inbox = Inbox(registry, shipscope=SHIPSCOPE, shipscope_get=FakeShipScope(routes))
    approve(inbox, make_draft)
    routes["/changes"] = (200, {"changes": [{"key": "CHG-12", "tasks": [{}, {}]}]})

    f = inbox.make_forecast("CHG-12")

    assert (f["tasks"], f["expected_days"]) == (2, 4.0)
    assert inbox.changes.get("CHG-12")["forecast"] == f


def test_failed_forecast_of_a_closed_change_is_not_retried(registry: Any, make_draft: Any) -> None:
    from pdi.inbox import Inbox

    routes: dict[str, tuple[int, Any]] = {"/changes": (500, {}), "/flow": (200, HISTORY)}
    inbox = Inbox(registry, shipscope=SHIPSCOPE, shipscope_get=FakeShipScope(routes))
    approve(inbox, make_draft)
    state = inbox.changes.get("CHG-12")
    inbox.changes.save({**state, "status": "rejected"})
    routes["/changes"] = (200, CHANGES)

    assert inbox.settle_forecasts() == []


# --- rzeczywisty czas przepływu także bez prognozy (PRB-22) ---


def test_delivered_change_with_a_failed_forecast_keeps_its_flow_time(registry: Any, make_draft: Any) -> None:
    from pdi.inbox import Inbox
    from tests.test_inbox import released_event

    routes: dict[str, tuple[int, Any]] = {"/changes": (500, {}), "/flow": (200, HISTORY)}
    inbox = Inbox(registry, shipscope=SHIPSCOPE, shipscope_get=FakeShipScope(routes))
    approve(inbox, make_draft)
    inbox.receive(released_event())
    routes["/flow"] = (200, DELIVERED)

    settled = inbox.settle_forecasts(today=date(2026, 10, 30))

    state = inbox.changes.get("CHG-12")
    assert state["forecast"]["status"] == "failed" and "actual" not in state["forecast"]
    assert state["flow"] == {"actual_days": 7.5, "measured_at": "2026-10-23T09:30:00Z"}
    assert state["history"][-1] == {"at": "2026-10-23T09:30:00Z", "what": "flow.measured", "actual_days": 7.5}
    assert settled == [{"change": "CHG-12", "forecast": "failed", "actual": None, "flow_days": 7.5}]
    assert inbox.settle_forecasts(today=date(2026, 10, 30)) == []  # zmierzone raz


def test_delivered_change_without_any_forecast_keeps_its_flow_time(registry: Any, make_draft: Any) -> None:
    from pdi.inbox import Inbox
    from tests.test_inbox import released_event

    approve(Inbox(registry), make_draft)  # bez ShipScope przy baseline: prognozy nie ma
    inbox = Inbox(registry, shipscope=SHIPSCOPE, shipscope_get=FakeShipScope({"/flow": (200, DELIVERED)}))
    inbox.receive(released_event())

    state = inbox.changes.get("CHG-12")
    assert "forecast" not in state
    assert state["flow"]["actual_days"] == 7.5
    assert calibration([state])["without_forecast"] == [{"change": "CHG-12", "actual_days": 7.5, "forecast": None}]


def test_undelivered_change_without_forecast_is_not_read(registry: Any, make_draft: Any) -> None:
    from pdi.inbox import Inbox

    approve(Inbox(registry), make_draft)
    shipscope = FakeShipScope({"/flow": (200, DELIVERED)})

    assert Inbox(registry, shipscope=SHIPSCOPE, shipscope_get=shipscope).settle_forecasts() == []
    assert shipscope.calls == [], "bez wydania nie ma czego mierzyć — bez zapytań do ShipScope"
