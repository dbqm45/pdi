import json
from collections.abc import Mapping
from pathlib import Path

import pytest

from pdi import pr_state
from pdi.dispatch import DispatchConfig

PR = "https://github.com/dbqm45/sklep/pull/7"
TOKEN = "ghs_tajny_token"  # noqa: S105 — token testowy
LOCAL = DispatchConfig(repo=None, mode="local", checkout="/tmp/sklep")  # noqa: S108 — ścieżka testowa


class Gh:
    def __init__(self, code: int, out: str) -> None:
        self.code, self.out = code, out
        self.calls: list[tuple[list[str], dict[str, str]]] = []

    def __call__(self, argv: list[str], cwd: Path, env: Mapping[str, str]) -> tuple[int, str]:
        self.calls.append((argv, dict(env)))
        return self.code, self.out


class Api:
    def __init__(self, status: int, body: object) -> None:
        self.status, self.body = status, body
        self.calls: list[tuple[str, dict[str, str]]] = []

    def __call__(self, url: str, headers: dict[str, str]) -> tuple[int, bytes]:
        self.calls.append((url, headers))
        return self.status, json.dumps(self.body).encode()


@pytest.mark.parametrize(("out", "state"), [("MERGED\n", "merged"), ("OPEN", "open"), ("CLOSED", "closed")])
def test_local_mode_reads_the_state_with_gh(out: str, state: str) -> None:
    gh = Gh(0, out)

    found = pr_state.check(PR, LOCAL, run=gh, environ={"PATH": "/bin", "PDI_GITHUB_TOKEN": TOKEN, "GH_TOKEN": "x"})

    assert found == {"state": state}
    ((argv, env),) = gh.calls
    assert argv == ["gh", "pr", "view", PR, "--json", "state", "-q", ".state"]
    assert env == {"PATH": "/bin", "GH_TOKEN": "x"}  # bez sekretów pdi


@pytest.mark.parametrize(
    ("body", "state"), [({"state": "closed", "merged": True}, "merged"), ({"state": "open"}, "open")]
)
def test_token_reads_the_state_from_the_api(body: dict[str, object], state: str) -> None:
    api = Api(200, body)

    found = pr_state.check(PR, DispatchConfig(repo="dbqm45/sklep", token=TOKEN), get=api)

    assert found == {"state": state}
    ((url, headers),) = api.calls
    assert url == "https://api.github.com/repos/dbqm45/sklep/pulls/7"
    assert headers["authorization"] == f"Bearer {TOKEN}"


def test_failing_gh_falls_back_to_the_api() -> None:
    config = DispatchConfig(repo=None, mode="local", checkout="/tmp/sklep", token=TOKEN)  # noqa: S108

    found = pr_state.check(PR, config, run=Gh(1, "not logged in"), get=Api(200, {"state": "closed", "merged": True}))

    assert found == {"state": "merged"}


@pytest.mark.parametrize(
    ("config", "gh", "api", "reason"),
    [
        (DispatchConfig(repo=None), None, None, "PDI_GITHUB_TOKEN"),
        (LOCAL, Gh(4, ""), None, "kodem 4"),
        (DispatchConfig(repo=None, token=TOKEN), None, Api(404, {}), "404"),
        (DispatchConfig(repo=None, token=TOKEN), None, Api(200, ["?"]), "nieznany stan"),
    ],
)
def test_unknown_state_names_the_reason_without_the_token(
    config: DispatchConfig, gh: Gh | None, api: Api | None, reason: str
) -> None:
    found = pr_state.check(PR, config, run=gh, get=api, environ={})

    assert found["state"] == "unknown"
    assert reason in found["reason"]
    assert TOKEN not in found["reason"]


def test_gh_that_cannot_start_is_unknown() -> None:
    def missing(argv: list[str], cwd: Path, env: Mapping[str, str]) -> tuple[int, str]:
        raise FileNotFoundError("gh")

    assert pr_state.check(PR, LOCAL, run=missing, environ={})["state"] == "unknown"


@pytest.mark.parametrize("url", [PR, PR + "/"])
def test_pr_url(url: str) -> None:
    assert pr_state.is_pr_url(url)


@pytest.mark.parametrize("url", ["https://github.com/a/b/issues/1", "http://github.com/a/b/pull/1", None, "x"])
def test_not_a_pr_url(url: object) -> None:
    assert not pr_state.is_pr_url(url)
