# Automatyzacja i konsola — plan

Data: 2026-10-25 · Status: **w realizacji** — A0, A1, A3 i A6 zrobione, A2, A4, A5, A7, A8 i konsola (K-1–K-4) do zrobienia (stan w §8); DA1 i DA2 przyjęte, DA3–DA6 otwarte

Gdzie jeszcze zautomatyzować workflow od pomysłu do wdrożenia i jak dać człowiekowi jedno miejsce, w którym widzi,
co się dzieje, i podejmuje decyzje tak jak w rozmowie z Claude. Uzupełnia [plan jednego flow](plan-jeden-flow-sdlc.md)
(krok A1 to jego faza F4) i [plan G1/G2](plan-g1-g2.md).

## 1. Zasady

| Zasada | Co oznacza w praktyce |
|---|---|
| **Najpierw spoiwo** | Automatyzujemy przenoszenie pracy między aplikacjami. Nikt nie traci kontroli, znika ręczne przechodzenie z Jiry do ci_for_sdlc, z Claude do GitHuba i do ShipScope. |
| **AI przygotowuje, człowiek zatwierdza** | Każda decyzja przychodzi do człowieka z rekomendacją, dowodami i konsekwencjami. Człowiek klika albo pisze, nie składa materiału. |
| **Autonomia zdobywana na danych** | Każdy typ decyzji startuje na poziomie 3 (decyduje człowiek). Niżej schodzi dopiero wtedy, gdy dane pokazują, że człowiek zatwierdza szkice AI bez zmian. Gdy odsetek zmian rośnie, typ wraca do człowieka. |
| **Nie automatyzujemy wartości ani nieodwracalnego** | Triaż (czy to robimy), zakres MVP, ocena skutku, wydanie zmiany wysokiego ryzyka, migracje danych, merge kodu z auth, płatnościami, IaC zawsze zostają u człowieka. |

## 2. Decyzje do podjęcia

| ID | Pytanie | Rekomendacja | Dlaczego |
|---|---|---|---|
| DA1 | Czy poziomy autonomii wchodzą do kontraktu | **Tak**, kontrakt 0.5.0 | wszystkie aplikacje muszą wiedzieć, czy decyzję podjął człowiek, reguła czy automat z wetem |
| DA2 | Próg obniżenia poziomu | **≥ 95% szkiców zatwierdzonych bez zmian w ostatnich 30 decyzjach danego typu**; obniżenie zawsze jako decyzja człowieka | jedna liczba, łatwa do sprawdzenia; człowiek nadal decyduje o samej automatyzacji |
| DA3 | Gdzie żyje konsola | **W pdi** (jego interfejs), nie jako szósty produkt | pdi i tak posiada skrzynkę bramek, rejestr decyzji i graf śladu; panel w Jirze (G2.5) zostaje wejściem z Jiry |
| DA4 | Stack usługi pdi (D5 z planu jednego flow) | **TypeScript + Fastify + Postgres** z wzorcami ShipScope; serwer MCP zostaje w Pythonie | rekomendacja z planu jednego flow; logowanie przez GitHub App, wielu klientów z RLS i szyfrowanie tokenów są już sprawdzone w ShipScope |
| DA5 | Czy rozmowa w konsoli może zatwierdzać decyzje | **Tylko z jawnym potwierdzeniem** (przycisk w karcie decyzji), nigdy samym tekstem | tekst z Jiry czy Confluence w kontekście rozmowy może zawierać polecenia; zatwierdzenie musi być osobnym gestem człowieka |
| DA6 | Kto wykonuje zmianę etapu flagi | **Adapter dostawcy flag albo PR do pliku flag przez tf**; ShipScope tylko obserwuje | ShipScope z założenia nie zmienia flag (ADR-001: flagi są do niego wypychane) |

## 3. Model: poziomy autonomii (kontrakt 0.5.0)

