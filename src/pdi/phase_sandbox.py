"""Krok `run` fazy tf w kontenerze Docker (krok Z8a, decyzja DZ9). Plan: docs/plan-z8a-izolacja-faz.md.

Persona fazy (i talos w `delivery`) działa w kontenerze `pdi-phase-…`, który widzi tylko klon repo produktu
(montowany pod tą samą ścieżką), bez katalogu domowego właściciela, `~/.sdlc/env`, `~/.ssh` i innych repo. Kontener
ma tylko wewnętrzną sieć Dockera; jedyna droga na zewnątrz to proxy `pdi-egress-…` z listą hostów (`pdi.phase_egress`),
a każda odmowa trafia do logu przebiegu. Drugą warstwą jest sandbox Claude Code: ustawienia zarządzane w
`/etc/claude-code/managed-settings.json` (tylko do odczytu, ustawienia z repo produktu ich nie poluzują) i te same
przez `--settings` (`PDI_CLAUDE_SETTINGS` w `phase_run.py`).

Wartości z hosta (token Claude, treść zgłoszenia) idą do kontenera tylko przez środowisko procesu `docker`
(`-e NAZWA` bez wartości), więc nie ma ich w argv ani w logu. Kroki z poświadczeniami (push, PR, prośba o bramkę,
cięcia talosa) zostają na hoście, w `pdi.dispatch_local`. `PDI_DISPATCH_SANDBOX=none` wyłącza kontener jawnie.
"""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
import urllib.parse
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pdi import phase_egress

MODE_ENV = "PDI_DISPATCH_SANDBOX"
MODES = ("docker", "none")
NONE_WARNING = (
    "# UWAGA: PDI_DISPATCH_SANDBOX=none — krok run działa bez izolacji, z dostępem do plików i sieci tego komputera; "
    "domyślnie (docker) persona widzi tylko klon repo produktu."
)
# Ta sama wersja co w sdlc-phase.yml tf; z klonu (szablon workflow) ma pierwszeństwo.
CLAUDE_VERSION = "2.1.310"
TEMPLATE = ".claude/skills/pdi-decisions/templates/sdlc-phase.yml"
_CLAUDE_PIN = re.compile(r"@anthropic-ai/claude-code@([0-9]+\.[0-9]+\.[0-9]+)")
# node:22-bookworm-slim, indeks obrazu z 2026-11-02 (docs/plan-z8a-izolacja-faz.md).
BASE_IMAGE = "node:22-bookworm-slim@sha256:4b150b48b4116e2a22f2c39cc27025fbf4f153e2078fd3b14d159fdb5c7279da"
IMAGE = "pdi-phase"
BASE_PACKAGES = ("python3", "git", "bubblewrap", "socat", "ca-certificates", "coreutils")
HOME = "/home/pdi"
TMP = "/tmp"  # noqa: S108 — tmpfs w kontenerze fazy, nie katalog hosta
SETTINGS_IN_CONTAINER = "/etc/claude-code/managed-settings.json"
EGRESS_IN_CONTAINER = "/opt/pdi/egress.py"
CONTAINER_UID = 10001
CPUS_ENV, MEMORY_ENV = "PDI_DISPATCH_CPUS", "PDI_DISPATCH_MEMORY"
DEFAULT_CPUS, DEFAULT_MEMORY, PIDS = "4", "6g", "1024"
ALLOW_HOSTS_ENV = "PDI_DISPATCH_ALLOW_HOSTS"
UPSTREAM_ENV = "PDI_EGRESS_UPSTREAM"
# Środowisko klienta `docker` na hoście: PATH (na Macu docker jest w /usr/local/bin) i HOME (kontekst Docker Desktop
# w ~/.docker) plus zmienne samego Dockera. Bez tokenów i reszty środowiska pdi.
DOCKER_ENV = (
    "PATH", "HOME", "USER", "TMPDIR",
    "DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_CONFIG", "DOCKER_CERT_PATH", "DOCKER_TLS_VERIFY",
)  # fmt: skip
# Ze zmiennych systemowych kroku `run` do kontenera idą tylko te, które nie są ścieżkami ani gniazdami hosta.
CONTAINER_SYSTEM = ("LANG", "LANGUAGE", "TERM", "TZ")
CONTAINER_PREFIXES = ("LC_", "GIT_")
TOKENS = ("CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY")
CLOUD_SWITCHES = ("CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY")
_SECRET_NAME = re.compile(r"(TOKEN|KEY|SECRET|PASSWORD)$")
_SIZE = re.compile(r"^[0-9]{1,4}(\.[0-9]{1,2})?$")
_MEMORY = re.compile(r"^[0-9]{1,6}[kmg]$")
_HOST = re.compile(r"^(\*\.)?[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?)+$")
ANY = tuple(range(256))

