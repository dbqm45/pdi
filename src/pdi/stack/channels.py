"""Pytania ze Slacka w `sdlc`: DI Definition, di-channels i tunel, z adresami w aplikacji Slack ustawianymi samemu.

Po `sdlc init` (klon di-channels i klucze Slacka) `sdlc up` startuje DI Definition (ci_for_sdlc, port 4317) i
di-channels (3100) ze wspólnym sekretem podpisu, tunel cloudflared do di-channels i, gdy jest token konfiguracyjny
aplikacji, wpisuje adres tunelu w Request URL komendy i interaktywności (Slack API `apps.manifest.update`). Darmowy
tunel ma nowy adres po każdym starcie, więc bez tego trzeba by go przepisywać ręcznie.

di-channels dostaje tożsamość suity (autor pytania z suity, ADR 17), gdy działa ona w `sdlc` (`suite.py`): wystawca,
sekret klienta di-channels z `~/.sdlc/env` i adres di-identity. Sekrety tylko przez środowisko procesów; w argv i w
wyjściu `sdlc` ich nie ma. Token konfiguracyjny Slacka żyje 12 godzin: przy każdym `up` jest odnawiany z refresh
tokenu, a nowy refresh token od razu zapisany (stary przestaje działać).
"""

from __future__ import annotations

import json
import re
import secrets as token
import urllib.parse
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pdi.stack import home, suite

if TYPE_CHECKING:
    from pdi.stack.cli import Ctx

DEFINITION_PORT = 4317
DEFINITION_URL = f"http://127.0.0.1:{DEFINITION_PORT}"
CHANNELS_PORT = 3100
CHANNELS_URL = f"http://127.0.0.1:{CHANNELS_PORT}"
TUNNEL_PATTERN = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
SLACK_API = "https://slack.com/api"
DEFINITION_WAIT = 5 * 60  # pierwszy start buduje interfejs
CHANNELS_WAIT = 30
TUNNEL_WAIT = 60
GENERATED = ("SUITE_CHANNELS_SIGNING_SECRET",)
SLACK_KEYS = ("SUITE_SLACK_SIGNING_SECRET", "SUITE_SLACK_BOT_TOKEN")
SLACK_CONFIG = ("SUITE_SLACK_APP_ID", "SUITE_SLACK_CONFIG_REFRESH_TOKEN")


def enabled(config: home.Config, values: Mapping[str, str]) -> bool:
    return config.channels is not None and all(values.get(key) for key in SLACK_KEYS)


def definition_env(ctx: Ctx, values: Mapping[str, str]) -> dict[str, str]:
    return {
        **ctx.environ,
        "PORT": str(DEFINITION_PORT),
        "CI_CHANNELS_SIGNING_SECRET": values["SUITE_CHANNELS_SIGNING_SECRET"],
    }


def channels_env(ctx: Ctx, config: home.Config, values: Mapping[str, str]) -> dict[str, str]:
    """Środowisko di-channels: Slack, DI Definition i (gdy działa w sdlc) tożsamość suity; bez sekretów pdi."""
    env = {
        **ctx.environ,
        "PORT": str(CHANNELS_PORT),
        "SLACK_SIGNING_SECRET": values["SUITE_SLACK_SIGNING_SECRET"],
        "SLACK_BOT_TOKEN": values["SUITE_SLACK_BOT_TOKEN"],
        "DI_DEFINITION_URL": DEFINITION_URL,
        "CI_CHANNELS_SIGNING_SECRET": values["SUITE_CHANNELS_SIGNING_SECRET"],
    }
    if suite.enabled(config) and values.get("SUITE_CLIENT_SECRET_DI_CHANNELS"):
        env.update(
            SUITE_ISSUER=suite.ISSUER,
            SUITE_CLIENT_SECRET=values["SUITE_CLIENT_SECRET_DI_CHANNELS"],
            DI_IDENTITY_URL=suite.IDENTITY_URL,
        )
    return env


def tunnel_url(ctx: Ctx) -> str | None:
    """Ostatni adres trycloudflare.com z logu tunelu (cloudflared wypisuje go po połączeniu)."""
    log = ctx.root / "logs" / "tunnel.log"
    if not log.is_file():
        return None
    found = TUNNEL_PATTERN.findall(log.read_text(encoding="utf-8", errors="replace"))
    return found[-1] if found else None


