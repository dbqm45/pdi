# Checki PR jako Definition of Done — plan

Stan: 2026-11-25, decyzje 1–6 przyjęte przez właściciela; **wdrożenie odłożone** (wrócimy do tego później, od pilota w pdi). Źródło: `TODO.md`, sekcja „Checki PR jako Definition
of Done” (pomysł właściciela, ostatni punkt listy). Pomysł: lista checków w PR mówi, czy zmiana jest *skończona*.
Jeden zbiorczy check **„Definition of Done”** ma w szczegółach tabelę wszystkich punktów i to on jest wymagany w
ochronie gałęzi.

## Co jest dziś (sprawdzone 2026-11-25 w `.github/workflows/` na `main`)

| Repo | Zadania uruchamiane przy PR |
|---|---|
| pdi | `test` (macierz Python 3.11 i 3.13: pytest, ruff, format, mypy, kontrakt) |
| ci_for_sdlc | `test`, `conventional-commit`, `npm-audit` |
| di-identity | `test` |
| di-contract | `check` |
| evdt-service-shipscope | `test` (`test.yml`: tytuł PR, testy główne, actionlint), `test` (`server-test.yml`) |
| evdt-shipscope-flags | 5 zadań z opisowymi nazwami (tytuł PR, backend, obrazy Docker, frontend, audyt) |
| tf | szablon `change-check.yml` — **ta sesja nie ma dostępu do `dbqm45/tf`**, więc go tu nie sprawdzałem [niezweryfikowane] |

Ochrona gałęzi i wymagane checki to ustawienia repozytoriów. Agent ich nie widzi i nie zmienia; robi to właściciel.

## Decyzje do potwierdzenia (rekomendacja w każdej)

1. **Zakres i kolejność: najpierw pdi jako pilot, potem kolejne repo, każde osobnym PR-em.** Szablon w tf dojdzie,
   gdy sesja dostanie dostęp do tf, bo z tf trafia on do każdego projektu. Pilot pokaże, jak tabela wygląda w PR.
   Kolejność po pdi: ci_for_sdlc, di-identity, di-contract, DI Release (evdt-service-shipscope), DI Release Control
   (evdt-shipscope-flags), tf. Rekomendacja: tak.
2. **Nazwy po angielsku:** `Definition of Done` dla zbiorczego checku, a dla zadań `DoD 2 · Tests (Python 3.11)`.
   Nazwy zadań w CI suity są dziś po angielsku, a tf jest publiczne. Rekomendacja: tak.
3. **Jak działa zbiorczy check.** To jedno zadanie `needs:` wszystkich pozostałych, uruchamiane zawsze (`if: always()`).
   - Pisze do podsumowania kroku (`$GITHUB_STEP_SUMMARY`) tabelę punktów: punkt, czym sprawdzany, wynik.
   - Wynik to ✅ przeszło, ❌ nie przeszło, ⏭ nie dotyczy tego repo albo 📝 do sprawdzenia przez człowieka.
   - Kończy się błędem, gdy którykolwiek wymagany punkt nie przeszedł albo został anulowany.
   - Bez nowej akcji z zewnątrz: zwykły skrypt w `run:`.

   Rekomendacja: tak.
4. **Punkt 9 („Wpływ na decyzje”) tylko informuje.** Zbiorczy check czyta opis PR z `github.event.pull_request.body`
   i wpisuje do tabeli, czy sekcja jest wypełniona. Na razie nie blokuje. Blokowanie dopiero po tym, jak zobaczymy na
   kilku PR-ach, że odczyt działa. Punkty 11 (dokumentacja) i 12 (przegląd człowieka) tylko się wyświetlają.
   Rekomendacja: tak.
5. **Bez zerwania wymaganych checków.** Zmiana nazwy zadania sprawia, że wymagany check czeka w nieskończoność
   („Expected”). Dlatego w każdym repo w dwóch krokach:
   - **(a)** dochodzi zbiorczy `Definition of Done`, a stare nazwy zostają;
   - właściciel ustawia w ochronie gałęzi wymagany tylko `Definition of Done`;
   - **(b)** osobny PR zmienia nazwy zadań na `DoD n · …`.

   Rekomendacja: tak.
6. **Punkty 6–8 tylko tam, gdzie już działają.** Definicja, cele i bezpieczeństwo pochodzą z `analyze`, które
   działa w projektach z fabryki tf. W repozytoriach suity tabela pokazuje ⏭ z powodem, a nowych bramek nie dokładam.
   Rekomendacja: tak.

## Kroki (pilot pdi)

1. Test na skrypt tabeli (`tools/dod_summary.py`, czysta funkcja: wyniki zadań i opis PR → tabela w Markdown i kod
   wyjścia). Testy pytest najpierw, potem skrypt.
2. `ci.yml`: zadanie `Definition of Done` (`needs: test`, `if: always()`) wołające skrypt z `toJSON(needs)` i opisem
   PR. Krok (a).
3. Właściciel ustawia wymagany check, a potem krok (b) z nazwami zadań, osobny PR.
4. Kolejne repo według decyzji 1, każde z tym samym skryptem przeniesionym jako kopia. Wspólne źródło przyjdzie z
   szablonem w tf.

## Ryzyka

- Zbiorczy check z `if: always()` przechodzi tylko wtedy, gdy skrypt dobrze czyta wyniki. Test musi pokryć `failure`,
  `cancelled` i `skipped`.
- Opis PR to tekst każdego, kto otwiera PR. Skrypt czyta go jako dane: szuka nagłówka sekcji i niczego z niego nie
  wykonuje.
