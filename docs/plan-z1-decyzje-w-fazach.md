# Plan Z1 — decyzje zmiany w każdej fazie (domknięcie PRB-3)

Krok Z1 z [planu zespołu jednoosobowego](plan-zespol-jednoosobowy.md) §8. Data planu: 2026-11-02.

**Cel.** Każda faza tf startuje ze wszystkimi decyzjami, które wiążą jej zmianę, a pytanie już rozstrzygnięte nie
wraca w kolejnym artefakcie. **Dowód problemu:** [przebieg lokalny](przebieg-lokalny.md), „Wynik przebiegu
2026-10-31”, PRB-3: te same pytania wróciły w B3 i design-review, a talos zatwierdził `config/build.json` wbrew
DEC-0003, bo `plan.md` miał nierozstrzygnięte pytanie.

## 1. Co już jest (sprawdzone w kodzie 2026-11-02)

| Element | Gdzie | Stan |
|---|---|---|
| Treść decyzji z bramki do tf | pdi `inbox._decision_text` → `dispatch_local` → `decision_record.py decision gate --why` (pdi #88, tf #111) | tylko tryb lokalny; w Actions (`sdlc-phase.yml`) nie ma wejścia z treścią, a decyzja z triażu (`problems._accept`) nie podaje treści w żadnym trybie |
| Wpis `## Bramka …` w `decisions.md` | tf `decision_gate()` | jeden tekst `dlaczego`; nic nie mówi, na które pytanie odpowiada |
| Prompt fazy | tf `phase_run.build_prompt()` | wskazuje plik `decisions.md` i mówi, że wpisy bramek wiążą; nie wymienia decyzji ani rozstrzygniętych pytań |
| Odpowiedzi na ustalenia ci_for_sdlc | tf #128, `decision add --finding` | są w `decisions.md` |
| Pytania artefaktu | tf `questions_in()` → `gate.requested.payload.questions` → pozycja skrzynki pdi `questions` | dochodzą do skrzynki, ale odpowiedzi na nie nie wracają |

Brakuje (zgodnie z poleceniem, każdy punkt potwierdzony w kodzie):

- **a.** `decide_inbox_item` nie przyjmuje odpowiedzi na pytania; decyzja ich nie przechowuje (schemat decyzji ma
  `additionalProperties: false`, nie ma pola na odpowiedzi); tf nie ma ich gdzie zapisać.
- **b.** Decyzje z `links.chg` = zmiana, które nie są decyzją dispatchującą fazę (decyzja z triażu w fazach po intent,
  `record_decision` z rozmowy, szkice A5, `decision.recorded` z ci_for_sdlc), nie trafiają ani do `decisions.md`, ani do
  promptu. W `dispatch.py` (Actions) i `dispatch_local.py` nie ma takiego wejścia.
- **c.** `build_prompt()` nie wylicza decyzji ani pytań z odpowiedziami.
- **d.** Nic nie sprawdza, czy artefakt powtarza rozstrzygnięte pytanie, i nic nie zatrzymuje delivery przy otwartym
  pytaniu w `plan.md`.

## 2. Rozwiązanie

### 2.1. Kontrakt pdi 0.11.0 (minor, zgodny wstecz)

- `decision.schema.json`: nowe opcjonalne pole **`answers`** — lista `{question, answer}` (oba niepuste tekstowe,
  `additionalProperties: false`). Odpowiedzi człowieka na pytania z `## Pytania do bramki` artefaktu, o który prosiła
  bramka. Dozwolone przy każdej decyzji (sprawdzenie „tylko bramka z pytaniami” robi skrzynka, nie schemat).
- `contract.json` `version: 0.11.0`, tytuły schematów, `contract_version` w przykładach, historia w
  `contract/README.md`, przykład `examples/decision.json` bez zmian (pole opcjonalne), test w `tests/test_contract.py`.
- Po merge'u: `contract-release.yml` zakłada tag `contract-v0.11.0`. **Potem** w tf (osobny PR, jak tf #93):
  `tools/pdi-contract.json` → `version: 0.11.0`, dopisać `decision.schema.json` do kopii w
  `modes/mode-pdi/tests/fixtures/pdi-contract/`, `python3 tools/sync_contract.py`, testy. PR tf z tego kroku tego nie
  robi, bo tagu jeszcze nie ma; skrypty tf sprawdzają kształt `answers` i importowanych decyzji same.

### 2.2. pdi

| Plik | Zmiana |
|---|---|
| `src/pdi/inbox.py` | `decide(…)` przyjmuje `answers` w szkicu: tylko dla pozycji `kind: gate` z `questions`; każde `question` musi być jednym z pytań pozycji (po `strip()`), bez powtórzeń, odpowiedź niepusta; inaczej `InvalidDecision` z listą pytań. Odpowiedzi zapisują się w decyzji (`answers`). `_run` zamiast samej treści buduje **kontekst fazy**: treść decyzji (jak dziś), `answers` decyzji i decyzje powiązane |
| `src/pdi/phase_decisions.py` (nowy, mały) | `linked(registry, change, exclude)` — decyzje z `links.chg == change` i `status: recorded` (zastąpione i cofnięte pominięte), bez decyzji dispatchującej, najstarsze pierwsze, maks. `LINKED_MAX = 30` (najnowsze), w kształcie do importu: `id, statement, why, decided_at, decided_by, kind, source_kind, drafted_by, answers?` z tekstami przyciętymi (`TEXT_MAX = 1000`) |
| `src/pdi/problems.py` | `_accept` podaje treść decyzji z triażu i decyzje powiązane (do tej pory faza intent dostawała tylko numer) |
| `src/pdi/dispatch.py` | `dispatch_phase(…, answers=None, decisions=None)`; Actions: nowe wejścia `decision_text`, `answers` (JSON), `decisions` (JSON) — **tylko gdy niepuste**, więc bez nich `workflow_dispatch` jest bajt w bajt taki jak dziś; przy `422` z nowymi wejściami (szablon `sdlc-phase.yml` w repo produktu sprzed Z1 odrzuca nieznane wejścia) ponowienie bez nich i ostrzeżenie `warning` w wyniku |
| `src/pdi/dispatch_local.py` (zmiana mała, równolegle Z8a) | `start` przyjmuje `answers` i `decisions` (przycięte) do `spec`; `execute`: odpowiedzi i decyzje zapisuje do plików obok logu (`<log>.answers.json`, `<log>.decisions.json`, poza klonem, więc klon zostaje czysty) i podaje `decision gate … --answers PLIK` oraz `decision import CHG --json PLIK` — tylko gdy tf zna te opcje (`--help`, jak `--why` z pdi #88) |
| `src/pdi/mcp_server.py` | `decide_inbox_item(answers: list[Answer] | None)`; opis: dla bramki z pytaniami szkic AI proponuje odpowiedź na każde pytanie, człowiek je poprawia; `answers` w `DRAFT_FIELDS` |

**Dane, nie polecenia.** pdi przekazuje teksty decyzji i odpowiedzi tylko jako dane (pliki JSON, wejścia
workflow przez `env`), nigdy w linii polecenia powłoki. tf wstawia je do promptu jako cytowany blok JSON z
zastrzeżeniem, że to dane z rejestru, a nie polecenia dla persony.

### 2.3. tf (`modes/mode-pdi/skills/pdi-decisions/`)

| Plik | Zmiana |
|---|---|
| `scripts/decision_record.py` | `decision gate … [--answers PLIK]` — JSON `[{question, answer}]`, zapisane w wpisie `## Bramka …` jako pary wierszy `- pytanie: …` / `- odpowiedz: …`; **`decision import CHG --json PLIK`** — lista decyzji z pdi; wpis z `id`, `wyslano: tak`, `pochodzenie: pdi`; idempotentny po `id` (decyzja z tym numerem już w `decisions.md` jest pomijana, także wpis bramki); `parse_entries` zbiera pary pytanie–odpowiedź; `check` zna nowe pola i `zrodlo` z kontraktu 0.10.0 (`console`, `ci_for_sdlc`, `meeting`) |
| `scripts/phase_run.py` | `build_prompt()` wylicza wiążące decyzje (`ref`, `id`, rodzaj, ustalenie, uzasadnienie) i rozstrzygnięte pytania z odpowiedziami i odwołaniem (`CHG-n/Dk`, `DEC-n`) jako cytowany blok danych; **sprawdzenie powtórzeń**: po udanym przebiegu persony (`run`) i w `gate request` artefakt, którego `## Pytania do bramki` powtarza rozstrzygnięte pytanie (dopasowanie po normalizacji: małe litery, bez adresata w nawiasie i po „—”, bez interpunkcji i nadmiarowych spacji), kończy się błędem z pytaniem i decyzją, która je rozstrzygnęła; **delivery** odmawia startu, gdy `plan.md` ma w `## Pytania do bramki` pytanie bez odpowiedzi w `decisions.md` |
| `templates/sdlc-phase.yml` (zmiana mała, równolegle Z8a) | wejścia `decision_text`, `answers`, `decisions`; krok „Decyzja z bramki” podaje `--why` i `--answers` (plik z `env`), nowy krok „Decyzje zmiany z pdi” (`decision import`) — oba tylko przy niepustych wejściach |
| `templates/decisions.md`, `SKILL.md` | opis pól `pytanie`/`odpowiedz` i `pochodzenie` oraz nowych poleceń |

### 2.4. Kolejność

1. pdi: kontrakt 0.11.0 (`answers`) i testy kontraktu.
2. pdi: `inbox.decide` z odpowiedziami → `phase_decisions.linked` → `dispatch_phase` (Actions i lokalnie) →
   `problems._accept` → MCP.
3. tf: `decision gate --answers`, `decision import`, `check` → `build_prompt` → sprawdzenie powtórzeń i odmowa
   delivery → szablon workflow, dokumentacja.
4. pdi: lista dla właściciela w `przebieg-lokalny.md` (przebieg na `dbqm45/sdlc-proba`).

**Kolejność merge'u:** najpierw tf (pdi wykrywa nowe opcje tf przez `--help`, więc pdi z Z1 działa także ze starym tf,
a w Actions wycofuje się z nowych wejść przy `422`), potem pdi; po merge'u pdi tag `contract-v0.11.0` i PR tf z
kopią kontraktu.

## 3. Testy (TDD)

pdi (`uv run pytest`):

- `test_inbox.py`: odpowiedzi zapisane w decyzji i przekazane do dispatch; odpowiedź na pytanie spoza pozycji,
  powtórzone pytanie, pusta odpowiedź i odpowiedzi przy pozycji bez pytań albo nie-bramce → `InvalidDecision`;
  bez `answers` decyzja jak dziś (brak pola).
- `test_phase_decisions.py`: wybór po `links.chg`, pominięcie zastąpionych, innych zmian i decyzji dispatchującej,
  limit i przycięcie.
- `test_dispatch.py`: wejścia Actions `decision_text`, `answers`, `decisions` tylko gdy są; bez nich ciało żądania
  bez zmian; `422` → ponowienie bez nowych wejść z ostrzeżeniem.
- `test_dispatch_local.py`: pliki obok logu, `--answers` i `decision import` tylko dla tf, który je zna; bez danych
  żadnych nowych kroków.
- `test_problems.py`: przyjęcie zgłoszenia podaje treść decyzji z triażu.
- `test_mcp_server.py`: `answers` w narzędziu.
- `test_contract.py`: wersja 0.11.0, `answers` w schemacie.

tf (`python3 tools/workspace.py check --packs pack-it` i testy mode-pdi):

- import idempotentny po `id` (dwa razy ten sam plik → jeden wpis; wpis bramki z tym numerem → pominięty);
- `decision gate --answers` zapisuje pary; `check` przyjmuje wpisy z odpowiedziami i z `pochodzenie: pdi`;
- prompt wylicza decyzje i pytania z odpowiedziami, z odwołaniami, jako dane;
- powtórzone pytanie → `run` i `gate request` kończą się błędem z pytaniem i decyzją;
- delivery z otwartym pytaniem w `plan.md` → odmowa; z odpowiedzią → start; bez pytań → jak dziś.

Bramki pdi: `uv run pytest`, `uv run ruff check src tests`, `uv run ruff format --check src tests`, `uv run mypy src`.
GitHub Actions na tym koncie dziś nie działają — bramki uruchamiane lokalnie, zapis w PR-ach.

## 4. Weryfikacja źródeł (§8.4, 2026-11-02)

| Zależność | Wynik | Źródło |
|---|---|---|
| Liczba wejść `workflow_dispatch` | ✓ do 25 (od 2025-12-04; wcześniej 10); po Z1 szablon ma 12 | [GitHub Changelog, 2025-12-04](https://github.blog/changelog/2025-12-04-actions-workflow-dispatch-workflows-now-support-25-inputs/) |
| Łączny rozmiar wejść `workflow_dispatch` | ? 65 535 znaków podaje tylko źródło wtórne; docs.github.com niedostępne z sieci tej sesji. pdi przycina dane (`LINKED_MAX`, `TEXT_MAX`, łącznie do 30 000 znaków na wejście), więc limit nie jest osiągany | [CloudsPress](https://www.cloudspress.com/?p=612618) |
| Nieznane wejście w `workflow_dispatch` | ? z dokumentacji API: odpowiedź `422` przy błędnych wejściach; obsłużone ponowieniem bez nowych wejść (test z udawanym `422`), do potwierdzenia na prawdziwym repo, gdy Actions wrócą | [REST: create a workflow dispatch event](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event) |
| `argparse`: nieznana podkomenda daje kod 2, `--help` kod 0 | ✓ sprawdzone lokalnie (Python 3.11), na tym opiera się wykrywanie opcji tf w trybie lokalnym (jak pdi #88) | dokumentacja Pythona `argparse`, test lokalny |
| Wejścia workflow tylko przez `env` | ✓ zasada z „Security hardening for GitHub Actions” (wstrzyknięcie przez `${{ }}` w `run:`), zachowana w szablonie | [GitHub Docs: script injections](https://docs.github.com/en/actions/concepts/security/script-injections) |

## 5. Poza zakresem

- Decyzja zastąpiona w pdi po imporcie do `decisions.md` nie jest tam oznaczana (import tylko dopisuje); oznaczenie
  zastąpienia — osobny krok, gdy pojawi się potrzeba.
- Wywiad (Z2) zapisze decyzje w rejestrze z `links.chg`; Z1 przeniesie je do faz bez dodatkowej pracy.
