"""Pokój sprintdecka z agendy „Discuss with team” (docs/plan-pokoj-sprintdeck.md): podpisany link z listą spraw."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest

from pdi import sprintdeck
from tests.test_discuss import Console, FakeIssuer, Registry, answer, ask, people, write_gate

SECRET = "pdi-sprintdeck-test"  # noqa: S105 — sekret tylko w teście
CFG = sprintdeck.SprintdeckConfig(url="http://127.0.0.1:3000", secret=SECRET)
NOW = datetime(2026, 11, 26, 9, 0, tzinfo=UTC)


def entry(n: int, **extra: Any) -> dict[str, Any]:
    return {"item_id": f"evt-{n}", "kind": "gate", "change": f"CHG-{n}", "gate": "B2",
            "summary": f"Prośba o bramkę B2 dla CHG-{n}",
            "reasons": ["the run is paused", f"CHG-{n} waits at B2"], "options": ["approved", "rejected"],
            "answers": [{"name": "Adm Test", "option": "talk_live", "reason": "Omówmy na żywo."},
                        {"name": "Trzecia Osoba", "option": None, "reason": None}], **extra}  # fmt: skip


def decode(link: str) -> tuple[dict[str, Any], str, str]:
    parts = urlsplit(link)
    q = parse_qs(parts.fragment)
    d, s = q["d"][0], q["s"][0]
    return json.loads(base64.urlsafe_b64decode(d + "=" * (-len(d) % 4))), d, s


def test_sd01_the_link_carries_the_agenda_in_the_fragment_signed_and_valid_for_less_than_an_hour() -> None:
    link = sprintdeck.room_link([entry(1), entry(2)], CFG, now=NOW)
    assert link.startswith("http://127.0.0.1:3000/from-pdi#d=")
    payload, d, s = decode(link)
    assert s == hmac.new(SECRET.encode(), d.encode(), hashlib.sha256).hexdigest()
    assert payload["v"] == 1
    assert payload["title"] == "Discuss with team — 2026-11-26"
    assert 0 < payload["exp"] - int(NOW.timestamp()) < 3600
    first = payload["items"][0]
    assert first["title"] == "Prośba o bramkę B2 dla CHG-1"
    assert "CHG-1 · B2" in first["description"]
    assert "Why now: the run is paused; CHG-1 waits at B2" in first["description"]
    assert "Adm Test: talk_live — Omówmy na żywo." in first["description"]
    assert "Trzecia Osoba: no answer" in first["description"]


def test_sd02_limits_match_sprintdeck_and_the_link_is_off_without_settings() -> None:
    many = [entry(n, summary="x" * 500) for n in range(40)]
    payload, _, _ = decode(sprintdeck.room_link(many, CFG, now=NOW))
    assert len(payload["items"]) == 30
    assert len(payload["items"][0]["title"]) == 200
    assert all(len(i["description"]) <= 2000 for i in payload["items"])
    assert sprintdeck.room_link([], CFG, now=NOW) is None
    assert sprintdeck.room_link([entry(1)], sprintdeck.SprintdeckConfig(url=None, secret=SECRET), now=NOW) is None
    assert (
        sprintdeck.SprintdeckConfig.from_env(
            {"PDI_SPRINTDECK_URL": "http://127.0.0.1:3000/", "PDI_SPRINTDECK_SECRET": "s"}
        ).url
        == "http://127.0.0.1:3000"
    )
    with pytest.raises(ValueError, match="https"):
        sprintdeck.SprintdeckConfig.from_env(
            {"PDI_SPRINTDECK_URL": "http://sprintdeck.example.com", "PDI_SPRINTDECK_SECRET": "s"}
        )


def test_sd03_the_agenda_page_offers_the_room_to_deciders_only(
    registry: Registry, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PDI_SPRINTDECK_URL", "http://127.0.0.1:3000")
    monkeypatch.setenv("PDI_SPRINTDECK_SECRET", SECRET)
    write_gate(registry)
    app = Console(registry, FakeIssuer(), monkeypatch)
    try:
        s = people(app)
        ask(app, s["ola"], ["s-adm", "s-3"])
        answer(app, s["adm"], "talk_live", "Omówmy na żywo.")
        answer(app, s["viewer"], "rejected", "Za duże ryzyko.")
        _, _, page, _ = app.request("GET", "/discuss", cookie=s["ola"])
        assert "Open a room in sprintdeck" in page
        assert 'href="http://127.0.0.1:3000/from-pdi#d=' in page
        _, _, page, _ = app.request("GET", "/discuss", cookie=s["viewer"])
        assert "Open a room in sprintdeck" not in page
    finally:
        app.close()


@pytest.fixture
def registry(tmp_path: Any) -> Registry:
    r = Registry(tmp_path / "registry")
    r.root.mkdir(parents=True, exist_ok=True)
    return r
