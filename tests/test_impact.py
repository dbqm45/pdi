from datetime import date
from typing import Any

import pytest

from pdi.impact import (
    ShipScopeConfig,
    collect,
    draft_verdict,
    due_date,
    intent_decision,
    parse_horizon,
)
from pdi.registry import Registry


@pytest.mark.parametrize(
    ("text", "days"),
    [
        ("30 dni", 30),
        ("30d", 30),
        ("30 days", 30),
        ("P30D", 30),
        ("4 tygodnie", 28),
        ("2 weeks", 14),
        ("P2W", 14),
        ("2 miesiące", 60),
        ("1 month", 30),
        ("1 kwartał", 90),
    ],
)
def test_horizon_forms(text: str, days: int) -> None:
    assert parse_horizon(text) == days


@pytest.mark.parametrize("text", ["", "do końca roku", "0 dni", "jak najszybciej"])
def test_unreadable_horizon_is_none(text: str) -> None:
    assert parse_horizon(text) is None


def intent(**overrides: Any) -> dict[str, Any]:
    return {
        "id": "DEC-0001",
        "kind": "intent",
        "status": "recorded",
        "recorded_at": "2026-09-01T10:00:00Z",
        "links": {"chg": "CHG-12"},
        "success_metric": {"metric": "rollbacks", "target": "<= 1", "horizon": "14 dni"},
        **overrides,
    }


def test_due_date_prefers_review_by_then_horizon_then_default() -> None:
    released = "2026-10-23T09:04:00Z"

    assert due_date(released, intent(review_by="2026-12-01")) == ("2026-12-01", "review_by")
    assert due_date(released, intent()) == ("2026-11-06", "horizon")
    no_horizon = intent(success_metric={"metric": "rollbacks", "target": "<= 1"})
    assert due_date(released, no_horizon) == ("2026-11-22", "default")
    assert due_date(released, None) == ("2026-11-22", "default")


def test_review_by_before_release_falls_back_to_horizon() -> None:
    assert due_date("2026-10-23T09:04:00Z", intent(review_by="2026-10-01")) == ("2026-11-06", "horizon")


def test_intent_decision_is_newest_recorded_with_metric_intent_first(registry: Registry, make_draft: Any) -> None:
    metric = {"metric": "rollbacks", "target": "<= 1"}
    registry.record(make_draft(statement="Produkt.", kind="product", links={"chg": "CHG-12"}, success_metric=metric))
    first = registry.record(
        make_draft(statement="Intencja.", kind="intent", links={"chg": "CHG-12"}, success_metric=metric)
    )
    registry.record(make_draft(statement="Bez metryki.", kind="intent", links={"chg": "CHG-12"}))
    registry.record(make_draft(statement="Inna zmiana.", kind="intent", links={"chg": "CHG-99"}, success_metric=metric))

    assert intent_decision(registry, "CHG-12")["id"] == first["id"]  # type: ignore[index]
    newer = registry.supersede(
        first["id"], make_draft(statement="Intencja 2.", kind="intent", links={"chg": "CHG-12"}, success_metric=metric)
    )
    assert intent_decision(registry, "CHG-12")["id"] == newer["id"]  # type: ignore[index]
    assert intent_decision(registry, "CHG-77") is None


def series(**columns: list[Any]) -> dict[str, Any]:
    n = len(next(iter(columns.values())))
    days = []
    for i in range(n):
        day: dict[str, Any] = {
            "date": f"2026-10-{23 + i}",
            "deployments": 0,
            "failedDeployments": 0,
            "rollbacks": 0,
            "leadTimeDaysMedian": None,
            "leadTimeCount": 0,
        }
        day.update({k: v[i] for k, v in columns.items()})
        days.append(day)
    return {"item": {"key": "CHG-12", "releasedOnProd": True}, "metrics": {"days": days}, "errors": []}


@pytest.mark.parametrize(
    ("target", "rollbacks", "verdict"),
    [("<= 1", [0, 1, 0], "met"), ("<= 1", [1, 1, 0], "not_met"), ("< 2", [1, 0], "met"), ("≥ 1", [0, 0], "not_met")],
)
def test_counted_metric_is_summed_over_window(target: str, rollbacks: list[int], verdict: str) -> None:
    result = draft_verdict({"metric": "rollbacks", "target": target}, series(rollbacks=rollbacks))

    assert result["verdict"] == verdict
    assert result["observed"] == sum(rollbacks)


