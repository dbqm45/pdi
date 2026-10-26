"""Odbiornik zdarzeń (G1.5, F4): `POST /events/<nadawca>` → skrzynka pdi (`pdi.inbox`).

Nadawcy: `shipscope` (nagłówki `X-ShipScope-*`, jak wysyła ShipScope), `tf` i `ci_for_sdlc` (`X-PDI-*`). Podpis
wszędzie ten sam: `v1=<hex HMAC-SHA256(sekret nadawcy, "<timestamp>.<body>")>`. Ścieżka nadawcy bez ustawionego
sekretu odpowiada 404. Biblioteka standardowa, jeden wątek. ShipScope wysyła tylko na publiczne `https://`, więc
przed odbiornikiem stoi proxy TLS albo tunel. Kod 2xx kończy ponowienia nadawcy.
"""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from pdi.dispatch import DispatchConfig
from pdi.inbox import BadSignature, Inbox, InvalidEvent, verify_signature
from pdi.registry import Registry

PATH = "/events/shipscope"
PREFIX = "/events/"
# Nadawca → (zmienna z sekretem, prefiks nagłówków).
SENDERS = {
    "shipscope": ("PDI_SHIPSCOPE_SIGNING_SECRET", "x-shipscope"),
    "tf": ("PDI_TF_SIGNING_SECRET", "x-pdi"),
    "ci_for_sdlc": ("PDI_CI_FOR_SDLC_SIGNING_SECRET", "x-pdi"),
}
MAX_BODY = 64 * 1024
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787


def _utc_now() -> datetime:
    return datetime.now(UTC)


def make_server(
    inbox: Inbox,
    secrets: dict[str, str],
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    clock: Callable[[], datetime] = _utc_now,
) -> HTTPServer:
    """Serwer HTTP odbiornika; `secrets`: nadawca → sekret podpisu; `port=0` wybiera wolny port (testy)."""

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802 — nazwa wymagana przez http.server
            sender = self.path.removeprefix(PREFIX) if self.path.startswith(PREFIX) else ""
            if sender not in SENDERS or sender not in secrets:
                known = ", ".join(PREFIX + s for s in SENDERS if s in secrets)
                return self._answer(404, {"error": f"Zdarzenia przyjmuje: {known}."})
            header = SENDERS[sender][1]
            length = self.headers.get("content-length", "")
            if not length.isdigit():
                return self._answer(411, {"error": "Brak Content-Length."})
            if int(length) > MAX_BODY:
                return self._answer(413, {"error": f"Treść większa niż {MAX_BODY} bajtów."})
            body = self.rfile.read(int(length))
            try:
                verify_signature(
                    secrets[sender],
                    self.headers.get(f"{header}-timestamp"),
                    body,
                    self.headers.get(f"{header}-signature"),
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
            if self.headers.get(f"{header}-event") != event.get("type"):
                return self._answer(400, {"error": f"Nagłówek {header}-event nie zgadza się z polem type."})
            if event.get("source") != sender:
                return self._answer(400, {"error": f"source zdarzenia nie zgadza się ze ścieżką {self.path}."})
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
    secrets = {sender: os.environ[var] for sender, (var, _) in SENDERS.items() if os.environ.get(var)}
    if not secrets:
        names = ", ".join(var for var, _ in SENDERS.values())
        raise SystemExit(f"Brak sekretu podpisu — ustaw co najmniej jedną zmienną: {names}.")
    try:
        registry = Registry.from_env()
    except RuntimeError as e:
        raise SystemExit(str(e)) from e
    host = os.environ.get("PDI_RECEIVER_HOST", DEFAULT_HOST)
    port = int(os.environ.get("PDI_RECEIVER_PORT", str(DEFAULT_PORT)))
    inbox = Inbox(registry, dispatch=DispatchConfig.from_env())
    server = make_server(inbox, secrets, host=host, port=port)
    paths = ", ".join(PREFIX + s for s in secrets)
    sys.stderr.write(f"pdi-receiver: nasłuchuje na http://{host}:{port} ({paths})\n")
    server.serve_forever()


if __name__ == "__main__":
    main()
