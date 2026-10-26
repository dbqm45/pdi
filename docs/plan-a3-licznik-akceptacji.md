# Plan realizacji: A3 — licznik akceptacji szkiców

**Data:** 2026-10-26 · **Źródło:** [plan automatyzacji §4](plan-automatyzacja-i-konsola.md#4-kroki-automatyzacji) · **Zależy od:** A0 (kontrakt 0.5.0) · **Decyzje:** DA1, DA2 ([decyzje](decyzje.md))

**Stan:** zrealizowany 2026-10-26 — 585 testów, ruff, mypy `--strict`. Przy okazji naprawione: rejestr zapisywał tylko
pola z listy `FIELD_ORDER`, więc pola z kontraktu 0.5.0 (`decision_type`, `draft_edited`, `automation`) ginęły przy
zapisie; test pilnuje teraz, że każde pole schematu decyzji trafia do pliku.

## Cel
Wiadomo, które typy decyzji są gotowe do automatyzacji, zanim cokolwiek zostanie zautomatyzowane. pdi liczy, jak
często człowiek zatwierdza szkic AI bez zmian, i proponuje zmianę poziomu. Zmiana poziomu to zawsze decyzja człowieka
w skrzynce. Ten krok niczego nie automatyzuje — wykonawcy poziomów 1–2 to A2 i A4.

## Ustalenia (czego plan automatyzacji nie przesądza)
1. **Zapis:** `record_decision` i `decide_inbox_item` przyjmują `decision_type` i `draft_edited` (kontrakt 0.5.0).
   Skrzynka nadaje typ sama, jeśli go nie podano: problem → `triage`, ocena skutku → `outcome.assessment`, bramka etapu
   flagi → `flag.stage_advance`, inna bramka → `gate.<bramka>` (np. `gate.b1`). Triaż zgłoszenia w `problems.py`
   → `triage`. Komenda `/record-decision` podaje `draft_edited`: `true`, gdy człowiek poprawił szkic przed zapisem.
2. **Polityka organizacji:** plik `autonomy.yaml` w katalogu rejestru, zgodny z `contract/autonomy.schema.json`.
   Brak pliku albo typu w pliku = poziom domyślny 3 (`contract.json` → `autonomy.default_level`).
3. **Pomiar** (moduł `pdi.autonomy`, raport także w `pdi-stats`): dla każdego typu okno to ostatnie N decyzji ze szkicem
   AI i znanym `draft_edited` (N i progi z polityki typu albo z `contract.json`: 30, 95%, 10%). Decyzje ze szkicem AI
   bez `draft_edited` są liczone osobno jako „nieznane” i nie wchodzą do okna.
4. **Rekomendacja:**
   - typ chroniony (DA2) — nigdy obniżenie;
   - obniżenie o jeden poziom (3 → 2, 2 → 1), gdy okno jest pełne i udział szkiców bez zmian ≥ progu; nigdy do 0
     (poziom 0 tylko dla czynności bez skutków dla produktu — ustawia go człowiek wprost w polityce);
   - powrót na 3, gdy typ jest poniżej 3, a udział poprawionych szkiców w oknie przekracza próg — bez wymogu pełnego
     okna, bo to kierunek bezpieczny;
   - w pozostałych przypadkach „bez zmian” z powodem (np. „za mało danych: 12/30”).
5. **Propozycja do skrzynki:** narzędzie `propose_autonomy_changes` tworzy pozycję `kind: autonomy`
   (`autonomy-<typ>-to<poziom>-<data>`) dla każdej rekomendacji zmiany, chyba że dla tego typu jest już otwarta
   pozycja. Poziom 2 dostaje domyślne okno weta `PT4H` (przykład z planu automatyzacji).
6. **Decyzja:** `decide_inbox_item` z `outcome` `approved` albo `rejected` zapisuje decyzję `kind: process`,
   `decision_type: autonomy.level_change`, z pomiarem jako dowodem. `approved` zmienia `autonomy.yaml` (poziom,
   okno weta, `decision`, `updated_at`); nowa polityka jest sprawdzana schematem przed zapisem decyzji, więc typu
   chronionego nie da się obniżyć nawet ręcznie zmienioną propozycją.

## Pliki
| Plik | Zmiana |
|---|---|
| `src/pdi/autonomy.py` (nowy) | polityka, pomiar, rekomendacje, pozycje propozycji, zastosowanie decyzji |
| `src/pdi/inbox.py` | `kind: autonomy` w `decide`; domyślny `decision_type` dla pozycji skrzynki |
| `src/pdi/problems.py` | domyślny `decision_type: triage` |
| `src/pdi/mcp_server.py` | `decision_type`, `draft_edited` w zapisie; narzędzia `autonomy_report`, `propose_autonomy_changes` |
| `src/pdi/stats.py` | sekcja autonomii w `pdi-stats` |
| `integrations/claude-code/record-decision.md` | `draft_edited` przy zapisie |
| `tests/test_autonomy.py` (nowy), testy skrzynki, MCP, statystyk | |

## Kolejność (TDD)
1. Testy pomiaru i rekomendacji (okno, progi, typy chronione, nieznane, powrót na 3).
2. Testy propozycji i decyzji w skrzynce (idempotencja, zastosowanie polityki, odrzucenie, obniżenie typu chronionego).
3. Testy zapisu `decision_type` / `draft_edited` przez MCP i domyślnych typów w skrzynce i triażu.
4. Kod, potem dokumentacja (status planu automatyzacji, README integracji).

Bramka: `uv run pytest`, `ruff check`, `ruff format --check`, `mypy --strict src` (Python 3.13 i 3.11).
