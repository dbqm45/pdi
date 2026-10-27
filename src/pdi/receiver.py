"""Odbiornik zdarzeń (G1.5, F4): `POST /events/<nadawca>` → skrzynka pdi (`pdi.inbox`).

Nadawcy: `shipscope` (nagłówki `X-ShipScope-*`, jak wysyła ShipScope), `tf` i `ci_for_sdlc` (`X-PDI-*`). Podpis
wszędzie ten sam: `v1=<hex HMAC-SHA256(sekret nadawcy, "<timestamp>.<body>")>`. Ścieżka nadawcy bez ustawionego
sekretu odpowiada 404. `GET /events/<nadawca>` z nagłówkiem `<prefiks>-event: ping` i podpisem nad pustą treścią
odpowiada 200: tak ShipScope sprawdza połączenie z pdi (Settings → pdi, co godzinę). Z `PDI_SHIPSCOPE_URL`
i `PDI_SHIPSCOPE_TOKEN` odbiornik czyta przy starcie i raz dziennie stan połączenia w ShipScope i wypisuje go na stderr;
ten odczyt jest dla ShipScope potwierdzeniem, że pdi go czyta. Formularz zgłoszeń (F3):
`GET /problems/new?t=<PDI_FORM_TOKEN>` i `POST /problems` (`pdi.form`), bez tokenu 404. Biblioteka standardowa, jeden
wątek (plus wątek w tle odczytu ShipScope). ShipScope wysyła tylko na publiczne `https://`, więc
przed odbiornikiem stoi proxy TLS albo tunel. Kod 2xx kończy ponowienia nadawcy.
"""

from __future__ import annotations

import hmac
import json
import os
import sys
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs, urlsplit

from pdi import form
from pdi.dispatch import DispatchConfig
from pdi.impact import ShipScopeConfig, read_connection
from pdi.inbox import BadSignature, Inbox, InvalidEvent, verify_signature
from pdi.notify import NotifyConfig, ReporterNotifyConfig
from pdi.problems import InvalidProblem
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
SHIPSCOPE_CHECK_SECONDS = 24 * 3600


def _utc_now() -> datetime:
    return datetime.now(UTC)


