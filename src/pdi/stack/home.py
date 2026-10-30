"""Pliki `sdlc` w `~/.sdlc` (L4): `config.toml` (ścieżki klonów), `env` (sekrety i ustawienia, prawa 600), `logs/`,
`run/` (pliki pid) i `ci-data/` (dane CLI ci_for_sdlc). Plan: docs/plan-l4-sdlc.md."""

from __future__ import annotations

import os
import secrets
import tempfile
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

# Generowane raz i nigdy nie nadpisywane.
GENERATED = ("PDI_TF_SIGNING_SECRET", "PDI_CI_FOR_SDLC_SIGNING_SECRET", "PDI_FORM_TOKEN")
# Ustawienia domyślne; użytkownik może je zmienić w pliku, `sdlc` ich nie nadpisuje.
DEFAULTS = {"PDI_EVENTS_URL": "http://127.0.0.1:8787", "PDI_DISPATCH": "local", "PDI_PHASE_BUDGET_USD": "3"}
# Trzy zmienne z połączenia z ShipScope (`local-pdi.js connect`).
SHIPSCOPE_KEYS = ("PDI_SHIPSCOPE_URL", "PDI_SHIPSCOPE_TOKEN", "PDI_SHIPSCOPE_SIGNING_SECRET")
SECRET_KEYS = (*GENERATED, "PDI_SHIPSCOPE_TOKEN", "PDI_SHIPSCOPE_SIGNING_SECRET")


def root(user_home: Path) -> Path:
    return user_home / ".sdlc"


@dataclass(frozen=True)
class Config:
    pdi: Path
    shipscope: Path
    ci_for_sdlc: Path
    registry: Path
    checkout: Path | None
    deploy_repo: str | None = None


def read_env(path: Path) -> dict[str, str]:
    """`KEY=wartość` w liniach; puste linie i `#` pomijane."""
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def write_env(path: Path, values: dict[str, str]) -> None:
    """Zapis atomowy: plik tymczasowy z prawami 600 w tym samym katalogu, potem zamiana; katalog z prawami 700."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    text = "# sdlc (pdi L4): sekrety i ustawienia lokalnego stosu. Nie commituj.\n"
    text += "".join(f"{key}={value}\n" for key, value in values.items())
    fd, tmp = tempfile.mkstemp(prefix="env.", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def ensure_env(
    sdlc_root: Path, generate: Callable[[], str] = lambda: secrets.token_urlsafe(32)
) -> tuple[dict[str, str], list[str]]:
    """Plik env z brakującymi sekretami i ustawieniami; zwraca wartości i nazwy wygenerowanych teraz sekretów."""
    path = sdlc_root / "env"
    values = read_env(path)
    created = [key for key in GENERATED if not values.get(key)]
    added = {key: value for key, value in DEFAULTS.items() if key not in values}
    if created or added or not path.is_file():
        values = {**values, **added, **{key: generate() for key in created}}
        write_env(path, values)
    return values, created


def load_config(path: Path) -> Config | None:
    if not path.is_file():
        return None
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    paths = data.get("paths", {})
    checkout = paths.get("checkout") or None
    return Config(
        pdi=Path(paths["pdi"]),
        shipscope=Path(paths["shipscope"]),
        ci_for_sdlc=Path(paths["ci_for_sdlc"]),
        registry=Path(paths["registry"]),
        checkout=Path(checkout) if checkout else None,
        deploy_repo=data.get("deploy", {}).get("repo") or None,
    )


def save_config(path: Path, config: Config) -> None:
    def quoted(value: object) -> str:
        return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'

    lines = ["# sdlc (pdi L4): ścieżki klonów. Zmieniaj ręcznie; `sdlc up` pyta tylko, gdy pliku brak.", "[paths]"]
    lines += [f"{name} = {quoted(getattr(config, name))}" for name in ("pdi", "shipscope", "ci_for_sdlc", "registry")]
    lines.append(f"checkout = {quoted(config.checkout or '')}")
    lines += ["", "[deploy]", f"repo = {quoted(config.deploy_repo or '')}", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    path.write_text("\n".join(lines), encoding="utf-8")
