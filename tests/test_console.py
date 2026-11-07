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
        assert [link.split("?")[0] for link in links] == ["/board", "/inbox", "/decisions", "/autonomy"]
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
