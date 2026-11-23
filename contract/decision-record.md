# Decision Record — specyfikacja pliku decyzji

**Wersja:** kontrakt 0.17.0 (format od 0.14.0, pochodzenie od 0.16.0) · **Decyzje:** DR1–DR4 ([`docs/decyzje.md`](https://github.com/dbqm45/pdi/blob/main/docs/decyzje.md)) · **Schemat:**
[`decision.schema.json`](decision.schema.json) · **Walidator:** `pdi-validate` ·
**Uzasadnienie i porównanie z MADR:** [`docs/propozycja-decision-record.md`](https://github.com/dbqm45/pdi/blob/main/docs/propozycja-decision-record.md)

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
`drafted_by`. Opisy pól: [dokument 14 §4.1](https://github.com/dbqm45/pdi/blob/main/docs/14-pdi-standalone.md#41-schemat-decyzji-contractdecisionschemajson)
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

## 8. Pochodzenie i publikowanie w suicie (od 0.16.0)

Każda aplikacja suity trzyma swoje decyzje u siebie; DI Decision (pdi) jest indeksem suity, nie drugim źródłem
prawdy ([plan budowy suity §3a](https://github.com/dbqm45/pdi/blob/main/docs/plan-budowy-suity.md)).

- **Pole `origin`** mówi, która aplikacja jest właścicielem decyzji i gdzie leży oryginał: `app` (te same wartości
  co `source` zdarzenia), `scope` (gdzie `local_id` jest jednoznaczny: repo `owner/name`, przestrzeń DI Definition,
  projekt), `local_id` (identyfikator u właściciela: `D-012`, `CHG-12/D1`, `PAY-12/COV-001`), opcjonalnie `path`,
  `commit`, `url`. Decyzja bez `origin` zapadła w DI Decision.
- **Publikowanie:** w suicie właściciel wysyła decyzję zdarzeniem `decision.recorded` z polem `origin`. `origin.app`
  musi być równe `source` zdarzenia — aplikacja publikuje tylko własne decyzje. Poza suitą nie wysyła nic.
- **Idempotencja:** kluczem decyzji w indeksie jest `origin.app` + `origin.scope` + `origin.local_id`.
  - To samo zdarzenie albo ta sama decyzja wysłana ponownie (np. zaległa po przerwie w łączności) z niezmienioną
    treścią nie tworzy nowego wpisu; indeks odpowiada tym samym numerem `DEC`.
  - Ta sama decyzja ze zmienioną treścią to nowa wersja od właściciela: indeks zapisuje ją jako nowy wpis, który
    zastępuje poprzedni (§7).
  - Treść to pola decyzji bez pól nadawanych przez indeks (`id`, `status`, `recorded_at`, `supersedes`,
    `superseded_by`, znacznik §3) i bez `origin.path`, `origin.commit` i `origin.url` — przeniesienie pliku albo
    nowy commit bez zmiany decyzji nie tworzą nowej wersji.
- **Zmiana tylko u właściciela:** wpis w indeksie zachowuje `origin`; aplikacja nie zmienia cudzej decyzji ani jej
  kopii, tylko publikuje nową wersję własnej.
- **Nadawcy sprzed 0.16.0** wysyłają `decision.recorded` bez `origin`; indeks rozpoznaje wtedy powtórzenie tylko po
  `id` zdarzenia. Nadawca powinien podawać `origin`; pole stanie się wymagane, gdy przejdą na nie wszyscy nadawcy.

## 9. Wersjonowanie

- Kontrakt jest wersjonowany według SemVer ([`README.md`](README.md)); w 0.x zmianę niezgodną wstecz oznacza druga
  liczba.
- Czytający może przyjąć plik z `contract_version` równym albo starszym niż jego kontrakt i sprawdzić go swoim
  schematem (pola dodawane są jako opcjonalne).
- Plik z `contract_version` nowszym niż kontrakt czytającego: czytający nie może twierdzić, że plik jest poprawny
  (może zawierać pola, których nie zna); powinien zgłosić potrzebę aktualizacji.

## 10. Sprawdzanie

`pdi-validate <plik|katalog>...` (pakiet pdi) sprawdza:
- w katalogu — wszystkie pliki `.md` rekurencyjnie; pliki bez pola `record` pomija; plik podany wprost musi być DR;
- w każdym DR — czytelny nagłówek, `record: decision`, `contract_version` nie nowszy niż walidator, zgodność
  ze schematem (§4), nazwę pliku (§5);
- między plikami — powtórzone `id` i spójność zastąpień (§7); brak wskazanej decyzji tylko przy sprawdzaniu
  całych katalogów.

Komunikaty podają plik i regułę, bez treści decyzji. Kod wyjścia 1 przy błędzie, 0 bez błędów (do CI).

## 11. Eksport do MADR

`pdi-records export-madr --out <katalog> [--project P] [--format 4|2]` zapisuje decyzje `kind: technical`
(`recorded`, `superseded`) jako ADR w formacie MADR 4.0.0 (domyślnie) albo 2.1.2 (dla narzędzi, które czytają
tylko ten układ): plik `NNNN-<slug>.md` z numeru decyzji. To widok dla ludzi i narzędzi ADR, nie Decision Record:
źródłem prawdy zostaje plik decyzji. Mapowanie pól: [propozycja §4.1](https://github.com/dbqm45/pdi/blob/main/docs/propozycja-decision-record.md#41-pole-po-polu),
plan: [`docs/plan-eksport-madr.md`](https://github.com/dbqm45/pdi/blob/main/docs/plan-eksport-madr.md).

## 12. Przykład

```markdown
---
record: decision
schema: https://github.com/dbqm45/pdi/contract/decision.schema.json
contract_version: 0.17.0
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
