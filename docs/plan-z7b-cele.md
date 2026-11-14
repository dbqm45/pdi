# Z7b-1a — cele zmiany (`targets`) w kontrakcie, planie i bramce B3

Data: 2026-11-06 · Powiązane decyzje: [DZ6, DZ7](decyzje.md); [plan „zespół jednoosobowy” §8.1, §8.3 (N4, N20), §8.5 (Z10a, Z10e)](plan-zespol-jednoosobowy.md).
Kontekst wyjścia (po A6): pdi `3754a61` na main (kontrakt `0.11.0`), tf 5.58.7 (kopia 0.11.0).
Otwarte PR w pdi: tylko #145 (docs); kontrakt na main jest `0.11.0`, więc przy tym PR biorę `0.12.0` (Z2a jeszcze nie scalone).

## Cel kroku

Każda zmiana niesie mierzalne cele jakości (`targets`): pokrycie i mutacje zmienionego kodu (N4), opcjonalne budżety wydajności
i opcjonalne progi ewaluacji aplikacji AI (obowiązkowe dla produktu AI, DZ7). Architekt (persona `tomasz`) proponuje
`targets` razem z planem (w planie minimum 2 rozważone opcje — N20), człowiek zatwierdza je na B3; sprawdzenie
przed B4 (Z7b-1b) używa tych samych pól. Zmiana celów po B3 wymaga nowej decyzji (`supersede`), nie cichej edycji
pliku.

Układ `targets` zostaje otwarty: jako opcjonalne pola w tym samym miejscu dojdą później `slo` (Z10a) oraz progi
wydajności i dostępności w `performance` i `accessibility` (Z10e), bez łamania zgodności wstecz.

## Sprawdzone źródła (§8.4)

- **Kontrakt pdi 0.11.0.** `contract/release-plan.schema.json` (sprawdzone 2026-11-06): `additionalProperties: false`
  na obiekcie głównym, więc nowe pole wchodzi przez minor; brak pola `targets`, `slo` ani SLO. `contract/event.schema.json`
  `readiness_changed` ma `additionalProperties: false` i pola `change`, `readiness`, `open_questions`, `url`.
- **StrykerJS** (mutacje JS/TS) — strona projektu `stryker-mutator.io`, cytowana w §8.3 N4, §8.2 (sprawdzone wcześniej
  w planie, plan N4 2026-11-03). Uruchamianie na `--mutate` ze zmienionym kodem jest wspierane.
- **mutmut** (mutacje Pythona) — `mutmut.readthedocs.io`, cytowane w §8.3 N4 (2026-11-03). Uruchamianie na podzbiorze
  plików przez `--paths-to-mutate`.
- **Pokrycie 100% z wyjątkami** — Lean TECHniques (§8.3 N4); projekt zapisuje wyjątki jawnie przy progu.
- **DZ6 i DZ7** — `docs/decyzje.md`, zapisane 2026-11-02.

Zasada weryfikacji (§8.4): nazw narzędzi i formatów nie zapisujemy w schemacie jako enum; zapisujemy tylko to, co jest
niezmienne w decyzji człowieka (jednostki, próg, opcjonalne wyłączenia). Wartości typu `python/mutmut`, `js/stryker`
zostają polami tekstowymi, a schemat waliduje kształt, nie zbiór narzędzi.

## Co dołożyć do kontraktu (wersja 0.12.0)

- **`release-plan.schema.json`** — w `properties` nowe opcjonalne pole `targets` (wraz z definicjami pomocniczymi
  w `$defs`): obiekt z `additionalProperties: false`, polami `coverage` (obiekt: `kind: "changed_lines"`, `min_percent`
  0–100, `tool`, `exclusions: [{pattern, reason}]`), `mutation` (obiekt: `kind: "changed_lines"`, `tool`, `min_score`
  0–100, `exclusions`) i dwiema listami: `performance: [{name, metric, limit, note?}]` i `evaluations:
  [{name, metric, min, dataset, note?}]`. Te dwie listy zostają puste, dopóki nie są potrzebne; w planach produktów AI
  `evaluations` jest wymagane — reguła biznesowa po stronie `tf` (persona `tomasz` i `decision_record.py`), nie schematu,
  bo kontrakt nie zna „typ produktu”.