| Poziom | Nazwa | Co się dzieje |
|---|---|---|
| 3 | człowiek | decyzja czeka w skrzynce; bez kliknięcia nic się nie dzieje |
| 2 | automat z wetem | automat przygotowuje decyzję i wykona ją po oknie weta (np. 4 h); człowiek widzi ją w skrzynce i może zatrzymać |
| 1 | automat z logiem | automat wykonuje od razu; wpis w rejestrze i w osi zdarzeń konsoli |
| 0 | automat po cichu | tylko dla czynności bez skutków dla produktu (np. ponowienie synchronizacji) |

Zmiany w `pdi/contract/`:

| Plik | Zmiana |
|---|---|
| `autonomy.schema.json` (nowy) | polityka organizacji: `decision_type` → `level` (0–3), `veto_window`, `rule` (warunek, np. „kryteria wyjścia spełnione i `min_days` minęło”), `lower_when` (próg z DA2), `raise_when` (np. odsetek zmian > 10%) |
| `decision.schema.json` | `decision_type` (stały klucz, np. `flag.stage_advance`, `ac.format_rewrite`, `finding.auto_close`); `automation` (`level`, `rule`, `veto_until`, `vetoed_by`); `draft_edited` (czy człowiek zmienił szkic AI) — razem z istniejącym `drafted_by` daje odsetek akceptacji; w `source.kind` nowa wartość `console` |
| `event.schema.json` | `decision.proposed` (pozycja w skrzynce), `decision.auto_applied`, `decision.vetoed`, `run.progress` (postęp pracy agenta: faza, kawałek, koszt) |
| `contract.json`, `README.md` | wersja 0.5.0, katalog typów decyzji z domyślnym poziomem 3 |

Typy decyzji na start (wszystkie poziom 3):

| `decision_type` | Kandydat do obniżenia, gdy |
|---|---|
| `finding.auto_close` | odpowiedź na pytanie ci_for_sdlc znaleziona w źródle, z cytatem |
| `ac.format_rewrite` | propozycja zmienia tylko format AC (GWT), nie treść |
| `flag.stage_advance` | kryteria wyjścia z `release.yaml` spełnione, `min_days` minęło, metryki ochronne w normie |
| `flag.removal_pr` | flaga na 100% dłużej niż X dni |
| `dependency.update` | patch/minor z zielonym CI |
| `review.light` | mała zmiana (testy, dokumentacja, drobne poprawki), zielone CI i AI review, zasięg poza listą wrażliwych obszarów |

Typy, które **nie** dostają poziomu poniżej 3: `triage`, `scope.r1`, `release.go`, `outcome.assessment`,
`review.sensitive`, `migration`.

## 4. Kroki automatyzacji

