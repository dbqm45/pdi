"""Autoryzacja zdalnego serwera MCP pdi tokenami suity (docs/plan-mcp-zdalny.md; ADR 17).

pdi jest tu tylko serwerem zasobów DI Decision: tokeny wydaje Keycloak z `dbqm45/di-identity` (realm `suite`), a
Claude Code loguje osobę klientem publicznym `di-decision-mcp` (PKCE). Token dostępu sprawdzany tutaj: RS256 z
kluczem z JWKS wystawcy (nigdy wskazanym przez sam token), `iss`, `aud` (`di-decision`), `azp`, `exp`. Bez e-maila
(DI3).

Dostęp jak w konsoli (`suite_login.access`): członek organizacji `PDI_SUITE_ORGANIZATION`; `editor` i `admin` mogą
też zapisywać, `viewer` tylko czyta. Agent (DI4: `kind` agent z właścicielem) tylko czyta, bez względu na role.
"""

from __future__ import annotations

import time
import urllib.parse
from collections.abc import Callable, Mapping
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Literal

import anyio.to_thread
from mcp.server.auth.provider import AccessToken, TokenVerifier

from pdi.suite_login import (
    CLOCK_SKEW_SECONDS,
    Http,
    SuiteSignInError,
    UnknownKey,
    UrllibHttp,
    _strings,
    signed_claims,
)

DEFAULT_PORT = 8790
AUDIENCE = "di-decision"
CLIENT_ID = "di-decision-mcp"
# Jedyny zakres, o który prosi klient MCP (metadane zasobu): bez tego wziąłby całą listę wystawcy, z `email` (DI3) i
# `offline_access`, i Keycloak odmówiłby logowania. Role i organizacja przychodzą w domyślnych zakresach klienta.
SCOPES = ["openid"]
DISCOVERY_TTL_SECONDS = 3600
JWKS_REFRESH_SECONDS = 300

Access = Literal["write", "read"]


@dataclass(frozen=True)
class McpAuthConfig:
    issuer: str
    organization: str
    resource_url: str
    audience: str = AUDIENCE
    client_id: str = CLIENT_ID


def config_from_env(env: Mapping[str, str]) -> McpAuthConfig | None:
    """Ustawienia z `PDI_SUITE_ISSUER`, `PDI_SUITE_ORGANIZATION` i `PDI_MCP_PORT`; None bez wystawcy.

    Serwer słucha tylko na 127.0.0.1 (lokalnie, przed hostingiem). Wystawca https, http tylko na localhost."""
    issuer = (env.get("PDI_SUITE_ISSUER") or "").strip()
    if not issuer:
        return None
    organization = (env.get("PDI_SUITE_ORGANIZATION") or "").strip()
    if not organization:
        raise ValueError("Zdalny serwer MCP wymaga także PDI_SUITE_ORGANIZATION.")
    parts = urllib.parse.urlsplit(issuer)
    local = parts.hostname in ("localhost", "127.0.0.1")
    if parts.scheme != "https" and not (parts.scheme == "http" and local):
        raise ValueError("PDI_SUITE_ISSUER musi być https (http tylko na localhost).")
    port = int((env.get("PDI_MCP_PORT") or "").strip() or DEFAULT_PORT)
    return McpAuthConfig(issuer=issuer, organization=organization, resource_url=f"http://127.0.0.1:{port}/mcp")


@dataclass(frozen=True)
class Caller:
    """Kto woła narzędzie: `access` None oznacza odmowę z powodem `reason` (po angielsku, jak w konsoli)."""

    sub: str
    name: str
    kind: Literal["person", "agent"]
    access: Access | None
    reason: str = ""


