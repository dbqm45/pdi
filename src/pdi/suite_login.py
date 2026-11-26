"""Logowanie do konsoli pdi przez tożsamość suity (docs/plan-konsola-tozsamosc.md; ADR 17 §3, krok 4).

Kod autoryzacji z PKCE wobec `dbqm45/di-identity` (Keycloak, realm `suite`, klient `di-decision`). ID token sprawdzany
tutaj: tylko RS256, klucz z JWKS wystawcy (nigdy wskazany przez sam token), `iss`, `aud`, `azp`, `exp`, `nonce` —
te same zasady co w DI Release Control, DI Definition i DI Release. Token nie niesie e-maila (DI3).

Dostęp: członek organizacji `PDI_SUITE_ORGANIZATION` z rolą klienta — `editor` albo `admin` decyduje przyciskami,
`viewer` tylko czyta. Sesje w pamięci procesu: restart konsoli wymaga ponownego logowania.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

DEFAULT_CLIENT_ID = "di-decision"
CLOCK_SKEW_SECONDS = 60
TIMEOUT_SECONDS = 5
LOGIN_TTL_SECONDS = 10 * 60
SESSION_TTL_SECONDS = 12 * 60 * 60
MAX_RESPONSE = 256 * 1024

Access = Literal["decide", "read"]


class SuiteSignInError(Exception):
    """Wystawca odmówił albo odpowiedział czymś, czego klient nie przyjmuje (502); bez tokenu w treści."""


class UnknownKey(SuiteSignInError):
    """Token podpisany kluczem, którego nie ma w JWKS wystawcy (może być po rotacji kluczy)."""


class Refused(Exception):
    """Osoba zalogowana, ale bez dostępu do konsoli (403): spoza organizacji albo bez roli."""


@dataclass(frozen=True)
class SuiteConfig:
    issuer: str
    client_id: str
    client_secret: str
    organization: str


@dataclass(frozen=True)
class Person:
    sub: str
    name: str
    organizations: tuple[str, ...]
    roles: tuple[str, ...]


@dataclass(frozen=True)
class Checks:
    state: str
    nonce: str
    verifier: str


class Http(Protocol):
    def get_json(self, url: str) -> Any: ...

    def post_form(self, url: str, data: dict[str, str]) -> Any: ...


class UrllibHttp:
    """Prawdziwe żądania do wystawcy: JSON, limit czasu i rozmiaru, bez przekierowań do innych hostów."""

    def _read(self, req: urllib.request.Request) -> Any:
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:  # noqa: S310 — adres wystawcy z konfiguracji
                body = resp.read(MAX_RESPONSE + 1)
        except urllib.error.HTTPError as e:
            raise SuiteSignInError(f"{urllib.parse.urlsplit(req.full_url).path}: HTTP {e.code}") from e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise SuiteSignInError(f"wystawca nieosiągalny: {type(e).__name__}") from e
        if len(body) > MAX_RESPONSE:
            raise SuiteSignInError("odpowiedź wystawcy za duża")
        try:
            return json.loads(body)
        except ValueError as e:
            raise SuiteSignInError("odpowiedź wystawcy to nie JSON") from e

    def get_json(self, url: str) -> Any:
        return self._read(urllib.request.Request(url, headers={"accept": "application/json"}))  # noqa: S310

    def post_form(self, url: str, data: dict[str, str]) -> Any:
        body = urllib.parse.urlencode(data).encode()
        headers = {"accept": "application/json", "content-type": "application/x-www-form-urlencoded"}
        return self._read(urllib.request.Request(url, data=body, headers=headers, method="POST"))  # noqa: S310


def config_from_env(env: Mapping[str, str]) -> SuiteConfig | None:
    """Ustawienia z `PDI_SUITE_*`; None, gdy logowanie przez suitę jest wyłączone.

    Połowiczne albo niebezpieczne ustawienia → ValueError."""
    issuer = (env.get("PDI_SUITE_ISSUER") or "").strip()
    secret = (env.get("PDI_SUITE_CLIENT_SECRET") or "").strip()
    organization = (env.get("PDI_SUITE_ORGANIZATION") or "").strip()
    if not issuer and not secret and not organization:
        return None
    missing = [k for k, v in (("PDI_SUITE_ISSUER", issuer), ("PDI_SUITE_CLIENT_SECRET", secret),
                              ("PDI_SUITE_ORGANIZATION", organization)) if not v]  # fmt: skip
    if missing:
        raise ValueError(f"Logowanie przez suitę wymaga także: {', '.join(missing)}.")
    parts = urllib.parse.urlsplit(issuer)
    local = parts.hostname in ("localhost", "127.0.0.1")
    if parts.scheme != "https" and not (parts.scheme == "http" and local):
        raise ValueError("PDI_SUITE_ISSUER musi być https (http tylko na localhost).")
    client_id = (env.get("PDI_SUITE_CLIENT_ID") or "").strip() or DEFAULT_CLIENT_ID
    return SuiteConfig(issuer=issuer, client_id=client_id, client_secret=secret, organization=organization)


def access(person: Person, config: SuiteConfig) -> Access:
    """Co osoba może w konsoli: `decide` (editor, admin), `read` (viewer); inaczej Refused z powodem."""
    if config.organization not in person.organizations:
        raise Refused("Your suite account is not a member of the organization that uses this pdi console.")
    if "admin" in person.roles or "editor" in person.roles:
        return "decide"
    if "viewer" in person.roles:
        return "read"
    raise Refused("Your suite account has no role in DI Decision. Ask an administrator to grant you one.")


def _b64decode(segment: str) -> bytes:
    if not segment or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in segment):
        raise SuiteSignInError("ID token to nie JWT")
    return base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))


def _json_part(segment: str) -> dict[str, Any]:
    try:
        value = json.loads(_b64decode(segment))
    except ValueError as e:
        raise SuiteSignInError("ID token to nie JSON") from e
    if not isinstance(value, dict):
        raise SuiteSignInError("ID token to nie obiekt JSON")
    return value


def _strings(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list):
        return tuple(v for v in value if isinstance(v, str))
    return ()


def signed_claims(token: str, keys: Any) -> dict[str, Any]:
    """Treść JWT podpisanego RS256 kluczem z JWKS wystawcy (`keys`), wybranym po `kid`; inaczej SuiteSignInError.

    Klucz nigdy nie pochodzi z samego tokenu; `alg` musi być RS256. Roszczeń (`iss`, `aud`, `exp`) nie sprawdza."""
    parts = token.split(".")
    if len(parts) != 3:
        raise SuiteSignInError("ID token to nie JWT")
    header = _json_part(parts[0])
    if header.get("alg") != "RS256":
        raise SuiteSignInError("ID token nie jest podpisany RS256")
    jwk = next(
        (k for k in keys or [] if isinstance(k, dict) and k.get("kid") == header.get("kid") and k.get("kty") == "RSA"),
        None,
    )
    if jwk is None or not isinstance(jwk.get("n"), str) or not isinstance(jwk.get("e"), str):
        raise UnknownKey("ID token podpisany nieznanym kluczem")
    public = rsa.RSAPublicNumbers(
        e=int.from_bytes(_b64decode(jwk["e"]), "big"), n=int.from_bytes(_b64decode(jwk["n"]), "big")
    ).public_key()
    try:
        public.verify(_b64decode(parts[2]), f"{parts[0]}.{parts[1]}".encode(), padding.PKCS1v15(), hashes.SHA256())
    except InvalidSignature as e:
        raise SuiteSignInError("podpis ID tokenu się nie zgadza") from e
    return _json_part(parts[1])


def _random() -> str:
    return secrets.token_urlsafe(32)


class SuiteClient:
    """Klient jednego wystawcy: `start()` daje adres logowania i sprawdziany, `finish()` sprawdza ID token."""

    def __init__(self, config: SuiteConfig, *, redirect_uri: str, http: Http | None = None,
                 now: Callable[[], float] = time.time) -> None:  # fmt: skip
        self.config = config
        self.redirect_uri = redirect_uri
        self.http: Http = http or UrllibHttp()
        self.now = now
        self._discovery: tuple[dict[str, Any], float] | None = None

    def _discover(self) -> dict[str, Any]:
        if self._discovery and self.now() - self._discovery[1] < 3600:
            return self._discovery[0]
        meta = self.http.get_json(f"{self.config.issuer.rstrip('/')}/.well-known/openid-configuration")
        if not isinstance(meta, dict) or meta.get("issuer") != self.config.issuer:
            raise SuiteSignInError("wystawca podaje inny issuer")
        for key in ("authorization_endpoint", "token_endpoint", "jwks_uri"):
            if not isinstance(meta.get(key), str):
                raise SuiteSignInError(f"metadane wystawcy bez {key}")
        self._discovery = (meta, self.now())
        return meta

    def start(self) -> tuple[str, Checks]:
        meta = self._discover()
        checks = Checks(state=_random(), nonce=_random(), verifier=_random())
        challenge = base64.urlsafe_b64encode(hashlib.sha256(checks.verifier.encode()).digest()).rstrip(b"=").decode()
        query = urllib.parse.urlencode({
            "client_id": self.config.client_id,
            "response_type": "code",
            "scope": "openid profile",
            "redirect_uri": self.redirect_uri,
            "state": checks.state,
            "nonce": checks.nonce,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        })  # fmt: skip
        return f"{meta['authorization_endpoint']}?{query}", checks

    def finish(self, code: str, checks: Checks) -> Person:
        meta = self._discover()
        tokens = self.http.post_form(meta["token_endpoint"], {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "code_verifier": checks.verifier,
        })  # fmt: skip
        id_token = tokens.get("id_token") if isinstance(tokens, dict) else None
        if not isinstance(id_token, str):
            raise SuiteSignInError("wystawca nie dał ID tokenu")
        jwks = self.http.get_json(meta["jwks_uri"])
        claims = signed_claims(id_token, jwks.get("keys") if isinstance(jwks, dict) else None)
        if claims.get("iss") != self.config.issuer:
            raise SuiteSignInError("ID token od innego wystawcy")
        if self.config.client_id not in _strings(claims.get("aud")):
            raise SuiteSignInError("ID token dla innej aplikacji")
        # Keycloak dopisuje do `aud` każdą aplikację, w której osoba ma role; `azp` mówi, komu go wydano.
        if "azp" in claims and claims["azp"] != self.config.client_id:
            raise SuiteSignInError("ID token wydany innej aplikacji")
        exp = claims.get("exp")
        if not isinstance(exp, int | float) or exp + CLOCK_SKEW_SECONDS < self.now():
            raise SuiteSignInError("ID token wygasł")
        nonce = claims.get("nonce")
        if not isinstance(nonce, str) or not hmac.compare_digest(nonce.encode(), checks.nonce.encode()):
            raise SuiteSignInError("ID token z innego logowania")
        sub = claims.get("sub")
        if not isinstance(sub, str) or not sub or len(sub) > 200:
            raise SuiteSignInError("ID token bez osoby")
        name = next(
            (v for v in (claims.get("name"), claims.get("preferred_username")) if isinstance(v, str) and v.strip()), sub
        )
        access_claim = claims.get("resource_access")
        own = access_claim.get(self.config.client_id) if isinstance(access_claim, dict) else None
        roles = _strings(own.get("roles")) if isinstance(own, dict) else ()
        return Person(sub=sub, name=name.strip()[:200], organizations=_strings(claims.get("organization")), roles=roles)


@dataclass(frozen=True)
class Session:
    sub: str
    name: str
    access: Access
    expires_at: float
    admin: bool = False  # rola admin w DI Decision (T7: eskalacja typów chronionych tylko do admina)


class SuiteLogin:
    """Logowanie konsoli: klient wystawcy, logowania w toku (`state` → sprawdziany) i sesje — w pamięci procesu."""

    def __init__(self, config: SuiteConfig, *, http: Http | None = None, now: Callable[[], float] = time.time) -> None:
        self.config = config
        self.http = http
        self.now = now
        self._client: SuiteClient | None = None
        self._pending: dict[str, tuple[Checks, float]] = {}
        self._sessions: dict[str, Session] = {}
        self._lock = threading.Lock()

    def client(self, redirect_uri: str) -> SuiteClient:
        if self._client is None or self._client.redirect_uri != redirect_uri:
            self._client = SuiteClient(self.config, redirect_uri=redirect_uri, http=self.http, now=self.now)
        return self._client

    def begin(self, redirect_uri: str) -> tuple[str, str]:
        """Adres logowania u wystawcy i `state` do ciasteczka logowania."""
        url, checks = self.client(redirect_uri).start()
        with self._lock:
            now = self.now()
            self._pending = {k: v for k, v in self._pending.items() if v[1] > now}
            self._pending[checks.state] = (checks, now + LOGIN_TTL_SECONDS)
        return url, checks.state

    def complete(self, redirect_uri: str, *, code: str, state: str, cookie_state: str) -> tuple[str, Session]:
        """Kończy logowanie: identyfikator nowej sesji (do ciasteczka) i sesja. KeyError — logowanie nieznane albo
        przeterminowane; SuiteSignInError — wystawca/token; Refused — brak dostępu."""
        with self._lock:
            entry = self._pending.pop(state, None)
        if (
            entry is None
            or not cookie_state
            or not hmac.compare_digest(cookie_state.encode(), state.encode())
            or entry[1] < self.now()
        ):
            raise KeyError(state)
        person = self.client(redirect_uri).finish(code, entry[0])
        level = access(person, self.config)
        session_id = secrets.token_urlsafe(32)
        session = Session(
            sub=person.sub,
            name=person.name,
            access=level,
            expires_at=self.now() + SESSION_TTL_SECONDS,
            admin="admin" in person.roles,
        )
        with self._lock:
            self._sessions[hashlib.sha256(session_id.encode()).hexdigest()] = session
        return session_id, session

    def session(self, session_id: str | None) -> Session | None:
        if not session_id:
            return None
        key = hashlib.sha256(session_id.encode()).hexdigest()
        with self._lock:
            found = self._sessions.get(key)
            if found is not None and found.expires_at < self.now():
                del self._sessions[key]
                return None
        return found

    def end(self, session_id: str | None) -> None:
        if session_id:
            with self._lock:
                self._sessions.pop(hashlib.sha256(session_id.encode()).hexdigest(), None)
