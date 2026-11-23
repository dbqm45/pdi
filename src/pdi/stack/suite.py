"""Tożsamość suity w `sdlc` (ADR 17): Keycloak, jego konfiguracja i di-identity bez ręcznego kopiowania sekretów.

`sdlc init` pyta raz o klon di-identity i klienta Google; `sdlc up` startuje Keycloak (kontener `sdlc-keycloak`, dane
w wolumenie) i bazę di-identity (`sdlc-identity-pg`), uruchamia `configure` realmu, zapisuje sekrety klientów
aplikacji do `~/.sdlc/env` (`npm run identity -- secrets`) i startuje di-identity. Sekrety idą do kontenerów i procesów
przez środowisko: `docker run -e NAZWA` bez wartości bierze ją ze środowiska `docker`, więc nie ma jej w argv.

Stałe porty (obok ShipScope/Flags na 3000, di-channels na 3100 i DI Definition na 4317): Keycloak 8180, di-identity
3200, baza di-identity 5434. Wszystko tylko na 127.0.0.1.
"""

from __future__ import annotations

import secrets as token
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import TYPE_CHECKING

from pdi.stack import home

if TYPE_CHECKING:
    from pdi.stack.cli import Ctx

KEYCLOAK = "sdlc-keycloak"
KEYCLOAK_IMAGE = "keycloak/keycloak:26.4"
KEYCLOAK_PORT = 8180
KEYCLOAK_URL = f"http://localhost:{KEYCLOAK_PORT}"
ISSUER = f"{KEYCLOAK_URL}/realms/suite"
IDENTITY_PG = "sdlc-identity-pg"
IDENTITY_PG_IMAGE = "postgres:17"
IDENTITY_PG_PORT = 5434
IDENTITY_PORT = 3200
IDENTITY_URL = f"http://127.0.0.1:{IDENTITY_PORT}"
ADMIN_USER = "admin"
# Generowane raz w ~/.sdlc/env i nigdy nie nadpisywane (jak sekrety pdi w home.GENERATED).
GENERATED = ("SUITE_KEYCLOAK_ADMIN_PASSWORD", "SUITE_IDENTITY_DB_PASSWORD", "SUITE_EVENTS_SECRET")
GOOGLE = ("SUITE_GOOGLE_CLIENT_ID", "SUITE_GOOGLE_CLIENT_SECRET")
KEYCLOAK_WAIT = 3 * 60
IDENTITY_WAIT = 60


class SuiteError(Exception):
    """Krok suity się nie udał; `sdlc` kończy się tym komunikatem."""


def enabled(config: home.Config) -> bool:
    return config.identity is not None


def ensure_secrets(sdlc_root: Path, values: dict[str, str]) -> tuple[dict[str, str], list[str]]:
    """Brakujące sekrety suity dopisane do ~/.sdlc/env; zwraca wartości i nazwy wygenerowanych teraz."""
    created = [key for key in GENERATED if not values.get(key)]
    if created:
        values = {**values, **{key: token.token_urlsafe(32) for key in created}}
        home.write_env(sdlc_root / "env", values)
    return values, created


def _container_state(ctx: Ctx, name: str) -> str | None:
    """`true`/`false` (działa/zatrzymany) albo None, gdy kontenera nie ma."""
    code, out, _ = ctx.run(["docker", "inspect", "-f", "{{.State.Running}}", name], None, ctx.environ, None)
    return out.strip() if code == 0 else None


def _docker(ctx: Ctx, argv: list[str], env: Mapping[str, str], what: str) -> None:
    code, _, err = ctx.run(["docker", *argv], None, {**ctx.environ, **env}, None)
    if code != 0:
        raise SuiteError(f"{what}: {(err.strip().splitlines() or [f'kod {code}'])[0]}")


