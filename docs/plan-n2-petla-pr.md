# Plan N2 — pętla budujący–recenzent na PR agenta tf i samonaprawa CI

Data: 2026-11-07 · Status: **w PR** (pdi + tf) · Krok N2 [planu „zespół jednoosobowy”](plan-zespol-jednoosobowy.md)
(§8.3, grupa A5), po A6, Z8a, Z1 i N1. Stan wyjściowy: pdi main `df1894e` (kontrakt 0.14.0), tf 5.65.0 (kopia
kontraktu 0.13.0), sdlc-proba na fabryce 5.65.0, Actions w sdlc-proba włączone 2026-11-07.

## Cel

PR cięcia agenta tf trafia do człowieka tylko z zielonymi checkami i zamkniętymi uwagami przeglądu albo z wyraźnym
„nie udało się po N rundach” i powodem — zawsze z sekcją **„Przewodnik dokończenia”** w opisie PR. Weryfikacja jest
oddzielona od agenta: przegląd, walidacja uwag i odczyt CI robi pdi (host) i drugi model, a agent tf tylko poprawia.

## Przebieg (po fazie delivery, na każdy PR cięcia)

```
_publish_cuts (jak dziś: tytuł z 1. commitu, opis = runs/TSK-n.md + „Change: CHG-n”)
  └─ pętla PR (pdi.pr_loop.run_loop), runda k = 1…:
       1. review    — kontener (Z8a): `pr_loop.py review` → ustalenia {id, severity, file, line, body, decision_ref?}
       2. walidacja — host: `second_review.py comments --pr <n> --input <plik>` (N1), tylko uwagi critical/important
       3. triaż     — pdi (deterministycznie): fix | question | minor
       4. checki    — host: `gh pr checks <url> --json name,state,bucket,link,workflow` do końca oczekiwania
       5. koniec?   — brak `fix` i checki zielone → green (albo needs_human, gdy są pytania);
                      runda k > PDI_PR_LOOP_ROUNDS (2, jak DZ6) albo budżet → needs_human z powodem
       6. poprawka  — kontener: `pr_loop.py fix` (agent tf, tylko uwagi `fix` i log CI jako dane cytowane) → host:
                      `git push origin story/…` → następna runda
     po każdej rundzie: host podmienia w opisie PR tylko sekcję „Przewodnik dokończenia” (`gh pr edit --body-file`)
```

### Triaż uwag (pdi `pr_loop.triage`)

| Uwaga | Trafia do |
|---|---|
| `minor` (poniżej progu; próg = `important`) | lista „Drobne uwagi (poza pętlą)” w przewodniku, bez poprawki |
| ma `decision_ref` (sprzeczna z decyzją zmiany, Z1) | pytanie do człowieka `[sprzeczne z CHG-n/Dk] …`, bez poprawki |
| walidacja `status: unavailable` (np. `no_api_key`) | pytanie `[niepotwierdzone: drugi przegląd niedostępny (no_api_key)] …`, bez poprawki; przewodnik mówi to wprost |
| walidacja `confirmed: false` albo brak wpisu dla id | pytanie `[niepotwierdzone] … — <powód drugiego modelu>` |
| `confirmed: true`, critical/important | poprawka agenta tf w następnej rundzie |

Wcześniejsze wyjście: gdy po przeglądzie nie ma uwag `fix` (zostały tylko drobne i pytania) i checki są zielone,
pętla kończy się od razu.

### Czerwone checki — decyzja: co znaczy „zielone”

**Zielone = GitHub zgłasza dla głowy PR co najmniej jeden check i wszystkie mają `bucket` `pass` albo `skipping`.**
N2 dokłada do szablonu `change-check.yml` (mode-pdi, uruchamiany `on: pull_request` dla każdego PR) obowiązkowy krok
**„Weryfikacja produktu (N3)”**: `BASE=origin/<baza> ./verify.sh`; brak `verify.sh` to czerwony krok z poleceniem
dodania (nie cichy PASS). Dzięki temu testy produktu biegną na każdym PR kodu, a nie tylko na zmianach definicji.

