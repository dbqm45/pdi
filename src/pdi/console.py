"""Konsola pdi w przeglądarce na Macu — proces `pdi-console` obok `pdi-receiver` (Z3-lokalnie, A7, DZ14, DZ18).

Serwis startowany przez `sdlc up` (zatrzymywany `sdlc down`, pokazywany w `sdlc status`, otwierany `sdlc open`),
nasłuchuje **tylko na 127.0.0.1**, z tokenem sesji w URL (jak formularz zgłoszeń: `src/pdi/receiver.py` +
`src/pdi/form.py`). Pokazuje tablicę w trzech pasach (Z7a), ślad zmiany z panelem „Pliki” i bocznym postępem
na żywo (DZ18), skrzynkę z przyciskami decyzji, read-only rejestr/autonomię i tablicę „Now” (DI Team T3:
przebiegi agentów z `agent-runs/` w kolumnach In progress / Awaiting decision / In review / Done,
filtr „Started by”). Nic nie pisze do klonu produktu;
pliki pokazuje tylko z białej listy, bez symlinków i bez treści, która wygląda na sekret.

Bezpieczeństwo:

- Nasłuch na `127.0.0.1` z hardcode; port z `PDI_CONSOLE_PORT` (domyślnie 8788).
- Token w URL (`?t=<token>`) i w treści POST; brak albo niezgodność → 404 (jak w formularzu, nie zdradzamy istnienia).
- Z `PDI_SUITE_ISSUER`/`PDI_SUITE_CLIENT_SECRET`/`PDI_SUITE_ORGANIZATION` (docs/plan-konsola-tozsamosc.md) zamiast
  tokenu logowanie przez tożsamość suity (`suite_login.py`): `/login` → wystawca (PKCE) → `/callback`, sesja w
  ciasteczku HttpOnly, SameSite=Lax; bez sesji każda strona przekierowuje na `/login`, a token w adresie nic nie
  otwiera. POST wymaga sesji z rolą `editor`/`admin` (DI Decision) i nagłówka Origin albo Referer z tej konsoli;
  `decided_by` = nazwa osoby z tokenu. `/logout` kończy sesję.
- CSP bez `script-src 'unsafe-inline'`; jedyny JS to statyczny plik z nonce.
- POST tylko `application/x-www-form-urlencoded`; `Origin` i `Referer` ograniczone do `http://127.0.0.1:<port>`.
- Każde pole treści (tekst decyzji, pytania, logi, ścieżki, nazwy gałęzi) idzie przez `html.escape`; linie postępu
  wyświetlane w `<pre>` po escapie.
- Pliki artefaktów: tylko biała lista nazw pod `docs/project/changes/<CHG>/`; bez symlinków; rozmiar ≤ 256 KiB;
  binarne i „sekretowe” (`.env`, nazwa z KEY/TOKEN/SECRET) odrzucone z 403.
- Decyzje przyciskami idą dokładnie tą samą ścieżką co `decide_inbox_item` (ten sam kod `Inbox.decide`):
  sprawdzenie PR-a dla `approved` (PRB-2), odmowa dla zmienionej pod ręką pozycji (409), `source.kind: console`.

Źródła 2026-11-06: code.claude.com/docs/en/cli-reference, code.claude.com/docs/en/headless,
code.claude.com/docs/en/agent-sdk/typescript. Plan: `docs/plan-z3-lokalnie.md`.
"""

from __future__ import annotations

import hashlib
import hmac
import html
import json
import os
import secrets
import socketserver
import subprocess
import sys
import time
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from http.cookies import CookieError, SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, cast
from urllib.parse import parse_qs, quote, urlsplit

from pdi import (
    agenda,
    autonomy,
    consult,
    delays,
    dispatch_local,
    escalate,
    pr_state,
    process,
    stale,
    suite_login,
    team_notify,
)
from pdi import trace as trace_mod
from pdi.changes import ChangeStore
from pdi.dispatch import DispatchConfig
from pdi.impact import ShipScopeConfig
from pdi.inbox import Inbox, ItemClosed, ItemNotFound
from pdi.notify import NotifyConfig, ReporterNotifyConfig
from pdi.registry import Decision, InvalidDecision, Registry
from pdi.waiting import ChannelsConfig

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8788
MAX_BODY = 128 * 1024
POLL_SECONDS = 0.5
FILE_SIZE_LIMIT = 256 * 1024
BINARY_PEEK = 8 * 1024
SSE_RETRY_MS = 2000
# Tryb suity (docs/plan-konsola-tozsamosc.md): ciasteczka logowania i sesji; widoki dostają w linkach `?t=` tę stałą,
# niesekretną wartość, bo o dostępie decyduje sesja, nie adres.
LOGIN_COOKIE = "pdi_login"
SESSION_COOKIE = "pdi_session"
SUITE_LINK_TOKEN = "s"  # noqa: S105 — wartość w linkach, nie sekret
# Mapowanie faza/bramka → pas (Z7a; makieta design/konsola/v2-klikalna/*).
LANES: dict[str, int] = {
    "intake": 1,
    "intent": 1,
    "B1": 1,
    "requirements": 1,
    "B2": 1,
    "architecture": 1,
    "B3": 1,
    "design": 1,
    "design-review": 1,
    "approve-for-implementation": 1,
    "delivery": 1,
    "B4": 2,
    "B5": 2,
    "B6": 3,
    "R1": 3,
    "impact_review": 3,
}
LANE_LABELS = {1: "Zaprojektuj i zbuduj", 2: "Oceń i wydaj", 3: "Wdróż, obserwuj, ulepszaj"}
# Artefakty zmiany pokazywane w panelu „Pliki” (DZ18).
ALLOWED_ARTIFACTS = ("intent.md", "requirements.md", "plan.md", "design.md", "release.yaml")
# Nazwy, które wyglądają na sekret — nigdy nie pokazujemy ich treści.
import re  # noqa: E402

_SECRETISH = re.compile(r"(^|/)(\.env$|.*(KEY|TOKEN|SECRET|PASSWORD|RSA|ED25519).*)", re.IGNORECASE)
_CTRL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")

_STYLE = """
body{margin:0;background:#F4F6F9;color:#15202b;font:16px/1.4 system-ui,"IBM Plex Sans",sans-serif}
a{color:#2846B5;text-decoration:none}
a:hover{text-decoration:underline}
header{display:flex;align-items:baseline;gap:18px;padding:12px 24px;background:#fff;border-bottom:1px solid #DDE3EA}
header .brand{font-weight:600;color:#2846B5;font-family:"IBM Plex Mono",ui-monospace,monospace}
header nav a{margin-right:12px;color:#444}
main{padding:16px 24px;max-width:1240px;margin:0 auto}
h1{margin:0 0 12px;font-size:22px}
h2{margin:20px 0 10px;font-size:17px}
.lanes{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.lanes.now{grid-template-columns:repeat(4,1fr)}
.lane.n2 h3{background:#FFF0D2}
.lane.n3 h3{background:#F3EEF9}
.lane.n4 h3{background:#E6F3EA}
.card .who{font-size:12px;color:#15202b}
.card .fresh{font-size:11px;color:#5B6878}
.filters a{margin-right:10px}
.filters a.on{font-weight:600}
@media (max-width:900px){.lanes,.lanes.now{grid-template-columns:1fr}}
.lane{background:#fff;border-radius:10px;border:1px solid #DDE3EA;overflow:hidden}
.lane h3{margin:0;padding:10px 14px;font-size:14px;color:#15202b;background:#EAF0FB}
.lane.l2 h3{background:#F3EEF9}
.lane.l3 h3{background:#E6F3EA}
.lane ul{list-style:none;margin:0;padding:8px}
.card{padding:8px 10px;border-radius:8px;border:1px solid #E1E5EC;margin:6px 0;background:#fafbfd}
.card .chg{font-family:"IBM Plex Mono",ui-monospace,monospace;font-weight:600}
.card .phase{color:#5B6878;font-size:12px;margin-left:4px}
.card .wait{color:#A1271D;font-size:12px}
.pill{display:inline-block;padding:1px 7px;border-radius:999px;font-size:11px;background:#EEF1F5;color:#444}
.pill.open{background:#FFF0D2;color:#7A4700}
.pill.decided{background:#DDF2E5;color:#17663A}
table{border-collapse:collapse;width:100%}
th,td{padding:6px 10px;border-bottom:1px solid #EDF0F3;text-align:left;vertical-align:top}
th{background:#F7F9FC;font-weight:600}
pre{background:#0b0c0e;color:#eceef1;padding:10px;border-radius:8px;overflow:auto;
  font:12px/1.4 "IBM Plex Mono",ui-monospace,monospace}
form .row{margin:12px 0}
form label{display:block;font-weight:600;margin-bottom:4px}
form textarea,form input[type=text]{width:100%;box-sizing:border-box;font:inherit;padding:8px;
  border:1px solid #BBC0C7;border-radius:6px}
form textarea{min-height:5em}
button{font:inherit;padding:8px 14px;border-radius:6px;border:1px solid #2846B5;
  background:#2846B5;color:#fff;cursor:pointer}
button.alt{background:#fff;color:#2846B5}
button.warn{background:#fff;color:#A1271D;border-color:#A1271D}
.side{position:sticky;top:0;background:#fff;border:1px solid #DDE3EA;border-radius:8px;
  padding:10px 12px;margin-left:16px;min-width:260px}
.grid{display:grid;grid-template-columns:1fr auto;gap:16px;align-items:flex-start}
small{color:#5B6878}
.err{color:#A1271D;font-weight:600}
.ok{color:#17663A}
"""


class Refused(ValueError):
    """Krótka odmowa — status HTTP wybiera caller."""


