# Plan realizacji: kontrakt 0.9.0 — format `design.md` (etap 07 Design, F6)

**Data:** 2026-10-27 · **Źródło:** plan jednego flow §2 etap 07 i §F6; tf `docs/plans/2026-10-27-faza-design-figma.md`;
decyzje właściciela 2026-10-27: D-F1 — agent domyślnie linkuje ramki projektanta (szkic ramek przez agenta tylko na
żądanie), D-F2 — format `design.md` w kontrakcie pdi.

**Stan:** zrealizowany 2026-10-27 — kontrakt 0.9.0, 700 testów, ruff, mypy.

## Zakres
`design.md` zmiany (`docs/project/changes/CHG-n/design.md`) ma tabelę, którą czytają maszyny: tf sprawdza pokrycie
przed bramką `design-review`, ci_for_sdlc bierze ramki Figmy z linków zamiast dopasowania po treści.

1. `contract.json` → `conventions.design`: lista stanów interfejsu (te same co `UiState` w ci_for_sdlc), nagłówki
   kolumn (PL i EN), wartości „brak ramki” i „nie dotyczy”, wzorzec identyfikatora wymagania.
2. `design-links.schema.json` — odczytana postać tabeli: wiersze `requirement`, `journey`, `state`, `status`
   (`linked` / `missing` / `not_applicable`), `frame` (`file_key`, `node_id`, `url`) przy `linked`, `note` wymagana
   przy `missing` i `not_applicable`.
3. Para przykładów `examples/design.md` ↔ `examples/design-links.json` — wzorzec dla parserów tf i ci_for_sdlc.
4. `pdi.design.parse_design_md` — parser referencyjny (pdi może pokazać ramki w grafie śladu); test: przykład .md
   daje dokładnie przykład .json.

## Reguły formatu
- Tabela z nagłówkiem `Wymaganie | Ścieżka | Stan | Ramka | Uwagi` (albo `Requirement | Journey | State | Frame |
  Notes`); inne tabele w pliku są pomijane. Pierwsza tabela z tym nagłówkiem jest tabelą ramek.
- Wymaganie: klucz (`US-3`, `CHG-12`, klucz z Jiry) z opcjonalnym `/AC-n`.
- Ramka: link `https://www.figma.com/(design|file|proto)/<fileKey>/…?node-id=<a>-<b>` → `node_id` `a:b`;
  `brak` / `missing` → `missing`; `nie dotyczy` / `n/a` → `not_applicable`. Przy obu ostatnich uwaga jest wymagana.
- Stan z listy z `conventions.design.states`.

## Kolejność (TDD)
1. Testy: schemat poprawny, przykład JSON zgodny ze schematem i z listą stanów, parser: przykład .md → przykład .json,
   błędy (nieznany stan, zły link, brak uwagi przy `missing`, brak tabeli) z numerem wiersza; wersja 0.9.0.
2. Schemat, `contract.json`, przykłady, parser.
3. README kontraktu, status planu.

Bramka: `uv run pytest`, `ruff check src tests`, `ruff format --check src tests`, `mypy src`.
