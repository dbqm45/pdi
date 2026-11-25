"""Konsola pdi na tożsamości suity (docs/plan-konsola-tozsamosc.md, ADR 17 §3 krok 4).

Fałszywy wystawca OIDC w procesie (discovery, JWKS, token endpoint sprawdzający PKCE), wstrzyknięty jako `http` klienta,
z roszczeniami takimi, jakie realm `suite` daje klientowi `di-decision` (Keycloak 26.4.7, di-identity 0.1.3):
bez e-maila.
"""

from __future__ import annotations

import base64
import hashlib
import http.client
import json
import threading
import time
import urllib.parse
from pathlib import Path
from typing import Any

import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from pdi import console, suite_login
from pdi.inbox import Inbox
from pdi.registry import Registry

ISSUER = "http://localhost:8180/realms/suite"
CONFIG = suite_login.SuiteConfig(
    issuer=ISSUER,
    client_id="di-decision",
    client_secret="dummy-suite-secret",  # noqa: S106 — fałszywy wystawca w teście
    organization="acme",  # noqa: S106
)
OLD_TOKEN = "stary-token-konsoli-w-url"  # noqa: S105 — nazwa zmiennej, nie hasło


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _int_b64(n: int) -> str:
    return _b64(n.to_bytes((n.bit_length() + 7) // 8, "big"))


def _person(
    roles: list[str], organization: list[str] | None = None, sub: str = "sub-1", name: str = "Ola Test"
) -> dict[str, Any]:
    return {
        "sub": sub,
        "name": name,
        "preferred_username": "ola.test",
        "organization": ["acme"] if organization is None else organization,
        "resource_access": {
            "account": {"roles": ["view-profile"]},
            "di-decision": {"roles": roles},
            "di-release": {"roles": ["admin"]},
        },
    }


class FakeIssuer:
    """Discovery, JWKS i token endpoint; `claims`, `tamper` i `key` ustawia test."""

    def __init__(self) -> None:
        self.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.stranger = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.signing = self.key
        self.claims: dict[str, Any] = _person(["editor"])
        self.tamper: Any = lambda c: c
        self.grants: dict[str, tuple[str, str]] = {}
        self.token_forms: list[dict[str, str]] = []

    def get_json(self, url: str) -> Any:
        if url == f"{ISSUER}/.well-known/openid-configuration":
            return {
                "issuer": ISSUER,
                "authorization_endpoint": f"{ISSUER}/protocol/openid-connect/auth",
                "token_endpoint": f"{ISSUER}/protocol/openid-connect/token",
                "jwks_uri": f"{ISSUER}/protocol/openid-connect/certs",
            }
        if url == f"{ISSUER}/protocol/openid-connect/certs":
            pub = self.key.public_key().public_numbers()
            return {
                "keys": [
                    {
                        "kid": "k1",
                        "kty": "RSA",
                        "alg": "RS256",
                        "use": "sig",
                        "n": _int_b64(pub.n),
                        "e": _int_b64(pub.e),
                    }
                ]
            }
        raise suite_login.SuiteSignInError(f"nieznany adres {url}")

    def post_form(self, url: str, data: dict[str, str]) -> Any:
        assert url == f"{ISSUER}/protocol/openid-connect/token"
        self.token_forms.append(data)
        grant = self.grants.get(data.get("code", ""))
        challenge = _b64(hashlib.sha256(data.get("code_verifier", "").encode()).digest())
        if grant is None or challenge != grant[1]:
            raise suite_login.SuiteSignInError("invalid_grant")
        now = int(time.time())
        claims = self.tamper({"iss": ISSUER, "aud": "di-decision", "azp": "di-decision", "typ": "ID", "iat": now,
                              "exp": now + 300, "nonce": grant[0], **self.claims})  # fmt: skip
        head = _b64(json.dumps({"alg": "RS256", "typ": "JWT", "kid": "k1"}).encode())
        body = _b64(json.dumps(claims).encode())
        sig = self.signing.sign(f"{head}.{body}".encode(), padding.PKCS1v15(), hashes.SHA256())
        return {"access_token": "dummy", "token_type": "Bearer", "id_token": f"{head}.{body}.{_b64(sig)}"}

    def approve(self, location: str) -> str:
        """Gra osobę logującą się u wystawcy: zapytanie powrotu dla żądania autoryzacji z `location`."""
        q = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(location).query))
        code = f"code-{len(self.grants)}"
        self.grants[code] = (q["nonce"], q["code_challenge"])
        return f"code={code}&state={q['state']}"


