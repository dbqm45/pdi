# 13. Rola pdi w procesie SDLC

**Data:** 2026-10-23 · **Źródła:** [plan jednego flow](plan-jeden-flow-sdlc.md), [wczesne etapy rozmowy](zrodla/2026-10-23-wczesne-etapy-rozmowy.md), [mapa procesu — wersje 1 i 2](zrodla/2026-10-23-mapa-sdlc.md), [kontekst rozmowy](kontekst-rozmowy.md), [dokument 12](12-zmiana-kierunku-sdlc.md)

## 1. Rola w jednym zdaniu

> **pdi odpowiada na pytanie „co, czy i dlaczego?”** — przyjmuje problemy, prowadzi ludzi przez decyzje na bramkach, pamięta te decyzje i ich uzasadnienie, uruchamia kolejne etapy i pokazuje ślad od zgłoszenia do skutku na produkcji. **Nie wykonuje pracy** — pisanie i analizę robi tf, spójność sprawdza ci_for_sdlc, status wydania liczy ShipScope.

Kluczowa zmiana między wersjami mapy: po przejrzeniu tf okazało się, że tf ma już cykl, bramki, dziennik, triaż i planowanie. Dlatego pdi jest **cienkie**: UI dla ludzi, decyzje, orkiestracja i ślad.

## 1a. Zasady, z których wyrosła ta rola

Z [wczesnych etapów rozmowy](zrodla/2026-10-23-wczesne-etapy-rozmowy.md) — obowiązują dalej i tłumaczą, dlaczego pdi ma być cienkie:

| Zasada | Konsekwencja dla pdi |
|---|---|
| **Orkiestrator nad łańcuchem artefaktów w gicie**, nie jedna duża aplikacja | pdi nie przechowuje artefaktów zmian; czyta je z repo |
| **Źródłem prawdy jest repo; bramka to PR** | na start bramki to zwykłe PR-y — pdi nie musi mieć własnego UI, żeby proces działał |
| **Orkiestrator najpierw jako CLI; aplikacja pdi dopiero, gdy proces działa end-to-end** | kolejność budowy pdi: kontrakt → CLI/orkiestracja → UI (skrzynka bramek, graf) |
| **Zgłoszenia w bazie pdi, nie w gicie; do repo trafia dopiero zaakceptowana intencja** | pdi jest jedynym miejscem dla zgłoszeń i decyzji triażu (podstawa rekomendacji R1) |
| **Dwie bramki: tania (czy analizować?) i droga (czy budujemy?)** | triaż w pdi to decyzja tania i szybka; decyzja o budowie to akceptacja intencji (B1) |
| **Człowiek decyduje co i czy; agent — jak; deterministyczne checki — wynik** | pdi pokazuje człowiekowi tylko decyzje; wszystko inne idzie do agentów i skryptów |
| **Odrzucenie zawsze z powodem, wraca do zgłaszającego; „wydane” zamyka pętlę** | obowiązkowy powód z listy; powiadomienie po `feature.released`, nie po wdrożeniu za flagą |
| **Parked z progiem powrotu** (np. 3 nowe zgłoszenia albo incydent) | pdi pilnuje progów i samo wraca do odłożonych zgłoszeń |
| **Liczba zgłaszających to dowód** | duplikaty grupowane w jedno zgłoszenie z wieloma dowodami, nie zamykane |

## 2. Co pdi posiada, a co wywołuje

| pdi posiada (źródło prawdy) | pdi wywołuje (logika gdzie indziej) |
|---|---|
| Zgłoszenia `PRB` — zanim staną się zmianą; większość zostanie odrzucona, więc nie trafia do repo | wzbogacenie i rekomendacja triażu → tf `proc-issue-triage` + rekonstrukcja |
| Decyzje triażu i odrzucenia z powodem | szkic intencji, wymagań, architektury, planu → persony tf (fazy 0–6) |
| Skrzynka bramek: jedna lista „czeka na Ciebie” dla wszystkich bramek | kontrola spójności i pytania → ci_for_sdlc |
| Stan każdej zmiany w maszynie stanów (orkiestrator) | build → tf Talos |
| Graf śladu PRB → CHG → TSK → PR → wydanie → skutek | status wydania → ShipScope |
| Ocena skutku decyzji i powiadomienie zgłaszającego | pasma kontrolne → tf `control_band.py` |
| Kontrakt (`contract/`): schematy i ID wspólne dla czterech projektów (rekomendacja D1) | |

