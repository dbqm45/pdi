# Plan realizacji: A2b (część pdi) — decyzje z ci_for_sdlc w rejestrze

**Data:** 2026-10-27 · **Źródło:** [polecenia startowe A2](polecenia-startowe-a2.md), decyzja [D-A2](decyzje.md) ·
**Zależy od:** A0 (kontrakt 0.5.0), A3 (licznik akceptacji)

## Cel
Decyzja podjęta w ci_for_sdlc (zamknięcie pytania z cytatem, `finding.auto_close`) trafia do rejestru pdi, więc
licznik akceptacji z A3 i `pdi-stats` ją liczą. Człowiek zatwierdza w ci_for_sdlc (D-A2); pdi tylko zapisuje gotową
decyzję. Drogi zwrotnej nie ma: odbiornik odpowiada numerem `DEC`, który ci_for_sdlc zapamiętuje.

## Kontrakt 0.7.0
- **Nowe zdarzenie `decision.recorded`** (wysyła ci_for_sdlc; później także tf). Treść:
  - wymagane: `decision_type`, `ref` (czego dotyczy decyzja w aplikacji nadawcy, np. `PAY-12/COV-001`),
    `statement`, `decided_by`, `drafted_by` (`ai` / `human`);
  - opcjonalne: `why`, `kind` (jak w decyzji, domyślnie `other`), `url` (strona pozycji w aplikacji nadawcy),
    `draft_edited` (czy człowiek zmienił szkic AI), `evidence` (cytaty: `text`, opcjonalnie `source_url`),
    `automation` (`level` 0–2, `rule`, przy 2 `veto_until` — decyzja automatu, bez człowieka), `supersedes`
    (`DEC` zastępowanej decyzji, np. ponowne otwarcie pytania), `change` (CHG), `problem` (PRB).
  - `automation` i `draft_edited` się wykluczają: automat nie poprawia szkicu, a decyzja automatu nie liczy się
    do akceptacji człowieka (w liczniku A3 jest „nieznana”).
- **`source.kind` decyzji:** nowa wartość `ci_for_sdlc`.
- Wersja 0.7.0 w `contract.json`, tytułach schematów, przykładach zdarzeń i pakiecie; zdarzenia z 0.4.0–0.6.0 dalej
  przechodzą. Nowy przykład `examples/event-decision.recorded.json`.

## pdi
1. **Odbiornik:** `ci_for_sdlc` może wysyłać `decision.recorded` (`inbox.ACCEPTED`). Skrzynka nie tworzy pozycji —
   zapisuje decyzję w rejestrze i zwraca `{"status": "recorded", "decision": "DEC-n"}`; ten sam `id` zdarzenia
   drugi raz → `duplicate` z tym samym `DEC` (znacznik `event:<id>` w decyzji).
2. **Które typy:** nadawca zapisuje tylko typy ze swojej listy (`ci_for_sdlc` → `finding.auto_close`). Typ chroniony
   (DA2) z `automation` → odrzucone (400): typy chronione decyduje zawsze człowiek.
3. **Polityka:** decyzja automatu (`automation.level`) poniżej poziomu typu w `autonomy.yaml` (domyślnie 3) jest
   zapisana (to już się stało w ci_for_sdlc), ale dostaje znacznik `autonomy:outside-policy`, a odpowiedź —
   ostrzeżenie. Zapis nie zmienia polityki.
4. **Mapowanie na decyzję:** `source` `{kind: ci_for_sdlc, url: url albo ref, excerpt: ref}`, `evidence` z cytatów
   (`epistemic_status: observation`), `links` `chg` / `prb`, znaczniki `ci_for_sdlc`, `ref:<ref>`, `event:<id>`,
   `typ:<decision_type>`; `why` domyślnie z nadawcy, typu i `ref`.
5. **Zastąpienie** (`supersedes`): tylko decyzja tego samego nadawcy i tego samego `ref`; inaczej 400. Używa
   `Registry.supersede`.

## Pliki
| Plik | Zmiana |
|---|---|
| `contract/event.schema.json`, `contract/decision.schema.json`, `contract/contract.json`, tytuły pozostałych schematów, `contract/examples/*` | 0.7.0, `decision.recorded`, `source.kind: ci_for_sdlc` |
| `contract/README.md` | wersja i historia, wiersz zdarzenia, zgodność wstecz |
| `src/pdi/inbox.py` | `decision.recorded` w `receive` |
| `src/pdi/receiver.py` | `decision` w odpowiedzi |
| `tests/test_contract.py`, `tests/test_inbox.py`, `tests/test_receiver.py`, `tests/test_autonomy.py` | jak niżej |
| `docs/polecenia-startowe-a2.md` | polecenie startowe A2b dla ci_for_sdlc (wysyłka) |
| `pyproject.toml`, `uv.lock` | wersja 0.7.0 |

## Kolejność (TDD)
1. Testy kontraktu: wersja 0.7.0, przykład `decision.recorded`, wymagane pola, `automation` wyklucza `draft_edited`,
   `source.kind: ci_for_sdlc`, zgodność wstecz zdarzeń 0.4.0–0.6.0.
2. Testy skrzynki: zapis decyzji z polami i znacznikami, duplikat po `id`, typ spoza listy nadawcy, typ chroniony
   z `automation`, decyzja poza polityką (znacznik, ostrzeżenie), `supersedes` (ten sam `ref` tak; obcy `ref` albo
   decyzja spoza nadawcy nie), licznik A3 liczy zapisane decyzje.
3. Test odbiornika: podpisany `POST /events/ci_for_sdlc` z `decision.recorded` → numer `DEC` w odpowiedzi.
4. Kod, potem dokumentacja.

Bramka: `uv run pytest`, `ruff check`, `ruff format --check`, `mypy --strict src` (Python 3.13 i 3.11).
