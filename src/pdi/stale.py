"""DV6: zgłoszenia porzucone (docs/plan-dv6-zgloszenia-porzucone.md).

Zgłoszenie odłożone (`parked`) dłużej niż `PARKED_DAYS` od decyzji, która je odłożyła, i zgłoszenie z pytaniami bez
odpowiedzi (`clarifying`) dłużej niż `CLARIFYING_DAYS` od ostatnich pytań. Decyduje człowiek
(`ProblemStore.review_stale`: zamknąć albo zwalidować ponownie); pdi samo niczego nie zmienia. Progi jak terminy OM1
— w kodzie, dopóki operating model (N1) nie da im źródła.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pdi.problems import ProblemStore
    from pdi.registry import Registry

PARKED_DAYS = 90
CLARIFYING_DAYS = 30
REVIEW_TYPE = "problem.stale_review"
OUTCOMES = ("close", "revalidate")


def _at(text: Any) -> datetime | None:
    raw = str(text or "")
    if not raw:
        return None
    try:
        if len(raw) == 10:
            return datetime.fromisoformat(raw).replace(tzinfo=UTC)
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def _since(store: ProblemStore, registry: Registry, item: dict[str, Any]) -> datetime | None:
    """Od kiedy zgłoszenie stoi: odłożone — od decyzji triażu; z pytaniami — od ostatnich pytań."""
    if item["status"] == "parked" and item.get("triage_decision"):
        try:
            d = registry.get(str(item["triage_decision"]))
        except LookupError:
            return _at(item.get("reported_at"))
        return _at(d.get("recorded_at")) or _at(d.get("decided_at"))
    if item["status"] == "clarifying":
        return _at(store.last_questions_at(str(item["id"]))) or _at(item.get("reported_at"))
    return None


def report(store: ProblemStore, registry: Registry, *, now: datetime) -> list[dict[str, Any]]:
    """Porzucone zgłoszenia, od najstarszego numeru: stan, od kiedy, ile dni, powód i rekomendacja."""
    rows = []
    for item in store.all():
        status = item.get("status")
        limit = PARKED_DAYS if status == "parked" else CLARIFYING_DAYS if status == "clarifying" else None
        since = _since(store, registry, item) if limit else None
        if limit is None or since is None:
            continue
        days = (now - since).days
        if days <= limit:
            continue
        if status == "parked":
            reason = (
                f"odłożone {days} dni (próg {PARKED_DAYS}); warunek powrotu „{item.get('return_when')}” się nie spełnił"
            )
            recommendation = "revalidate"
        else:
            reason = f"pytania bez odpowiedzi od {days} dni (próg {CLARIFYING_DAYS})"
            recommendation = "close"
        rows.append(
            {
                "problem": item["id"],
                "title": item.get("title"),
                "status": status,
                "since": since.strftime("%Y-%m-%d"),
                "days": days,
                "reason": reason,
                "recommendation": recommendation,
            }
        )
    return rows