- `fail`/`cancel` → host czyta log: z `link` checku wyciąga numer przebiegu Actions i woła
  `gh run view <id> --log-failed` (token `gh` zostaje na hoście); ostatnie 200 linii / 20 000 znaków idą do agenta tf
  w znacznikach `<untrusted source=ci-log>` (treść z zewnątrz, N14).
- `pending` dłużej niż `PDI_PR_LOOP_CHECKS_WAIT` (domyślnie 1200 s) → needs_human, powód `checks_timeout`.
- **brak checków** po `PDI_PR_LOOP_CHECKS_GRACE` (domyślnie 120 s) → zapas lokalny: `pr_loop.py verify` (N3,
  `./verify.sh`) w kontenerze fazy. Czerwony wynik → log idzie do agenta tf jak log CI. Zielony wynik **nie** daje
  `green`: PR kończy się `needs_human` z powodem `no_ci_checks` („weryfikacja N3 lokalnie przeszła, ale PR nie ma
  checków CI”). PR bez checków nigdy nie jest zielony.

Tryb Actions (`sdlc-phase.yml`): pętla tam nie działa w tym kroku — push tokenem `github.token` nie uruchamia
workflow CI na gałęziach cięć (ograniczenie GitHuba opisane w szablonie), więc pętla nie miałaby na co czekać.
Zostaje to na krok z tokenem aplikacji (Z8g); szablon dostaje tylko komentarz. Pętla działa w trybie lokalnym
(`PDI_DISPATCH=local`), w którym pdi wypycha gałęzie tokenem `gh` właściciela.

### Przewodnik dokończenia (wspólny z N7)

Stała sekcja `## Przewodnik dokończenia` w opisie PR, przed linią `Change: CHG-n`; host podmienia tylko ją (znacznik
`<!-- pdi:przewodnik -->`), raport agenta tf i linia `Change:` zostają. Podsekcje:

- **Stan** — `green` / `needs_human` / w toku, runda k z N, powód, checki (np. „2 checki zielone”), koszt pętli;
- **Zrobione** — tematy commitów cięcia (z `git log`), poprawione uwagi z rund;
- **Zostaje dla Ciebie** — pytania (niepotwierdzone, sprzeczne z decyzją z refem), otwarte uwagi po limicie
  (plik:linia), kroki: przejrzyj, odpowiedz w PR, scal; brak `REVIEW.md` → polecenie `pr_loop.py scaffold`;
- **Decyzje poza planem — do zatwierdzenia** — sekcje „Odłożone do decyzji” i odstępstwa `plan_drift` z raportu
  agenta tf (już w opisie) wskazane z prośbą o zatwierdzenie, plus `[założenie]` z raportu;
- **Ryzyka** — walidacja niedostępna, brak checków CI, limit rund, budżet, drobne uwagi bez poprawki;
- **Drobne uwagi (poza pętlą)** — lista uwag poniżej progu.

### Stan w pdi

`state["pr_loop"]` w `changes/CHG-n.yaml` — słownik po adresie PR:

```yaml
pr_loop:
  https://github.com/o/r/pull/44:
    branch: story/tsk-1-…
    round: 2            # ostatnia runda przeglądu
    max_rounds: 2
    status: green       # reviewing | fixing | green | needs_human
    reason: "…"        # ostatni powód (needs_human: limit, budget, checks_timeout, no_ci_checks, questions, error)
    cost_usd: 0.42
    questions: […]
    minor: […]
    rounds: [{round, findings, fixed, questions, minor, checks, validation, cost_usd}]
```

Na żywo: proces w tle pisze `<log>.pr_loop.json` po każdej zmianie; `dispatch_local.settle` dokłada go do stanu
także w trakcie (`running`), więc tablica konsoli pokazuje rundę. Wynik fazy (`result.json`) ma `pr_loop` i
`pr_loop_cost_usd`. Budżet: `PDI_PHASE_BUDGET_USD` obejmuje personę delivery i pętlę; każdy krok w kontenerze
dostaje `--budget-usd` = pozostała kwota, przy 0 pętla kończy się `needs_human` z powodem `budget`.

