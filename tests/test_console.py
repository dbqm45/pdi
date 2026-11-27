"""Konsola pdi (Z3-lokalnie, A7, DZ14, DZ18): strony, decyzje przyciskami, panel „Pliki”, SSE postępu, CSP.

Serwer stawiamy na losowym porcie (`port=0`), w wątku; klient — `urllib.request`. Nie dotykamy sieci poza localhost.
"""

from __future__ import annotations

import json
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from pdi import console, dispatch_local
from pdi.inbox import Inbox
from pdi.registry import Registry

TOKEN = "testowy-token-sesji-konsoli"  # noqa: S105 — nazwa zmiennej, nie hasło


@pytest.fixture
def registry(tmp_path: Path) -> Registry:
    r = Registry(tmp_path / "registry")
    r.root.mkdir(parents=True, exist_ok=True)
    return r


def _git(repo: Path, *args: str) -> None:
    import subprocess

    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
           "HOME": str(repo), "PATH": "/usr/bin:/bin:/usr/local/bin"}  # fmt: skip
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, env=env)  # noqa: S603, S607


def _commit_on(repo: Path, branch: str, files: dict[str, bytes], *, link: tuple[str, str] | None = None) -> None:
    """Commit artefaktów CHG-1 na gałęzi fazy; katalog roboczy wraca na `main` (jak klon po przebiegu)."""
    _git(repo, "switch", "-q", "-C", branch, "main")
    folder = repo / "docs/project/changes/CHG-1"
    folder.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (folder / name).write_bytes(data)
    if link:
        (folder / link[0]).symlink_to(link[1])
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", f"phase {branch}")
    _git(repo, "switch", "-q", "main")


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    """Klon produktu jak po fazie: artefakty tylko na gałęzi `pdi/CHG-1-intent`, katalog roboczy na `main`."""
    co = tmp_path / "sklep"
    co.mkdir()
    _git(co, "init", "-q", "-b", "main")
    (co / "README.md").write_text("produkt\n", encoding="utf-8")
    _git(co, "add", "-A")
    _git(co, "commit", "-q", "-m", "init")
    _commit_on(co, "pdi/CHG-1-intent", {"intent.md": b"# intent\n", "requirements.md": b"# requirements\n",
                                        "plan.md": b"# plan\n"})  # fmt: skip
    return co


class FakeGit:
    def __init__(self, result: tuple[int, str] = (0, "diff --git a/file b/file\n")) -> None:
        self.result = result
        self.calls: list[list[str]] = []

    def __call__(self, argv: list[str], cwd: Path) -> tuple[int, str]:
        self.calls.append(argv)
        return self.result


def _write_change(registry: Registry, change: str, **state: Any) -> None:
    (registry.root / "changes").mkdir(parents=True, exist_ok=True)
    base = {"change": change, "status": "open", "approved": {}, "waiting": [], "history": []}
    base.update(state)
    (registry.root / "changes" / f"{change}.yaml").write_text(json.dumps(base), encoding="utf-8")


def _write_inbox_gate(
    registry: Registry, *, change: str = "CHG-1", gate: str = "B2", questions: Any = None, item_id: str = "evt-1"
) -> dict[str, Any]:
    (registry.root / "inbox").mkdir(parents=True, exist_ok=True)
    item = {
        "id": item_id,
        "kind": "gate",
        "status": "open",
        "change": change,
        "source": "tf",
        "release": None,
        "summary": f"Prośba o bramkę {gate}",
        "received_at": "2026-11-06T10:00:00Z",
        "event": {
            "id": item_id,
            "type": "gate.requested",
            "occurred_at": "2026-11-06T10:00:00Z",
            "source": "tf",
            "contract_version": "0.11.0",
            "payload": {"change": change, "gate": gate},
        },
        "gate": gate,
        "missing_before": [],
    }
    if questions is not None:
        item["questions"] = questions
    (registry.root / "inbox" / f"{item_id}.yaml").write_text(json.dumps(item), encoding="utf-8")
    return item


def _serve(deps: console.Deps, *, token: str = TOKEN) -> tuple[console.ThreadedHTTPServer, str]:
    server = console.make_server(deps, token=token, port=0)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{port}"


def _get(url: str) -> tuple[int, bytes, dict[str, str]]:
    req = urllib.request.Request(url, method="GET")  # noqa: S310 — localhost testowy
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:  # noqa: S310 — localhost testowy
            return int(resp.status), resp.read(), {k.lower(): v for k, v in resp.headers.items()}
    except urllib.error.HTTPError as e:
        return int(e.code), e.read(), {k.lower(): v for k, v in e.headers.items()}


def _post(url: str, data: dict[str, Any], *, extra_headers: dict[str, str] | None = None) -> tuple[int, bytes]:
    body = urllib.parse.urlencode(data).encode()
    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "origin": f"http://127.0.0.1:{urllib.parse.urlsplit(url).port}",
    }
    headers.update(extra_headers or {})
    req = urllib.request.Request(url, data=body, method="POST", headers=headers)  # noqa: S310
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:  # noqa: S310
            return int(resp.status), resp.read()
    except urllib.error.HTTPError as e:
        return int(e.code), e.read()