# Pliki w katalogu głównym klonu → pakiety Debiana (narzędzia budowania produktu) i hosty rejestrów.
TOOLS = {
    "pyproject.toml": ("python3-pip", "python3-venv"),
    "requirements.txt": ("python3-pip", "python3-venv"),
    "go.mod": ("golang-go",),
    "Cargo.toml": ("cargo",),
    "Gemfile": ("ruby-full", "bundler"),
    "pom.xml": ("default-jdk-headless", "maven"),
    "build.gradle": ("default-jdk-headless",),
    "build.gradle.kts": ("default-jdk-headless",),
}
REGISTRIES = {
    "package.json": ("registry.npmjs.org",),
    "pyproject.toml": ("pypi.org", "files.pythonhosted.org"),
    "requirements.txt": ("pypi.org", "files.pythonhosted.org"),
    "go.mod": ("proxy.golang.org", "sum.golang.org"),
    "Cargo.toml": ("index.crates.io", "static.crates.io"),
    "Gemfile": ("rubygems.org", "index.rubygems.org"),
    "pom.xml": ("repo.maven.apache.org", "repo1.maven.org"),
    "build.gradle": ("repo.maven.apache.org", "repo1.maven.org", "plugins.gradle.org"),
    "build.gradle.kts": ("repo.maven.apache.org", "repo1.maven.org", "plugins.gradle.org"),
}
ALWAYS_HOSTS = ("api.anthropic.com",)
# Rejestr reguł Semgrepa dla skanera w pętli talosa (Z8c, DZ11).
SCANNER_HOSTS = ("semgrep.dev",)
# Wywołania jądra zakazane w kontenerze fazy. Reszta dozwolona, w tym przestrzenie nazw użytkownika, których
# potrzebuje sandbox Claude Code (bubblewrap); domyślny profil Dockera je blokuje (plan, „Sprawdzone lokalnie”).
SECCOMP_DENY = (
    "acct", "add_key", "bpf", "clock_adjtime", "clock_settime", "create_module", "delete_module", "finit_module",
    "get_kernel_syms", "get_mempolicy", "init_module", "ioperm", "iopl", "kcmp", "kexec_file_load", "kexec_load",
    "keyctl", "lookup_dcookie", "mbind", "move_pages", "name_to_handle_at", "nfsservctl", "open_by_handle_at",
    "perf_event_open", "process_vm_readv", "process_vm_writev", "ptrace", "query_module", "quotactl", "reboot",
    "request_key", "set_mempolicy", "settimeofday", "stime", "swapoff", "swapon", "sysfs", "_sysctl", "uselib",
    "userfaultfd", "ustat", "vm86", "vm86old",
)  # fmt: skip

# (argv, ok, quiet, extra) → (kod, wyjście); w pdi.dispatch_local to `step` z logiem i nazwą kroku.
Step = Callable[..., tuple[int, str]]
Run = Callable[[list[str], Path, Mapping[str, str]], tuple[int, str]]


