# 12. Zmiana kierunku: pdi jako warstwa decyzji w jednym flow SDLC

**Data:** 2026-10-23 · **Status:** kierunek przyjęty przez właściciela (merge [planu jednego flow](plan-jeden-flow-sdlc.md)); propozycje w sekcji 4 czekają na akceptację

## 1. Co się zmieniło

| | Do 2026-10-22 | Od 2026-10-23 |
|---|---|---|
| Czym jest pdi | samodzielne narzędzie dla PM-a: analiza decyzji, potem „strażnik podstaw decyzji” ([decyzja 11](11-propozycja-wartosci.md)) | **warstwa decyzji** w jednym procesie AI-native SDLC razem z tf, ci_for_sdlc i ShipScope ([plan](plan-jeden-flow-sdlc.md)) |
| Zakres | model decyzji, wykrywanie ryzyk, zamykanie luk, pilnowanie podstaw, ochrona uwagi | zgłoszenia, triaż, rejestr decyzji, skrzynka bramek, orkiestracja, graf śladu, ocena skutku |
| Użytkownik | PM jako właściciel decyzji | PO/PM na triażu i bramkach, zgłaszający problem, ludzie na bramkach B1–B6 |
| Walidacja | design partnerzy z zewnętrznych firm | pilot na własnych problemach EV (F3 planu), przebieg próbny flow tf na samym pdi |
| Produkt czy narzędzie | otwarte, z rekomendacją w stronę narzędzia wewnętrznego ([test v2](../eval/v2-pamiec-decyzji/wyniki/raport.md)) | **narzędzie w ramach własnego flow**; usługa wielodostępna (D5) jako opcja techniczna |

Sesja, w której powstał plan jednego flow, zakładała, że repo pdi jest puste. Ten dokument łączy oba wątki.

## 2. Wcześniejsze wnioski są zgodne z nowym kierunkiem

| Wniosek z pracy koncepcyjnej | Jak wspiera plan jednego flow |
|---|---|
| Jednorazową analizę decyzji ogólny asystent AI robi równie dobrze jak specjalizowany prototyp ([test v1](../eval/status-zamowienia/wyniki/raport.md)) | Plan słusznie nie buduje w pdi logiki analizy: wzbogacenie i triaż wykonują skille tf („Czego pdi nie robi”) |
| Przewagę daje trwały model decyzji z liczbami i warunkami — bez niego asystent mówi tylko „sprawdź opłacalność” (test v2: 3/3 vs 0/3) | Rejestr decyzji w pdi (D2) jest właściwym miejscem na tę pamięć; to jest rdzeń, który odróżnia pdi od trackera |
| Szum ogranicza metoda (poziomy reakcji, „zbędne powiadomienie to błąd”), nie pamięć (test v2, wariant A+: 0 fałszywych alarmów) | Skrzynka bramek i powiadomienia potrzebują tej polityki od początku, inaczej człowiek na bramkach utonie |
| Rejestry decyzji, które wymagają ręcznego prowadzenia, nie są używane ([analiza konkurencji](10-analiza-konkurencji.md), U8) | W flow decyzje powstają jako skutek uboczny pracy (bramka = approve PR, triaż w pdi) — nikt nie „prowadzi rejestru” osobno |
| Przewaga jest technicznie prosta i łatwa do skopiowania (test v2) | Nie ma znaczenia przy narzędziu wewnętrznym; wartość leży w połączeniu z resztą flow, nie w samym mechanizmie |

## 3. Co przechodzi do nowego kierunku

| Element wcześniejszej pracy | Dokąd trafia | Faza planu | Co konkretnie |
|---|---|---|---|
| [Living Decision Model](02-living-decision-model.md) + [schemat](../model/living-decision-model.schema.json) | `contract/` — schemat decyzji (DEC) | F0 | pola z sekcji 4.1 |
| Strażnik podstaw decyzji ([11](11-propozycja-wartosci.md)) i Guardian z testu v2 | rejestr decyzji: obok „wykrywa decyzje sprzeczne z wcześniejszymi” — **„wykrywa informacje unieważniające podstawy decyzji”** | F5 (obok oceny skutku), zapis założeń już od F3 | zdarzenie z sekcji 4.2 |
| [Poziomy uwagi i reguły antyszumowe](05-attention-intelligence.md) | skrzynka bramek, powiadomienia | F4–F5 | poziomy 0–3, budżet uwagi, deduplikacja, format komunikatu „Co / Dlaczego / Wpływ / Pewność / Propozycja” |
| [Wzorce ryzyka R1–R12](03-decision-risk-radar.md) | skill tf używany przy wzbogaceniu i przeglądzie intencji (B1) — **nie kod pdi** | F3 | lista kontrolna dla persony szkicującej intencję |
| [Drabina zamykania luk](04-knowledge-gap-closure.md) | pytania doprecyzowujące w intake („najpierw sprawdź, czy odpowiedź już istnieje”) | F3 | reguła dla AI w intake |
| Ewaluacje v1 i v2 (klucz, warianty, sędzia, kryteria przed testem) | evale flow | F6 | wzorzec dla scenariuszy PRB → intent oraz „decyzja → nowa informacja → ostrzeżenie” |
| [Przykład roboczy](../examples/status-zamowienia.yaml), materiały z [eval/v2](../eval/v2-pamiec-decyzji/README.md) | dane testowe dla walidacji kontraktu i evali | F0, F6 | gotowe przypadki z decyzjami, założeniami i sygnałami |

