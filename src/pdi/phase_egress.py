"""Proxy wyjścia z listą dozwolonych hostów dla fazy tf w kontenerze (krok Z8a, decyzja DZ9).

Działa w osobnym kontenerze (`pdi-egress-…`) podłączonym do dwóch sieci: wewnętrznej sieci fazy (bez wyjścia na
świat) i zwykłej sieci Dockera. Kontener fazy ma tylko sieć wewnętrzną i `HTTPS_PROXY` wskazujące na to proxy, więc
jedyna droga na zewnątrz prowadzi tędy. Proxy przyjmuje wyłącznie `CONNECT host:port` (TLS idzie dalej bez
rozszywania) do hostów z listy i portów 443/80; każdą odmowę wypisuje jako `pdi-egress: blocked <host>:<port>`, a pdi
przenosi te linie do logu przebiegu. Opcjonalne `PDI_EGRESS_UPSTREAM=http://host:port` — proxy firmowe, przez które
idą dozwolone połączenia. Tylko biblioteka standardowa: ten sam plik jest w obrazie fazy (`/opt/pdi/egress.py`).
"""

from __future__ import annotations

import os
import re
import select
import socket
import socketserver
import sys
import urllib.parse
from collections.abc import Sequence

PORT = 3128
PORTS = (443, 80)
BLOCKED = "pdi-egress: blocked"
ALLOWED = "pdi-egress: allowed"
_HOST = re.compile(r"^[A-Za-z0-9.-]{1,253}$")
IDLE_SECONDS = 600
BUFFER = 65536


def allowed(host: str, port: int, patterns: Sequence[str]) -> bool:
    """Czy `host:port` jest na liście: dokładna nazwa albo `*.domena` (sama domena i jej poddomeny)."""
    host = host.lower().rstrip(".")
    if port not in PORTS or not _HOST.match(host) or ".." in host:
        return False
    for pattern in (p.strip().lower() for p in patterns if p.strip()):
        if pattern.startswith("*."):
            suffix = pattern[2:]
            if host == suffix or host.endswith("." + suffix):
                return True
        elif host == pattern:
            return True
    return False


def parse_connect(line: str) -> tuple[str, int] | None:
    """`CONNECT host:port HTTP/1.1` → (host, port); inne żądania → None."""
    parts = line.split()
    if len(parts) != 3 or parts[0] != "CONNECT" or not parts[2].startswith("HTTP/"):
        return None
    host, sep, port = parts[1].rpartition(":")
    if not sep or not port.isdigit():
        return None
    return host.strip("[]"), int(port)


def _target_of(line: str) -> str:
    parts = line.split()
    if len(parts) < 2:
        return "?"
    if parts[0] == "CONNECT":
        return parts[1][:300]
    url = urllib.parse.urlsplit(parts[1])
    return f"{url.hostname or '?'}:{url.port or 80}"


def _pipe(a: socket.socket, b: socket.socket) -> None:
    sockets = [a, b]
    while True:
        ready, _, _ = select.select(sockets, [], [], IDLE_SECONDS)
        if not ready:
            return
        for s in ready:
            data = s.recv(BUFFER)
            if not data:
                return
            (b if s is a else a).sendall(data)


def _open(host: str, port: int, upstream: str | None) -> socket.socket:
    if not upstream:
        return socket.create_connection((host, port), timeout=30)
    proxy = urllib.parse.urlsplit(upstream)
    s = socket.create_connection((proxy.hostname or "", proxy.port or 3128), timeout=30)
    s.sendall(f"CONNECT {host}:{port} HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n".encode())
    head = b""
    while b"\r\n\r\n" not in head and len(head) < BUFFER:
        chunk = s.recv(4096)
        if not chunk:
            break
        head += chunk
    if head.split(b"\r\n", 1)[0].split(b" ")[1:2] != [b"200"]:
        s.close()
        raise OSError("upstream refused CONNECT")
    return s


class Handler(socketserver.StreamRequestHandler):
    patterns: Sequence[str] = ()
    upstream: str | None = None

    def handle(self) -> None:
        line = self.rfile.readline(8192).decode("latin-1").strip()
        while True:  # nagłówki żądania nie są potrzebne
            header = self.rfile.readline(8192)
            if header in (b"\r\n", b"\n", b""):
                break
        target = parse_connect(line)
        if target is None or not allowed(*target, self.patterns):
            print(f"{BLOCKED} {_target_of(line)}", flush=True)
            self.wfile.write(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
            return
        host, port = target
        try:
            remote = _open(host, port, self.upstream)
        except OSError as e:
            print(f"pdi-egress: failed {host}:{port} ({type(e).__name__})", flush=True)
            self.wfile.write(b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
            return
        print(f"{ALLOWED} {host}:{port}", flush=True)
        with remote:
            self.wfile.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
            self.wfile.flush()
            _pipe(self.connection, remote)


class Server(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


def main(argv: Sequence[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    patterns = [p for a in args for p in a.split(",") if p.strip()]
    Handler.patterns = tuple(patterns)
    Handler.upstream = os.environ.get("PDI_EGRESS_UPSTREAM") or None
    with Server(("0.0.0.0", PORT), Handler) as server:  # noqa: S104 — słucha w sieci wewnętrznej fazy
        print(f"pdi-egress: listening on {PORT}, allowed: {', '.join(patterns) or '-'}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
