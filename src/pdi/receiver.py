"""Odbiornik zdarzeń ShipScope (G1.5): `POST /events/shipscope` → skrzynka pdi (`pdi.inbox`).

Biblioteka standardowa, jeden wątek. ShipScope wysyła tylko na publiczne `https://`, więc przed odbiornikiem stoi
proxy TLS albo tunel. Kod 2xx kończy ponowienia ShipScope; na 4xx i 5xx ShipScope ponawia (do 10 razy).
"""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from pdi.inbox import BadSignature, Inbox, InvalidEvent, verify_signature
from pdi.registry import Registry

PATH = "/events/shipscope"
MAX_BODY = 64 * 1024
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787


def _utc_now() -> datetime:
    return datetime.now(UTC)


def make_server(
    inbox: Inbox,
    secret: str,
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    clock: Callable[[], datetime] = _utc_now,
) -> HTTPServer:
    """Serwer HTTP odbiornika; `port=0` wybiera wolny port (testy)."""

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802 — nazwa wymagana przez http.server
            if self.path != PATH:
                return self._answer(404, {"error": f"Zdarzenia ShipScope przyjmuje tylko {PATH}."})
            length = self.headers.get("content-length", "")
            if not length.isdigit():
                return self._answer(411, {"error": "Brak Content-Length."})
            if int(length) > MAX_BODY:
                return self._answer(413, {"error": f"Treść większa niż {MAX_BODY} bajtów."})
            body = self.rfile.read(int(length))
            try:
                verify_signature(
                    secret,
                    self.headers.get("x-shipscope-timestamp"),
                    body,
                    self.headers.get("x-shipscope-signature"),
                    now=clock(),
                )
            except BadSignature as e:
                return self._answer(401, {"error": str(e)})
            try:
                event = json.loads(body)
            except (ValueError, UnicodeDecodeError):
                return self._answer(400, {"error": "Treść nie jest poprawnym JSON."})
            if not isinstance(event, dict):
                return self._answer(400, {"error": "Zdarzenie musi być obiektem JSON."})
            if self.headers.get("x-shipscope-event") != event.get("type"):
                return self._answer(400, {"error": "Nagłówek X-ShipScope-Event nie zgadza się z polem type."})
            try:
                result = inbox.receive(event)
            except InvalidEvent as e:
                return self._answer(400, {"error": str(e)})
            item = result["item"]
            self._answer(
                202 if result["status"] == "created" else 200,
                {"status": result["status"], "item": item["id"] if item else None},
            )

        def do_GET(self) -> None:  # noqa: N802
            self._answer(405, {"error": "Tylko POST."})

        def _answer(self, status: int, body: dict[str, Any]) -> None:
            data = json.dumps(body, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("content-type", "application/json; charset=utf-8")
            self.send_header("content-length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 — sygnatura z http.server
            # Linia dostępu bez treści zdarzenia: metoda, ścieżka, kod.
            sys.stderr.write(f"pdi-receiver: {self.command} {self.path} {args[1] if len(args) > 1 else ''}\n")

    return HTTPServer((host, port), Handler)


def main() -> None:
    secret = os.environ.get("PDI_SHIPSCOPE_SIGNING_SECRET")
    if not secret:
        raise SystemExit(
            "Brak zmiennej PDI_SHIPSCOPE_SIGNING_SECRET — ustaw ją na sekret podpisu workspace'u ShipScope "
            "(Settings → Sources)."
        )
    try:
        registry = Registry.from_env()
    except RuntimeError as e:
        raise SystemExit(str(e)) from e
    host = os.environ.get("PDI_RECEIVER_HOST", DEFAULT_HOST)
    port = int(os.environ.get("PDI_RECEIVER_PORT", str(DEFAULT_PORT)))
    server = make_server(Inbox(registry), secret, host=host, port=port)
    sys.stderr.write(f"pdi-receiver: nasłuchuje na http://{host}:{port}{PATH}\n")
    server.serve_forever()


if __name__ == "__main__":
    main()