def make_server(
    inbox: Inbox,
    secrets: dict[str, str],
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    clock: Callable[[], datetime] = _utc_now,
    form_token: str | None = None,
) -> HTTPServer:
    """Serwer HTTP odbiornika; `secrets`: nadawca → sekret podpisu; `form_token` włącza formularz zgłoszeń;
    `port=0` wybiera wolny port (testy)."""

    def token_ok(given: str) -> bool:
        return bool(form_token) and hmac.compare_digest(given.encode(), str(form_token).encode())

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802 — nazwa wymagana przez http.server
            if self.path == "/problems":
                return self._form_post()
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
            url = urlsplit(self.path)
            sender = url.path.removeprefix(PREFIX) if url.path.startswith(PREFIX) else ""
            if sender in SENDERS:
                return self._ping(sender)
            if url.path == "/problems/new":
                given = (parse_qs(url.query).get("t") or [""])[0]
                if not token_ok(given):
                    return self._answer(404, {"error": "Nie ma takiej strony."})
                return self._html(200, form.form_page(given))
            self._answer(405, {"error": "Tylko POST."})

        def _ping(self, sender: str) -> None:
            """Podpisany ping nadawcy: sprawdza sekret, niczego nie zapisuje."""
            if sender not in secrets:
                return self._answer(404, {"error": "Nie ma takiej strony."})
            header = SENDERS[sender][1]
            if self.headers.get(f"{header}-event") != "ping":
                return self._answer(405, {"error": "Tylko POST (albo podpisany ping)."})
            try:
                verify_signature(
                    secrets[sender],
                    self.headers.get(f"{header}-timestamp"),
                    b"",
                    self.headers.get(f"{header}-signature"),
                    now=clock(),
                )
            except BadSignature as e:
                return self._answer(401, {"error": str(e)})
            self._answer(200, {"status": "ok", "sender": sender})

        def _form_post(self) -> None:
            if not form_token:
                return self._answer(404, {"error": "Formularz zgłoszeń jest wyłączony."})
            length = self.headers.get("content-length", "")
            if not length.isdigit():
                return self._answer(411, {"error": "Brak Content-Length."})
            if int(length) > MAX_BODY:
                return self._answer(413, {"error": f"Treść większa niż {MAX_BODY} bajtów."})
            body = self.rfile.read(int(length))
            draft, errors, given = form.parse_form(body)
            if not token_ok(given):
                return self._html(
                    403, "<!doctype html><title>Brak dostępu</title><p>Link formularza jest nieważny.</p>"
                )
            if not errors:
                try:
                    problem = inbox.problems.record(draft)
                except InvalidProblem:
                    errors = {"form": "Zgłoszenie nie przeszło sprawdzenia — popraw pola i wyślij jeszcze raz."}
                else:
                    return self._html(201, form.thanks_page(problem, problem["similar"]))
            return self._html(400, form.form_page(given, values=form.values_of(body), errors=errors))

        def _html(self, status: int, page: str) -> None:
            data = page.encode()
            self.send_response(status)
            self.send_header("content-type", "text/html; charset=utf-8")
            self.send_header("content-length", str(len(data)))
            self.send_header(
                "content-security-policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'"
            )
            self.send_header("x-frame-options", "DENY")
            self.end_headers()
            self.wfile.write(data)

        def _answer(self, status: int, body: dict[str, Any]) -> None:
            data = json.dumps(body, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("content-type", "application/json; charset=utf-8")
            self.send_header("content-length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 — sygnatura z http.server
            # Linia dostępu bez treści zdarzenia i bez tokenu formularza: metoda, ścieżka, kod.
            path = urlsplit(self.path).path
            sys.stderr.write(f"pdi-receiver: {self.command} {path} {args[1] if len(args) > 1 else ''}\n")

    return HTTPServer((host, port), Handler)


def connection_line(value: dict[str, Any] | None, error: str | None) -> str:
    """Linia na stderr ze stanem połączenia w ShipScope albo z problemem (bez tokenu)."""
    if value is None:
        return f"pdi-receiver: ShipScope: {error}\n"
    return f"pdi-receiver: ShipScope: workspace {value['workspace']}, połączenie z pdi: {value['state']}\n"


def watch_shipscope(config: ShipScopeConfig) -> None:
    """Czyta stan połączenia w ShipScope teraz i potem raz dziennie, w wątku w tle (nie blokuje odbiornika)."""

    def check() -> None:
        while True:
            sys.stderr.write(connection_line(*read_connection(config)))
            stop.wait(SHIPSCOPE_CHECK_SECONDS)

    stop = threading.Event()
    threading.Thread(target=check, name="shipscope-connection", daemon=True).start()


def main() -> None:
    secrets = {sender: os.environ[var] for sender, (var, _) in SENDERS.items() if os.environ.get(var)}
    form_token = os.environ.get("PDI_FORM_TOKEN") or None
    if not secrets and not form_token:
        names = ", ".join([*(var for var, _ in SENDERS.values()), "PDI_FORM_TOKEN"])
        raise SystemExit(f"Brak sekretu podpisu ani tokenu formularza — ustaw co najmniej jedną zmienną: {names}.")
    try:
        registry = Registry.from_env()
    except RuntimeError as e:
        raise SystemExit(str(e)) from e
    host = os.environ.get("PDI_RECEIVER_HOST", DEFAULT_HOST)
    port = int(os.environ.get("PDI_RECEIVER_PORT", str(DEFAULT_PORT)))
    inbox = Inbox(
        registry,
        dispatch=DispatchConfig.from_env(),
        notify=NotifyConfig.from_env(),
        reporters=ReporterNotifyConfig.from_env(),
    )
    server = make_server(inbox, secrets, host=host, port=port, form_token=form_token)
    shipscope = ShipScopeConfig.from_env()
    if shipscope.url:
        watch_shipscope(shipscope)
    paths = ", ".join([*(PREFIX + s for s in secrets), *(["/problems/new"] if form_token else [])])
    sys.stderr.write(f"pdi-receiver: nasłuchuje na http://{host}:{port} ({paths})\n")
    server.serve_forever()


if __name__ == "__main__":
    main()