class SandboxError(Exception):
    """Kontener fazy nie może wystartować; komunikat mówi, co zrobić."""


def mode(env: Mapping[str, str]) -> str:
    value = (env.get(MODE_ENV) or "docker").strip()
    if value not in MODES:
        raise SandboxError(f"{MODE_ENV} musi być jednym z: {', '.join(MODES)} (jest „{value[:40]}”).")
    return value


def docker_problem(run: Run, cwd: Path, env: Mapping[str, str]) -> str | None:
    """Opis problemu, gdy Docker nie odpowiada; None, gdy działa."""
    code, _ = run(["docker", "version", "--format", "{{.Server.Version}}"], cwd, _docker_env(env))
    if code == 0:
        return None
    return (
        "Docker nie odpowiada, a fazy w trybie lokalnym działają w kontenerze (PDI_DISPATCH_SANDBOX=docker, "
        "domyślnie). Uruchom Docker Desktop i ponów; bez izolacji tylko jawnie: PDI_DISPATCH_SANDBOX=none."
    )


# --- obraz ---


@dataclass(frozen=True)
class Image:
    tag: str
    dockerfile: str


def claude_version(checkout: Path) -> str:
    """Wersja Claude Code z szablonu sdlc-phase.yml w klonie (tę samą instaluje Actions) albo CLAUDE_VERSION."""
    try:
        match = _CLAUDE_PIN.search((checkout / TEMPLATE).read_text(encoding="utf-8"))
    except OSError:
        match = None
    return match.group(1) if match else CLAUDE_VERSION


def build_tools(checkout: Path) -> list[str]:
    return sorted({p for name, packages in TOOLS.items() if (checkout / name).is_file() for p in packages})


def allowed_hosts(checkout: Path, env: Mapping[str, str]) -> list[str]:
    hosts = list(ALWAYS_HOSTS)
    base_url = urllib.parse.urlsplit(env.get("ANTHROPIC_BASE_URL") or "").hostname
    candidates = [
        *(h for name, found in REGISTRIES.items() if (checkout / name).is_file() for h in found),
        *SCANNER_HOSTS,
        *([base_url] if base_url else []),
        *(h.strip().lower() for h in (env.get(ALLOW_HOSTS_ENV) or "").split(",")),
    ]
    for host in candidates:
        if host and _HOST.match(host) and host not in hosts:
            hosts.append(host)
    return hosts


def dockerfile(version: str, packages: Sequence[str]) -> str:
    """Dockerfile obrazu fazy: przypięta baza, Claude Code w wersji z sdlc-phase.yml, bez roota i bez sekretów."""
    apt = " ".join([*BASE_PACKAGES, *packages])
    onboarding = (
        'if [ -n "$HOME" ] && [ -w "$HOME" ] && [ ! -e "$HOME/.claude.json" ]; then '
        'echo "{\\"hasCompletedOnboarding\\": true}" > "$HOME/.claude.json"; fi'
    )
    return "\n".join(
        [
            f"FROM {BASE_IMAGE}",
            "RUN apt-get update \\",
            f" && apt-get install -y --no-install-recommends {apt} \\",
            " && rm -rf /var/lib/apt/lists/*",
            f"RUN npm install -g @anthropic-ai/claude-code@{version} && npm cache clean --force",
            "RUN git config --system safe.directory '*'",
            f"RUN useradd --create-home --uid {CONTAINER_UID} pdi",
            f"COPY egress.py {EGRESS_IN_CONTAINER}",
            # anthropics/claude-code#73403: token pomijany, dopóki onboarding nie jest oznaczony jako zrobiony.
            f"RUN printf '%s\\n' '#!/bin/sh' '{onboarding}' 'exec \"$@\"' > /opt/pdi/entrypoint.sh \\",
            " && chmod 755 /opt/pdi/entrypoint.sh",
            "USER pdi",
            f"WORKDIR {HOME}",
            'ENTRYPOINT ["/opt/pdi/entrypoint.sh"]',
            "",
        ]
    )


