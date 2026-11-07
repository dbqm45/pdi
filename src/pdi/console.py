"""Konsola pdi w przeglądarce na Macu — proces `pdi-console` obok `pdi-receiver` (Z3-lokalnie, A7, DZ14, DZ18).

Serwis startowany przez `sdlc up` (zatrzymywany `sdlc down`, pokazywany w `sdlc status`, otwierany `sdlc open`),
nasłuchuje **tylko na 127.0.0.1**, z tokenem sesji w URL (jak formularz zgłoszeń: `src/pdi/receiver.py` +
`src/pdi/form.py`). Pokazuje tablicę w trzech pasach (Z7a), ślad zmiany z panelem „Pliki” i bocznym postępem
na żywo (DZ18), skrzynkę z przyciskami decyzji i read-only rejestr/autonomię. Nic nie pisze do klonu produktu;
pliki pokazuje tylko z białej listy, bez symlinków i bez treści, która wygląda na sekret.

Bezpieczeństwo:

- Nasłuch na `127.0.0.1` z hardcode; port z `PDI_CONSOLE_PORT` (domyślnie 8788).
- Token w URL (`?t=<token>`) i w treści POST; brak albo niezgodność → 404 (jak w formularzu, nie zdradzamy istnienia).
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
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from pdi import autonomy, dispatch_local, pr_state
from pdi import trace as trace_mod
from pdi.changes import ChangeStore
from pdi.dispatch import DispatchConfig
from pdi.impact import ShipScopeConfig
from pdi.inbox import Inbox, ItemClosed, ItemNotFound
from pdi.notify import NotifyConfig, ReporterNotifyConfig
from pdi.registry import Decision, InvalidDecision, Registry

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8788
MAX_BODY = 128 * 1024
POLL_SECONDS = 0.5
FILE_SIZE_LIMIT = 256 * 1024
BINARY_PEEK = 8 * 1024
SSE_RETRY_MS = 2000
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
    pages = (("board", "Tablica"), ("inbox", "Skrzynka"), ("decisions", "Decyzje"), ("autonomy", "Autonomia"))
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
                progress_line = f"<small>{_escape(progress['message'])}{cost_label}</small>"
            link = f"/trace/{chg}?t={_escape(token)}"
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
        "</div>"
        f"<aside class='side'>{progress_html}</aside>"
        "</div>"
    )


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


def _inbox_body(deps: Deps, token: str) -> str:
    items = deps.inbox.items(status="open")
    rows = []
    for item in items:
        lane = _lane_of(item.get("gate") or item.get("kind"), None, kind=item.get("kind"))
        questions = item.get("questions") or []
        q_html = _render_questions(item["id"], questions)
        action_buttons = _action_buttons_for(item["kind"])
        link = f"/inbox/{_escape(item['id'])}?t={_escape(token)}"
        rows.append(
            f'<section class="card">'
            f'<h2><a href="{link}">{_escape(item["id"])}</a> '
            f'<span class="pill">pas {lane}</span> '
            f'<span class="pill">{_escape(item["kind"])}</span> '
            f'<span class="pill open">czeka</span></h2>'
            f"<p><strong>{_escape(item.get('summary'))}</strong></p>"
            f'<form method="post" action="/inbox/{_escape(item["id"])}/decide?t={_escape(token)}">'
            f'<input type="hidden" name="t" value="{_escape(token)}">'
            f'<input type="hidden" name="loaded_at" value="{_escape(item["received_at"])}">'
            f"{q_html}"
            '<div class="row"><label>Treść decyzji (statement)</label>'
            '<textarea name="statement" required maxlength="800"></textarea></div>'
            '<div class="row"><label>Dlaczego (why)</label>'
            '<textarea name="why" required maxlength="2000"></textarea></div>'
            f"{action_buttons}"
            "</form></section>"
        )
    triage = _triage_cards(deps, token)
    body = "".join(rows) if rows else "<p><small>brak pozycji bramek i ocen</small></p>"
    return f"<h1>Skrzynka</h1>{triage}{body}"


TRIAGE_OPEN = ("new", "clarifying", "ready_for_triage")
REJECTION_REASONS = (
    ("out_of_strategy", "poza strategią"),
    ("works_as_designed", "działa zgodnie z założeniem"),
    ("cost_disproportionate", "koszt nieproporcjonalny"),
    ("already_exists", "już istnieje"),
    ("out_of_scope_recorded", "poza zakresem (zapisane)"),
    ("other", "inny powód"),
)


def _triage_cards(deps: Deps, token: str) -> str:
    """Zgłoszenia z formularza czekające na triaż (ta sama ścieżka co `triage_problem` w MCP)."""
    waiting = [p for p in deps.inbox.problems.all() if p.get("status") in TRIAGE_OPEN]
    if not waiting:
        return ""
    t = _escape(token)
    reasons = "".join(f'<option value="{v}">{_escape(label)}</option>' for v, label in REJECTION_REASONS)
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


# --- pliki artefaktów i diff ---


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
) -> ThreadedHTTPServer:
    """Serwer HTTP konsoli; `port=0` wybiera wolny port (do testów)."""
    nonce = secrets.token_urlsafe(16)

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
        def do_GET(self) -> None:  # noqa: N802
            url = urlsplit(self.path)
            params = {k: v[-1] for k, v in parse_qs(url.query).items() if v}
            given = params.get("t", "")
            if not _token_ok(token, given):
                return self._html(404, "<h1>404</h1><p>Brak takiej strony.</p>")

            path = url.path
            try:
                if path == "/" or path == "/board":
                    return self._html(200, _render_page("Tablica", _board_body(deps, token), nonce=nonce, token=token))
                if path == "/inbox":
                    return self._html(200, _render_page("Skrzynka", _inbox_body(deps, token), nonce=nonce, token=token))
                if path == "/decisions":
                    return self._html(
                        200, _render_page("Decyzje", _decisions_body(deps, token), nonce=nonce, token=token)
                    )
                if path == "/autonomy":
                    return self._html(
                        200, _render_page("Autonomia", _autonomy_body(deps, token), nonce=nonce, token=token)
                    )
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
            if match is None and triage is None:
                return self._html(404, "<h1>404</h1>")
            origin = self.headers.get("origin") or ""
            referer = self.headers.get("referer") or ""
            if origin and not origin.startswith(f"http://{host}:"):
                return self._html(403, "<h1>403</h1><p>origin</p>")
            if referer and not referer.startswith(f"http://{host}:"):
                return self._html(403, "<h1>403</h1><p>referer</p>")
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

            if not _token_ok(token, one("t")):
                return self._html(404, "<h1>404</h1>")
            if triage is not None:
                return self._triage(triage.group(1), one)
            if match is None:  # pragma: no cover — jedno z dwóch dopasowań jest zawsze ustawione
                return self._html(404, "<h1>404</h1>")
            item_id = match.group(1)
            try:
                item = deps.inbox.get(item_id)
            except LookupError:
                return self._html(404, "<h1>404</h1>")
            loaded_at = one("loaded_at")
            if loaded_at and loaded_at != item.get("received_at"):
                msg = "Pozycja zmieniła się od czasu wczytania strony. Odśwież i spróbuj ponownie."
                return self._html(409, f"<h1>409</h1><p>{msg}</p>")
            outcome = one("outcome") or None
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
                "decided_by": os.environ.get("PDI_DECIDED_BY") or "console",
                "decided_at": clock().date().isoformat(),
                # Kontrakt pdi: `draft_edited` tylko przy `drafted_by: ai` (decision.schema.json allOf, 2026-11-06).
                "drafted_by": "human",
                "kind": "other",
                "source": {
                    "kind": "console",
                    "url": f"http://{host}:{port}/inbox/{item_id}",
                    "excerpt": _sanitize_text(item.get("summary"), limit=200),
                },
            }
            if answers is not None:
                draft["answers"] = answers
            try:
                result = deps.inbox.decide(item_id, draft, outcome=outcome)
            except (InvalidDecision, ItemClosed) as e:
                return self._html(409, f"<h1>409</h1><p>{_escape(str(e))}</p>")
            except ItemNotFound as e:
                return self._html(404, f"<h1>404</h1><p>{_escape(str(e))}</p>")
            back = f"/inbox?t={given_token(given=one('t'))}"
            warning = result.get("warning")
            info = (
                f"<h1>Decyzja zapisana</h1><p>{_escape(result['decision']['id'])}: "
                f"{_escape(result['decision']['statement'])}</p>"
            )
            if warning:
                info += f"<p class='warn'>{_escape(warning)}</p>"
            info += f'<p><a href="{back}">wróć do skrzynki</a></p>'
            return self._html(200, _render_page("Decyzja zapisana", info, nonce=nonce, token=token))

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
            draft: Decision = {
                "statement": statement,
                "why": why,
                "decided_by": os.environ.get("PDI_DECIDED_BY") or "console",
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

        def _html(self, status: int, body: str) -> None:
            page = body if body.startswith("<!doctype") else _render_page("pdi", body, nonce=nonce)
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
    token = os.environ.get("PDI_CONSOLE_TOKEN") or ""
    if not token:
        raise SystemExit("Brak PDI_CONSOLE_TOKEN — token sesji konsoli.")
    port = int(os.environ.get("PDI_CONSOLE_PORT", str(DEFAULT_PORT)))
    try:
        registry = Registry(Path(registry_path))
    except (OSError, ValueError) as e:
        raise SystemExit(str(e)) from e
    checkout_raw = os.environ.get("PDI_DISPATCH_CHECKOUT")
    checkout = Path(checkout_raw) if checkout_raw else None
    deps = Deps(registry, checkout=checkout, inbox=inbox_from_env(registry))
    server = make_server(deps, token=token, port=port)
    sys.stderr.write(f"pdi-console: nasłuchuje na http://{DEFAULT_HOST}:{port}/\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