# --- klient OIDC i konfiguracja ---


def test_config_from_env_needs_all_three_and_https_except_localhost() -> None:
    assert suite_login.config_from_env({}) is None
    env = {"PDI_SUITE_ISSUER": ISSUER, "PDI_SUITE_CLIENT_SECRET": "s", "PDI_SUITE_ORGANIZATION": "acme"}
    assert suite_login.config_from_env(env) == suite_login.SuiteConfig(ISSUER, "di-decision", "s", "acme")
    with pytest.raises(ValueError, match="PDI_SUITE_ORGANIZATION"):
        suite_login.config_from_env({"PDI_SUITE_ISSUER": ISSUER, "PDI_SUITE_CLIENT_SECRET": "s"})
    with pytest.raises(ValueError, match="https"):
        suite_login.config_from_env({**env, "PDI_SUITE_ISSUER": "http://id.example.com/realms/suite"})


def test_access_from_the_token_editor_and_admin_decide_viewer_reads() -> None:
    def person(roles: list[str], orgs: tuple[str, ...] = ("acme",)) -> suite_login.Person:
        return suite_login.Person(sub="s", name="n", organizations=orgs, roles=tuple(roles))

    assert suite_login.access(person(["admin"]), CONFIG) == "decide"
    assert suite_login.access(person(["editor"]), CONFIG) == "decide"
    assert suite_login.access(person(["viewer"]), CONFIG) == "read"
    with pytest.raises(suite_login.Refused, match="no role"):
        suite_login.access(person([]), CONFIG)
    with pytest.raises(suite_login.Refused, match="not a member"):
        suite_login.access(person(["admin"], ("globex",)), CONFIG)


@pytest.mark.parametrize(
    "spoil",
    ["key", "aud", "azp", "nonce", "exp", "iss"],
)
def test_finish_refuses_a_bad_id_token(spoil: str) -> None:
    fake = FakeIssuer()
    client = suite_login.SuiteClient(CONFIG, redirect_uri="http://127.0.0.1:8788/callback", http=fake)
    url, checks = client.start()
    if spoil == "key":
        fake.signing = fake.stranger
    else:
        changes = {"aud": {"aud": "di-release"}, "azp": {"azp": "di-release"}, "nonce": {"nonce": "x" * 30},
                   "exp": {"exp": int(time.time()) - 600},
                   "iss": {"iss": "http://localhost:8180/realms/other"}}  # fmt: skip
        fake.tamper = lambda c: {**c, **changes[spoil]}
    code = dict(urllib.parse.parse_qsl(fake.approve(url)))["code"]
    with pytest.raises(suite_login.SuiteSignInError):
        client.finish(code, checks)


def test_start_asks_with_pkce_state_and_nonce_without_email() -> None:
    fake = FakeIssuer()
    client = suite_login.SuiteClient(CONFIG, redirect_uri="http://127.0.0.1:8788/callback", http=fake)
    url, checks = client.start()
    parts = urllib.parse.urlsplit(url)
    q = dict(urllib.parse.parse_qsl(parts.query))
    assert f"{parts.scheme}://{parts.netloc}{parts.path}" == f"{ISSUER}/protocol/openid-connect/auth"
    assert q["client_id"] == "di-decision"
    assert q["scope"] == "openid profile"
    assert q["redirect_uri"] == "http://127.0.0.1:8788/callback"
    assert q["code_challenge_method"] == "S256"
    assert q["code_challenge"] == _b64(hashlib.sha256(checks.verifier.encode()).digest())
    assert q["state"] == checks.state and q["nonce"] == checks.nonce
    person = client.finish(dict(urllib.parse.parse_qsl(fake.approve(url)))["code"], checks)
    assert person == suite_login.Person(sub="sub-1", name="Ola Test", organizations=("acme",), roles=("editor",))
    assert fake.token_forms[-1]["client_secret"] == "dummy-suite-secret"  # noqa: S105 — fałszywy wystawca


# --- konsola w trybie suity ---


@pytest.fixture
def registry(tmp_path: Path) -> Registry:
    r = Registry(tmp_path / "registry")
    r.root.mkdir(parents=True, exist_ok=True)
    return r