**Wstrzymane:** pozyskiwanie zewnętrznych design partnerów ([outreach/](../outreach/profil-design-partnera.md)), plan etapów 0–6 z [dokumentu 08](08-plan-projektu.md). Materiały zostają w repo; mogą wrócić, jeśli po F5 pojawi się pytanie o użycie pdi poza własnym flow.

## 4. Propozycje do planu jednego flow (do akceptacji)

### 4.1. Schemat decyzji w `contract/` (F0, uzupełnienie D2)

Plan definiuje rdzeń decyzji: kto, kiedy, dlaczego, na jakich dowodach, jakie były opcje i czy przyniosła efekt. Proponuję dodać pola, bez których rejestr nie potrafi później ocenić, czy decyzja nadal ma podstawy:

| Pole | Znaczenie | Skąd |
|---|---|---|
| `kind` | `triage` / `intent` / `gate` / `answer` / `release` / `impact` | rozróżnienie decyzji merytorycznych od proceduralnych |
| `evidence[]` z `epistemic_status` (`observation` / `interpretation` / `hypothesis` / `ai_inference`) i `source` | czym jest każdy dowód i skąd pochodzi | [02 §2.1](02-living-decision-model.md#21-zasada-epistemiczna--najważniejsza-reguła-modelu) |
| `assumptions[]` z `load_bearing` i `invalidated_if` | założenia, a dla nośnych — warunek (najlepiej liczbowy), przy którym decyzja przestaje mieć sens | test v2: to pole dało wykrycie S1 |
| `dependencies[]` | systemy, dostawcy, rynki, zespoły, od których zależy decyzja | test v2: sygnały przychodziły z tych miejsc |
| `success_metric` | metryka z wartością docelową i horyzontem | wejście do oceny skutku (etap 14) |
| `supersedes` / `superseded_by` | zastępowanie zamiast nadpisywania | [02 §2.6](02-living-decision-model.md#26-model-żyje); plan: „wersje i zastępowanie” |
| `recommended_by` + `decided_by` | rozdzielenie rekomendacji AI od decyzji człowieka | plan: „AI rekomenduje, PO decyduje” |

**Ograniczenie, żeby nie powtórzyć błędu rejestrów decyzji:** `assumptions`, `dependencies` i `success_metric` wymagane tylko dla `kind: intent` (oraz opcjonalnie `triage` przy priorytecie) — tam, gdzie decyzja ma uzasadnienie merytoryczne. Decyzje bramek proceduralnych zostają krótkie. Wypełnienie szkicuje persona tf przy B1; człowiek tylko potwierdza.

### 4.2. Nowe zdarzenie w kontrakcie

| Zdarzenie | Wysyła | Odbiera | Po co |
|---|---|---|---|
| `decision.basis_invalidated` | pdi (rejestr decyzji) | skrzynka bramek pdi; tf (opcjonalnie nowy PRB) | nowa informacja (z `readiness.changed`, `metric.breached`, nowego PRB albo dokumentu) unieważnia `invalidated_if` decyzji `intent`; poziom 2–3 według polityki uwagi |

Źródła informacji, które rejestr porównuje z założeniami, są już w planie (zdarzenia z ci_for_sdlc i ShipScope, nowe zgłoszenia); nie trzeba nowych integracji, tylko porównania z założeniami zapisanymi w decyzji.

### 4.3. Polityka uwagi dla skrzynki bramek (F4)

Przenieść z [dokumentu 05](05-attention-intelligence.md): poziomy 0–3, łączenie powiązanych sygnałów, deduplikacja, budżet pozycji na osobę na tydzień, reakcja „trafne / nietrafne / już wiedziałem / bez znaczenia” jako dane do kalibracji. Test v2 pokazał też, że przy decyzjach z cienkim marginesem pamięć bez progu daje nadwrażliwość — próg odchylenia (np. poniżej X% założenia = poziom ≤ 1) powinien być częścią polityki.

## 5. Wpływ na otwarte decyzje D1–D7

| Decyzja | Rekomendacja planu | Wpływ wcześniejszej pracy |
|---|---|---|
| D1 kontrakt w `pdi/contract/` | tak | bez zmian; materiał testowy z `examples/` i `eval/v2` może służyć do testów walidacji |
| D2 rejestr decyzji w pdi | tak | **wzmacnia rekomendację**; proponowane pola w 4.1 |
| D3 format ID | kształt Jiry | bez zmian |
| D4–D7 | jak w planie | bez wpływu |

## 6. Co dalej

1. Zatwierdzić D1–D3 (blokują F0) oraz zdecydować, czy pola z 4.1 wchodzą do schematu decyzji w F0.
2. F0 w pdi: `contract/` ze schematami problem / zmiana / decyzja / zdarzenie — schemat decyzji na bazie [`model/living-decision-model.schema.json`](../model/living-decision-model.schema.json), uproszczony do pól z 4.1.
3. ~~Zdecydować, czy zdarzenie `decision.basis_invalidated` (4.2) dopisać do planu w F5.~~ Przyjęte 2026-10-23 (D-Z1 w [decyzjach](decyzje.md)); w kontrakcie 0.3.0.
