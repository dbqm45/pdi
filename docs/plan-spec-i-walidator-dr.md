# Plan realizacji: specyfikacja Decision Record i walidator `pdi-validate`

**Data:** 2026-11-07 · **Źródło:** [`TODO.md`](../TODO.md) („Format Decision Record”, kroki 2 i 4), decyzje DR1–DR4
([decyzje](decyzje.md)) · **Zależy od:** kontrakt 0.14.0, zapis ze znacznikiem (pdi #173, #174)

## Cel
Aplikacja spoza ekosystemu wie z jednego dokumentu, jak rozpoznać i odczytać plik decyzji, a CI może sprawdzić
katalog decyzji jednym poleceniem.

## Specyfikacja `contract/decision-record.md`
Plik (UTF-8, `.md`, nagłówek YAML między `---`), reguła rozpoznania (`record: decision`), znacznik (`schema`,
`contract_version`), co jest normatywne (nagłówek) a co nie (treść), identyfikator i nazwa pliku (`<id>.md`),
katalogi (rejestr pdi: `decisions/<projekt>/`, gdzie indziej dowolne), łańcuch zastąpień, wersjonowanie (plik
z wersją nowszą niż czytający → czytający nie twierdzi, że plik jest poprawny), przykład.

## Walidator `pdi-validate <plik|katalog>...`
- **Katalog:** wszystkie pliki `.md` rekurencyjnie; pliki bez znacznika pomija (to nie Decision Record).
- **Plik podany wprost** bez znacznika to błąd (ktoś chciał sprawdzić decyzję, a to nie jest decyzja).
- **Każdy Decision Record:** nagłówek czytelny; `record: decision`; `contract_version` nie nowszy niż kontrakt
  walidatora; nagłówek przechodzi `decision.schema.json`; nazwa pliku = `<id>.md`.
- **Między plikami:** powtórzone `id`; `superseded_by` wskazuje istniejącą decyzję, która ma `supersedes` z powrotem
  (i odwrotnie); `status: superseded` wtedy i tylko wtedy, gdy jest `superseded_by`.
- Wynik: linie `✗ <plik>: <problem>`, podsumowanie; kod wyjścia 1 przy błędzie (dla CI), 0 bez błędów.

## Pliki
| Plik | Zmiana |
|---|---|
| `contract/decision-record.md` (nowy) | specyfikacja |
| `src/pdi/validate.py` (nowy), `pyproject.toml` | walidator i punkt wejścia `pdi-validate` |
| `tests/test_validate.py` (nowy) | |
| `contract/README.md`, `README.md`, `TODO.md` | odnośniki i stan |

## Kolejność (TDD)
1. Testy walidatora: rejestr zapisany przez pdi przechodzi; każdy rodzaj błędu (zły nagłówek, schemat, nazwa pliku,
   nowsza wersja, powtórzone `id`, zerwany łańcuch, status bez `superseded_by`); pliki bez znacznika w katalogu
   pominięte, podane wprost — błąd; kod wyjścia; wynik bez treści decyzji poza nazwą pliku i problemem.
2. Test: przykład `contract/examples/decision.json` zapisany jako plik przechodzi (specyfikacja i kod mówią to samo).
3. Kod, specyfikacja, dokumentacja.

Bramka: `uv run pytest`, `ruff check`, `ruff format --check`, `mypy --strict src` (Python 3.13 i 3.11).
