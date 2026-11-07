# Propozycja: Decision Record jako wspólny format pliku decyzji

**Data:** 2026-11-07 · **Status:** przyjęta 2026-11-07 (decyzje DR1–DR4 w [`decyzje.md`](decyzje.md)), do realizacji ([`TODO.md`](../TODO.md)) · **Kontrakt:** 0.13.0

## 1. Problem

Decyzje zapadają w wielu systemach: w pdi, w repo zmian (tf), w ci_for_sdlc, na spotkaniach i w Slacku. Pomysł:
jeden format pliku decyzji, który każda aplikacja umie rozpoznać i odczytać, także spoza naszego ekosystemu.

## 2. Jak jest dziś

- **Rejestr pdi:** `decisions/<projekt>/DEC-0041.md` (decyzje ogólne w `decisions/_ogolne/`). Na górze nagłówek YAML
  z polami decyzji (źródło prawdy), pod nim tekst dla człowieka generowany z tych pól (`# DEC-0041: …`,
  „Dlaczego”, opcje, założenia, dowody, źródło).
- **Repo zmiany (tf):** wpisy w `docs/project/changes/CHG-n/decisions.md` z nagłówkami tego samego kształtu.
- **Wspólny kształt:** `contract/decision.schema.json` (JSON Schema 2020-12). Pola wymagane: `id`, `statement`, `why`,
  `decided_at`, `decided_by`, `kind`, `source`, `status`, `drafted_by`; opcjonalne m.in. `options`, `evidence`
  (ze statusem epistemicznym), `assumptions` (nośne, z warunkiem unieważnienia), `answers`, `success_metric`,
  `review_by`, `supersedes` / `superseded_by`, `links`, `decision_type`, `automation`, `draft_edited`.

Format więc istnieje, ale nie ma nazwy ani znacznika: obca aplikacja nie odróżni pliku decyzji od zwykłego markdownu.

## 3. Propozycja: „Decision Record” (DR)

1. **Plik zostaje markdownem (`.md`) z nagłówkiem YAML.** GitHub, edytory, Obsidian i Confluence go wyświetlają;
   własne rozszerzenie (`.dr`) traciłoby to wszystko, a niczego nie gwarantuje — o zgodności decyduje schemat.
   `.adr` odpada: to utrwalona nazwa „Architecture Decision Record” (Nygard, MADR).
2. **Znacznik w nagłówku** rozpoznaje plik bez względu na nazwę:
   ```yaml
   ---
   record: decision
   schema: https://github.com/dbqm45/pdi/contract/decision.schema.json
   contract_version: 0.14.0
   id: DEC-0041
   statement: …
   ```
   Reguła dla czytających: plik `.md`, którego nagłówek ma `record: decision`, jest Decision Record i jego nagłówek
   przechodzi `decision.schema.json` w podanej wersji.
3. **Nazwa pliku** — dwie możliwości (do decyzji, §6):
   - zostaje `DEC-0041.md` (bez zmian w istniejących rejestrach; rozpoznanie tylko po znaczniku);
   - `DEC-0041.dr.md` (rozpoznanie także po nazwie, wzorzec `*.dr.md`; nadal zwykły markdown). Wymaga zmiany nazw
     istniejących plików przy migracji.
4. **Treść pod nagłówkiem** jest dla ludzi i może się różnić między aplikacjami; maszyny czytają tylko nagłówek.
5. **Krótka specyfikacja** `contract/decision-record.md`: znacznik, reguła rozpoznania, łańcuch zastąpień
   (`supersedes` / `superseded_by`), katalogi, wersjonowanie, przykład. Plus walidator `pdi-validate <plik|katalog>`.

## 4. Porównanie z MADR 4.0.0

MADR (Markdown Architectural Decision Records) to najpopularniejszy szablon ADR w markdownie. Wersja 4.0.0
z 2024-09-17, licencja MIT albo CC0, pliki `nnnn-title.md` w `docs/decisions/`. Źródło: szablon
`template/adr-template.md`, `README.md` i `CHANGELOG.md` w repo `adr/madr` (gałąź `main`, odczyt 2026-11-07).

### 4.1. Pole po polu

| MADR 4.0.0 | Gdzie w MADR | pdi (kontrakt 0.13.0) | Uwagi |
|---|---|---|---|
| tytuł (`# {short title}`) | nagłówek treści | `statement` | pdi: jedno zdanie decyzji, w treści jako `# DEC-n: …` |
| `status`: proposed / rejected / accepted / deprecated / superseded by ADR-0123 | nagłówek (opcjonalnie) | `status`: recorded / superseded / reverted; `superseded_by` | pdi nie ma „proposed” ani „rejected” w rejestrze: propozycje żyją w skrzynce, odrzucony szkic nie trafia do rejestru; accepted ≈ recorded, deprecated ≈ reverted |
| `date` | nagłówek | `decided_at` (+ `recorded_at`) | |
| `decision-makers` (lista) | nagłówek | `decided_by` (jeden tekst) | pdi: jedno pole tekstowe |
| `consulted`, `informed` | nagłówek | — | brak w pdi |
| Context and Problem Statement | sekcja | częściowo `why`, `links.prb` | pdi trzyma problem jako osobny obiekt (PRB) |
| Decision Drivers | sekcja (opcjonalnie) | — | najbliżej: `success_metric`, `assumptions` |
| Considered Options | sekcja | `options[]` (`option`, `chosen`) | |
| Decision Outcome („Chosen option …, because …”) | sekcja | `statement` + `why` | |
| Consequences (Good / Bad) | podsekcja (opcjonalnie) | — | brak w pdi |
| Confirmation (jak sprawdzić wykonanie) | podsekcja (opcjonalnie) | — | w pdi zaplanowane jako `verify` (`TODO.md`) |
| Pros and Cons of the Options | sekcja (opcjonalnie) | `options[].note` (tekst) | pdi bez podziału na plusy i minusy |
| More Information | sekcja (opcjonalnie) | `evidence`, `links`, `dependencies` | |

