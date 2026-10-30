# Plan L4: `sdlc`, jedno polecenie dla całego stosu

Data: 2026-10-30 · Status: **zrobione** · Część [planu sdlc-lokalnie](plan-sdlc-lokalnie.md) (§2 Z3 i Z5, §4 L4),
decyzje DL2 (usługi jako procesy na localhost, w Dockerze tylko Postgres) i DL3 (`sdlc` w `pdi/stack/`).

## 1. Warunki wstępne (sprawdzone 2026-10-30)

| Krok | Sprawdzenie | Wynik |
|---|---|---|
| L1 | ShipScope `server/lib/safe-fetch.js` przepuszcza loopback przy `PUBLIC_BASE_URL` na localhost (`lib/local-mode.js`) | jest (ShipScope #125) |
| L2 | pdi zna `PDI_DISPATCH=local` i `PDI_DISPATCH_CHECKOUT` (`src/pdi/dispatch.py`, `dispatch_local.py`) | jest (pdi #59) |
| L3 | ci_for_sdlc `npm run analyze -- --repo … --send-to-pdi` (stan w `CI_DATA_DIR`: `pdi-state.json`, `pdi-outbox.json`) | jest (ci_for_sdlc #102) |

## 2. Polecenia

| Polecenie | Co robi |
|---|---|
| `sdlc up` | narzędzia → konfiguracja → `~/.sdlc/env` → Postgres → ShipScope (migracje, web, worker) → pdi-receiver → połączenie ShipScope ↔ pdi → MCP → adresy i „gotowe” |
| `sdlc status` | procesy (pid, adres), Postgres, ShipScope ↔ pdi, ci_for_sdlc → pdi, które sekrety są ustawione (tylko tak/nie), ostatnie linie logu odbiornika, otwarte pozycje skrzynki |
| `sdlc deploy <prod\|test> [--repo owner/name]` | `gh api` zakłada GitHub Deployment dla `HEAD` gałęzi `main` (środowisko `production` albo `test`) i status `success`; wypisuje id i sha |
| `sdlc open` | otwiera ShipScope i formularz zgłoszenia pdi (`/problems/new?t=…`) w przeglądarce; token formularza nie trafia do argv przeglądarki: `sdlc` zapisuje stronę z przekierowaniem (`meta refresh`) w `~/.sdlc/run/form.html` (tryb 600) i otwiera ten plik |
| `sdlc down` | zatrzymuje procesy i kontener Postgresa (`docker stop`); wolumen z danymi zostaje |
| `sdlc reset` | po wpisaniu z klawiatury nazwy `shipscope-dev-pg`: `down`, usunięcie kontenera i wolumenu, katalogów `~/.sdlc/ci-data`, `logs` i `run` oraz zmiennych `PDI_SHIPSCOPE_*` z env (połączenie znika razem z bazą); pozostałe sekrety i konfiguracja zostają |
| `sdlc check [--repo ścieżka]` | ci_for_sdlc na repo z `--send-to-pdi`: `npm run analyze` w klonie ci_for_sdlc z `PDI_EVENTS_URL`, `PDI_SIGNING_SECRET` i `CI_DATA_DIR` ze środowiska `sdlc` (nikt nie przepisuje sekretu); wyjście wypisuje, bez osobnego logu |
| `sdlc mcp <pdi\|shipscope>` | uruchamia serwer MCP ze zmiennymi z `~/.sdlc/env`; tak rejestruje go `sdlc up` |

Serwera ci_for_sdlc (`npm start`) `sdlc` nie uruchamia: przepływ z repo potrzebuje tylko CLI (`sdlc check`).

## 3. Pliki w `~/.sdlc`

| Plik | Zawartość |
|---|---|
| `config.toml` | ścieżki klonów pdi, ShipScope i ci_for_sdlc, rejestr decyzji (`PDI_REGISTRY_PATH`), opcjonalny klon produktu (`PDI_DISPATCH_CHECKOUT`); trzy pytania tylko przy pierwszym `up`: katalog z klonami (domyślnie katalog nad klonem pdi; ShipScope i ci_for_sdlc to `evdt-service-shipscope` i `ci_for_sdlc` w nim), rejestr (domyślnie `pdi-decisions` w tym katalogu), klon produktu (Enter = brak) |
| `env` | sekrety i zmienne (`KLUCZ=wartość`), tryb 600 w katalogu 700, zapis atomowy (plik tymczasowy w tym samym katalogu + `os.replace`); istniejących wartości `sdlc` nigdy nie nadpisuje |
| `logs/<usługa>.log` | wyjście procesów (`shipscope-web`, `shipscope-worker`, `pdi-receiver`) i nieudanych migracji (`shipscope-migrate`) |
| `run/<usługa>.pid` | pid procesu uruchomionego w tle |
| `ci-data/` | `CI_DATA_DIR` ci_for_sdlc dla `sdlc check` (stąd `status` czyta wysyłki do pdi) |

Generowane raz: `PDI_TF_SIGNING_SECRET`, `PDI_CI_FOR_SDLC_SIGNING_SECRET`, `PDI_FORM_TOKEN`, `TOKEN_ENCRYPTION_KEY`
(32 bajty w base64). Gdy ShipScope ma już klucz w `server/.env` (np. po `npm run dev`), `sdlc` przejmuje go do
`~/.sdlc/env`, żeby zapieczętowane dane dało się dalej odczytać. Stałe: `PDI_EVENTS_URL=http://127.0.0.1:8787`,
`PDI_DISPATCH=local`, `PDI_PHASE_BUDGET_USD=3` (rekomendacja DL5). Z połączenia: `PDI_SHIPSCOPE_URL`,
`PDI_SHIPSCOPE_TOKEN`, `PDI_SHIPSCOPE_SIGNING_SECRET`.

## 4. Kolejność `sdlc up`

1. **Narzędzia:** `docker` (i `docker info`: czy Docker działa), `gh` (i `gh auth status`), `claude`, `node`, `npm`,
   `uv`. Brak → po jednym poleceniu instalacji na narzędzie (`brew install …`, `gh auth login`), kod 1, zanim
   cokolwiek się zmieni.
2. **Konfiguracja i env** jak w §3.
3. **Postgres** (te same nazwy co ShipScope `npm run dev`, więc obie drogi dzielą jedną bazę): kontener
   `shipscope-dev-pg`, wolumen `shipscope-dev-pg`, `postgres:16-alpine`, port `127.0.0.1:54329`. Istnieje → `docker
   start`, nie istnieje → `docker run -d`. Zdrowie: `pg_isready` w kontenerze. Potem rola `shipscope_app` (bez
   superusera, przez RLS) i baza `shipscope` przez `psql` w kontenerze.
4. **Aplikacja GitHub ShipScope** (jednorazowo, przeglądarka): bez `GITHUB_APP_CLIENT_ID` i `…_SECRET`
   w `server/.env` `sdlc` prosi o jednorazowe `npm run dev` w `server/` ShipScope i kliknięcie „Create the GitHub App
   on GitHub” (przepływ manifestu zapisuje klucze w `server/.env`), czeka na Enter i czyta plik ponownie.
5. **ShipScope:** `npm ci` w `server/` ShipScope i w klonie ci_for_sdlc, gdy brak `node_modules`. Potem
   `node scripts/migrate.js` (błąd → wyjście w `logs/shipscope-migrate.log`, kod 1), potem `node web.js` i `node worker.js` w tle (cwd `server/`).
   Środowisko: `server/.env` + `DATABASE_URL` bazy z kroku 3, `DATABASE_SSL=false`,
   `PUBLIC_BASE_URL=http://localhost:3000`, `PORT=3000`, `TOKEN_ENCRYPTION_KEY` z `~/.sdlc/env`. Zdrowie:
   `GET /health` → 200.
6. **pdi-receiver:** `uv run --directory <pdi> pdi-receiver` w tle ze zmiennymi z `~/.sdlc/env` i
   `PDI_REGISTRY_PATH`. Zdrowie: odpowiedź HTTP na `127.0.0.1:8787` (odbiornik nie ma `/health`, dowolny kod
   oznacza, że słucha).
7. **Połączenie ShipScope ↔ pdi** (gdy w env brak `PDI_SHIPSCOPE_TOKEN`), patrz §5. Potem restart odbiornika.
8. **MCP:** dla `pdi` i `shipscope`: gdy `claude mcp get <nazwa>` pokazuje już właściwe polecenie, nic; inaczej
   `claude mcp remove --scope user <nazwa>`, potem `claude mcp add --scope user <nazwa> -- uv run --directory <pdi>
   sdlc mcp <nazwa>`.
9. Adresy usług i linia „gotowe”.

Drugie `up` uruchamia tylko to, co nie działa (żywy pid albo zajęty port = działa), i nic poza tym nie zmienia.
Każde czekanie na zdrowie ma limit czasu; po nim `sdlc` podaje ścieżkę logu i kończy z kodem 1.

## 5. Kroki tylko dla zalogowanego admina — i jak je ominąć bez zmiany ShipScope

API ShipScope za Connect (`POST /tenants/:id/pdi-connection`) i Track repository (`PUT
/tenants/:id/github/repos/:repoId`) wymaga sesji admina (`sid` z logowania przez GitHub OAuth). Tokenu do tych
tras nie ma. Dlatego:

- **Jednorazowo w przeglądarce** (`sdlc up` wypisuje kliknięcia raz i czeka na Enter):
  1. aplikacja GitHub (§4 krok 4),
  2. logowanie przez GitHub na `http://localhost:3000` i założenie przestrzeni.
- **Połączenie automatycznie, bez kopiowania:** `sdlc` uruchamia `node -e <skrypt>` w `server/` ShipScope.
  Skrypt używa bibliotek ShipScope (`lib/db`, `lib/config`, `lib/pdi-connection.connectPdi`), wybiera pierwszego
  admina pierwszej przestrzeni (zapytanie na koncie właściciela bazy, bo RLS) i wywołuje `connectPdi(…, {localMode:
  true})` — ten sam kod co przycisk Connect. Na stdout wypisuje trzy zmienne jako JSON; `sdlc` zapisuje je do
  `~/.sdlc/env` i niczego z nich nie wypisuje. Wszystkie dane wejściowe (adresy bazy, klucz) idą przez środowisko.
  - brak przestrzeni (kod 3) → kliknięcia z punktu 2 i ponowna próba po Enter,
  - przestrzeń już połączona (kod 4) → rozłącz w Settings → Integrations → pdi i uruchom `sdlc up` jeszcze raz
    (tokenu nie da się odczytać ponownie).
- **Track repository** zostaje w przeglądarce (wymaga instalacji aplikacji GitHub na repo); dotyczy L5.
- **Później (osobna zmiana w ShipScope):** skrypt `server/scripts/local-connect-pdi.js` w trybie lokalnym
  zamiast skryptu w `sdlc`, żeby `sdlc` nie zależał od wewnętrznych modułów ShipScope.

## 6. MCP w Claude Code

`claude mcp add --scope user` zapisuje rejestrację w `~/.claude.json`. Rejestrowane jest tylko polecenie `uv run
--directory <pdi> sdlc mcp <nazwa>`, bez wartości: sekrety zostają w `~/.sdlc/env`, a `sdlc mcp` wczytuje je przy
starcie i uruchamia `pdi-mcp` albo `node <ShipScope>/adapters/mcp/shipscope-mcp.js` (`SHIPSCOPE_URL`
i `SHIPSCOPE_TOKEN` z `PDI_SHIPSCOPE_URL` i `PDI_SHIPSCOPE_TOKEN`). Właściwy wpis zostaje bez zmian; inny jest
najpierw usuwany, więc rejestracja się nie dubluje.

## 7. Sekrety

- Nigdy w argv procesów potomnych (tylko w środowisku), w logach `sdlc` ani w jego wyjściu.
- `status` pokazuje tylko „ustawiony / brak”.
- Linia logu odbiornika zawiera tylko metodę, ścieżkę i kod (tak loguje `pdi-receiver`).
- Test: każdy argv, każda linia wyjścia i zawartość logów przeszukane pod kątem wygenerowanych wartości.

## 8. Testy (`tests/test_stack.py`, wstrzyknięty wykonawca, HTTP, start w tle i katalog domowy)

- env z trybem 600 (katalog 700), istniejące wartości nienadpisane, klucz w formacie base64 32 bajtów;
- brakujące narzędzia z poleceniami instalacji i kod 1;
- kolejność startu i czekanie na zdrowie (limit czasu → kod 1 z logiem), drugie `up` bez zmian;
- dokładne wywołania `gh api` dla `deploy prod` i `deploy test`;
- wywołania `claude mcp remove` i `add`;
- krok połączenia zapisuje trzy zmienne i restartuje odbiornik;
- brak sekretu w argv, wyjściu i logach;
- `reset` odmawia bez wpisanej nazwy; `down` nie usuwa wolumenu.

## 9. Pytania otwarte

- Skrypt połączenia zależy od wewnętrznych modułów ShipScope (`lib/pdi-connection.js`). Zmiana ich sygnatur zepsuje
  `sdlc up` — docelowo skrypt w ShipScope (§5).
- `sdlc` nie zatrzymuje `npm run dev`, jeśli ktoś go zostawił: zajęty port 3000 traktuje jak działający ShipScope.
- `SYNC_INTERVAL_MINUTES=1` (skrócenie czasu z §5 planu) dodaje L5.
