import hashlib
import hmac
import json

import pytest

from pdi.notify import NotifyConfig, notify_ci_for_sdlc

AT = "2026-10-26T10:00:00Z"
SECRET = "wspolny-z-ci"  # noqa: S105 — sekret testowy
EVENT = {
    "id": "gate.decided-evt-1",
    "type": "gate.decided",
    "occurred_at": AT,
    "source": "pdi",
    "contract_version": "0.4.0",
    "payload": {"change": "CHG-12", "gate": "approve-for-implementation", "outcome": "approved", "decision": "DEC-1"},
}


class FakeCi:
    def __init__(self, status: int = 200, error: Exception | None = None) -> None:
        self.status = status
        self.error = error
        self.calls: list[tuple[str, dict[str, str], bytes]] = []

    def __call__(self, url: str, headers: dict[str, str], body: bytes) -> int:
        self.calls.append((url, headers, body))
        if self.error:
            raise self.error
        return self.status


def test_sends_signed_gate_decided_to_ci_for_sdlc() -> None:
    ci = FakeCi()

    result = notify_ci_for_sdlc(
        NotifyConfig(url="https://ci.example.com/", secret=SECRET), EVENT, at=AT, post=ci, now=1793000000
    )

    url, headers, body = ci.calls[0]
    assert url == "https://ci.example.com/api/webhooks/pdi"
    assert json.loads(body) == EVENT
    assert headers["x-pdi-event"] == "gate.decided"
    assert headers["x-pdi-timestamp"] == "1793000000"
    want = "v1=" + hmac.new(SECRET.encode(), b"1793000000." + body, hashlib.sha256).hexdigest()
    assert headers["x-pdi-signature"] == want
    assert result == {"status": "sent", "at": AT, "event": "gate.decided-evt-1"}


def test_without_url_or_secret_nothing_is_sent() -> None:
    ci = FakeCi()

    assert notify_ci_for_sdlc(NotifyConfig(url=None, secret=SECRET), EVENT, at=AT, post=ci)["status"] == "skipped"
    failed = notify_ci_for_sdlc(NotifyConfig(url="https://ci.example.com", secret=None), EVENT, at=AT, post=ci)
    assert failed["status"] == "failed"
    assert "PDI_CI_FOR_SDLC_SIGNING_SECRET" in failed["error"]
    assert ci.calls == []


@pytest.mark.parametrize("url", ["http://ci.example.com", "ftp://ci.example.com", "https://user:pw@ci.example.com"])
def test_insecure_url_is_refused(url: str) -> None:
    ci = FakeCi()

    result = notify_ci_for_sdlc(NotifyConfig(url=url, secret=SECRET), EVENT, at=AT, post=ci)

    assert (result["status"], ci.calls) == ("failed", [])


def test_local_http_is_allowed() -> None:
    ci = FakeCi()

    assert (
        notify_ci_for_sdlc(NotifyConfig(url="http://127.0.0.1:4317", secret=SECRET), EVENT, at=AT, post=ci)["status"]
        == "sent"
    )


@pytest.mark.parametrize(
    ("ci", "fragment"),
    [(FakeCi(status=401), "401"), (FakeCi(error=OSError(f"boom {SECRET}")), "połączenia")],
    ids=["odmowa", "siec"],
)
def test_failure_is_reported_without_the_secret(ci: FakeCi, fragment: str) -> None:
    result = notify_ci_for_sdlc(NotifyConfig(url="https://ci.example.com", secret=SECRET), EVENT, at=AT, post=ci)

    assert result["status"] == "failed"
    assert fragment in result["error"]
    assert SECRET not in json.dumps(result)


def test_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PDI_CI_FOR_SDLC_URL", "https://ci.example.com")
    monkeypatch.setenv("PDI_CI_FOR_SDLC_SIGNING_SECRET", SECRET)

    cfg = NotifyConfig.from_env()

    assert (cfg.url, cfg.secret) == ("https://ci.example.com", SECRET)
    assert SECRET not in repr(cfg)