- **Zarezerwowane pola** w `targets` (opisane w schemacie jako komentarz do wersji, bez deklaracji na razie): `slo`
  (Z10a), `accessibility` (Z10e). Dodawane w swoich krokach — zostają opcjonalne.
- **`event.schema.json`** — w `$defs/readiness_changed` dojdzie opcjonalne pole `targets_status`: obiekt
  `additionalProperties: false` z `overall: enum("met","not_met","unknown")`, `checked_at` (data i czas), `summary`
  (krótki tekst) i listą `details: [{name, kind: enum("coverage","mutation","performance","evaluation","other"),
  status: enum("met","not_met","unknown"), observed, required, note?, url?}]`. Z7b-1b wypełnia je
  z ci_for_sdlc; brak pola znaczy „nie badano”.
- **`examples/release-plan.json`** rozszerzamy o `targets` (pokrycie 90% w zmienionych liniach, mutacje 70%, jeden
  element `performance`, pusta `evaluations`). Nowy przykład `examples/release-plan-ai.json` pokazuje `evaluations`.
- **`examples/event-readiness.changed.json`** rozszerzamy o `targets_status` (co najmniej jeden element w `details`).
- **`contract.json`** — podbijamy `version` na `0.12.0`.
- **`contract/README.md`** — wpis historii i akapit o `targets` i `targets_status`.

## Co w pdi

1. Odczyt `release.yaml` repo zmiany. pdi obecnie nie czyta pliku `release.yaml`; dołożę minimalną funkcję
   `pdi.changes.read_release_plan(change, repo_root)` (`None` gdy pliku nie ma), która zwraca sparsowany plan po
   walidacji przez `contract.errors("release_plan", data)`.
2. Rozszerzenie bramki B3 (`Inbox.decide` / `_run` / szkicu gate.requested):
   - Przy zatwierdzeniu `approved` na B3 bierzemy `targets` z `release.yaml` i zapisujemy ich kopię w stanie zmiany
     jako `approved_targets_at_b3` (razem z numerem decyzji). To daje punkt odniesienia dla detekcji zmiany po B3.
   - Nowa pozycja skrzynki typu `gate` dla B3 pokazuje `targets` i rozważone opcje w `summary` / `questions`: tego
     potrzebuje konsola (A7) i prośba do człowieka.
3. `pdi.flow.readiness_changed` dostaje opcjonalny parametr `targets_status`; `_run_* / Inbox.receive` dla
   zdarzenia `readiness.changed` zapisuje pole w stanie (`state["targets_status"]`). `approve-for-implementation`
   i B4 w `_run` sygnalizują człowiekowi, że cele są `not_met` (jeśli taki jest ostatni znany status).
4. Detekcja zmiany celów po B3. Propozycja: w `Inbox.decide` po B3 zapisana kopia `approved_targets_at_b3`; każda
   pozycja skrzynki dla `approve-for-implementation` sprawdza bieżące `targets` z `release.yaml` i porównuje
   z `approved_targets_at_b3`; różnica → `status: "changes_requested_by_automation"` w `questions` i
   rekomendacja `supersede` dla decyzji z B3. Implementacja minimalna: pole `targets_changed_since_b3: true` w stanie
   i w `summary` prośby o `approve-for-implementation`; MCP `propose_decisions_from_conversation` pozostaje bez zmian.
5. Rozszerzenie `get_change`: `targets`, `approved_targets_at_b3` i `targets_status` już są w stanie (punkty 2–3),
   więc `get_change` zwraca je naturalnie przez `ChangeStore.get`. W `get_trace`: na krawędzi `approved`
   bramki B3 dokładamy w `nodes[gate:B3].data.targets` kopię zatwierdzonych celów (do karty bramki w konsoli
   z A7).

## Co w tf

Pack `pack-it` / mode `mode-pdi`:

