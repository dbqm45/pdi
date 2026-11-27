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


# --- wyniki pokoju z powrotem (docs/plan-wyniki-sprintdecka.md) ---


def results_link(payload: dict[str, Any], secret: str = SECRET) -> str:
    d = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    s = hmac.new(secret.encode(), d.encode(), hashlib.sha256).hexdigest()
    return f"/discuss/results?d={d}&s={s}"


def results(**extra: Any) -> dict[str, Any]:
    room = {"title": "Discuss with team — 2026-11-27", "url": "http://127.0.0.1:3000/r/NhkrbG3RxFqo", "deck": "Risk"}
    first = {
        "ref": "evt-1",
        "title": "Prośba o bramkę B2",
        "status": "estimated",
        "final": "High",
        "rounds": 2,
        "votes": {"High": 3},
        "consensus": "Full consensus",
        "notes": ["Przegląd bezpieczeństwa przed B2 <b>"],
    }
    unknown = {
        "ref": "evt-9",
        "title": "Nieznana",
        "status": "pending",
        "final": None,
        "rounds": 0,
        "votes": {},
        "consensus": None,
        "notes": [],
    }
    return {"v": 1, "exp": int(datetime.now(UTC).timestamp()) + 600, "room": room, "items": [first, unknown],
            **extra}  # fmt: skip


def test_sd04_the_room_link_names_each_pdi_item_and_results_are_checked_like_the_link() -> None:
    payload, _, _ = decode(sprintdeck.room_link([entry(1)], CFG, now=NOW))
    assert payload["items"][0]["ref"] == "evt-1"
    good = results()
    d = base64.urlsafe_b64encode(json.dumps(good).encode()).decode().rstrip("=")
    s = hmac.new(SECRET.encode(), d.encode(), hashlib.sha256).hexdigest()
    now = datetime.now(UTC)
    assert sprintdeck.verify_results(CFG, d, s, now=now)["room"]["deck"] == "Risk"
    for bad_d, bad_s, reason in ((d, "0" * 64, "signature"), ("%%", s, "signature")):
        with pytest.raises(sprintdeck.ResultsRefused, match=reason):
            sprintdeck.verify_results(CFG, bad_d, bad_s, now=now)
    old = base64.urlsafe_b64encode(json.dumps(results(exp=1)).encode()).decode().rstrip("=")
    with pytest.raises(sprintdeck.ResultsRefused, match="expired"):
        sprintdeck.verify_results(
            CFG, old, hmac.new(SECRET.encode(), old.encode(), hashlib.sha256).hexdigest(), now=now
        )
    with pytest.raises(sprintdeck.ResultsRefused, match="off"):
        sprintdeck.verify_results(sprintdeck.SprintdeckConfig(url=None, secret=None), d, s, now=now)


def test_sd05_results_are_shown_first_then_attached_to_the_agenda_and_shown_on_the_card(
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
        link = results_link(results())
        status, _, page, _ = app.request("GET", link, cookie=s["ola"])
        assert status == 200
        assert "Results from sprintdeck" in page and "Prośba o bramkę B2" in page
        assert "Not on the agenda: Nieznana" in page
        assert not (registry.root / "sprintdeck-results").exists(), "nothing is stored before the decider confirms"
        _, _, page, _ = app.request("GET", link, cookie=s["viewer"])
        assert "Attach to the agenda" not in page, "a viewer sees, but does not attach"
        d, sig = link.split("d=")[1].split("&s=")
        assert app.request("POST", "/discuss/results", cookie=s["viewer"], form={"d": d, "s": sig})[0] == 403
        assert app.request("POST", "/discuss/results", cookie=s["ola"], form={"d": d, "s": "0" * 64})[0] == 400
        assert app.request("POST", "/discuss/results", cookie=s["ola"], form={"d": d, "s": sig})[0] == 303
        stored = json.loads((registry.root / "sprintdeck-results" / "evt-1.json").read_text(encoding="utf-8"))
        assert stored["final"] == "High" and stored["room"]["url"].endswith("/r/NhkrbG3RxFqo")
        assert not (registry.root / "sprintdeck-results" / "evt-9.json").exists()
        _, _, page, _ = app.request("GET", "/discuss", cookie=s["ola"])
        assert "From the sprintdeck room" in page
        assert "Final: High" in page and "High × 3" in page and "Full consensus" in page
        assert "Przegląd bezpieczeństwa przed B2 &lt;b&gt;" in page
    finally:
        app.close()


def test_sd06_the_agent_sees_the_room_results_on_the_agenda(registry: Registry) -> None:
    import asyncio

    from pdi import consult
    from pdi.mcp_server import build_server
    from tests.test_discuss import discuss

    write_gate(registry)
    discuss(consult.Consultations(registry.root, now=registry.now), "evt-1")
    sprintdeck.ResultsStore(registry.root).save(results(), now=NOW, open_items={"evt-1"})
    server = build_server(lambda: registry)
    out = asyncio.run(server.call_tool("discussion_agenda", {})).structured_content
    assert out["items"][0]["room"]["final"] == "High"