def _ensure_container(ctx: Ctx, name: str, port: int, run_args: list[str], env: Mapping[str, str]) -> str:
    """Kontener uruchomiony: nowy (`docker run`), wznowiony (`docker start`) albo już działający."""
    state = _container_state(ctx, name)
    if state == "true":
        return "działa"
    if state is None and not ctx.port_free("127.0.0.1", port):
        raise SuiteError(
            f"{name}: port {port} zajmuje inny proces (np. Keycloak albo Postgres uruchomiony ręcznie). "
            f"Sprawdź: lsof -nP -iTCP:{port} -sTCP:LISTEN, zatrzymaj go i uruchom sdlc up ponownie."
        )
    if state is None:
        _docker(ctx, ["run", "-d", "--name", name, *run_args], env, name)
        return "utworzony"
    _docker(ctx, ["start", name], env, name)
    return "wznowiony"


def _wait(ctx: Ctx, what: str, check: Callable[[], bool], seconds: float) -> None:
    from pdi.stack.cli import POLL_SECONDS

    deadline = ctx.clock() + seconds
    while not check():
        if ctx.clock() >= deadline:
            raise SuiteError(f"{what} nie odpowiada od {int(seconds)} s")
        ctx.sleep(POLL_SECONDS)


def _http_ok(ctx: Ctx, url: str) -> bool:
    try:
        status, _ = ctx.http(url, {})
    except OSError:
        return False
    return status == 200


def _first_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), "")


def start_keycloak(ctx: Ctx, values: Mapping[str, str]) -> str:
    env = {
        "KC_BOOTSTRAP_ADMIN_USERNAME": ADMIN_USER,
        "KC_BOOTSTRAP_ADMIN_PASSWORD": values["SUITE_KEYCLOAK_ADMIN_PASSWORD"],
    }
    run_args = [
        "-p", f"127.0.0.1:{KEYCLOAK_PORT}:8080",
        "-v", f"{KEYCLOAK}:/opt/keycloak/data",
        "-e", "KC_BOOTSTRAP_ADMIN_USERNAME",
        "-e", "KC_BOOTSTRAP_ADMIN_PASSWORD",
        KEYCLOAK_IMAGE, "start-dev",
    ]  # fmt: skip
    state = _ensure_container(ctx, KEYCLOAK, KEYCLOAK_PORT, run_args, env)
    _wait(ctx, "Keycloak", lambda: _http_ok(ctx, f"{KEYCLOAK_URL}/realms/master"), KEYCLOAK_WAIT)
    return state


def start_identity_db(ctx: Ctx, values: Mapping[str, str]) -> str:
    env = {
        "POSTGRES_USER": "identity",
        "POSTGRES_DB": "identity",
        "POSTGRES_PASSWORD": values["SUITE_IDENTITY_DB_PASSWORD"],
    }
    run_args = [
        "-p", f"127.0.0.1:{IDENTITY_PG_PORT}:5432",
        "-v", f"{IDENTITY_PG}:/var/lib/postgresql/data",
        "-e", "POSTGRES_USER", "-e", "POSTGRES_DB", "-e", "POSTGRES_PASSWORD",
        IDENTITY_PG_IMAGE,
    ]  # fmt: skip
    state = _ensure_container(ctx, IDENTITY_PG, IDENTITY_PG_PORT, run_args, env)

    def ready() -> bool:
        argv = ["docker", "exec", IDENTITY_PG, "pg_isready", "-U", "identity", "-d", "identity"]
        return ctx.run(argv, None, ctx.environ, None)[0] == 0

    _wait(ctx, "Postgres di-identity", ready, 60)
    return state


def admin_env(ctx: Ctx, values: Mapping[str, str]) -> dict[str, str]:
    """Środowisko poleceń `npm run identity`: Keycloak, administrator i (gdy jest) klient Google."""
    env = {
        **ctx.environ,
        "KEYCLOAK_URL": KEYCLOAK_URL,
        "KEYCLOAK_ADMIN_USERNAME": ADMIN_USER,
        "KEYCLOAK_ADMIN_PASSWORD": values["SUITE_KEYCLOAK_ADMIN_PASSWORD"],
    }
    if all(values.get(key) for key in GOOGLE):
        env["GOOGLE_CLIENT_ID"] = values["SUITE_GOOGLE_CLIENT_ID"]
        env["GOOGLE_CLIENT_SECRET"] = values["SUITE_GOOGLE_CLIENT_SECRET"]
    env.update({key: value for key, value in values.items() if key.startswith("REDIRECT_DI_")})
    return env


