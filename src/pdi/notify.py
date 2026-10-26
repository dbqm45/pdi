"""Podpisane wiadomości z pdi: `gate.decided` do ci_for_sdlc (F4) i powiadomienia zgłaszającego (F5).

ci_for_sdlc: `POST <PDI_CI_FOR_SDLC_URL>/api/webhooks/pdi` — decyzja „Approve for implementation” ustawia tam baseline
historyjek zmiany; sekret ten sam, którym ci_for_sdlc podpisuje `readiness.changed` dla pdi. Zgłaszający:
`POST <PDI_NOTIFY_URL>` z `problem.notification` (sekret `PDI_NOTIFY_SIGNING_SECRET`); odbiorca sam wybiera kanał.
Podpis jak w pozostałych kierunkach: `X-PDI-Signature: v1=<hex HMAC-SHA256(sekret, "<X-PDI-Timestamp>.<body>")>`.
Błąd nie cofa decyzji; wynik trafia do stanu i jest ponawiany.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from pdi.dispatch import Post

PATH = "/api/webhooks/pdi"
TIMEOUT_SECONDS = 10
LOCAL_HOSTS = ("127.0.0.1", "localhost", "::1")


@dataclass(frozen=True)
class NotifyConfig:
    url: str | None
    secret: str | None = field(default=None, repr=False)

    @classmethod
    def from_env(cls) -> NotifyConfig:
        return cls(
            url=os.environ.get("PDI_CI_FOR_SDLC_URL") or None,
            secret=os.environ.get("PDI_CI_FOR_SDLC_SIGNING_SECRET") or None,
        )


@dataclass(frozen=True)
class ReporterNotifyConfig:
    url: str | None
    secret: str | None = field(default=None, repr=False)

    @classmethod
    def from_env(cls) -> ReporterNotifyConfig:
        return cls(
            url=os.environ.get("PDI_NOTIFY_URL") or None,
            secret=os.environ.get("PDI_NOTIFY_SIGNING_SECRET") or None,
        )


def notify_ci_for_sdlc(
    config: NotifyConfig, event: dict[str, Any], *, at: str, post: Post | None = None, now: int | None = None
) -> dict[str, Any]:
    """Wysyła `event`; wynik `{"status": sent | skipped | failed, …}` do zapisu w stanie zmiany."""
    result: dict[str, Any] = {"status": "failed", "at": at, "event": event["id"]}
    if not config.url:
        return {**result, "status": "skipped", "error": "Brak PDI_CI_FOR_SDLC_URL — ci_for_sdlc nie dostał decyzji."}
    sent = _send(
        config.url,
        config.url.rstrip("/") + PATH,
        config.secret,
        event,
        names=("PDI_CI_FOR_SDLC_URL", "PDI_CI_FOR_SDLC_SIGNING_SECRET"),
        who="ci_for_sdlc",
        post=post,
        now=now,
    )
    return {**result, **sent}


def notify_reporter(
    config: ReporterNotifyConfig, message: dict[str, Any], *, at: str, post: Post | None = None, now: int | None = None
) -> dict[str, Any]:
    """Wysyła `problem.notification` na PDI_NOTIFY_URL; wynik `{"status": sent | skipped | failed, …}`."""
    result: dict[str, Any] = {"status": "failed", "at": at, "id": message["id"]}
    if not config.url:
        return {**result, "status": "skipped", "error": "Brak PDI_NOTIFY_URL — zgłaszający nie dostał powiadomienia."}
    sent = _send(
        config.url,
        config.url,
        config.secret,
        message,
        names=("PDI_NOTIFY_URL", "PDI_NOTIFY_SIGNING_SECRET"),
        who="odbiorca powiadomień",
        post=post,
        now=now,
    )
    return {**result, **sent}


def _send(
    base: str,
    target: str,
    secret: str | None,
    message: dict[str, Any],
    *,
    names: tuple[str, str],
    who: str,
    post: Post | None,
    now: int | None,
) -> dict[str, Any]:
    """Podpisany POST `message`; `{"status": "sent"}` albo `{"status": "failed", "error": …}` (bez sekretu)."""
    url = urllib.parse.urlsplit(base)
    if (
        url.username
        or url.password
        or not (url.scheme == "https" or (url.scheme == "http" and url.hostname in LOCAL_HOSTS))
    ):
        return {
            "status": "failed",
            "error": f"{names[0]} musi być adresem https:// (http tylko dla localhost), bez loginu.",
        }
    if not secret:
        return {"status": "failed", "error": f"Brak {names[1]} — wiadomość nie została wysłana."}
    body = json.dumps(message, ensure_ascii=False).encode()
    ts = str(now if now is not None else int(time.time()))
    signature = "v1=" + hmac.new(secret.encode(), ts.encode() + b"." + body, hashlib.sha256).hexdigest()
    headers = {
        "content-type": "application/json",
        "x-pdi-timestamp": ts,
        "x-pdi-event": str(message["type"]),
        "x-pdi-signature": signature,
    }
    try:
        status = (post or _post)(target, headers, body)
    except OSError:
        return {"status": "failed", "error": f"Nie udało się nawiązać połączenia: {who}."}
    if not 200 <= status < 300:
        return {"status": "failed", "error": f"{who} odpowiedział {status} na {message['type']}."}
    return {"status": "sent"}


def _post(url: str, headers: dict[str, str], body: bytes) -> int:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")  # noqa: S310 — adres sprawdzony
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310
            return int(response.status)
    except urllib.error.HTTPError as e:
        return int(e.code)
