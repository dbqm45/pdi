# 14. pdi standalone: rejestr decyzji z punktami zapisu

**Data:** 2026-10-23 · **Status:** kierunek przyjęty przez właściciela; kryteria walidacji (§6) zapisane przed startem

## 1. Decyzja

pdi zaczyna jako **niezależna aplikacja: rejestr decyzji z punktami zapisu tam, gdzie decyzje zapadają** — w Claude CLI, potem w Slacku, Confluence i Jirze. Jedno kliknięcie („record decision”), AI szkicuje decyzję z kontekstu rozmowy, człowiek zatwierdza. Ten sam rejestr czyta się z powrotem w trakcie pracy („co już zdecydowaliśmy i dlaczego?”).

Flow SDLC z [planu jednego flow](plan-jeden-flow-sdlc.md) staje się **jednym z klientów** tego rejestru, a nie jedynym sposobem użycia pdi.

## 2. Dlaczego

| Powód | Źródło |
|---|---|
| Rejestr decyzji i tak jest rdzeniem pdi | plan jednego flow, D2; [dokument 13](13-rola-pdi-w-sdlc.md) |
| Rejestry decyzji umierają, bo zapis to dodatkowa praca; zapis w miejscu decyzji, jednym kliknięciem, z gotowym szkicem, celuje w tę barierę | [analiza konkurencji](10-analiza-konkurencji.md), U8 |
| Jedynym wyróżnikiem w testach była pamięć uzasadnienia (liczby, założenia, warunki) — trzeba ją złapać w chwili decyzji | [test v2](../eval/v2-pamiec-decyzji/wyniki/raport.md), [dokument 12](12-zmiana-kierunku-sdlc.md) |
| Wartość od razu i bez zależności — nie trzeba czekać na zmiany w tf, ci_for_sdlc i ShipScope (F3 planu) | zmiana kolejności (§7) |
| Najtańsza walidacja: właściciel projektu jest pierwszym użytkownikiem | protokół w §6 |

## 3. Architektura

```
  Claude CLI ──┐ (MCP: record_decision, find_decisions; komenda /record-decision)
  Claude.ai ───┤ (ten sam serwer MCP jako zdalny connector)          ── etap 2+
  Slack ───────┤ (skrót na wiadomości „Record decision”)              ── etap 3
  Confluence ──┤ (rozszerzenie przeglądarki albo aplikacja Forge)     ── etap 4
  Jira ────────┘
               │
               ▼
     pdi: rejestr decyzji  ◄── flow SDLC (F3+): triaż, bramki, ocena skutku
     jeden schemat (contract/decision), jedno ID (DEC-n)
               │
               ▼
     odczyt: find_decisions — Claude sprawdza wcześniejsze decyzje przed propozycją
```

**Zasady:**

