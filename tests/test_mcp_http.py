"""Zdalny serwer MCP z OAuth suity (docs/plan-mcp-zdalny.md): pdi jako serwer zasobów DI Decision."""

from __future__ import annotations

import base64
import json
import socket
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from typing import Any

import httpx2
import pytest
import uvicorn
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from pdi import mcp_auth
from pdi.mcp_server import build_server
from pdi.registry import Registry

pytestmark = pytest.mark.anyio

ISSUER = "http://localhost:8180/realms/suite"
ORG = "acme"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
KID = "k1"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _jwk(key: rsa.RSAPrivateKey, kid: str) -> dict[str, str]:
    numbers = key.public_key().public_numbers()
    return {
        "kty": "RSA",
        "kid": kid,
        "use": "sig",
        "n": _b64(numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big")),
        "e": _b64(numbers.e.to_bytes(3, "big")),
    }


def token(claims: dict[str, Any] | None = None, *, header: dict[str, Any] | None = None,
          key: rsa.RSAPrivateKey = KEY) -> str:  # fmt: skip
    now = int(time.time())
    body = {
        "iss": ISSUER,
        "aud": ["di-decision"],
        "azp": "di-decision-mcp",
        "sub": "person-ola",
        "name": "Ola Test",
        "exp": now + 300,
        "iat": now,
        "organization": [ORG],
        "resource_access": {"di-decision": {"roles": ["editor"]}},
        "scope": "openid profile",
        **(claims or {}),
    }
    head = _b64(json.dumps({"alg": "RS256", "typ": "JWT", "kid": KID, **(header or {})}).encode())
    payload = _b64(json.dumps({k: v for k, v in body.items() if v is not None}).encode())
    signature = key.sign(f"{head}.{payload}".encode(), padding.PKCS1v15(), hashes.SHA256())
    return f"{head}.{payload}.{_b64(signature)}"


class FakeIssuer:
    """Metadane i JWKS wystawcy bez sieci; liczy pobrania JWKS."""

    def __init__(self) -> None:
        self.jwks_calls = 0

    def get_json(self, url: str) -> Any:
        if url == f"{ISSUER}/.well-known/openid-configuration":
            return {"issuer": ISSUER, "jwks_uri": f"{ISSUER}/protocol/openid-connect/certs"}
        if url == f"{ISSUER}/protocol/openid-connect/certs":
            self.jwks_calls += 1
            return {"keys": [_jwk(KEY, KID)]}
        raise AssertionError(url)

    def post_form(self, url: str, data: dict[str, str]) -> Any:
        raise AssertionError(url)


def config(url: str = "http://127.0.0.1:8790/mcp") -> mcp_auth.McpAuthConfig:
    return mcp_auth.McpAuthConfig(issuer=ISSUER, organization=ORG, resource_url=url)


def verifier(**kw: Any) -> mcp_auth.SuiteTokenVerifier:
    return mcp_auth.SuiteTokenVerifier(config(), http=FakeIssuer(), **kw)


# --- weryfikator tokenu ---


async def test_mh01_valid_person_token_is_accepted() -> None:
    got = await verifier().verify_token(token())
    assert got is not None
    assert got.subject == "person-ola"
    assert got.client_id == "di-decision-mcp"
    assert got.claims is not None and got.claims["name"] == "Ola Test"
    assert got.scopes == ["openid", "profile"]


@pytest.mark.parametrize(
    "bad",
    [
        pytest.param(lambda: token(key=OTHER_KEY), id="podpis innym kluczem"),
        pytest.param(lambda: token(header={"alg": "HS256"}), id="alg HS256"),
        pytest.param(lambda: token(header={"alg": "none"}), id="alg none"),
        pytest.param(lambda: token(header={"kid": "nieznany"}), id="nieznany klucz"),
        pytest.param(lambda: token({"iss": "http://localhost:8180/realms/inny"}), id="inny wystawca"),
        pytest.param(lambda: token({"aud": ["di-release"]}), id="inny odbiorca"),
        pytest.param(lambda: token({"azp": "di-release"}), id="wydany innej aplikacji"),
        pytest.param(lambda: token({"exp": int(time.time()) - 3600}), id="wygasły"),
        pytest.param(lambda: token({"sub": None}), id="bez osoby"),
        pytest.param(lambda: "to.nie.jwt", id="śmieci"),
        pytest.param(lambda: "", id="pusty"),
    ],
)
async def test_mh02_bad_tokens_are_refused(bad: Any) -> None:
    assert await verifier().verify_token(bad()) is None


async def test_mh03_unknown_key_refetches_jwks_at_most_once_per_interval() -> None:
    issuer = FakeIssuer()
    clock = [time.time()]
    v = mcp_auth.SuiteTokenVerifier(config(), http=issuer, now=lambda: clock[0])
    assert await v.verify_token(token()) is not None
    assert await v.verify_token(token(header={"kid": "nieznany"})) is None
    assert issuer.jwks_calls == 1, "keys fetched a moment ago are not fetched again"
    clock[0] += mcp_auth.JWKS_REFRESH_SECONDS + 1
    assert await v.verify_token(token(header={"kid": "nieznany"})) is None
    assert await v.verify_token(token(header={"kid": "nieznany"})) is None
    assert issuer.jwks_calls == 2, "an unknown key refetches once after the interval"


# --- kto co może ---


def claims(**over: Any) -> dict[str, Any]:
    base = {
        "sub": "person-ola",
        "name": "Ola Test",
        "azp": "di-decision-mcp",
        "organization": [ORG],
        "resource_access": {"di-decision": {"roles": ["editor"]}},
    }
    return {**base, **over}


def test_mh04_access_comes_from_organization_and_roles() -> None:
    c = config()
    assert mcp_auth.caller(claims(), c).access == "write"
    assert mcp_auth.caller(claims(resource_access={"di-decision": {"roles": ["admin"]}}), c).access == "write"
    assert mcp_auth.caller(claims(resource_access={"di-decision": {"roles": ["viewer"]}}), c).access == "read"
    no_role = mcp_auth.caller(claims(resource_access={"di-release": {"roles": ["admin"]}}), c)
    assert no_role.access is None and "role" in no_role.reason
    outsider = mcp_auth.caller(claims(organization=["inna"]), c)
    assert outsider.access is None and "organization" in outsider.reason


def test_mh05_agents_only_read_whatever_their_roles() -> None:
    agent = claims(sub="agent-sub", azp="agent-architect-acme", kind="agent", owner="person-ola")
    who = mcp_auth.caller(agent, config())
    assert who.kind == "agent"
    assert who.access == "read"


async def test_mh06_agent_token_is_accepted_only_with_an_owner() -> None:
    agent = {"azp": "agent-architect-acme", "kind": "agent", "owner": "person-ola", "sub": "agent-sub"}
    assert await verifier().verify_token(token(agent)) is not None
    assert await verifier().verify_token(token({**agent, "owner": None})) is None


def test_mh07_config_from_env() -> None:
    assert mcp_auth.config_from_env({}) is None
    env = {"PDI_SUITE_ISSUER": ISSUER, "PDI_SUITE_ORGANIZATION": ORG}
    got = mcp_auth.config_from_env(env)
    assert got == mcp_auth.McpAuthConfig(issuer=ISSUER, organization=ORG, resource_url="http://127.0.0.1:8790/mcp")
    assert mcp_auth.config_from_env({**env, "PDI_MCP_PORT": "9001"}).resource_url == "http://127.0.0.1:9001/mcp"  # type: ignore[union-attr]
    with pytest.raises(ValueError, match="https"):
        mcp_auth.config_from_env({**env, "PDI_SUITE_ISSUER": "http://id.example.com/realms/suite"})
    with pytest.raises(ValueError, match="PDI_SUITE_ORGANIZATION"):
        mcp_auth.config_from_env({"PDI_SUITE_ISSUER": ISSUER})


# --- przez HTTP, jak klient MCP ---


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture
def served(registry: Registry) -> Iterator[str]:
    port = _free_port()
    url = f"http://127.0.0.1:{port}/mcp"
    server = build_server(lambda: registry, auth=config(url), http=FakeIssuer())
    app = server.streamable_http_app(stateless_http=True, json_response=True)
    uv = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=uv.run, daemon=True)
    thread.start()
    for _ in range(100):
        if uv.started:
            break
        time.sleep(0.05)
    yield url
    uv.should_exit = True
    thread.join(timeout=5)