def configure(ctx: Ctx, identity: Path, values: Mapping[str, str]) -> None:
    """Realm `suite` według keycloak/suite.json (idempotentne), potem sekrety klientów do ~/.sdlc/env."""
    if not (identity / "node_modules").is_dir():
        code, _, err = ctx.run(["npm", "ci"], identity, ctx.environ, None)
        if code != 0:
            raise SuiteError(f"di-identity: npm ci — {_first_line(err) or f'kod {code}'}")
    env = admin_env(ctx, values)
    for step in (["configure"], ["secrets", "--env-file", str(ctx.root / "env")]):
        code, _, err = ctx.run(["npm", "run", "--silent", "identity", "--", *step], identity, env, None)
        if code != 0:
            raise SuiteError(f"di-identity: {step[0]} — {_first_line(err) or f'kod {code}'}")


def identity_env(ctx: Ctx, values: Mapping[str, str]) -> dict[str, str]:
    """Środowisko usługi di-identity: tylko to, czego potrzebuje (bez sekretów pdi i ShipScope).

    `npm start` czyta też `.env` z klonu, ale zmienne procesu mają pierwszeństwo. Dlatego sekret klienta idzie także
    jako DI_IDENTITY_CLIENT_SECRET: stary `.env` z ręcznej konfiguracji (sekret z innego Keycloak) go nie przesłoni.
    """
    secret = values.get("SUITE_CLIENT_SECRET_DI_IDENTITY", "")
    return {
        **ctx.environ,
        "HOST": "127.0.0.1",
        "PORT": str(IDENTITY_PORT),
        "DATABASE_URL": f"postgres://identity:{values['SUITE_IDENTITY_DB_PASSWORD']}@127.0.0.1:{IDENTITY_PG_PORT}/identity",
        "DATABASE_SSL": "false",
        "OIDC_ISSUER": ISSUER,
        "OIDC_AUDIENCE": "di-identity",
        "OIDC_SERVICE_CLIENTS": "di-channels",
        "KEYCLOAK_URL": KEYCLOAK_URL,
        "DI_EVENTS_SECRET": values["SUITE_EVENTS_SECRET"],
        "SUITE_CLIENT_SECRET_DI_IDENTITY": secret,
        "DI_IDENTITY_CLIENT_SECRET": secret,
    }


def up(ctx: Ctx, config: home.Config, values: dict[str, str]) -> dict[str, str]:
    """Keycloak, baza i di-identity; zwraca ~/.sdlc/env po dopisaniu sekretów klientów."""
    from pdi.stack import cli

    identity = config.identity
    if identity is None:
        ctx.out("tożsamość suity: pominięta (uv run sdlc init, żeby ją dodać)")
        return values
    if not (identity / "package.json").is_file():
        raise SuiteError(f"{identity} nie jest klonem di-identity (brak package.json) — popraw ~/.sdlc/config.toml")
    values, created = ensure_secrets(ctx.root, values)
    if created:
        ctx.out(f"~/.sdlc/env: wygenerowane {', '.join(created)}")
    ctx.out(f"Keycloak ({KEYCLOAK}): {start_keycloak(ctx, values)} — {KEYCLOAK_URL}/admin")
    ctx.out(f"Postgres di-identity ({IDENTITY_PG}): {start_identity_db(ctx, values)}")
    configure(ctx, identity, values)
    values = home.read_env(ctx.root / "env")
    secrets_count = sum(1 for key in values if key.startswith("SUITE_CLIENT_SECRET_"))
    ctx.out(f"realm suite: skonfigurowany; sekrety klientów w ~/.sdlc/env: {secrets_count}")
    if not all(values.get(key) for key in GOOGLE):
        ctx.out("  uwaga: bez klienta Google nikt się nie zaloguje do suity — uv run sdlc init")
    if cli.pid_of(ctx, "di-identity") is None:
        cli.ensure_port_free(ctx, "di-identity", IDENTITY_URL)
        cli.start(ctx, "di-identity", ["npm", "start"], identity, identity_env(ctx, values))
        cli.wait_for(ctx, "di-identity", f"{IDENTITY_URL}/health", seconds=IDENTITY_WAIT, any_status=False)
    ctx.out(f"di-identity: działa — {IDENTITY_URL}")
    return values