def start_tunnel(ctx: Ctx) -> str | None:
    """Tunel do di-channels (HTTP/2: QUIC bywa blokowany w sieciach domowych); adres albo None bez cloudflared."""
    from pdi.stack import cli

    if ctx.which("cloudflared") is None:
        ctx.out("tunel: pominięty — brak cloudflared (brew install cloudflared); Slack nie dotrze do di-channels")
        return None
    if cli.pid_of(ctx, "tunnel") is None:
        log = ctx.root / "logs" / "tunnel.log"
        log.unlink(missing_ok=True)  # stary adres nie może udawać nowego
        argv = [
            "cloudflared",
            "tunnel",
            "--no-autoupdate",
            "--protocol",
            "http2",
            "--url",
            f"http://localhost:{CHANNELS_PORT}",
        ]
        cli.start(ctx, "tunnel", argv, ctx.root, ctx.environ)
    deadline = ctx.clock() + TUNNEL_WAIT
    while (url := tunnel_url(ctx)) is None:
        if cli.pid_of(ctx, "tunnel") is None or ctx.clock() >= deadline:
            raise suite.SuiteError("tunel nie podał adresu — zobacz ~/.sdlc/logs/tunnel.log")
        ctx.sleep(cli.POLL_SECONDS)
    # Nowa nazwa w DNS bywa widoczna dopiero po kilku sekundach; bez odpowiedzi tylko ostrzeżenie.
    deadline = ctx.clock() + TUNNEL_WAIT
    while not suite._http_ok(ctx, f"{url}/health"):
        if ctx.clock() >= deadline:
            ctx.out(f"  uwaga: {url}/health jeszcze nie odpowiada — sprawdź za chwilę w przeglądarce")
            break
        ctx.sleep(cli.POLL_SECONDS)
    return url


def _slack(ctx: Ctx, method: str, form: Mapping[str, str], bearer: str | None = None) -> dict[str, Any]:
    headers = {"content-type": "application/x-www-form-urlencoded"}
    if bearer:
        headers["authorization"] = f"Bearer {bearer}"
    try:
        _, body = ctx.post(f"{SLACK_API}/{method}", headers, urllib.parse.urlencode(form).encode())
        answer = json.loads(body)
    except (OSError, ValueError) as e:
        return {"ok": False, "error": f"brak odpowiedzi ({e})"}
    return answer if isinstance(answer, dict) else {"ok": False, "error": "nieczytelna odpowiedź"}


def point_slack(ctx: Ctx, url: str, values: dict[str, str]) -> str:
    """Request URL komendy i interaktywności w aplikacji Slack na adres tunelu; zwraca, co się stało."""
    commands, interactions = f"{url}/slack/commands", f"{url}/slack/interactions"
    if not all(values.get(key) for key in SLACK_CONFIG):
        return f"wpisz ręcznie (api.slack.com/apps): komenda {commands}, interaktywność {interactions}"
    rotated = _slack(ctx, "tooling.tokens.rotate", {"refresh_token": values["SUITE_SLACK_CONFIG_REFRESH_TOKEN"]})
    if not rotated.get("ok"):
        return f"token konfiguracyjny odrzucony ({rotated.get('error')}) — nowy: sdlc init; do tego czasu wpisz ręcznie"
    values["SUITE_SLACK_CONFIG_REFRESH_TOKEN"] = str(rotated["refresh_token"])
    home.write_env(ctx.root / "env", values)  # od razu: poprzedni refresh token już nie działa
    access = str(rotated["token"])
    app = values["SUITE_SLACK_APP_ID"]
    exported = _slack(ctx, "apps.manifest.export", {"app_id": app}, access)
    manifest = exported.get("manifest")
    if not exported.get("ok") or not isinstance(manifest, dict):
        return f"nie odczytano manifestu aplikacji ({exported.get('error')})"
    changed = False
    for command in manifest.get("features", {}).get("slash_commands", []):
        if command.get("url") != commands:
            command["url"], changed = commands, True
    interactivity = manifest.setdefault("settings", {}).setdefault("interactivity", {"is_enabled": True})
    if interactivity.get("request_url") != interactions:
        interactivity["request_url"], changed = interactions, True
    if not changed:
        return "adresy już aktualne"
    updated = _slack(ctx, "apps.manifest.update", {"app_id": app, "manifest": json.dumps(manifest)}, access)
    if not updated.get("ok"):
        return f"aktualizacja odrzucona ({updated.get('error')}) — wpisz ręcznie: {commands}, {interactions}"
    return "adresy ustawione"