def test_board_lists_each_change_in_its_lane(registry: Registry) -> None:
    _write_change(
        registry, "CHG-1", waiting=["B2"], dispatch={"mode": "local", "status": "done", "phase": "requirements"}
    )
    _write_change(registry, "CHG-2", waiting=["B5"], dispatch={"mode": "local", "status": "done", "phase": "delivery"})
    _write_change(registry, "CHG-3", waiting=["B6"])
    deps = console.Deps(registry, checkout=None)
    server, url = _serve(deps)
    try:
        status, body, headers = _get(f"{url}/board?t={TOKEN}")
        assert status == 200
        page = body.decode("utf-8")
        lane1 = page.split('class="lane l1"')[1].split('class="lane')[0]
        lane2 = page.split('class="lane l2"')[1].split('class="lane')[0]
        lane3 = page.split('class="lane l3"')[1]
        assert "CHG-1" in lane1 and "CHG-2" in lane2 and "CHG-3" in lane3
        assert "content-security-policy" in headers
        assert "script-src 'self' 'nonce-" in headers["content-security-policy"]
    finally:
        server.shutdown()


@pytest.mark.parametrize(
    ("waiting", "expected"),
    [
        pytest.param(["design-review"], "czeka na bramkę design-review", id="bramka-otwarta"),
        pytest.param([], "bramka design-review rozstrzygnięta", id="bramka-rozstrzygnieta"),
    ],
)
def test_board_card_separates_phase_from_progress(registry: Registry, waiting: list[str], expected: str) -> None:
    progress = {"phase": "design", "status": "waiting_gate", "message": "design-review", "cost_usd": 0.42}
    _write_change(
        registry,
        "CHG-4",
        waiting=waiting,
        dispatch={"mode": "local", "status": "done", "phase": "design", "last_progress": progress},
    )
    deps = console.Deps(registry, checkout=None)
    server, url = _serve(deps)
    try:
        _, body, _ = _get(f"{url}/board?t={TOKEN}")
        card = body.decode("utf-8").split('<span class="chg">CHG-4</span>')[1].split("</li>")[0]
        assert '<span class="phase">design</span>' in card
        assert f'<div class="progress"><small>{expected} · 0.42 USD</small></div>' in card
    finally:
        server.shutdown()


def test_board_requires_token(registry: Registry) -> None:
    deps = console.Deps(registry, checkout=None)
    server, url = _serve(deps)
    try:
        status, _, _ = _get(f"{url}/board")
        assert status == 404
        status, _, _ = _get(f"{url}/board?t=inny")
        assert status == 404
    finally:
        server.shutdown()


def test_inbox_page_renders_questions_as_text_fields(registry: Registry) -> None:
    _write_inbox_gate(registry, questions=["Kto odpowiada?", "Jaki jest próg?"])
    deps = console.Deps(registry, checkout=None)
    server, url = _serve(deps)
    try:
        status, body, _ = _get(f"{url}/inbox?t={TOKEN}")
        page = body.decode("utf-8")
        assert status == 200
        assert 'name="answer_0"' in page and 'name="answer_1"' in page
        assert 'name="statement"' in page and 'name="why"' in page
        assert 'name="outcome" value="approved"' in page
    finally:
        server.shutdown()


def test_inbox_page_renders_options_as_radio_for_n19(registry: Registry) -> None:
    _write_inbox_gate(
        registry,
        questions=[
            {
                "question": "Kto odpowiada?",
                "options": [{"value": "ops", "label": "Operacje"}, {"value": "dev", "label": "Deweloperzy"}],
                "recommended": "dev",
                "other": True,
            },
        ],
    )
    deps = console.Deps(registry, checkout=None)
    server, url = _serve(deps)
    try:
        _, body, _ = _get(f"{url}/inbox?t={TOKEN}")
        page = body.decode("utf-8")
        assert 'type="radio" name="answer_0" value="ops"' in page
        assert 'type="radio" name="answer_0" value="dev"' in page and " checked" in page
        assert 'value="__other__"' in page and 'name="answer_0_other"' in page
    finally:
        server.shutdown()