| Krok | Repo | Co | Zależy od | Działa po kroku |
|---|---|---|---|---|
| A0 | pdi | Kontrakt 0.5.0 z §3; walidacja w `src/pdi/contract.py`, przykłady, testy | — | wszystkie aplikacje mają wspólny język dla autonomii i zdarzeń konsoli |
| A1 | pdi + tf | **Orkiestrator i skrzynka bramek** (faza F4): maszyna stanów per CHG w usłudze pdi; `gate.decided` uruchamia następną fazę tf bez interakcji (`tf run <persona> --change CHG-n --phase …` albo agent z targetu `managed-agents` w `build.py`); gotowość 🟢 i stan bazowy w ci_for_sdlc uruchamiają Talosa z budżetem; `feature.released` uruchamia licznik oceny skutku | DA4, F4 w tf | człowiek klika tylko na bramkach; kolejne fazy startują same |
| A2 | ci_for_sdlc | **Automatyczne zamykanie pytań z cytatem**: gdy odpowiedź jest w Confluence, Figmie albo we wcześniejszej decyzji, finding dostaje stan `resolved` z dowodem i znacznikiem „zamknięte automatycznie” (rozszerzenie dzisiejszego „answered by source” z adversarial review na wszystkie findings). Polityka `autoClose: off \| suggest \| apply`, domyślnie `suggest`. Lista „Zamknięte automatycznie” z przyciskiem „Otwórz ponownie” | A0 | PO odpowiada tylko na pytania, na które naprawdę nie ma odpowiedzi |
| A3 | pdi | **Licznik akceptacji szkiców**: w `src/pdi/stats.py` odsetek decyzji zatwierdzonych bez zmian per `decision_type`; narzędzie MCP `autonomy_report`; propozycja obniżenia poziomu jako decyzja do skrzynki (sama zmiana poziomu też jest decyzją człowieka) | A0 | wiadomo, które decyzje są gotowe do automatyzacji, zanim cokolwiek zostanie zautomatyzowane |
| A4 | ShipScope + tf + pdi | **Udostępnianie flag według reguły**: ShipScope wykrywa „kryteria wyjścia spełnione” na podstawie `release.yaml` i stanu flagi → `decision.proposed` typu `flag.stage_advance`; wykonawca z DA6 zmienia etap; przekroczenie metryk ochronnych → propozycja cofnięcia z poziomem 1. Flaga na 100% przez X dni → Talos otwiera PR usuwający flagę (`flag.removal_pr`) | A1, G1.3, źródło metryk ochronnych (luka G5) | flagi przechodzą etapy i znikają z kodu bez pamiętania o tym |
| A5 | pdi | **Decyzje ze spotkań i Slacka** ([dokument 14](14-pdi-standalone.md), etapy 2–3): z transkrypcji i wątków szkic `DEC-n` z cytatem do zatwierdzenia w skrzynce | A1 | decyzje nie giną w rozmowach |
| A6 | pdi + tf | **Triaż z grupowaniem** (faza F3): zgłoszenia z supportu i feedbacku grupowane w jedno `PRB` z liczbą zgłoszeń jako dowodem; rekomendacja z `proc-issue-triage` | F3 | PO decyduje na podstawie zebranych dowodów, nie pojedynczych ticketów |
| A7 | tf + ci_for_sdlc | **Review w trybie uproszczonym** (`review.light`): AI review według `REVIEW.md`, zielone CI, lista wrażliwych ścieżek (auth, płatności, migracje, IaC) wyklucza zmianę z trybu | F6, działające GitHub Actions | człowiek przegląda uważnie tylko zmiany, które tego wymagają |
| A8 | konektory | **Lustro Jira ↔ repo** (P2 z planu G1/G2): zatwierdzona zmiana w repo aktualizuje historyjkę w Jirze i odwrotnie | F1, F2, DG3 | koniec ręcznego przepisywania między Jirą a repo |

## 5. Konsola: wspólny interfejs

### 5.1. Co widzi i robi człowiek

Jedna aplikacja w przeglądarce, w trzech częściach:

| Część | Co pokazuje | Co można zrobić |
|---|---|---|
| **Teraz** | oś zdarzeń na żywo: Talos na kawałku K2 z 4 przy CHG-12 (koszt 1,40 USD), ci_for_sdlc analizuje PAY-140, flaga `payment-retry` od 5 dni na 10%, przebiegi agentów w toku | wejść w zmianę i zobaczyć jej graf śladu: PRB → CHG → US/AC → TSK → PR → wdrożenie → etap flagi → skutek |
| **Skrzynka** | decyzje czekające na człowieka, posortowane według pilności: bramki, pytania z ci_for_sdlc, propozycje podziału, etapy flag, oceny skutku; każda z rekomendacją AI, dowodami i konsekwencjami | zatwierdzić, wybrać inną opcję, odrzucić z powodem, odłożyć; przy poziomie 2 zatrzymać automat przed końcem okna weta |
| **Rozmowa** | Claude z dostępem do wszystkich aplikacji przez MCP: wyjaśnia, porównuje, szkicuje, odpowiada na „dlaczego”, tak jak w tej rozmowie | dopytać („co się stanie, jeśli przesuniemy PAY-142 do R2?”), poprosić o szkic decyzji albo zmiany; zatwierdzenie zawsze przyciskiem w karcie decyzji (DA5) |

