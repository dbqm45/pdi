"""`gate.decided` do ci_for_sdlc (F4): decyzja „Approve for implementation” ustawia tam baseline historyjek zmiany.

`POST <PDI_CI_FOR_SDLC_URL>/api/webhooks/pdi`, podpis jak w pozostałych kierunkach:
`X-PDI-Signature: v1=<hex HMAC-SHA256(PDI_CI_FOR_SDLC_SIGNING_SECRET, "<X-PDI-Timestamp>.<body>")>` — ten sam sekret,
którym ci_for_sdlc podpisuje `readiness.changed` dla pdi. Błąd nie cofa decyzji; `retry_dispatch` ponawia.
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


def notify_ci_for_sdlc(
    config: NotifyConfig, event: dict[str, Any], *, at: str, post: Post | None = None, now: int | None = None
) -> dict[str, Any]:
    """Wysyła `event`; wynik `{"status": sent | skipped | failed, …}` do zapisu w stanie zmiany."""
    result: dict[str, Any] = {"status": "failed", "at": at, "event": event["id"]}
    if not config.url:
        return {**result, "status": "skipped", "error": "Brak PDI_CI_FOR_SDLC_URL — ci_for_sdlc nie dostał decyzji."}
    url = urllib.parse.urlsplit(config.url)
    if (
        url.username
        or url.password
        or not (url.scheme == "https" or (url.scheme == "http" and url.hostname in LOCAL_HOSTS))
    ):
        return {
            **result,
            "error": "PDI_CI_FOR_SDLC_URL musi być adresem https:// (http tylko dla localhost), bez loginu.",
        }
    if not config.secret:
        return {**result, "error": "Brak PDI_CI_FOR_SDLC_SIGNING_SECRET — decyzja nie została wysłana."}
    body = json.dumps(event, ensure_ascii=False).encode()
    ts = str(now if now is not None else int(time.time()))
    signature = "v1=" + hmac.new(config.secret.encode(), ts.encode() + b"." + body, hashlib.sha256).hexdigest()
    headers = {
        "content-type": "application/json",
        "x-pdi-timestamp": ts,
        "x-pdi-event": str(event["type"]),
        "x-pdi-signature": signature,
    }
    try:
        status = (post or _post)(config.url.rstrip("/") + PATH, headers, body)
    except OSError:
        return {**result, "error": "Nie udało się nawiązać połączenia z ci_for_sdlc."}
    if not 200 <= status < 300:
        return {**result, "error": f"ci_for_sdlc odpowiedział {status} na gate.decided."}
    return {**result, "status": "sent"}


def _post(url: str, headers: dict[str, str], body: bytes) -> int:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")  # noqa: S310 — adres sprawdzony
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310
            return int(response.status)
    except urllib.error.HTTPError as e:
        return int(e.code)