def status(ctx: Ctx, config: home.Config) -> None:
    from pdi.stack import cli

    if config.identity is None:
        ctx.out("tożsamość suity: nie dodana (uv run sdlc init)")
        return
    for name in (KEYCLOAK, IDENTITY_PG):
        state = _container_state(ctx, name)
        ctx.out(f"{name}: {'działa' if state == 'true' else 'zatrzymany' if state == 'false' else 'brak'}")
    pid = cli.pid_of(ctx, "di-identity")
    ctx.out(f"di-identity: {'działa, pid ' + str(pid) if pid else 'nie działa'} — {IDENTITY_URL}")
    values = home.read_env(ctx.root / "env")
    count = sum(1 for key in values if key.startswith("SUITE_CLIENT_SECRET_"))
    google = "ustawiony" if all(values.get(key) for key in GOOGLE) else "brak"
    ctx.out(f"sekrety klientów suity: {count}; klient Google: {google}")


def down(ctx: Ctx) -> None:
    from pdi.stack import cli

    ctx.out(f"di-identity: {'zatrzymany' if cli.stop(ctx, 'di-identity') else 'nie działał'}")
    for name in (KEYCLOAK, IDENTITY_PG):
        if _container_state(ctx, name) == "true":
            ctx.run(["docker", "stop", name], None, ctx.environ, None)
            ctx.out(f"{name}: zatrzymany; dane zostają w wolumenie {name}")


def reset(ctx: Ctx) -> None:
    for name in (KEYCLOAK, IDENTITY_PG):
        ctx.run(["docker", "rm", "-f", name], None, ctx.environ, None)
        ctx.run(["docker", "volume", "rm", name], None, ctx.environ, None)


def init(ctx: Ctx, config: home.Config) -> home.Config:
    """Raz: klon di-identity i klient Google (do logowania osób). Pozostałe sekrety suity `sdlc up` generuje sam."""
    import dataclasses

    default = config.identity or config.pdi.parent / "di-identity"
    value = ctx.ask("Klon di-identity (puste = bez tożsamości suity)", str(default)).strip()
    identity = Path(value).expanduser() if value else None
    if identity is not None and not (identity / "package.json").is_file():
        raise SuiteError(f"{identity} nie jest klonem di-identity — git clone https://github.com/dbqm45/di-identity")
    config = dataclasses.replace(config, identity=identity)
    home.save_config(ctx.root / "config.toml", config)
    values = home.read_env(ctx.root / "env")
    ctx.out("Klient Google (OAuth „Web application”, przekierowanie "
            f"{ISSUER}/broker/google/endpoint). Enter = bez zmian.")  # fmt: skip
    client_id = ctx.ask("Google client ID", values.get("SUITE_GOOGLE_CLIENT_ID", "")).strip()
    client_secret = ctx.ask_secret("Google client secret (niewidoczny; Enter = bez zmian): ").strip()
    if client_id:
        values["SUITE_GOOGLE_CLIENT_ID"] = client_id
    if client_secret:
        values["SUITE_GOOGLE_CLIENT_SECRET"] = client_secret
    home.write_env(ctx.root / "env", values)
    return config
