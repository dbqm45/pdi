import http.client
import json
import threading
from collections.abc import Iterator
from datetime import UTC, datetime
from http.server import HTTPServer
from typing import Any

import pytest

from pdi.inbox import Inbox
from pdi.receiver import MAX_BODY, PATH, main, make_server
from pdi.registry import Registry
from tests.test_inbox import SECRET, gate_event, metric_event, readiness_event, released_event, sign, stage_event

TF_SECRET = "sekret-tf"  # noqa: S105 — sekret testowy

NOW = datetime(2026, 10, 23, 9, 30, tzinfo=UTC)
TS = str(int(NOW.timestamp()))


@pytest.fixture
def server(registry: Registry) -> Iterator[HTTPServer]:
    srv = make_server(Inbox(registry), {"shipscope": SECRET, "tf": TF_SECRET}, port=0, clock=lambda: NOW)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield srv
    srv.shutdown()
    srv.server_close()


def post(
    server: HTTPServer,
    body: bytes,
    *,
    path: str = PATH,
    signature: str | None = None,
    timestamp: str = TS,
    event: str | None = "release.stage_changed",
    prefix: str = "x-shipscope",
    secret: str = SECRET,
) -> tuple[int, dict[str, Any]]:
    conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
    headers = {"content-type": "application/json", f"{prefix}-timestamp": timestamp}
    headers[f"{prefix}-signature"] = signature if signature is not None else sign(timestamp, body, secret)
    if event:
        headers[f"{prefix}-event"] = event
    conn.request("POST", path, body=body, headers=headers)
    response = conn.getresponse()
    data = response.read()
    conn.close()
    return response.status, json.loads(data) if data else {}


def encode(event: dict[str, Any]) -> bytes:
    return json.dumps(event).encode()


def test_new_event_is_202_and_lands_in_inbox(server: HTTPServer, registry: Registry) -> None:
    status, body = post(server, encode(stage_event()))

    assert (status, body["status"], body["item"]) == (202, "created", "evt-stage-1")
    assert Inbox(registry).get("evt-stage-1")["kind"] == "gate"


def test_duplicate_and_recorded_events_are_200(server: HTTPServer) -> None:
    post(server, encode(stage_event()))

    dup, dup_body = post(server, encode(stage_event()))
    recorded, recorded_body = post(server, encode(released_event(release="R2")), event="feature.released")

    assert (dup, dup_body["status"]) == (200, "duplicate")
    assert (recorded, recorded_body["status"]) == (200, "recorded")


def test_mvp_release_is_scheduled_with_200(server: HTTPServer) -> None:
    status, body = post(server, encode(released_event()), event="feature.released")

    assert (status, body) == (200, {"status": "scheduled", "item": None})


def test_bad_signature_is_401_and_stores_nothing(server: HTTPServer, registry: Registry) -> None:
    status, body = post(server, encode(stage_event()), signature="v1=" + "0" * 64)

    assert status == 401
    assert "payment-retry" not in json.dumps(body)
    assert Inbox(registry).items() == []


def test_stale_timestamp_is_401(server: HTTPServer) -> None:
    old = str(int(NOW.timestamp()) - 3600)

    status, _ = post(server, encode(stage_event()), timestamp=old)

    assert status == 401


def test_event_header_must_match_body_type(server: HTTPServer) -> None:
    status, body = post(server, encode(stage_event()), event="feature.released")

    assert status == 400
    assert "x-shipscope-event" in body["error"].lower()


def test_invalid_json_and_schema_are_400_without_echoing_content(server: HTTPServer) -> None:
    bad_json, _ = post(server, b"{nie json")
    event = stage_event()
    event["payload"]["rollout"] = 500
    bad_schema, body = post(server, encode(event))

    assert bad_json == 400
    assert bad_schema == 400
    assert "rollout" in body["error"]
    assert "payment-retry" not in body["error"]


def test_other_path_is_404_and_too_large_body_is_413(server: HTTPServer) -> None:
    other, _ = post(server, encode(stage_event()), path="/events/inne")
    large, _ = post(server, b"x" * (MAX_BODY + 1))

    assert other == 404
    assert large == 413


def test_get_is_405(server: HTTPServer) -> None:
    conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
    conn.request("GET", PATH)
    response = conn.getresponse()
    response.read()
    conn.close()

    assert response.status == 405


def test_main_requires_secret(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    monkeypatch.setenv("PDI_REGISTRY_PATH", str(tmp_path))
    monkeypatch.delenv("PDI_SHIPSCOPE_SIGNING_SECRET", raising=False)

    monkeypatch.delenv("PDI_TF_SIGNING_SECRET", raising=False)
    monkeypatch.delenv("PDI_CI_FOR_SDLC_SIGNING_SECRET", raising=False)

    with pytest.raises(SystemExit, match="PDI_SHIPSCOPE_SIGNING_SECRET.*PDI_TF_SIGNING_SECRET"):
        main()


def test_tf_gate_request_uses_pdi_headers_and_its_own_secret(server: HTTPServer, registry: Registry) -> None:
    body = encode(gate_event())

    status, answer = post(server, body, path="/events/tf", event="gate.requested", prefix="x-pdi", secret=TF_SECRET)

    assert (status, answer["item"]) == (202, "evt-gate-1")
    assert Inbox(registry).get("evt-gate-1")["gate"] == "B1"


def test_tf_breached_metric_becomes_problem_item(server: HTTPServer, registry: Registry) -> None:
    body = encode(metric_event())
    status, answer = post(server, body, path="/events/tf", event="metric.breached", prefix="x-pdi", secret=TF_SECRET)

    assert (status, answer["status"]) == (202, "created")
    assert Inbox(registry).get("tf-metric-rollbacks-2026-10-10")["kind"] == "problem"


def test_tf_path_refuses_the_shipscope_secret(server: HTTPServer) -> None:
    status, _ = post(server, encode(gate_event()), path="/events/tf", event="gate.requested", prefix="x-pdi")

    assert status == 401


def test_event_source_must_match_the_path(server: HTTPServer) -> None:
    body = encode(stage_event())

    status, answer = post(server, body, path="/events/tf", prefix="x-pdi", secret=TF_SECRET)

    assert status == 400
    assert "source" in answer["error"]


def test_path_without_configured_secret_is_404(server: HTTPServer) -> None:
    body = encode(readiness_event("ready"))

    status, _ = post(server, body, path="/events/ci_for_sdlc", event="readiness.changed", prefix="x-pdi")

    assert status == 404


def test_main_reads_secrets_per_sender(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    started: dict[str, Any] = {}

    def fake_make_server(inbox: Inbox, secrets: dict[str, str], **kwargs: Any) -> Any:
        started.update(secrets=secrets, **kwargs)

        class Stop(Exception):
            pass

        class Server:
            def serve_forever(self) -> None:
                raise Stop

        started["stop"] = Stop
        return Server()

    monkeypatch.setenv("PDI_REGISTRY_PATH", str(tmp_path))
    monkeypatch.delenv("PDI_SHIPSCOPE_SIGNING_SECRET", raising=False)
    monkeypatch.setenv("PDI_TF_SIGNING_SECRET", TF_SECRET)
    monkeypatch.setenv("PDI_CI_FOR_SDLC_SIGNING_SECRET", "s-ci")
    monkeypatch.setattr("pdi.receiver.make_server", fake_make_server)

    with pytest.raises(Exception) as stopped:  # noqa: PT011 — Stop powstaje w podstawionym serwerze
        main()

    assert stopped.type is started["stop"]
    assert started["secrets"] == {"tf": TF_SECRET, "ci_for_sdlc": "s-ci"}