def image_for(checkout: Path) -> Image:
    version = claude_version(checkout)
    text = dockerfile(version, build_tools(checkout))
    digest = hashlib.sha256((text + "\0" + _egress_source()).encode()).hexdigest()[:12]
    return Image(tag=f"{IMAGE}:{version}-{digest}", dockerfile=text)


def ensure_image(checkout: Path, *, run: Run, env: Mapping[str, str], force: bool = False) -> tuple[str, bool]:
    """Obraz fazy dla klonu: `(tag, zbudowany_teraz)`; buduje, gdy go nie ma (albo `force`)."""
    image = image_for(checkout)
    docker_env = _docker_env(env)
    if (
        not force
        and run(["docker", "image", "inspect", "--format", "{{.Id}}", image.tag], checkout, docker_env)[0] == 0
    ):
        return image.tag, False
    with tempfile.TemporaryDirectory(prefix="pdi-phase-") as context:
        (Path(context) / "Dockerfile").write_text(image.dockerfile, encoding="utf-8")
        (Path(context) / "egress.py").write_text(_egress_source(), encoding="utf-8")
        code, out = run(["docker", "build", "-t", image.tag, context], checkout, docker_env)
    if code != 0:
        tail = "\n".join(out.strip().splitlines()[-5:])
        raise SandboxError(f"docker build {image.tag} zakończony kodem {code}: {tail}")
    return image.tag, True


# --- ustawienia Claude Code i profil seccomp ---


def claude_settings(hosts: Sequence[str], secret_names: Sequence[str]) -> dict[str, Any]:
    """Ustawienia sandboxu Claude Code: zarządzane w kontenerze i te same w `--settings`."""
    denied = sorted({*TOKENS, "ANTHROPIC_AUTH_TOKEN", "GH_TOKEN", "GITHUB_TOKEN", *secret_names})
    home_secrets = ["~/.claude.json", "~/.claude", "~/.ssh", "~/.sdlc", "~/.aws", "~/.config"]
    return {
        "sandbox": {
            "enabled": True,
            "failIfUnavailable": True,
            "allowUnsandboxedCommands": False,
            "autoAllowBashIfSandboxed": False,
            "enableWeakerNestedSandbox": True,
            "filesystem": {"denyRead": home_secrets, "allowWrite": [TMP]},
            "network": {"allowedDomains": list(hosts), "allowManagedDomainsOnly": True},
            "credentials": {"envVars": [{"name": name, "mode": "deny"} for name in denied]},
        },
        "permissions": {
            "deny": [
                "Read(//proc/**)",
                "Read(~/.claude.json)",
                "Read(~/.claude/**)",
                "Read(~/.ssh)",
                "Read(~/.sdlc/**)",
            ]
        },
    }


def seccomp_profile() -> dict[str, Any]:
    return {
        "defaultAction": "SCMP_ACT_ALLOW",
        "syscalls": [{"names": list(SECCOMP_DENY), "action": "SCMP_ACT_ERRNO", "errnoRet": 1}],
    }


# --- krok run ---


@dataclass
class Box:
    """Kontener fazy jednego przebiegu: nazwy, argv i co już powstało (do sprzątania)."""

    network: str
    phase: str
    egress: str
    argv: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    created: list[str] = field(default_factory=list)

    @classmethod
    def of(cls, log: str) -> Box:
        name = re.sub(r"[^a-z0-9_.-]", "-", Path(log).stem.lower()).strip("-.") or "run"
        return cls(network=f"pdi-phase-{name}", phase=f"pdi-phase-{name}", egress=f"pdi-egress-{name}")