1. **`packs/pack-it/personas/tomasz.yaml`.** Dodać do `habits` zdanie: „Przy fazie `architecture` zapisz
   w `plan.md` sekcję `## Cele zmiany (targets)` z co najmniej pokryciem i mutacjami (N4), krótkim uzasadnieniem
   każdego progu i, dla produktu AI, obowiązkowymi progami ewaluacji (DZ7). Progi uzasadniaj wartością, nie
   generyczne 100%/80%: wysokość progu wynika z atrybutów jakości (`arch-quality-attributes`) i kodu zmienianego
   (ryzyko + historia defektów)." `arch-tech-selection` już wymaga 2–3 kandydatów i macierzy (SKILL §3, §5) —
   dla N20 wystarczy wymusić zapis tego porównania w `plan.md`; dopiszemy sekcję `## Rozważone opcje` do szablonu
   i do checka.
2. **`modes/mode-pdi/skills/pdi-decisions/templates/plan.md`.** Dodać dwie sekcje: „Rozważone opcje” (minimum dwie,
   z plusami, minusami i kosztem; wskazany wybór i powód) i „Cele zmiany (`targets`)” (tabela: Nazwa, Rodzaj,
   Próg, Narzędzie, Uzasadnienie). Format tekstowy czytelny dla człowieka; walidacja w `decision_record.py`.
3. **`modes/mode-pdi/skills/pdi-decisions/templates/release.yaml`.** Dodać komentarze przykładowe sekcji `targets`
   z pokryciem, mutacjami i (opcjonalnie) `evaluations` dla produktu AI.
4. **`modes/mode-pdi/skills/pdi-decisions/scripts/decision_record.py`.**
   - `check_release` sprawdza `targets` tylko przez schemat (schemat już to zrobi po bumpie i resyncu kopii).
   - `check_plan` dostaje dwa nowe testy: (a) co najmniej dwa pod-nagłówki w sekcji „Rozważone opcje” — jedno zdanie
     błędu dla planu z jedną opcją; (b) obecna sekcja „Cele zmiany (`targets`)” z co najmniej jednym wpisem pokrycia
     i jednym mutacji, gdy plan ma status inny niż `draft`.
5. **Resync kontraktu.** Po tagu `contract-v0.12.0` tf #136-podobny PR: `tools/pdi-contract.json` `version: 0.12.0`,
   regenerowane kopie plików z tagu i fixtures. (PR odpali się po merge pdi PR-a; tutaj przygotowuję pliki,
   kopia pójdzie jako osobny tf PR.)
6. **N4 w `delivery` pod `claude --print`.** W `packs/pack-it/settings.json` i `modes/mode-pdi/settings.json`
   `permissions.allow` ma już wiersze typu `Bash(pytest …)`. Dodać wiersze dla:
   - `Bash(mutmut run:*)`, `Bash(mutmut results:*)`, `Bash(mutmut show:*)` — mutacje Pythona;
   - `Bash(npx stryker run:*)`, `Bash(npx stryker init:*)` — StrykerJS; `npx` wstępnie dopuszczony, jeśli jest
     w settings coverage (sprawdzę `core/tests/test_settings_coverage.py`). Jeśli nie ma — dopisać.
   Instalacja narzędzi jako dev-zależność idzie przez lockfile i karencję N10; same komendy ograniczają się do
   `mutmut run --paths-to-mutate <zmienione>` i `stryker run --mutate <zmienione>` — bez sieci po instalacji.

## Kolejność i TDD

1. **pdi: plan (ten dokument).**
2. **pdi: kontrakt (testy pierwsze).**
   - Test: `targets` w `release-plan` z poprawnym kształtem przechodzi; brak `targets` jest poprawny; znany zły
     kształt (`min_percent: 120`, `kind: "all"`) jest błędem; `coverage.exclusions` bez `reason` jest błędem;
     niepuste pole `evaluations` z brakującym `dataset` jest błędem.
   - Test: zarezerwowane pola (`slo`, `accessibility`) nie są wymagane; nieznane pole wchodzi do `targets` tylko
     wtedy, gdy obiekt `targets` go dopuszcza (brak dla nieznanego → `additionalProperties: false`).
   - Test: `readiness_changed` z poprawnym `targets_status` przechodzi; z `overall: "maybe"` jest błędem.
   - Zmiana `contract.json` i README; aktualizacja `test_contract.py` (`CONTRACT_VERSION == "0.12.0"`); nowe
     przykłady.
