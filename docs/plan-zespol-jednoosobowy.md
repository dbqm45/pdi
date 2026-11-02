# Plan: zespół jednoosobowy — greenfield od wywiadu, brownfield od poznania projektu, wszystko w przeglądarce

Data: 2026-11-02 · Status: **plan; decyzje DZ1–DZ5 przyjęte 2026-11-02**, DZ1–DZ13 przyjęte, otwarte DA4 · Kolejność całości: §0 · Stan wyjściowy: pdi `d66b4bf`, tf 5.55.0,
ShipScope 0.2.67, ci_for_sdlc 0.1.35+ · Powiązane: [plan `sdlc up`](plan-sdlc-lokalnie.md),
[przebieg lokalny](przebieg-lokalny.md#wynik-przebiegu-2026-10-31), [etapy 2–18](polecenia-startowe-sdlc-lokalnie.md),
[automatyzacja i konsola](plan-automatyzacja-i-konsola.md), [jedna platforma](15-jedna-platforma.md)

## 0. Kolejność całości (stan 2026-11-02)

Jedna lista od teraz do końca planu: kroki Z1–Z9 i N1–N11 z tego planu oraz etapy 2–18 z
[poleceń startowych](polecenia-startowe-sdlc-lokalnie.md), po zmianie kolejności z DZ5. Kroki w jednym wierszu mogą iść
równolegle. „Bramka” to warunek przejścia do następnej grupy.

**A. Przed prawdziwym kodem (przed etapem 2)**

| # | Krok | Repo | Po czym | Polecenie startowe |
|---|---|---|---|---|
| A1 | Z1 — wszystkie decyzje zmiany w każdej fazie · Z8a — fazy w kontenerze · Z8c-1 — SARIF w ci_for_sdlc | pdi + tf · pdi + tf · ci_for_sdlc | — | [jest](polecenia-startowe-zespol.md) |
| A2 | Z8c-2 — skaner w pętli talosa i w CI, razem z N3 (jeden skrypt weryfikacji) i N10 (karencja dla nowych wersji zależności) | tf | Z8c-1 | [jest](polecenia-startowe-zespol.md) |
| A3 | N1 — przegląd drugim modelem · N5 — evale przebiegu (20 zadań) | tf | Z1 | [jest](polecenia-startowe-zespol.md) |
| A4 | Z7b-1 — cele zmiany (`targets`): proponowane w planie, zatwierdzane w B3, sprawdzane przed B4; razem z N4 (pokrycie i testy mutacyjne na zmienionym kodzie) | pdi + tf + ci_for_sdlc | Z1, Z8c-1 | [jest](polecenia-startowe-zespol.md) (Z7b-1a, Z7b-1b) |
| A5 | N2 — pętla budujący–recenzent na PR i samonaprawa CI | pdi + tf | Z8a, N1 | [jest](polecenia-startowe-zespol.md) |
| A6 | **Bramka:** ponowny przebieg lokalny na `sdlc-proba` w kontenerze, z jedną zmianą od zgłoszenia do oceny skutku; bez obejść z przebiegu 2026-10-31 | — | A1–A5 | lista: [przebieg lokalny](przebieg-lokalny.md) |
| A7 | **Etap 2** — scenariusz S5 na sprintdecku (prawdziwy kod i wdrożenie) | pdi + sprintdeck | A6 | [jest](polecenia-startowe-sdlc-lokalnie.md#etap-2--pdi--sprintdeck-scenariusz-s5-na-prawdziwym-wdrożeniu) |

**B. Przed produkcją (przed etapem 3)**

| # | Krok | Repo | Po czym | Polecenie startowe |
|---|---|---|---|---|
| B1 | Z2a — faza `discovery` i bramka B0 | pdi | Z1 | [jest](polecenia-startowe-zespol.md) |
| B2 | Z2b — wywiad `/discovery` w mode-pdi | tf | Z2a i tag kontraktu | jest |
| B3 | Z7b-2 — pętla ulepszeń: ocena skutku `not_met` albo wybicie metryki otwiera zmianę ponownie od wymagań albo architektury, z danymi z produkcji jako wejściem (DZ6: najwyżej 2 próby, potem człowiek) · Z7c + Z8d — pas governance (blokuje B5) i pakiet dowodów · Z8b — tożsamość agentów | pdi + tf + ci_for_sdlc | Z1 | do przygotowania |
| B4 | **Decyzja DA4** — stos usługi pdi | — | — | decyzja właściciela |
| B5 | Z3 — usługa pdi, konsola na żywo i rozmowa (dawne etapy 4 i 10), razem z Z7a (trzy pasy) i N11 (karta decyzji przy bramce) | pdi + tf | DA4, Z2 | do przygotowania |
| B6 | **Etap 3** — z localhosta na produkcję | pdi + ShipScope + tf + sprintdeck | B1–B5, działające Actions | [jest](polecenia-startowe-sdlc-lokalnie.md#etap-3--pdi--shipscope-tf-z-localhosta-na-produkcję) |

**C. Greenfield i brownfield**

| # | Krok | Repo | Po czym | Polecenie startowe |
|---|---|---|---|---|
| C1 | Z4 — greenfield do końca: wybór stosu, bootstrap repo z tf (z N3), lista kroków infrastruktury | tf + pdi | Z2 | do przygotowania |
| C2 | Z5 — onboarding brownfield z N9 (wzorce, testy charakteryzujące, uruchamialność) i N6 (mapa projektu z kodu) | tf + pdi + ci_for_sdlc | Z1 | do przygotowania |
| C3 | Z6 — Slack, potem Teams i Miro jako źródła wiedzy | pdi | Z5 | do przygotowania |
| C4 | N7 — wznawianie przerwanej fazy · N8 — makiety HTML w fazie design | pdi + tf | Z8a | do przygotowania |

**D. Dalsze etapy (bez zmian, po kolei)**

Etap 5 (graf śladu, rejestr decyzji, panel w Jirze) → etap 6 (autonomia na danych) → etap 7 (etapy flag według reguły,
metryki ochronne) → etap 8 (uproszczone review, lustro Jira) → etap 9 (incydenty, aplikacja Slacka) → etap 11 (zaległe
kroki G1/G2) → etap 12 (jedno wejście, miary przepływu; razem z Z8e) → etapy 13–14 (łączenie backendów) → etap 15
(pilotaż) → etap 16 (utrzymanie) → etap 17 (cennik) → etap 18 (przegląd na dowodach). Etapy 4 i 10 weszły do Z3.

**Na bieżąco:** Z8f — po każdym przebiegu PRB dotyczące uprzęży zamieniają się w zmiany w tf z evalem. Z7d — przy
pierwszym produkcie, który sam jest aplikacją AI.

## Skrót: co już mamy i czego brakuje

Tabele w brzmieniu z rozmowy 2026-11-02, bez pozycji już zrobionych. Szczegóły i kroki: §2–§10.

### Co już mamy, a czego brakuje

**Model „zespołu jednoosobowego” już jest w tf.** Persony to role w zespole:

| Rola | Kto | Stan |
|---|---|---|
| PM | Maja: intencja | jest |
| Analityk | Ewa: wymagania | jest |
| Architekt | Tomasz: plan cięć i wydania | jest |
| UX | Natalia: design | jest |
| Programista | Talos: cięcia jako PR | jest |
| Recenzent bezpieczeństwa | `security-reviewer` w tf | jest |
| QA | ci_for_sdlc i testy | w części |
| Ops | ShipScope | jest |

Każda faza to dziś agent działający **bez rozmowy**: dostaje wejście, robi artefakt, prosi o bramkę.

### Greenfield

| Etap | Stan | Brakuje |
|---|---|---|
| Wywiad na start (styl grill-me: pytanie po pytaniu, po kolei przez całe drzewo decyzji, z rekomendowaną odpowiedzią przy każdym) | **brak**; dziś proces startuje od gotowego zgłoszenia | faza `discovery` przed intencją; to jedyna faza, która z natury jest rozmową |
| Kształt produktu, PRD | w części: Maja pisze intencję, ale z jednego zgłoszenia | wywiad jako wejście; odpowiedzi jako decyzje w rejestrze pdi |
| Wybór stosu | **brak** | krok z porównaniem opcji; skille `10x-tech-stack-selector` i `10x-stack-assess` robią dokładnie to |
| Założenie repo, CLAUDE.md, CI, tf | w części: `sdlc sandbox` zakłada repo tylko z gotowego szablonu | bootstrap z wybranego stosu (`10x-bootstrapper`, `10x-init`, `10x-agents-md`) |
| Infrastruktura (konta, domena, baza, sekrety, płatności) | **brak** | to musi zostać decyzją człowieka: kosztuje pieniądze i jest nieodwracalne; system może tylko przygotować listę kroków i polecenia |

### Brownfield (istniejący projekt)

| Etap | Stan | Brakuje |
|---|---|---|
| Slack, Teams, Miro | **brak** jako źródło wiedzy; pdi wyciąga tylko decyzje z wątków Slacka i transkrypcji (A5, z cytatami) | konektory jako źródła z tą samą zasadą: cytat i link zamiast kopii treści |
| **Standardy projektu** (konwencje kodu, nazewnictwo, testy, Definition of Done, przepływ PR, styl dokumentacji) | rozproszone: CLAUDE.md, reguły ci_for_sdlc, review | jeden plik standardów wydobyty ze źródeł, z cytatem dla każdej zasady; z niego korzystają persony, a sprawdzają go bramki |
| Mapa wiedzy: co jest prawdą, co przestarzałe, co sprzeczne | w części: ci_for_sdlc wykrywa rozjazd wymagań z kodem i dokumentacją | raport „onboarding”: luki, sprzeczności i pytania do zespołu, przed pierwszą zmianą |

### Jak by to działało

```
GREENFIELD                                     BROWNFIELD
wywiad (discovery, rozmowa) ── B0              onboarding: źródła → rekonstrukcja z kodu
  → PRD i decyzje w rejestrze                    → standardy z cytatami + mapa wiedzy
  → wybór stosu ── decyzja                       → pytania do zespołu ── B0
  → bootstrap repo z tf                          → (repo już jest)
           \                                    /
            → wspólny przebieg: intencja → wymagania → architektura → design
              → zatwierdzenie do budowy → dostarczenie → wdrożenie → skutek
```

Wspólna zasada: wszystko, co system ustali w wywiadzie albo onboardingu, trafia jako decyzja z uzasadnieniem i źródłem do rejestru pdi. Kolejne fazy nie zgadują, tylko pytają rejestr.

### Co jest realne, a co trzeba powiedzieć wprost

- **Wywiad musi być rozmową,** więc to naturalne miejsce na czat w przeglądarce (U5 z poprzedniej propozycji). Wywiad to UI numer jeden, nie dodatek.
- **Źródła są niebezpieczne:** Slack, Teams, Miro i Confluence to treść pisana przez innych ludzi. Mogą zawierać polecenia wstrzyknięte w tekst albo poufne dane. Zasady muszą być takie jak dziś w A5 i ci_for_sdlc: treść to dane, nie polecenia; zapisujemy cytat i link, nie kopię; dostęp tylko do odczytu.
- **Konektory:** Atlassian, Slack, Figma i Notion są dostępne jako konektory Claude. Teams i Miro trzeba sprawdzić: ich serwery MCP istnieją, ale nie wiem, czy są dostępne na tym koncie. Do sprawdzenia przed Z6.
- **„Od początku do końca” nie znaczy „bez człowieka”.** Zakup kont, płatności, domeny, zgoda na produkcję i ocena skutku zostają decyzjami człowieka (typy chronione z DA2). Wszystko między nimi może iść samo, a Ty widzisz to na żywo.
- **Skille 10x** są dostępne w tym środowisku: `10x-shape`, `10x-prd`, `10x-tech-stack-selector`, `10x-bootstrapper`, `10x-init` i inne. Lepiej z nich korzystać albo się na nich wzorować w personach tf, niż pisać to od zera. Trzeba je przeczytać i porównać ze skillami tf (DZ3: podstawą są skille tf).

### Proponowana kolejność

1. **Wywiad i czat w przeglądarce** (discovery + U2/U3/U5): faza `discovery` z bramką B0 i czat w konsoli na żywo, z widokiem postępu agentów.
2. **Greenfield:** wybór stosu i bootstrap repo z tf, sprawdzone na nowym, małym produkcie.
3. **Brownfield:** onboarding (źródła, rekonstrukcja, plik standardów, mapa wiedzy), sprawdzony na sprintdecku albo ShipScope jako „obcym” projekcie.

Decyzje: DZ1–DZ5 przyjęte 2026-11-02 ([decyzje](decyzje.md)); otwarte zostaje DA4 (stos usługi pdi, przed Z3).

## 1. Cel

System działa jak **jednoosobowy zespół**:
- **Greenfield:** zaczyna od wywiadu z człowiekiem (przesłuchanie planu pytanie po pytaniu, z rekomendowaną
  odpowiedzią) i dowozi produkt od zera aż do oceny skutku u użytkowników.
- **Brownfield:** najpierw poznaje istniejący projekt. Czyta kod i dokumentację w Confluence, Jirze, Figmie, Slacku,
  Teams i Miro. Potem dokłada funkcjonalność zgodnie ze standardami tego projektu i z podanymi wymaganiami.
- **Przeglądarka:** całość widać na żywo, z tym, co agent robi teraz („myśli”, pisze, testuje), ile to trwa
  i kosztuje. Człowiek dostaje sygnał, gdy coś na niego czeka, zamiast sprawdzać wynik co chwilę.

Między decyzjami człowieka proces jest autonomiczny. Decyzje o pieniądzach, nieodwracalnych krokach, wydaniu do ludzi
i ocenie skutku zostają u człowieka (typy chronione z DA2).

## 2. Co już jest

**Przebieg lokalny z 2026-10-31 przeszedł od zgłoszenia do oceny skutku** (repo `dbqm45/sdlc-proba`, CHG-1, wynik
`met`), ale z obejściami. Luki są zapisane jako PRB-2…PRB-22. Według commitów w main do 2026-11-02 naprawione są
PRB-2, 4–10, 16–22. PRB-3 (odpowiedzi z bramek nie docierają do kolejnych faz) jest naprawione w części: pdi #88 przekazuje
treść decyzji z bramki, tf #111 zapisuje ją w `decisions.md`, a prompt fazy każe traktować ją jako wiążącą; nie sprawdzono
tego w ponownym przebiegu. Otwarte zostają PRB-11–14 (tf) i PRB-15 (repo próbne bez CI).

| Rola w zespole | Kto | Stan |
|---|---|---|
| PM / product owner | persona maja (faza `intent`) | jest; zaczyna od jednego zgłoszenia, nie od wywiadu |
| Analityk | ewa (`requirements`) | jest |
| Architekt | tomasz (`architecture`: plan cięć, `release.yaml`) | jest |
| UX | natalia (`design`, tabela ramek Figmy) | jest; próba na prawdziwym pliku Figmy czeka (D-F3) |
| Programista | talos (`delivery`, cięcia jako PR) | jest |
| Recenzent bezpieczeństwa | agent `security-reviewer` w tf | jest |
| QA | ci_for_sdlc (reguły STORY/AC/REL/DES/TEST) + testy repo | w części; testy kryteriów tylko z JUnit XML |
| Ops / wydania | ShipScope (wdrożenia, flagi, etapy, plan wydania) | jest |
| Pamięć zespołu | rejestr decyzji pdi | jest; do faz trafiają decyzje z bramek (pdi #88, tf #111), ale nie pozostałe decyzje zmiany z rejestru |

**Umiejętności tf, które już robią część tego planu** (dziś jako skille, nie jako fazy pdi):

| Skill tf | Co robi | Gdzie się przyda |
|---|---|---|
| `core-plan-interview` | przesłuchanie planu: drzewo decyzji, rundy pytań z rekomendacją | wywiad greenfield (styl grill-me) |
| `core-delivery-lifecycle`, etap 0 | brief: problem, cel, użytkownicy, zakres, „poza zakresem”, ograniczenia, plan faz; plan projektu P50/P80 | wynik wywiadu |
| `proc-product-discovery` | wynik zamiast funkcji, JTBD, drzewo szans, testy założeń | wywiad, część produktowa |
| `arch-tech-selection` | wybór technologii z porównaniem | wybór stosu |
| `eng-project-reconstruction` | odtworzenie z kodu: stos, moduły, domeny, wymagania, reguły, **standardy** — raport z dowodami | brownfield |
| `eng-legacy-dossier` | opis i ocena architektury legacy z dowodami | brownfield |
| `ddd-discovery-intake` | surowe materiały (wywiady, notatki, tablice) → obszary z cytatami i sprzecznościami | brownfield: Slack, Teams, Miro |

Skille 10x z tego środowiska (`10x-shape`, `10x-prd`, `10x-tech-stack-selector`, `10x-bootstrapper`, `10x-init`,
`10x-agents-md`, `10x-stack-assess`) pokrywają podobny obszar. Decyzja DZ3: czy z nich korzystać, czy tylko się na nich
wzorować (§9).

## 3. Czego brakuje: greenfield

| Etap | Stan | Brakuje | Krok |
|---|---|---|---|
| Wywiad na start (pytanie po pytaniu przez drzewo decyzji, z rekomendacją) | skill `core-plan-interview` jest, ale proces startuje od gotowego zgłoszenia (PRB) | faza `discovery` przed `intent`, jedyna faza z natury rozmową; bramka **B0** (brief zatwierdzony) w kontrakcie | Z2 |
| Brief i PRD | maja pisze intencję z jednego zgłoszenia | brief z wywiadu jako wejście intencji; każda odpowiedź z wywiadu jako decyzja w rejestrze z cytatem z rozmowy | Z2 |
| Wybór stosu | skill `arch-tech-selection` jest, nie jest fazą | krok w `discovery` albo osobna faza z decyzją typu `stack` (opcje, kryteria, koszt) | Z4 |
| Założenie repo, CLAUDE.md, CI, tf | `sdlc sandbox` zakłada repo tylko z gotowego szablonu | bootstrap z wybranego stosu: szkielet aplikacji, testy, CI, plik flag, tf (`mode-pdi`, `mode-talos`) | Z4 |
| Infrastruktura (konta, domena, baza, sekrety, płatności) | brak | **zostaje u człowieka** (koszt, nieodwracalne); system przygotowuje listę kroków i polecenia, a człowiek je wykonuje i potwierdza | Z4 |
| Dalej: intencja → … → skutek | jest | wszystkie decyzje zmiany, także z wywiadu, muszą trafiać do kolejnych faz (domknięcie PRB-3) | Z1 |

## 4. Czego brakuje: brownfield

| Etap | Stan | Brakuje | Krok |
|---|---|---|---|
| Kod: stos, moduły, domeny, reguły, standardy | **jest**: `eng-project-reconstruction`, rekonstrukcja F1a–F2 z eksportem JSON (tf #83), czytana przez ci_for_sdlc | uruchomienie jako faza `onboarding` w pdi | Z5 |
| Jira, Confluence, Figma, OpenAPI | **jest w ci_for_sdlc** (konektory Atlassian, Figma; OpenAPI #93) | podanie ich wyniku personom tf, nie tylko regułom | Z5 |
| Slack, Teams, Miro | brak jako źródło wiedzy; pdi bierze ze Slacka i transkrypcji tylko decyzje z cytatem (A5) | konektory tylko do odczytu; treść jako dane, w rejestrze cytat i link zamiast kopii; Teams i Miro — sprawdzić dostępność konektorów MCP na koncie | Z6 |
| **Standardy projektu** (konwencje kodu, nazewnictwo, testy, Definition of Done, przepływ PR, styl dokumentacji) | rozproszone: CLAUDE.md, reguły ci_for_sdlc, review | `docs/project/standards.md` z każdą zasadą z dowodem (plik, strona, wątek); czytają go persony, a sprawdzają bramki (ci_for_sdlc, review) | Z5 |
| Mapa wiedzy: prawdziwe, przestarzałe, sprzeczne | w części: ci_for_sdlc wykrywa rozjazd wymagań z kodem i dokumentacją | raport onboardingu: luki, sprzeczności, pytania do zespołu; bramka **B0** (onboarding zatwierdzony) przed pierwszą zmianą | Z5 |
| Wymagania od zespołu → zmiana zgodna ze standardami | przebieg jest; standardy podawane nie wprost | `standards.md` i mapa wiedzy w wejściu każdej fazy; reguła w ci_for_sdlc „zmiana łamie standard X” | Z5 |

## 5. Czego brakuje: przeglądarka i praca na żywo

| Co | Stan | Brakuje | Krok |
|---|---|---|---|
| Postęp persony na żywo („myśli”, czyta, pisze, testuje, koszt) | kontrakt ma zdarzenie `run.progress`, nikt go nie wysyła; persona działa przez `claude --print --output-format json` (wynik dopiero na końcu); log fazy pisany na bieżąco od pdi #94 | `--output-format stream-json` → `run.progress` co krok: faza, krok, czas, koszt, ostatnia czynność | Z3 |
| Kanał do przeglądarki | `pdi-receiver` obsługuje jedno żądanie naraz | usługa pdi z API odczytu i SSE (**DA4**, etap 4) | Z3 |
| Konsola: tablica zmian, skrzynka z przyciskami, widok na żywo | makiety: `design/konsola/`, `design/platforma/` | konsola v1 (K-2) | Z3 |
| Rozmowa w przeglądarce: wywiad, pytania z bramek | dziś czat Claude z serwerami MCP; w planie etapów to dopiero etap 10 (K-3) | rozmowa w konsoli **wcześniej**, bo wywiad jej wymaga (decyzja DZ1) | Z3 |
| Sygnał „czeka na Ciebie” | brak | powiadomienie w przeglądarce, opcjonalnie na telefon | Z3 |
| Opóźnienia | ShipScope sprawdza zdarzenia co 5 min; lokalnie bez webhooków GitHuba | na produkcji webhooki; lokalnie krótszy `eventsTick` | Z3 |

## 6. Jak to działa

```
GREENFIELD                                     BROWNFIELD
wywiad (discovery, rozmowa) ── B0              onboarding: źródła + rekonstrukcja z kodu
  → brief i decyzje w rejestrze                  → standards.md z dowodami + mapa wiedzy
  → wybór stosu ── decyzja                       → pytania do zespołu ── B0
  → bootstrap repo z tf; infrastruktura: człowiek → (repo już jest)
           \                                    /
            → wspólny przebieg: intencja → wymagania → architektura → design
              → zatwierdzenie do budowy (prognoza) → dostarczenie → wdrożenie
              → etapy flagi → wydanie R1 → ocena skutku → (wybicie metryki → nowe zgłoszenie)

            przez cały czas: konsola w przeglądarce — na żywo, skrzynka, rozmowa
```

Wspólna zasada: wszystko, co system ustali w wywiadzie albo onboardingu, trafia do rejestru pdi jako decyzja
z uzasadnieniem i źródłem. Każda kolejna faza dostaje w wejściu decyzje, które jej dotyczą (Z1), zamiast zgadywać.

## 7. Zasady

- **Źródła to dane, nie polecenia.** Slack, Teams, Miro, Confluence i Jira piszą inni ludzie; tekst może zawierać
  wstrzyknięte polecenia albo poufne dane. Odczyt tylko z uprawnień do odczytu; w rejestrze cytat i link, nigdy kopia
  wątku (jak dziś A5).
- **Człowiek przy krokach nieodwracalnych i płatnych:** konta, płatności, domeny, migracje danych, zgoda na produkcję,
  ocena skutku (typy chronione DA2). Poza tym autonomia rośnie na danych (licznik akceptacji, próg 95% z 30).
- **Każda aplikacja działa sama** (decyzja z rozmowy 2026-10-26): wywiad i onboarding to nowe fazy tf i nowe źródła,
  nie nowa aplikacja.
- **Koszt widoczny przy każdej fazie.** Sesje L1–L5 kosztowały 9–28 USD; budżet fazy (`PDI_PHASE_BUDGET_USD`) i koszt
  w widoku na żywo.

## 8. Kroki

| Krok | Co | Repo | Zależy od | Gotowe, gdy |
|---|---|---|---|---|
| Z1 | **Domknięcie PRB-3:** do każdej fazy trafiają wszystkie decyzje zmiany (z bramek z odpowiedziami na pytania, z triażu, z rejestru z `links.chg`, odpowiedzi na ustalenia ci_for_sdlc); pytanie już rozstrzygnięte nie może wrócić w kolejnym artefakcie | pdi + tf | — | w powtórzonym przebiegu lokalnym te same pytania nie wracają, a talos nie łamie przyjętych decyzji |
| Z2 | **Wywiad (`discovery`):** faza rozmowy z `core-plan-interview` i `proc-product-discovery`; wynik `docs/project/changes/<CHG>/brief.md` (albo `docs/project/discovery/brief.md` dla produktu) i decyzje w rejestrze; bramka B0 w kontrakcie (wersja minor) | tf + pdi (kontrakt) | Z1, DZ1, DZ3 | wywiad w czacie Claude z MCP kończy się briefem i B0; intencja powstaje z briefu |
| Z3 | **Przeglądarka:** `run.progress` ze `stream-json`; usługa pdi z SSE; konsola v1 (tablica, skrzynka, na żywo) i rozmowa (wywiad, pytania z bramek); sygnał „czeka na Ciebie” | tf + pdi | DA4, DZ1, DZ2 | wywiad i cały przebieg widać i prowadzi się w przeglądarce, bez terminala i bez dopytywania |
| Z4 | **Greenfield do końca:** wybór stosu (`arch-tech-selection`, decyzja `stack`), bootstrap repo ze stosu z tf, lista kroków infrastruktury dla człowieka | tf + pdi (`sdlc new`) | Z2, DZ3 | nowy mały produkt od wywiadu do oceny skutku, bez szablonu `sdlc-sandbox` |
| Z5 | **Onboarding brownfield:** faza `onboarding` (rekonstrukcja z kodu + wyniki ci_for_sdlc z Jiry, Confluence, Figmy) → `standards.md` z dowodami, mapa wiedzy, pytania; B0; standardy w wejściu faz i reguła w ci_for_sdlc | tf + pdi + ci_for_sdlc | Z1 | na „obcym” repo (DZ4) pierwsza zmiana przechodzi zgodnie z jego standardami, a review nie znajduje naruszeń konwencji |
| Z6 | **Źródła rozmów:** Slack, potem Miro (oficjalny serwer MCP Miro, OAuth, dostęp do jednego zespołu) jako źródła wiedzy do onboardingu (cytat i link); Teams po wyjściu serwera MCP Microsoftu z wersji preview | pdi (+ konektory) | Z5, DZ2 | mapa wiedzy cytuje wątki i tablice; sprzeczności z Confluence są w pytaniach |
| Z7 | **Układ z cyklu aplikacji AI** (§8.1): trzy pasy w konsoli i dokumentacji, bramka „spełnia cele?” z krótką pętlą do wskazanej fazy, pas governance przez wszystkie fazy, opcjonalna gałąź dla produktów, które same są aplikacją AI | pdi + tf + ci_for_sdlc (+ ShipScope) | Z1, Z3 (pasy w konsoli) | patrz §8.1, Z7a–Z7d |
| Z8 | **Uprząż i dowody** (§8.2): izolacja faz, tożsamość agentów, skaner bezpieczeństwa w pętli talosa i w CI, pakiet dowodów zmiany, miary wartości, uprząż ucząca się z PRB | tf + pdi (+ ci_for_sdlc, ShipScope) | Z1 | patrz §8.2, Z8a–Z8f |
| Z9 | **Pętle jakości i kontekst** (§8.3): przegląd drugim modelem, pętla budujący–recenzent i samonaprawa CI, jeden skrypt weryfikacji, cele pokrycia i testy mutacyjne, evale przebiegu, kontekst przycięty do fazy, wznawianie pracy, makiety HTML, wzorce i testy charakteryzujące w brownfield, łańcuch dostaw, karta decyzji przy bramce | tf + pdi (+ ci_for_sdlc) | Z1, Z8c | patrz §8.3, N1–N11 |

Kolejność: Z1 → Z2 (w czacie Claude, bez nowej usługi) → Z3 → Z4 i Z5 równolegle → Z6. Z7: Z7b i Z7c mogą iść
razem z Z1–Z2 (nie zależą od konsoli), Z7a razem z Z3, Z7d przy pierwszym produkcie, który jest aplikacją AI. Z8: Z8a i Z8c
przed kolejnym przebiegiem z prawdziwym kodem (etap 2 na sprintdecku), Z8b przed etapem 3 (produkcja), Z8d razem z Z7c, Z8e
z etapem 12 (G7), Z8f po każdym przebiegu. Z9: N1, N2 i N5 przed etapem 2; N9 razem z Z5;
pozostałe razem z krokami, do których są przypięte (§8.3).

**Miejsce w etapach 2–18:** Z1 to poprawka przed etapem 2 (zalecana w wyniku przebiegu). Z3 łączy etap 4 (usługa
i konsola K-2) z etapem 10 (rozmowa K-3) i przesuwa rozmowę wcześniej. Z2, Z4, Z5 i Z6 to nowe etapy, których w tej
tabeli nie ma. Zmianę kolejności etapów zatwierdza właściciel (DZ5).

### 8.1. Z7 — układ z cyklu aplikacji AI

Źródło: diagram cyklu życia aplikacji AI (pokazany 2026-11-02): trzy pasy „Design & Build”, „Evaluate & Ship”,
„Deploy, Monitor & Improve”, bramka „meets targets?” z pętlą „fail → iterate”, pętla ulepszeń wracająca do faz 2–7
i pas „Governance, Security & Compliance” przez wszystkie fazy. Diagram opisuje budowę aplikacji AI, a nasz przebieg
dowożenie dowolnej zmiany, więc nie zastępujemy przebiegu, tylko przejmujemy cztery elementy.

**Porównanie z naszym przebiegiem**

| Na diagramie | U nas dziś | Brakuje |
|---|---|---|
| 1. Cel biznesowy i metryki | metryka sukcesu w decyzji B1 (`success_metric`), cel MVP w `release.yaml` | metryka już w wywiadzie (Z2), przed kształtem rozwiązania |
| 2. Przygotowanie danych i wiedzy | brownfield: rekonstrukcja z kodu, ci_for_sdlc; reszta w Z5–Z6 | — (pokrywa Z5, Z6) |
| 3–7. Model, kontekst, RAG, agenci, fine-tuning | brak jako faz; skille tf (wywołania LLM, ewaluacje RAG, bramki dla agentów) | opcjonalna gałąź dla produktów AI (Z7d) |
| 8. Ewaluacja i testy | reguły ci_for_sdlc (STORY/AC/REL/DES/TEST), testy repo, review | mierzalne cele jakości zmiany (progi), sprawdzane automatycznie |
| Bramka „spełnia cele?”, „fail → iterate” | bramki ludzi; „do poprawek” wraca tylko do tej samej fazy | bramka z celami i powrót do wskazanej wcześniejszej fazy (Z7b) |
| 9. Wdrożenie i integracja | ShipScope: wdrożenia, flagi, etapy | — |
| 10. Obserwowalność i monitoring | `metric_watch.py` (pasma 3σ), ShipScope (`/metrics`, `/flow`) | metryki ochronne produktu (G5, etap 7) |
| 11. Informacja zwrotna i analiza błędów | ocena skutku (`met`/`not_met`), `metric.breached` → nowe zgłoszenie | analiza przyczyny przy `not_met` jako wejście dla kolejnej iteracji |
| „Update & Experiment”, pętla do faz 2–7 | `not_met` i wybicie metryki otwierają nowe PRB: cały cykl od triażu | ponowne otwarcie tej samej zmiany od wymagań albo architektury, z danymi z produkcji (Z7b) |
| 12. Governance przez wszystkie fazy | rozproszone: rejestr decyzji, graf śladu, typy chronione (DA2), `security-reviewer`, zasady źródeł (A5) | jeden pas: co w każdej fazie sprawdzono pod kątem danych osobowych, dostępów, zabezpieczeń i audytu (Z7c) |

**Kroki**

| Krok | Co | Repo | Zależy od | Gotowe, gdy |
|---|---|---|---|---|
| Z7a | **Trzy pasy:** „Zaprojektuj i zbuduj” (zgłoszenie, wywiad, intencja, wymagania, architektura, design, gotowość, budowa), „Oceń i wydaj” (review, cele zmiany, B4/B5, wdrożenie na PROD ukryte za flagą), „Wdróż, obserwuj, ulepszaj” (udostępnianie etapami, wydanie R1, ocena skutku, pętla do pasa 1); użytkownik w każdej chwili widzi pas i bieżący etap: na tablicy kolumny faz są pogrupowane w pasy, a w śladzie zmiany nad etapami są pasy z „teraz” i w nagłówku „Pas N z 3 · teraz: … · dalej: …” (propozycja: `design/konsola/pasy-propozycja/`); `stage` każdej fazy i bramki w kontrakcie, tablica konsoli i dokumentacja według pasów | pdi (kontrakt, konsola) | Z3 | na tablicy widać, w którym pasie jest każda zmiana |
| Z7b | **Bramka z celami i krótka pętla:** `targets` zmiany (progi: testy kryteriów, pokrycie, wydajność, ewaluacje dla AI) w `release.yaml` albo planie; sprawdzane przez ci_for_sdlc i testy przed B4; wynik „nie spełnia” albo ocena skutku `not_met` może wrócić do wskazanej fazy (`return_to: requirements \| architecture \| design \| delivery`) tej samej zmiany, z danymi jako wejściem, zamiast nowego zgłoszenia. Dwie części: **Z7b-1** — cele i ich sprawdzenie przed B4 (grupa A, przed etapem 2); **Z7b-2** — pętla ulepszeń po `not_met` i wybiciu metryki (grupa B) | pdi + tf + ci_for_sdlc | Z1 | zmiana, która nie spełnia celu, wraca do wskazanej fazy z powodem, a pętla ma limit prób i potem trafia do człowieka |
| Z7c | **Pas governance:** dla każdej fazy lista kontrolna (dane osobowe, dostępy i sekrety, zabezpieczenia AI, audyt i pochodzenie) z wynikiem w stanie zmiany; graf śladu i konsola pokazują go jako pas; brak sprawdzenia blokuje B5 (autoryzacja PROD) | pdi + tf | Z1 | `get_trace` pokazuje pas governance każdej zmiany; B5 bez kompletu odmawia z listą braków |
| Z7d | **Gałąź dla produktów AI:** gdy wywiad albo architektura oznaczy produkt jako aplikację AI, dochodzą fazy opcjonalne: dobór modelu (decyzja z kosztem), kontekst i RAG, orkiestracja agentów, decyzja o fine-tuningu, ewaluacje z progami (Z7b); skille tf jako podstawa (DZ3) | tf + pdi (kontrakt) | Z2, Z7b | mały produkt AI przechodzi gałąź z ewaluacją spełniającą próg przed wydaniem |

### 8.2. Z8 — uprząż i dowody

Źródło: materiały „Agentic SDLC” pokazane 2026-11-02 (dwie strony: specyfikacja i uprząż; pięć warstw: intencja,
wykonanie, uprząż, weryfikacja, governance; drabina dojrzałości L1–L5) i transkrypcja z NotebookLM. Liczby z tych
materiałów (Symphony, wyniki modeli, odsetki przyjęć) to w dużej części dane od dostawców; w planie nie przyjmujemy ich
jako faktów. Jedyną liczbą z niezależnego badania jest raport Veracode z 2025 r. (ok. 45% kodu z AI z podatnością
z OWASP Top 10), którą przed cytowaniem trzeba sprawdzić u źródła. Zasada przyjęta z materiału: „nie da się bezpiecznie
zautomatyzować tego, czego się nie rozumie” — uzasadnia Z2 (wywiad) i Z5 (onboarding).

**Pięć warstw a nasz ekosystem**

| Warstwa | U nas dziś | Kroki planu | Sprawdzone w źródłach (§8.4) |
|---|---|---|---|
| 1. Intencja (specyfikacja w repo jako źródło prawdy) | `docs/project/changes/CHG-n/`: `intent.md`, `requirements.md`, `plan.md`, `release.yaml`, `design.md` wg kontraktu pdi — jest | Z1 (decyzje zmiany w każdej fazie), Z2 (wywiad, B0), Z5 (`standards.md`, mapa wiedzy), Z6 (Slack, Teams, Miro), N1 (drugi model szuka luk w wymaganiach i planie), N8 (makiety HTML) | grill-me ✓; Miro MCP ✓; Teams MCP — preview |
| 2. Wykonanie (agenci) | persony tf, talos — jest | Z4 (bootstrap greenfield), Z7d (gałąź dla produktów AI), N2 (pętla budujący–recenzent, samonaprawa CI), N6 (kontekst przycięty do fazy), N7 (wznawianie) | Spotify Honk ✓ (PR po weryfikacji oddzielonej od agenta) |
| 3. Uprząż: przewodniki | CLAUDE.md, skille, persony — jest | N3 (jeden skrypt weryfikacji), N9 (wzorce, testy charakteryzujące), Z8f (uprząż ucząca się z PRB) | — |
| 3. Uprząż: czujniki i izolacja | hooki tf (`tdd_guard`, `scan_secrets`, `guard_bash`, `guard_paths`), testy, reguły ci_for_sdlc, pętla kawałka talosa — w części: brak skanu podatności i izolacji | Z8a (kontener + sandbox Claude Code), Z8c (Semgrep, audyt zależności), N10 (karencja dla nowych wersji) | sandbox Claude Code ✓; token w kontenerze ✓ (znany błąd); karencja w npm, pnpm, Yarn ✓; Semgrep bez logowania — do sprawdzenia; Veracode 45% ✓ jako benchmark |
| 4. Weryfikacja | ci_for_sdlc (STORY/AC/REL/DES/TEST), review — w części | Z8c-1 (SARIF jako ustalenia), Z7b-1 (cele zmiany przed B4), Z7b-2 (pętla ulepszeń), N4 (pokrycie, testy mutacyjne), N5 (evale przebiegu), walidacja uwag z review w N1 | Stryker, mutmut ✓ |
| 5. Governance | rejestr decyzji, graf śladu, typy chronione, licznik autonomii — w części: brak tożsamości agentów i eksportu dowodów | Z7c (pas governance, blokuje B5), Z8b (tożsamość agentów), Z8d (pakiet dowodów), Z8e (miary wartości) | token aplikacji GitHub 1 h ✓; NIST SP 800-218 i 800-218A ✓ |
| Widok (wszystkie warstwy naraz) | makiety konsoli — w części | Z3 (konsola, rozmowa, na żywo), Z7a (trzy pasy), N11 (karta decyzji przy bramce) | — |

Na drabinie z materiału jesteśmy między L3 (agenci bez nadzoru, deterministyczne bramki) a L4 (fabryka z governance).

**Kroki**

| Krok | Co | Dlaczego | Repo | Gotowe, gdy |
|---|---|---|---|---|
| Z8a | **Izolacja faz:** persony i talos w kontenerze albo sandboxie z listą dozwolonych adresów sieci, bez dostępu do kluczy i plików spoza klonu repo; drugą warstwą jest sandbox Claude Code (`network.allowedDomains`, `filesystem.denyRead`, `failIfUnavailable: true`) podawany przez pdi w `--settings`, bo ustawienia z repo produktu nie mogą luzować ograniczeń; token Claude w kontenerze z `claude setup-token` (tylko jedna ze zmiennych `CLAUDE_CODE_OAUTH_TOKEN` i `ANTHROPIC_API_KEY`); w Actions to samo w obrazie joba | w trybie lokalnym (`PDI_DISPATCH=local`) persona działa wprost na komputerze właściciela z `--permission-mode acceptEdits`, jego `gh` i kluczami | pdi (`dispatch_local`, `sdlc`) + tf (`sdlc-phase.yml`) | faza w trybie lokalnym nie widzi `~/.sdlc/env`, `~/.ssh` ani innych repo, a próba wyjścia poza listę adresów kończy się błędem w logu |
| Z8b | **Tożsamość agentów:** osobna aplikacja GitHub (bot) z krótkotrwałymi tokenami instalacji do push i PR; w commicie dopiski `Agent: <persona>` i `Phase: <faza>` obok `Change:`; graf śladu łączy linię kodu z agentem, fazą, decyzją i człowiekiem, który zatwierdził bramkę | dziś lokalne commity agentów wyglądają jak commity właściciela; audyt musi odróżniać człowieka od agenta | pdi + tf (+ ShipScope: odczyt dopisków) | każdy commit agenta jest podpisany botem, a `get_trace` pokazuje agenta przy każdym PR |
| Z8c | **Skaner bezpieczeństwa jako czujnik:** SAST i skan zależności w pętli kawałka talosa (przed commitem) i w CI na PR; blokujące ustalenie wraca do talosa jak czerwony test; PR dopiero, gdy wszystkie czujniki są zielone | w benchmarku Veracode z lipca 2025 r. (80 zadań, ponad 100 modeli) 45% przypadków zawierało podatność z OWASP Top 10, a dla Javy 72% (§8.4); to wynik benchmarku, nie odsetek kodu produkcyjnego | tf (talos, `change-check.yml`) + ci_for_sdlc (wynik skanu jako ustalenie) | podatność wstrzyknięta w teście (np. SQL injection) zatrzymuje kawałek przed PR, a w PR nie ma blokujących ustaleń; Semgrep z regułami OWASP działa bez logowania albo z regułami zapisanymi w repo |
| Z8d | **Pakiet dowodów zmiany:** `export_evidence CHG-n` (MCP i CLI): intencja, decyzje i bramki, testy kryteriów, wyniki skanów, review, tożsamości agentów, wdrożenia, etapy flag, ocena skutku; z mapowaniem na SSDF (NIST SP 800-218), jego profil dla AI generatywnego (SP 800-218A) i NIST AI RMF (skille tf z #91) | audyt jako produkt uboczny normalnej pracy; dla klientów regulowanych (np. infrastruktura ładowania EV) | pdi | dla CHG-1 z repo próbnego powstaje jeden pakiet (Markdown + JSON) bez ręcznego zbierania |
| Z8e | **Miary wartości:** odsetek PR-ów agentów przyjętych bez poprawek, usterki po wydaniu na zmianę, czas od intencji do PROD; bez liczby linii i liczby PR-ów | uzupełnia licznik autonomii (mierzy szkice decyzji, nie kod) | pdi + ShipScope | `pdi-stats` i konsola pokazują trzy miary dla ostatnich zmian |
| Z8f | **Uprząż ucząca się:** każde PRB z przebiegu z kategorii „uprząż” daje szkic zmiany reguły, skilla albo hooka w tf (wzór: `10x-lesson`, `10x-rule-review`); człowiek zatwierdza w skrzynce pdi, a zmiana idzie PR-em do tf z evalem | poziom L5 z materiału, ale pod nadzorem; materiał już jest (PRB-2…22 z jednego przebiegu) | pdi + tf | po kolejnym przebiegu co najmniej jedno PRB „uprzęży” kończy się zmianą w tf z evalem, zatwierdzoną w skrzynce |


### 8.3. Z9 — pętle jakości i kontekst

Źródło: transkrypcje czterech nagrań pokazanych 2026-11-02 — studium przypadku Open Mercato (podcast Better Software
Design), webinar Lean TECHniques „Building an Agentic-First Software Organization”, przegląd „Claude Code: The Complete
AI-Native SDLC Guide” i webinar Overcut „From SDLC to ADLC”. Liczby z nagrań pochodzą od samych mówców (firmy doradcze,
producenci, autorzy projektu) i nie są w planie podstawą decyzji. Nagrania potwierdzają kierunek przyjęty w Z1–Z8:
wywiad typu grill-me na start, łańcuch intencja → specyfikacja → plan w repo, triaż jako jedno wejście, izolacja
uruchomień, tożsamość agentów, pętla z produkcji do nowej intencji, uczenie się z poprzednich uruchomień i miary wartości
zamiast liczby PR-ów. Poniżej mechanizmy, których w planie brakowało.

| # | Mechanizm | Skąd | Przypięty do | Gotowe, gdy |
|---|---|---|---|---|
| N1 | **Przegląd drugim modelem** (najlepiej innego dostawcy): szuka luk w `requirements.md` i `plan.md` przed bramką i sprawdza uwagi z review, zanim talos je poprawi; uwagi, których drugi model nie potwierdza, idą do człowieka zamiast do poprawki | Open Mercato, Overcut | fazy requirements i architecture (tf), review w tf (`REVIEW.md`) | prośba o B2 i B3 zawiera wynik drugiego przeglądu, a poprawki po review dotyczą tylko potwierdzonych uwag |
| N2 | **Pętla budujący–recenzent na PR i samonaprawa CI:** review → sprawdzenie uwag (N1) → poprawka → ponowny review, z limitem rund; przy czerwonym CI agent czyta log, poprawia i czeka na zielone; człowiek widzi PR dopiero po zielonym CI i zamkniętych uwagach | wszystkie cztery | po fazie delivery (pdi `dispatch_local`, tf `sdlc-phase.yml`) | PR talosa trafia do człowieka z zielonym CI i zamkniętymi uwagami albo z wyraźnym „nie udało się po N rundach” |
| N3 | **Jeden skrypt weryfikacji** (formatter, lint, typy, testy, skan bezpieczeństwa Z8c) wskazany w pierwszej linii CLAUDE.md produktu i uruchamiany tak samo w CI | Lean TECHniques, Claude Code | tf (szablon CLAUDE.md, bootstrap Z4), Z8c | talos i CI uruchamiają to samo polecenie z tym samym wynikiem |
| N4 | **Cele pokrycia i testy mutacyjne:** pokrycie 100% z jawnie oznaczonymi wyjątkami; testy mutacyjne (StrykerJS dla JS/TS, mutmut dla Pythona) tylko na zmienionym kodzie, bo cały projekt trwa za długo; sprawdzają, czy testy wykrywają zmianę zachowania | Lean TECHniques | Z7b (`targets` zmiany), ci_for_sdlc | cel pokrycia i progi mutacji są w `targets`, a ich niespełnienie zatrzymuje zmianę przed B4 |
| N5 | **Evale przebiegu:** zestaw 20–200 prawdziwych zadań z przeszłości (zmiany i cięcia z repo próbnego i sprintdecka), uruchamiany po każdej zmianie modelu, skilla albo promptu fazy; mierzy wynik, koszt, liczbę czytanych plików i przyjęcie; także na tańszych modelach | Open Mercato, Claude Code | tf (evale skilli już są), „evale flow” z planu jednego flow | zmiana modelu albo skilla nie wchodzi bez przebiegu evali, a raport porównuje wynik i koszt |
| N6 | **Kontekst przycięty do fazy:** każda faza ładuje tylko swoje skille (klasyfikator zadania); mapa projektu (API, zdarzenia, ekrany, moduły) generowana z kodu przy buildzie zamiast przeszukiwania repo | Open Mercato, Overcut | tf (persony, instalacja), rekonstrukcja z kodu (Z5) | faza czyta wyraźnie mniej plików i tokenów przy tym samym wyniku evali (N5) |
| N7 | **Wznawianie przerwanej pracy:** notatka w PR, co z planu zrobione, a co nie; po błędzie faza rusza od ostatniego kroku zamiast od zera | Open Mercato, Overcut | pdi `dispatch_local`, talos | `retry_dispatch` po błędzie w połowie delivery kończy tylko brakujące cięcia |
| N8 | **Klikalne makiety HTML** w design systemie produktu; komentarze do komponentów zapisywane jako JSON i przekazywane talosowi; gdy nie ma pliku Figmy | Open Mercato | faza design (tf, natalia), `design.md` | design-review działa bez Figmy, a talos dostaje komentarze z makiety jako wejście |
| N9 | **Brownfield: wzorcowa implementacja i testy charakteryzujące.** `standards.md` wskazuje pliki do naśladowania, bo agenci kopiują istniejące wzorce. Przed zmianą w kodzie legacy powstają testy obecnego zachowania, a aplikacja musi dać się uruchomić lokalnie. | Lean TECHniques | Z5 | onboarding kończy się listą wzorców, uruchamialną aplikacją i testami charakteryzującymi obszar pierwszej zmiany |
| N10 | **Łańcuch dostaw:** nowa wersja zależności wchodzi najwcześniej 7 dni po publikacji, przez ustawienia menedżera pakietów: npm `min-release-age` (dni, od npm 11.10), pnpm `minimumReleaseAge` (minuty, od 10.16; w v11 domyślnie 1 dzień), Yarn `npmMinimalAgeGate`, uv `exclude-newer`; pliki blokad w repo; uwaga na Dependabota z `--frozen-lockfile` w pnpm 11; opcjonalnie własny rejestr pakietów | Lean TECHniques | Z8c (obok skanu zależności) | dodanie świeżo opublikowanej wersji zatrzymuje kawałek z wyjaśnieniem |
| N11 | **Karta decyzji przy bramce:** streszczenie zmiany, diagram architektury przed i po, plusy i minusy | Open Mercato | konsola (Z3), skrzynka pdi | bramki B3 i approve-for-implementation pokazują kartę w konsoli |

### 8.4. Weryfikacja źródeł

Sprawdzone 2026-11-02 w internecie: to, na czym opierają się kroki Z7–Z9. „✓” — potwierdzone; „?” — do sprawdzenia
w praktyce przy realizacji kroku; „✗” — nie potwierdzone, nie cytujemy.

| Teza | Wynik | Krok | Źródło |
|---|---|---|---|
| Kod z AI zawiera podatności z OWASP Top 10 | ✓ jako wynik benchmarku: 80 zadań, ponad 100 modeli, 45% przypadków z podatnością; Java 72%; raport z wiosny 2026 ma inne liczby | Z8c | [Veracode, komunikat](https://www.veracode.com/press-release/ai-generated-code-poses-major-security-risks-in-nearly-half-of-all-development-tasks-veracode-research-reveals/), [blog](https://veracode.com/blog/genai-code-security-report) |
| Karencja dla nowych wersji zależności | ✓ wbudowana: npm `min-release-age` (11.10), pnpm `minimumReleaseAge` (10.16; v11 domyślnie 1 dzień), Yarn `npmMinimalAgeGate`; znany problem z Dependabotem w pnpm 11 | N10 | [classmethod](https://dev.classmethod.jp/en/articles/pnpm-11-minimum-release-age-dependabot-ci-failure/), [gist](https://gist.github.com/mcollina/b294a6c39ee700d24073c0e5a4e93104) |
| Sandbox Claude Code: sieć i pliki | ✓ `network.allowedDomains`, `filesystem.denyRead`, `failIfUnavailable`; ustawienia z repo nie luzują ograniczeń; oficjalna strona do potwierdzenia w Z8a | Z8a | [przewodnik](https://claudefa.st/blog/guide/sandboxing-guide), [classmethod](https://dev.classmethod.jp/articles/claude-code-sandbox-202604/) |
| Token Claude w kontenerze | ✓ `claude setup-token` daje token na rok; ? znany błąd przy pierwszym uruchomieniu (`hasCompletedOnboarding`); nie ustawiać naraz z `ANTHROPIC_API_KEY` | Z8a | [zgłoszenie](https://claudeissues.com/issue/73403-bug-claude-code-oauth-token-ignored-on-first-run-due-to-onboarding-gate), [poradnik](https://www.vellum.ai/skills/headless-claude-code) |
| Token instalacji aplikacji GitHub | ✓ wygasa zawsze po godzinie | Z8b, DZ10 | [GitHub Docs](https://docs.github.com/en/enterprise-server@3.21/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation) |
| Semgrep z regułami OWASP bez konta | ? skan lokalny bez konta działa; nie potwierdzone, czy `p/owasp-top-ten` pobiera się bez logowania | Z8c, DZ11 | [Semgrep: JSON i SARIF](https://docs.semgrep.dev/semgrep-appsec-platform/json-and-sarif), [poradnik](https://aicodereview.cc/blog/how-to-setup-semgrep) |
| Wywiad grill-me | ✓ skill Matta Pococka (MIT): jedno pytanie naraz, z rekomendacją, bez pytań o to, co agent znajdzie sam; wariant `grill-with-docs` zapisuje ustalenia w słowniku i ADR | Z2 | [claudemarket](https://claudemarket.ai/skills/mattpocock/grill-me), [Medium](https://medium.com/@marc.bara.iniesta/the-ai-coding-repo-that-went-viral-because-it-adds-friction-e2b5c4d2fcc2) |
| SSDF dla AI | ✓ NIST SP 800-218A, finalny profil SSDF dla AI generatywnego (lipiec 2024) | Z8d | [NIST](https://csrc.nist.gov/pubs/sp/800/218/a/final) |
| Miro i Teams przez MCP | ✓ Miro: oficjalny serwer MCP; ? Teams: serwer Microsoftu w wersji preview | Z6 | [Miro](https://developers.miro.com/docs/connecting-to-miro-mcp), [przegląd Teams](https://eseospace.com/blog/microsoft-teams-mcp-server/) |
| Spotify Honk | ✓ ponad 1500 scalonych PR-ów; weryfikacja oddzielona od agenta; PR po pełnej weryfikacji | N2 | [Spotify](https://engineering.atspotify.com/2025/11/spotifys-background-coding-agent-part-1), [InfoQ](https://infoq.com/news/2026/03/spotify-honk-rewrite) |
| Stripe Minions, 1300 PR tygodniowo | ✗ tylko wzmianka na InfoQ, bez materiału Stripe | — | — |
| Open Mercato | ✓ organizacja na GitHubie, MIT, TypeScript | N6–N9 | [GitHub](https://github.com/open-mercato) |
| Testy mutacyjne | ✓ StrykerJS (JS/TS), mutmut (Python); uruchamiać na zmienionym kodzie | N4 | [przegląd](https://playbooks.com/skills/secondsky/claude-skills/mutation-testing) |

**Zasada na dalej.** Każde polecenie startowe wymaga, by sesja przed planem sprawdziła zachowanie zewnętrznych
narzędzi, API i ustawień w oficjalnej dokumentacji (z datą), a to, czego dokumentacja nie rozstrzyga, sprawdziła
lokalnie, i zapisała źródła w swoim planie. Przed każdą grupą z §0 (A–D) tabela wyżej jest sprawdzana ponownie dla
kroków tej grupy.

## 9. Decyzje do podjęcia

| # | Pytanie | Rekomendacja |
|---|---|---|
| DZ1 | Gdzie najpierw wywiad: w czacie Claude z MCP czy od razu w przeglądarce? | **przyjęte 2026-11-02**: najpierw czat Claude (Z2 bez nowej usługi, sprawdzamy sam wywiad); przeglądarka w Z3 |
| DZ2 | Które źródła brownfield najpierw? | **przyjęte**: Confluence i Jira (już w ci_for_sdlc), potem Slack (konektor dostępny); Teams i Miro po sprawdzeniu konektorów na koncie |
| DZ3 | Skille 10x czy skille tf? | **przyjęte**: skille tf (`core-plan-interview`, `proc-product-discovery`, `arch-tech-selection`, `eng-project-reconstruction`) jako podstawa — są w fabryce i w kontrakcie pracy agentów; ze skilli 10x przenieść tylko to, czego brakuje, po porównaniu |
| DZ4 | Na jakim repo sprawdzić brownfield? | **przyjęte**: sprintdeck albo ShipScope jako „obcy” projekt: mają dokumentację, standardy i historię |
| DZ5 | Czy zmienić kolejność etapów 2–18? | **przyjęte**: Z1 przed etapem 2; Z2 i Z3 przed etapem 3; rozmowa (K-3) razem z konsolą (K-2) |
| DA4 | Stos usługi pdi (otwarte od etapu 4) | do rozstrzygnięcia przed Z3 |
| DZ6 | Co robi pętla przy niespełnionym celu albo `not_met`: wraca do fazy tej samej zmiany czy otwiera nowe zgłoszenie? | **przyjęte 2026-11-02**: wraca do wskazanej fazy tej samej zmiany (z powodem i danymi), z limitem prób (np. 2), potem decyzja człowieka; nowe zgłoszenie tylko dla nowego problemu |
| DZ7 | Kto ustala cele zmiany (`targets`) | **przyjęte**: architekt (tomasz) proponuje w planie, człowiek zatwierdza w B3; dla produktów AI progi ewaluacji obowiązkowe |
| DZ8 | Czy governance blokuje wydanie | **przyjęte**: tak, tylko na B5 (autoryzacja PROD); wcześniej ostrzega |
| DZ9 | Czym izolować fazy (Z8a) | **przyjęte**: kontener (Docker, jest już wymagany przez `sdlc up`) z montowanym tylko klonem repo i listą adresów sieci; sandbox Claude Code jako druga warstwa |
| DZ10 | Osobna aplikacja GitHub dla agentów (Z8b) | **przyjęte**: tak, jedna na organizację, z uprawnieniami tylko do repo produktu (contents, pull requests); tokeny instalacji (GitHub wydaje je zawsze na godzinę) |
| DZ11 | Jaki skaner (Z8c) | **przyjęte**: Semgrep (reguły OWASP, lokalnie i w CI; do sprawdzenia, czy reguły z rejestru pobierają się bez logowania, inaczej reguły zapisane w repo) + skan zależności z menedżera pakietów (`npm audit`, `pip-audit`); CodeQL później, w Actions |
| DZ12 | Drugi model w N1: od tego samego dostawcy czy innego? | **przyjęte 2026-11-02**: inny dostawca (osobny klucz API, koszt w budżecie fazy); bez klucza — inny model Claude z osobnym promptem recenzenta, oznaczony w wyniku |
| DZ13 | Ile zadań w evalach przebiegu (N5) i jaki budżet | **przyjęte**: start: 20 zadań z repo próbnego i sprintdecka, budżet na jedno uruchomienie ustalony w tf; rozbudowa do ok. 200 po pierwszych wynikach |

## 10. Stan

| Krok | Stan |
|---|---|
| Z1 | do zrobienia; [polecenie startowe](polecenia-startowe-zespol.md) |
| Z2 | do zrobienia; [polecenia startowe Z2a i Z2b](polecenia-startowe-zespol.md) |
| Z3 | do zrobienia, po DA4 |
| Z4 | do zrobienia |
| Z5 | do zrobienia, po DZ4 |
| Z6 | do zrobienia, po DZ2 |
| Z7 | do zrobienia (Z7a po Z3) |
| Z8 | do zrobienia; Z8a i Z8c przed etapem 2, [polecenia startowe](polecenia-startowe-zespol.md) |
| Z9 | do zrobienia; N1, N2 i N5 przed etapem 2 |
