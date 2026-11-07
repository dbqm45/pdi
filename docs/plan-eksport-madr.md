# Plan realizacji: eksport decyzji technicznych do MADR (DR3)

**Data:** 2026-11-07 · **Źródło:** decyzja DR3 ([decyzje](decyzje.md)), [propozycja §4](propozycja-decision-record.md#4-porównanie-z-madr-400),
[`TODO.md`](../TODO.md) („Format Decision Record”, krok 5)

## Cel
Decyzje techniczne z rejestru pdi są czytelne jako ADR w repo projektu, dla ludzi i narzędzi ADR, bez pdi.

## Wersja docelowa
Dwa formaty, wybór opcją:
- **`--format 4` (domyślnie): MADR 4.0.0** (2024-09-17; szablon `template/adr-template.md` w `adr/madr`) —
  nagłówek YAML `status`, `date`, `decision-makers`; sekcje Context and Problem Statement, Considered Options,
  Decision Outcome z Consequences i Confirmation, Pros and Cons of the Options, More Information.
- **`--format 2`: MADR 2.1.2** (`template/template.md` na tagu 2.1.2) — bez nagłówka YAML, lista `* Status:`,
  `* Deciders:`, `* Date:`, `Technical Story:`, Positive / Negative Consequences, Links. Ten układ czytają według
  `adr.github.io/adr-tooling/` (2026-11-07) adr-log, ADR Manager, Hugo Markdown ADR Tools, Log4brains, pyadr
  i wtyczka Backstage.
- MADR 3.x nie osobno: różni się od 4.0.0 nazwą `deciders` i sekcją Validation zamiast Confirmation.

## Ustalenia
1. **Co:** decyzje `kind: technical` ze statusem `recorded` albo `superseded`, opcjonalnie jednego projektu
   (`--project`). `reverted` pomijane (znaczenie nieopisane w kontrakcie). Polecenie:
   `pdi-records export-madr --out <katalog> [--project P] [--format 4|2]`, zwykle `--out docs/decisions` w repo projektu.
2. **Plik:** `NNNN-<slug>.md`, `NNNN` z numeru decyzji (`DEC-0041` → `0041`), `slug` z `statement` (małe litery
   ASCII, polskie znaki bez ogonków, myślniki, do 50 znaków).
3. **Mapowanie** (propozycja §4.1): tytuł = `statement`; `status`: `recorded` → `accepted`, `superseded` →
   `superseded by ADR-NNNN` (gdy następczyni też jest eksportowana; w 2.1.2 z linkiem), inaczej `superseded (pdi
   DEC-n)`; `date` = `decided_at`; decydujący = `decided_by`; Context = skąd decyzja (rejestr pdi, projekt, problem
   PRB); Considered Options = `options` (bez opcji: samo `statement`); Decision Outcome = „Chosen option: "…",
   because {why}.” (wybrana opcja albo `statement`); Consequences = `consequences` (Good / Bad / Neutral);
   Confirmation = `confirmation`; Pros and Cons = notatki opcji; More Information = id w pdi, źródło, powiązania,
   założenia z warunkiem ponownego rozważenia, `review_by`, dowody. Treść decyzji bez tłumaczenia; stałe nagłówki
   szablonu po angielsku (tak je czytają narzędzia).
4. **Bezpieczeństwo cudzych plików:** każdy wyeksportowany plik kończy komentarz `<!-- pdi: DEC-n … -->`. Eksport
   nadpisuje i usuwa tylko pliki z tym komentarzem; plik `NNNN-*.md` bez niego (ADR napisany ręcznie) zostaje
   nietknięty i wraca jako konflikt.
5. **Powtarzalność:** drugi eksport bez zmian w rejestrze niczego nie zapisuje; zmiana `statement` zmienia nazwę
   pliku (stary plik pdi usunięty). Jeden przebieg = wynik `{written, unchanged, removed, skipped, conflicts}`.

## Pliki
| Plik | Zmiana |
|---|---|
| `src/pdi/madr.py` (nowy) | renderowanie obu formatów, nazwy plików, eksport |
| `src/pdi/records.py` | podpolecenie `export-madr` |
| `tests/test_madr.py` (nowy) | |
| `integrations/claude-code/README.md`, `contract/decision-record.md`, `TODO.md` | opis i stan |

## Kolejność (TDD)
1. Testy: wybór decyzji, nazwa pliku, oba formaty (pola i sekcje), zastąpienia, cudzy plik, powtarzalność, CLI.
2. Kod, potem dokumentacja.

Bramka: `uv run pytest`, `ruff check`, `ruff format --check`, `mypy --strict src` (Python 3.13 i 3.11).
