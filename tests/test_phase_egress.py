"""Proxy wyjścia fazy w kontenerze (Z8a): tylko CONNECT do hostów z listy, każda odmowa w wyjściu."""

import contextlib
import io
import socket
import threading
from collections.abc import Iterator

import pytest

from pdi import phase_egress


@pytest.mark.parametrize(
    ("host", "port", "ok"),
    [
        ("api.anthropic.com", 443, True),
        ("API.Anthropic.com.", 443, True),
        ("registry.npmjs.org", 443, True),
        ("npmjs.org", 443, True),
        ("evil-npmjs.org", 443, False),
        ("api.anthropic.com.evil.com", 443, False),
        ("api.anthropic.com", 22, False),
        ("example.com", 443, False),
        ("a..b", 443, False),
    ],
)
def test_allowed_matches_exact_hosts_and_wildcard_domains(host: str, port: int, ok: bool) -> None:
    assert phase_egress.allowed(host, port, ["api.anthropic.com", "*.npmjs.org"]) is ok


def test_parse_connect_takes_only_connect_requests() -> None:
    assert phase_egress.parse_connect("CONNECT api.anthropic.com:443 HTTP/1.1") == ("api.anthropic.com", 443)
    assert phase_egress.parse_connect("GET http://example.com/ HTTP/1.1") is None
    assert phase_egress.parse_connect("CONNECT example.com HTTP/1.1") is None


@contextlib.contextmanager
def proxy(patterns: list[str]) -> Iterator[tuple[int, io.StringIO]]:
    out = io.StringIO()

    class Handler(phase_egress.Handler):
        pass

    Handler.patterns = tuple(patterns)
    server = phase_egress.Server(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    with contextlib.redirect_stdout(out):
        thread.start()
        try:
            yield server.server_address[1], out
        finally:
            server.shutdown()
            server.server_close()


@contextlib.contextmanager
def echo_server() -> Iterator[int]:
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()

    def serve() -> None:
        conn, _ = listener.accept()
        with conn:
            conn.sendall(conn.recv(100).upper())

    threading.Thread(target=serve, daemon=True).start()
    try:
        yield listener.getsockname()[1]
    finally:
        listener.close()


def ask(port: int, request: bytes) -> bytes:
    with socket.create_connection(("127.0.0.1", port), timeout=5) as s:
        s.sendall(request)
        return s.recv(200)


def test_proxy_refuses_a_host_outside_the_list_and_says_so() -> None:
    with proxy(["api.anthropic.com"]) as (port, out):
        answer = ask(port, b"CONNECT example.com:443 HTTP/1.1\r\nHost: example.com:443\r\n\r\n")
        plain = ask(port, b"GET http://example.org/x HTTP/1.1\r\nHost: example.org\r\n\r\n")

    assert answer.startswith(b"HTTP/1.1 403")
    assert plain.startswith(b"HTTP/1.1 403")
    assert "pdi-egress: blocked example.com:443" in out.getvalue()
    assert "pdi-egress: blocked example.org:80" in out.getvalue()


def test_proxy_tunnels_to_an_allowed_host(monkeypatch: pytest.MonkeyPatch) -> None:
    with echo_server() as target, proxy(["localhost"]) as (port, out):
        monkeypatch.setattr(phase_egress, "PORTS", (target,))
        with socket.create_connection(("127.0.0.1", port), timeout=5) as s:
            s.sendall(f"CONNECT localhost:{target} HTTP/1.1\r\n\r\n".encode())
            assert s.recv(100).startswith(b"HTTP/1.1 200")
            s.sendall(b"ping")
            assert s.recv(100) == b"PING"

    assert f"pdi-egress: allowed localhost:{target}" in out.getvalue()
