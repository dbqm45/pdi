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


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    co = tmp_path / "sklep"
    (co / ".git").mkdir(parents=True)
    changes = co / "docs/project/changes/CHG-1"
    changes.mkdir(parents=True)
    (changes / "intent.md").write_text("# intent\n", encoding="utf-8")
    (changes / "requirements.md").write_text("# requirements\n", encoding="utf-8")
    (changes / "plan.md").write_text("# plan\n", encoding="utf-8")
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


def _write_inbox_gate(registry: Registry, *, change: str = "CHG-1", gate: str = "B2",
                      questions: Any = None, item_id: str = "evt-1") -> dict[str, Any]:
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
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:  # noqa: S310 — localhost testowy
            return int(resp.status), resp.read(), {k.lower(): v for k, v in resp.headers.items()}
    except urllib.error.HTTPError as e:
        return int(e.code), e.read(), {k.lower(): v for k, v in e.headers.items()}


def _post(url: str, data: dict[str, Any], *, extra_headers: dict[str, str] | None = None) -> tuple[int, bytes]:
    body = urllib.parse.urlencode(data).encode()
    headers = {"content-type": "application/x-www-form-urlencoded",
               "origin": f"http://127.0.0.1:{urllib.parse.urlsplit(url).port}"}
    headers.update(extra_headers or {})
    req = urllib.request.Request(url, data=body, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:  # noqa: S310
            return int(resp.status), resp.read()
    except urllib.error.HTTPError as e:
        return int(e.code), e.read()


def test_board_lists_each_change_in_its_lane(registry: Registry) -> None:
    _write_change(registry, "CHG-1", waiting=["B2"], dispatch={"mode": "local", "status": "done", "phase": "requirements"})
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
    _write_inbox_gate(registry, questions=[
        {"question": "Kto odpowiada?", "options": [{"value": "ops", "label": "Operacje"},
                                                    {"value": "dev", "label": "Deweloperzy"}],
         "recommended": "dev", "other": True},
    ])
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
        status, _ = _post(f"{url}/inbox/{item['id']}/decide",
                          {"statement": "x", "why": "x", "outcome": "approved"})
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
            {"t": TOKEN, "loaded_at": "2020-01-01T00:00:00Z",
             "statement": "x", "why": "x", "outcome": "approved"},
        )
        assert status == 409
        assert b"zmieni" in body
    finally:
        server.shutdown()


def test_decide_with_unknown_option_is_refused(registry: Registry) -> None:
    _write_change(registry, "CHG-1", waiting=["B2"])
    item = _write_inbox_gate(registry, questions=[
        {"question": "Co?", "options": [{"value": "a", "label": "A"}], "other": False}
    ])
    deps = console.Deps(registry, checkout=None)
    server, url = _serve(deps)
    try:
        status, _ = _post(
            f"{url}/inbox/{item['id']}/decide?t={TOKEN}",
            {"t": TOKEN, "loaded_at": item["received_at"], "statement": "x", "why": "x",
             "outcome": "approved", "answer_0": "nieznana"},
        )
        assert status == 403
    finally:
        server.shutdown()


def test_decide_with_other_requires_text(registry: Registry) -> None:
    _write_change(registry, "CHG-1", waiting=["B2"])
    item = _write_inbox_gate(registry, questions=[
        {"question": "Co?", "options": [{"value": "a", "label": "A"}], "other": True}
    ])
    deps = console.Deps(registry, checkout=None)
    server, url = _serve(deps)
    try:
        status, _ = _post(
            f"{url}/inbox/{item['id']}/decide?t={TOKEN}",
            {"t": TOKEN, "loaded_at": item["received_at"], "statement": "x", "why": "x",
             "outcome": "approved", "answer_0": "__other__", "answer_0_other": ""},
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
    changes = checkout / "docs/project/changes/CHG-1"
    (tmp_path / "secret.md").write_text("tajne", encoding="utf-8")
    (changes / "design.md").symlink_to(tmp_path / "secret.md")
    deps = console.Deps(registry, checkout=checkout)
    server, url = _serve(deps)
    try:
        status, _, _ = _get(f"{url}/trace/CHG-1/file?path=design.md&t={TOKEN}")
        assert status == 403
    finally:
        server.shutdown()


def test_files_panel_refuses_binary(registry: Registry, checkout: Path) -> None:
    (checkout / "docs/project/changes/CHG-1/design.md").write_bytes(b"binarny \x00 plik")
    deps = console.Deps(registry, checkout=checkout)
    server, url = _serve(deps)
    try:
        status, _, _ = _get(f"{url}/trace/CHG-1/file?path=design.md&t={TOKEN}")
        assert status == 403
    finally:
        server.shutdown()


def test_files_panel_refuses_too_big(registry: Registry, checkout: Path) -> None:
    (checkout / "docs/project/changes/CHG-1/design.md").write_bytes(b"x" * (console.FILE_SIZE_LIMIT + 1))
    deps = console.Deps(registry, checkout=checkout)
    server, url = _serve(deps)
    try:
        status, _, _ = _get(f"{url}/trace/CHG-1/file?path=design.md&t={TOKEN}")
        assert status == 403
    finally:
        server.shutdown()


def test_diff_uses_current_cut(registry: Registry, checkout: Path) -> None:
    _write_change(
        registry, "CHG-1",
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
    _write_change(registry, "CHG-1", dispatch={"mode": "local", "status": "running",
                                                "log": str(log), "phase": "requirements"})
    deps = console.Deps(registry, checkout=None)
    server, url = _serve(deps)

    def writer() -> None:
        time.sleep(0.6)
        with dispatch_local.progress_path(log).open("a", encoding="utf-8") as f:
            f.write(json.dumps({"phase": "requirements", "status": "in_progress",
                                "message": "pisze plik"}) + "\n")
            f.flush()

    threading.Thread(target=writer, daemon=True).start()
    sock = socket.create_connection(("127.0.0.1", server.server_port), timeout=5)
    try:
        sock.sendall(
            f"GET /sse/progress?change=CHG-1&t={TOKEN} HTTP/1.1\r\nHost: localhost\r\n\r\n".encode()
        )
        sock.settimeout(4)
        buf = b""
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline and b"pisze plik" not in buf:
            try:
                chunk = sock.recv(4096)
            except socket.timeout:
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
            {"t": TOKEN, "loaded_at": item["received_at"], "statement": "x", "why": "x",
             "outcome": "approved"},
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