**Tylko w pdi:** `kind` (product / technical / process / triage / intent / gate), `decision_type` i `automation`
(poziomy autonomii), `project`, `source` (skąd decyzja: Claude, Slack, spotkanie, Jira… z linkiem i cytatem),
`evidence` ze statusem epistemicznym, `assumptions` z `load_bearing` i `invalidated_if`, `answers`, `review_by`,
`drafted_by` i `draft_edited` (pomiar szkiców AI), `links` do PRB / CHG / TSK / PR / ADR, `tags`.

### 4.2. Różnica w podejściu

| | MADR | pdi |
|---|---|---|
| Zakres | decyzje architektoniczne | każda decyzja: produktowa, techniczna, procesowa, triaż, bramka, automat |
| Kto pisze | człowiek wypełnia szablon | AI szkicuje z rozmowy, człowiek zatwierdza |
| Gdzie strukturę | w sekcjach treści (markdown) | w nagłówku YAML sprawdzanym schematem; treść generowana |
| Sprawdzanie | markdownlint (forma tekstu) | JSON Schema (pola i wartości) |
| Co pamięta szczególnie | opcje z plusami i minusami, konsekwencje | uzasadnienie, założenia z warunkiem unieważnienia, źródło z cytatem, status epistemiczny dowodów |

### 4.3. Wniosek

MADR nie zastąpi formatu pdi: zgubiłby to, co w testach okazało się wyróżnikiem (założenia nośne, źródło, status
epistemiczny; [test v2](../eval/v2-pamiec-decyzji/wyniki/raport.md)), i automatyzację. Warto natomiast:
- **eksport do MADR** decyzji technicznych (`kind: technical`) jako `docs/decisions/nnnn-title.md` w repo projektu —
  wtedy narzędzia i ludzie przyzwyczajeni do ADR czytają je bez pdi;
- **import z MADR**: istniejące ADR-y zespołu jako szkice w skrzynce pdi do zatwierdzenia (jak A5), z `source` na plik;
- **przejąć z MADR dwa pola** jako opcjonalne: `consequences` (dobre i złe skutki) i `confirmation` / `verify`
  (już w planie w `TODO.md`), a z nagłówka `consulted` i `informed`.

**Narzędzia** (tabela „MADR template” na `adr.github.io/adr-tooling/`, odczyt 2026-11-07): adr-log, ADR Manager
(strona i rozszerzenie VS Code), Hugo Markdown ADR Tools, Log4brains (bez numerów w nazwie pliku) i pyadr obsługują
MADR **2.1.2**, wtyczka ADR do Backstage — 2.1.2 i 3.x; żadne nie jest tam wpisane dla 4.0.0. adr-tools (bash, z
przepisaniami na Node.js, C# i Pythona) używa szablonu Nygarda, nie MADR. Eksport do MADR musi więc wybrać wersję:
4.0.0 dla ludzi i najnowszych zasad albo układ zgodny z 2.1.2 / 3.x, jeśli zespół korzysta z tych narzędzi —
do ustalenia w planie eksportu.

## 5. Koszt i zgodność

- Znacznik w nagłówku to zmiana kontraktu (0.14.0): `decision.schema.json` ma `additionalProperties: false`, więc
  `record`, `schema` i `contract_version` trzeba do niego dodać jako pola opcjonalne. Zgodne wstecz: stare pliki bez
  znacznika dalej przechodzą; nowe zapisy pdi i tf (`decision_record.py`) dostają znacznik.
- Migracja istniejących rejestrów: dopisanie znacznika (skrypt, jeden commit). Zmiana nazw na `.dr.md` — tylko przy
  wariancie z §3.3.
- Eksport i import MADR to osobne, późniejsze kroki.

## 6. Do decyzji

Wszystkie przyjęte 2026-11-07 według rekomendacji.

| # | Pytanie | Decyzja |
|---|---|---|
| DR1 | Czy wprowadzamy nazwany format „Decision Record” ze znacznikiem w nagłówku? | tak (kontrakt 0.14.0, specyfikacja i walidator) |
| DR2 | Nazwa pliku: `DEC-n.md` czy `DEC-n.dr.md`? | `DEC-n.md` + znacznik; bez zmiany nazw istniejących plików |
| DR3 | Zgodność z MADR: eksport, import, oba, żadne? | najpierw eksport decyzji technicznych; import, gdy pojawi się zespół z istniejącymi ADR |
| DR4 | Przejąć pola z MADR (`consequences`, `confirmation`, `consulted`, `informed`)? | `consequences` i `confirmation` tak (razem z `verify` z `TODO.md`); `consulted` / `informed` dopiero, gdy pdi będzie miało wielu użytkowników |
