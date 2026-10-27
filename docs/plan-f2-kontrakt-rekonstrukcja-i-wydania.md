# Plan realizacji: kontrakt 0.8.0 — eksport rekonstrukcji z kodu i wydania kontraktu (F2)

**Data:** 2026-10-27 · **Źródło:** plan jednego flow §5 (F2: eksport rekonstrukcji w JSON, konektor rekonstrukcji
w ci_for_sdlc); decyzja właściciela 2026-10-27: format tf → ci_for_sdlc trafia do kontraktu, kontrakt ma jedno
źródło (pdi), a tf i ci_for_sdlc trzymają przypięte, generowane kopie sprawdzane w CI.

**Stan:** zrealizowany 2026-10-27 — kontrakt 0.8.0, workflow tagu wydania.

## Zakres
1. `contract/reconstruction.schema.json` — eksport rekonstrukcji z kodu (format `tf-reconstruction`, `format_version` 1),
   przeniesiony bez zmian pól z tf (`eng-codebase-mapping/scripts/reconstruction-export.schema.json`, tf #83);
   ci_for_sdlc czyta go od #69 (kopia identyczna, sprawdzone 2026-10-27). Przykład `examples/reconstruction.json` —
   wynik prawdziwego eksportera tf (ten sam, co fixture w ci_for_sdlc).
2. **Wydania kontraktu:** workflow `.github/workflows/contract-release.yml` po wejściu na `main` zmiany w `contract/`
   zakłada tag `contract-v<wersja z contract.json>`, jeśli go nie ma. Tag jest niezmienny: ponowne użycie wersji
   z inną treścią to błąd (workflow nie przesuwa tagu). Konsumenci (tf, ci_for_sdlc) pobierają pliki z tagu.
3. README kontraktu: sekcja „Wydania i kopie u konsumentów” (jak przypiąć wersję, zakaz ręcznej edycji kopii).

## Ustalenia
- `format` i `format_version` zostają w pliku (konsument rozpoznaje format bez kontraktu); `contract_version` nie
  jest dodawany — eksport to plik, nie zdarzenie.
- Test pilnuje, że tytuły wszystkich schematów niosą bieżącą wersję i że przykład przechodzi walidację.
- Tagu dla wersji sprzed 0.8.0 nie tworzymy wstecznie; pierwsze przypięcie konsumentów to 0.8.0.

## Kolejność (TDD)
1. Testy: nazwa `reconstruction` w `SCHEMA_NAMES`, przykład poprawny, przypadki błędne (zły `format`, `format_version` 2,
   linia 0, nieznany `status`, brak `evidence`), wersja 0.8.0.
2. Schemat, przykład, `contract.json`, tytuły, przykłady zdarzeń, wersja pakietu.
3. Workflow tagu (akcje przypięte do SHA), README, status planu.

Bramka: `uv run pytest`, `ruff check src tests`, `ruff format --check src tests`, `mypy src`.
