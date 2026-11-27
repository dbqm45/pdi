"""Pomocnik testów: decyzja przez szkic zatwierdzony w konsoli (docs/plan-zapis-decyzji-po-zatwierdzeniu.md)."""

from __future__ import annotations

from typing import Any

from pdi.drafts import DecisionDrafts
from pdi.registry import Registry


async def record_via_draft(server: Any, registry: Registry, args: dict[str, Any], *, by: str = "Ola") -> Any:
    """`present_decision_draft` → zatwierdzenie (jak przycisk w konsoli) → `record_decision`."""
    shown = await server.call_tool("present_decision_draft", args)
    assert shown.is_error is False
    d = shown.structured_content
    DecisionDrafts(registry).approve(d["draft_id"], d["sha256"], by={"name": by})
    saved = await server.call_tool("record_decision", {"draft_id": d["draft_id"], "sha256": d["sha256"]})
    assert saved.is_error is False
    return saved.structured_content