def _escape(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _sanitize_text(value: Any, limit: int = 2000) -> str:
    """Jedno- lub wielowierszowy tekst do wyświetlenia: usunięte znaki sterujące, obcięte do `limit`."""
    text = "" if value is None else str(value)
    cleaned = _CTRL.sub(" ", text)
    if len(cleaned) > limit:
        cleaned = cleaned[: limit - 1] + "…"
    return cleaned


def _token_ok(token: str, given: str) -> bool:
    return bool(token) and hmac.compare_digest(token.encode(), (given or "").encode())


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _lane_of(phase: str | None, waiting: list[str] | None, kind: str | None = None) -> int:
    """Pas 1/2/3 na podstawie bieżącej fazy, oczekujących bramek i rodzaju pozycji."""
    if kind == "impact_review":
        return 3
    if waiting:
        for gate in waiting:
            if gate in LANES:
                return LANES[gate]
    if phase and phase in LANES:
        return LANES[phase]
    return 1


class Deps:
    """Źródła danych konsoli (łatwe do podstawienia w testach)."""

    def __init__(
        self,
        registry: Registry,
        *,
        checkout: Path | None,
        git: Callable[[list[str], Path], tuple[int, str]] | None = None,
        inbox: Inbox | None = None,
    ) -> None:
        self.registry = registry
        self.inbox = inbox or Inbox(registry)
        # DI Team T4 „Ask team”: konsultacje przy pozycjach skrzynki i osoby, które logowały się przez suitę.
        self.consults = consult.Consultations(registry.root, now=registry.now)
        self.people = consult.People(registry.root, now=registry.now)
        self.agenda = agenda.Order(registry.root)
        self.escalations = escalate.Escalations(registry.root, now=registry.now)  # T7
        self.changes = ChangeStore(registry)
        self.checkout = checkout
        self.git = git or _git_run

    def trace(self, change: str) -> dict[str, Any]:
        """Graf śladu zmiany (bez `live`, żeby konsola nie biła do ShipScope)."""
        return trace_mod.trace(self.registry, change, live=False)


def inbox_from_env(registry: Registry) -> Inbox:
    """Skrzynka z tymi samymi ustawieniami co w serwerze MCP: uruchamianie faz, sprawdzenie PR (PRB-2), powiadomienia.

    Bez tego decyzja przyciskiem zapisywała się, ale nie ruszała następnej fazy tf ani nie sprawdzała merge'a PR.
    """
    config = DispatchConfig.from_env()
    return Inbox(
        registry,
        dispatch=config,
        notify=NotifyConfig.from_env(),
        shipscope=ShipScopeConfig.from_env(),
        reporters=ReporterNotifyConfig.from_env(),
        channels=ChannelsConfig.from_env(),
        pr_state=pr_state.checker(config),
    )


def _git_run(argv: list[str], cwd: Path) -> tuple[int, str]:
    """Uruchamia git w klonie produktu bez powłoki, z twardym timeoutem i obcięciem wyjścia do 1 MiB."""
    try:
        done = subprocess.run(  # noqa: S603
            ["git", "-C", str(cwd), *argv],  # noqa: S607 — lista argumentów; git z PATH
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            check=False,
        )
    except FileNotFoundError:
        return 127, "brak polecenia git"
    except subprocess.TimeoutExpired:
        return 124, "git: przekroczony czas"
    out = (done.stdout or "") + (done.stderr or "")
    return done.returncode, out[: 1024 * 1024]


# --- odczyt (strony) ---


def _nav(token: str) -> str:
    """Menu z tokenem w każdym linku (bez tokenu strony zwracają 404); bez tokenu — samo menu bez linków."""
    if not token:
        return "<nav></nav>"
    t = _escape(token)
    pages = (
        ("now", "Now"),
        ("discuss", "Discuss"),
        ("board", "Tablica"),
        ("inbox", "Skrzynka"),
        ("decisions", "Decyzje"),
        ("autonomy", "Autonomia"),
        ("flow", "Przepływ"),
    )
    return "<nav>" + "".join(f'<a href="/{path}?t={t}">{label}</a>' for path, label in pages) + "</nav>"


def _render_page(title: str, body: str, *, nonce: str, token: str = "") -> str:
    """Wrapuje `body` w szkielet HTML ze stałym CSP. Bez inline-JS: jedyny JS ma `script-src 'self' 'nonce-<los>'`.

    `token` trafia tylko do linków menu stron, na które wszedł ktoś z poprawnym tokenem (nie do stron błędów)."""
    return (
        '<!doctype html><html lang="pl"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{_escape(title)} — pdi</title>"
        f"<style>{_STYLE}</style>"
        "</head><body>"
        f'<header><span class="brand">pdi</span> <strong>Konsola</strong>'
        f"{_nav(token)}"
        "</header>"
        f"<main>{body}</main></body></html>"
    )


def _board_body(deps: Deps, token: str) -> str:
    changes = (
        [deps.changes.get(p.stem) for p in sorted((deps.registry.root / "changes").glob("*.yaml"))]
        if (deps.registry.root / "changes").is_dir()
        else []
    )
    inbox_open = [i for i in deps.inbox.items(status="open")]
    open_by_change: dict[str, list[dict[str, Any]]] = {}
    for item in inbox_open:
        if item.get("change"):
            open_by_change.setdefault(item["change"], []).append(item)

    def _cards(lane: int) -> str:
        cards = []
        for state in changes:
            waiting = state.get("waiting") or []
            dispatch = state.get("dispatch") or {}
            phase = dispatch.get("phase")
            ch_lane = _lane_of(phase, waiting)
            if ch_lane != lane:
                continue
            chg = _escape(state["change"])
            phase_label = _escape(phase or (waiting[0] if waiting else state.get("status") or "open"))
            waits = open_by_change.get(state["change"]) or []
            wait_line = ""
            if waits:
                labels = ", ".join(_escape(w.get("summary") or w["id"])[:60] for w in waits)
                wait_line = f'<div class="wait">czeka na Ciebie: {labels}</div>'
            progress = dispatch.get("last_progress") or {}
            progress_line = ""
            if isinstance(progress, dict) and progress.get("message"):
                cost = progress.get("cost_usd")
                cost_label = f" · {cost:.2f} USD" if isinstance(cost, (int, float)) else ""
                text = _escape(_progress_text(progress, waiting))
                progress_line = f'<div class="progress"><small>{text}{cost_label}</small></div>'
            link = f"/trace/{chg}?t={_escape(token)}"
            progress_line += _pr_loop_line(state.get("pr_loop"))
            cards.append(
                f'<li><div class="card">'
                f'<a href="{link}"><span class="chg">{chg}</span></a>'
                f'<span class="phase">{phase_label}</span>'
                f"{wait_line}{progress_line}"
                "</div></li>"
            )
        return "<ul>" + ("".join(cards) if cards else "<li><small>brak zmian</small></li>") + "</ul>"

    lanes_html = "".join(
        f'<div class="lane l{lane}"><h3>{lane}. {LANE_LABELS[lane]}</h3>{_cards(lane)}</div>' for lane in (1, 2, 3)
    )
    summary = f"<p><strong>Zmiany:</strong> {len(changes)} · <strong>Czeka na Ciebie:</strong> {len(inbox_open)}</p>"
    return f"<h1>Tablica</h1>{summary}<section class='lanes'>{lanes_html}</section>"


NOW_COLUMNS = {1: "In progress", 2: "Awaiting decision", 3: "In review", 4: "Done"}
NOW_DONE_DAYS = 7
NOW_DONE_MAX = 20
_REVIEW_OPEN = ("open", "green", "needs_human")


def _ago(stamp: Any, now: datetime) -> str:
    """„5 min temu”, „3 h temu”, „2 dni temu” z czasu ISO (`…Z`); pusty tekst, gdy czasu nie ma albo jest zły."""
    try:
        moment = datetime.strptime(str(stamp), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError:
        return ""
    minutes = max(0, int((now - moment).total_seconds() // 60))
    if minutes < 60:
        return f"{minutes} min temu"
    if minutes < 48 * 60:
        return f"{minutes // 60} h temu"
    return f"{minutes // (24 * 60)} dni temu"


def _now_column(run: dict[str, Any], now: datetime) -> int | None:
    """Kolumna tablicy „Now” dla przebiegu agenta (DI Team T3); None — poza tablicą (stary albo bez stanu)."""
    status = run.get("status")
    review = run.get("review") if isinstance(run.get("review"), dict) else None
    if status == "running":
        return 1
    if status == "waiting_gate":
        return 2
    if status == "done" and review and review.get("status") in _REVIEW_OPEN:
        return 3
    if status in ("done", "failed", "cancelled"):
        finished = str(run.get("finished_at") or run.get("updated_at") or "")
        try:
            moment = datetime.strptime(finished, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        except ValueError:
            return None
        return 4 if (now - moment).days < NOW_DONE_DAYS else None
    return None


def _run_card(run: dict[str, Any], column: int, now: datetime, token: str) -> str:
    started = run.get("started_by")
    who: dict[str, Any] = started if isinstance(started, dict) else {}
    name = _escape(who.get("name") or "?")
    robot = " (automat)" if who.get("kind") == "automation" else ""
    change = run.get("change")
    title = (
        f'<a href="/trace/{_escape(change)}?t={_escape(token)}"><span class="chg">{_escape(change)}</span></a>'
        if change
        else '<span class="chg">sesja</span>'
    )
    bits = [_escape(x) for x in (run.get("task"), run.get("phase"), run.get("agent")) if x]
    lines = [f'<div class="who">Started by: {name}{robot}</div>']
    if column == 1 and run.get("activity"):
        lines.append(f"<div><small>{_escape(_sanitize_text(run['activity'], 200))}</small></div>")
    if column == 2:
        lines.append('<div class="wait">czeka na decyzję na bramce</div>')
    cost = run.get("cost_usd")
    budget = run.get("budget_usd")
    if isinstance(cost, (int, float)):
        money = f"{cost:.2f} USD" + (f" z {budget:.2f}" if isinstance(budget, (int, float)) else "")
        lines.append(f"<div><small>koszt: {money}</small></div>")
    review = run.get("review") if isinstance(run.get("review"), dict) else None
    if review and column in (3, 4):
        parts = [x for x in (review.get("status"), review.get("ai_verdict"), review.get("risk")) if x]
        rev = review.get("reviewer")
        label = _escape(" · ".join(str(p) for p in parts)) + (f" · {_escape(rev)}" if rev else "")
        lines.append(f"<div><small>{_escape(_pr_label_of(review.get('url')))} {label}</small></div>")
    if column == 4 and run.get("status") != "done":
        lines.append(f'<div class="err"><small>{_escape(run.get("status"))}</small></div>')
    fresh = _ago(run.get("updated_at"), now)
    if fresh:
        lines.append(f'<div class="fresh">zmiana karty: {fresh}</div>')
    head = title + (f' <span class="phase">{" · ".join(bits)}</span>' if bits else "")
    return f'<li><div class="card">{head}{"".join(lines)}</div></li>'


def _item_card(item: dict[str, Any], now: datetime, token: str, team: dict[str, Any] | None = None) -> str:
    """Pozycja skrzynki w kolumnie „Awaiting decision”: na co czeka; decyzja zawsze w skrzynce (link).

    `team`: konsultacja „Ask team” (T4) widziana bez odpowiedzi innych — „With team · N/M” albo wynik po zamknięciu."""
    change = item.get("change")
    head = f'<span class="chg">{_escape(change)}</span> ' if change else ""
    gate = f'<span class="phase">{_escape(item.get("gate") or item.get("kind") or "")}</span>'
    summary = _escape(_sanitize_text(item.get("summary") or item["id"], 200))
    link = f'<a href="/inbox/{_escape(item["id"])}?t={_escape(token)}">zdecyduj w skrzynce</a>'
    fresh = _ago(item.get("received_at"), now)
    tail = f'<div class="fresh">czeka od: {fresh}</div>' if fresh else ""
    notices = item.get("deadline_notices") or {}
    if item.get("needs_review"):
        tail += '<div class="fresh"><b>do przeglądu</b> (4 × termin)</div>'
    elif item.get("paused_at"):
        tail += '<div class="fresh"><b>wstrzymana</b> (2 × termin)</div>'
    elif "overdue" in notices:
        tail += '<div class="fresh"><b>po terminie</b></div>'
    if team is not None:
        if team["status"] == "open":
            label = f"With team · {team['answered']}/{team['asked']} · closes {team['closes_at']}"
        elif team["result"]["kind"] == "agree":
            label = f"Team agrees: {team['result']['option']}"
        else:
            label = "To discuss" if team["result"]["kind"] == "discuss" else "Nobody answered"
        tail += f'<div class="fresh"><b>{_escape(label)}</b></div>'
    return f'<li><div class="card">{head}{gate}<div><small>{summary}</small></div><div>{link}</div>{tail}</div></li>'


def _now_body(deps: Deps, token: str, who: str, now: datetime) -> str:
    """Tablica „Now” (DI Team T3): co dzieje się teraz, tylko odczyt. Przebiegi z `agent-runs/`, decyzje ze skrzynki.

    Filtr `who` zawęża przebiegi do jednej osoby („Started by”); pozycje skrzynki nie mają tej osoby, więc przy
    filtrze ich nie widać. Zapis zawsze w aplikacji-właścicielu (decyzja → skrzynka), nie tutaj."""
    runs = deps.inbox.runs.list()
    people = sorted(
        {
            str(r["started_by"]["name"])
            for r in runs
            if isinstance(r.get("started_by"), dict) and r["started_by"].get("name")
        }
    )
    if who:
        runs = [r for r in runs if isinstance(r.get("started_by"), dict) and r["started_by"].get("name") == who]
    columns: dict[int, list[str]] = {n: [] for n in NOW_COLUMNS}
    for run in runs:
        col = _now_column(run, now)
        if col is not None and not (col == 4 and len(columns[4]) >= NOW_DONE_MAX):
            columns[col].append(_run_card(run, col, now, token))
    if not who:
        columns[2] = [
            _item_card(i, now, token, deps.consults.view(i["id"], "")) for i in deps.inbox.items(status="open")
        ] + columns[2]
    t = _escape(token)
    links = [f'<a href="/now?t={t}"{" class=on" if not who else ""}>wszyscy</a>']
    links += [
        f'<a href="/now?t={t}&amp;who={_escape(quote(p))}"{" class=on" if p == who else ""}>{_escape(p)}</a>'
        for p in people
    ]
    counts = " · ".join(f"<strong>{label}:</strong> {len(columns[n])}" for n, label in NOW_COLUMNS.items())
    lanes = "".join(
        f'<div class="lane n{n}"><h3>{label}</h3><ul>'
        + ("".join(columns[n]) if columns[n] else "<li><small>nic</small></li>")
        + "</ul></div>"
        for n, label in NOW_COLUMNS.items()
    )
    return (
        f"<h1>Now</h1><p>{counts}</p>"
        f'<p class="filters"><small>Started by:</small> {"".join(links)}</p>'
        f"<section class='lanes now'>{lanes}</section>"
        f"<p><small>Przebiegi agentów zgłasza fabryka (tf); „Done” pokazuje ostatnie {NOW_DONE_DAYS} dni.</small></p>"
    )


def _trace_body(deps: Deps, change: str, token: str) -> str:
    try:
        graph = deps.trace(change)
    except LookupError as e:
        raise Refused(str(e)) from e
    state: dict[str, Any] = {}
    try:
        state = deps.changes.get(change)
    except LookupError:
        state = {}
    waiting = state.get("waiting") or []
    dispatch = state.get("dispatch") or {}
    progress = dispatch.get("last_progress") or {}
    lane = _lane_of(dispatch.get("phase"), waiting)
    files = _files_section(deps, change, token)
    progress_html = _progress_panel(change, progress, token)
    steps = []
    for node in graph.get("nodes") or []:
        label = _sanitize_text(node.get("label"), limit=120)
        status = _escape(node.get("status") or "")
        kind = _escape(node.get("kind"))
        steps.append(
            f"<tr><td><span class='pill'>{kind}</span></td>"
            f"<td>{_escape(label)}</td>"
            f"<td><small>{status}</small></td></tr>"
        )
    steps_html = (
        "<table><thead><tr><th>Rodzaj</th><th>Etykieta</th><th>Status</th></tr></thead>"
        f"<tbody>{''.join(steps) or '<tr><td colspan=3><small>brak węzłów</small></td></tr>'}</tbody></table>"
    )
    return (
        f"<h1>Ślad zmiany {_escape(change)}</h1>"
        f"<p><strong>Pas {lane} z 3</strong> · {LANE_LABELS[lane]} · teraz: "
        f"{_escape(dispatch.get('phase') or waiting or state.get('status') or '—')}</p>"
        "<div class='grid'><div>"
        f"<h2>Kroki</h2>{steps_html}"
        f"<h2>Pliki zmiany</h2>{files}"
        f"{_pr_loop_table(state.get('pr_loop'))}"
        "</div>"
        f"<aside class='side'>{progress_html}</aside>"
        "</div>"
    )


def _pr_loop_line(loop: Any) -> str:
    """Linia na karcie tablicy: każdy PR cięcia z pętli PR (N2) — numer, status, runda."""
    if not isinstance(loop, dict) or not loop:
        return ""
    parts = []
    for url, entry in loop.items():
        if not isinstance(entry, dict):
            continue
        number = re.search(r"/pull/([0-9]+)", str(url))
        label = f"PR #{number.group(1)}" if number else "PR"
        parts.append(f"{label}: {entry.get('status')} (runda {entry.get('round')}/{entry.get('max_rounds')})")
    return f'<div class="progress"><small>{_escape(" · ".join(parts))}</small></div>' if parts else ""


def _pr_loop_table(loop: Any) -> str:
    """Rundy pętli PR na stronie śladu zmiany: przegląd, poprawki, pytania, checki, koszt."""
    if not isinstance(loop, dict) or not loop:
        return ""
    rows = []
    for url, entry in loop.items():
        if not isinstance(entry, dict):
            continue
        for r in entry.get("rounds") or []:
            if not isinstance(r, dict):
                continue
            raw_checks = r.get("checks")
            checks: dict[str, Any] = raw_checks if isinstance(raw_checks, dict) else {}
            cost = r.get("cost_usd")
            rows.append(
                f"<tr><td>{_escape(_pr_label_of(url))}</td><td>{_escape(r.get('round'))}</td>"
                f"<td>{_escape(r.get('findings'))}</td><td>{_escape(', '.join(r.get('fixed') or []) or '—')}</td>"
                f"<td>{_escape(', '.join(r.get('questions') or []) or '—')}</td>"
                f"<td>{_escape(checks.get('state') or '—')}</td>"
                f"<td>{_escape(f'{cost:.2f}' if isinstance(cost, (int, float)) else '—')}</td></tr>"
            )
        rows.append(
            f"<tr><td colspan=7><small>{_escape(_pr_label_of(url))}: <strong>{_escape(entry.get('status'))}</strong>"
            f" — {_escape(_sanitize_text(entry.get('reason'), limit=200))}</small></td></tr>"
        )
    head = (
        "<thead><tr><th>PR</th><th>Runda</th><th>Uwagi</th><th>Poprawione</th><th>Do Ciebie</th>"
        "<th>Checki</th><th>USD</th></tr></thead>"
    )
    return f"<h2>Pętla PR</h2><table>{head}<tbody>{''.join(rows)}</tbody></table>"


def _pr_label_of(url: Any) -> str:
    number = re.search(r"/pull/([0-9]+)", str(url))
    return f"PR #{number.group(1)}" if number else str(url)


def _pr_ready_html(item: dict[str, Any]) -> str:
    url = str(item.get("url") or "")
    link = f'<p><a href="{_escape(url)}">{_escape(_pr_label_of(url))}</a></p>' if url.startswith("https://") else ""
    questions = [q for q in item.get("open_questions") or [] if isinstance(q, str)]
    listing = "".join(f"<li>{_escape(_sanitize_text(q, limit=400))}</li>" for q in questions)
    return link + (f"<p>Do Ciebie (odpowiedz w PR):</p><ul>{listing}</ul>" if listing else "")


def _files_section(deps: Deps, change: str, token: str) -> str:
    """Artefakty zmiany z gita (gałąź fazy i commit), a nie z katalogu roboczego klonu — tylko te, które istnieją."""
    found = _find_artifacts(deps, change) if deps.checkout is not None else {}
    rows = []
    for name in ALLOWED_ARTIFACTS:
        if name not in found:
            continue
        ref, _, blob = found[name]
        link = f"/trace/{_escape(change)}/file?path={_escape(name)}&t={_escape(token)}"
        rows.append(
            f'<li><a href="{link}">{_escape(name)}</a> <small>{_escape(ref)} · {_escape(blob[:7])}</small></li>'
        )
    listing = "<ul>" + "".join(rows) + "</ul>" if rows else "<p><small>brak artefaktów na gałęziach zmiany</small></p>"
    diff_link = f"/trace/{_escape(change)}/diff?t={_escape(token)}"
    return listing + f'<p><a href="{diff_link}">diff bieżącego cięcia</a></p>'


PHASES_NEWEST_FIRST = ("delivery", "design", "architecture", "requirements", "intent")


def _artifact_refs(change: str) -> list[str]:
    """Gałęzie, na których szukamy artefaktów: najpierw najnowsza faza (lokalna, potem z origin), na końcu main."""
    local = [f"pdi/{change}-{phase}" for phase in PHASES_NEWEST_FIRST]
    remote = [f"origin/{ref}" for ref in local]
    return [*local, *remote, "main", "origin/main"]


def _find_artifacts(deps: Deps, change: str) -> dict[str, tuple[str, str, str]]:
    """`{nazwa: (gałąź, tryb, sha blobu)}` z `git ls-tree` — pierwsza gałąź z listy, na której plik jest."""
    if deps.checkout is None or not re.match(r"^CHG-[0-9]+$", change):
        return {}
    found: dict[str, tuple[str, str, str]] = {}
    folder = f"docs/project/changes/{change}/"
    for ref in _artifact_refs(change):
        code, out = deps.git(["ls-tree", ref, folder], Path(deps.checkout))
        if code != 0:
            continue
        for line in out.splitlines():
            meta, _, path = line.partition("\t")
            parts = meta.split()
            name = path.rsplit("/", 1)[-1]
            if len(parts) == 3 and name in ALLOWED_ARTIFACTS and name not in found:
                found[name] = (ref, parts[0], parts[2])
        if len(found) == len(ALLOWED_ARTIFACTS):
            break
    return found


def _progress_text(progress: dict[str, Any], waiting: list[str]) -> str:
    """Ostatnia linia postępu po ludzku: przy `waiting_gate` wiadomość to nazwa bramki, która mogła już zostać
    rozstrzygnięta, więc sama nazwa obok fazy myli („designdesign-review”)."""
    message = _sanitize_text(progress.get("message"), limit=60)
    if progress.get("status") == "waiting_gate":
        return f"czeka na bramkę {message}" if message in waiting else f"bramka {message} rozstrzygnięta"
    return message


def _progress_panel(change: str, progress: dict[str, Any], token: str) -> str:
    sse = f"/sse/progress?change={_escape(change)}&t={_escape(token)}"
    cost = progress.get("cost_usd")
    cost_line = f"<p><strong>Koszt do tej pory:</strong> {cost:.2f} USD</p>" if isinstance(cost, (int, float)) else ""
    status = _escape(progress.get("status") or "")
    message = _escape(_sanitize_text(progress.get("message"), limit=200))
    phase = _escape(progress.get("phase") or "")
    return (
        "<h2>Postęp</h2>"
        f"<p><small>faza</small> {phase or '—'}</p>"
        f"<p><strong>{status or 'bez danych'}</strong> {message}</p>"
        f"{cost_line}"
        f'<p><small>strumień: <a href="{sse}">SSE</a></small></p>'
        "<p><small>Miejsce na kolejne liczby (OpenTelemetry, Z10c): koszt, tokeny, odmowy, błędy.</small></p>"
    )


ITEM_OPTIONS = {
    "gate": ("approved", "changes_requested", "rejected"),
    "impact_review": ("met", "not_met", "unknown"),
    "problem": ("accepted", "rejected"),
    "autonomy": ("approved", "rejected"),
    "capture": ("approved", "rejected"),
    "process": ("approved", "rejected"),
}
ASK_HOURS = (("4", "4 h"), ("24", "24 h"), ("72", "3 days"))


def _options_for(kind: str) -> tuple[str, ...]:
    return ITEM_OPTIONS.get(kind, ("approved",))


def _ask_html(deps: Deps, item: dict[str, Any], viewer: Any) -> str:
    """„Ask team” (DI Team T4) na karcie pozycji: pytanie, stan, odpowiedź zapytanego, wynik po zamknięciu.

    Tylko z logowaniem przez suitę (`viewer` to sesja). Odpowiedzi innych są ukryte do zamknięcia dla wszystkich."""
    if viewer is None or item.get("kind") == "pr_ready":
        return ""
    iid = _escape(item["id"])
    view = deps.consults.view(item["id"], viewer.sub)
    if view is None:
        if viewer.access != "decide":
            return ""
        others = [p for p in deps.people.all() if p.sub != viewer.sub]
        if not others:
            return "<p><small>Ask team: nobody else has signed in to this console yet.</small></p>"
        boxes = " ".join(
            f'<label><input type="checkbox" name="ask_{_escape(p.sub)}" value="1"> {_escape(p.name)}</label>'
            for p in others
        )
        hours = "".join(
            f'<option value="{v}"{" selected" if v == "24" else ""}>{label}</option>' for v, label in ASK_HOURS
        )
        select = f'<select name="hours">{hours}</select>'
        return (
            f'<form class="ask" method="post" action="/inbox/{iid}/ask"><details><summary>Ask team</summary>'
            f"<p>{boxes}</p><p><label>Closes in {select}</label> "
            '<button type="submit">Ask</button> <small>Answers stay hidden from everyone, you too, until it closes. '
            "The team advises; you decide.</small></p></details></form>"
        )
    effects = "".join(f"<li><strong>{_escape(o)}</strong>: {_escape(t)}</li>" for o, t in view["effects"].items())
    effects_html = f"<p><small>Agent on the options:</small></p><ul>{effects}</ul>" if effects else ""
    if view["status"] == "open":
        counts = f"{view['answered']}/{view['asked']}"
        head = (
            f'<p class="pill open">With team · {counts} · closes {_escape(view["closes_at"])}</p>'
            f"<p><small>Asked by {_escape(view['decider'])}: {_escape(', '.join(view['asked_names']))}</small></p>"
            + (
                f"<p><small>Not reachable in Slack: {_escape(', '.join(view['unreachable']))}</small></p>"
                if view["unreachable"]
                else ""
            )
        )
        mine = ""
        if view["is_asked"]:
            current = view["mine"] or {}
            radios = " ".join(
                f'<label><input type="radio" name="option" value="{_escape(o)}"'
                f"{' checked' if current.get('option') == o else ''} required> {_escape(o)}</label>"
                for o in (*view["options"], consult.TALK_LIVE)
            )
            mine = (
                f'<form class="ask" method="post" action="/inbox/{iid}/answer"><p><strong>Asked of you</strong> '
                f'{radios}</p><p><input type="text" name="reason" maxlength="{consult.MAX_REASON}" required '
                f'placeholder="One sentence: why" value="{_escape(current.get("reason") or "")}"> '
                '<button type="submit">Answer</button></p></form>'
            )
        close = ""
        if viewer.sub == view["decider_sub"]:
            close = (
                f'<form class="ask" method="post" action="/inbox/{iid}/close-ask">'
                '<button type="submit">Close the question now</button></form>'
            )
        return head + effects_html + mine + close
    result = view["result"]
    if result["kind"] == "agree":
        verdict = f'<p class="pill open">Team agrees: {_escape(result["option"])}</p>'
    elif result["kind"] == "discuss":
        verdict = '<p class="pill warn">To discuss</p>'
    else:
        verdict = '<p class="pill">Nobody answered</p>'
    rows = "".join(
        f"<li>{_escape(a['name'])}: <strong>{_escape(a['option'] or '—')}</strong>"
        f"{' — ' + _escape(a['reason']) if a['reason'] else ''}</li>"
        for a in view["answers"]
    )
    return verdict + f"<ul>{rows}</ul>" + effects_html


def _escalate_html(deps: Deps, item: dict[str, Any], viewer: Any) -> str:
    """„Escalate” (DI Team T7, OM2) na karcie: stan eskalacji, formularz przekazania decyzji i oddanie sprawy."""
    if viewer is None or item.get("kind") == "pr_ready":
        return ""
    iid = _escape(item["id"])
    limit = escalate.MAX_TEXT
    e = deps.escalations.view(item["id"])
    if e is not None and not e.get("returned_at"):
        by, to = _escape(e["by"]["name"]), _escape(e["to"]["name"])
        if e["to"]["sub"] == viewer.sub:
            question = f"<p><small>Question: {_escape(e['question'])}</small></p>" if e.get("question") else ""
            return (
                f'<p class="pill warn">{by} escalated this to you</p>'
                f"<p><small>Why: {_escape(e['reason'])}</small></p>{question}"
                f'<form class="ask" method="post" action="/inbox/{iid}/give-back">'
                "<details><summary>Give it back</summary>"
                f'<p><input type="text" name="note" maxlength="{limit}" required placeholder="Why you give it back">'
                ' <button type="submit">Give back</button></p></details></form>'
            )
        return (
            f'<p class="pill warn">Escalated to {to} · since {_escape(e["at"])}</p>'
            f"<p><small>By {by}: {_escape(e['reason'])}. Only {to} decides now.</small></p>"
        )
    note = ""
    if e is not None and e.get("returned_at"):
        note = f"<p><small>{_escape(e['to']['name'])} gave it back: {_escape(e.get('return_note') or '')}</small></p>"
    if viewer.access != "decide":
        return note
    admin_only = escalate.protected(item)
    choices = [
        p
        for p in deps.people.deciders()
        if p.sub != viewer.sub and (not admin_only or (deps.people.get(p.sub) or {}).get("admin"))
    ]
    if not choices:
        return note + "<p><small>Escalate: nobody else who can decide has signed in to this console yet.</small></p>"
    options = "".join(f'<option value="{_escape(p.sub)}">{_escape(p.name)}</option>' for p in choices)
    hint = " Protected decision: only admins." if admin_only else ""
    picker = "<p><label>To " + '<select name="to">' + options + "</select></label></p>"
    return note + (
        f'<form class="ask" method="post" action="/inbox/{iid}/escalate"><details><summary>Escalate</summary>{picker}'
        f'<p><input type="text" name="reason" maxlength="{limit}" required '
        'placeholder="Why the team should not decide this alone"></p>'
        f'<p><input type="text" name="question" maxlength="{limit}" placeholder="Question for them (optional)"></p>'
        '<p><button type="submit">Escalate</button> '
        f"<small>They decide this item now; the deadline stays.{hint}</small></p></details></form>"
    )


def _discuss_body(deps: Deps, viewer: Any, now: datetime, token: str = "") -> str:
    """„Discuss with team” (T5): sprawy z rozbieżnością zespołu według tego, co blokują, z decyzją ze spotkania."""
    deps.inbox.check_deadlines()
    entries = agenda.build(deps.inbox.items(status="open"), deps.consults, order=deps.agenda.get(), now=now)
    decides = viewer is None or viewer.access == "decide"
    cards = []
    for n, e in enumerate(entries, 1):
        iid = _escape(e["item_id"])
        where = " · ".join(_escape(x) for x in (e["change"], e["gate"]) if x)
        answers = "".join(
            f"<li>{_escape(a['name'])}: <strong>{_escape(a['option'] or '—')}</strong>"
            f"{' — ' + _escape(a['reason']) if a['reason'] else ''}</li>"
            for a in e["answers"]
        )
        effects = "".join(f"<li><strong>{_escape(o)}</strong>: {_escape(t)}</li>" for o, t in e["effects"].items())
        move = ""
        decide = ""
        if decides:
            q = f"?t={_escape(token)}" if token else ""
            hidden = f'<input type="hidden" name="t" value="{_escape(token)}">' if token else ""
            move = " ".join(
                f'<form class="inline" method="post" action="/discuss/{iid}/{d}{q}">{hidden}'
                f'<button type="submit">{arrow}</button></form>'
                for d, arrow in (("up", "↑"), ("down", "↓"))
            )
            buttons = " ".join(
                f'<button name="outcome" value="{_escape(o)}">{_escape(o)}</button>' for o in e["options"]
            )
            decide = (
                f'<form method="post" action="/inbox/{iid}/decide{q}">{hidden}'
                '<input type="hidden" name="via" value="agenda">'
                f'<input type="hidden" name="loaded_at" value="{_escape(e["received_at"])}">'
                '<div class="row"><label>Treść decyzji (statement)</label>'
                '<textarea name="statement" required maxlength="800"></textarea></div>'
                '<div class="row"><label>Dlaczego (why)</label>'
                '<textarea name="why" required maxlength="2000"></textarea></div>'
                f'<div class="row">{buttons}</div></form>'
            )
        cards.append(
            f'<section class="card"><h2>{n}. {_escape(_sanitize_text(e["summary"], 200))} '
            f'<span class="pill">{where or _escape(e["kind"])}</span> {move}</h2>'
            f"<p><small>Why now: {_escape('; '.join(e['reasons']))} · asked by {_escape(e['decider'])}</small></p>"
            f"<ul>{answers}</ul>"
            + (f"<p><small>Agent on the options:</small></p><ul>{effects}</ul>" if effects else "")
            + f"{decide}</section>"
        )
    md = agenda.markdown(entries, day=now.date().isoformat())
    body = (
        "".join(cards) if cards else "<p>Nothing to discuss: no team question ended in a split or a call to talk.</p>"
    )
    export = (
        "<details><summary>Markdown for the invitation or notes</summary>"
        f'<textarea readonly rows="12" style="width:100%">{_escape(md)}</textarea></details>'
    )
    hint = "<p><small>Ordered by what each item blocks; the decider may move them.</small></p>"
    return f"<h1>Discuss with team</h1>{hint}{body}{export}"


def _inbox_body(deps: Deps, token: str, viewer: Any = None) -> str:
    deps.inbox.open_ready_prs()  # PR-y cięć po pętli PR (N2): pozycja dopiero przy green albo needs_human
    deps.inbox.check_deadlines()  # terminy z OM1 (N3): przypomnienia, „wstrzymana”, „do przeglądu”
    items = deps.inbox.items(status="open")
    rows = []
    for item in items:
        lane = _lane_of(item.get("gate") or item.get("kind"), None, kind=item.get("kind"))
        questions = item.get("questions") or []
        # pytania z pętli PR (N2) odpowiada się w PR, nie w formularzu bramki
        q_html = _pr_ready_html(item) if item["kind"] == "pr_ready" else _render_questions(item["id"], questions)
        action_buttons = _action_buttons_for(item["kind"])
        link = f"/inbox/{_escape(item['id'])}?t={_escape(token)}"
        # „Ask team” (T4): przy zgodności zespołu szkic decyzji jest już wypełniony — wystarczy przycisk.
        statement_default = why_default = ""
        team = deps.consults.view(item["id"], viewer.sub) if viewer is not None else None
        if team and team["status"] == "closed" and team["result"]["kind"] == "agree":
            option = team["result"]["option"]
            statement_default = f"{_sanitize_text(item.get('summary'), limit=600)}: {option} (the team agrees)"
            why_default = "; ".join(f"{a['name']}: {a['reason']}" for a in team["answers"] if a["reason"])
        rows.append(
            f'<section class="card">'
            f'<h2><a href="{link}">{_escape(item["id"])}</a> '
            f'<span class="pill">pas {lane}</span> '
            f'<span class="pill">{_escape(item["kind"])}</span> '
            f'<span class="pill open">czeka</span></h2>'
            f"<p><strong>{_escape(item.get('summary'))}</strong></p>"
            f"{_risk_html(item)}{_pin_html(item)}"
            f"{_ask_html(deps, item, viewer)}{_escalate_html(deps, item, viewer)}"
            f'<form method="post" action="/inbox/{_escape(item["id"])}/decide?t={_escape(token)}">'
            f'<input type="hidden" name="t" value="{_escape(token)}">'
            f'<input type="hidden" name="loaded_at" value="{_escape(item["received_at"])}">'
            f"{q_html}"
            '<div class="row"><label>Treść decyzji (statement)</label>'
            f'<textarea name="statement" required maxlength="800">{_escape(statement_default)}</textarea></div>'
            '<div class="row"><label>Dlaczego (why)</label>'
            f'<textarea name="why" required maxlength="2000">{_escape(why_default[:2000])}</textarea></div>'
            f"{action_buttons}"
            "</form></section>"
        )
    triage = _triage_cards(deps, token) + _stale_cards(deps, token)
    body = "".join(rows) if rows else "<p><small>brak pozycji bramek i ocen</small></p>"
    return f"<h1>Skrzynka</h1>{triage}{body}"


TRIAGE_OPEN = ("new", "clarifying", "ready_for_triage")
REJECTION_REASONS = (
    ("out_of_strategy", "poza strategią"),
    ("works_as_designed", "działa zgodnie z założeniem"),
    ("cost_disproportionate", "koszt nieproporcjonalny"),
    ("already_exists", "już istnieje"),
    ("out_of_scope_recorded", "poza zakresem (zapisane)"),
    ("no_code", "bez kodu (konfiguracja, proces, istniejąca funkcja)"),
    ("other", "inny powód"),
)
NO_CODE_KINDS = (
    ("configuration", "konfiguracja"),
    ("process_change", "zmiana procesu"),
    ("existing_feature", "istniejąca funkcja"),
)


def _stale_cards(deps: Deps, token: str) -> str:
    """DV6: zgłoszenia porzucone — odłożone i bez odpowiedzi — z decyzją „zamknąć” albo „zwalidować ponownie”."""
    rows = stale.report(deps.inbox.problems, deps.inbox.registry, now=deps.inbox.registry.now())
    if not rows:
        return ""
    t = _escape(token)
    labels = {"close": "zamknąć", "revalidate": "zwalidować ponownie"}
    cards = []
    for r in rows:
        pid = _escape(r["problem"])
        cards.append(
            f'<section class="card"><h2>{pid} <span class="pill">porzucone</span> '
            f'<span class="pill open">{_escape(r["days"])} dni</span></h2>'
            f"<p><strong>{_escape(r['title'])}</strong></p><p>{_escape(r['reason'])}. Rekomendacja: "
            f"{_escape(labels[r['recommendation']])}.</p>"
            f'<form method="post" action="/problems/{pid}/stale?t={t}">'
            f'<input type="hidden" name="t" value="{t}">'
            '<div class="row"><label>Treść decyzji (statement)</label>'
            '<textarea name="statement" required maxlength="800"></textarea></div>'
            '<div class="row"><label>Dlaczego (why)</label>'
            '<textarea name="why" required maxlength="2000"></textarea></div>'
            '<div class="row">'
            '<button class="warn" name="outcome" value="close">zamknij</button> '
            '<button name="outcome" value="revalidate">zwaliduj ponownie</button>'
            "</div></form></section>"
        )
    return "<h2>Zgłoszenia porzucone</h2>" + "".join(cards)


def _triage_cards(deps: Deps, token: str) -> str:
    """Zgłoszenia z formularza czekające na triaż (ta sama ścieżka co `triage_problem` w MCP)."""
    waiting = [p for p in deps.inbox.problems.all() if p.get("status") in TRIAGE_OPEN]
    if not waiting:
        return ""
    t = _escape(token)
    reasons = "".join(f'<option value="{v}">{_escape(label)}</option>' for v, label in REJECTION_REASONS)
    kinds = "".join(f'<option value="{v}">{_escape(label)}</option>' for v, label in NO_CODE_KINDS)
    cards = []
    for p in waiting:
        pid = _escape(p["id"])
        facts = "".join(
            f"<li><strong>{label}:</strong> {_escape(p.get(key))}</li>"
            for key, label in (("who", "kto"), ("cannot", "czego nie może"), ("impact", "skutek"))
            if p.get(key)
        )
        cards.append(
            f'<section class="card"><h2>{pid} <span class="pill">triaż</span> '
            f'<span class="pill open">czeka</span></h2>'
            f"<p><strong>{_escape(p.get('title'))}</strong></p><ul>{facts}</ul>"
            f'<form method="post" action="/problems/{pid}/triage?t={t}">'
            f'<input type="hidden" name="t" value="{t}">'
            '<div class="row"><label>Treść decyzji (statement)</label>'
            '<textarea name="statement" required maxlength="800"></textarea></div>'
            '<div class="row"><label>Dlaczego (why)</label>'
            '<textarea name="why" required maxlength="2000"></textarea></div>'
            f'<div class="row"><label>Powód odrzucenia (tylko przy reject)</label>'
            f'<select name="rejection_reason"><option value="">—</option>{reasons}</select></div>'
            '<div class="row"><label>Bez kodu: rodzaj i co zrobić (tylko przy powodzie „bez kodu”)</label>'
            f'<select name="no_code_kind"><option value="">—</option>{kinds}</select>'
            '<textarea name="no_code_how" maxlength="2000"></textarea></div>'
            '<div class="row">'
            '<button name="outcome" value="accepted">accept (załóż CHG)</button> '
            '<button class="warn" name="outcome" value="rejected">reject</button>'
            "</div></form></section>"
        )
    return "<h2>Zgłoszenia do triażu</h2>" + "".join(cards)


def _action_buttons_for(kind: str) -> str:
    """Zestaw przycisków decyzji per rodzaj pozycji (ta sama ścieżka co `decide_inbox_item`)."""
    if kind == "gate":
        return (
            '<div class="row">'
            '<button name="outcome" value="approved">approve</button> '
            '<button class="alt" name="outcome" value="changes_requested">changes requested</button> '
            '<button class="warn" name="outcome" value="rejected">reject</button>'
            "</div>"
        )
    if kind == "impact_review":
        return (
            '<div class="row">'
            '<button name="outcome" value="met">met</button> '
            '<button class="alt" name="outcome" value="not_met">not met</button> '
            '<button class="warn" name="outcome" value="unknown">unknown</button>'
            "</div>"
        )
    if kind == "problem":
        return (
            '<div class="row">'
            '<button name="outcome" value="accepted">accept (załóż CHG)</button> '
            '<button class="warn" name="outcome" value="rejected">reject</button>'
            "</div>"
        )
    if kind == "pr_ready":
        return '<div class="row"><button name="outcome" value="reviewed">przejrzane</button></div>'
    if kind in ("autonomy", "capture"):
        return (
            '<div class="row">'
            '<button name="outcome" value="approved">approve</button> '
            '<button class="warn" name="outcome" value="rejected">reject</button>'
            "</div>"
        )
    return '<div class="row"><button name="outcome" value="approved">approve</button></div>'


def _render_questions(item_id: str, questions: list[Any]) -> str:
    """Pytania pozycji jako pola odpowiedzi; N19 (pytanie z `options`) daje radio z `recommended`."""
    if not questions:
        return ""
    rows = []
    for i, q in enumerate(questions):
        if isinstance(q, dict) and isinstance(q.get("options"), list):
            text = _escape(q.get("question") or "")
            recommended = q.get("recommended")
            options_html = ""
            for opt in q["options"]:
                if not isinstance(opt, dict):
                    continue
                value = _escape(opt.get("value") or opt.get("label") or "")
                label = _escape(opt.get("label") or opt.get("value") or "")
                checked = " checked" if opt.get("value") == recommended else ""
                options_html += (
                    f'<label><input type="radio" name="answer_{i}" value="{value}" required{checked}> '
                    f"{label}</label><br>"
                )
            if q.get("other"):
                options_html += (
                    f'<label><input type="radio" name="answer_{i}" value="__other__" required> inne:</label> '
                    f'<input type="text" name="answer_{i}_other" maxlength="800">'
                )
            rows.append(f'<div class="row"><label>{text}</label>{options_html}</div>')
        else:
            rows.append(
                f'<div class="row"><label>{_escape(q)}</label>'
                f'<input type="text" name="answer_{i}" maxlength="800" required></div>'
            )
    return "".join(rows)


def _decisions_body(deps: Deps, token: str) -> str:
    rows = []
    for d in deps.registry.decisions()[-100:]:
        links = d.get("links") or {}
        chg = _escape(links.get("chg") or "")
        rows.append(
            f'<tr><td><span class="pill">{_escape(d["id"])}</span></td>'
            f"<td>{_escape(d.get('decision_type'))}</td>"
            f"<td>{_escape(_sanitize_text(d.get('statement'), limit=160))}</td>"
            f"<td>{chg}</td>"
            f"<td>{_escape(d.get('decided_at'))}</td></tr>"
        )
    return (
        "<h1>Decyzje</h1>"
        "<table><thead><tr><th>ID</th><th>Typ</th><th>Ustalenie</th><th>Zmiana</th><th>Dzień</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def _autonomy_body(deps: Deps, token: str) -> str:
    policy = autonomy.load_policy(deps.registry)
    types = policy.get("decision_types") or {}
    rows = []
    for name, cfg in sorted(types.items()):
        level = cfg.get("level") if isinstance(cfg, dict) else "?"
        rows.append(f"<tr><td>{_escape(name)}</td><td>{_escape(level)}</td></tr>")
    return (
        "<h1>Autonomia</h1>"
        "<table><thead><tr><th>Typ decyzji</th><th>Poziom</th></tr></thead>"
        f"<tbody>{''.join(rows) or '<tr><td colspan=2><small>brak konfiguracji</small></td></tr>'}</tbody></table>"
    )


def _h(value: Any) -> str:
    return "—" if value is None else f"{value:.1f} h"


def _share(value: Any) -> str:
    return "—" if value is None else f"{round(100 * value)}%"


def _pin_html(item: dict[str, Any]) -> str:
    """Wersja artefaktu, której dotyczy zgoda (kontrakt 0.21.0): skrót i commit."""
    digest = item.get("artifact_sha256")
    if not digest:
        return ""
    commit = f" · commit {_escape(str(item.get('artifact_commit'))[:12])}" if item.get("artifact_commit") else ""
    return f"<p><small>artefakt: {_escape(str(digest)[:12])}{commit} — zgoda dotyczy tej wersji</small></p>"


_RISK_LABEL = {"low": "niskie", "medium": "średnie", "high": "wysokie"}


def _risk_html(item: dict[str, Any]) -> str:
    """Doradcza ocena ryzyka zmiany (DV2) na karcie pozycji: poziom i do 10 pozycji z plikiem i powodem."""
    risk = item.get("risk")
    if not isinstance(risk, dict) or risk.get("level") not in _RISK_LABEL:
        return ""
    rows = "".join(
        f"<li><code>{_escape(i.get('file') or '—')}</code> — {_escape(i.get('reason'))}</li>"
        for i in (risk.get("items") or [])[:10]
        if isinstance(i, dict)
    )
    return (
        f'<p><span class="pill">ryzyko: {_RISK_LABEL[risk["level"]]}</span> '
        "<small>ocena doradcza (tf risk), bramki bez zmian</small></p>" + (f"<ul>{rows}</ul>" if rows else "")
    )


_STAGE_LABEL = {
    "new": "nowa",
    "reminder": "przypomnienie",
    "due_today": "termin dziś",
    "overdue": "po terminie",
    "paused": "wstrzymana",
    "review": "do przeglądu",
}


def _flow_body(deps: Deps, token: str, now: datetime) -> str:
    """DV4: gdzie zmiana czeka — otwarte bramki od najdłużej czekającej, bramki, rodzaje pozycji, czekanie i praca."""
    states = deps.changes.all(status=None)
    r = delays.report(states, deps.inbox.items(status=None), now=now)
    stopped = {p["gate"]: f"{p['stopped']} z {p['measured']}" for p in process.report(states, now=now)}
    t = _escape(token)
    waiting_rows = (
        "".join(
            f'<tr><td><a href="/trace/{_escape(w["change"])}?t={t}">{_escape(w["change"])}</a></td>'
            f"<td>{_escape(w['gate'])}</td><td>{_escape(w['since'])}</td><td>{_h(w['hours'])}</td>"
            f"<td>{_escape(_STAGE_LABEL.get(w['stage'] or '', '—'))}</td>"
            f"<td>{_escape(_RISK_LABEL.get(w.get('risk') or '', '—'))}</td></tr>"
            for w in r["waiting"]
        )
        or "<tr><td colspan=6><small>nic nie czeka na decyzję</small></td></tr>"
    )
    gate_rows = (
        "".join(
            f"<tr><td>{_escape(g['gate'])}</td><td>{g['decided']}</td><td>{_h(g['median_hours'])}</td>"
            f"<td>{_h(g['p90_hours'])}</td><td>{_h(g['max_hours'])}</td>"
            f"<td>{_escape(stopped.get(g['gate'], '—'))}</td><td>{g['open']}</td></tr>"
            for g in r["gates"]
        )
        or "<tr><td colspan=7><small>brak bramek w historii zmian</small></td></tr>"
    )
    kind_rows = (
        "".join(
            f"<tr><td>{_escape(k['kind'])}</td><td>{k['decided']}</td><td>{_h(k['median_hours'])}</td>"
            f"<td>{_h(k['p90_hours'])}</td><td>{k['open']}</td></tr>"
            for k in r["items"]
        )
        or "<tr><td colspan=5><small>skrzynka pusta</small></td></tr>"
    )
    change_rows = (
        "".join(
            f"<tr><td>{_escape(c['change'])}</td><td>{_h(c['waiting_hours'])}</td><td>{_h(c['working_hours'])}</td>"
            f"<td>{_share(c['waiting_share'])}</td></tr>"
            for c in r["changes"]
        )
        or "<tr><td colspan=4><small>brak zmian</small></td></tr>"
    )
    return (
        "<h1>Przepływ</h1>"
        "<p><small>Godziny zegarowe od prośby o bramkę do decyzji (DV4); czekanie — bramki otwarte, praca — reszta "
        "czasu zmiany do wydania albo do teraz.</small></p>"
        "<h2>Gdzie zmiana czeka</h2>"
        "<table><thead><tr><th>Zmiana</th><th>Bramka</th><th>Od</th><th>Czeka</th><th>Termin</th><th>Ryzyko</th></tr></thead>"
        f"<tbody>{waiting_rows}</tbody></table>"
        "<h2>Bramki</h2>"
        "<table><thead><tr><th>Bramka</th><th>Decyzje</th><th>Mediana</th><th>p90</th><th>Najdłużej</th><th>Zatrzymała</th><th>Otwarte</th></tr>"
        f"</thead><tbody>{gate_rows}</tbody></table>"
        "<h2>Skrzynka</h2>"
        "<table><thead><tr><th>Rodzaj</th><th>Decyzje</th><th>Mediana do decyzji</th><th>p90</th>"
        "<th>Otwarte</th></tr></thead>"
        f"<tbody>{kind_rows}</tbody></table>"
        "<h2>Zmiany</h2>"
        "<table><thead><tr><th>Zmiana</th><th>czekanie</th><th>praca</th><th>udział czekania</th></tr></thead>"
        f"<tbody>{change_rows}</tbody></table>"
    )


# --- pliki artefaktów i diff ---


def _artifact_changed(deps: Deps, item: dict[str, Any]) -> str | None:
    """Komunikat, gdy artefakt bramki zmienił się po wysłaniu prośby (kontrakt 0.21.0: `artifact_sha256`); None, gdy
    jest ten sam albo nie da się tego sprawdzić (brak skrótu, klonu albo pliku). Końce linii jako LF, jak liczy tf."""
    expected = item.get("artifact_sha256")
    artifact = str(item.get("artifact") or "")
    if not expected or not item.get("change") or deps.checkout is None:
        return None
    name = artifact.rsplit("/", 1)[-1]
    try:
        current = _read_artifact(deps, str(item["change"]), name)
    except Refused:
        return None
    digest = hashlib.sha256(current.replace(b"\r\n", b"\n")).hexdigest()
    if digest == expected:
        return None
    return (
        f"Artefakt {name} zmienił się po wysłaniu prośby (skrót {str(expected)[:12]} → {digest[:12]}) — zgoda "
        "dotyczyłaby innej wersji niż ta, o którą proszono. Poproś o bramkę ponownie dla bieżącej wersji."
    )


def _read_artifact(deps: Deps, change: str, name: str) -> bytes:
    """Treść artefaktu z gita (gałąź fazy zmiany), po białej liście; bez symlinków, binariów i za dużych plików."""
    if name not in ALLOWED_ARTIFACTS:
        raise Refused(f"plik {name!r} spoza białej listy")
    if _SECRETISH.search(name):
        raise Refused(f"plik {name!r} wygląda na sekret")
    if not re.match(r"^CHG-[0-9]+$", change):
        raise Refused(f"klucz zmiany {change!r} niepoprawny")
    found = _find_artifacts(deps, change).get(name)
    if found is None:
        raise Refused("plik nie istnieje na żadnej gałęzi zmiany")
    _, mode, blob = found
    if mode == "120000":
        raise Refused("symlink odrzucony")
    if mode not in ("100644", "100755"):
        raise Refused("to nie jest zwykły plik")
    if deps.checkout is None:  # pragma: no cover — _find_artifacts zwraca {} bez klonu
        raise Refused("brak klonu produktu")
    code, size = deps.git(["cat-file", "-s", blob], Path(deps.checkout))
    if code != 0 or not size.strip().isdigit():
        raise Refused("nie da się odczytać pliku z gita")
    if int(size) > FILE_SIZE_LIMIT:
        raise Refused(f"plik za duży: {size.strip()} > {FILE_SIZE_LIMIT}")
    code, text = deps.git(["cat-file", "blob", blob], Path(deps.checkout))
    if code != 0:
        raise Refused("nie da się odczytać pliku z gita")
    if "\x00" in text[:BINARY_PEEK]:
        raise Refused("plik wygląda na binarny")
    return text.encode("utf-8")


def _diff_of_current_cut(
    state: dict[str, Any], git: Callable[[list[str], Path], tuple[int, str]], checkout: Path
) -> str:
    """`git diff base..head` bieżącego cięcia; bez cięcia — pusty tekst."""
    dispatch = state.get("dispatch") or {}
    cuts = dispatch.get("cuts") or []
    ref = dispatch.get("ref") or "main"
    if not cuts:
        return "(brak bieżącego cięcia do pokazania)"
    branch = cuts[0].get("branch") if isinstance(cuts[0], dict) else None
    if not branch:
        return "(bieżące cięcie bez nazwy gałęzi)"
    code, out = git(["diff", f"{ref}...{branch}"], checkout)
    if code != 0:
        return f"(git zwrócił kod {code})\n{out}"[:FILE_SIZE_LIMIT]
    return out


# --- SSE ---


def _sse_line(data: Any, *, event: str | None = None) -> bytes:
    text = ""
    if event:
        text += f"event: {event}\n"
    text += f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    return text.encode("utf-8")


# --- serwer ---


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def make_server(
    deps: Deps,
    *,
    token: str,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    clock: Callable[[], datetime] = _utc_now,
    suite: suite_login.SuiteLogin | None = None,
) -> ThreadedHTTPServer:
    """Serwer HTTP konsoli; `port=0` wybiera wolny port (do testów).

    Z `suite` (logowanie przez tożsamość suity, docs/plan-konsola-tozsamosc.md) strony wymagają sesji z logowania,
    a `token` w adresie niczego nie otwiera; decyzja zapisuje osobę z sesji w `decided_by`, a decydować może tylko
    rola `editor` albo `admin` klienta `di-decision`."""
    nonce = secrets.token_urlsafe(16)
    if suite is not None:
        token = SUITE_LINK_TOKEN

    def _csp() -> str:
        return (
            "default-src 'none'; "
            "style-src 'self' 'unsafe-inline'; "
            f"script-src 'self' 'nonce-{nonce}'; "
            "connect-src 'self'; "
            "img-src 'self' data:; "
            "form-action 'self'; "
            "base-uri 'none'"
        )

    class Handler(BaseHTTPRequestHandler):
        session: suite_login.Session | None = None

        def _cookie(self, name: str) -> str:
            jar: SimpleCookie = SimpleCookie()
            try:
                jar.load(self.headers.get("cookie") or "")
            except CookieError:
                return ""
            morsel = jar.get(name)
            return morsel.value if morsel is not None else ""

        def _redirect_uri(self) -> str:
            return f"http://{host}:{cast(ThreadedHTTPServer, self.server).server_port}/callback"

        def _decider(self) -> str:
            if self.session is not None:
                return self.session.name
            return os.environ.get("PDI_DECIDED_BY") or "console"

        def _decider_id(self) -> dict[str, str]:
            """`decided_by_id` (kontrakt 0.25.0): `sub` osoby z sesji suity; bez sesji — pole pominięte."""
            return {"decided_by_id": self.session.sub} if self.session is not None else {}

        def _redirect(self, location: str, cookies: list[str] | None = None) -> None:
            self.send_response(302)
            self.send_header("location", location)
            for cookie in cookies or []:
                self.send_header("set-cookie", cookie)
            self.send_header("content-length", "0")
            self.send_header("cache-control", "no-store")
            self.end_headers()

        def _suite_get(self, path: str, params: Mapping[str, str]) -> bool:
            """Logowanie przez suitę: `/login`, `/callback` i sesja przed każdą stroną; True, gdy odpowiedź poszła."""
            assert suite is not None  # noqa: S101 — wołane tylko w trybie suity
            if path == "/login":
                try:
                    location, state = suite.begin(self._redirect_uri())
                except suite_login.SuiteSignInError as e:
                    sys.stderr.write(f"pdi-console: wystawca suity nieosiągalny: {e}\n")
                    self._html(502, "<h1>502</h1><p>Usługa tożsamości suity nie odpowiada. Spróbuj za chwilę.</p>")
                    return True
                ttl = suite_login.LOGIN_TTL_SECONDS
                cookie = f"{LOGIN_COOKIE}={state}; Path=/callback; Max-Age={ttl}; HttpOnly; SameSite=Lax"
                self._redirect(location, [cookie])
                return True
            if path == "/callback":
                clear = f"{LOGIN_COOKIE}=; Path=/callback; Max-Age=0; HttpOnly; SameSite=Lax"
                try:
                    session_id, signed_in = suite.complete(
                        self._redirect_uri(), code=params.get("code", ""), state=params.get("state", ""),
                        cookie_state=self._cookie(LOGIN_COOKIE),
                    )  # fmt: skip
                except KeyError:
                    self._html(
                        400,
                        "<h1>400</h1><p>Logowanie wygasło albo nie zaczęło się tutaj. "
                        '<a href="/login">Zaloguj się ponownie</a>.</p>',
                    )
                    return True
                except suite_login.Refused as e:
                    self._html(403, f"<h1>403</h1><p>{_escape(str(e))}</p>")
                    return True
                except suite_login.SuiteSignInError as e:
                    sys.stderr.write(f"pdi-console: logowanie przez suitę odrzucone: {e}\n")
                    self._html(
                        502,
                        "<h1>502</h1><p>Logowanie przez suitę nie powiodło się. "
                        '<a href="/login">Spróbuj ponownie</a>.</p>',
                    )
                    return True
                # „Ask team” (T4): kto logował się do tej konsoli, żeby dało się go zapytać (bez e-maila, DI3).
                deps.people.seen(
                    consult.Person(sub=signed_in.sub, name=signed_in.name),
                    decides=signed_in.access == "decide",
                    admin=signed_in.admin,
                )
                ttl = suite_login.SESSION_TTL_SECONDS
                session = f"{SESSION_COOKIE}={session_id}; Path=/; Max-Age={ttl}; HttpOnly; SameSite=Lax"
                self._redirect("/", [clear, session])
                return True
            self.session = suite.session(self._cookie(SESSION_COOKIE))
            if self.session is None:
                self._redirect("/login")
                return True
            return False

        def do_GET(self) -> None:  # noqa: N802
            url = urlsplit(self.path)
            params = {k: v[-1] for k, v in parse_qs(url.query).items() if v}
            given = params.get("t", "")
            if suite is not None:
                if self._suite_get(url.path, params):
                    return None
            elif not _token_ok(token, given):
                return self._html(404, "<h1>404</h1><p>Brak takiej strony.</p>")

            path = url.path
            try:
                if path == "/now":
                    body = _now_body(deps, token, params.get("who", ""), clock())
                    return self._html(200, _render_page("Now", body, nonce=nonce, token=token))
                if path == "/discuss":
                    body = _discuss_body(deps, self.session, clock(), token if suite is None else "")
                    return self._html(200, _render_page("Discuss with team", body, nonce=nonce, token=token))
                if path == "/" or path == "/board":
                    return self._html(200, _render_page("Tablica", _board_body(deps, token), nonce=nonce, token=token))
                if path == "/inbox":
                    return self._html(
                        200, _render_page("Skrzynka", _inbox_body(deps, token, self.session), nonce=nonce, token=token)
                    )
                if path == "/decisions":
                    return self._html(
                        200, _render_page("Decyzje", _decisions_body(deps, token), nonce=nonce, token=token)
                    )
                if path == "/autonomy":
                    return self._html(
                        200, _render_page("Autonomia", _autonomy_body(deps, token), nonce=nonce, token=token)
                    )
                if path == "/flow":
                    body = _flow_body(deps, token, clock())
                    return self._html(200, _render_page("Przepływ", body, nonce=nonce, token=token))
                if path.startswith("/trace/"):
                    return self._trace_route(path, params, token)
                if path == "/sse/progress":
                    return self._sse_progress(params, token)
                return self._html(404, "<h1>404</h1><p>Brak takiej strony.</p>")
            except Refused as e:
                return self._html(403, f"<h1>403</h1><p>{_escape(str(e))}</p>")
            except Exception as e:  # noqa: BLE001
                return self._html(500, f"<h1>500</h1><p>{_escape(type(e).__name__)}</p>")

        def _trace_route(self, path: str, params: Mapping[str, str], token: str) -> None:
            parts = path.split("/", 4)
            # /trace/<CHG>, /trace/<CHG>/file, /trace/<CHG>/diff
            if len(parts) < 3 or not parts[2]:
                return self._html(404, "<h1>404</h1>")
            change = parts[2]
            if not re.match(r"^CHG-[0-9]+$", change):
                return self._html(404, "<h1>404</h1>")
            if len(parts) == 3:
                return self._html(
                    200, _render_page(f"Ślad {change}", _trace_body(deps, change, token), nonce=nonce, token=token)
                )
            action = parts[3]
            if action == "file":
                if deps.checkout is None:
                    return self._html(404, "<h1>404</h1><p>brak klonu produktu</p>")
                try:
                    data = _read_artifact(deps, change, params.get("path", ""))
                except Refused as e:
                    return self._html(403, f"<h1>403</h1><p>{_escape(str(e))}</p>")
                return self._raw(200, data, "text/plain; charset=utf-8")
            if action == "diff":
                if deps.checkout is None:
                    return self._html(404, "<h1>404</h1><p>brak klonu produktu</p>")
                try:
                    state = deps.changes.get(change)
                except LookupError:
                    state = {"change": change, "dispatch": {}}
                diff = _diff_of_current_cut(state, deps.git, Path(deps.checkout))
                return self._raw(200, diff.encode("utf-8")[:FILE_SIZE_LIMIT], "text/plain; charset=utf-8")
            return self._html(404, "<h1>404</h1>")

        def _sse_progress(self, params: Mapping[str, str], token: str) -> None:
            change = params.get("change", "")
            if not re.match(r"^CHG-[0-9]+$", change):
                return self._html(404, "<h1>404</h1>")
            try:
                state = deps.changes.get(change)
            except LookupError:
                state = None
            log_path: Path | None = None
            if state is not None:
                raw = (state.get("dispatch") or {}).get("log") or ""
                if raw:
                    log_path = Path(raw)
            self.send_response(200)
            self.send_header("content-type", "text/event-stream; charset=utf-8")
            self.send_header("cache-control", "no-store")
            self.send_header("content-security-policy", _csp())
            self.send_header("x-content-type-options", "nosniff")
            self.end_headers()
            self.wfile.write(f"retry: {SSE_RETRY_MS}\n\n".encode())
            if log_path is None:
                self.wfile.write(_sse_line({"status": "no-progress"}, event="status"))
                return
            progress = dispatch_local.progress_path(log_path)
            if not progress.exists():
                progress.parent.mkdir(parents=True, exist_ok=True)
                progress.touch()
            # Śledź plik aż do rozłączenia klienta (max ok. 15 min; limit w testach: 1 iteracja).
            with progress.open("r", encoding="utf-8") as f:
                f.seek(0, 2)
                deadline = time.monotonic() + 15 * 60
                while time.monotonic() < deadline:
                    line = f.readline()
                    if line:
                        try:
                            row = json.loads(line)
                        except ValueError:
                            continue
                        try:
                            self.wfile.write(_sse_line(row, event="progress"))
                            self.wfile.flush()
                        except (BrokenPipeError, ConnectionResetError):
                            return
                    else:
                        try:
                            self.wfile.write(b": ping\n\n")
                            self.wfile.flush()
                        except (BrokenPipeError, ConnectionResetError):
                            return
                        time.sleep(POLL_SECONDS)

        def do_POST(self) -> None:  # noqa: N802
            url = urlsplit(self.path)
            # /inbox/<ID>/decide albo /problems/<PRB>/triage
            match = re.match(r"^/inbox/([A-Za-z0-9._-]{1,128})/decide$", url.path)
            triage = re.match(r"^/problems/(PRB-[0-9]{1,9})/triage$", url.path)
            stale_review = re.match(r"^/problems/(PRB-[0-9]{1,9})/stale$", url.path)  # DV6
            # DI Team T4 „Ask team”: pytanie, odpowiedź zapytanego i wcześniejsze zamknięcie (tylko w trybie suity).
            team = (
                re.match(r"^/inbox/([A-Za-z0-9._-]{1,128})/(ask|answer|close-ask|escalate|give-back)$", url.path)
                if suite is not None
                else None
            )
            reorder = re.match(r"^/discuss/([A-Za-z0-9._-]{1,128})/(up|down)$", url.path)  # T5
            logout = suite is not None and url.path == "/logout"
            if (
                match is None
                and triage is None
                and stale_review is None
                and team is None
                and reorder is None
                and not logout
            ):
                return self._html(404, "<h1>404</h1>")
            origin = self.headers.get("origin") or ""
            referer = self.headers.get("referer") or ""
            if origin and not origin.startswith(f"http://{host}:"):
                return self._html(403, "<h1>403</h1><p>origin</p>")
            if referer and not referer.startswith(f"http://{host}:"):
                return self._html(403, "<h1>403</h1><p>referer</p>")
            if suite is not None:
                # Sesja jedzie w ciasteczku, więc zmiana musi przyjść z tej strony: Origin albo Referer jest wymagany.
                if not origin and not referer:
                    return self._html(403, "<h1>403</h1><p>brak nagłówka Origin</p>")
                self.session = suite.session(self._cookie(SESSION_COOKIE))
                if logout:
                    suite.end(self._cookie(SESSION_COOKIE))
                    return self._redirect("/login", [f"{SESSION_COOKIE}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"])
                if self.session is None:
                    return self._redirect("/login")
                # Odpowiedzieć może każdy zapytany, także z rolą viewer; resztę zmian robi editor albo admin.
                if self.session.access != "decide" and not (team is not None and team.group(2) == "answer"):
                    return self._html(403, "<h1>403</h1><p>Decydować może rola editor albo admin w DI Decision.</p>")
            length = self.headers.get("content-length", "")
            if not length.isdigit() or int(length) > MAX_BODY:
                return self._html(413, "<h1>413</h1><p>treść za duża</p>")
            body = self.rfile.read(int(length))
            try:
                fields = parse_qs(body.decode("utf-8"), keep_blank_values=True, max_num_fields=100)
            except (UnicodeDecodeError, ValueError):
                return self._html(400, "<h1>400</h1><p>zła treść</p>")

            def one(name: str) -> str:
                values = fields.get(name) or []
                return values[0] if values else ""

            if suite is None and not _token_ok(token, one("t")):
                return self._html(404, "<h1>404</h1>")
            if team is not None:
                return self._team(team.group(1), team.group(2), fields, one)
            if reorder is not None:
                entries = agenda.build(
                    deps.inbox.items(status="open"), deps.consults, order=deps.agenda.get(), now=clock()
                )
                deps.agenda.set(agenda.moved([e["item_id"] for e in entries], reorder.group(1), reorder.group(2)))
                self.send_response(303)
                self.send_header("location", f"/discuss?t={token}" if suite is None else "/discuss")
                self.send_header("content-length", "0")
                self.end_headers()
                return None
            if triage is not None:
                return self._triage(triage.group(1), one)
            if stale_review is not None:
                return self._stale(stale_review.group(1), one)
            if match is None:  # pragma: no cover — jedno z dwóch dopasowań jest zawsze ustawione
                return self._html(404, "<h1>404</h1>")
            item_id = match.group(1)
            try:
                item = deps.inbox.get(item_id)
            except LookupError:
                return self._html(404, "<h1>404</h1>")
            holder = deps.escalations.holder(item_id)
            if holder is not None and (self.session is None or self.session.sub != holder):
                to = (deps.escalations.view(item_id) or {}).get("to", {}).get("name", holder)
                return self._html(
                    403, f"<h1>403</h1><p>This item was escalated to {_escape(to)}; only they decide.</p>"
                )
            loaded_at = one("loaded_at")
            if loaded_at and loaded_at != item.get("received_at"):
                msg = "Pozycja zmieniła się od czasu wczytania strony. Odśwież i spróbuj ponownie."
                return self._html(409, f"<h1>409</h1><p>{msg}</p>")
            outcome = one("outcome") or None
            changed = _artifact_changed(deps, item) if item.get("kind") == "gate" and outcome == "approved" else None
            if changed:
                return self._html(409, f"<h1>409</h1><p>{_escape(changed)}</p>")
            statement = _sanitize_text(one("statement"), limit=800)
            why = _sanitize_text(one("why"), limit=2000)
            if not statement or not why:
                return self._html(400, "<h1>400</h1><p>Brak treści decyzji albo powodu.</p>")
            try:
                answers = _collect_answers(item, fields)
            except Refused as e:
                return self._html(403, f"<h1>403</h1><p>{_escape(str(e))}</p>")
            draft: Decision = {
                "statement": statement,
                "why": why,
                "decided_by": self._decider(),
                **self._decider_id(),
                "decided_at": clock().date().isoformat(),
                # Kontrakt pdi: `draft_edited` tylko przy `drafted_by: ai` (decision.schema.json allOf, 2026-11-06).
                "drafted_by": "human",
                "kind": "other",
                "source": {
                    "kind": "console",
                    "url": f"http://{host}:{port}/inbox/{item_id}",
                    "excerpt": _sanitize_text(item.get("summary"), limit=200),
                }
                if one("via") != "agenda"
                else {  # T5: decyzja ze spotkania, z agendy „Discuss with team”
                    "kind": "meeting",
                    "url": f"http://{host}:{port}/discuss",
                    "excerpt": f"Discuss with team, {clock().date().isoformat()}: "
                    + _sanitize_text(item.get("summary"), limit=150),
                },
            }
            if answers is not None:
                draft["answers"] = answers
            consulted = deps.consults.consulted(item_id) if suite is not None else None
            if consulted:
                draft["consulted"] = consulted  # kogo zapytano i co odpowiedział (kontrakt 0.26.0)
            try:
                result = deps.inbox.decide(item_id, draft, outcome=outcome)
            except (InvalidDecision, ItemClosed) as e:
                return self._html(409, f"<h1>409</h1><p>{_escape(str(e))}</p>")
            except ItemNotFound as e:
                return self._html(404, f"<h1>404</h1><p>{_escape(str(e))}</p>")
            if consulted:
                deps.consults.close(item_id)
            back = f"/inbox?t={given_token(given=one('t'))}"
            warning = result.get("warning")
            if result.get("decision") is None:  # pozycja zamknięta bez wpisu w rejestrze (pr_ready, odrzucony szkic)
                info = f"<h1>Pozycja zamknięta</h1><p>{_escape(item_id)}: {_escape(result['item'].get('outcome'))}</p>"
            else:
                info = (
                    f"<h1>Decyzja zapisana</h1><p>{_escape(result['decision']['id'])}: "
                    f"{_escape(result['decision']['statement'])}</p>"
                )
            if warning:
                info += f"<p class='warn'>{_escape(warning)}</p>"
            info += f'<p><a href="{back}">wróć do skrzynki</a></p>'
            return self._html(200, _render_page("Decyzja zapisana", info, nonce=nonce, token=token))

        def _stale(self, problem_id: str, one: Callable[[str], str]) -> None:
            """DV6: decyzja o porzuconym zgłoszeniu — ten sam `ProblemStore.review_stale` co MCP."""
            outcome = one("outcome")
            statement = _sanitize_text(one("statement"), limit=800)
            why = _sanitize_text(one("why"), limit=2000)
            if not statement or not why:
                return self._html(400, "<h1>400</h1><p>Brak treści decyzji albo powodu.</p>")
            draft: Decision = {
                "statement": statement,
                "why": why,
                "decided_by": self._decider(),
                **self._decider_id(),
                "decided_at": clock().date().isoformat(),
                "drafted_by": "human",
                "kind": "triage",
                "source": {"kind": "console", "url": f"http://{host}:{port}/inbox", "excerpt": problem_id},
            }
            try:
                result = deps.inbox.problems.review_stale(problem_id, outcome, draft)
            except InvalidDecision as e:
                return self._html(409, f"<h1>409</h1><p>{_escape(str(e))}</p>")
            except LookupError as e:
                return self._html(404, f"<h1>404</h1><p>{_escape(str(e))}</p>")
            decision = result.get("decision") or {}
            return self._html(
                200,
                f"<h1>Decyzja zapisana</h1><p>{_escape(decision.get('id'))}: {_escape(decision.get('statement'))}</p>",
            )

        def _triage(self, problem_id: str, one: Callable[[str], str]) -> None:
            """Triaż zgłoszenia przyciskiem: ten sam `ProblemStore.triage` co narzędzie MCP `triage_problem`."""
            outcome = one("outcome")
            if outcome not in ("accepted", "rejected"):
                return self._html(400, "<h1>400</h1><p>outcome: accepted albo rejected.</p>")
            statement = _sanitize_text(one("statement"), limit=800)
            why = _sanitize_text(one("why"), limit=2000)
            if not statement or not why:
                return self._html(400, "<h1>400</h1><p>Brak treści decyzji albo powodu.</p>")
            reason = one("rejection_reason") or None
            if outcome == "rejected" and reason not in {v for v, _ in REJECTION_REASONS}:
                return self._html(409, "<h1>409</h1><p>Odrzucenie wymaga powodu z listy.</p>")
            no_code = None
            if outcome == "rejected" and reason == "no_code":
                kind, how = one("no_code_kind"), _sanitize_text(one("no_code_how"), limit=2000)
                if kind not in {v for v, _ in NO_CODE_KINDS} or not how:
                    return self._html(409, "<h1>409</h1><p>„Bez kodu” wymaga rodzaju i opisu, co zrobić.</p>")
                no_code = {"kind": kind, "how": how}
            draft: Decision = {
                "statement": statement,
                "why": why,
                "decided_by": self._decider(),
                **self._decider_id(),
                "decided_at": clock().date().isoformat(),
                "drafted_by": "human",
                "kind": "triage",
                "source": {"kind": "console", "url": f"http://{host}:{port}/inbox", "excerpt": problem_id},
            }
            try:
                result = deps.inbox.problems.triage(
                    problem_id,
                    outcome,
                    draft,
                    rejection_reason=reason if outcome == "rejected" else None,
                    rejection_note=why if outcome == "rejected" else None,
                    no_code=no_code,
                )
            except InvalidDecision as e:
                return self._html(409, f"<h1>409</h1><p>{_escape(str(e))}</p>")
            except LookupError as e:
                return self._html(404, f"<h1>404</h1><p>{_escape(str(e))}</p>")
            decision = result.get("decision") or {}
            change = result.get("change") or (result.get("problem") or {}).get("change")
            info = (
                f"<h1>Decyzja zapisana</h1><p>{_escape(decision.get('id'))}: {_escape(decision.get('statement'))}</p>"
            )
            if change:
                info += f'<p>Zmiana <a href="/trace/{_escape(change)}?t={_escape(token)}">{_escape(change)}</a>.</p>'
            info += f'<p><a href="/inbox?t={_escape(token)}">wróć do skrzynki</a></p>'
            return self._html(200, _render_page("Decyzja zapisana", info, nonce=nonce, token=token))

        def _team(self, item_id: str, action: str, fields: Mapping[str, list[str]], one: Callable[[str], str]) -> None:
            """„Ask team” (T4): `ask` i `close-ask` — decydent, `answer` — zapytany; potem z powrotem do skrzynki."""
            assert self.session is not None  # noqa: S101 — trasa tylko w trybie suity, po sprawdzeniu sesji
            me = consult.Person(sub=self.session.sub, name=self.session.name)
            try:
                item = deps.inbox.get(item_id)
            except LookupError:
                return self._html(404, "<h1>404</h1>")
            if item.get("status") != "open":
                return self._html(409, "<h1>409</h1><p>This item is already decided.</p>")
            try:
                if action == "ask":
                    known = {p.sub: p for p in deps.people.all()}
                    asked = [known[k[4:]] for k in fields if k.startswith("ask_") and k[4:] in known]
                    hours = int(one("hours")) if one("hours").isdigit() else 0
                    c = deps.consults.ask(
                        item_id, decider=me, asked=asked, options=list(_options_for(item["kind"])), hours=hours
                    )
                    # T6: zapytani dostają wiadomość w Slacku (DI Channels); błąd wysyłki nie cofa pytania.
                    channels = deps.inbox.channels
                    if channels.url:
                        at = deps.registry.now().astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
                        deps.consults.record_notice(item_id, team_notify.notify_asked(channels, item, c, at=at))
                elif action == "answer":
                    deps.consults.answer(item_id, me, option=one("option"), reason=one("reason"))
                elif action in ("escalate", "give-back"):
                    return self._escalate(item, action, me, one)
                else:
                    view = deps.consults.view(item_id, me.sub)
                    if view is None or view["decider_sub"] != me.sub:
                        return self._html(403, "<h1>403</h1><p>Only the person who asked can close the question.</p>")
                    deps.consults.close(item_id)
            except consult.ConsultError as e:
                status = 403 if "not asked" in str(e) else 409
                return self._html(status, f"<h1>{status}</h1><p>{_escape(str(e))}</p>")
            self.send_response(303)
            self.send_header("location", "/inbox")
            self.send_header("content-length", "0")
            self.end_headers()

        def _escalate(self, item: dict[str, Any], action: str, me: consult.Person, one: Callable[[str], str]) -> None:
            """„Escalate” (T7, OM2): przekazanie decyzji o tej sprawie albo jej oddanie przez adresata."""
            item_id = item["id"]
            try:
                if action == "escalate":
                    to_sub = one("to")
                    target = deps.people.get(to_sub)
                    to = consult.Person(sub=to_sub, name=str((target or {}).get("name") or to_sub))
                    e = deps.escalations.escalate(
                        item, by=me, to=to, reason=one("reason"), question=one("question"), people=deps.people
                    )
                    view = deps.consults.view(item_id, me.sub)
                    if view is not None and view["status"] == "open":
                        deps.consults.close(item_id)  # pytanie do zespołu zamyka się z tym, co zebrano
                    channels = deps.inbox.channels
                    if channels.url:
                        at = deps.registry.now().astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
                        deps.escalations.record_notice(item_id, team_notify.notify_escalated(channels, item, e, at=at))
                else:
                    deps.escalations.give_back(item_id, me, note=one("note"))
            except escalate.EscalationError as err:
                status = 403 if "only the person" in str(err) else 409
                return self._html(status, f"<h1>{status}</h1><p>{_escape(str(err))}</p>")
            self.send_response(303)
            self.send_header("location", "/inbox")
            self.send_header("content-length", "0")
            self.end_headers()
            return None

        def _html(self, status: int, body: str) -> None:
            page = body if body.startswith("<!doctype") else _render_page("pdi", body, nonce=nonce)
            if self.session is not None:
                # Kto jest zalogowany (tryb suity) i wylogowanie — formularz bez skryptu, ten sam Origin co reszta.
                level = "decyduje" if self.session.access == "decide" else "tylko odczyt"
                who = (
                    f'<div class="who">{_escape(self.session.name)} · {level} '
                    '<form method="post" action="/logout" style="display:inline">'
                    '<button type="submit">Wyloguj</button></form></div>'
                )
                if self.session.access != "decide":
                    # Rola viewer: przyciski decyzji schowane (serwer i tak odmawia, 403), z wyjaśnieniem.
                    who += (
                        '<p class="read-only">Masz rolę viewer w DI Decision: decyzje podejmuje editor albo admin.</p>'
                        "<style>form[action*='/decide'],form[action*='/triage'],form[action*='/stale']{display:none}</style>"
                    )
                page = page.replace("<main>", f"<main>{who}", 1)
            data = page.encode("utf-8")
            self.send_response(status)
            self.send_header("content-type", "text/html; charset=utf-8")
            self.send_header("content-length", str(len(data)))
            self.send_header("content-security-policy", _csp())
            self.send_header("x-frame-options", "DENY")
            self.send_header("referrer-policy", "same-origin")
            self.send_header("x-content-type-options", "nosniff")
            self.end_headers()
            self.wfile.write(data)

        def _raw(self, status: int, data: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("content-type", content_type)
            self.send_header("content-length", str(len(data)))
            self.send_header("content-security-policy", _csp())
            self.send_header("x-frame-options", "DENY")
            self.send_header("referrer-policy", "same-origin")
            self.send_header("x-content-type-options", "nosniff")
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            path = urlsplit(self.path).path
            sys.stderr.write(f"pdi-console: {self.command} {path} {args[1] if len(args) > 1 else ''}\n")

    return ThreadedHTTPServer((host, port), Handler)


def given_token(*, given: str) -> str:
    """Pomocniczo w widokach: zwraca `given` (do użycia jako wartość `?t=`), żeby mypy nie marudził."""
    return given


def _collect_answers(item: dict[str, Any], fields: Mapping[str, list[str]]) -> list[dict[str, str]] | None:
    """Odpowiedzi na pytania pozycji skrzynki; obsługuje stringi i kształt N19 (options/other)."""
    questions = item.get("questions") or []
    if not questions:
        return None
    collected: list[dict[str, str]] = []
    for i, q in enumerate(questions):
        raw_values = fields.get(f"answer_{i}") or []
        raw = raw_values[0] if raw_values else ""
        if not raw:
            raise Refused(f"brak odpowiedzi na pytanie {i + 1}")
        if isinstance(q, dict) and isinstance(q.get("options"), list):
            text = q.get("question") or ""
            if raw == "__other__":
                if not q.get("other"):
                    raise Refused(f"pytanie {i + 1} nie dopuszcza „inne”")
                other_values = fields.get(f"answer_{i}_other") or []
                other = other_values[0] if other_values else ""
                answer = _sanitize_text(other, limit=800)
                if not answer:
                    raise Refused(f"pytanie {i + 1}: brak treści „inne”")
            else:
                known = {str(opt.get("value")): opt for opt in q["options"] if isinstance(opt, dict)}
                if raw not in known:
                    raise Refused(f"pytanie {i + 1}: nieznana opcja")
                option = known[raw]
                answer = _sanitize_text(option.get("label") or option.get("value"), limit=800)
            collected.append({"question": str(text), "answer": answer})
        else:
            collected.append({"question": str(q), "answer": _sanitize_text(raw, limit=800)})
    return collected


def main() -> None:
    registry_path = os.environ.get("PDI_REGISTRY_PATH")
    if not registry_path:
        raise SystemExit("Brak PDI_REGISTRY_PATH — katalog rejestru pdi.")
    try:
        suite_config = suite_login.config_from_env(os.environ)
    except ValueError as e:
        raise SystemExit(str(e)) from e
    token = os.environ.get("PDI_CONSOLE_TOKEN") or ""
    if not token and suite_config is None:
        raise SystemExit("Brak PDI_CONSOLE_TOKEN — token sesji konsoli (albo PDI_SUITE_* — logowanie przez suitę).")
    port = int(os.environ.get("PDI_CONSOLE_PORT", str(DEFAULT_PORT)))
    try:
        registry = Registry(Path(registry_path))
    except (OSError, ValueError) as e:
        raise SystemExit(str(e)) from e
    checkout_raw = os.environ.get("PDI_DISPATCH_CHECKOUT")
    checkout = Path(checkout_raw) if checkout_raw else None
    deps = Deps(registry, checkout=checkout, inbox=inbox_from_env(registry))
    suite = suite_login.SuiteLogin(suite_config) if suite_config is not None else None
    server = make_server(deps, token=token or secrets.token_urlsafe(32), port=port, suite=suite)
    sys.stderr.write(f"pdi-console: nasłuchuje na http://{DEFAULT_HOST}:{port}/\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
