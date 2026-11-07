# Plan realizacji: kontrakt 0.14.0 — Decision Record

**Data:** 2026-11-07 · **Źródło:** [propozycja Decision Record](propozycja-decision-record.md), decyzje DR1–DR4
([decyzje](decyzje.md)), [`TODO.md`](../TODO.md) („Format Decision Record”, pierwszy krok)

## Cel
Schemat decyzji przyjmuje znacznik formatu Decision Record i dwa pola przejęte z MADR. Ten krok zmienia tylko
kontrakt i to, żeby rejestr nie gubił nowych pól; zapis znacznika przez pdi i tf, specyfikacja formatu, walidator
i eksport do MADR to kolejne kroki z `TODO.md`.

## Pola (wszystkie opcjonalne, więc zgodne wstecz)
| Pole | Kształt | Skąd |
|---|---|---|
| `record` | stała `decision` | DR1: znacznik rozpoznania |
| `schema` | adres `https://` schematu decyzji | DR1 |
| `contract_version` | SemVer (`0.14.0`) | DR1: wersja kontraktu, wg której zapisano plik |
| `consequences` | lista `{text, effect}`, `effect`: `good` / `bad` / `neutral` | DR4, MADR „Consequences” (Good / Bad, because …; neutral z „Pros and Cons”) |
| `confirmation` | `{how, kind?, ref?}`: `how` — jak sprawdzić, że decyzję wykonano; `kind`: `test` / `ci_check` / `review` / `metric` / `manual`; `ref` — odwołanie (id testu, nazwa kontroli, link) | DR4, MADR „Confirmation”; obejmuje planowane `verify` z `TODO.md` (jedno pole zamiast dwóch) |

## Pliki
| Plik | Zmiana |
|---|---|
| `contract/decision.schema.json` | pięć pól wyżej |
| `contract/contract.json`, tytuły schematów, `contract_version` w przykładach | 0.14.0 |
| `contract/examples/decision.json` | znacznik, `consequences`, `confirmation` |
| `contract/README.md` | wersja i historia, zgodność wstecz |
| `src/pdi/registry.py` | nowe pola w `FIELD_ORDER` (inaczej zapis je gubi; test pilnuje każdego pola schematu) |
| `tests/test_contract.py` | wersja, pola, odrzucane wartości, zgodność wstecz |
| `TODO.md` | `verify` objęte przez `confirmation`; krok odhaczony |

## Kolejność (TDD)
1. Testy kontraktu: wersja 0.14.0; przykład ze znacznikiem przechodzi; zły `record`, `schema` bez `https://`,
   `contract_version` spoza SemVer, `effect` spoza listy, `confirmation` bez `how`, nieznany `kind` — odrzucone;
   decyzja bez nowych pól dalej przechodzi; zdarzenia z wcześniejszych wersji dalej przechodzą.
2. Test rejestru: `consequences` i `confirmation` przeżywają zapis (istniejący test „każde pole schematu jest
   w `FIELD_ORDER`” obejmie też znacznik).
3. Schemat, przykład, `FIELD_ORDER`, potem dokumentacja.

Bramka: `uv run pytest`, `ruff check`, `ruff format --check`, `mypy --strict src` (Python 3.13 i 3.11).