def caller(claims: Mapping[str, Any], config: McpAuthConfig) -> Caller:
    sub = str(claims.get("sub") or "")
    name = next(
        (v for v in (claims.get("name"), claims.get("preferred_username")) if isinstance(v, str) and v.strip()), sub
    )
    kind: Literal["person", "agent"] = "agent" if claims.get("kind") == "agent" else "person"
    access_claim = claims.get("resource_access")
    own = access_claim.get(config.audience) if isinstance(access_claim, dict) else None
    roles = _strings(own.get("roles")) if isinstance(own, dict) else ()

    def refused(reason: str) -> Caller:
        return Caller(sub=sub, name=name.strip()[:200], kind=kind, access=None, reason=reason)

    if config.organization not in _strings(claims.get("organization")):
        return refused("Your suite account is not a member of the organization that uses this pdi.")
    if "admin" in roles or "editor" in roles:
        access: Access = "write"
    elif "viewer" in roles:
        access = "read"
    else:
        return refused("Your suite account has no role in DI Decision. Ask an administrator to grant you one.")
    if kind == "agent":
        access = "read"  # AI szkicuje, człowiek zatwierdza: agent nigdy nie zapisuje.
    return Caller(sub=sub, name=name.strip()[:200], kind=kind, access=access)


class SuiteTokenVerifier(TokenVerifier):
    """Sprawdza token dostępu suity; None (→ 401) dla każdego tokenu, którego nie przyjmuje. Bez tokenu w logach."""

    def __init__(
        self, config: McpAuthConfig, *, http: Http | None = None, now: Callable[[], float] = time.time
    ) -> None:
        self.config = config
        self.http: Http = http or UrllibHttp()
        self.now = now
        self._discovery: tuple[dict[str, Any], float] | None = None
        self._keys: tuple[Any, float] | None = None

    def _jwks_uri(self) -> str:
        if self._discovery and self.now() - self._discovery[1] < DISCOVERY_TTL_SECONDS:
            return str(self._discovery[0]["jwks_uri"])
        meta = self.http.get_json(f"{self.config.issuer.rstrip('/')}/.well-known/openid-configuration")
        if (
            not isinstance(meta, dict)
            or meta.get("issuer") != self.config.issuer
            or not isinstance(meta.get("jwks_uri"), str)
        ):
            raise SuiteSignInError("metadane wystawcy się nie zgadzają")
        self._discovery = (meta, self.now())
        return str(meta["jwks_uri"])

    def _fetch_keys(self) -> Any:
        jwks = self.http.get_json(self._jwks_uri())
        keys = jwks.get("keys") if isinstance(jwks, dict) else None
        self._keys = (keys, self.now())
        return keys

    def _claims(self, token: str) -> dict[str, Any]:
        keys = self._keys[0] if self._keys else self._fetch_keys()
        try:
            return signed_claims(token, keys)
        except UnknownKey:
            # Po rotacji kluczy wystawcy: pobrać JWKS jeszcze raz, ale nie częściej niż co JWKS_REFRESH_SECONDS.
            if self._keys and self.now() - self._keys[1] < JWKS_REFRESH_SECONDS:
                raise
            return signed_claims(token, self._fetch_keys())

    def check(self, token: str) -> AccessToken | None:
        try:
            claims = self._claims(token)
        except (SuiteSignInError, ValueError):
            return None
        c = self.config
        exp = claims.get("exp")
        sub = claims.get("sub")
        azp = claims.get("azp")
        if claims.get("iss") != c.issuer or c.audience not in _strings(claims.get("aud")):
            return None
        if not isinstance(exp, int | float) or exp + CLOCK_SKEW_SECONDS < self.now():
            return None
        if not isinstance(sub, str) or not sub or len(sub) > 200 or not isinstance(azp, str):
            return None
        if claims.get("kind") == "agent":
            # DI4: agent zawsze z właścicielem; wydany jego własnemu klientowi `agent-<persona>-<organizacja>`.
            if not isinstance(claims.get("owner"), str) or not claims["owner"] or not azp.startswith("agent-"):
                return None
        elif azp != c.client_id:
            return None
        scope = claims.get("scope")
        scopes = scope.split() if isinstance(scope, str) else []
        return AccessToken(token=token, client_id=azp, scopes=scopes, expires_at=int(exp), subject=sub, claims=claims)

    async def verify_token(self, token: str) -> AccessToken | None:
        return await anyio.to_thread.run_sync(self.check, token)


current_caller: ContextVar[Caller | None] = ContextVar("pdi_mcp_caller", default=None)
"""Osoba z tokenu na czas jednego wywołania narzędzia przez HTTP; None w stdio."""
