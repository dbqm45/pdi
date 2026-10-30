# Plan L4: `sdlc`, jedno polecenie dla całego stosu

Data: 2026-10-30 · Źródło: [plan `sdlc up`](plan-sdlc-lokalnie.md) §2 Z3 i Z5, §4 L4 · Decyzje DL2 (procesy na
localhost, w Dockerze tylko Postgres) i DL3 (`sdlc` w pdi) w [decyzjach](decyzje.md) · Warunki: L1 (ShipScope #125),
L2 (pdi #59, #62) i L3 (ci_for_sdlc #102) są na `main`.

## Cel

Na Macu z Dockerem, `gh`, `claude`, Node i `uv` polecenie `uv run sdlc up` kończy się linią „gotowe”, a `uv run sdlc
status` pokazuje `connected` dla ShipScope ↔ pdi i ci_for_sdlc → pdi. Nikt nie przepisuje sekretu, tokenu ani
adresu; to zastępuje kroki P2, P5, P7 i P8 [przebiegu S5](przebieg-na-sobie-s5.md).

## Co wymaga przeglądarki (i najmniejsze obejście)

- **Aplikacja GitHub ShipScope.** Przy pierwszym `npm run dev` ShipScope zakłada ją przepływem manifestu: jedno
  kliknięcie na lokalnej stronie (`http://localhost:3000/`). `sdlc up` wypisuje ten adres i czeka (do 15 minut).
- **Logowanie i przestrzeń.** Użytkownik ShipScope powstaje przy logowaniu przez GitHub, a przestrzeń tworzy
  zalogowany człowiek. Tego nie da się zrobić z terminala bez obchodzenia logowania. `sdlc up` raz prosi: „zaloguj
  się w ShipScope i utwórz przestrzeń”, i czeka (do 15 minut).
- **Connect.** W ShipScope Connect wymaga sesji admina, a trzy zmienne pokazuje raz, w przeglądarce. Najmniejsza
  zmiana to osobny PR w ShipScope: komenda `npm run pdi:local --prefix server -- connect|test`
  (`server/scripts/local-pdi.js`). Działa tylko w trybie lokalnym z L1, jako pierwszy admin najstarszej przestrzeni,
  i wypisuje JSON na stdout:
  - kod 3: brak przestrzeni,
  - kod 4: już połączone, `--replace` daje nowe zmienne,
  - `test` pinguje odbiornik jak przycisk Test.

  `sdlc` czyta ten JSON ze stdout, więc sekrety nie trafiają ani do argv, ani na ekran. Bez tego PR-a w ShipScope
  `sdlc up` zatrzymuje się na kroku połączenia i mówi, czego brakuje.

## Polecenia

- `sdlc up` (idempotentne: drugie uruchomienie startuje tylko to, co nie działa):
  1. narzędzia: `docker`, `gh` (+ `gh auth status`), `claude`, `node`, `npm`, `uv`; przy braku — jedno polecenie
     instalacji na narzędzie i kod 1;
  2. `~/.sdlc/config.toml`: ścieżki klonów pdi, ShipScope, ci_for_sdlc, rejestru (`PDI_REGISTRY_PATH`) i opcjonalnie
     repo produktu (`PDI_DISPATCH_CHECKOUT`); pytania tylko przy pierwszym uruchomieniu, z podpowiedziami (sąsiednie
     katalogi klonu pdi);
  3. `~/.sdlc/env` (600, katalog 700, zapis atomowy). Raz generuje `PDI_TF_SIGNING_SECRET`,
     `PDI_CI_FOR_SDLC_SIGNING_SECRET` i `PDI_FORM_TOKEN`; ustawia `PDI_EVENTS_URL=http://127.0.0.1:8787`,
     `PDI_DISPATCH=local` i `PDI_PHASE_BUDGET_USD=3` (DL5). Istniejących wartości nigdy nie nadpisuje;
  4. ShipScope: `node server/scripts/dev.js` w tle (Postgres w Dockerze w kontenerze `shipscope-dev-pg` z wolumenem
     o tej samej nazwie, migracje, web i worker, `SYNC_INTERVAL_MINUTES=1`), czekanie na `GET /health`;
  5. `pdi-receiver` (`uv run --directory <pdi> pdi-receiver`) w tle, czekanie na odpowiedź HTTP z `127.0.0.1:8787`;
  6. pierwsze połączenie, gdy `~/.sdlc/env` nie ma jeszcze `PDI_SHIPSCOPE_*`:
     - `local-pdi.js connect` (czeka na przestrzeń), zapis trzech zmiennych w `~/.sdlc/env`;
     - restart odbiornika, który przy starcie czyta połączenie z ShipScope (dowód „pdi czyta”);
     - `local-pdi.js test` (dowód „ShipScope dociera do pdi”);
  7. ci_for_sdlc, gdy jest repo produktu: `npm install` przy pierwszym razie, potem `npm run analyze -- --repo
     <produkt> --send-to-pdi` z `PDI_EVENTS_URL`, `PDI_SIGNING_SECRET` i `CI_DATA_DIR=~/.sdlc/ci-data`. Serwer
     ci_for_sdlc nie jest potrzebny, bo przepływ na zmianach z repo używa tylko CLI;
  8. serwery MCP `pdi` i `shipscope` w Claude Code (`claude mcp remove` + `claude mcp add --scope user`). Komenda to
     `uv run --directory <pdi> sdlc mcp <nazwa>`, która przy starcie czyta `~/.sdlc/env`, więc w konfiguracji Claude
     (`~/.claude.json`) nie ma żadnej wartości ani sekretu;
  9. lista usług z adresami i „gotowe”.
- `sdlc check`: ponownie krok 7 (np. po scaleniu PR fazy `design`).
- `sdlc deploy <prod|test> [--repo owner/name]`: `gh api` z danymi JSON na stdin:
  - SHA `main` repo próbnego,
  - `POST …/deployments` (`environment` `production` albo `test`, `auto_merge: false`, `required_contexts: []`),
  - `POST …/deployments/<id>/statuses` (`success`);

  wypisuje id i SHA. Repo pochodzi z `--repo`, z `[deploy] repo` w konfiguracji albo z `origin` repo produktu.
- `sdlc status`:
  - procesy (pid, adres, działa?) i Postgres (`docker inspect`);
  - ShipScope ↔ pdi z `GET /api/service/v1/connection` (ta sama funkcja co `get_shipscope_connection`);
  - ci_for_sdlc → pdi z `CI_DATA_DIR` (`pdi-state.json`, `pdi-outbox.json`): `connected` (coś dostarczone, nic w
    kolejce), `queued N`, `configured` (sprawdzenie przeszło, brak zmian do wysłania) albo `not run`;
  - które sekrety są ustawione (same nazwy);
  - ostatnie linie logu odbiornika;
  - otwarte pozycje skrzynki.
- `sdlc open`: ShipScope i formularz zgłoszeń w przeglądarce (token formularza nie pojawia się w wyjściu).
- `sdlc down`: zatrzymuje procesy (grupy procesów z plików pid) i kontener Postgresa; wolumen zostaje.
- `sdlc reset`: po wpisaniu `usuń` usuwa:
  - kontener i wolumen Postgresa,
  - `~/.sdlc/ci-data`, `logs` i `run`,
  - trzy zmienne `PDI_SHIPSCOPE_*`.

  Konfiguracja, pozostałe sekrety i rejestr decyzji zostają.

## Sekrety

- Do procesów trafiają tylko przez środowisko, nigdy przez argv.
- Nie ma ich w wyjściu ani logach `sdlc`; `status` pokazuje tylko, czy są ustawione.
- Plik env jest zapisywany atomowo z prawami 600.
- `TOKEN_ENCRYPTION_KEY` ShipScope zostaje w `server/.env`. `npm run dev` zapisuje go tam sam (L1), a jeden
  właściciel klucza jest bezpieczniejszy niż dwa (odstępstwo od polecenia startowego, które chciało go w
  `~/.sdlc/env`).

## Pliki

- `src/pdi/stack/` z punktem wejścia `sdlc = "pdi.stack.cli:main"`, tylko biblioteka standardowa:
  - `__init__.py`;
  - `home.py` (ścieżki `~/.sdlc`, plik env, `config.toml`);
  - `services.py` (start, stop, health checki, pliki pid);
  - `cli.py` (argparse, polecenia, `Ctx` z podstawianym wykonawcą, HTTP, uruchamianiem procesów i katalogiem
    domowym).
- `tests/test_stack.py`.
- README (sekcja `sdlc`) i [plan `sdlc up`](plan-sdlc-lokalnie.md) §9.

## Testy (najpierw czerwone; bez prawdziwego Dockera, sieci i procesów)

- env: prawa 600 i 700, wygenerowane sekrety, istniejące wartości nienadpisane, zapis atomowy;
- brak narzędzi: polecenia instalacji i kod 1;
- konfiguracja: pytania tylko przy pierwszym uruchomieniu;
- kolejność startu i czekanie na health checki; drugie `up` niczego nie restartuje;
- połączenie: czekanie na przestrzeń (kod 3), zapis trzech zmiennych, restart odbiornika, `test`; kod 4 bez
  zmiennych → `--replace`;
- dokładne wywołania `gh api` dla `deploy prod` i `deploy test`, z danymi na stdin;
- wywołania `claude mcp`, bez wartości w argv; `sdlc mcp` uruchamia serwery ze zmiennymi z env;
- `status`: stany połączeń i ci_for_sdlc z plików;
- brak sekretu w argv, w logu `sdlc` i w wyjściu;
- `reset` bez wpisanej nazwy niczego nie usuwa; `down` nie usuwa wolumenu.

## Otwarte pytania

- `connected` dla ci_for_sdlc → pdi wymaga zmiany `CHG-n` w repo produktu, bo CLI wysyła tylko gotowość zmian.
  W pustym repo próbnym (przed L5) `status` pokazuje `configured`, nie `connected`. Pełny stan pojawi się po
  pierwszej zmianie.
- Port ShipScope jest brany z `server/.env` (`PORT`, domyślnie 3000); odbiornik zawsze na 8787.
