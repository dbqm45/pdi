# Plan Z3-lokalnie — konsola w przeglądarce na Macu (A7, DZ14 i DZ18) z konsolową częścią N19

Data planu: 2026-11-06 · Status: **plan; do realizacji** · Krok A7 z [planu zespołu
jednoosobowego](plan-zespol-jednoosobowy.md) (§0 wiersz A7, §5, §8.3 N19); decyzje
[DZ14 i DZ18](decyzje.md) · Stan wyjściowy: pdi `05cb642` (main, kontrakt 0.11.0), tf 5.58.7 (main)

**Cel.** W trybie lokalnym (`sdlc up`) każdy przebieg zmiany widać i prowadzi się w przeglądarce:
trzy pasy, ślad zmiany z krokami, panel „Pliki” i boczny panel postępu na żywo (z `run.progress`),
skrzynka decyzji z przyciskami. Bez usługi na produkcji (to Z3 po DA4), bez rozmowy
i powiadomień (zostaje w Z3). Dowód problemu: dziś przebieg śledzi się przez logi fazy
i `get_change` z MCP — PR cięcia, budżet i odmowy widać dopiero po końcu fazy ([A6,
plan §0](plan-zespol-jednoosobowy.md#0-kolejność-całości)).

## 1. Co już jest (sprawdzone w kodzie i dokumentacji 2026-11-06)

| Element | Gdzie | Stan |
|---|---|---|
| Kontrakt `run.progress` | `contract/event.schema.json` (`$defs/run_progress`, kontrakt 0.11.0): `phase` i `status` wymagane; `change`, `task`, `slice`, `cost_usd`, `budget_usd`, `message`, `url` opcjonalne; `status` ∈ `started`, `in_progress`, `waiting_gate`, `done`, `failed` | jest; nikt tego dzisiaj nie wysyła |
| Faza przez `claude --print --output-format json` | tf `modes/mode-pdi/skills/pdi-decisions/scripts/phase_run.py` (`cmd_run`): wynik dopiero na końcu, `result = json.loads(r.stdout)`, zachowuje `detail`, `permission_denials`, `total_cost_usd` (PRB-28, tf #145) | jest |
| Log fazy pisany na bieżąco | pdi `src/pdi/dispatch_local.py` (`_stream_run` już podaje `on_line` do logu linia po linii) | jest; nic nie oddziela postępu od reszty logu |
| Faza w kontenerze (Z8a) | pdi `src/pdi/phase_sandbox.py`: kontener widzi **tylko klon repo produktu**, bez `runs/` | jest |
| Wynik persony `_persona_report` | pdi `src/pdi/dispatch_local.py` (ostatni obiekt JSON w wyjściu kroku `run`: `status`, `cost_usd`, `detail`, `permission_denials`) | jest; MUSI pozostać dokładnie taki sam |
| Decyzja z pytaniami (Z1) | pdi `src/pdi/inbox.py` (`decide(…)`: `answers` sprawdzane przez `_checked_answers` przeciw `item["questions"]`); MCP `decide_inbox_item(answers=…)` | jest; przyciski w konsoli idą **tą samą** ścieżką |
| Sprawdzenie PR przed `approved` (PRB-2) | pdi `src/pdi/inbox.py` (`_check_pr` przez `pr_state_mod`) | jest; konsola z tego korzysta |
| Pasy („Z7a”) i mock-upy | `design/konsola/v2-klikalna/{Main,Slad,Decyzje,Autonomia}.html`; mapowanie faz → pas w [planie §8.1](plan-zespol-jednoosobowy.md#81-z7--układ-z-cyklu-aplikacji-ai) | makieta; pasów nie ma jeszcze w kontrakcie — plan Z7a dokłada je równolegle; konsola trzyma mapowanie po stronie kodu |
| `sdlc up/down/status/open` | pdi `src/pdi/stack/cli.py` (`cmd_up`, `cmd_down`, `cmd_status`, `cmd_open`); `~/.sdlc/env` generuje tokeny (`PDI_FORM_TOKEN`), łącznie ze `pdi-receiver` jako odłączonym procesem | jest |
| Formularz zgłoszeń (odczyt + CSP) | pdi `src/pdi/form.py` + `src/pdi/receiver.py` (CSP `default-src 'none'; style-src 'unsafe-inline'; form-action 'self'`, `X-Frame-Options: DENY`, token w URL, token sprawdzany `hmac.compare_digest`) | jest; konsola idzie dokładnie tym samym wzorem |
| `claude --print --output-format stream-json` (do sprawdzenia dziś) | **sprawdzone 2026-11-06 w [Claude Code CLI reference](https://code.claude.com/docs/en/cli-reference) i [Headless](https://code.claude.com/docs/en/headless)**: `stream-json` wymaga `--print` **i `--verbose`**; NDJSON na stdout bez preambuły; typy `system`, `assistant`, `user`, `result`, opcjonalnie `stream_event` (z `--include-partial-messages`) i `hook_started|progress|response` (z `--include-hook-events`); końcowy `result` ma `subtype`, `is_error`, `result: {type, text?}`, `total_cost_usd`, `usage`, `duration_ms`, `duration_api_ms`, `num_turns`, `permission_denials[]`, `session_id` ([typescript types](https://code.claude.com/docs/en/agent-sdk/typescript)); odmowy uprawnień w trakcie — `system` z `subtype: permission_denied`, w końcowym — `result.permission_denials[]` ([Turn off permission prompts](https://code.claude.com/docs/en/headless)); `--max-budget-usd` i `--max-turns` dalej działają ([CLI reference](https://code.claude.com/docs/en/cli-reference)); `total_cost_usd` jest szacunkiem po stronie klienta ([cost-tracking](https://code.claude.com/docs/en/agent-sdk/cost-tracking)) | używamy; „waiting for a gate” nie jest w stream ani w rezultacie — stan derywowany po stronie `phase_run.py` (jak dziś: `gate` z PHASES, status `waiting_gate` po udanym stream-je) |

Brakuje, co ten krok dokłada:

- **a.** `phase_run.py run` wciąż wywołuje `--output-format json` — faza widać dopiero na końcu. (Nie ma linii `run.progress` do konsoli.)
- **b.** `dispatch_local` nie rozdziela ewentualnych linii postępu od reszty logu, bo postępu nie ma.
- **c.** `pdi.changes.settle()` i `get_change` nie pokazują bieżącej czynności — tylko wynik po przebiegu.
- **d.** Brak lokalnej konsoli (`sdlc up` uruchamia stos, nie stronę).
- **e.** Panel „Pliki” w śladzie zmiany: artefakty i diff cięcia z klonu produktu — brak.
- **f.** `questions` pozycji skrzynki są dziś **tylko stringami** (`contract/event.schema.json`: `questions` ∈ `payload.gate_requested` to `array of string`, kontrakt 0.11.0) — konsola musi obsłużyć strukturę opcji (N19), gdy Z2a ją doda, i zostać do tego czasu **gotowa na dołączenie opcji bez zmiany struktury strony** (sprawdzone 2026-11-06, Z2a nie jest zmergowane).

## 2. Rozwiązanie

### 2.1. tf — stream-json i `PDI-PROGRESS` prefix (bez zmiany kontraktu wyniku kroku `run`)

Krok `run` w `phase_run.py` zaczyna używać `claude --print --output-format stream-json --verbose`
i konwertuje linie stream-JSON na **linie postępu** z ustalonym prefiksem, obok normalnego
wyjścia. Końcowy, jedyny obiekt JSON wyniku kroku (ten, który czyta `_persona_report` w pdi)
pozostaje dokładnie taki sam co dziś (`status`, `cost_usd`, `detail`, `permission_denials`,
`repeated_question`, …) — żadnej zmiany w kształcie i kolejności pól.

| Plik | Zmiana |
|---|---|
| `modes/mode-pdi/skills/pdi-decisions/scripts/phase_run.py` | `cmd_run` ustawia `argv = [claude, "--print", "--verbose", "--output-format", "stream-json", "--agent", persona, "--permission-mode", "acceptEdits", …]`. Wynik `claude` strumieniuje się z `Popen(stdout=PIPE, bufsize=1, text=True)`; linie są parsowane z JSON. Nowy moduł `phase_progress.py` obok (w `scripts/`): `events_to_progress(events_iterator, *, phase, change, budget_usd) → iterator[dict]`; każdy emitowany słownik to linia postępu z polami `phase`, `status`, opcjonalnie `change`, `cost_usd`, `budget_usd`, `message`, `url`, a dodatkowo lokalne pola pomocnicze (`event`: `start`, `tool_use`, `tool_result`, `assistant_text`, `permission_denied`, `result`). Każda linia postępu wypisana na stdout **z prefiksem** `PDI-PROGRESS: `. Końcowy `result` event stream-JSON jest w tej samej funkcji zapamiętany i zwrócony (dict), a `cmd_run` buduje z niego dotychczasowy obiekt wyniku kroku (`status`, `cost_usd`, `detail`, `permission_denials`, `repeated_question`) **dokładnie jak dziś**. Wymagane flagi i kształt `result` sprawdzone w [Claude Code CLI reference](https://code.claude.com/docs/en/cli-reference) i [agent-sdk/typescript](https://code.claude.com/docs/en/agent-sdk/typescript) 2026-11-06. `_persona_report` pdi parsuje ostatni obiekt JSON wyjścia — zasada „linie postępu nigdy nie zaczynają się od `{`, tylko od `PDI-PROGRESS: {`” gwarantuje, że żadna linia postępu nie zostanie wzięta za wynik persony. |
| `modes/mode-pdi/skills/pdi-decisions/scripts/phase_progress.py` (nowy, mały) | Zamiana zdarzeń stream-JSON na linie postępu. Zdarzenie → linia (najkrócej jak się da): `system` z `subtype: init` → `{status: started, message: "persona <name> startuje"}` z `cost_usd: 0`; `assistant` z `tool_use` (`name, input`) → `{status: in_progress, message: <PLAIN>}` z `cost_usd` wyliczonym narastająco (o ile `usage` + tabela cen jest w evencie; inaczej bez `cost_usd` do końca — `result` da dokładną wartość); `user` z `tool_result` → opcjonalnie `{status: in_progress, message: "wynik narzędzia <name>"}` (bez treści wyniku); `system` z `subtype: permission_denied` → `{status: in_progress, message: "odmowa: <tool_name> <reason skrócony do 80 znaków>"}`; `result` → `{status: done | failed, cost_usd: <total_cost_usd>, message: <subtype>}`; po `result` jeszcze linia `{status: waiting_gate}` emituje `cmd_run`, gdy faza nie jest delivery i nie ma `failed`. **Mapowanie wiadomości**: `Read` → „czyta <ścieżka z `file_path`>”, `Edit`/`Write` → „pisze <ścieżka>”, `Grep` → „szuka wzorca w <ścieżka>” (bez wzorca), `Bash` → „uruchamia polecenie” (pierwsze słowo + „…” jeśli były argumenty), `WebFetch`/`WebSearch` → „pobiera dane” (bez URL i zapytania), `Task` → „uruchamia agenta <subagent_type>”, MCP (`mcp__<server>__<tool>`) → „używa narzędzia <server>/<tool>”. Każda wiadomość jest przycinana do 200 znaków i oczyszczona z `\n`, `\r`, znaków sterujących. **Zakazane**: wrzucanie `input` tool_use do wiadomości (żadnej treści plików, poleceń, promptów, decyzji, sekretów); dla ścieżki plików tylko względna ścieżka (gdy kiedyś by pokazywała bezwzględną, ucinamy do części po `CHANGES/`). Linia postępu jest walidowana po stronie tf przez miniaturowy checker (`phase` niepusty, `status` ∈ `{started, in_progress, waiting_gate, done, failed}`, reszta pól opcjonalna i o właściwym typie), inaczej **nie** wypisujemy jej (żeby nie hałasować w logu). |
| `modes/mode-pdi/skills/pdi-decisions/tests/test_phase_run.py` | Nowe testy: sample streamy (sukces, waiting_gate, failed, `repeated_question`, stream z `permission_denied`) z `events_to_progress(…)` → oczekiwana lista linii postępu; `cmd_run` ze sfejkowanym `subprocess` wypuszczającym NDJSON na stdout wypisuje linie `PDI-PROGRESS: …` i kończy identycznym wynikiem jak dziś (ten sam obiekt JSON na końcu stdout) — porównane z dzisiejszym wynikiem na tych samych danych. |

**Co zostaje bez zmian:** struktura stdout kroku `run` poza nowymi liniami postępu (końcowy obiekt wyniku bajt w bajt taki sam co dziś), kod wyjścia 0 (OK) / 1 (błąd), `--max-budget-usd` w argv, `--settings $PDI_CLAUDE_SETTINGS` w argv, `--permission-mode acceptEdits`, agent persony. `sdlc-phase.yml` działa dalej: linie postępu idą do logu joba w czytelnej formie (prefiks + JSON), wynik persony czyta pdi albo workflow bez żadnej zmiany. Kontrakt pdi **nie zmienia wersji** w tym kroku: `run.progress` już istnieje.

### 2.2. pdi — rozdzielenie postępu od logu i uwidocznienie ostatniej linii

| Plik | Zmiana |
|---|---|
| `src/pdi/dispatch_local.py` | `_stream_run` zostaje. Nowa funkcja w tym samym module `run_progress_sink(log_path: Path) → tuple[write_log, on_progress_line_path]`: zwraca parę zamkniętą na `log_path`. `on_line` kroku `run` (i tylko tego) idzie przez wrapper: linie z prefiksem `PDI-PROGRESS: ` → `<log>.progress.jsonl` (po walidacji); reszta linii → dotychczasowy `log(line)`. Walidacja progresu: miniaturowy checker (`status` ∈ enum, typy pól) **oraz** walidacja run_progress z `pdi.contract` (jedno wywołanie, bez wysyłki na receiver). Nieznane linie pomija. `execute` wywołuje `step("run", …, extra=…)` tak samo, ale dla fazy `run` używa nowego wrappera `on_line`. Dodatkowo `_write_result` przy failed keep `persona` jak dziś. |
| `src/pdi/dispatch_local.py` | `settle(state)`: po doklejeniu pól z `result.json` jak dziś dokłada `last_progress` — ostatnia poprawna linia z `<log>.progress.jsonl` jako słownik (bez `PDI-PROGRESS: ` prefiksu). `last_progress` idzie do `state["dispatch"]` tylko jeśli plik istnieje i ma co najmniej jedną poprawną linię. |
| `src/pdi/changes.py` | Zostaje; `ChangeStore.get` wywołuje `dispatch_local.settle(data)` — `last_progress` trafia do `get_change` automatycznie. |
| `src/pdi/dispatch_local.py` | `running(runs_dir, change)` zwraca `(log_path, progress_path)` **zaplecze** dla konsoli: używamy nowej funkcji `progress_path(log) = log.with_name(log.stem + '.progress.jsonl')` (symetrycznie do `result_path`). Konsola tego używa do SSE z pliku. |
| `tests/test_dispatch_local.py` | Nowe testy: sample linii `PDI-PROGRESS: {...}` w strumieniu kroku `run` → nie wchodzą do logu, wchodzą do `.progress.jsonl` po walidacji; linie ze złym kształtem pomijane; linie z innym statusem pomijane; `settle` dokłada `last_progress`; `get_change` zwraca `dispatch.last_progress`. |

**Co zostaje bez zmian:** zapis logu fazy, końcowy `result.json`, `_persona_report`, `_publish_cuts`, `_cut_pr_text`, kolejność kroków, treść zgłoszenia poza logiem. Linie postępu nigdy nie zawierają promptów, decyzji, treści plików ani sekretów (gwarant po stronie tf i dodatkowe sprawdzenie w walidacji).

### 2.3. pdi — konsola w przeglądarce (`pdi-console`, stdlib)

Nowy moduł `src/pdi/console.py` — osobny proces `pdi-console` (jak `pdi-receiver`), biblioteka
standardowa (`http.server`, `urllib`, `threading`), związany z `127.0.0.1:8788` (domyślnie;
zmienna `PDI_CONSOLE_PORT`, `PDI_CONSOLE_HOST=127.0.0.1` hardcode z pola `listen` w kodzie —
nie przyjmujemy wartości z zewnątrz). Token sesji w URL (`?t=<token>`), analogicznie jak
`PDI_FORM_TOKEN` w `receiver.py`. Token stały w obrębie startu (w `~/.sdlc/env` jako
`PDI_CONSOLE_TOKEN`, generowany raz w `home.ensure_env`). CSP i inne reguły bezpieczeństwa
jak w `form.py` (`default-src 'none'`), **bez skryptów inline**: jedyny JS to statyczny plik
`/static/console.js` serwowany z pamięci (albo `pdi/static/console.js`), ze zdefiniowanym
nonce w CSP. Tam SSE i prosty router między stronami.

| Plik | Zmiana |
|---|---|
| `src/pdi/console.py` (nowy) | `make_server(inbox, changes, registry, *, token, host, port, runs_dir, checkout)` zwraca `HTTPServer` z `ThreadingHTTPServer` (wiele połączeń SSE jednocześnie, max 16 wątków, inaczej 503). Endpointy (każdy sprawdza `?t=<token>` przez `hmac.compare_digest`; bez tokenu — 404 jak w `receiver.py`, nie 401, żeby nie zdradzać, że strona istnieje): **GET `/`** → redirect `/board?t=`; **GET `/board?t=`** HTML z trzema pasami (karty zmian z `list_changes`); **GET `/trace/<CHG>?t=`** HTML z krokami, decyzjami, PR-ami, wydaniami (dane z `pdi.trace.trace(registry, change, live=False)`) plus sekcja `files` i boczny panel postępu; **GET `/trace/<CHG>/file?path=…&t=`** zawartość pliku artefaktu z klonu (tylko z białej listy: `docs/project/changes/<CHG>/{intent,requirements,plan,design}.md` i `release.yaml`), 404 inaczej; **GET `/trace/<CHG>/diff?t=`** `git diff` cięcia (`git diff <base> <head>`, gdzie `base` i `head` wyciąga z `state["dispatch"]["cuts"]` i `state["dispatch"]["ref"]`) — tekst; **GET `/inbox?t=`** HTML lista pozycji bramek, oceny skutku, triażu, autonomii (z polem na odpowiedź do każdego pytania i przyciskami approve / changes_requested / rejected); **POST `/inbox/<ID>/decide?t=`** `application/x-www-form-urlencoded` (jak `form.py`), parsuje `outcome`, `statement`, `why`, `answer_<i>` (jedno pole lub wybór opcji), `loaded_at` (znacznik wczytania strony, patrz niżej) i zapisuje przez **ten sam** `Inbox.decide(item_id, draft, outcome=…)` co MCP — źródło `{"kind": "console", "url": "http://127.0.0.1:…/inbox/<ID>?t=…"}`, `drafted_by: "human"`, `draft_edited: False`; przy zmianie stanu pozycji od `loaded_at` (czytamy `item["received_at"]` lub `item.get("decided_at")`) → odmowa 409 z komunikatem „pozycja zmieniła się od czasu wczytania strony, odśwież i spróbuj ponownie”; przy niezgodności PR-a — ta sama odmowa co w MCP (`_check_pr`, PRB-2); **GET `/decisions?t=`** HTML lista decyzji (`registry.decisions()`), filtr po kind; **GET `/autonomy?t=`** HTML raport (`pdi.autonomy`); **GET `/sse/progress?change=<CHG>&t=`** Server-Sent Events: strumień linii `<log>.progress.jsonl` przy użyciu polli (`sleep 0.5 s`) i `tail -F` w kodzie (plik otwarty do odczytu, `seek(0, 2)`, wait for growth, polling stat); **GET `/sse/board?t=`** SSE agregat (nowe zmiany, zmiana `dispatch.status`, nowe pozycje skrzynki) z polli `changes.all()` i `inbox.items()` co 2 s. Każda strona ma w nagłówku **CSP** `default-src 'none'; style-src 'self' 'unsafe-inline'; script-src 'self' 'nonce-<nonce>'; connect-src 'self'; img-src 'self' data:; form-action 'self'; base-uri 'none'`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `X-Content-Type-Options: nosniff`. Wszystkie wartości w HTML escapowane przez `html.escape` (teksty decyzji, pytania, logi, ścieżki, nazwy gałęzi). |
| `src/pdi/console.py` — model odczytu | Mapowanie faza → pas (lane 1/2/3) w stałej `LANES` w kodzie (łatwe do zmiany, gdy Z7a doda `stage` do kontraktu). Trzy pasy: lane 1 Zaprojektuj i zbuduj = {intake, intent, requirements, architecture, design, approve-for-implementation, delivery}; lane 2 Oceń i wydaj = {B4}; lane 3 Wdróż, obserwuj, ulepszaj = {B5, B6, R1, impact_review}. Szczegóły w §3. |
| `src/pdi/console.py` — pytania z opcjami (N19) | Przy renderowaniu pozycji skrzynki `kind: gate`: jeśli `questions` jest listą stringów → pole tekstowe z `name="answer_<i>"` dla każdego pytania (dzisiejszy stan, kontrakt 0.11.0). Jeśli element `questions[i]` jest `dict` z polami zgodnymi z Z2a (`question`, `options: [{value, label}]`, `recommended?`, `other?: bool`) → zestaw `<input type="radio" name="answer_<i>" value="<value>">` z `<label>…</label>`; `recommended` otrzymuje `checked` (można zmienić); `other: true` dokłada `<input type="radio" value="__other__">` i pokazuje pole tekstowe `name="answer_<i>_other"` (JS pokazuje je po wyborze „inne” — bez JS ten input jest widoczny od razu, szukamy wartości `__other__` w POST). Serwer wybiera `answer`: wartość `label` wybranej opcji (deterministyczna, bez JS po stronie klienta); wartość `__other__` wymaga niepustego pola `_other`, inaczej błąd walidacji; nieznana wartość → 400. Bez struktury opcji na pytanie (dzisiaj) zachowujemy się zgodnie z kontraktem 0.11.0 i oddajemy odpowiedź tekstową. Konsola nie wymusza Z2a; po jego merge'u wystarczy zmiana modelu odczytu, strona ma już tę gałąź. |
| `src/pdi/console.py` — panel „Pliki” (DZ18) | Lista plików z białej listy w klonie produktu (`checkout`): `intent.md`, `requirements.md`, `plan.md`, `design.md`, `release.yaml` pod `docs/project/changes/<CHG>/`. Każdy plik: GET `/trace/<CHG>/file?path=…` zwraca `text/plain; charset=utf-8` o ile: ścieżka to dokładnie jedna z białej listy (porównanie po `Path(checkout) / "docs/project/changes" / CHG / NAME`), plik istnieje, **nie jest symlinkiem** (`os.path.islink` na realizowanej ścieżce i wszystkich przodkach aż do `checkout`), `resolve()` zwraca ścieżkę **wewnątrz** `checkout` (porównanie przez `Path.is_relative_to`), **rozmiar ≤ 256 KiB**, `.gitignore` / `.env` / plik z `KEY` / `TOKEN` / `SECRET` w nazwie → 403 z komunikatem (brak wycieku treści). Diff cięcia: `/trace/<CHG>/diff?t=` uruchamia `git -C <checkout> diff <base>..<head>` dla bieżącego `dispatch.cuts` (po jednym cięciu na kart; `base` to `ref` fazy, `head` to `branch` cięcia); `git` uruchamiane bez powłoki, lista argumentów, `cwd=checkout`, timeout 5 s, output strony cięty do 1 MiB. SSE odświeża panel „Pliki” co 2 s po mtime plików z białej listy; po zmianie wysyła `event: file-changed` z nazwą. |
| `src/pdi/console.py` — ochrona przed zmianą pod decyzją | Strona `GET /inbox/<ID>` wkłada w ukryte pole `loaded_at` ISO ze stanu pozycji (najświeższy ze `received_at`, mtime `log`, mtime `last_progress`; nagłówek strony ma datę w widoku). `POST /inbox/<ID>/decide`: wczytuje pozycję ponownie i porównuje z `loaded_at`; przy dowolnej zmianie odmawia 409 z komunikatem i linkiem do odświeżenia. |
| `src/pdi/stack/home.py` | `GENERATED` dostaje nowy klucz `PDI_CONSOLE_TOKEN`; `DEFAULTS` dostaje `PDI_CONSOLE_PORT=8788`. `SECRET_KEYS` dostaje `PDI_CONSOLE_TOKEN` (pokazywany jako „ustawiony” / „brak” w `sdlc status`). |
| `src/pdi/stack/cli.py` | `cmd_up` uruchamia `pdi-console` (odłączony proces, jak `pdi-receiver`, pid w `~/.sdlc/run/pdi-console.pid`, log w `~/.sdlc/logs/pdi-console.log`). `cmd_status` dokleja linię `pdi-console: działa/nie działa — http://127.0.0.1:8788/`. `cmd_down` zatrzymuje `pdi-console`. `cmd_open` otwiera `/board?t=<token>` konsoli zamiast samego formularza (formularz dostępny z konsoli nawigacją). Konfiguracja konsoli dostaje `PDI_REGISTRY_PATH`, `PDI_CONSOLE_PORT`, `PDI_CONSOLE_TOKEN`, `PDI_DISPATCH_CHECKOUT`, `PDI_DISPATCH_RUNS` (nowa zmienna — katalog runs; w planie L2 to `PDI_REGISTRY_PATH/../runs` albo blisko logu, dziś `tmp` w workspace `sdlc up`; zobacz §2.6). Rejestracja wejścia konsoli w `pyproject.toml` jako `pdi-console = "pdi.console:main"`. |
| `src/pdi/console.py` — główna funkcja | `main()` czyta zmienne (`PDI_REGISTRY_PATH`, `PDI_CONSOLE_PORT`, `PDI_CONSOLE_TOKEN`, `PDI_DISPATCH_CHECKOUT`, `PDI_DISPATCH_RUNS`); bez tokenu — `SystemExit` z komunikatem; buduje `Registry`, `Inbox` (bez `dispatch`/`notify`, tylko odczyt plus zapis do skrzynki), uruchamia `make_server(…)` na `127.0.0.1:<port>`; wyświetla adres na stderr (`console: nasłuchuje na http://127.0.0.1:<port>/`). |
| `pyproject.toml` | Nowy wpis `pdi-console = "pdi.console:main"` w `[project.scripts]`. |
| `tests/test_console.py` (nowy) | Test strony `/board?t=` (lista zmian po pasach, escapowanie), `/inbox?t=` (lista bramek, pytania jako pola, radio dla pytań z opcjami gdy symulujemy kształt N19), `/inbox/<ID>/decide` (POST kieruje przez `Inbox.decide`; odmowa bez tokenu — 404; odmowa dla pozycji „stale”; odmowa dla niezmergowanego PR-a; odpowiedzi z opcji → `answers` w decyzji), `/trace/<CHG>` (zwraca artefakty i diff z klonu testowego; symlink odrzucony; plik poza klonem odrzucony; `.env` odrzucony; binarny plik odrzucony; rozmiar > 256 KiB odrzucony), SSE `/sse/progress?change=` (strumień linii po przyroście pliku), CSP i escaping (treść pytania z `<script>` nie trafia do strony jako znacznik). |
| `tests/test_stack.py` | Rozszerzyć o uruchomienie i zatrzymanie `pdi-console` razem ze ShipScope i `pdi-receiver` (wzorzec już jest), o linię w `sdlc status` i o URL w `sdlc open`. |

**Bezpieczeństwo (podsumowanie):**

- Nasłuch tylko na `127.0.0.1` (`host = "127.0.0.1"` hardcode z pola `listen` w kodzie; zmiana wartości wymaga zmiany kodu — nie przyjmujemy z env ani z CLI).
- Każde żądanie bez tokenu → 404; token w URL porównywany `hmac.compare_digest`; **nie** logujemy tokenu w access logu (`log_message` usuwa `?t=…` z wpisu).
- CSP bez `script-src 'unsafe-inline'`; `script-src 'self' 'nonce-<los>'` dla jednego pliku statycznego. Jedyne style inline mają ten sam nonce albo są w `<style>` bez `script-src 'unsafe-eval'`.
- POST tylko `application/x-www-form-urlencoded`, pole `t` **musi** być w treści (dodatkowo do URL; same-origin check); `Origin` i `Referer` sprawdzane: `http://127.0.0.1:<port>`.
- Żadne pole decyzji, pytania, odpowiedzi ani logów nie trafia na stronę nieoczyszczone. Treści z zewnątrz (`tool_use`, URL-e PR, nazwy gałęzi) idą przez `html.escape` i są obcinane; HTML z `plan.md` renderowany jako `<pre>` z zawartością escapowaną.
- Sekrety (`PDI_CONSOLE_TOKEN`, token GitHub, tokeny ShipScope, token Claude) nigdy nie trafiają na stronę, do SSE, do logu konsoli ani do linii postępu — żaden endpoint ich nie pokazuje; `log_message` czyści `?t=…`.
- Plik artefaktu: tylko tekst (`text/plain`), tylko biała lista, bez symlinków, do 256 KiB; plik z nazwą wyglądającą na sekretową (`^\.env`, zawierający `KEY`, `TOKEN`, `SECRET`, `_RSA`, `_ED25519`) odrzucony z 403; binarne wykrywamy po `b"\0"` w pierwszych 8 KiB.
- `git diff` robimy przez `subprocess.run(["git", "-C", str(checkout), "diff", f"{base}...{head}"], …)` z `timeout`, bez powłoki, wynik tnięty do 1 MiB i escapowany w `<pre>`.

### 2.4. Postęp fazy live — jak to współgra z Z8a (phase_sandbox)

Krok `run` idzie w kontenerze (Z8a) — i to on wypisuje linie postępu na swoim stdout. Kontener
**nie widzi** `runs/` hosta, więc nie może pisać do pliku `.progress.jsonl` wprost (dobrze, bo
to zakres hosta). pdi po stronie hosta łapie linie z `on_line` wrappera `_stream_run` (patrz
§2.2) i zapisuje do pliku `.progress.jsonl` obok logu. Nic nie trzeba zmieniać w montowaniach
(`phase_sandbox.py`). W Actions (`sdlc-phase.yml`) stdout persony idzie do logu joba —
linie postępu tam po prostu wylądują jako czytelne linie (prefiks + JSON). Kontrakt pdi i
odbiornik nie są zaangażowane: `run.progress` wysyłamy do odbiornika dopiero, gdy Z3 na
produkcji tego zachce (DZ14: usługa po DA4, poza tym krokiem).

### 2.5. Co zostaje na Z3 (po DA4)

- `run.progress` **wysyłane** z fazy do odbiornika pdi i stamtąd dalej do konsoli przez SSE
  (teraz czytamy plik `.progress.jsonl` wprost — `sdlc up` i konsola są na tym samym Macu).
- Usługa pdi, rozmowa w konsoli, wywiad (Z2b), sygnał „czeka na Ciebie” (powiadomienia),
  pełne dane OpenTelemetry (Z10c) — ten krok zostawia miejsce w panelu bocznym, dane dokłada
  Z10c.
- Konsola **bez** panelu decyzji wyjścia („Deploy”) i bez nowych bramek z Z2a — dopiero po
  nich i po DA4.

### 2.6. Katalog `runs/` — ścieżka hosta

`pdi.dispatch_local` używa `runs_dir` podawanego przez wywołującego (MCP, testy). Konsola
musi wiedzieć, z którego katalogu czytać. Dziś `sdlc up` nie generuje ścieżki `runs/`
— ustalam ją w `pdi.stack.home` jako `root / "runs"` (`~/.sdlc/runs/`). `cmd_up` ustawia
`PDI_DISPATCH_RUNS=~/.sdlc/runs` w środowisku `pdi-console` i (dla symetrii) w zmiennych
MCP pdi. `Registry.from_env()` już bierze `PDI_REGISTRY_PATH`; dla `runs_dir` w MCP
dopisze się fallback `~/.sdlc/runs` jeśli zmienna jest pusta (zmiana mała w `mcp_server.py`,
dziś `dispatch_local` dostaje runs_dir z wywołania `start` — tu bez zmian).

## 3. Mapowanie faza → pas (A7, Z7a)

Konsola trzyma ten układ (3 pasy z makiety v2-klikalnej, [plan §0 wiersz A7 i §8.1](plan-zespol-jednoosobowy.md#81-z7--układ-z-cyklu-aplikacji-ai)); `stage` w kontrakcie Z7a dołoży później:

| Pas | Kroki (fazy tf i bramki pdi) |
|---|---|
| **1. Zaprojektuj i zbuduj** | przyjęcie zgłoszenia (triage) · intent · requirements · architecture · design · approve-for-implementation · delivery |
| **2. Oceń i wydaj** | B4 (review i cele zmiany) · B5 (autoryzacja PROD) |
| **3. Wdróż, obserwuj, ulepszaj** | B6 (etapy flag) · wydanie R1 · ocena skutku (impact_review) · pętla do pasa 1 (`not_met` albo wybicie metryki) |

Na tablicy każda zmiana ma kartę w kolumnie **bieżącej** fazy w swoim pasie. „Waiting
for you” (pozycja skrzynki `kind: gate` / `impact_review` / `problem` / `autonomy` /
`capture` w stanie `open`) podświetla kartę. Trwająca faza pokazuje mały pasek z
`dispatch.last_progress.message` i `cost_usd`; po kliknięciu — ślad zmiany
(`/trace/<CHG>?t=`).

## 4. Testy (TDD)

Każdy test pisany **przed** zmianą kodu; każdy ma jedną konkretną obserwację. Lista nie jest
zamknięta — w trakcie realizacji dojdą te, które wyjdą z nieoczywistych przypadków.

### 4.1. tf (`modes/mode-pdi/tests/test_phase_run.py` i `test_phase_progress.py` nowy)

- `events_to_progress_from_success_stream` — recorded sample NDJSON z `system init`, kilkoma
  `assistant` z `tool_use` (Read, Edit, Bash), `user` z `tool_result`, `result` z
  `is_error:false` → oczekiwana sekwencja linii postępu: `started` (na `init`), kilka
  `in_progress` z wiadomościami w mapowaniu (patrz §2.1), `done` z `cost_usd` równym
  `total_cost_usd`.
- `events_to_progress_from_waiting_gate_stream` — stream kończy się `result` z `is_error:false`
  i faza nie jest delivery → ostatnia linia postępu `status: waiting_gate` (po `done` z
  `result` emitujemy drugą linię), `message` = nazwa bramki (`B2`, …).
- `events_to_progress_from_failed_stream` — `result.is_error=true` z `subtype:"error_max_turns"`
  → ostatnia linia `status: failed` z `message` = `subtype`.
- `events_to_progress_from_repeated_question` — stream kończy się `result` ok, ale artefakt
  po fazie powtarza rozstrzygnięte pytanie (wejście dla testu jak dziś przez `repeated(…)`)
  → `cmd_run` wypisuje linię postępu `failed` z `message: "repeated_question"` **po** tej
  z `done`, kod wyjścia 1, końcowy obiekt JSON wyniku ma `error: "repeated_question"` jak
  dziś.
- `events_to_progress_from_permission_denied` — stream ma `system` z `subtype: permission_denied`
  → linia postępu `in_progress` z `message: "odmowa: …"` (bez wrzucania treści wywołania
  narzędzia); końcowy `result.permission_denials` dochodzi do wyniku jak dziś.
- `events_to_progress_sanitizes_message` — tool_use z `input.command = "rm -rf /tmp/..." + \nsekret`
  nie trafia w całości do wiadomości; `Bash` daje tylko „uruchamia polecenie”; `\n` i znaki
  sterujące obcięte; długość ≤ 200.
- `events_to_progress_drops_bad_lines` — linie, które nie są JSON-em, albo mają zły kształt
  (brak `status`), są pomijane bez błędu.
- `cmd_run_streams_events_and_keeps_the_final_json_result` — `subprocess` (podstawiony)
  wypluwa NDJSON; `cmd_run` wypisuje na stdout w kolejności: `PDI-PROGRESS: {…}` kilka razy,
  potem **jeden** końcowy obiekt JSON wyniku **identyczny** z dzisiejszym (deep equal na
  zestawie sample streamów).
- `cmd_run_uses_stream_json_and_verbose_flags` — argv kroku `run` zawiera `--output-format
  stream-json --verbose --print` w tej kolejności, obok dotychczasowych flag.

### 4.2. pdi (`tests/test_dispatch_local.py`)

- `progress_lines_from_run_go_to_progress_file_not_log` — kiedy `run` wypisuje linie
  `PDI-PROGRESS: {…}` wymieszane z logiem (podstawiony `_stream_run`), log bez tych linii,
  `.progress.jsonl` je ma po walidacji.
- `invalid_progress_lines_are_ignored` — linia z błędnym JSON-em albo złym `status` pominięta
  w `.progress.jsonl`.
- `settle_adds_last_progress_from_file` — po końcu przebiegu `settle` dokleja `last_progress`
  do `state["dispatch"]`.
- `get_change_sees_last_progress` — `ChangeStore.get(change)["dispatch"]["last_progress"]`
  ma ostatnią poprawną linię.
- `persona_report_still_reads_the_final_json_object` — przy failed delivery z liniami
  postępu w stdout wynik `persona` ma `detail` i `permission_denials` jak dziś (test
  regresji).

### 4.3. pdi (`tests/test_console.py` nowy)

- `board_lists_each_change_in_its_lane_and_phase` — zmiany z fixturze (`state` z `waiting`,
  `approved`, `releases`) widoczne w odpowiedniej kolumnie każdego pasa.
- `board_sse_emits_update_on_state_change` — po zapisie stanu zmiany (`ChangeStore.save`)
  pojawia się event SSE `event: change-updated`.
- `inbox_page_renders_questions_as_text_fields` — pozycja bramki z `questions: ["kto?", "kiedy?"]`
  ma dwa pola `name="answer_0"`, `name="answer_1"`; brak JS inline.
- `inbox_page_renders_question_options_as_radio_when_n19_is_on` — pozycja bramki z pytaniem
  w kształcie N19 (dict z `options` i `recommended`) ma radio z zaznaczoną rekomendowaną
  i polem tekstowym dla `other: true`.
- `decide_via_button_goes_through_decide_inbox_item` — POST z `outcome=approved`, polami
  odpowiedzi → ta sama ścieżka co `Inbox.decide(…)`, rejestr dostaje decyzję z
  `answers=[{question, answer}]` i `source.kind = console`.
- `decide_refused_without_token` — POST bez `?t=` i bez `t` w body → 404.
- `decide_refused_when_item_changed_since_load` — POST z `loaded_at` wcześniejszym niż
  `received_at` pozycji po zmianie → 409.
- `decide_refused_when_pr_unmerged` — POST `approved` dla bramki z `url` niezmergowanego
  PR-a (stubbed `_check_pr`) → odmowa jak w MCP.
- `inbox_known_option_only` — POST z `answer_0` nieobecnym w `options` pytania N19 → 400.
- `inbox_other_requires_text` — POST z `answer_0=__other__` bez `answer_0_other` → 400.
- `files_panel_lists_artifacts_and_diff` — fixture klonu z `docs/project/changes/CHG-1/…`
  i cięciem story/* → strona „Pliki” pokazuje nazwy plików, `GET /trace/CHG-1/file?path=…`
  zwraca ich treść, `GET /trace/CHG-1/diff` zwraca `git diff`.
- `files_panel_refuses_symlink` — plik `intent.md` jest symlinkiem poza klon → 403.
- `files_panel_refuses_binary` — plik `design.md` ma bajt `\0` w pierwszych 8 KiB → 403.
- `files_panel_refuses_path_outside_checkout` — ścieżka `..` albo spoza białej listy → 404.
- `files_panel_refuses_secret_like_names` — plik `.env` w klonie → 403.
- `files_panel_size_limit` — plik powyżej 256 KiB → 403 z link do PR-a.
- `files_panel_live_refreshes_over_sse` — po zapisie `intent.md` SSE wysyła `event: file-changed`
  z nazwą.
- `progress_sse_streams_new_lines` — `.progress.jsonl` dopisywany po otwarciu SSE → kolejne
  linie trafiają do klienta w ciągu 1 s (polling 0.5 s).
- `csp_header_blocks_inline_scripts_and_nonce_matches` — nagłówek CSP w każdej odpowiedzi
  ma oczekiwany kształt; nonce ten sam co w HTML.
- `escaping_of_question_decision_and_log_text` — pytanie z `<script>` nie zamyka tagu
  w HTML; treść decyzji z cudzysłowami bezpieczna; linia postępu z `<img onerror…>` w
  `message` wyświetlona jako tekst.

### 4.4. pdi (`tests/test_stack.py`)

- `sdlc_up_starts_console_and_registers_mcp` — podstawiony świat: `cmd_up` startuje
  `pdi-console` po `pdi-receiver`; `sdlc status` pokazuje linię z URL konsoli; `sdlc
  down` go kończy.
- `sdlc_open_opens_the_console_board_with_token` — URL otwarty w przeglądarce
  (podstawiony `open_url`) to `http://127.0.0.1:8788/board?t=<PDI_CONSOLE_TOKEN>`.
- `ensure_env_generates_console_token` — `PDI_CONSOLE_TOKEN` powstaje raz; `PDI_CONSOLE_PORT`
  dostaje domyślną.

### 4.5. kontraktowa walidacja linii postępu

- `pdi.contract.errors("event", {"type": "run.progress", …, "payload": <linia>})` —
  w teście `tests/test_dispatch_local.py` opakuję linię z `.progress.jsonl` w zdarzenie
  kontraktu i sprawdzę, że walidacja zdaje; żaden `pdi.contract` ani kontrakt nie
  zmienia się w tym kroku.

## 5. Bramki i uruchomienie (wszystko lokalnie)

- **pdi:**
  - `uv run pytest` — wszystko zielone (plus nowe testy §4).
  - `uv run ruff check src tests`, `uv run ruff format --check src tests`.
  - `uv run mypy src`.
- **tf:**
  - `python3 tools/workspace.py check --packs pack-it` (pozostaje jak dziś).
  - `python3 tools/workspace.py check --packs mode-pdi` (dotyka zmian w `phase_run.py` i nowego `phase_progress.py`).
  - `python3 modes/mode-pdi/tests/skill_gate/...` (skill gate pdi-decisions — zapewnia, że SKILL.md i skrypty się zgadzają).
  - `python3 core/tests/test_settings_coverage.py` (żadne nowe polecenie Bash w sesji persony nie wchodzi; stream-json wywołuje `phase_run.py run` subprocess, więc coverage bez zmian).

**Przebieg lokalny na `dbqm45/sdlc-proba`** (mój Mac, Docker + `gh` + `claude`): nowa lista
kontrolna w [docs/przebieg-lokalny.md](przebieg-lokalny.md): jedna zmiana od zgłoszenia do
pierwszej bramki, prowadzona tylko w konsoli (`sdlc open`), decyzja przyciskiem z
odpowiedzią na pytanie (wybrana z opcji, jeśli Z2a zmergowane; inaczej wpisana), następna
faza widoczna live. Pozycja na liście kontrolnej właściciela — do zrobienia poza pracą
tego PR.

## 6. Kolejność prac (gałęzie, commity, PR-y)

1. **tf**: gałąź `feat/phase-stream-json-progress` od `origin/main`.
   - Nowy `phase_progress.py` z testami.
   - `phase_run.py` przełącza się na stream-json z `--verbose`; końcowy obiekt wyniku bez zmian.
   - Testy, bramki, commit, push, PR.
2. **pdi**: gałąź `feat/console-lokalnie` od `origin/main`.
   - `pdi.dispatch_local`: wrapper `on_line` → `.progress.jsonl`; `settle` z `last_progress`; testy.
   - `pdi.console` + testy (trzy pasy, ślad, inbox z przyciskami, pliki, SSE, N19-ready).
   - `pdi.stack.home` + `pdi.stack.cli`: `PDI_CONSOLE_TOKEN/PORT`, `pdi-console` w `sdlc up/down/status`, `sdlc open` otwiera `/board?t=…`.
   - `pyproject.toml`: `pdi-console`.
   - Aktualizacja `README.md`, `docs/przebieg-lokalny.md`, `integrations/claude-code/README.md`, `modes/mode-pdi/GUIDE.md` w tf.
   - Testy, bramki, commit, push, PR.

**Kolejność merge'u (po zielonym CI, nie merguję sam):** tf → pdi.

**Koordynacja z innymi sesjami.** Inne sesje mogą dotknąć `src/pdi/dispatch_local.py`
(pdi) i `scripts/phase_run.py` (tf). Zmieniam w `dispatch_local.py` tylko kroki fazy
`run` (nowy wrapper `on_line`), nowe funkcje (`progress_path`, `_read_last_progress`,
`last_progress_of`) i rozszerzenie `settle(…)` — bez przestawiania istniejących
kroków. W `phase_run.py` dotykam tylko `cmd_run` (argv, strumieniowanie) i dodaję
import nowego `phase_progress` — nie zmieniam `build_prompt`, `gate_event`,
`cmd_cuts`, `cmd_workflow_install`, ani kontraktu wyniku. Przed PR-em rebase na
`origin/main` i rozwiązanie konfliktów z obu zachowaniami.

## 7. Źródła z datami

- Claude Code **CLI reference** — `--output-format`, `stream-json`, `--verbose`,
  `--max-budget-usd`, `--max-turns`, `--print`, `--include-partial-messages`,
  `--include-hook-events`: [code.claude.com/docs/en/cli-reference](https://code.claude.com/docs/en/cli-reference) (odczyt 2026-11-06).
- Claude Code **Headless** — stream-JSON event types `system`, `assistant`, `user`, `result`;
  `permission_denied` w strumieniu; brak preambuły na stdout; `--include-partial-messages`;
  background work na stderr: [code.claude.com/docs/en/headless](https://code.claude.com/docs/en/headless)
  (odczyt 2026-11-06).
- Claude Code **Agent SDK (TypeScript) typy** — `SDKResultMessage`, `tool_use`, `tool_result`:
  [code.claude.com/docs/en/agent-sdk/typescript](https://code.claude.com/docs/en/agent-sdk/typescript)
  (odczyt 2026-11-06).
- Claude Code **cost-tracking** — `total_cost_usd` jest szacunkiem po stronie klienta:
  [code.claude.com/docs/en/agent-sdk/cost-tracking](https://code.claude.com/docs/en/agent-sdk/cost-tracking)
  (odczyt 2026-11-06).
- Claude Code **Permissions** — permissions.allow i zasady decyzji o narzędziach:
  [code.claude.com/docs/en/permissions](https://code.claude.com/docs/en/permissions) (odczyt 2026-11-05, przypomniany).
- Claude Code **Sandboxing** — kontener + `enableWeakerNestedSandbox` (Z8a, kontekst):
  [code.claude.com/docs/en/sandboxing](https://code.claude.com/docs/en/sandboxing) (Z8a §8.4,
  odczyt 2026-11-02).
- Kontrakt pdi 0.11.0 — `run_progress` i `answers` w decyzji: `contract/event.schema.json`
  i `contract/decision.schema.json` w tym repo (stan 2026-11-02).
- Mock-upy konsoli — `design/konsola/v2-klikalna/{Main,Slad,Decyzje,Autonomia}.html` (stan
  2026-11-02).
- Wynik A6 — `docs/przebieg-lokalny.md#wynik-przebiegu-2026-11-03-05-a6` (2026-11-03–06).

**Zasada weryfikacji (§8.4 planu).** Każde wejście zewnętrzne, na którym opiera się ten
krok, sprawdzone 2026-11-06 w oficjalnej dokumentacji z datą; niepewność („waiting for a
gate” nie jest w stream-JSON) nazwana wprost — stan derywowany.
