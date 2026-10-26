# Plan kroku F3 — pdi MVP (intake, wzbogacenie, triaż, przyjęcie do budowy)

Stan: 2026-10-26. Krok z planu jednego flow (`docs/plan-jeden-flow-sdlc.md` §6, F3: „pdi: intake, wzbogacenie,
triaż, rejestr decyzji, przyjęcie do budowy jako PR z `intent.md`”). Rejestr decyzji jest od początku, mały rejestr
zgłoszeń i triaż od pdi #21. Decyzje właściciela z 2026-10-26: **formularz + Claude** jako intake, **faza `intent` w
tf** jako przyjęcie do budowy, **duplikaty i próg powrotu** jako wzbogacenie (kontekst z tf i ci_for_sdlc później).

## Intake
- **Formularz** w `pdi-receiver`: `GET /problems/new?t=<PDI_FORM_TOKEN>` daje stronę HTML bez skryptów (kto, czego nie
  może, jaki skutek, tytuł, obejście, jak często, proponowane rozwiązanie, kto zgłasza, problem czy pomysł);
  `POST /problems` (formularz, token w ukrytym polu, porównanie w stałym czasie) zapisuje PRB z `channel: form` i
  odpowiada stroną z numerem i podobnymi zgłoszeniami. Bez `PDI_FORM_TOKEN` obie ścieżki odpowiadają 404. Wszystko, co
  wraca na stronę, jest escapowane; błędy pól wracają przy polach, z wpisanymi wartościami.
- **Claude**: `record_problem` (jest), `clarify_problem(problem, pytania)` — 3–5 pytań do zgłaszającego, status
  `clarifying`, pytania w `problem-notes/<PRB>.yaml` i w powiadomieniu (`what: questions`); `update_problem(problem,
  pola, ready)` — poprawia opis (np. rozwiązanie przeformułowane na problem, a pierwotne w `proposed_solution`) i przy
  `ready` ustawia `ready_for_triage`. Instrukcja serwera MCP mówi, że opis to problem, nie rozwiązanie.

## Wzbogacenie
- **Podobne zgłoszenia**: `similar_problems()` — słowa (≥ 4 litery) tytułu i opisu (who, cannot, impact), miara
  Jaccarda ≥ 0,3, najwyżej 5, bez odrzuconych i duplikatów; zwracane przy zapisie (narzędzie i formularz) i przez
  `find_similar_problems`.
- **Scalenie duplikatu**: triaż `duplicate` z `duplicate_of` dopisuje oryginałowi `reports_count` (domyślnie 1 +
  liczba z duplikatu), dowód `observation` („Duplikat PRB-9 od … z …”) i `related`.
- **Próg powrotu**: odłożenie (`parked`) zapamiętuje liczbę zgłoszeń; gdy `return_when` mówi „N nowe zgłoszenia”
  (albo „N new reports”) i kolejne duplikaty go przekroczą, zgłoszenie wraca do `ready_for_triage`, a zgłaszający
  dostaje powiadomienie (`what: returned`). Inny próg (np. incydent) jest tylko pokazany.

## Przyjęcie do budowy
- Triaż `accepted` bez `change` nadaje kolejny `CHG-n` (prefiks z `contract.json`, ponad znane zmiany i zgłoszenia);
  z `change` używa podanego. Zakłada stan zmiany (`changes/<CHG>.yaml`, `source: PRB-n`), zostawia w `outbox/`
  zdarzenie `problem.accepted` (kontrakt 0.4.0) i uruchamia w tf fazę `intent` (`dispatch_phase`, jak po bramkach
  w F4) z nowymi wejściami `source` (PRB) i `problem` (JSON: tytuł, kto, czego nie może, skutek, obejście, jak często,
  rozwiązanie zgłaszającego); persona tf pisze `intent.md`, otwiera PR i prosi o B1. Wynik uruchomienia trafia do
  stanu zmiany, `retry_dispatch` ponawia.
- Strona tf (osobny PR): szablon `sdlc-phase.yml` przyjmuje `source` i `problem`; w fazie `intent` brak katalogu zmiany
  zakłada go (`decision_record.py change new CHG --source PRB`), a prompt persony dostaje treść zgłoszenia.

## Elementy
`src/pdi/problems.py` (podobne, doprecyzowanie, scalenie, próg powrotu, przyjęcie), `src/pdi/form.py` (strony i
parsowanie formularza, czyste), `src/pdi/receiver.py` (ścieżki formularza), `src/pdi/dispatch.py` (`source`,
`problem`), `src/pdi/mcp_server.py` (`clarify_problem`, `update_problem`, `find_similar_problems`, `triage_problem`
z opcjonalną zmianą), README.

## Testy (najpierw czerwone)
`tests/test_problems.py`: podobne (próg, kolejność, wykluczenia), doprecyzowanie i aktualizacja (statusy, pola własne
pdi odrzucone), scalenie duplikatu, próg powrotu (z liczbą i bez), przyjęcie (nadany CHG, podany CHG, stan zmiany,
`problem.accepted` zgodne z kontraktem, wejścia dispatchu, brak konfiguracji → `skipped`, ponowienie).
`tests/test_form.py`: strona (escapowanie, wartości po błędzie), parsowanie (wymagane pola, limity, kanał).
`tests/test_receiver.py`: GET/POST formularza (zły token 404/403, zapis 201 ze stroną), bez tokenu 404.
`tests/test_dispatch.py`: nowe wejścia tylko gdy podane. `tests/test_mcp_server.py`: nowe narzędzia.

## Wynik (2026-10-26)
- Najpierw czerwone (nowe przypadki w `test_problems.py`, `test_form.py`, `test_receiver.py`, `test_dispatch.py`,
  `test_mcp_server.py`), potem kod; cały `pytest` 523/523, `ruff check`, `ruff format --check`, `mypy` (strict)
  czyste.
- Prawdziwy `pdi-receiver` z `PDI_FORM_TOKEN`: strona 200 (zły token 404), wysłany formularz 201 i `PRB-1` z
  `channel: form`; token nie trafia do logu dostępu.
- Do zrobienia po stronie tf (osobny PR): wejścia `source` i `problem` w `sdlc-phase.yml`, założenie katalogu zmiany w
  fazie `intent`, treść zgłoszenia w prompcie persony. Do tego czasu przyjęcie zapisuje się w pdi, a uruchomienie fazy
  może się nie udać (stan zmiany pokazuje błąd, `retry_dispatch` ponawia).