Skrzynka: `Inbox.open_ready_prs()` tworzy pozycję `kind: pr_ready` („PR gotowy do Twojego przeglądu: PR #44 …”)
tylko dla `green` i `needs_human`; `decide_inbox_item` z `outcome: reviewed` zamyka ją bez wpisu w rejestrze.
`get_trace`: węzeł PR ma `status` z pętli i `data.pr_loop` (rundy); konsola: linia na karcie tablicy i tabela
„Pętla PR” na stronie śladu.

## Pliki i kolejność (TDD: najpierw czerwony test)

tf (PR pierwszy — pdi woła jego polecenia):

| # | Plik | Zmiana | Test |
|---|---|---|---|
| 1 | `modes/mode-pdi/skills/pdi-decisions/scripts/pr_loop.py` (nowy, stdlib) | `review` (claude `--print --output-format json --json-schema`, narzędzia Read/Grep/Glob, REVIEW.md produktu albo szablon, diff i decyzje w `<untrusted>`), `fix` (agent tf, wejście z `PDI_PR_LOOP_INPUT`), `verify` (N3), `scaffold` (REVIEW.md z szablonu) | `modes/mode-pdi/tests/test_pr_loop.py` (atrapa `PDI_CLAUDE_BIN`) |
| 2 | `modes/mode-pdi/skills/pdi-decisions/templates/REVIEW.md` (nowy) | szablon z `core-git-workflow/references/review-md.md` dopasowany do dziennika zmiany | test_pr_loop (scaffold) |
| 3 | `templates/change-check.yml` | krok „Weryfikacja produktu (N3)” obowiązkowy | test_pr_loop (szablon) |
| 4 | `templates/sdlc-phase.yml` | komentarz: pętla PR tylko w trybie lokalnym (powód) | — |
| 5 | `modes/mode-pdi/settings.json`, `core/tests/test_settings_coverage.py` | `Bash(python3 .claude/skills/pdi-decisions/scripts/pr_loop.py *)`; polecenia z promptu `fix` w REQUIRED | test_settings_coverage |
| 6 | `core/skills/tf/SKILL.md` | §5 „Poprawki z pętli PR (N2)”: tylko wskazane uwagi, commit `fix(…)` ze stopką `Change: TSK-n`, bez push | skill gate tf |
| 7 | `modes/mode-pdi/skills/pdi-decisions/SKILL.md`, `GUIDE.md`, `pack.yaml` (0.9.0) | opis pętli, zmienne, co znaczy zielone | test_mode_pdi, skill gate pdi-decisions |

pdi:

| # | Plik | Zmiana | Test |
|---|---|---|---|
| 8 | `src/pdi/pr_loop.py` (nowy) | `triage`, `run_loop` ze wstrzykniętymi krokami (`Steps`), `guide_section`, `replace_guide`, `checks_state`, `run_id_of` | `tests/test_pr_loop.py` |
| 9 | `src/pdi/dispatch_local.py` | po `_publish_cuts`: `_pr_loop` z prawdziwymi krokami (kontener dla review/fix/verify, host dla walidacji, push, `gh pr checks`, `gh run view --log-failed`, `gh pr edit --body-file`); `<log>.pr_loop.json`; `settle` przenosi `pr_loop` | `tests/test_dispatch_local.py` (brak tokenu GitHub w kontenerze, kolejność kroków) |
| 10 | `src/pdi/inbox.py`, `src/pdi/mcp_server.py` | `open_ready_prs`, `pr_ready`, outcome `reviewed` | `tests/test_inbox.py` |
| 11 | `src/pdi/trace.py`, `src/pdi/console.py` | status i rundy na węźle PR, karta tablicy, tabela „Pętla PR” | `tests/test_trace.py`, `tests/test_console.py` |
| 12 | `README.md`, `integrations/claude-code/README.md`, `docs/przebieg-lokalny.md`, `docs/plan-zespol-jednoosobowy.md` | opis i punkt listy kontrolnej dla właściciela | — |

## Testy (przypadki)

pdi `tests/test_pr_loop.py`: zielone po 1 rundzie (bez uwag); poprawka i zielone w 2. rundzie; limit 2 rund →
`needs_human` z „nie udało się po 2 rundach”; wcześniejsze wyjście, gdy zostają tylko `minor` (lista w przewodniku);
niepotwierdzona uwaga → pytanie, nie do poprawki; walidacja niedostępna (`no_api_key`) → pytanie i ryzyko w
przewodniku; uwaga z `decision_ref` → pytanie z refem; czerwony check z nagranym logiem → log w poprawce jako dane w
`<untrusted>` (z neutralizacją `</untrusted>`); brak checków → lokalna weryfikacja, `no_ci_checks`; przewodnik
podmieniany co rundę bez naruszenia raportu i `Change:`; koszt per runda i przerwanie przy budżecie.
`tests/test_dispatch_local.py`: pętla po delivery, kroki review/fix w kontenerze bez `GH_TOKEN`/`GITHUB_TOKEN`,
push i `gh` na hoście, `result.json` z `pr_loop`, `settle` → `state["pr_loop"]`. `tests/test_inbox.py`: pozycja
`pr_ready` tylko dla green/needs_human, bez duplikatu, zamknięcie `reviewed`. Trace i konsola: status i rundy.

tf `test_pr_loop.py`: prompt `review` z REVIEW.md, z szablonem przy braku, diff i decyzje w znacznikach; parsowanie
`structured_output` i zapasowo tekstu; `fix` czyta `PDI_PR_LOOP_INPUT`, log CI w znacznikach; `verify` bez
`verify.sh` → `missing`; `scaffold` nie nadpisuje; change-check ma krok N3.

## Źródła (dostęp 2026-11-07)

| Co | Wynik | Źródło |
|---|---|---|
| `claude -p --json-schema` — zwalidowany JSON po zakończeniu pracy agenta (tylko print) | ✓ | [CLI reference](https://code.claude.com/docs/en/cli-reference) |
| Wynik ze schematem w polu `structured_output` wiadomości `result`; błąd `error_max_structured_output_retries`; `success` bez `structured_output` traktować jak błąd | ✓ (SDK); dla CLI `--output-format json` zakładamy to samo pole, zapasowo JSON z `result` — **do sprawdzenia na żywo** | [Structured outputs](https://code.claude.com/docs/en/agent-sdk/structured-outputs) |
| `--tools "Read,Grep,Glob"` ogranicza narzędzia; domyślny zestaw na Linuksie nie ma Glob/Grep | ✓ | CLI reference |
| `--max-budget-usd` (szacunek klienta, może przekroczyć), `--max-turns` | ✓ | CLI reference |
| `gh pr checks --json bucket,…` (`bucket`: pass, fail, pending, skipping, cancel; kod 8 — pending) | ✓ `gh 2.89.0 pr checks --help` (lokalnie; cli.github.com niedostępne z tej sesji) | gh help |
| `gh run view <id> --log-failed`; `gh pr edit --body-file`; `gh pr view --json body,headRefOid` | ✓ `gh 2.89.0 … --help` | gh help |
| Push tokenem `github.token` nie uruchamia workflow | ✓ (znane, opisane w `sdlc-phase.yml` tf) | [GitHub Docs — Triggering a workflow from a workflow](https://docs.github.com/en/actions/using-workflows/triggering-a-workflow#triggering-a-workflow-from-a-workflow) |
| Spotify Honk: PR po weryfikacji oddzielonej od agenta | ✓ według §8.4 planu; artykułu nie udało się otworzyć z tej sesji (host poza siecią) — szczegółów (liczba rund) nie przejmujemy | [Spotify, 2025-11](https://engineering.atspotify.com/2025/11/spotifys-background-coding-agent-part-1) |
| Przewodnik dokończenia | ✓ jako praktyka dostawcy | podcast Modern CTO z Blitzy (plan §8.4) |
| Limit 2 rund | ✓ | DZ6 ([decyzje](decyzje.md)) |

## Niezweryfikowane

- Pole `structured_output` w `--output-format json` CLI (SDK potwierdzone) — parser ma zapas; sprawdzić w pierwszym
  przebiegu na sdlc-proba (lista w [przebiegu lokalnym](przebieg-lokalny.md), §4b).
- Jak długo GitHub pokazuje pusty `gh pr checks` po push, zanim pojawi się check `pending` — stąd zapas 120 s.