3. **pdi: flow, inbox, trace, mcp_server, changes.**
   - Testy `test_flow.py`: `readiness_changed(state, "ready", targets_status={...})` zapisuje pole.
   - Testy `test_inbox.py`: po `gate.decided` dla B3 z `approved` i release.yaml z `targets`, stan ma
     `approved_targets_at_b3` równe kopii z planu; prośba o `approve-for-implementation` zawiera
     `targets_changed_since_b3: true`, gdy plan po B3 ma inne `targets`.
   - Testy `test_trace.py`: `data.targets` na węźle `gate:B3` po zatwierdzeniu.
   - Testy `test_mcp_server.py` dla `get_change`: zwrócony stan ma `targets` i `approved_targets_at_b3`.
4. **tf (osobny PR po tagu).**
   - Testy `modes/mode-pdi/tests/test_decision_record.py` (jeśli jest) lub `test_plan_check.py`: plan z jedną
     opcją w sekcji „Rozważone opcje” → błąd; plan bez sekcji „Cele zmiany” → błąd; plan z poprawnymi dwiema
     opcjami i `targets` → zero błędów.
   - Testy `test_settings_coverage.py`: dopisanie wymagań dla `mutmut`, `npx stryker` (jeśli używamy `stryker`).
5. **Dokumenty.**
   - `contract/README.md` — historia `0.12.0` i opis `targets` / `targets_status`.
   - `README.md` (pdi) — jeden akapit w sekcji kontraktu.
   - `docs/plan-zespol-jednoosobowy.md` §10 — status Z7b-1a: zrobione (po merge).
   - `docs/polecenia-startowe-zespol.md` — wiersz Z7b-1a: polecenie odświeżone o decyzje wdrożeniowe.
   - `docs/przebieg-lokalny.md` — nowy element listy dla B3: „B3 pokazuje `targets` i rozważone opcje; po akceptacji
     są wiążące”.

## Bramki (co uruchomić lokalnie)

- pdi: `uv run pytest`, `uv run ruff check src tests`, `uv run ruff format --check src tests`, `uv run mypy src`.
- tf (osobny PR): `python3 scripts/workspace.py check --packs pack-it` i `--packs mode-pdi`; testy skilla
  `pdi-decisions` (`modes/mode-pdi/tests/test_decision_record.py` i powiązane).

## Nazwy nowych pól (wejścia dla Z7b-1b)

- `release_plan.targets` (obiekt): `coverage`, `mutation`, `performance[]`, `evaluations[]`.
  - `coverage`: `kind`, `min_percent`, `tool`, `exclusions: [{pattern, reason}]`.
  - `mutation`: `kind`, `tool`, `min_score`, `exclusions: [{pattern, reason}]`.
  - `performance[]`: `{name, metric, limit, note?}`.
  - `evaluations[]`: `{name, dataset, metric, min, note?}`.
- `event.readiness_changed.targets_status`: `{overall, checked_at, summary?, details: [{name, kind, status, observed?,
  required?, note?, url?}]}`.
- Stan zmiany po bramce B3: `approved_targets_at_b3`, `targets_status`, `targets_changed_since_b3`.

## Co zostaje poza Z7b-1a

- Realne uruchamianie StrykerJS / mutmut w fazie `delivery` — fakt, że `claude --print` dostaje komendy przez
  `settings.json`, zapisuję w tf PR; pętla, która zmusza agenta tf do uruchomienia narzędzi i zaraportowania wyniku,
  jest w ci_for_sdlc (Z7b-1b).
- `slo` (Z10a) i progi wydajności / dostępności (Z10e) wchodzą swoimi krokami jako opcjonalne pola w `targets` —
  schemat już zostawia na nie miejsce (`additionalProperties: false` nie blokuje dodania nowych nazwanych pól w
  kolejnych minorach).
- Automat `supersede` dla decyzji B3 po zmianie celów. Teraz dajemy sygnał (`targets_changed_since_b3`); pełna
  decyzja w pdi inbox (powiązanie z `supersedes` w kontrakcie 0.11.0) idzie w B3 grupie planu (Z7b-2).
