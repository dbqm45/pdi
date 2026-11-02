# Plan Z8a — fazy tf w kontenerze (izolacja persony i talosa)

Data: 2026-11-02 · Status: **w PR** (pdi + tf, do przeglądu; GitHub Actions na tym koncie nie działają, bramki uruchomione lokalnie) · Krok Z8a [planu „zespół jednoosobowy”](plan-zespol-jednoosobowy.md)
(§8.2), w granicach decyzji **DZ9** ([decyzje](decyzje.md)): kontener Docker z zamontowanym tylko klonem repo produktu,
z listą dozwolonych adresów sieci; sandbox Claude Code jako druga warstwa; kroki z poświadczeniami zostają poza
kontenerem.

## Cel

W trybie lokalnym (`PDI_DISPATCH=local`) krok `run` fazy (`phase_run.py run` → `claude --print --agent <persona>`,
w fazie `delivery` także talos) działa w kontenerze, który:

- widzi tylko klon repo produktu (montowany do zapisu pod tą samą ścieżką), a nie katalog domowy właściciela,
  `~/.sdlc/env`, `~/.ssh`, `~/.claude`, inne repo ani klucze;
- łączy się tylko z hostami z listy, przez proxy wyjścia; każda odmowa jest w logu przebiegu z krokiem i hostem;
- dostaje środowisko dzisiejszego kroku `run` (zmienne systemowe, `PDI_SOURCE`, `PDI_PROBLEM`, zmienne Claude) i nic
  więcej; token Claude idzie tylko do tego kontenera, nigdy do argv, logu ani obrazu.

Kroki `checkout`, `branch`, `change`, `prompt`, `decision`, `commit`, `push`, `pr`, `gate` i wypychanie cięć talosa
zostają na komputerze właściciela, jak dziś (potrzebują `gh`, kluczy git i sekretu odbiornika).

## Sprawdzone w dokumentacji (§8.4), 2026-11-02