def _write_inbox_gate(registry: Registry) -> dict[str, Any]:
    (registry.root / "changes").mkdir(parents=True, exist_ok=True)
    change = {"change": "CHG-1", "status": "open", "approved": {}, "waiting": ["B2"], "history": []}
    (registry.root / "changes" / "CHG-1.yaml").write_text(json.dumps(change), encoding="utf-8")
    (registry.root / "inbox").mkdir(parents=True, exist_ok=True)
    item = {
        "id": "evt-1", "kind": "gate", "status": "open", "change": "CHG-1", "source": "tf", "release": None,
        "summary": "Prośba o bramkę B2", "received_at": "2026-11-06T10:00:00Z", "gate": "B2", "missing_before": [],
        "event": {"id": "evt-1", "type": "gate.requested", "occurred_at": "2026-11-06T10:00:00Z", "source": "tf",
                  "contract_version": "0.11.0", "payload": {"change": "CHG-1", "gate": "B2"}},
    }  # fmt: skip
    (registry.root / "inbox" / "evt-1.yaml").write_text(json.dumps(item), encoding="utf-8")
    return item


class Console:
    """Konsola w trybie suity na wolnym porcie, z klientem bez podążania za przekierowaniami."""

    def __init__(self, registry: Registry, fake: FakeIssuer, monkeypatch: pytest.MonkeyPatch) -> None:
        deps = console.Deps(registry, checkout=None)
        monkeypatch.setattr(deps.inbox, "_check_pr", lambda item: None)
        self.fake = fake
        self.server = console.make_server(
            deps, token=OLD_TOKEN, port=0, suite=suite_login.SuiteLogin(CONFIG, http=fake)
        )
        self.port = self.server.server_port
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def request(self, method: str, path: str, *, cookie: str = "", form: dict[str, str] | None = None,
                origin: bool = True) -> tuple[int, dict[str, str], str, list[str]]:  # fmt: skip
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        headers = {"cookie": cookie} if cookie else {}
        body = None
        if form is not None:
            body = urllib.parse.urlencode(form)
            headers["content-type"] = "application/x-www-form-urlencoded"
            if origin:
                headers["origin"] = f"http://127.0.0.1:{self.port}"
        conn.request(method, path, body=body, headers=headers)
        resp = conn.getresponse()
        data = resp.read().decode("utf-8", "replace")
        cookies = resp.headers.get_all("set-cookie") or []
        out = (resp.status, {k.lower(): v for k, v in resp.getheaders()}, data, cookies)
        conn.close()
        return out

    def sign_in(self) -> tuple[int, str, str]:
        """Całe logowanie: status powrotu, treść i para `pdi_session=…` (pusta, gdy sesji nie ma)."""
        status, headers, _, cookies = self.request("GET", "/login")
        assert status == 302
        login = next(c for c in cookies if c.startswith("pdi_login=")).split(";")[0]
        back, _, body, cookies = self.request(
            "GET", f"/callback?{self.fake.approve(headers['location'])}", cookie=login
        )
        session = next(
            (c.split(";")[0] for c in cookies if c.startswith("pdi_session=") and not c.startswith("pdi_session=;")), ""
        )
        return back, body, session

    def close(self) -> None:
        self.server.shutdown()


@pytest.fixture
def suite_console(registry: Registry, monkeypatch: pytest.MonkeyPatch) -> Any:
    app = Console(registry, FakeIssuer(), monkeypatch)
    yield app
    app.close()


def test_pages_need_a_session_and_the_old_token_alone_opens_nothing(suite_console: Console) -> None:
    status, headers, _, _ = suite_console.request("GET", "/board")
    assert status == 302 and headers["location"] == "/login"
    status, headers, _, _ = suite_console.request("GET", f"/board?t={OLD_TOKEN}")
    assert status == 302 and headers["location"] == "/login"
    status, headers, _, cookies = suite_console.request("GET", "/login")
    assert status == 302 and headers["location"].startswith(f"{ISSUER}/protocol/openid-connect/auth?")
    login = next(c for c in cookies if c.startswith("pdi_login="))
    assert "HttpOnly" in login and "SameSite=Lax" in login and "Path=/callback" in login