**Zasada z planu:** jeśli w pdi zaczyna powstawać kopia logiki tf, ci_for_sdlc albo ShipScope, brakuje API w tamtym projekcie.

## 3. Gdzie w procesie pojawia się pdi

Według wersji 2 mapy (numeracja etapów z mapy; bramki tf B1–B6):

| # | Etap | Rola pdi | Człowiek w pdi |
|---|---|---|---|
| 1a | Zgłoszenie problemu | **posiada** — Intake: format „kto nie może czego → skutek”, 3–5 pytań doprecyzowujących | zgłaszający |
| 1b | Pomysł (greenfield) | wejście → przekazuje do tf (`core-plan-interview`, `proc-product-discovery`) | autor |
| 2 | Wzbogacenie | **wywołuje** tf i ci_for_sdlc, pokazuje wynik | – |
| 3 | Triaż | **posiada** — skrzynka bramek, stany z `proc-issue-triage` | **[B]** PO |
| 4–6 | Brief, wymagania, architektura (B1–B3) | **orkiestruje** — uruchamia persony tf, zbiera bramki do skrzynki | **[B1–B3]** |
| 7 | Design | orkiestruje | **[B]** review designu |
| 8 | Kontrola spójności | pytania z ci_for_sdlc trafiają do skrzynki; „Approve for implementation” jako decyzja | **[B]** |
| 9–11 | Szkielet, build, review | orkiestruje; ślad przez dopisek w commitach | **[B]** merge (w GitHubie) |
| 12–13 | Gotowość i release (B4, B5) | bramki w skrzynce | **[B4, B5]** |
| 14 | Status wydania | słucha `feature.released` z ShipScope; aktualizuje graf śladu | **[B]** flaga (w ShipScope) |
| 15 | Utrzymanie i pętla | przyjmuje `metric.breached` jako nowy PRB; powiadamia zgłaszającego; **ocena skutku** po N dniach | **[B6]**, ocena skutku |

Około 8–10 decyzji człowieka na zmianę; wszystkie decyzyjne. pdi jest miejscem, gdzie ten człowiek je widzi i podejmuje — poza merge i flagą, które zostają w GitHubie i ShipScope.

## 4. Rozbieżności między wersjami mapy i planem — do rozstrzygnięcia

| # | Temat | Wersja 2 mapy | Plan jednego flow | Wpływ | Rekomendacja |
|---|---|---|---|---|---|
| **R1** | **Gdzie żyje rejestr decyzji** | `decisions.md` w repo w formacie tf (`D-xxx`) — „jeden rejestr decyzji dla całego procesu”; ci_for_sdlc zapisuje tam swoje decyzje | rejestr w pdi (`DEC-201`); tf i ci_for_sdlc trzymają lokalne wpisy z ID z pdi (D2) | **blokuje F0** (schemat decyzji, D2) | **Podział według życia decyzji:** decyzje o PRB (triaż, odrzucenia — te nigdy nie trafiają do repo) są w pdi; decyzje o zmianie (B1–B6, odpowiedzi na pytania ci_for_sdlc) mają **źródło prawdy w repo** `changes/CHG-n/decisions.md` — audyt w gicie i dostęp dla agentów; pdi **indeksuje** wszystkie (jedno ID `DEC-n`, odczyt z repo), liczy dług decyzyjny i ocenia skutek. Zgodne z zasadą planu „od przyjęcia źródłem prawdy jest repo” |
| **R2** | Format ID decyzji | `D-001` (tf, numeracja per projekt) | `DEC-201` (globalny, kształt Jiry) | D3 | `DEC-n` globalny; w `decisions.md` tf pole `id: DEC-n` zamiast lokalnego `D-xxx` dla dziennika per zmiana — zmiana w `core-project-record` (F0 w tf) |
| **R3** | Dopisek w commitach | `Change: PRB-123` | `Change: TSK-57` | F1 | Jak w planie (`TSK`): ShipScope liczy TSK do rodzica CHG, a CHG ma `source: PRB` — ślad do zgłoszenia jest pełny bez wpisywania PRB w commitach |
| **R4** | Kto orkiestruje | pdi albo GitHub Actions | maszyna stanów w pdi + `workflow_dispatch` szablonu fazy z tf | F4 | Jak w planie: stan w pdi, wykonanie w GitHub Actions — pdi nie uruchamia agentów na swoich serwerach |
| R5 | Idea chat (greenfield) | wejście w pdi, logika w tf | brak modułu w tabeli pdi | kosmetyczny | dopisać do Intake jako drugi formularz; logika w tf |
| R7 | Statusy zgłoszenia | `needs-triage → needs-info → ready-for-agent / ready-for-human / wontfix` (tf `proc-issue-triage`) | wczesny etap: `New → Clarifying → Ready for triage → Accepted / Rejected / Parked / Duplicate`; plan: „stany z `proc-issue-triage`” | schemat problemu w F0 | Stany biznesowe z wczesnego etapu w pdi (`Parked` z progiem, `Duplicate`, `Rejected` z powodem z listy — tf tego nie ma); mapowanie na stany tf w kontrakcie, bo tf wykonuje wzbogacenie |
| R6 | Kolejność: kiedy pdi | krok 5 z 6 (po zmianach w tf, ci_for_sdlc i ShipScope) | kontrakt w pdi w F0, MVP pdi w F3 | brak | spójne: najpierw kontrakt (bez którego pozostałe zmiany są kruche), MVP pdi dopiero gdy ślad w repo działa |