| Co | Wynik | Źródło |
|---|---|---|
| Sandbox Claude Code: klucze | `sandbox.enabled`, `failIfUnavailable`, `allowUnsandboxedCommands`, `autoAllowBashIfSandboxed`, `filesystem.denyRead`/`allowWrite`, `network.allowedDomains`, `network.allowManagedDomainsOnly` (tylko ustawienia zarządzane), `enableWeakerNestedSandbox`, `credentials.envVars` z `mode: deny` (zmienna usunięta przed każdym poleceniem w sandboxie) | [Sandboxing](https://code.claude.com/docs/en/sandboxing) |
| Zakres sandboxu | tylko polecenia powłoki (Bash) i procesy, które uruchamiają; Read/Edit/WebFetch idą według reguł uprawnień (`denyRead` nie blokuje narzędzia Read) | jw. |
| Ustawienia z repo nie luzują | listy łączą się między zakresami, więc `.claude/settings.json` produktu mógłby dopisać hosty; przy `allowManagedDomainsOnly: true` albo `allowUnsandboxedCommands: false` w **ustawieniach zarządzanych** Claude Code ignoruje luzujące klucze z repo (`allowedDomains`, `allowWrite`, `excludedCommands`) | jw. |
| Kolejność ustawień | zarządzane > `--settings` (plik albo JSON) > lokalne projektu > projektu > użytkownika; `--settings` nie nadpisuje zarządzanych | [Settings](https://code.claude.com/docs/en/settings) |
| Sandbox w kontenerze | bez uprawnień bubblewrap nie zamontuje nowego `/proc`; `enableWeakerNestedSandbox: true`, gdy zewnętrzny kontener już izoluje | [Sandboxing](https://code.claude.com/docs/en/sandboxing) |
| Proxy firmowe pod sandboxem | sandbox sprawdza listę, a dozwolone połączenia tuneluje przez `HTTPS_PROXY` | jw. |
| Linux | potrzebne `bubblewrap` i `socat`; Ubuntu 24.04 z AppArmor blokuje przestrzenie nazw dla bwrap (dotyczy Actions) | jw. |
| Uwierzytelnianie | `claude setup-token` → token na rok, do `CLAUDE_CODE_OAUTH_TOKEN`; kolejność: `ANTHROPIC_AUTH_TOKEN` > `ANTHROPIC_API_KEY` > `apiKeyHelper` > `CLAUDE_CODE_OAUTH_TOKEN` > `/login`; w `-p` klucz API zawsze wygrywa, więc ustawiamy tylko jedną zmienną | [Authentication](https://code.claude.com/docs/en/authentication) |
| Hosty Claude Code | `api.anthropic.com` (API, flagi, telemetria); `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` wyłącza resztę (Datadog, aktualizacje) | [Network config](https://code.claude.com/docs/en/network-config) |
| Błąd onboardingu | zgłoszenie [anthropics/claude-code#73403](https://github.com/anthropics/claude-code/issues/73403) („CLAUDE_CODE_OAUTH_TOKEN ignored on first run due to onboarding gate”) zamknięte 2026-07-02; strona Authentication: przed 2.1.290 ekran logowania pojawiał się mimo poświadczeń | GitHub (wyszukiwarka), [Authentication](https://code.claude.com/docs/en/authentication) |
| Wersja CLI | `@anthropic-ai/claude-code@2.1.310` (tę instaluje `sdlc-phase.yml`), opublikowana 2026-10-23, `node >= 22`, binarka natywna z pakietu dla platformy | registry.npmjs.org |
| Obraz bazowy | `node:22-bookworm-slim`, indeks `sha256:4b150b48b4116e2a22f2c39cc27025fbf4f153e2078fd3b14d159fdb5c7279da` (2026-11-02) | Docker Hub (przez mirror.gcr.io) |

### Sprawdzone lokalnie (Docker 29.9.2, Linux, 2026-11-02)

1. **bwrap w kontenerze:** z domyślnym profilem seccomp Dockera `bwrap --unshare-user` kończy się „No permissions to
   create new namespace”; z `seccomp=unconfined` nie montuje `/proc` („Can't mount proc”), a wariant z
   `--bind /proc /proc` (to robi `enableWeakerNestedSandbox`) działa. Działa też z własnym, małym profilem seccomp
   (domyślnie zezwól, zakaz ok. 40 wywołań jądra: `bpf`, `kexec_*`, `keyctl`, `ptrace`, `perf_event_open`,
   `process_vm_*`, moduły jądra, `userfaultfd`, …) razem z `--cap-drop ALL`, `no-new-privileges` i `--read-only`.
2. **`failIfUnavailable` z ustawień zarządzanych** (`/etc/claude-code/managed-settings.json`): bez bwrap Claude Code
   2.1.310 kończy się przy starcie: „sandbox required but unavailable … refusing to start without a working sandbox”.
   Przy działającym bwrap, ale zablokowanych przestrzeniach nazw, start przechodzi, a odmowa przyszłaby przy pierwszym
   poleceniu — stąd własny profil seccomp.
3. **Token:** z `CLAUDE_CODE_OAUTH_TOKEN` (fałszywy) w czystym `HOME` i bez `~/.claude.json` `claude --print` 2.1.310
   wysyła token do API (odpowiedź 401 „OAuth access token is invalid”), a bez tokenu odpowiada „Not logged in”. Błąd
   onboardingu w trybie `--print` tej wersji nie występuje; mimo to obraz zapisuje `{"hasCompletedOnboarding": true}` w
   `~/.claude.json` kontenera (tmpfs), co nie szkodzi i chroni przy starszej wersji.
4. **Sieć:** kontener tylko w sieci `--internal` nie rozwiązuje nazw spoza Dockera; przez proxy wyjścia `CONNECT` do
   hosta z listy daje 200, do innego 403 i linię `pdi-egress: blocked example.com:443`.

## Obraz `pdi-phase`

- **Budowa:** `sdlc up` (gdy jest skonfigurowany klon repo faz) i `sdlc image` (ręcznie, `--force` od nowa). Dockerfile
  generuje pdi (`pdi.phase_sandbox.dockerfile()`); kontekst budowy to katalog tymczasowy z Dockerfile i
  `egress.py` (kopia `pdi.phase_egress`). Bez sekretów: żadnego `ARG`/`ENV` z tokenem, żadnych plików z domu.
- **Zawartość:** `FROM node:22-bookworm-slim@sha256:…` (przypięty), `apt-get install` `python3 git bubblewrap socat
  ca-certificates coreutils` i narzędzia produktu wykryte w klonie, `npm install -g @anthropic-ai/claude-code@<wersja>`,
  `git config --system safe.directory '*'`, użytkownik `pdi` (uid 10001, bez roota), `/opt/pdi/egress.py`.
- **Wersja Claude Code:** z `.claude/skills/pdi-decisions/templates/sdlc-phase.yml` w klonie (to samo
  `@anthropic-ai/claude-code@X` co w Actions), a gdy go nie ma — `CLAUDE_VERSION` w pdi (2.1.310).
- **Narzędzia produktu** (wykrywane po plikach w katalogu głównym klonu): `pyproject.toml`/`requirements*.txt` →
  `python3-venv python3-pip`; `go.mod` → `golang-go`; `Cargo.toml` → `cargo`; `Gemfile` → `ruby-full bundler`;
  `pom.xml`/`build.gradle*` → `default-jdk-headless maven`; `package.json` — node i npm już są.
- **Nazwa:** `pdi-phase:<wersja claude>-<12 znaków sha256 z Dockerfile i egress.py>`; inna wersja albo inne narzędzia
  to inny tag, więc zmiana nie wymaga ręcznego czyszczenia.

## Krok `run` w kontenerze

Na hoście, przed krokiem (`pdi.phase_sandbox.prepare`): sprawdzenie Dockera i obrazu, tokenu (dokładnie jedna z
`CLAUDE_CODE_OAUTH_TOKEN`, `ANTHROPIC_API_KEY`; Bedrock/Vertex — bez tego wymogu), zapis ustawień Claude i profilu
seccomp obok logu (bez sekretów), sieć i proxy:

```text
docker network create --internal pdi-phase-<id>
docker run -d --rm --name pdi-egress-<id> --read-only --cap-drop ALL --security-opt no-new-privileges
    --memory 256m --cpus 0.5 [-e PDI_EGRESS_UPSTREAM] pdi-phase:… python3 -I /opt/pdi/egress.py <hosty>
docker network connect pdi-phase-<id> pdi-egress-<id>
```

Sam krok:

```text
docker run --rm --name pdi-phase-<id> --network pdi-phase-<id> --user <właściciel klonu> --read-only
    --tmpfs /tmp:rw,exec,size=1g --tmpfs /home/pdi:rw,exec,size=1g,uid=<uid>,gid=<gid>
    --cap-drop ALL --security-opt no-new-privileges --security-opt seccomp=<profil>
    --cpus 4 --memory 6g --pids-limit 1024
    --mount type=bind,src=<klon>,dst=<klon> [--mount … wspólny katalog .git, gdy klon jest worktree]
    --mount type=bind,src=<ustawienia>,dst=/etc/claude-code/managed-settings.json,readonly
    --workdir <klon> -e HOME=/home/pdi -e HTTPS_PROXY=http://pdi-egress-<id>:3128 … -e PDI_PROBLEM -e CLAUDE_CODE_OAUTH_TOKEN …
    pdi-phase:… timeout --kill-after=30 <limit> python3 .claude/skills/pdi-decisions/scripts/phase_run.py run …
```

- **Środowisko:** wartości jawne i stałe (`HOME`, `PATH`, proxy, `DISABLE_AUTOUPDATER=1`,
  `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`, `PDI_CLAUDE_SETTINGS`) idą jako `-e NAZWA=wartość`; wszystko z hosta
  (zmienne `LANG`, `LC_*`, `TZ`, `TERM`, `GIT_*`, `PDI_DISPATCH_ENV_PASS`, `PDI_SOURCE`, `PDI_PROBLEM`, `ANTHROPIC_*`,
  `CLAUDE_*`) — jako samo `-e NAZWA`, a wartość dostaje proces `docker` w środowisku. Bez `PATH`, `HOME`, `TMPDIR`,
  `SSH_AUTH_SOCK`, `XDG_*` i proxy hosta (ścieżki i gniazda z komputera właściciela). `PDI_CLAUDE_BIN` nie idzie (ścieżka
  z hosta). Tożsamość git (`user.name`, `user.email` z klonu na hoście) idzie jako `GIT_AUTHOR_*`/`GIT_COMMITTER_*`, bo
  talos robi commity cięć w kontenerze.
- **Użytkownik:** uid:gid właściciela klonu na hoście (pliki persony mają tego samego właściciela); gdy klon należy do
  roota — uid 10001, nigdy root.
- **Limity:** `PDI_DISPATCH_CPUS` (4), `PDI_DISPATCH_MEMORY` (6g), czas = `STEP_TIMEOUT_SECONDS` przez `timeout` w
  kontenerze (zabicie klienta `docker` nie zatrzymuje kontenera); po kroku zawsze `docker rm -f` kontenera fazy i
  proxy oraz `docker network rm`.
- **Ustawienia Claude Code** (`--settings` przez `PDI_CLAUDE_SETTINGS` w tf i ten sam plik jako ustawienia zarządzane;
  te same klucze wypisuje w tf `sandbox_settings.py`, w kontenerze z `enableWeakerNestedSandbox: true`):

```json
{
  "sandbox": {
    "enabled": true, "failIfUnavailable": true, "allowUnsandboxedCommands": false,
    "autoAllowBashIfSandboxed": false, "enableWeakerNestedSandbox": true,
    "filesystem": {"denyRead": ["~/.claude.json", "~/.claude", "~/.ssh", "~/.sdlc", "~/.aws", "~/.config"], "allowWrite": ["/tmp"]},
    "network": {"allowedDomains": ["<hosty>"], "allowManagedDomainsOnly": true},
    "credentials": {"envVars": [{"name": "ANTHROPIC_API_KEY", "mode": "deny"}, {"name": "CLAUDE_CODE_OAUTH_TOKEN", "mode": "deny"}, …]}
  },
  "permissions": {"deny": ["Read(//proc/**)", "Read(~/.claude.json)", "Read(~/.claude/**)", "Read(~/.ssh)", "Read(~/.sdlc/**)"]}
}
```

  `autoAllowBashIfSandboxed: false` zostawia dzisiejsze uprawnienia persony (`acceptEdits` i reguły z repo), więc
  sandbox nie poszerza tego, co persona może uruchomić bez pytania. W kontenerze ustawienia zarządzane są pod
  `/etc/claude-code/managed-settings.json` (tylko do odczytu) — to one blokują luzowanie z repo produktu.

## Sieć

- **Lista hostów:** `api.anthropic.com` zawsze; rejestry według plików w klonie (`package.json` → `registry.npmjs.org`;
  Python → `pypi.org`, `files.pythonhosted.org`; Go → `proxy.golang.org`, `sum.golang.org`; Rust → `index.crates.io`,
  `static.crates.io`; Ruby → `rubygems.org`, `index.rubygems.org`; Java → `repo.maven.apache.org`, `repo1.maven.org`);
  `semgrep.dev` dla reguł Semgrepa (Z8c); dodatkowe przez `PDI_DISPATCH_ALLOW_HOSTS` (po przecinku, `*.domena`
  dozwolone). `github.com` nie jest na liście: push i PR robi host.
- **Dwie warstwy:** sieć Dockera `--internal` + proxy `pdi-egress` (jedyna droga na zewnątrz, zatrzymuje wszystko, co
  nie jest na liście, także WebFetch i sam proces `claude`), a w kontenerze sandbox Claude Code z tą samą listą dla
  poleceń Bash.
- **Log:** po kroku pdi czyta `docker logs pdi-egress-<id>` i dopisuje `# sieć: krok run — zablokowany host <host:port>`
  dla każdej odmowy; odmowy sandboxu Claude Code (polecenie Bash) persona widzi w wyniku narzędzia, a proxy loguje
  każdą próbę, która ominęła sandbox.
- **Proxy firmowe:** `PDI_EGRESS_UPSTREAM=http://host:port` — proxy wyjścia łączy się przez nie (adres musi być osiągalny
  z sieci Dockera, nie `127.0.0.1` hosta).

## Konfiguracja

- `PDI_DISPATCH_SANDBOX=docker` (domyślnie) | `none` — `none` to jawne wyłączenie: każdy przebieg zaczyna się w logu od
  `# UWAGA: PDI_DISPATCH_SANDBOX=none — krok run działa bez izolacji …`; inna wartość — przebieg odmawia.
- Bez Dockera (`docker version` nie odpowiada) `dispatch_phase` odmawia od razu („Docker nie odpowiada — uruchom
  Docker Desktop albo ustaw PDI_DISPATCH_SANDBOX=none”), a `sdlc up` kończy się błędem z tym samym opisem. Brak obrazu →
  krok `run` odmawia z „uruchom `uv run sdlc image`”. Bez tokenu albo z dwoma → krok `run` odmawia z instrukcją
  (`claude setup-token`, wpis w `~/.sdlc/env`).

## GitHub Actions (tf `sdlc-phase.yml`)

- `actions/checkout` z `persist-credentials: false` — w `.git/config` nie ma tokenu, więc persona go nie przeczyta.
- `GH_TOKEN: ${{ github.token }}` tylko w krokach, które go potrzebują (gałąź fazy: `ls-remote`; PR-y cięć; PR fazy);
  w nich `gh auth setup-git` (pomocnik poświadczeń `gh`, token tylko z env kroku).
- Krok persony: `sudo apt-get install bubblewrap socat`, profil AppArmor dla bwrap (Ubuntu 24.04), ustawienia
  zarządzane w `/etc/claude-code/managed-settings.json` (te same klucze, lista: `api.anthropic.com`, rejestry z repo,
  `semgrep.dev`) i `PDI_CLAUDE_SETTINGS` dla `--settings`.
- `phase_run.py run`: gdy jest `PDI_CLAUDE_SETTINGS`, dodaje `--settings <wartość>` do wywołania `claude`.
- Nowy `scripts/sandbox_settings.py [--nested] [--root .]` wypisuje JSON ustawień (te same klucze co pdi); w Actions
  bez `--nested`, bo runner to maszyna wirtualna, w której bwrap montuje własny `/proc`.
- Sieć w Actions: lista hostów obejmuje polecenia Bash persony (sandbox); proces `claude` i jego narzędzia sieciowe
  (WebFetch) nie mają w Actions proxy wyjścia — runner jest jednorazowy i nie ma sekretów poza kluczem Claude.

## Pliki

pdi:
1. `src/pdi/phase_egress.py` (nowy) — proxy wyjścia (biblioteka standardowa, też w obrazie).
2. `src/pdi/phase_sandbox.py` (nowy) — tryb, Dockerfile i tag obrazu, wykrywanie narzędzi i hostów, ustawienia Claude,
   profil seccomp, argv `docker run`, `prepare()`/`cleanup()` kroku `run`, `ensure_image()`.
3. `src/pdi/dispatch_local.py` — mała zmiana: w `start()` sprawdzenie Dockera, w `execute()` krok `run` przez
   `phase_sandbox` (albo ostrzeżenie przy `none`). Reszta kroków bez zmian (równoległy Z1 zmienia ten plik).
4. `src/pdi/stack/cli.py` — `sdlc up` sprawdza Dockera i buduje obraz; nowe `sdlc image [--force]`.
5. README, `docs/plan-zespol-jednoosobowy.md` §10, `docs/przebieg-lokalny.md` (pozycje do sprawdzenia na Macu).

tf:
1. `modes/mode-pdi/skills/pdi-decisions/scripts/phase_run.py` — `--settings` z `PDI_CLAUDE_SETTINGS` (dwie linie, bo
   równoległy Z1 zmienia ten plik); nowy `scripts/sandbox_settings.py`.
2. `modes/mode-pdi/skills/pdi-decisions/templates/sdlc-phase.yml` — jak wyżej.
3. Testy w `modes/mode-pdi/tests/`.

## Testy (najpierw czerwone)

pdi (`tests/test_phase_sandbox.py`, `tests/test_phase_egress.py`, `tests/test_stack.py`; dotychczasowe testy
kroków w `tests/test_dispatch_local.py` i `tests/test_inbox.py` działają jawnie w trybie `none`):
- argv `docker run` dla każdej fazy (z podstawionym wykonawcą): montowany tylko klon (i wspólny `.git` worktree), bez
  domu, `--read-only`, `--cap-drop ALL`, `no-new-privileges`, seccomp, limity CPU, pamięci, procesów i czasu, sieć fazy,
  `--user`; środowisko: tylko nazwy z dzisiejszego kroku `run` plus stałe; wartości tokenów nigdy w argv ani logu;
- sieć: kolejność `network create --internal` → proxy → `network connect` → faza → sprzątanie, także po błędzie
  kroku; zablokowane hosty z logów proxy w logu przebiegu;
- token: brak, dwa naraz → odmowa z instrukcją; Bedrock bez tokenu → dalej;
- `PDI_DISPATCH_SANDBOX=none` → ostrzeżenie w logu i dzisiejszy krok na hoście; zła wartość → odmowa;
- bez Dockera: `start()` i `sdlc up` odmawiają z jasnym komunikatem; brak obrazu → odmowa kroku `run`;
- obraz: Dockerfile z przypiętą bazą, wersją Claude z szablonu w klonie, użytkownikiem bez roota, bez sekretów; tag
  zależny od treści; narzędzia i hosty wykryte z plików klonu;
- ustawienia Claude: klucze sandboxu, lista hostów, `credentials.envVars` z oboma tokenami;
- proxy: dopasowanie `*.domena`, porty, odrzucenie zwykłego HTTP, linia `blocked`, test na prawdziwym gnieździe
  (lokalny serwer, dozwolony i zablokowany host).

tf (`modes/mode-pdi/tests/test_phase_run.py`, `test_mode_pdi.py`):
- `run` z `PDI_CLAUDE_SETTINGS` ma `--settings`, bez — nie ma;
- `sandbox_settings.py`: klucze sandboxu, hosty z plików repo i `PDI_DISPATCH_ALLOW_HOSTS` (złe pominięte), tokeny i
  sekrety z domu zablokowane, `--nested`;
- szablon: `persist-credentials: false`; `GH_TOKEN`/`github.token` tylko w krokach gałęzi i PR; krok persony bez
  `GH_TOKEN`/`GITHUB_TOKEN`, z `PDI_CLAUDE_SETTINGS`, ustawieniami zarządzanymi i `failIfUnavailable`.

## Co zostaje (ryzyko szczątkowe)

- Token Claude jest w kontenerze (bez niego persona nie zadziała). Polecenia Bash go nie widzą (`credentials.envVars`),
  narzędzie Read nie czyta `/proc`, a wyjść może tylko do hostów z listy. Token daje tylko dostęp do modelu.
- Kontener ma własny profil seccomp, luźniejszy od domyślnego w jednym punkcie: pozwala na przestrzenie nazw
  użytkownika, których potrzebuje sandbox Claude Code (druga warstwa).
- Linux jako host z AppArmor (np. Ubuntu): profil `docker-default` może blokować montowanie w bwrap — do sprawdzenia
  przy pierwszym takim hoście; docelowy komputer właściciela to Mac (Docker Desktop, maszyna wirtualna bez AppArmor).
- Pierwszy prawdziwy przebieg w kontenerze (Mac, `sdlc-proba`) — pozycje w [przebiegu lokalnym](przebieg-lokalny.md).