- **Jeden schemat i jedno API** dla wszystkich punktów zapisu i dla flow SDLC.
- **AI szkicuje, człowiek zatwierdza.** Zapis tylko na wyraźne żądanie — AI nie decyduje samo, co jest decyzją.
- **Źródło zawsze podlinkowane** (wątek Slacka, strona Confluence, sesja Claude) — decyzja bez kontekstu jest bezużyteczna.
- **Koszt zapisu bliski zera:** cel ≤ 60 s od kliknięcia do zapisu.
- **Zgodność z R1** ([dokument 13](13-rola-pdi-w-sdlc.md#4-rozbieżności-między-wersjami-mapy-i-planem--do-rozstrzygnięcia)): decyzje niezwiązane ze zmianą są w pdi; decyzja o konkretnej zmianie (`CHG-n`) dostaje link, a dla zmiany źródłem prawdy pozostaje repo. pdi indeksuje wszystkie.

## 4. Pierwszy krok (MVP) — specyfikacja

> **Zbudowane 2026-10-23** ([plan i ustalenia](plan-krok-1.md)): `contract/decision.schema.json`, `src/pdi/` (rejestr, serwer MCP), [`integrations/claude-code/`](../integrations/claude-code/README.md). Następny krok: utworzenie repo rejestru i walidacja (§6).

### 4.1. Schemat decyzji (`contract/decision.schema.json`)

Pierwszy schemat kontraktu (F0). Pola z [dokumentu 12 §4.1](12-zmiana-kierunku-sdlc.md#41-schemat-decyzji-w-contract-f0-uzupełnienie-d2), w wersji minimalnej dla trybu standalone:

| Pole | Wymagane | Znaczenie |
|---|---|---|
| `id` | tak | `DEC-n`, nadawane przez rejestr |
| `statement` | tak | co zdecydowano, jedno zdanie |
| `why` | tak | uzasadnienie, 1–5 zdań |
| `decided_at`, `decided_by` | tak | kiedy i kto |
| `kind` | tak | `product` / `technical` / `process` / `triage` / `intent` / `gate` / … |
| `source` | tak | `{kind: claude-cli \| claude-ai \| slack \| confluence \| jira \| manual, url, excerpt}` |
| `options[]` | nie | rozważane opcje, wybrana oznaczona |
| `evidence[]` | nie | `{text, source_url, epistemic_status: observation \| interpretation \| hypothesis \| ai_inference}` |
| `assumptions[]` | nie (zalecane dla `product`/`intent`) | `{statement, load_bearing, invalidated_if}` |
| `dependencies[]` | nie | systemy, dostawcy, zespoły, rynki |
| `success_metric` | nie | metryka, wartość docelowa, horyzont |
| `review_by` | nie | data przeglądu |
| `status` | tak | `recorded` / `superseded` / `reverted` |
| `supersedes`, `superseded_by` | nie | zastępowanie zamiast nadpisywania |
| `links` | nie | `{prb, chg, tsk, pr, adr}` — powiązanie z flow SDLC |
| `tags[]` | nie | obszar, projekt |
| `drafted_by` | tak | `ai` / `human` — kto przygotował szkic (decyduje zawsze człowiek) |

### 4.2. Przechowywanie

**Rekomendacja na start: pliki markdown z frontmatterem YAML w prywatnym repo git** (np. `decisions/DEC-0001.md`).

- zero infrastruktury, pełna historia w gicie, wyszukiwanie `grep`-em;
- ten sam format co wpisy `changes/CHG-n/decisions.md` w tf → jedna konwencja dla obu światów (R1);
- migracja do usługi z bazą (Postgres, wielu użytkowników — D5) dopiero, gdy pojawi się Slack lub drugi użytkownik.

### 4.3. Serwer MCP pdi (lokalny, stdio)

| Narzędzie | Wejście | Wynik |
|---|---|---|
| `record_decision` | pola schematu bez `id`; `source` wypełnione przez klienta | `DEC-n`, ścieżka pliku; walidacja względem schematu |
| `find_decisions` | `query`, opcjonalnie `tags`, `since`, `status`, `kind` | lista: `id`, `statement`, `why`, `decided_at`, założenia nośne |
| `get_decision` | `id` | pełny wpis |
| `supersede_decision` | `id` starej + pola nowej | nowa decyzja, stara ze statusem `superseded` |

Język: **Python** z oficjalnym SDK MCP (przyjęte 2026-10-23, [decyzje](decyzje.md)). Kod serwera żyje w repo pdi; ścieżkę do rejestru podaje zmienna środowiskowa (np. `PDI_REGISTRY_PATH`), więc testy działają na katalogu tymczasowym, a nie na prawdziwym rejestrze.

### 4.4. Komenda w Claude Code: `/record-decision`

Zachowanie:

1. Z bieżącej rozmowy wyciąga: co zdecydowano, dlaczego, jakie były opcje, na jakich dowodach i założeniach (z oznaczeniem, co jest obserwacją, a co hipotezą).
2. Jeśli brakuje założenia nośnego dla decyzji produktowej — zadaje **najwyżej 2 pytania**.
3. Pokazuje szkic w zwięzłej formie.
4. Zapisuje (`record_decision`) **dopiero po wyraźnym potwierdzeniu**; poprawki w jednym kroku.
5. Zwraca `DEC-n` i link.

### 4.5. Odczyt w trakcie pracy

Fragment `CLAUDE.md` / skill: „zanim zaproponujesz rozwiązanie w obszarze, który mógł być już rozstrzygnięty, wywołaj `find_decisions`; jeśli propozycja przeczy wcześniejszej decyzji — powiedz to wprost i zaproponuj `supersede_decision` zamiast cichej zmiany kursu”.

## 5. Kolejne punkty zapisu

| Etap | Punkt zapisu | Wymaga |
|---|---|---|
| 2 | Claude.ai / desktop — ten sam serwer MCP jako zdalny connector | hostowany serwer MCP (HTTP) |
| 3 | Slack — skrót na wiadomości; AI czyta wątek i wypełnia formularz; zapis z linkiem do wątku | aplikacja Slack, hostowany pdi (D5), zgoda na przetwarzanie treści wątku |
| 4 | Confluence, Jira (i każda inna strona) — rozszerzenie przeglądarki: zaznacz → zapisz; ewentualnie aplikacja Forge | rozszerzenie albo Forge |
| 5 | E-mail — przekazanie na adres rejestru | skrzynka i parser |
| później | Strażnik podstaw: porównywanie nowych informacji z `invalidated_if` (zdarzenie `decision.basis_invalidated`) | źródła informacji; polityka uwagi ([05](05-attention-intelligence.md)) |

Każdy kanał to osobna integracja do utrzymania — kolejny etap tylko wtedy, gdy poprzedni jest używany (§6).

## 6. Walidacja: dwa tygodnie na sobie (kryteria zapisane przed startem)

Po zbudowaniu kroku 1 (§4) właściciel projektu używa pdi przez **10 dni roboczych** w normalnej pracy. Notatka dzienna w `eval/dogfood/` (bez treści poufnych): liczba zapisów, czas zapisu, liczba poprawek szkicu, przypadki użycia `find_decisions`, zapisy porzucone.

| Kryterium | Spełnione, jeśli… |
|---|---|
| **W1 — zapis jest naturalny** | ≥ 5 decyzji tygodniowo zapisanych bez przymusu |
| **W2 — zapis jest tani** | mediana czasu od komendy do zapisu ≤ 60 s; ≥ 70% szkiców zatwierdzonych z najwyżej jedną poprawką |
| **W3 — odczyt ma wartość** | ≥ 2 sytuacje, w których `find_decisions` przypomniało decyzję, która zmieniła lub potwierdziła bieżącą pracę |
| **W4 — szkic jest uczciwy** | w szkicach nie pojawiają się zmyślone uzasadnienia ani założenia (sprawdzane przy zatwierdzaniu; każdy przypadek zapisany) |

| Wynik | Co dalej |
|---|---|
| W1–W4 spełnione | etap 2–3 (Claude.ai, Slack); ewentualnie pierwsza osoba z zespołu |
| W1 niespełnione | zapis nie jest naturalny nawet dla autora — poprawić moment i formę (np. sugestia zapisu na końcu sesji) zanim pójdziemy dalej |
| W2 niespełnione | szkic za słaby albo za długi — poprawić komendę, nie dokładać kanałów |
| W3 niespełnione | rejestr jest „pisany, nie czytany” — wzmocnić odczyt (§4.5) albo przemyśleć wartość |
| W4 niespełnione | zaostrzyć zasady szkicu (statusy epistemiczne, pytania zamiast domysłów) — bez tego rejestr traci wiarygodność |

## 7. Zmiana kolejności w planie jednego flow

| Faza planu | Było | Jest |
|---|---|---|
| F0 | kontrakt (wszystkie schematy) | **najpierw schemat decyzji** (§4.1), potem pozostałe |
| **nowa: F0+ (pdi standalone)** | — | rejestr (§4.2), serwer MCP (§4.3), `/record-decision` (§4.4), walidacja na sobie (§6). **Nie zależy od tf, ci_for_sdlc ani ShipScope** — może iść równolegle z F0 w tf i F1 |
| F3 (pdi MVP) | intake, triaż, rejestr decyzji, przyjęcie do budowy | rejestr **już jest**; F3 dokłada intake i triaż, które zapisują decyzje przez to samo API |
| F4–F5 | skrzynka bramek, ocena skutku | bez zmian; korzystają z rejestru |

## 8. Ryzyka

| Ryzyko | Ograniczenie |
|---|---|
| Szum: zapisywanie drobiazgów | zapis tylko na żądanie; `kind` i tagi do filtrowania |
| Zmyślone uzasadnienia w szkicu AI | statusy epistemiczne; pytania zamiast domysłów; W4 |
| Poufność (Slack, Confluence → pdi → model AI) | etap 1 lokalnie; od etapu 3 uprawnienia, zgoda organizacji, warunki dostawcy modelu |
| Koszt utrzymania integracji przy jednej osobie | kolejny kanał tylko po spełnieniu W1–W3 na poprzednim |
| Rozjazd z rejestrem w repo zmian (R1) | jeden format markdown + frontmatter; pdi indeksuje wpisy z `changes/*/decisions.md` przez link |

## 9. Decyzje do podjęcia przed budową

1. ~~**D1**~~ — przyjęte 2026-10-23: kontrakt w `pdi/contract/` ([decyzje](decyzje.md)); R1 też przyjęte.
2. ~~Miejsce rejestru~~ — przyjęte 2026-10-23: **osobne prywatne repo** (np. `pdi-decisions`). Tworzymy je, gdy serwer MCP i `/record-decision` przejdą testy na katalogu tymczasowym — tuż przed pierwszym dniem walidacji (§6). Wcześniej nie jest potrzebne.
3. ~~Język serwera MCP~~ — przyjęte 2026-10-23: **Python**.
4. ~~Pola schematu~~ — przyjęte 2026-10-23: zgodnie z §4.1.

Wszystkie decyzje blokujące krok 1 są podjęte; można budować.