Rozmowa i skrzynka są połączone: Claude w rozmowie przygotowuje kartę decyzji, a człowiek zatwierdza ją w skrzynce.
Decyzja trafia do rejestru z `source.kind: console` i linkiem do rozmowy.

### 5.2. Jak to działa

| Element | Skąd | Uwagi |
|---|---|---|
| Oś zdarzeń | zdarzenia z kontraktu (`gate.*`, `readiness.changed`, `feature.released`, `release.stage_changed`, `decision.*`, `run.progress`) | ci_for_sdlc ma dziś wewnętrzne SSE `/api/events` (do wyprowadzenia jako webhooki w F3); tf zapisuje postęp w `run_report.py` (do wysyłania jako `run.progress`); ShipScope wysyła zdarzenia od F5 |
| Skrzynka | usługa pdi (A1) | jedno źródło pozycji „czeka na Ciebie” dla konsoli, panelu w Jirze i powiadomień w Slacku |
| Rozmowa | model Claude przez API z narzędziami MCP | pdi ma już serwer MCP (decyzje); potrzebne serwery MCP dla ci_for_sdlc (nad istniejącym REST API) i ShipScope (nad API usług z F5) oraz narzędzia skrzynki w pdi (`inbox_list`, `propose_decision`) |
| Agenci | tf lokalnie albo jako Claude Managed Agents (target `managed-agents` w `build.py` tf) | konsola pokazuje ich przebiegi i pozwala zatrzymać przebieg |
| Logowanie i uprawnienia | wzorce ShipScope (GitHub App, wielu klientów z RLS) | rola decyduje, kto zatwierdza który typ decyzji |

### 5.3. Etapy konsoli

| Etap | Co | Zależy od | Działa po etapie |
|---|---|---|---|
| K-1 | **Claude jako interfejs już teraz**: serwery MCP dla ci_for_sdlc i ShipScope obok istniejącego serwera pdi; w Claude (claude.ai albo Claude Code) człowiek pyta o stan i podejmuje decyzje w rozmowie, jak dziś | — | jedna rozmowa widzi wszystkie aplikacje; bez nowego UI |
| K-2 | **Skrzynka i oś zdarzeń** w usłudze pdi, bez rozmowy | A0, A1 | jedna lista „czeka na Ciebie” i widok tego, co się dzieje na żywo |
| K-3 | **Rozmowa wbudowana w konsolę**: panel rozmowy z tymi samymi narzędziami MCP; karty decyzji z rozmowy trafiają do skrzynki | K-1, K-2 | pełne doświadczenie: widzę, pytam, decyduję w jednym miejscu |
| K-4 | **Graf śladu** jako widok zmiany i panel w Jirze (G2.5) korzystający z tej samej skrzynki | K-2, tryb SaaS | ta sama skrzynka w konsoli, w Jirze i w Slacku |

K-1 daje większość wartości od razu i sprawdza, które pytania i decyzje ludzie faktycznie zadają, zanim powstanie
interfejs. Etap K-3 warto budować dopiero, gdy K-1 pokaże, że rozmowa jest głównym sposobem pracy.

## 6. Kolejność

| Fala | pdi | ci_for_sdlc | ShipScope | tf |
|---|---|---|---|---|
| 1 | A0 kontrakt 0.5.0 | K-1 serwer MCP | K-1 serwer MCP | |
| 2 | A3 licznik akceptacji | A2 zamykanie pytań z cytatem | | |
| 3 | A1 orkiestrator i skrzynka (F4), K-2 | | | F4 uruchamianie bez interakcji |
| 4 | K-3 rozmowa w konsoli, A5 | | A4 wykrywanie kryteriów wyjścia | A4 PR usuwający flagę |
| 5 | A6 (F3), K-4 | A7 (po F6) | | A7, A8 |