R1 jest główną rozbieżnością merytoryczną. Wczesne etapy rozmowy ją wspierają: tam decyzje o zmianie lądują w repo (`decisions/*.md`), a zgłoszenia — w bazie pdi. Wpływa na propozycje z [dokumentu 12](12-zmiana-kierunku-sdlc.md#41-schemat-decyzji-w-contract-f0-uzupełnienie-d2): pola `assumptions`, `invalidated_if`, `success_metric` powinny być w nagłówku wpisu w `changes/CHG-n/decisions.md` (tam je szkicuje persona tf przy B1), a pdi czyta je do sprawdzania podstaw i oceny skutku.

## 5. Gdzie wnosi wcześniejsza praca koncepcyjna

Szczegóły: [dokument 12](12-zmiana-kierunku-sdlc.md). W skrócie, w kategoriach z sekcji 2:

| Co pdi posiada | Wkład wcześniejszej pracy |
|---|---|
| Decyzje (rejestr / indeks) | schemat z założeniami nośnymi i warunkami unieważnienia; zdarzenie `decision.basis_invalidated` — wynik testu v2 |
| Skrzynka bramek, powiadomienia | polityka uwagi: poziomy 0–3, deduplikacja, budżet, próg odchylenia — wynik testu v2 (wariant A+) |
| Ocena skutku | `success_metric` w decyzji o intencji; porównanie z danymi z ShipScope |
| Intake | drabina „najpierw sprawdź, czy odpowiedź już istnieje”; wzorce R1–R12 jako lista kontrolna dla skilla tf |

## 6. Decyzje do podjęcia (zebrane)

1. **D1–D3 z planu** — blokują F0.
2. **R1** — podział rejestru decyzji: PRB w pdi, zmiany w repo, pdi jako indeks. Od tego zależy, gdzie trafią pola z dokumentu 12 §4.1.
3. **R2** — globalne `DEC-n` także w dzienniku tf.
4. **R7** — statusy zgłoszenia w pdi (z `Parked` i `Duplicate`) i ich mapowanie na stany `proc-issue-triage`.
5. Propozycje z dokumentu 12: pola schematu decyzji (§4.1) i zdarzenie `decision.basis_invalidated` (§4.2).
6. Pierwszy krok budowy: **pdi standalone** — rejestr decyzji z zapisem z Claude CLI przez MCP, niezależny od tf, ci_for_sdlc i ShipScope ([dokument 14](14-pdi-standalone.md#9-decyzje-do-podjęcia-przed-budową)): miejsce rejestru na start, język serwera MCP, zakres pól schematu.