def test_a_viewer_reads_without_any_token_in_the_page_but_cannot_decide(
    suite_console: Console, registry: Registry
) -> None:
    item = _write_inbox_gate(registry)
    suite_console.fake.claims = _person(["viewer"])
    back, _, session = suite_console.sign_in()
    assert back == 302 and session
    cookie_line = session
    status, _, page, _ = suite_console.request("GET", "/inbox", cookie=cookie_line)
    assert status == 200
    assert OLD_TOKEN not in page
    assert "Ola Test" in page  # kto jest zalogowany
    assert 'class="read-only"' in page  # przyciski decyzji schowane, z wyjaśnieniem
    form = {"t": "", "loaded_at": item["received_at"], "statement": "Tak.", "why": "Bo tak.", "outcome": "approved"}
    status, _, _, _ = suite_console.request("POST", "/inbox/evt-1/decide", cookie=cookie_line, form=form)
    assert status == 403
    assert Inbox(registry).items(status="decided") == []


def test_an_editor_decides_and_the_decision_names_them(suite_console: Console, registry: Registry) -> None:
    item = _write_inbox_gate(registry)
    suite_console.fake.claims = _person(["editor"], name="Ewa Decydentka")
    _, _, session = suite_console.sign_in()
    form = {"t": "", "loaded_at": item["received_at"], "statement": "Zatwierdzam.", "why": "Wymagania są pełne.",
            "outcome": "approved"}  # fmt: skip
    status, _, _, _ = suite_console.request("POST", "/inbox/evt-1/decide", cookie=session, form=form)
    assert status == 200
    decided = Inbox(registry).items(status="decided")
    assert len(decided) == 1
    decision = registry.get(decided[0]["decision"])
    assert decision["decided_by"] == "Ewa Decydentka"
    assert decision["decided_by_id"] == "sub-1"  # `sub` osoby z tokenu (kontrakt 0.25.0)
    assert decision["source"]["kind"] == "console"
    # Bez nagłówka Origin/Referer zmiana jest odrzucona (sesja w ciasteczku, nie w treści).
    status, _, _, _ = suite_console.request("POST", "/inbox/evt-1/decide", cookie=session, form=form, origin=False)
    assert status == 403


@pytest.mark.parametrize(
    ("claims", "reason"),
    [(_person(["admin"], ["globex"]), "not a member"), (_person([]), "no role")],
)
def test_people_without_access_are_refused_with_a_reason(
    suite_console: Console, claims: dict[str, Any], reason: str
) -> None:
    suite_console.fake.claims = claims
    back, body, session = suite_console.sign_in()
    assert back == 403 and not session
    assert reason in body


def test_a_forged_callback_and_a_bad_token_get_no_session(suite_console: Console) -> None:
    status, _, _, cookies = suite_console.request("GET", "/callback?code=x&state=y")
    assert status == 400 and not any(c.startswith("pdi_session=") and "Max-Age=0" not in c for c in cookies)
    suite_console.fake.signing = suite_console.fake.stranger
    back, _, session = suite_console.sign_in()
    assert back == 502 and not session
    assert len(suite_console.fake.token_forms) == 1


def test_logout_ends_the_session(suite_console: Console) -> None:
    _, _, session = suite_console.sign_in()
    assert suite_console.request("GET", "/board", cookie=session)[0] == 200
    status, _, _, cookies = suite_console.request("POST", "/logout", cookie=session, form={})
    assert status == 302
    assert any(c.startswith("pdi_session=") and "Max-Age=0" in c for c in cookies)
    assert suite_console.request("GET", "/board", cookie=session)[0] == 302


def test_main_needs_no_console_token_with_the_suite(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PDI_REGISTRY_PATH", str(tmp_path))
    monkeypatch.delenv("PDI_CONSOLE_TOKEN", raising=False)
    monkeypatch.setenv("PDI_SUITE_ISSUER", ISSUER)
    monkeypatch.setenv("PDI_SUITE_CLIENT_SECRET", "s")
    monkeypatch.setenv("PDI_SUITE_ORGANIZATION", "acme")
    built: dict[str, Any] = {}

    def fake_make_server(deps: Any, **kwargs: Any) -> Any:
        built.update(kwargs)
        raise SystemExit(0)

    monkeypatch.setattr(console, "make_server", fake_make_server)
    with pytest.raises(SystemExit):
        console.main()
    assert built["suite"] is not None
    assert built["suite"].config.organization == "acme"