def test_lead_time_is_median_of_daily_medians() -> None:
    data = series(leadTimeDaysMedian=[2.0, None, 6.0, 4.0], leadTimeCount=[1, 0, 1, 1])

    result = draft_verdict({"metric": "Lead time Done → PROD (lead_time_days_median)", "target": "<= 5"}, data)

    assert (result["verdict"], result["observed"]) == ("met", 4.0)


@pytest.mark.parametrize(
    ("metric", "data", "reason"),
    [
        ({"metric": "konwersja koszyka", "target": ">= 3%"}, series(rollbacks=[0]), "ShipScope"),
        ({"metric": "rollbacks", "target": "mało"}, series(rollbacks=[0]), "porównani"),
        (None, series(rollbacks=[0]), "intencji"),
        ({"metric": "rollbacks", "target": "<= 1"}, {"item": None, "metrics": None, "errors": ["401"]}, "danych"),
        ({"metric": "lead_time_days_median", "target": "<= 5"}, series(leadTimeDaysMedian=[None]), "danych"),
    ],
)
def test_otherwise_verdict_is_unknown_with_reason(metric: Any, data: dict[str, Any], reason: str) -> None:
    result = draft_verdict(metric, data)

    assert result["verdict"] == "unknown"
    assert reason in result["reason"]


def test_not_released_on_prod_is_noted() -> None:
    data = series(rollbacks=[0])
    data["item"]["releasedOnProd"] = False

    result = draft_verdict({"metric": "rollbacks", "target": "<= 1"}, data)

    assert result["verdict"] == "met"
    assert "PROD" in result["reason"]


class FakeShipScope:
    def __init__(self, status: int = 200) -> None:
        self.status = status
        self.calls: list[tuple[str, dict[str, str]]] = []

    def __call__(self, url: str, headers: dict[str, str]) -> tuple[int, bytes]:
        import json

        self.calls.append((url, headers))
        if self.status != 200:
            return self.status, b'{"error":"nope"}'
        if "/items/" in url:
            return 200, json.dumps({"key": "CHG-12", "releasedOnProd": True}).encode()
        return 200, json.dumps({"days": [{"date": "2026-10-23", "rollbacks": 0}]}).encode()


TOKEN = "shps_test"  # noqa: S105 — token testowy


def test_collect_reads_item_and_metrics_from_release_day() -> None:
    shipscope = FakeShipScope()
    config = ShipScopeConfig(url="https://shipscope.example.com/", token=TOKEN)

    data = collect(config, "CHG-12", "2026-10-23T09:04:00Z", date(2026, 11, 22), get=shipscope)

    assert data["errors"] == []
    assert data["item"]["key"] == "CHG-12"
    assert data["metrics"]["days"][0]["rollbacks"] == 0
    urls = [u for u, _ in shipscope.calls]
    assert urls == [
        "https://shipscope.example.com/api/service/v1/items/CHG-12",
        "https://shipscope.example.com/api/service/v1/metrics?from=2026-10-23&to=2026-11-22&format=json",
    ]
    assert all(h["authorization"] == f"Bearer {TOKEN}" for _, h in shipscope.calls)


def test_collect_window_is_at_most_400_days() -> None:
    shipscope = FakeShipScope()
    config = ShipScopeConfig(url="https://shipscope.example.com", token=TOKEN)

    collect(config, "CHG-12", "2024-01-01T00:00:00Z", date(2026, 11, 22), get=shipscope)

    assert "from=2025-10-19&to=2026-11-22" in shipscope.calls[1][0]


def test_collect_errors_never_carry_the_token() -> None:
    config = ShipScopeConfig(url="https://shipscope.example.com", token=TOKEN)

    data = collect(config, "CHG-12", "2026-10-23T09:04:00Z", date(2026, 11, 22), get=FakeShipScope(401))

    assert data["item"] is None and data["metrics"] is None
    assert len(data["errors"]) == 2 and "401" in data["errors"][0]
    assert TOKEN not in repr(data) and TOKEN not in repr(config)


@pytest.mark.parametrize(
    ("config", "match"),
    [
        (ShipScopeConfig(url=None), "PDI_SHIPSCOPE_URL"),
        (ShipScopeConfig(url="https://s.example.com", token=None), "PDI_SHIPSCOPE_TOKEN"),
        (ShipScopeConfig(url="http://s.example.com", token=TOKEN), "https"),
    ],
)
def test_collect_without_usable_config_reads_nothing(config: ShipScopeConfig, match: str) -> None:
    shipscope = FakeShipScope()

    data = collect(config, "CHG-12", "2026-10-23T09:04:00Z", date(2026, 11, 22), get=shipscope)

    assert shipscope.calls == []
    assert match in data["errors"][0]