def prepare(
    box: Box,
    *,
    checkout: Path,
    log_path: Path,
    env: Mapping[str, str],
    base: Mapping[str, str],
    passed: set[str],
    run_argv: Sequence[str],
    run_env: Mapping[str, str],
    timeout: int,
    step: Step,
    user: tuple[int, int] | None = None,
) -> Box:
    """Sprawdza token i obraz, zapisuje ustawienia, stawia sieć i proxy; wypełnia `box.argv` i `box.env`."""
    _check_token(env)
    docker_env = _docker_env(env)
    image = image_for(checkout)
    code, _ = step("run", ["docker", "image", "inspect", "--format", "{{.Id}}", image.tag], ok=ANY, quiet=True,
                   extra=docker_env)  # fmt: skip
    if code != 0:
        raise SandboxError(
            f"Brak obrazu fazy {image.tag} — uruchom `uv run sdlc image` (albo `uv run sdlc up`) i ponów."
        )

    mounts = [checkout]
    if (checkout / ".git").is_file():  # worktree: git potrzebuje też wspólnego katalogu .git
        _, out = step("run", ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], quiet=True)
        common = Path(out.strip())
        if common.is_absolute() and not _inside(common, checkout):
            mounts.append(common)
    for path in mounts:
        if "," in str(path) or "=" in str(path):
            raise SandboxError(f"Ścieżka {path} ma przecinek albo znak „=” — Docker nie zamontuje jej przez --mount.")

    identity = {}
    for key, names in (("user.name", ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME")),
                       ("user.email", ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"))):  # fmt: skip
        code, out = step("run", ["git", "config", key], ok=ANY, quiet=True)
        if code == 0 and out.strip():
            identity.update(dict.fromkeys(names, out.strip()))

    values = {
        **{k: v for k, v in base.items() if k in CONTAINER_SYSTEM or k.startswith(CONTAINER_PREFIXES) or k in passed},
        **{k: v for k, v in run_env.items() if k != "PDI_CLAUDE_BIN"},
        **identity,
    }
    proxy = f"http://{box.egress}:{phase_egress.PORT}"
    fixed = {
        "HOME": HOME,
        "TMPDIR": TMP,
        "HTTPS_PROXY": proxy,
        "HTTP_PROXY": proxy,
        "https_proxy": proxy,
        "http_proxy": proxy,
        "NO_PROXY": "localhost,127.0.0.1",
        "no_proxy": "localhost,127.0.0.1",
        "DISABLE_AUTOUPDATER": "1",
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        "PDI_CLAUDE_SETTINGS": SETTINGS_IN_CONTAINER,
    }
    values = {k: v for k, v in values.items() if k not in fixed}

    hosts = allowed_hosts(checkout, env)
    stem = log_path.stem
    settings = log_path.with_name(f"{stem}.claude-settings.json")
    seccomp = log_path.with_name(f"{stem}.seccomp.json")
    secret_names = [k for k in values if _SECRET_NAME.search(k)]
    _write_json(settings, claude_settings(hosts, secret_names))
    _write_json(seccomp, seccomp_profile())

    step("run", ["docker", "network", "create", "--internal", box.network], quiet=True, extra=docker_env)
    box.created.append("network")
    upstream = ["-e", UPSTREAM_ENV] if env.get(UPSTREAM_ENV) else []
    egress = [
        "docker", "run", "-d", "--rm", "--name", box.egress, "--network", "bridge", "--read-only",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--memory", "256m", "--cpus", "0.5",
        "--pids-limit", "128", *upstream, image.tag, "python3", "-I", EGRESS_IN_CONTAINER, ",".join(hosts),
    ]  # fmt: skip
    step("run", egress, quiet=True, extra={**docker_env, **({UPSTREAM_ENV: env[UPSTREAM_ENV]} if upstream else {})})
    box.created.append("egress")
    step("run", ["docker", "network", "connect", box.network, box.egress], quiet=True, extra=docker_env)

    uid, gid = user or _owner(checkout)
    box.argv = [
        "docker", "run", "--rm", "--name", box.phase, "--network", box.network, "--user", f"{uid}:{gid}",
        "--read-only", "--tmpfs", f"{TMP}:rw,exec,nosuid,size=1g",
        "--tmpfs", f"{HOME}:rw,exec,nosuid,size=1g,uid={uid},gid={gid}",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--security-opt", f"seccomp={seccomp}",
        "--cpus", _limit(env, CPUS_ENV, DEFAULT_CPUS, _SIZE),
        "--memory", _limit(env, MEMORY_ENV, DEFAULT_MEMORY, _MEMORY),
        "--pids-limit", PIDS,
        *(a for path in mounts for a in ("--mount", f"type=bind,src={path},dst={path}")),
        "--mount", f"type=bind,src={settings},dst={SETTINGS_IN_CONTAINER},readonly",
        "--workdir", str(checkout),
        *(a for k, v in fixed.items() for a in ("-e", f"{k}={v}")),
        *(a for k in values for a in ("-e", k)),
        image.tag, "timeout", "--kill-after=30", str(max(timeout - 60, 60)), *run_argv,
    ]  # fmt: skip
    box.env = {**docker_env, **values}
    box.created.append("phase")
    return box


def cleanup(box: Box, *, step: Step, log: Callable[[str], None], env: Mapping[str, str]) -> None:
    """Zablokowane hosty z logów proxy do logu przebiegu, potem usuwa kontenery i sieć przebiegu."""
    if not box.created:
        return
    docker_env = _docker_env(env)
    if "egress" in box.created:
        code, out = step("run", ["docker", "logs", box.egress], ok=ANY, quiet=True, extra=docker_env)
        for line in out.splitlines() if code == 0 else []:
            if line.startswith(phase_egress.BLOCKED):
                log(f"# sieć: krok run — zablokowany host {line[len(phase_egress.BLOCKED) :].strip()[:300]}")
    names = [n for n, part in ((box.phase, "phase"), (box.egress, "egress")) if part in box.created]
    if names:
        step("run", ["docker", "rm", "-f", *names], ok=ANY, quiet=True, extra=docker_env)
    if "network" in box.created:
        step("run", ["docker", "network", "rm", box.network], ok=ANY, quiet=True, extra=docker_env)
    box.created.clear()


def _check_token(env: Mapping[str, str]) -> None:
    present = [name for name in TOKENS if env.get(name)]
    if len(present) > 1:
        raise SandboxError(
            "Ustaw tylko jedną ze zmiennych CLAUDE_CODE_OAUTH_TOKEN i ANTHROPIC_API_KEY (w -p klucz API wygrywa i "
            "zastępuje subskrypcję) — usuń drugą z ~/.sdlc/env i ponów."
        )
    if present or env.get("ANTHROPIC_AUTH_TOKEN") or any(env.get(s) for s in CLOUD_SWITCHES):
        return
    raise SandboxError(
        "Faza w kontenerze nie widzi logowania Claude z tego komputera. Uruchom `claude setup-token` i dopisz "
        "CLAUDE_CODE_OAUTH_TOKEN=<token> do ~/.sdlc/env (albo ANTHROPIC_API_KEY — tylko jedną z nich), potem "
        "`uv run sdlc up` i ponów fazę."
    )


def _docker_env(env: Mapping[str, str]) -> dict[str, str]:
    return {k: env[k] for k in DOCKER_ENV if env.get(k)}


def _limit(env: Mapping[str, str], name: str, default: str, pattern: re.Pattern[str]) -> str:
    value = (env.get(name) or "").strip().lower()
    return value if pattern.match(value) else default


def _owner(checkout: Path) -> tuple[int, int]:
    """uid:gid właściciela klonu (pliki persony mają tego samego właściciela co na hoście); nigdy root."""
    info = checkout.stat()
    return (CONTAINER_UID, CONTAINER_UID) if info.st_uid == 0 else (info.st_uid, info.st_gid)


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _egress_source() -> str:
    return Path(phase_egress.__file__).read_text(encoding="utf-8")