def test_decide_via_button_goes_through_inbox_decide(registry: Registry, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_change(registry, "CHG-1", waiting=["B2"])
    item = _write_inbox_gate(registry, questions=["Kto odpowiada?"])
    deps = console.Deps(registry, checkout=None)
    monkeypatch.setattr(deps.inbox, "_check_pr", lambda item: None)
    server, url = _serve(deps)
    try:
        status, _ = _post(
            f"{url}/inbox/{item['id']}/decide?t={TOKEN}",
            {
                "t": TOKEN,
                "loaded_at": item["received_at"],
                "statement": "Odpowiada zespół Ops.",
                "why": "Bo oni mają dyżur 24/7.",
                "outcome": "approved",
                "answer_0": "Ops",
            },
        )
        assert status == 200
        decided_items = Inbox(registry).items(status="decided")
        assert len(decided_items) == 1
        decision_id = decided_items[0]["decision"]
        decision = registry.get(decision_id)
        assert decision["source"]["kind"] == "console"
        assert decision["drafted_by"] == "human"
        assert decision["answers"] == [{"question": "Kto odpowiada?", "answer": "Ops"}]
    finally:
        server.shutdown()


def test_decide_refused_without_token(registry: Registry) -> None:
    item = _write_inbox_gate(registry, questions=None)
    deps = console.Deps(registry, checkout=None)
    server, url = _serve(deps)
    try:
        status, _ = _post(f"{url}/inbox/{item['id']}/decide", {"statement": "x", "why": "x", "outcome": "approved"})
        assert status == 404
    finally:
        server.shutdown()


def test_decide_refused_when_item_changed_since_load(registry: Registry) -> None:
    _write_change(registry, "CHG-1", waiting=["B2"])
    item = _write_inbox_gate(registry, questions=None)
    deps = console.Deps(registry, checkout=None)
    server, url = _serve(deps)
    try:
        status, body = _post(
            f"{url}/inbox/{item['id']}/decide?t={TOKEN}",
            {"t": TOKEN, "loaded_at": "2020-01-01T00:00:00Z", "statement": "x", "why": "x", "outcome": "approved"},
        )
        assert status == 409
        assert b"zmieni" in body
    finally:
        server.shutdown()


def test_decide_with_unknown_option_is_refused(registry: Registry) -> None:
    _write_change(registry, "CHG-1", waiting=["B2"])
    item = _write_inbox_gate(
        registry, questions=[{"question": "Co?", "options": [{"value": "a", "label": "A"}], "other": False}]
    )
    deps = console.Deps(registry, checkout=None)
    server, url = _serve(deps)
    try:
        status, _ = _post(
            f"{url}/inbox/{item['id']}/decide?t={TOKEN}",
            {
                "t": TOKEN,
                "loaded_at": item["received_at"],
                "statement": "x",
                "why": "x",
                "outcome": "approved",
                "answer_0": "nieznana",
            },
        )
        assert status == 403
    finally:
        server.shutdown()


def test_decide_with_other_requires_text(registry: Registry) -> None:
    _write_change(registry, "CHG-1", waiting=["B2"])
    item = _write_inbox_gate(
        registry, questions=[{"question": "Co?", "options": [{"value": "a", "label": "A"}], "other": True}]
    )
    deps = console.Deps(registry, checkout=None)
    server, url = _serve(deps)
    try:
        status, _ = _post(
            f"{url}/inbox/{item['id']}/decide?t={TOKEN}",
            {
                "t": TOKEN,
                "loaded_at": item["received_at"],
                "statement": "x",
                "why": "x",
                "outcome": "approved",
                "answer_0": "__other__",
                "answer_0_other": "",
            },
        )
        assert status == 403
    finally:
        server.shutdown()


def test_files_panel_lists_artifacts(registry: Registry, checkout: Path) -> None:
    deps = console.Deps(registry, checkout=checkout)
    server, url = _serve(deps)
    try:
        status, body, _ = _get(f"{url}/trace/CHG-1/file?path=intent.md&t={TOKEN}")
        assert status == 200
        assert body == b"# intent\n"
    finally:
        server.shutdown()


def test_files_panel_refuses_path_outside_whitelist(registry: Registry, checkout: Path) -> None:
    deps = console.Deps(registry, checkout=checkout)
    server, url = _serve(deps)
    try:
        for path in (".env", "../../../etc/passwd", "secrets.txt", "docs/project/changes/CHG-1/intent.md"):
            status, _, _ = _get(f"{url}/trace/CHG-1/file?path={urllib.parse.quote(path)}&t={TOKEN}")
            assert status == 403, path
    finally:
        server.shutdown()


def test_files_panel_refuses_symlink(registry: Registry, checkout: Path, tmp_path: Path) -> None:
    (tmp_path / "secret.md").write_text("tajne", encoding="utf-8")
    _commit_on(checkout, "pdi/CHG-1-design", {}, link=("design.md", str(tmp_path / "secret.md")))
    deps = console.Deps(registry, checkout=checkout)
    server, url = _serve(deps)
    try:
        status, _, _ = _get(f"{url}/trace/CHG-1/file?path=design.md&t={TOKEN}")
        assert status == 403
    finally:
        server.shutdown()


def test_files_panel_refuses_binary(registry: Registry, checkout: Path) -> None:
    _commit_on(checkout, "pdi/CHG-1-design", {"design.md": b"binarny \x00 plik"})
    deps = console.Deps(registry, checkout=checkout)
    server, url = _serve(deps)
    try:
        status, _, _ = _get(f"{url}/trace/CHG-1/file?path=design.md&t={TOKEN}")
        assert status == 403
    finally:
        server.shutdown()


def test_files_panel_refuses_too_big(registry: Registry, checkout: Path) -> None:
    _commit_on(checkout, "pdi/CHG-1-design", {"design.md": b"x" * (console.FILE_SIZE_LIMIT + 1)})
    deps = console.Deps(registry, checkout=checkout)
    server, url = _serve(deps)
    try:
        status, _, _ = _get(f"{url}/trace/CHG-1/file?path=design.md&t={TOKEN}")
        assert status == 403
    finally:
        server.shutdown()


def test_diff_uses_current_cut(registry: Registry, checkout: Path) -> None:
    _write_change(
        registry,
        "CHG-1",
        dispatch={"cuts": [{"branch": "story/tsk-1", "pr": "https://x/pull/1"}], "ref": "main"},
    )
    git = FakeGit((0, "diff output\n"))
    deps = console.Deps(registry, checkout=checkout, git=git)
    server, url = _serve(deps)
    try:
        status, body, _ = _get(f"{url}/trace/CHG-1/diff?t={TOKEN}")
        assert status == 200
        assert b"diff output" in body
        assert git.calls == [["diff", "main...story/tsk-1"]]
    finally:
        server.shutdown()


def test_progress_sse_streams_new_lines(registry: Registry, tmp_path: Path) -> None:
    log = tmp_path / "runs" / "CHG-1-requirements.log"
    log.parent.mkdir()
    log.write_text("", encoding="utf-8")
    _write_change(
        registry, "CHG-1", dispatch={"mode": "local", "status": "running", "log": str(log), "phase": "requirements"}
    )
    deps = console.Deps(registry, checkout=None)
    server, url = _serve(deps)

    def writer() -> None:
        time.sleep(0.6)
        with dispatch_local.progress_path(log).open("a", encoding="utf-8") as f:
            f.write(json.dumps({"phase": "requirements", "status": "in_progress", "message": "pisze plik"}) + "\n")
            f.flush()

    threading.Thread(target=writer, daemon=True).start()
    sock = socket.create_connection(("127.0.0.1", server.server_port), timeout=5)
    try:
        sock.sendall(f"GET /sse/progress?change=CHG-1&t={TOKEN} HTTP/1.1\r\nHost: localhost\r\n\r\n".encode())
        sock.settimeout(4)
        buf = b""
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline and b"pisze plik" not in buf:
            try:
                chunk = sock.recv(4096)
            except TimeoutError:
                break
            if not chunk:
                break
            buf += chunk
        assert b"pisze plik" in buf
        assert b"content-type: text/event-stream" in buf.lower()
    finally:
        sock.close()
        server.shutdown()


def test_decide_rejects_bad_origin(registry: Registry) -> None:
    item = _write_inbox_gate(registry)
    deps = console.Deps(registry, checkout=None)
    server, url = _serve(deps)
    try:
        status, _ = _post(
            f"{url}/inbox/{item['id']}/decide?t={TOKEN}",
            {"t": TOKEN, "loaded_at": item["received_at"], "statement": "x", "why": "x", "outcome": "approved"},
            extra_headers={"origin": "http://evil.example"},
        )
        assert status == 403
    finally:
        server.shutdown()


def test_escapes_question_and_log_text(registry: Registry) -> None:
    _write_inbox_gate(registry, questions=["Wstrzykuję <script>alert(1)</script>"])
    deps = console.Deps(registry, checkout=None)
    server, url = _serve(deps)
    try:
        _, body, _ = _get(f"{url}/inbox?t={TOKEN}")
        page = body.decode("utf-8")
        assert "<script>alert" not in page
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page
    finally:
        server.shutdown()


def test_main_rejects_missing_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PDI_REGISTRY_PATH", raising=False)
    monkeypatch.setenv("PDI_CONSOLE_TOKEN", "x")
    with pytest.raises(SystemExit):
        console.main()


def test_main_rejects_missing_token(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PDI_REGISTRY_PATH", str(tmp_path))
    monkeypatch.delenv("PDI_CONSOLE_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        console.main()


# --- poprawki po pierwszym przebiegu na Macu (2026-11-07) ---


def _problem_draft(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "kind": "problem",
        "category": "enhancement",
        "title": "Nie widać, na którym środowisku jest strona",
        "who": "odwiedzający stronę",
        "cannot": "rozpoznać, czy patrzy na test, czy na prod",
        "impact": "pomylone zgłoszenia test/prod",
        "reporter": "dbqm45",
        "channel": "form",
    }
    base.update(overrides)
    return base


def test_menu_links_keep_the_token(registry: Registry) -> None:
    """Menu miało `?nav=…` bez tokenu — każde kliknięcie dawało 404."""
    import re

    deps = console.Deps(registry, checkout=None)
    server, url = _serve(deps)
    try:
        status, body, _ = _get(f"{url}/board?t={TOKEN}")
        assert status == 200
        nav = body.decode().split("<nav>", 1)[1].split("</nav>", 1)[0]
        links = re.findall(r'href="([^"]+)"', nav)
        assert [link.split("?")[0] for link in links] == [
            "/now",
            "/discuss",
            "/board",
            "/inbox",
            "/decisions",
            "/autonomy",
            "/flow",
            "/drafts",
        ]
        for link in links:
            assert f"t={TOKEN}" in link
            assert _get(f"{url}{link.replace('&amp;', '&')}")[0] == 200
    finally:
        server.shutdown()


def test_inbox_lists_problems_waiting_for_triage(registry: Registry) -> None:
    from pdi.problems import ProblemStore

    ProblemStore(registry).record(_problem_draft())
    done = ProblemStore(registry).record(_problem_draft(title="Inne"))
    ProblemStore(registry).triage(done["id"], "rejected", {**_draft_for_test(), "kind": "triage"},
                                  rejection_reason="other", rejection_note="test")  # fmt: skip
    deps = console.Deps(registry, checkout=None)
    server, url = _serve(deps)
    try:
        _, body, _ = _get(f"{url}/inbox?t={TOKEN}")
        page = body.decode()
        assert "PRB-1" in page and "Nie widać, na którym środowisku jest strona" in page
        assert "/problems/PRB-1/triage" in page and "accept (załóż CHG)" in page
        assert "/problems/PRB-2/triage" not in page  # już po triażu
    finally:
        server.shutdown()


def _draft_for_test() -> dict[str, Any]:
    return {
        "statement": "Odrzucone w teście.",
        "why": "Test.",
        "decided_by": "test",
        "decided_at": "2026-11-07",
        "drafted_by": "human",
        "source": {"kind": "manual", "excerpt": "test"},
    }


def test_triage_by_button_accepts_and_opens_a_change(registry: Registry) -> None:
    from pdi.problems import ProblemStore

    ProblemStore(registry).record(_problem_draft())
    deps = console.Deps(registry, checkout=None)
    server, url = _serve(deps)
    try:
        form = {
            "t": TOKEN,
            "statement": "Przyjmujemy PRB-1.",
            "why": "Mały, sprawdzalny problem.",
            "outcome": "accepted",
        }
        status, body = _post(f"{url}/problems/PRB-1/triage?t={TOKEN}", form)
        assert status == 200, body
        stored = ProblemStore(registry).get("PRB-1")
        assert stored["status"] == "accepted" and stored["change"].startswith("CHG-")
        decision = registry.get(stored["triage_decision"])
        assert decision["kind"] == "triage" and decision["source"]["kind"] == "console"
        assert decision["links"]["prb"] == "PRB-1"
        assert _post(f"{url}/problems/PRB-1/triage?t={TOKEN}", form)[0] == 409  # drugi raz: już po triażu
    finally:
        server.shutdown()


def test_triage_reject_needs_a_reason_and_a_token(registry: Registry) -> None:
    from pdi.problems import ProblemStore

    ProblemStore(registry).record(_problem_draft())
    deps = console.Deps(registry, checkout=None)
    server, url = _serve(deps)
    try:
        form = {"t": TOKEN, "statement": "Odrzucamy.", "why": "Poza zakresem.", "outcome": "rejected"}
        assert _post(f"{url}/problems/PRB-1/triage?t={TOKEN}", form)[0] == 409  # bez rejection_reason
        assert _post(f"{url}/problems/PRB-1/triage", {**form, "t": "zly"})[0] == 404
        status, _ = _post(f"{url}/problems/PRB-1/triage?t={TOKEN}", {**form, "rejection_reason": "out_of_strategy"})
        assert status == 200
        assert ProblemStore(registry).get("PRB-1")["status"] == "rejected"
    finally:
        server.shutdown()


def test_triage_by_button_parks_and_marks_duplicates(registry: Registry) -> None:
    """Agent nie triażuje przez MCP (docs/plan-decyzje-tylko-przyciskiem.md): konsola ma wszystkie wyniki triażu."""
    from pdi.problems import ProblemStore

    store = ProblemStore(registry)
    store.record(_problem_draft())
    store.record(_problem_draft(title="Drugie"))
    store.record(_problem_draft(title="Trzecie"))
    server, url = _serve(console.Deps(registry, checkout=None))
    try:
        _, page, _ = _get(f"{url}/inbox?t={TOKEN}")
        text = page.decode("utf-8")
        assert 'value="parked"' in text and 'name="return_when"' in text
        assert 'value="duplicate"' in text and 'name="duplicate_of"' in text
        form = {"t": TOKEN, "statement": "Odkładamy.", "why": "Jedno zgłoszenie to za mało.", "outcome": "parked"}
        assert _post(f"{url}/problems/PRB-2/triage?t={TOKEN}", form)[0] == 409  # bez warunku powrotu
        form["return_when"] = "3 nowe zgłoszenia"
        assert _post(f"{url}/problems/PRB-2/triage?t={TOKEN}", form)[0] == 200
        assert store.get("PRB-2")["status"] == "parked" and store.get("PRB-2")["return_when"] == "3 nowe zgłoszenia"
        dup = {"t": TOKEN, "statement": "Duplikat PRB-1.", "why": "To samo.", "outcome": "duplicate"}
        assert _post(f"{url}/problems/PRB-3/triage?t={TOKEN}", dup)[0] == 409  # bez oryginału
        assert _post(f"{url}/problems/PRB-3/triage?t={TOKEN}", {**dup, "duplicate_of": "PRB-1"})[0] == 200
        assert store.get("PRB-3")["duplicate_of"] == "PRB-1"
    finally:
        server.shutdown()


def test_process_proposals_can_be_rejected_by_button() -> None:
    assert 'value="rejected"' in console._action_buttons_for("process")


def test_main_builds_the_inbox_like_the_mcp_server(registry: Registry, monkeypatch: pytest.MonkeyPatch) -> None:
    """Konsola tworzyła Inbox bez konfiguracji: decyzja przyciskiem nie uruchamiała następnej fazy ani nie sprawdzała
    PR (PRB-2). Teraz te same ustawienia ze środowiska co serwer MCP."""
    monkeypatch.setenv("PDI_DISPATCH", "local")
    inbox = console.inbox_from_env(registry)
    assert inbox._dispatch.local
    assert inbox.problems._dispatch.local


def test_files_come_from_the_phase_branch_not_the_working_tree(registry: Registry, checkout: Path) -> None:
    """Na Macu: klon na `main`, intent.md tylko na gałęzi fazy → 403 „plik nie istnieje” (2026-11-07)."""
    assert not (checkout / "docs/project/changes/CHG-1/intent.md").exists()
    (checkout / "docs/project/changes/CHG-1").mkdir(parents=True)
    (checkout / "docs/project/changes/CHG-1/design.md").write_text("niezacommitowane\n", encoding="utf-8")
    _write_change(registry, "CHG-1", waiting=["B1"])
    deps = console.Deps(registry, checkout=checkout)
    server, url = _serve(deps)
    try:
        _, body, _ = _get(f"{url}/trace/CHG-1?t={TOKEN}")
        page = body.decode()
        files = page.split("Pliki zmiany", 1)[1]
        assert "intent.md" in files and "requirements.md" in files and "plan.md" in files
        assert "design.md" not in files and "release.yaml" not in files  # nie ma ich na żadnej gałęzi zmiany
        assert "pdi/CHG-1-intent" in files  # skąd plik i który commit
        assert _get(f"{url}/trace/CHG-1/file?path=intent.md&t={TOKEN}")[1] == b"# intent\n"
        status, _, _ = _get(f"{url}/trace/CHG-1/file?path=design.md&t={TOKEN}")
        assert status == 403  # lokalny, niezacommitowany plik nie jest pokazywany
    finally:
        server.shutdown()


def test_newer_phase_branch_wins(registry: Registry, checkout: Path) -> None:
    _commit_on(checkout, "pdi/CHG-1-requirements", {"intent.md": b"# intent v2\n"})
    deps = console.Deps(registry, checkout=checkout)
    server, url = _serve(deps)
    try:
        assert _get(f"{url}/trace/CHG-1/file?path=intent.md&t={TOKEN}")[1] == b"# intent v2\n"
    finally:
        server.shutdown()


def test_pages_let_the_browser_send_a_real_origin_on_post(registry: Registry) -> None:
    """Na Macu „approve” dawało 403 origin (2026-11-07): przy `Referrer-Policy: no-referrer` przeglądarka wysyła
    `Origin: null` w POST formularza (Fetch Standard, „serializing a request origin”), a konsola słusznie to odrzuca.
    `same-origin` zostawia Origin i Referer tylko dla własnych żądań, token z adresu nie wychodzi na zewnątrz."""
    deps = console.Deps(registry, checkout=None)
    server, url = _serve(deps)
    try:
        _, _, headers = _get(f"{url}/inbox?t={TOKEN}")
        assert headers["referrer-policy"] == "same-origin"
        item = _write_inbox_gate(registry, questions=None)
        form = {"t": TOKEN, "loaded_at": item["received_at"], "statement": "x", "why": "y", "outcome": "approved"}
        status, _ = _post(f"{url}/inbox/{item['id']}/decide?t={TOKEN}", form, extra_headers={"origin": "null"})
        assert status == 403  # Origin: null dalej odrzucone
    finally:
        server.shutdown()


# --- pętla PR (N2) ---

LOOP_PR = "https://github.com/dbqm45/sdlc-proba/pull/44"
LOOP = {
    LOOP_PR: {
        "branch": "story/tsk-1-badge",
        "status": "green",
        "round": 2,
        "max_rounds": 2,
        "cost_usd": 0.4,
        "reason": "checki zielone, uwagi zamknięte",
        "questions": [{"id": "R2", "text": "[niepotwierdzone] x"}],
        "rounds": [
            {
                "round": 1,
                "findings": 2,
                "fixed": ["R1"],
                "questions": ["R2"],
                "checks": {"state": "red"},
                "cost_usd": 0.3,
            },
            {"round": 2, "findings": 0, "fixed": [], "questions": [], "checks": {"state": "green"}, "cost_usd": 0.1},
        ],
    }
}


def test_board_card_and_trace_show_the_pr_loop(registry: Registry) -> None:
    _write_change(registry, "CHG-4", dispatch={"mode": "local", "status": "done", "phase": "delivery"}, pr_loop=LOOP)
    deps = console.Deps(registry, checkout=None)
    server, url = _serve(deps)
    try:
        _, body, _ = _get(f"{url}/board?t={TOKEN}")
        card = body.decode("utf-8").split('<span class="chg">CHG-4</span>')[1].split("</li>")[0]
        assert "PR #44: green (runda 2/2)" in card
        _, body, _ = _get(f"{url}/trace/CHG-4?t={TOKEN}")
        page = body.decode("utf-8")
        assert "<h2>Pętla PR</h2>" in page and "<td>R1</td>" in page and "<td>red</td>" in page
        assert "checki zielone, uwagi zamknięte" in page
    finally:
        server.shutdown()


def test_ready_pr_in_inbox_closes_with_reviewed(registry: Registry) -> None:
    _write_change(registry, "CHG-4", dispatch={"mode": "local", "status": "done", "phase": "delivery"}, pr_loop=LOOP)
    deps = console.Deps(registry, checkout=None)
    server, url = _serve(deps)
    try:
        _, body, _ = _get(f"{url}/inbox?t={TOKEN}")
        page = body.decode("utf-8")
        assert "PR gotowy do Twojego przeglądu: CHG-4 PR #44" in page
        assert 'value="reviewed"' in page and "[niepotwierdzone] x" in page and 'value="approved"' not in page
        item = deps.inbox.get("pr-ready-CHG-4-44")
        status, body = _post(
            f"{url}/inbox/{item['id']}/decide?t={TOKEN}",
            {
                "t": TOKEN,
                "loaded_at": item["received_at"],
                "statement": "Przejrzane",
                "why": "ok",
                "outcome": "reviewed",
            },
        )
        assert status == 200 and "Pozycja zamknięta" in body.decode("utf-8")
        assert deps.inbox.get(item["id"])["status"] == "decided"
    finally:
        server.shutdown()


# --- tablica „Now” (DI Team T3): przebiegi agentów z agent-runs/ i decyzje ze skrzynki ---

NOW_AT = datetime(2026, 11, 22, 12, 0, tzinfo=UTC)


def _run_event(kind: str, run: str, event_id: str, at: str, **payload: Any) -> dict[str, Any]:
    return {
        "id": event_id,
        "type": f"run.{kind}",
        "occurred_at": at,
        "source": "tf",
        "contract_version": "0.15.1",
        "payload": {"run": run, "phase": "delivery", **payload},
    }


def _seed_runs(registry: Registry) -> None:
    inbox = Inbox(registry)
    ola, kuba = {"name": "Ola", "kind": "human"}, {"name": "Kuba", "kind": "human"}
    inbox.receive(
        _run_event(
            "started",
            "r-run",
            "e1",
            "2026-11-22T11:50:00Z",
            started_by=ola,
            trigger="manual",
            change="CHG-12",
            task="TSK-57",
            agent="jan",
        )
    )
    inbox.receive(
        _run_event(
            "progress",
            "r-run",
            "e2",
            "2026-11-22T11:55:00Z",
            status="in_progress",
            activity="uruchamia <testy> cięcia",
            cost_usd=1.2,
            budget_usd=10,
        )
    )
    inbox.receive(_run_event("started", "r-gate", "e3", "2026-11-22T10:00:00Z", started_by=kuba, trigger="pdi"))
    inbox.receive(_run_event("finished", "r-gate", "e4", "2026-11-22T10:30:00Z", outcome="waiting_gate"))
    review = {"url": "https://github.com/acme/pay/pull/88", "status": "open", "ai_verdict": "approved", "risk": "low"}
    inbox.receive(_run_event("started", "r-rev", "e5", "2026-11-22T08:00:00Z", started_by=ola, trigger="manual"))
    inbox.receive(_run_event("finished", "r-rev", "e6", "2026-11-22T09:00:00Z", outcome="done", review=review))
    inbox.receive(_run_event("finished", "r-done", "e7", "2026-11-21T09:00:00Z", outcome="failed"))
    inbox.receive(_run_event("finished", "r-old", "e8", "2026-11-01T09:00:00Z", outcome="done"))


def _serve_at(deps: console.Deps) -> tuple[console.ThreadedHTTPServer, str]:
    server = console.make_server(deps, token=TOKEN, port=0, clock=lambda: NOW_AT)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_port}"


def _column(page: str, n: int) -> str:
    return page.split(f'class="lane n{n}"')[1].split('class="lane')[0]


def test_now_puts_each_run_in_its_column(registry: Registry) -> None:
    _seed_runs(registry)
    _write_inbox_gate(registry, item_id="evt-gate-9", change="CHG-30")
    server, url = _serve_at(console.Deps(registry, checkout=None))
    try:
        status, body, _ = _get(f"{url}/now?t={TOKEN}")
        page = body.decode("utf-8")
    finally:
        server.shutdown()
    assert status == 200
    in_progress, awaiting, review, done = (_column(page, n) for n in (1, 2, 3, 4))
    assert "CHG-12" in in_progress and "Started by: Ola" in in_progress and "TSK-57" in in_progress
    assert "uruchamia &lt;testy&gt; cięcia" in in_progress and "<testy>" not in page
    assert "koszt: 1.20 USD z 10.00" in in_progress and "zmiana karty: 5 min temu" in in_progress
    assert "Started by: Kuba" in awaiting and "czeka na decyzję na bramce" in awaiting
    assert "CHG-30" in awaiting and "zdecyduj w skrzynce" in awaiting
    assert "PR #88" in review and "approved" in review
    assert "failed" in done and "zmiana karty: 27 h temu" in done
    assert page.count('class="card"') == 5  # r-old (21 dni) jest poza tablicą


def test_now_filters_by_who_started_the_run(registry: Registry) -> None:
    _seed_runs(registry)
    _write_inbox_gate(registry, item_id="evt-gate-9", change="CHG-30")
    server, url = _serve_at(console.Deps(registry, checkout=None))
    try:
        _, body, _ = _get(f"{url}/now?t={TOKEN}&who=Kuba")
        page = body.decode("utf-8")
    finally:
        server.shutdown()
    assert "Started by: Kuba" in page and "Started by: Ola" not in page
    assert "CHG-30" not in page  # pozycje skrzynki nie mają osoby, więc filtr je chowa
    assert "class=on>Kuba</a>" in page


def test_now_requires_token_and_works_without_runs(registry: Registry) -> None:
    server, url = _serve_at(console.Deps(registry, checkout=None))
    try:
        assert _get(f"{url}/now")[0] == 404
        status, body, _ = _get(f"{url}/now?t={TOKEN}")
    finally:
        server.shutdown()
    assert status == 200 and body.decode("utf-8").count("<small>nic</small>") == 4


# --- DV4: „Przepływ” — gdzie zmiana czeka ---


def test_flow_page_shows_where_changes_wait(registry: Registry) -> None:
    from pdi.changes import ChangeStore

    store = ChangeStore(registry)
    store.save(
        {
            "change": "CHG-41",
            "status": "open",
            "history": [
                {"at": "2026-11-20T12:00:00Z", "what": "gate.requested", "gate": "B1"},
                {
                    "at": "2026-11-20T16:00:00Z",
                    "what": "gate.decided",
                    "gate": "B1",
                    "outcome": "approved",
                    "decision": "DEC-1",
                },
                {"at": "2026-11-21T12:00:00Z", "what": "gate.requested", "gate": "B2"},
            ],
        }
    )
    _write_inbox_gate(registry, item_id="evt-gate-41", change="CHG-41", gate="B2")
    server, url = _serve_at(console.Deps(registry, checkout=None))
    try:
        status, body, _ = _get(f"{url}/flow?t={TOKEN}")
        page = body.decode("utf-8")
    finally:
        server.shutdown()
    assert status == 200 and "<h1>Przepływ</h1>" in page
    waiting = page.split("Gdzie zmiana czeka", 1)[1].split("</table>", 1)[0]
    assert "CHG-41" in waiting and "B2" in waiting and "24.0 h" in waiting
    per_gate = page.split("Bramki", 1)[1].split("</table>", 1)[0]
    assert "B1" in per_gate and "4.0 h" in per_gate
    assert "<th>Zatrzymała</th>" in per_gate and "<td>0 z 1</td>" in per_gate
    assert "<th>p90</th>" in per_gate  # 9 na 10 decyzji szybciej niż ta wartość
    assert "czekanie" in page and "praca" in page


def test_flow_page_without_changes_says_so(registry: Registry) -> None:
    server, url = _serve(console.Deps(registry, checkout=None))
    try:
        status, body, _ = _get(f"{url}/flow?t={TOKEN}")
    finally:
        server.shutdown()
    assert status == 200 and "nic nie czeka" in body.decode("utf-8")


def test_flow_page_puts_the_gate_queue_next_to_release_quality(registry: Registry) -> None:
    """G7: tydzień po tygodniu kolejka bramek, CFR z ShipScope i nowe zgłoszenia; bez ShipScope — powód."""
    server, url = _serve(console.Deps(registry, checkout=None))
    try:
        status, body, _ = _get(f"{url}/flow?t={TOKEN}")
    finally:
        server.shutdown()
    page = body.decode("utf-8")
    assert status == 200 and "<h2>Kolejka a jakość</h2>" in page
    section = page.split("Kolejka a jakość", 1)[1].split("</table>", 1)[0]
    assert "<th>Kolejka na koniec</th>" in section and "<th>CFR</th>" in section and "<th>Nowe PRB</th>" in section
    assert section.count("<tr><td>") == 8
    assert "PDI_SHIPSCOPE_URL" in page  # dlaczego kolumn ShipScope nie ma


# --- DV2: ocena ryzyka zmiany (kontrakt 0.20.0) przy bramce, doradcza ---

RISK = {
    "level": "high",
    "files": 2,
    "base": "main",
    "items": [{"level": "high", "category": "auth", "file": "src/auth/<login>.py", "reason": "authentication"}],
}


def test_inbox_card_shows_the_change_risk(registry: Registry) -> None:
    item = _write_inbox_gate(registry, item_id="evt-risk-1", change="CHG-5", gate="B4")
    item["risk"] = RISK
    (registry.root / "inbox" / "evt-risk-1.yaml").write_text(json.dumps(item), encoding="utf-8")
    server, url = _serve(console.Deps(registry, checkout=None))
    try:
        status, body, _ = _get(f"{url}/inbox?t={TOKEN}")
        page = body.decode("utf-8")
    finally:
        server.shutdown()
    assert status == 200 and "ryzyko: wysokie" in page
    assert "src/auth/&lt;login&gt;.py" in page and "<login>" not in page and "authentication" in page


def test_flow_page_shows_the_risk_of_the_waiting_gate(registry: Registry) -> None:
    from pdi.changes import ChangeStore

    ChangeStore(registry).save(
        {
            "change": "CHG-5",
            "status": "open",
            "history": [{"at": "2026-11-21T12:00:00Z", "what": "gate.requested", "gate": "B4"}],
        }
    )
    item = _write_inbox_gate(registry, item_id="evt-risk-2", change="CHG-5", gate="B4")
    item["risk"] = RISK
    (registry.root / "inbox" / "evt-risk-2.yaml").write_text(json.dumps(item), encoding="utf-8")
    server, url = _serve_at(console.Deps(registry, checkout=None))
    try:
        _, body, _ = _get(f"{url}/flow?t={TOKEN}")
        page = body.decode("utf-8")
    finally:
        server.shutdown()
    waiting = page.split("Gdzie zmiana czeka", 1)[1].split("</table>", 1)[0]
    assert "<th>Ryzyko</th>" in waiting and "wysokie" in waiting


# --- kontrakt 0.21.0: zgoda przypięta do wersji artefaktu (artifact_sha256 z gate.requested) ---


def _pinned_gate(registry: Registry, digest: str) -> dict[str, Any]:
    _write_change(registry, "CHG-1", waiting=["B3"])
    item = _write_inbox_gate(registry, item_id="evt-pin", change="CHG-1", gate="B3")
    item.update(artifact="docs/project/changes/CHG-1/plan.md", artifact_sha256=digest, artifact_commit="abc1234")
    (registry.root / "inbox" / "evt-pin.yaml").write_text(json.dumps(item), encoding="utf-8")
    return item


def _decide_pin(url: str, item: dict[str, Any], outcome: str) -> tuple[int, bytes]:
    return _post(
        f"{url}/inbox/{item['id']}/decide?t={TOKEN}",
        {
            "t": TOKEN,
            "loaded_at": item["received_at"],
            "statement": "Plan przyjęty.",
            "why": "Zgodny z celami.",
            "outcome": outcome,
        },
    )


def test_approval_of_a_changed_artifact_is_refused(registry: Registry, checkout: Path) -> None:
    import hashlib

    item = _pinned_gate(registry, hashlib.sha256(b"# plan sprzed zmiany\n").hexdigest())
    server, url = _serve(console.Deps(registry, checkout=checkout))
    try:
        status, body = _decide_pin(url, item, "approved")
        page = _get(f"{url}/inbox?t={TOKEN}")[1].decode("utf-8")
    finally:
        server.shutdown()
    assert status == 409 and "zmienił się po wysłaniu prośby" in body.decode("utf-8")
    assert Inbox(registry).get("evt-pin")["status"] == "open"
    assert "artefakt: " in page and "abc1234" in page


def test_approval_of_the_same_artifact_carries_its_hash_back(registry: Registry, checkout: Path) -> None:
    import hashlib

    _commit_on(checkout, "pdi/CHG-1-architecture", {"plan.md": b"# plan\r\nkrok 1\r\n"})  # Windows: CRLF
    item = _pinned_gate(registry, hashlib.sha256(b"# plan\nkrok 1\n").hexdigest())
    server, url = _serve(console.Deps(registry, checkout=checkout))
    try:
        status, _ = _decide_pin(url, item, "approved")
    finally:
        server.shutdown()
    assert status == 200
    sent = [json.loads(p.read_text(encoding="utf-8")) for p in (registry.root / "outbox").glob("*.json")]
    assert [e["payload"].get("artifact_sha256") for e in sent if e["type"] == "gate.decided"] == [
        item["artifact_sha256"]
    ]


def test_sending_back_a_changed_artifact_is_allowed(registry: Registry, checkout: Path) -> None:
    item = _pinned_gate(registry, "0" * 64)
    server, url = _serve(console.Deps(registry, checkout=checkout))
    try:
        status, _ = _decide_pin(url, item, "changes_requested")
    finally:
        server.shutdown()
    assert status == 200