Przed falą 3 trzeba naprawić GitHub Actions (płatności na koncie): orkiestrator uruchamia fazy w CI, a tryb
uproszczonego review zakłada zielone CI.

## 7. Ryzyka

| Ryzyko | Skutek | Co robimy |
|---|---|---|
| Automat podejmuje złą decyzję w powtarzalnym typie | błędna zmiana bez wiedzy człowieka | start na poziomie 3, obniżanie tylko na danych (DA2), automatyczny powrót na wyższy poziom, okno weta na poziomie 2, każda decyzja automatu w rejestrze |
| Polecenia ukryte w treści z Jiry lub Confluence trafiają do rozmowy | Claude próbuje wykonać coś, czego człowiek nie chciał | treść źródeł jako dane, nie polecenia (jak w ci_for_sdlc); zatwierdzenie tylko przyciskiem (DA5); narzędzia rozmowy nie mają uprawnień do zatwierdzania |
| Zautomatyzowanie przed zmierzeniem | automatyzujemy decyzje, których ludzie i tak nie akceptują | A3 przed A4 i A7; najpierw dane, potem automatyzacja |
| Konsola jako kolejny interfejs | ludzie nie przenoszą się z Jiry i Slacka | K-1 bez nowego UI; skrzynka widoczna też w Jirze i Slacku (K-4) |
| Koszt rozmowy i agentów | rosnące rachunki za API | budżet per zmiana (mechanizm `--budget` Talosa), koszt w osi zdarzeń i w grafie śladu |
| Etap flagi bez wiarygodnych metryk ochronnych | automat przesuwa flagę na podstawie niepełnych danych | A4 dopiero ze źródłem metryk (luka G5); do tego czasu `flag.stage_advance` zostaje na poziomie 3 |

## 8. Stan realizacji

Stan na 2026-10-26, sprawdzony na gałęziach `main` wszystkich repozytoriów.

| Krok | Stan | Gdzie | Uwagi |
|---|---|---|---|
| A0 kontrakt 0.5.0 | zrobione | pdi #24 | [plan A0](plan-a0-kontrakt-050.md) |
| A1 orkiestrator i skrzynka (F4) | zrobione | pdi #15–#17; tf #79; ci_for_sdlc #66 | maszyna stanów per CHG, fazy tf bez interakcji, zatwierdzenie w ci_for_sdlc z bramek pdi |
| A2 zamykanie pytań z cytatem | do zrobienia | | ci_for_sdlc |
| A3 licznik akceptacji szkiców | zrobione | pdi #27 | [plan A3](plan-a3-licznik-akceptacji.md) |
| A4 flagi według reguły | do zrobienia | | potrzebuje źródła metryk ochronnych (luka G5); do tego czasu `flag.stage_advance` zostaje na poziomie 3 |
| A5 decyzje ze spotkań i Slacka | do zrobienia | | |
| A6 triaż z grupowaniem (F3) | zrobione | pdi #23; tf #82 | duplikaty i rekomendacja triażu w stanach pdi |
| A7 review uproszczone | do zrobienia | | AI review w CI jest (tf #86); brakuje trybu `review.light` i listy wrażliwych ścieżek; wymaga działającego CI |
| A8 lustro Jira ↔ repo | do zrobienia | | |
| K-1 Claude jako interfejs | do zrobienia | | serwer MCP pdi jest (także skrzynka: `list_inbox`, `decide_inbox_item`); brakuje serwerów MCP dla ci_for_sdlc i ShipScope (ShipScope ma API usług, #110) |
| K-2 skrzynka i oś zdarzeń w UI | do zrobienia | | skrzynka i graf śladu są w pdi po stronie danych; brakuje interfejsu |
| K-3 rozmowa w konsoli | do zrobienia | | |
| K-4 graf śladu i panel w Jirze | do zrobienia | | makieta ekranów: [`design/konsola/`](../design/konsola/README.md) |
