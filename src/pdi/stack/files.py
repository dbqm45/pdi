"""Pliki `~/.sdlc`: konfiguracja (`config.toml`) i zmienne z sekretami (`env`, tryb 600, zapis atomowy)."""

from __future__ import annotations

import base64
import json
import os
import re
import tempfile
import tomllib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

# Wartości, których `sdlc` nigdy nie wypisuje, nie loguje i nie przekazuje w argv.
SECRETS = (
    "PDI_TF_SIGNING_SECRET",
    "PDI_CI_FOR_SDLC_SIGNING_SECRET",
    "PDI_FORM_TOKEN",
    "TOKEN_ENCRYPTION_KEY",
    "PDI_SHIPSCOPE_TOKEN",
    "PDI_SHIPSCOPE_SIGNING_SECRET",
)
GENERATED_HEX = ("PDI_TF_SIGNING_SECRET", "PDI_CI_FOR_SDLC_SIGNING_SECRET", "PDI_FORM_TOKEN")
CONSTANTS = {
    "PDI_EVENTS_URL": "http://127.0.0.1:8787",
    "PDI_DISPATCH": "local",
    "PDI_PHASE_BUDGET_USD": "3",  # rekomendacja DL5
}
# Trzy wartości z ShipScope Settings → Integrations → pdi → Connect.
SHIPSCOPE_VARS = ("PDI_SHIPSCOPE_URL", "PDI_SHIPSCOPE_TOKEN", "PDI_SHIPSCOPE_SIGNING_SECRET")

_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_DOTENV_LINE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")


@dataclass(frozen=True)
class Config:
    pdi: Path
    shipscope: Path
    ci_for_sdlc: Path
    registry: Path
    checkout: Path | None = None

    def service_vars(self) -> dict[str, str]:
        """Zmienne pdi z konfiguracji; plik `env` może je nadpisać (np. `PDI_DISPATCH_CHECKOUT` z L5)."""
        values = {"PDI_REGISTRY_PATH": str(self.registry)}
        if self.checkout:
            values["PDI_DISPATCH_CHECKOUT"] = str(self.checkout)
        return values


def save_config(path: Path, config: Config) -> None:
    # Napis JSON jest poprawnym napisem TOML (cudzysłowy i ukośniki wsteczne zescapowane).
    fields = (
        ("pdi", config.pdi),
        ("shipscope", config.shipscope),
        ("ci_for_sdlc", config.ci_for_sdlc),
        ("registry", config.registry),
        ("checkout", config.checkout),
    )
    write_private(path, "".join(f"{name} = {json.dumps(str(value))}\n" for name, value in fields if value))


def load_config(path: Path) -> Config:
    data = tomllib.loads(path.read_text())
    checkout = data.get("checkout")
    return Config(
        pdi=Path(data["pdi"]),
        shipscope=Path(data["shipscope"]),
        ci_for_sdlc=Path(data["ci_for_sdlc"]),
        registry=Path(data["registry"]),
        checkout=Path(checkout) if checkout else None,
    )


def read_env(path: Path) -> dict[str, str]:
    """Plik `KLUCZ=wartość` z `~/.sdlc`; brak pliku to brak wartości."""
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text().splitlines():
        name, sep, value = line.partition("=")
        if sep and _NAME.match(name):
            values[name] = value
    return values


def write_env(path: Path, values: Mapping[str, str]) -> None:
    for name, value in values.items():
        if not _NAME.match(name) or "\n" in value or "\r" in value:
            raise ValueError(f"Niepoprawna zmienna {name}: nazwa albo znak nowej linii w wartości.")
    write_private(path, "".join(f"{name}={value}\n" for name, value in values.items()))


def ensure_env(
    path: Path, *, random: Callable[[int], bytes], shipscope_env: Mapping[str, str]
) -> tuple[dict[str, str], bool]:
    """Dopisuje brakujące sekrety i stałe, istniejących nie zmienia. Zwraca wartości i to, czy plik się zmienił.

    `TOKEN_ENCRYPTION_KEY` przejmuje z `server/.env` ShipScope, jeśli już tam jest (np. po `npm run dev`), żeby
    zapieczętowane nim dane dało się dalej odczytać."""
    values = read_env(path)
    before = dict(values)
    for name in GENERATED_HEX:
        values.setdefault(name, random(32).hex())
    if not values.get("TOKEN_ENCRYPTION_KEY"):
        adopted = shipscope_env.get("TOKEN_ENCRYPTION_KEY")
        values["TOKEN_ENCRYPTION_KEY"] = adopted or base64.b64encode(random(32)).decode("ascii")
    for name, value in CONSTANTS.items():
        values.setdefault(name, value)
    changed = values != before
    if changed:
        write_env(path, values)
    return values, changed


def read_dotenv(path: Path) -> dict[str, str]:
    """`server/.env` ShipScope czytany tak jak w `scripts/dev.js` (cudzysłowy wokół wartości zdjęte)."""
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text().splitlines():
        match = _DOTENV_LINE.match(line)
        if not match:
            continue
        value = match.group(2)
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[match.group(1)] = value
    return values


def write_private(path: Path, text: str) -> None:
    """Plik tylko dla właściciela (600) w katalogu 700, zapisany atomowo: plik tymczasowy obok i `os.replace`."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w") as f:
            os.fchmod(f.fileno(), 0o600)
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
