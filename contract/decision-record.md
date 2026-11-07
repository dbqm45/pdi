# Decision Record — specyfikacja pliku decyzji

**Wersja:** kontrakt 0.14.0 · **Decyzje:** DR1–DR4 ([`docs/decyzje.md`](../docs/decyzje.md)) · **Schemat:**
[`decision.schema.json`](decision.schema.json) · **Walidator:** `pdi-validate` ·
**Uzasadnienie i porównanie z MADR:** [`docs/propozycja-decision-record.md`](../docs/propozycja-decision-record.md)

Decision Record (DR) to plik jednej decyzji, który każda aplikacja może rozpoznać i odczytać bez pdi. Słowa
„musi”, „nie może”, „powinien” i „może” mają znaczenie wymagań.

## 1. Plik

- Tekst UTF-8 z rozszerzeniem `.md`.
- Zaczyna się od nagłówka YAML: wiersz `---`, mapa YAML, wiersz `---`. Pod nagłówkiem jest treść w markdownie.
- **Nagłówek jest normatywny**, treść nie: treść to widok dla ludzi i może się różnić między aplikacjami
  (rejestr pdi generuje ją z nagłówka przy każdym zapisie). Aplikacja czytająca decyzję musi brać dane z nagłówka.
- Daty (`decided_at`, `review_by`) są tekstem `RRRR-MM-DD`. Czytający powinien przyjąć także datę YAML bez
  cudzysłowów (wynik ręcznej edycji) i traktować ją jak ten sam tekst.

## 2. Rozpoznanie

Plik `.md` jest Decision Record wtedy i tylko wtedy, gdy jego nagłówek ma pole `record` o wartości `decision`.
Pole `record` jest zarezerwowane dla rodzajów zapisu z tego kontraktu; dziś jedynym jest `decision`. Plik bez
pola `record` nie jest Decision Record, nawet jeśli leży w katalogu decyzji.

## 3. Znacznik

| Pole | Wymagane w DR | Wartość |
|---|---|---|
| `record` | tak | `decision` |
| `schema` | powinno | `https://github.com/dbqm45/pdi/contract/decision.schema.json` (`$id` schematu) |
| `contract_version` | powinno | wersja kontraktu (SemVer), według której zapisano plik, np. `0.14.0` |

Znacznik powinien stać na początku nagłówka. Rejestr pdi nadaje go sam przy każdym zapisie; w szkicu przysłanym
do pdi te pola są odrzucane. Pliki zapisane przed kontraktem 0.14.0 nie mają znacznika — `pdi-records migrate`
dopisuje go w miejscu.

## 4. Pola decyzji

Poza znacznikiem nagłówek musi przejść [`decision.schema.json`](decision.schema.json) w wersji z
`contract_version`. Wymagane: `id`, `statement`, `why`, `decided_at`, `decided_by`, `kind`, `source`, `status`,
`drafted_by`. Opisy pól: [dokument 14 §4.1](../docs/14-pdi-standalone.md#41-schemat-decyzji-contractdecisionschemajson)
i opisy w schemacie; od 0.14.0 także `consequences` (skutki `good` / `bad` / `neutral`) i `confirmation` (`how`,
`kind`, `ref`: jak sprawdzić, że decyzję wykonano).

## 5. Identyfikator i nazwa pliku

- `id` ma kształt klucza kontraktu (`^[A-Z][A-Z0-9]+-[0-9]+$`, prefiks decyzji domyślnie `DEC`, `contract.json`).
- Nazwa pliku musi być `<id>.md` (np. `DEC-0041.md`). Nazwy plików się nie zmienia (DR2).
- `id` musi być jednoznaczne w zbiorze decyzji (rejestrze, katalogu).

## 6. Katalogi

- **Rejestr pdi:** `decisions/<projekt>/<id>.md`, gdzie `<projekt>` to pole `project`; decyzje bez projektu
  w `decisions/_ogolne/`. Ręcznie przeniesiony plik dalej jest częścią rejestru; pole `project` jest źródłem prawdy.
- **Gdzie indziej** (repo projektu, eksport, inne aplikacje): dowolny katalog. Czytający rozpoznaje pliki po
  znaczniku (§2), nie po ścieżce.

## 7. Zastąpienie decyzji

- Decyzja zastąpiona ma `status: superseded` i `superseded_by: <id nowej>`; nowa ma `supersedes: <id starej>`.
- `status: superseded` wtedy i tylko wtedy, gdy jest `superseded_by`.
- Łańcuch musi być spójny w obie strony: jeśli A ma `superseded_by: B`, to B ma `supersedes: A`, i odwrotnie.
- Treści zastąpionej decyzji się nie zmienia; zmieniają się tylko `status` i `superseded_by`.
- `status: reverted` jest w schemacie, ale jego znaczenie nie jest jeszcze opisane w kontrakcie, a rejestr pdi go
  nie nadaje; do czasu opisu aplikacje nie powinny go zapisywać.

## 8. Wersjonowanie

- Kontrakt jest wersjonowany według SemVer ([`README.md`](README.md)); w 0.x zmianę niezgodną wstecz oznacza druga
  liczba.
- Czytający może przyjąć plik z `contract_version` równym albo starszym niż jego kontrakt i sprawdzić go swoim
  schematem (pola dodawane są jako opcjonalne).
- Plik z `contract_version` nowszym niż kontrakt czytającego: czytający nie może twierdzić, że plik jest poprawny
  (może zawierać pola, których nie zna); powinien zgłosić potrzebę aktualizacji.

## 9. Sprawdzanie

`pdi-validate <plik|katalog>...` (pakiet pdi) sprawdza:
- w katalogu — wszystkie pliki `.md` rekurencyjnie; pliki bez pola `record` pomija; plik podany wprost musi być DR;
- w każdym DR — czytelny nagłówek, `record: decision`, `contract_version` nie nowszy niż walidator, zgodność
  ze schematem (§4), nazwę pliku (§5);
- między plikami — powtórzone `id` i spójność zastąpień (§7); brak wskazanej decyzji tylko przy sprawdzaniu
  całych katalogów.

Komunikaty podają plik i regułę, bez treści decyzji. Kod wyjścia 1 przy błędzie, 0 bez błędów (do CI).

## 10. Przykład

```markdown
---
record: decision
schema: https://github.com/dbqm45/pdi/contract/decision.schema.json
contract_version: 0.14.0
id: DEC-0041
statement: Bulk konfiguracja ładowarek zaczyna od zmiany taryfy.
why: Najczęstsza operacja w zgłoszeniach; restart i firmware mają inne ryzyka.
decided_at: '2026-10-23'
decided_by: po
kind: triage
project: control-tower
status: recorded
drafted_by: ai
draft_edited: false
source:
  kind: manual
consequences:
- text: Operator zmienia taryfę na wielu ładowarkach naraz zamiast po jednej.
  effect: good
- text: Restart i aktualizacja firmware czekają na kolejne cięcia.
  effect: bad
confirmation:
  how: Test e2e zmiany taryfy na 50 ładowarkach w jednej operacji
  kind: test
  ref: e2e/bulk-tariff.spec.ts
links:
  prb: PRB-34
  chg: CHG-12
---

# DEC-0041: Bulk konfiguracja ładowarek zaczyna od zmiany taryfy.

**Dlaczego:** Najczęstsza operacja w zgłoszeniach; restart i firmware mają inne ryzyka.
```