def up(ctx: Ctx, config: home.Config, values: dict[str, str]) -> dict[str, str]:
    """DI Definition, di-channels, tunel i adresy w Slacku; zwraca ~/.sdlc/env (z odnowionym tokenem Slacka)."""
    from pdi.stack import cli

    if config.channels is None:
        ctx.out("pytania ze Slacka: pominięte (uv run sdlc init, żeby je dodać)")
        return values
    if not all(values.get(key) for key in SLACK_KEYS):
        ctx.out("pytania ze Slacka: brak kluczy Slacka w ~/.sdlc/env — uv run sdlc init")
        return values
    if not (config.channels / "package.json").is_file():
        raise suite.SuiteError(f"{config.channels} nie jest klonem di-channels — popraw ~/.sdlc/config.toml")
    created = [key for key in GENERATED if not values.get(key)]
    if created:
        values = {**values, **{key: token.token_urlsafe(32) for key in created}}
        home.write_env(ctx.root / "env", values)
        ctx.out(f"~/.sdlc/env: wygenerowane {', '.join(created)}")
    if cli.pid_of(ctx, "di-definition") is None:
        cli.ensure_port_free(ctx, "DI Definition", DEFINITION_URL)
        ctx.out("DI Definition: start (pierwszy raz buduje interfejs, do kilku minut)…")
        cli.start(ctx, "di-definition", ["npm", "start"], config.ci_for_sdlc, definition_env(ctx, values))
        cli.wait_for(ctx, "di-definition", f"{DEFINITION_URL}/api/health", seconds=DEFINITION_WAIT, any_status=False)
    if cli.pid_of(ctx, "di-channels") is None:
        cli.ensure_port_free(ctx, "di-channels", CHANNELS_URL)
        cli.start(ctx, "di-channels", ["npm", "start"], config.channels, channels_env(ctx, config, values))
        cli.wait_for(ctx, "di-channels", f"{CHANNELS_URL}/health", seconds=CHANNELS_WAIT, any_status=False)
    author = (
        "z suity" if "SUITE_ISSUER" in channels_env(ctx, config, values) else "nazwa ze Slacka (bez tożsamości suity)"
    )
    ctx.out(f"di-channels: działa — {CHANNELS_URL}; autor pytań: {author}")
    url = start_tunnel(ctx)
    if url is not None:
        ctx.out(f"tunel: {url}")
        ctx.out(f"Slack: {point_slack(ctx, url, values)}")
    return values


def status(ctx: Ctx, config: home.Config) -> None:
    from pdi.stack import cli

    if config.channels is None:
        ctx.out("pytania ze Slacka: nie dodane (uv run sdlc init)")
        return
    for name, address in (
        ("di-definition", DEFINITION_URL),
        ("di-channels", CHANNELS_URL),
        ("tunnel", tunnel_url(ctx) or "—"),
    ):
        pid = cli.pid_of(ctx, name)
        ctx.out(f"{name}: {'działa, pid ' + str(pid) if pid else 'nie działa'} — {address}")
    values = home.read_env(ctx.root / "env")
    slack = "ustawione" if all(values.get(key) for key in SLACK_KEYS) else "brak"
    auto = "tak" if all(values.get(key) for key in SLACK_CONFIG) else "nie (adresy wpisujesz ręcznie)"
    ctx.out(f"klucze Slacka: {slack}; adresy w Slacku ustawiane same: {auto}")


def down(ctx: Ctx) -> None:
    from pdi.stack import cli

    for name in ("tunnel", "di-channels", "di-definition"):
        ctx.out(f"{name}: {'zatrzymany' if cli.stop(ctx, name) else 'nie działał'}")


def init(ctx: Ctx, config: home.Config) -> home.Config:
    """Raz: klon di-channels i klucze aplikacji Slack (wpisywane niewidoczne). Enter zostawia to, co już jest."""
    import dataclasses

    default = config.channels or config.pdi.parent / "di-channels"
    value = ctx.ask("Klon di-channels (puste = bez pytań ze Slacka)", str(default)).strip()
    channels = Path(value).expanduser() if value else None
    if channels is not None and not (channels / "package.json").is_file():
        raise suite.SuiteError(
            f"{channels} nie jest klonem di-channels — git clone https://github.com/dbqm45/di-channels"
        )
    config = dataclasses.replace(config, channels=channels)
    home.save_config(ctx.root / "config.toml", config)
    if channels is None:
        return config
    values = home.read_env(ctx.root / "env")
    ctx.out("Aplikacja Slack (api.slack.com/apps → aplikacja). Enter = bez zmian.")
    asked = {
        "SUITE_SLACK_SIGNING_SECRET": "Signing Secret (Basic Information)",
        "SUITE_SLACK_BOT_TOKEN": "Bot User OAuth Token xoxb-… (OAuth & Permissions)",
        "SUITE_SLACK_CONFIG_REFRESH_TOKEN": "opcjonalnie: refresh token konfiguracji (Your App Configuration Tokens → "
        "Generate Token) — wtedy sdlc sam wpisuje adres tunelu w aplikacji",
    }
    for key, prompt in asked.items():
        answer = ctx.ask_secret(f"{prompt}: ").strip()
        if answer:
            values[key] = answer
    if values.get("SUITE_SLACK_CONFIG_REFRESH_TOKEN"):
        app = ctx.ask("App ID aplikacji (Basic Information, A0…)", values.get("SUITE_SLACK_APP_ID", "")).strip()
        if app:
            values["SUITE_SLACK_APP_ID"] = app
    home.write_env(ctx.root / "env", values)
    return config