async def session_call(url: str, bearer: str, fn: Any) -> Any:
    async with (
        httpx2.AsyncClient(headers={"Authorization": f"Bearer {bearer}"}) as http,
        streamable_http_client(url, http_client=http) as (read, write, *_),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        return await fn(session)


def test_mh08_without_a_token_401_points_to_the_resource_metadata(served: str) -> None:
    with pytest.raises(urllib.error.HTTPError) as e:
        request = urllib.request.Request(  # noqa: S310
            served, data=b"{}", method="POST", headers={"content-type": "application/json"}
        )
        urllib.request.urlopen(request)  # noqa: S310 — lokalny serwer testu
    assert e.value.code == 401
    header = e.value.headers.get("WWW-Authenticate", "")
    base = served.removesuffix("/mcp")
    assert f'resource_metadata="{base}/.well-known/oauth-protected-resource/mcp"' in header
    with urllib.request.urlopen(f"{base}/.well-known/oauth-protected-resource/mcp") as resp:  # noqa: S310
        meta = json.loads(resp.read())
    assert meta["resource"] == served
    assert meta["authorization_servers"] == [ISSUER]
    # Klient MCP prosi o zakresy z metadanych zasobu; bez nich wziąłby całą listę wystawcy (z `email`, DI3).
    assert meta["scopes_supported"] == ["openid"]


def test_mh08b_a_token_without_the_openid_scope_is_refused(served: str) -> None:
    request = urllib.request.Request(  # noqa: S310
        served,
        data=b"{}",
        method="POST",
        headers={"content-type": "application/json", "authorization": f"Bearer {token({'scope': 'profile'})}"},
    )
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(request)  # noqa: S310 — lokalny serwer testu
    assert e.value.code == 403


async def test_mh09_viewer_sees_and_calls_only_read_tools(served: str) -> None:
    viewer = token({"resource_access": {"di-decision": {"roles": ["viewer"]}}})

    async def run(session: ClientSession) -> tuple[set[str], Any, Any]:
        tools = (await session.list_tools()).tools
        found = await session.call_tool("find_decisions", {})
        write = await session.call_tool("record_decision", {
            "statement": "X", "why": "Y", "kind": "product", "drafted_by": "human",
            "source": {"kind": "claude-cli", "excerpt": "ustalamy"},
        })  # fmt: skip
        return {t.name for t in tools if not (t.annotations and t.annotations.read_only_hint)}, found, write

    writable, found, write = await session_call(served, viewer, run)
    assert writable == set()
    assert found.is_error is False
    assert write.is_error is True
    assert "editor" in write.content[0].text


async def test_mh10_editor_records_a_decision_as_the_person_from_the_token(served: str, registry: Registry) -> None:
    async def run(session: ClientSession) -> Any:
        return await session.call_tool("record_decision", {
            "statement": "Próg zostaje na 199 zł.", "why": "Koszt paczki rośnie.", "kind": "product",
            "drafted_by": "human", "decided_at": "2026-11-25",
            "source": {"kind": "claude-cli", "excerpt": "ustalamy, że próg zostaje"},
        })  # fmt: skip

    result = await session_call(served, token(), run)
    assert result.is_error is False, result.content
    stored = registry.get(result.structured_content["id"])
    assert stored["decided_by_id"] == "person-ola"
    assert stored["decided_by"] == "Ola Test"


async def test_mh11_outsider_sees_no_tools_and_is_refused_with_the_reason(served: str) -> None:
    outsider = token({"organization": ["inna"]})

    async def run(session: ClientSession) -> tuple[list[Any], Any]:
        return (await session.list_tools()).tools, await session.call_tool("find_decisions", {})

    tools, found = await session_call(served, outsider, run)
    assert tools == []
    assert found.is_error is True
    assert "organization" in found.content[0].text


async def test_mh12_stdio_server_without_auth_is_unchanged(registry: Registry) -> None:
    server = build_server(lambda: registry)
    tools = await server.list_tools()
    assert len(tools) == 37
