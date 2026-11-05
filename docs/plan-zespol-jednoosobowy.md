# Plan: zespół jednoosobowy — greenfield od wywiadu, brownfield od poznania projektu, wszystko w przeglądarce

Data: 2026-11-02 · Status: **plan; decyzje DZ1–DZ5 przyjęte 2026-11-02**, DZ1–DZ14 przyjęte, otwarte DA4; Z10 (niezawodność i obserwowalność) dodane 2026-11-03, DZ15–DZ19 przyjęte 2026-11-03 · Kolejność całości: §0 · Stan wyjściowy: pdi `d66b4bf`, tf 5.55.0,
ShipScope 0.2.67, ci_for_sdlc 0.1.35+ · Powiązane: [plan `sdlc up`](plan-sdlc-lokalnie.md),
[przebieg lokalny](przebieg-lokalny.md#wynik-przebiegu-2026-10-31), [etapy 2–18](polecenia-startowe-sdlc-lokalnie.md),
[automatyzacja i konsola](plan-automatyzacja-i-konsola.md), [jedna platforma](15-jedna-platforma.md)

## 0. Kolejność całości

Stan: 2026-11-03 (kolejność grupy A według DZ19). Stan poszczególnych poleceń startowych: [tabela](polecenia-startowe-zespol.md).

Jedna lista od teraz do końca planu: kroki Z1–Z9 i N1–N11 z tego planu oraz etapy 2–18 z
[poleceń startowych](polecenia-startowe-sdlc-lokalnie.md), po zmianie kolejności z DZ5. Kroki w jednym wierszu mogą iść
równolegle. „Bramka” to warunek przejścia do następnej grupy.

**A. Przed prawdziwym kodem (przed etapem 2)**

Kolejność od 2026-11-03 (DZ19): A1 i A2 zrobione → bramka A6 → A3–A5 i A7 równolegle → A8. Wiersze zostają przy swoich numerach, tabela jest w kolejności wykonania.

| # | Krok | Repo | Po czym | Polecenie startowe |
|---|---|---|---|---|
| A1 | ~~Z1 — wszystkie decyzje zmiany w każdej fazie~~ (**zrobione 2026-11-02**, pdi #110, tf #135 i #136, kontrakt 0.11.0) · ~~Z8a — fazy w kontenerze~~ (**zrobione**, pdi #111, tf 5.56.0) · ~~Z8c-1 — SARIF w ci_for_sdlc~~ (**zrobione**, ci_for_sdlc #109) | pdi + tf · pdi + tf · ci_for_sdlc | — | [jest](polecenia-startowe-zespol.md) |
| A2 | ~~Z8c-2 — skaner w pętli talosa i w CI, razem z N3 (jeden skrypt weryfikacji) i N10 (karencja dla nowych wersji zależności)~~ (**zrobione 2026-11-03**, tf #138; kawałek talosa na `sdlc-proba` #10) | tf | Z8c-1 | [jest](polecenia-startowe-zespol.md) |
| A6 | **Bramka:** ponowny przebieg lokalny na `sdlc-proba` w kontenerze, z jedną zmianą od zgłoszenia do oceny skutku; bez obejść z przebiegu 2026-10-31 | — | A1, A2 (DZ19: przed A3–A5) | [jest](polecenia-startowe-zespol.md#a6--pdi--tf-shipscope-ci_for_sdlc-ponowny-przebieg-lokalny-na-sdlc-proba); lista: [przebieg lokalny](przebieg-lokalny.md); **2026-11-03–05 wynik mieszany** ([wynik](przebieg-lokalny.md#wynik-przebiegu-2026-11-03%E2%80%9305-a6)): §0–§3 zaliczone (Z1 i PRB-2 potwierdzone), delivery dwukrotnie `failed` na `step: cuts` — czeka na PRB-29 (semgrep w obrazie fazy) i PRB-28 (`detail` w `result.json`); §5–§7 pominięte świadomie (bez zmian od 2026-10-31) |
| A3 | N1 — przegląd drugim modelem · N5 — evale przebiegu (20 zadań) z N17 (reguły sędziego) | tf | A6; Z1 | [jest](polecenia-startowe-zespol.md) |
| A4 | Z7b-1 — cele zmiany (`targets`): proponowane w planie, zatwierdzane w B3, sprawdzane przed B4; razem z N4 (pokrycie i testy mutacyjne na zmienionym kodzie) i N20 (co najmniej dwie opcje w planie) | pdi + tf + ci_for_sdlc | A6; Z1, Z8c-1 | [jest](polecenia-startowe-zespol.md) (Z7b-1a, Z7b-1b) |
| A5 | N2 — pętla budujący–recenzent na PR i samonaprawa CI · N12 — weryfikacja przed zakończeniem fazy · N13 — limity tur i czasu, zapętlenie trafia do skrzynki · N15 — zakres zapisu fazy; zmieniają te same pliki (talos, `phase_run.py`, hooki), więc idą po kolei; N13 i N15 mogą podbić kontrakt (wersję uzgadniają z Z2a i Z7b-1a) | pdi + tf (N12: tf; N13: tf + pdi; N15: tf + kontrakt pdi) | A6; Z8a, N1 (N2); N3 zrobione (N12) | jest, stan z 2026-11-03: [N2](polecenia-startowe-zespol.md#n2--pdi--tf-pętla-budujący-recenzent-na-pr-i-samonaprawa-ci), [N12](polecenia-startowe-zespol.md#n12--tf-weryfikacja-przed-zakończeniem-fazy), [N13](polecenia-startowe-zespol.md#n13--tf--pdi-limity-tur-i-czasu-zapętlenie-trafia-do-skrzynki), [N15](polecenia-startowe-zespol.md#n15--tf--pdi-zakres-zapisu-fazy) |
| A7 | Z3-lokalnie — konsola w przeglądarce na Macu (DZ14): `sdlc up` uruchamia ją obok stosu; tablica zmian w trzech pasach, ślad zmiany z krokami, postęp fazy na żywo z `run.progress` (pasek, bieżąca czynność, czas, koszt), skrzynka z przyciskami decyzji; panel „Pliki” w śladzie zmiany (artefakty zmiany i diff bieżącego cięcia na żywo, tylko do odczytu) i boczny panel postępu i kosztu, który dane z OpenTelemetry dostaje w Z10c (DZ18); bez usługi, rozmowy i powiadomień (zostają w Z3, B5) | pdi + tf | A6 (równolegle z A3–A5) | [jest](polecenia-startowe-zespol.md#z3-lokalnie--pdi--tf-konsola-w-przeglądarce-na-macu) |
| A8 | **Etap 2** — scenariusz S5 na sprintdecku (prawdziwy kod i wdrożenie) | pdi + sprintdeck | A3–A5, A7 | [jest](polecenia-startowe-sdlc-lokalnie.md#etap-2--pdi--sprintdeck-scenariusz-s5-na-prawdziwym-wdrożeniu) |

**B. Przed produkcją (przed etapem 3)**

| # | Krok | Repo | Po czym | Polecenie startowe |
|---|---|---|---|---|
| B1 | Z2a — faza `discovery` i bramka B0 · N19 — pytania z opcjami w kontrakcie | pdi | Z1 | [jest](polecenia-startowe-zespol.md) |
| B2 | Z2b — wywiad `/discovery` w mode-pdi, z pytaniami z opcjami (N19) | tf | Z2a i tag kontraktu | jest |
| B3 | Z7b-2 — pętla ulepszeń: ocena skutku `not_met` albo wybicie metryki otwiera zmianę ponownie od wymagań albo architektury, z danymi z produkcji jako wejściem (DZ6: najwyżej 2 próby, potem człowiek) · Z7c + Z8d — pas governance (blokuje B5) i pakiet dowodów · Z8b — tożsamość agentów · Z8g — proxy poświadczeń (token Claude poza kontenerem) · Z10a — SLO produktu i budżet błędów (wyczerpany budżet otwiera pętlę Z7b-2) · Z10d — SBOM i licencje w pakiecie dowodów | pdi + tf + ci_for_sdlc + ShipScope | Z1 | do przygotowania |
| B4 | **Decyzja DA4** — stos usługi pdi | — | — | decyzja właściciela |
| B5 | Z3 — usługa pdi: konsola z A7 jako usługa, rozmowa w konsoli (dawne etapy 4 i 10) i sygnał „czeka na Ciebie”, razem z N11 (karta decyzji przy bramce) i Z10c (obserwowalność przebiegu agentów i miesięczny budżet kosztu) | pdi + tf | DA4, Z2, A7 | do przygotowania |
| B6 | **Etap 3** — z localhosta na produkcję | pdi + ShipScope + tf + sprintdeck | B1–B5, działające Actions | [jest](polecenia-startowe-sdlc-lokalnie.md#etap-3--pdi--shipscope-tf-z-localhosta-na-produkcję) |

**C. Greenfield i brownfield**

| # | Krok | Repo | Po czym | Polecenie startowe |
|---|---|---|---|---|
| C1 | Z4 — greenfield do końca: wybór stosu, bootstrap repo z tf (z N3), lista kroków infrastruktury | tf + pdi | Z2 | do przygotowania |
| C2 | Z5 — onboarding brownfield z N9 (wzorce, testy charakteryzujące, uruchamialność), N6 (mapa projektu z kodu), N14 (oznaczanie treści z zewnątrz) i N18 (sprawdzanie cytatów) | tf + pdi + ci_for_sdlc | Z1 | do przygotowania |
| C3 | Z6 — Slack, potem Teams i Miro jako źródła wiedzy | pdi | Z5 | do przygotowania |
| C4 | N7 — wznawianie przerwanej fazy · N8 — makiety HTML w fazie design · Z10e — wydajność i dostępność (WCAG) w celach zmiany | pdi + tf (+ ci_for_sdlc) | Z8a, Z7b-1 | do przygotowania |

**D. Dalsze etapy (bez zmian, po kolei)**

Etap 5 (graf śladu, rejestr decyzji, panel w Jirze) → etap 6 (autonomia na danych) → etap 7 (etapy flag według reguły,
metryki ochronne, alerty spalania budżetu błędów — Z10b) → etap 8 (uproszczone review, lustro Jira) → etap 9 (incydenty, aplikacja Slacka) → etap 11 (zaległe
kroki G1/G2) → etap 12 (jedno wejście, miary przepływu; razem z Z8e) → etapy 13–14 (łączenie backendów) → etap 15
(pilotaż) → etap 16 (utrzymanie; SLO platformy i SLA dla partnerów — Z10) → etap 17 (cennik) → etap 18 (przegląd na dowodach). Etapy 4 i 10 weszły do Z3.

**Na bieżąco:** Z8f — po każdym przebiegu PRB dotyczące uprzęży zamieniają się w zmiany w tf z evalem; N16 dokłada do tego propozycje wyciągnięte z logów faz. Z7d — przy
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
| Dalej: intencja → … → skutek | jest; od Z1 (2026-11-02) decyzje zmiany z rejestru (`links.chg`) i odpowiedzi na pytania z bramek trafiają do każdej fazy | decyzje z wywiadu trafią tą samą drogą, gdy zapisze je Z2 (z `links.chg`) | Z2 |

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
| Podgląd plików zmiany (DZ18) | brak; artefakty i diff widać tylko w repo i w PR | panel „Pliki” w śladzie zmiany: `intent.md`, `requirements.md`, `plan.md`, `design.md`, `release.yaml` i diff bieżącego cięcia z klonu repo produktu, odświeżane na żywo, tylko do odczytu (bez konfliktów z agentem); przy bramce widać dokładnie to, co się zatwierdza; boczny panel z postępem z `run.progress` (bieżąca czynność, czas, koszt), w Z10c uzupełniany o koszt, tokeny, błędy i odmowy z OpenTelemetry | A7 (Z3-lokalnie), potem Z3 |
| Sygnał „czeka na Ciebie” | brak | powiadomienie w przeglądarce, opcjonalnie na telefon | Z3 |
| Opóźnienia | ShipScope sprawdza zdarzenia co 5 min; lokalnie bez webhooków GitHuba | na produkcji webhooki; lokalnie krótszy `eventsTick` | Z3 |

**Najpierw lokalnie (DZ14):** konsola, postęp na żywo i przyciski decyzji powstają jako Z3-lokalnie (§0, A7), zanim zapadnie DA4: lokalny proces obok stosu `sdlc up`, tylko na `127.0.0.1`, czyta to samo co narzędzia MCP (rejestr, skrzynka, logi przebiegów) i wygląda jak makieta `design/konsola/v2-klikalna/` (trzy pasy, Z7a). Etap 2 na sprintdecku oglądasz już w przeglądarce. Z3 w B5 przenosi tę konsolę do usługi i dokłada rozmowę, wywiad i powiadomienia; wiersze „Kanał do przeglądarki”, „Rozmowa” i „Sygnał” zostają w Z3.

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
| Z1 | **Domknięcie PRB-3:** do każdej fazy trafiają wszystkie decyzje zmiany (z bramek z odpowiedziami na pytania, z triażu, z rejestru z `links.chg`, odpowiedzi na ustalenia ci_for_sdlc); pytanie już rozstrzygnięte nie może wrócić w kolejnym artefakcie. **Zrobione 2026-11-02** ([plan Z1](plan-z1-decyzje-w-fazach.md); pdi #110, tf #135, #136): pole `answers` w decyzji (kontrakt 0.11.0, tag `contract-v0.11.0`), `decide_inbox_item(answers=…)`, decyzje z `links.chg` w wejściu fazy (`decision import`, `decision gate --answers`, wejścia `decision_text`, `answers`, `decisions` w `sdlc-phase.yml`), lista decyzji w prompcie, odmowa przy powtórzonym pytaniu (`repeated_question`) i delivery przy otwartym pytaniu w `plan.md`; zostaje sprawdzenie w przebiegu lokalnym (A6, [lista](przebieg-lokalny.md)) | pdi + tf | — | w powtórzonym przebiegu lokalnym te same pytania nie wracają, a talos nie łamie przyjętych decyzji |
| Z2 | **Wywiad (`discovery`):** faza rozmowy z `core-plan-interview` i `proc-product-discovery`; wynik `docs/project/changes/<CHG>/brief.md` (albo `docs/project/discovery/brief.md` dla produktu) i decyzje w rejestrze; bramka B0 w kontrakcie (wersja minor) | tf + pdi (kontrakt) | Z1, DZ1, DZ3 | wywiad w czacie Claude z MCP kończy się briefem i B0; intencja powstaje z briefu |
| Z3 | **Przeglądarka:** `run.progress` ze `stream-json`; usługa pdi z SSE; konsola v1 (tablica, skrzynka, na żywo) i rozmowa (wywiad, pytania z bramek); sygnał „czeka na Ciebie” | tf + pdi | DA4, DZ1, DZ2 | wywiad i cały przebieg widać i prowadzi się w przeglądarce, bez terminala i bez dopytywania |
| Z4 | **Greenfield do końca:** wybór stosu (`arch-tech-selection`, decyzja `stack`), bootstrap repo ze stosu z tf, lista kroków infrastruktury dla człowieka | tf + pdi (`sdlc new`) | Z2, DZ3 | nowy mały produkt od wywiadu do oceny skutku, bez szablonu `sdlc-sandbox` |
| Z5 | **Onboarding brownfield:** faza `onboarding` (rekonstrukcja z kodu + wyniki ci_for_sdlc z Jiry, Confluence, Figmy) → `standards.md` z dowodami, mapa wiedzy, pytania; B0; standardy w wejściu faz i reguła w ci_for_sdlc | tf + pdi + ci_for_sdlc | Z1 | na „obcym” repo (DZ4) pierwsza zmiana przechodzi zgodnie z jego standardami, a review nie znajduje naruszeń konwencji |
| Z6 | **Źródła rozmów:** Slack, potem Miro (oficjalny serwer MCP Miro, OAuth, dostęp do jednego zespołu) jako źródła wiedzy do onboardingu (cytat i link); Teams po wyjściu serwera MCP Microsoftu z wersji preview | pdi (+ konektory) | Z5, DZ2 | mapa wiedzy cytuje wątki i tablice; sprzeczności z Confluence są w pytaniach |
| Z7 | **Układ z cyklu aplikacji AI** (§8.1): trzy pasy w konsoli i dokumentacji, bramka „spełnia cele?” z krótką pętlą do wskazanej fazy, pas governance przez wszystkie fazy, opcjonalna gałąź dla produktów, które same są aplikacją AI | pdi + tf + ci_for_sdlc (+ ShipScope) | Z1, Z3 (pasy w konsoli) | patrz §8.1, Z7a–Z7d |
| Z8 | **Uprząż i dowody** (§8.2): izolacja faz, tożsamość agentów, skaner bezpieczeństwa w pętli talosa i w CI, pakiet dowodów zmiany, miary wartości, uprząż ucząca się z PRB, proxy poświadczeń | tf + pdi (+ ci_for_sdlc, ShipScope) | Z1 | patrz §8.2, Z8a–Z8g |
| Z9 | **Pętle jakości i kontekst** (§8.3): przegląd drugim modelem, pętla budujący–recenzent i samonaprawa CI, jeden skrypt weryfikacji, cele pokrycia i testy mutacyjne, evale przebiegu, kontekst przycięty do fazy, wznawianie pracy, makiety HTML, wzorce i testy charakteryzujące w brownfield, łańcuch dostaw, karta decyzji przy bramce, weryfikacja przed zakończeniem fazy, limity i zapętlenie, oznaczanie treści z zewnątrz, zakres zapisu fazy, uczenie z logów faz, reguły sędziego, sprawdzanie cytatów, pytania z opcjami, alternatywy w architekturze | tf + pdi (+ ci_for_sdlc) | Z1, Z8c | patrz §8.3, N1–N20 |
| Z10 | **Niezawodność i obserwowalność** (§8.5): SLO produktu i budżet błędów w planie wydania, alerty spalania budżetu przy etapach flag, obserwowalność przebiegu agentów (OpenTelemetry z Claude Code) z miesięcznym budżetem kosztu, SBOM i licencje, wydajność i dostępność w celach zmiany; SLA tylko jako decyzja człowieka | pdi + tf + ShipScope (+ ci_for_sdlc) | Z1, Z7b-1, Z8a | patrz §8.5, Z10a–Z10e |

Kolejność: Z1 → Z3-lokalnie (konsola na Macu, DZ14) → Z2 (w czacie Claude, bez nowej usługi) → Z3 → Z4 i Z5 równolegle → Z6. Z7: Z7b i Z7c mogą iść
razem z Z1–Z2 (nie zależą od konsoli), Z7a razem z Z3-lokalnie (trzy pasy w konsoli), Z7d przy pierwszym produkcie, który jest aplikacją AI. Z8: Z8a i Z8c
przed kolejnym przebiegiem z prawdziwym kodem (etap 2 na sprintdecku), Z8b przed etapem 3 (produkcja), Z8d razem z Z7c, Z8e
z etapem 12 (G7), Z8f po każdym przebiegu, Z8g przed etapem 3. Z9: N1, N2 i N5 przed etapem 2, razem z N2 także N12, N13 i N15; N9, N14 i N18 razem z Z5; N16 razem z Z8f; N17 razem z N5; N19 razem z Z2; N20 razem z Z7b-1;
pozostałe razem z krokami, do których są przypięte (§8.3). Z10: Z10a i Z10d razem z Z7b-2 i Z8d (grupa B), Z10c razem z Z3,
Z10e po Z7b-1, Z10b z etapem 7 (G5), SLO platformy i SLA w etapie 16 (§8.5).

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
| 10. Obserwowalność i monitoring | `metric_watch.py` (pasma 3σ), ShipScope (`/metrics`, `/flow`) | metryki ochronne produktu (G5, etap 7); SLO, budżet błędów i alerty spalania (Z10a, Z10b); obserwowalność samych agentów (Z10c) |
| 11. Informacja zwrotna i analiza błędów | ocena skutku (`met`/`not_met`), `metric.breached` → nowe zgłoszenie | analiza przyczyny przy `not_met` jako wejście dla kolejnej iteracji |
| „Update & Experiment”, pętla do faz 2–7 | `not_met` i wybicie metryki otwierają nowe PRB: cały cykl od triażu | ponowne otwarcie tej samej zmiany od wymagań albo architektury, z danymi z produkcji (Z7b) |
| 12. Governance przez wszystkie fazy | rozproszone: rejestr decyzji, graf śladu, typy chronione (DA2), `security-reviewer`, zasady źródeł (A5) | jeden pas: co w każdej fazie sprawdzono pod kątem danych osobowych, dostępów, zabezpieczeń i audytu (Z7c) |

**Kroki**

| Krok | Co | Repo | Zależy od | Gotowe, gdy |
|---|---|---|---|---|
| Z7a | **Trzy pasy:** „Zaprojektuj i zbuduj” (zgłoszenie, wywiad, intencja, wymagania, architektura, design, gotowość, budowa), „Oceń i wydaj” (review, cele zmiany, B4/B5, wdrożenie na PROD ukryte za flagą), „Wdróż, obserwuj, ulepszaj” (udostępnianie etapami, wydanie R1, ocena skutku, pętla do pasa 1); użytkownik w każdej chwili widzi pas i bieżący etap: na tablicy kolumny faz są pogrupowane w pasy, a w śladzie zmiany nad etapami są pasy z „teraz” i w nagłówku „Pas N z 3 · teraz: … · dalej: …” (makieta z pasami: `design/konsola/`, klikalna `design/konsola/v2-klikalna/`, wprowadzona 2026-11-02); `stage` każdej fazy i bramki w kontrakcie, tablica konsoli i dokumentacja według pasów | pdi (kontrakt, konsola) | Z3 | na tablicy widać, w którym pasie jest każda zmiana |
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
| Z8g | **Proxy poświadczeń:** prawdziwy token Claude nie wchodzi do kontenera fazy; kontener dostaje zastępczą wartość, a bramka na hoście (obok proxy wyjścia z Z8a) dokłada prawdziwe poświadczenie do żądań do API Claude; do sprawdzenia w dokumentacji przed krokiem: czy wystarczy `ANTHROPIC_BASE_URL` wskazujący lokalną bramkę (bez przechwytywania TLS), czy potrzebne jest proxy z własnym CA | dziś `CLAUDE_CODE_OAUTH_TOKEN` jest w środowisku kontenera (Z8a), więc wstrzyknięte polecenie może go odczytać i wysłać na dozwolony host; wzorzec „secretless credential proxy” z dokumentu Harness Engineering (Omnigent, Codex), §8.3 | pdi (`phase_sandbox`, proxy); przed etapem 3 | w kontenerze fazy nie ma prawdziwego tokenu (`env` i pliki), a faza i tak rozmawia z API; próba wysłania tokenu na dozwolony host wysyła tylko wartość zastępczą |


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
| N2 | **Pętla budujący–recenzent na PR i samonaprawa CI:** review → sprawdzenie uwag (N1) → poprawka → ponowny review, z limitem rund; pętla kończy się wcześniej, gdy zostają tylko uwagi poniżej progu wagi (np. bez blokujących i ważnych), a uwagi poniżej progu idą do PR jako lista; przy czerwonym CI agent czyta log, poprawia i czeka na zielone; człowiek widzi PR dopiero po zielonym CI i zamkniętych uwagach; PR talosa ma stałą sekcję „Przewodnik dokończenia”: co zrobione, co zostaje dla człowieka (pliki, kroki), decyzje podjęte poza planem z prośbą o zatwierdzenie, ryzyka | wszystkie cztery; przewodnik dokończenia: podcast z Blitzy | po fazie delivery (pdi `dispatch_local`, tf `sdlc-phase.yml`) | PR talosa trafia do człowieka z zielonym CI i zamkniętymi uwagami albo z wyraźnym „nie udało się po N rundach”, zawsze z przewodnikiem dokończenia |
| N3 | **Jeden skrypt weryfikacji** (formatter, lint, typy, testy, skan bezpieczeństwa Z8c) wskazany w pierwszej linii CLAUDE.md produktu i uruchamiany tak samo w CI | Lean TECHniques, Claude Code | tf (szablon CLAUDE.md, bootstrap Z4), Z8c | talos i CI uruchamiają to samo polecenie z tym samym wynikiem |
| N4 | **Cele pokrycia i testy mutacyjne:** pokrycie 100% z jawnie oznaczonymi wyjątkami; testy mutacyjne (StrykerJS dla JS/TS, mutmut dla Pythona) tylko na zmienionym kodzie, bo cały projekt trwa za długo; sprawdzają, czy testy wykrywają zmianę zachowania | Lean TECHniques | Z7b (`targets` zmiany), ci_for_sdlc | cel pokrycia i progi mutacji są w `targets`, a ich niespełnienie zatrzymuje zmianę przed B4 |
| N5 | **Evale przebiegu:** zestaw 20–200 prawdziwych zadań z przeszłości (zmiany i cięcia z repo próbnego i sprintdecka), uruchamiany po każdej zmianie modelu, skilla albo promptu fazy; mierzy wynik, koszt, liczbę czytanych plików i przyjęcie; także na tańszych modelach | Open Mercato, Claude Code | tf (evale skilli już są), „evale flow” z planu jednego flow | zmiana modelu albo skilla nie wchodzi bez przebiegu evali, a raport porównuje wynik i koszt |
| N6 | **Kontekst przycięty do fazy:** każda faza ładuje tylko swoje skille (klasyfikator zadania) i dostaje tylko swoje narzędzia i serwery MCP (lista per faza, np. `--allowedTools`; przy kilkudziesięciu narzędziach model gorzej je dobiera); mapa projektu (API, zdarzenia, ekrany, moduły) generowana z kodu przy buildzie zamiast przeszukiwania repo | Open Mercato, Overcut | tf (persony, instalacja), rekonstrukcja z kodu (Z5) | faza czyta wyraźnie mniej plików i tokenów przy tym samym wyniku evali (N5) |
| N7 | **Wznawianie przerwanej pracy:** notatka w PR, co z planu zrobione, a co nie (ta sama sekcja co przewodnik dokończenia z N2); po błędzie faza rusza od ostatniego kroku zamiast od zera | Open Mercato, Overcut | pdi `dispatch_local`, talos | `retry_dispatch` po błędzie w połowie delivery kończy tylko brakujące cięcia |
| N8 | **Klikalne makiety HTML** w design systemie produktu; komentarze do komponentów zapisywane jako JSON i przekazywane talosowi; gdy nie ma pliku Figmy | Open Mercato | faza design (tf, natalia), `design.md` | design-review działa bez Figmy, a talos dostaje komentarze z makiety jako wejście |
| N9 | **Brownfield: wzorcowa implementacja i testy charakteryzujące.** `standards.md` wskazuje pliki do naśladowania, bo agenci kopiują istniejące wzorce. Przed zmianą w kodzie legacy powstają testy obecnego zachowania, a aplikacja musi dać się uruchomić lokalnie. `standards.md` wymienia też wewnętrzne biblioteki, usługi i zestaw UI produktu; talos ich używa, a gdy potrzebnego komponentu w nich brakuje, zgłasza pytanie albo ustalenie zamiast pisać własny zamiennik obok. | Lean TECHniques; wewnętrzne komponenty: podcast z Blitzy | Z5 | onboarding kończy się listą wzorców, uruchamialną aplikacją i testami charakteryzującymi obszar pierwszej zmiany; zmiana, która potrzebuje brakującego komponentu, daje pytanie, a nie nowy komponent |
| N10 | **Łańcuch dostaw:** nowa wersja zależności wchodzi najwcześniej 7 dni po publikacji, przez ustawienia menedżera pakietów: npm `min-release-age` (dni, od npm 11.10), pnpm `minimumReleaseAge` (minuty, od 10.16; w v11 domyślnie 1 dzień), Yarn `npmMinimalAgeGate`, uv `exclude-newer`; pliki blokad w repo; uwaga na Dependabota z `--frozen-lockfile` w pnpm 11; opcjonalnie własny rejestr pakietów | Lean TECHniques | Z8c (obok skanu zależności) | dodanie świeżo opublikowanej wersji zatrzymuje kawałek z wyjaśnieniem |
| N11 | **Karta decyzji przy bramce:** streszczenie zmiany, diagram architektury przed i po, plusy i minusy | Open Mercato | konsola (Z3), skrzynka pdi | bramki B3 i approve-for-implementation pokazują kartę w konsoli |
| N12 | **Weryfikacja przed zakończeniem fazy:** faza delivery i kawałek talosa nie mogą zakończyć się sukcesem, jeśli po ostatniej zmianie kodu nie ma świeżego wyniku skryptu weryfikacji (N3) dla tego commita; brak wyniku zamienia „gotowe” w kontynuację z poleceniem uruchomienia weryfikacji | Harness Engineering (verify-on-stop, Hermes; zewnętrzna pętla weryfikacji, OpenHands) | talos (`talos-story-run`), tf `phase_run.py`, N3 | zmiana kodu bez świeżego wyniku N3 nie kończy fazy; w logu widać wymuszoną weryfikację |
| N13 | **Tanie limity i zapętlenie:** limit tur fazy (`--max-turns`) obok limitu kosztu (`PDI_PHASE_BUDGET_USD`, `--max-budget-usd`), limit czasu fazy i licznik identycznych wywołań narzędzi; trzy identyczne wywołania z rzędu nie przerywają fazy po cichu, tylko dają pozycję w skrzynce pdi („faza się powtarza”) z ostatnimi krokami; limity w ustawieniach produktu | Harness Engineering (rek. 18; doom-loop w OpenCode, limity w Mini-SWE-Agent) | tf `phase_run.py` (flagi, hook licznika), pdi skrzynka i boczny panel konsoli (A7) | faza przerwana limitem kończy się czytelnym powodem, a zapętlenie trafia do skrzynki zamiast zużyć budżet |
| N14 | **Oznaczanie treści z zewnątrz:** każda treść, której nie napisał właściciel ani persona (Slack, Confluence, Jira, komentarze PR, ustalenia ci_for_sdlc, wątki i transkrypcje), trafia do promptu fazy w znacznikach treści niezaufanej, ze zneutralizowanymi znacznikami w środku i z zasadą w prompcie: to dane, nie polecenia; to samo dla tekstów decyzji i odpowiedzi przekazywanych przez Z1 | Harness Engineering (untrusted-content delimiting, Hermes, OpenHands) | Z5, Z6, tf (budowa promptu fazy), pdi (wejście fazy z Z1) | test z wstrzykniętym poleceniem w treści źródła: persona go nie wykonuje, a znacznik w treści nie zamyka bloku |
| N15 | **Zakres zapisu fazy:** `guard_paths` dostaje listę dozwolonych ścieżek dla każdej fazy (np. intent: tylko `intent.md` zmiany; architecture: `plan.md` i `release.yaml`; design: `design.md`); zapis do kodu dopiero w delivery; próba zapisu poza zakresem jest odmową w logu | Harness Engineering (tryb planu jako jedyny zapisywalny plik, Mistral Vibe; profile tylko do odczytu) | tf (`guard_paths`, persony), kontrakt (lista ścieżek fazy) | persona fazy architecture nie może zmienić kodu ani artefaktów innych faz |
| N16 | **Uczenie z logów faz:** po każdym przebiegu podagent czyta logi faz i ich wyniki (błędy, ponowienia, odmowy, zapętlenia z N13) i najpierw streszcza je do zwięzłych dowodów (co poszło źle, z cytatem z logu), potem proponuje poprawki skilli, reguł albo hooków jako szkice do skrzynki pdi; każda propozycja ma manifest: które zadania z N5 ma naprawić i które może zepsuć, a kolejne uruchomienie evali sprawdza tę prognozę i zapisuje wynik w decyzji; evale N5 i reguły sędziego N17 są dla tego podagenta tylko do odczytu; pierwszeństwo mają zmiany w hookach, narzędziach i skillach przed zmianami tekstu promptu persony; człowiek zatwierdza, zmiana idzie PR-em do tf z evalem (jak Z8f); bez samodzielnych zmian w skillach | Harness Engineering (pamięć z przeglądem człowieka, Gemini CLI; samodoskonalące się skille, Hermes); manifest i ewaluator tylko do odczytu: omówienie pracy „Agentic Harness Engineering” (Zundamon) | Z8f, N5, N17, skrzynka pdi | po przebiegu w skrzynce są propozycje z logów z cytatem z logu, a zatwierdzona przechodzi evale N5; raport podaje, czy prognoza z manifestu się sprawdziła |
| N17 | **Reguły sędziego w evalach:** ocena według skali z przykładem dla każdego poziomu (np. 1–5 dla poprawności, zgodności z decyzjami, stylu); przy porównaniu dwóch wyników sędzia ocenia je w obu kolejnościach, a różnica między kolejnościami trafia do raportu; kontrola, czy sędzia nie nagradza długości; oceniany model nigdy nie jest sędzią; temperatura 0 tam, gdzie sędzia jest wywoływany przez API | wystąpienie T. Ducina (LLM as a judge) | N5, N1 | raport evali podaje wynik obu kolejności i zgodność sędziego z oceną człowieka na próbce |
| N18 | **Sprawdzanie cytatów:** każdy cytat, na którym opiera się zasada albo decyzja, jest najpierw sprawdzany deterministycznie (czy tekst cytatu jest w źródle pod podanym linkiem), potem modelem (czy teza wynika z cytatu); cytat, którego nie ma w źródle, odrzuca zasadę albo decyzję z wyjaśnieniem | wystąpienie T. Ducina (trustworthy generation, verifier) | `standards.md` i mapa wiedzy (Z5), źródła rozmów (Z6), decyzje z wątków (A5 w pdi), automatyczne zamykanie pytań w ci_for_sdlc (D-A2) | zmyślony cytat w teście nie przechodzi, a każda zasada w `standards.md` ma potwierdzony cytat |
| N19 | **Pytania z opcjami:** pytanie w wywiadzie (Z2) i przy bramce (Z1, `questions`) ma opcje do wyboru z rekomendowaną odpowiedzią i pole „inne”; persona zadaje je przez strukturę zgodną ze schematem kontraktu, a pytanie niezgodne ze schematem jest odrzucane i ponawiane (najwyżej 2 razy); konsola (A7) pokazuje opcje jako przyciski, a odpowiedź wraca jako `answers` | wystąpienie T. Ducina (clarify jako narzędzie ze schematem) | kontrakt (Z2a), tf (Z2b, persony), konsola (A7, Z3) | większość odpowiedzi w wywiadzie to wybór opcji, a w rejestrze decyzji są odpowiedzi ze strukturą |
| N20 | **Alternatywy w architekturze:** `plan.md` zawiera co najmniej dwie rozważone opcje z plusami, minusami i kosztem, z wyborem i powodem; odrzucone opcje trafiają do uzasadnienia decyzji B3, a karta decyzji (N11) pokazuje porównanie; przed krokiem sprawdzić, czy persona tomasz (`arch-tech-selection`, ADR) już tego wymaga, i dopisać tylko brakującą część | wystąpienie T. Ducina (tree/graph of thoughts: architekt nie bierze pierwszego rozwiązania) | tf (tomasz, faza architecture), ci_for_sdlc (reguła sprawdzająca), N11 | plan z jedną opcją dostaje ustalenie przed B3 |

N12–N16 i Z8g pochodzą z dokumentu „Harness Engineering: Anatomy, Architecture, and Evolution of Coding Agents” (Barbaste i in., Wavestone AI Lab, arXiv:2609.00006, lipiec 2026; plik od właściciela, przeczytany 2026-11-03): porównanie kodu źródłowego jedenastu harnessów, 29 wzorców i 18 rekomendacji. Dokument potwierdza kierunek Z8 i Z9 (zasady jako konfiguracja z twardym minimum, izolacja z proxy wyjścia, recenzent od innego dostawcy, skille przed MCP, wyszukiwanie deterministyczne zamiast embeddingów, jeden agent na fazę, pamięć z przeglądem człowieka). Nie przejmujemy: frameworków agentowych (LangChain, LangGraph i podobnych), wyszukiwania wektorowego w kodzie ani rozbudowanego wykrywania zapętleń. Na później: granica adaptera w `phase_run.py` (albo ACP), żeby harness dało się wymienić, gdy N1 dostanie drugiego dostawcę.

N17–N20 i uzupełnienia N2 i N6 pochodzą z wystąpienia Tomasza Ducina „Context Engineering Patterns” (automatyczna transkrypcja bez slajdów, plik od właściciela, przeczytana 2026-11-03). To opinie i doświadczenie prelegenta, nie wyniki badań. Wystąpienie potwierdza też Z1 i N6 (kontekst podawany deterministycznie przed pierwszym wywołaniem), DZ12 (sędzia nie jest jednym z kandydatów) i N13. Nie przejmujemy teraz wyszukiwania hybrydowego z embeddingami i rerankerem (do Z6 najpierw wyszukiwanie pełnotekstowe) ani taniego modelu jako filtra tematu na wejściu (ma sens dopiero przy publicznym przyjmowaniu zgłoszeń; triaż zostaje u człowieka).

Rozszerzenia N2, N7, N9 i N16 (przewodnik dokończenia, wewnętrzne komponenty, manifest zmiany uprzęży) pochodzą z dwóch materiałów od właściciela, przeczytanych 2026-11-03: omówienia pracy „Agentic Harness Engineering: Observability-Driven Automatic Evolution of Coding Agent Harnesses” w filmie Zundamon's AI Paper Explained #34 (streszczenie, nie sama praca; transkrypcja z błędami, liczb nie cytujemy) i podcastu Modern CTO z Brianem Elliottem (Blitzy) i Tomem Jacksonem (RSM) „How Agentic SDLC Turned a 5-month Project Into 5 Days” (rozmowa z dostawcą; liczby podaje dostawca i jego klient, nie są dowodem). Podcast potwierdza też Z5 i N9 (najpierw opis systemu, dokumentacja i testy obecnego zachowania), plan zatwierdzany przez człowieka i przesunięcie wąskiego gardła na to, czego się chce (Z2, DZ5).

### 8.4. Weryfikacja źródeł

Sprawdzone 2026-11-02 w internecie: to, na czym opierają się kroki Z7–Z9. „✓” — potwierdzone; „?” — do sprawdzenia
w praktyce przy realizacji kroku; „✗” — nie potwierdzone, nie cytujemy.

| Teza | Wynik | Krok | Źródło |
|---|---|---|---|
| Kod z AI zawiera podatności z OWASP Top 10 | ✓ jako wynik benchmarku: 80 zadań, ponad 100 modeli, 45% przypadków z podatnością; Java 72%; raport z wiosny 2026 ma inne liczby | Z8c | [Veracode, komunikat](https://www.veracode.com/press-release/ai-generated-code-poses-major-security-risks-in-nearly-half-of-all-development-tasks-veracode-research-reveals/), [blog](https://veracode.com/blog/genai-code-security-report) |
| Karencja dla nowych wersji zależności | ✓ wbudowana: npm `min-release-age` (11.10), pnpm `minimumReleaseAge` (10.16; v11 domyślnie 1 dzień), Yarn `npmMinimalAgeGate`; znany problem z Dependabotem w pnpm 11 | N10 | [classmethod](https://dev.classmethod.jp/en/articles/pnpm-11-minimum-release-age-dependabot-ci-failure/), [gist](https://gist.github.com/mcollina/b294a6c39ee700d24073c0e5a4e93104) |
| Sandbox Claude Code: sieć i pliki | ✓ `network.allowedDomains`, `filesystem.denyRead`, `failIfUnavailable`; listy z repo łączą się z innymi, a luzowanie blokują dopiero ustawienia zarządzane (`allowManagedDomainsOnly`, `allowUnsandboxedCommands: false`); sandbox obejmuje tylko polecenia powłoki; w kontenerze `enableWeakerNestedSandbox` — potwierdzone w dokumentacji i lokalnie 2026-11-02 ([plan Z8a](plan-z8a-izolacja-faz.md)) | Z8a | [Sandboxing](https://code.claude.com/docs/en/sandboxing), [Settings](https://code.claude.com/docs/en/settings) |
| Token Claude w kontenerze | ✓ `claude setup-token` daje token na rok; ✓ błąd przy pierwszym uruchomieniu (`hasCompletedOnboarding`, #73403) zamknięty 2026-07-02, w 2.1.310 `--print` używa tokenu bez flagi (sprawdzone lokalnie), obraz i tak ją zapisuje; `ANTHROPIC_API_KEY` ma pierwszeństwo przed tokenem, więc tylko jedna | Z8a | [zgłoszenie](https://claudeissues.com/issue/73403-bug-claude-code-oauth-token-ignored-on-first-run-due-to-onboarding-gate), [poradnik](https://www.vellum.ai/skills/headless-claude-code) |
| Token instalacji aplikacji GitHub | ✓ wygasa zawsze po godzinie | Z8b, DZ10 | [GitHub Docs](https://docs.github.com/en/enterprise-server@3.21/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation) |
| Semgrep z regułami OWASP bez konta | ? skan lokalny bez konta działa; nie potwierdzone, czy `p/owasp-top-ten` pobiera się bez logowania | Z8c, DZ11 | [Semgrep: JSON i SARIF](https://docs.semgrep.dev/semgrep-appsec-platform/json-and-sarif), [poradnik](https://aicodereview.cc/blog/how-to-setup-semgrep) |
| Wywiad grill-me | ✓ skill Matta Pococka (MIT): jedno pytanie naraz, z rekomendacją, bez pytań o to, co agent znajdzie sam; wariant `grill-with-docs` zapisuje ustalenia w słowniku i ADR | Z2 | [claudemarket](https://claudemarket.ai/skills/mattpocock/grill-me), [Medium](https://medium.com/@marc.bara.iniesta/the-ai-coding-repo-that-went-viral-because-it-adds-friction-e2b5c4d2fcc2) |
| SSDF dla AI | ✓ NIST SP 800-218A, finalny profil SSDF dla AI generatywnego (lipiec 2024) | Z8d | [NIST](https://csrc.nist.gov/pubs/sp/800/218/a/final) |
| Miro i Teams przez MCP | ✓ Miro: oficjalny serwer MCP; ? Teams: serwer Microsoftu w wersji preview | Z6 | [Miro](https://developers.miro.com/docs/connecting-to-miro-mcp), [przegląd Teams](https://eseospace.com/blog/microsoft-teams-mcp-server/) |
| Spotify Honk | ✓ ponad 1500 scalonych PR-ów; weryfikacja oddzielona od agenta; PR po pełnej weryfikacji | N2 | [Spotify](https://engineering.atspotify.com/2025/11/spotifys-background-coding-agent-part-1), [InfoQ](https://infoq.com/news/2026/03/spotify-honk-rewrite) |
| Stripe Minions, 1300 PR tygodniowo | ✗ tylko wzmianka na InfoQ, bez materiału Stripe | — | — |
| Open Mercato | ✓ organizacja na GitHubie, MIT, TypeScript | N6–N9 | [GitHub](https://github.com/open-mercato) |
| Testy mutacyjne | ✓ StrykerJS (JS/TS), mutmut (Python); uruchamiać na zmienionym kodzie | N4 | [przegląd](https://playbooks.com/skills/secondsky/claude-skills/mutation-testing) |
| Telemetria Claude Code przez OpenTelemetry | ✓ sprawdzone 2026-11-03: metryki i zdarzenia (`CLAUDE_CODE_ENABLE_TELEMETRY=1`, `OTEL_METRICS_EXPORTER`, `OTEL_LOGS_EXPORTER`, `OTEL_EXPORTER_OTLP_PROTOCOL` bez wartości domyślnej, `OTEL_EXPORTER_OTLP_ENDPOINT`); metryki m.in. `claude_code.cost.usage`, `claude_code.token.usage`; zdarzenia m.in. `claude_code.api_request`, `claude_code.tool_result`, `claude_code.tool_decision`; ślady w becie (`CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1`); treść promptów redagowana, chyba że `OTEL_LOG_USER_PROMPTS=1` | Z10c | [Monitoring](https://code.claude.com/docs/en/monitoring-usage) |
| Alerty spalania budżetu błędów w kilku oknach | ? nie sprawdzone: strona sre.google niedostępna z sesji 2026-11-03; sprawdzić liczby (tempa i okna) przed Z10b | Z10b | [SRE Workbook: Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/) |
| SBOM z menedżera pakietów (`npm sbom`, CycloneDX i SPDX) | ? nie sprawdzone: docs.npmjs.com niedostępne z sesji 2026-11-03; sprawdzić wersję npm i formaty przed Z10d | Z10d | [npm sbom](https://docs.npmjs.com/cli/v11/commands/npm-sbom) |
| Harness Engineering: wzorce i rekomendacje dla N12–N16, Z8g | ✓ jako przegląd kodu źródłowego (preprint, nie recenzowany); Claude Code analizowany z krążącej kopii kodu, więc jego szczegółów stamtąd nie traktujemy jako faktów; wyniki SWE-Bench podane przez autorów narzędzi | N12–N16, Z8g | arXiv:2609.00006 (plik od właściciela, 2026-11-03) |
| Limity fazy w Claude Code | ✓ sprawdzone 2026-11-03: `--max-turns` (tylko tryb print, domyślnie bez limitu) i `--max-budget-usd` (tylko tryb print, według szacunku kosztu po stronie klienta, koszt może przekroczyć limit, liczy też podagentów; pełne działanie od v2.1.217) | N13 | [CLI reference](https://code.claude.com/docs/en/cli-reference) |
| Wzorce kontekstu: sędzia, cytaty, pytania z opcjami, alternatywy | ✓ jako doświadczenie praktyka (transkrypcja wystąpienia, bez slajdów i bez źródeł badań); obserwacje o uwadze modelu w środku kontekstu prelegent sam określa jako niepewne | N17–N20, N2, N6 | T. Ducin, „Context Engineering Patterns” (plik od właściciela, 2026-11-03) |
| Manifest zmiany uprzęży i ewaluator tylko do odczytu | ? metoda z omówienia pracy w filmie, nie z samej pracy; przed N16 przeczytać pracę u źródła i sprawdzić wyniki | N16 | Zundamon's AI Paper Explained #34 (plik od właściciela, 2026-11-03) |
| Przewodnik dokończenia w PR i wewnętrzne komponenty | ✓ jako praktyka opisana przez dostawcę i klienta (bez danych do sprawdzenia) | N2, N7, N9 | podcast Modern CTO z Blitzy i RSM (plik od właściciela, 2026-11-03) |

**Zasada na dalej.** Każde polecenie startowe wymaga, by sesja przed planem sprawdziła zachowanie zewnętrznych
narzędzi, API i ustawień w oficjalnej dokumentacji (z datą), a to, czego dokumentacja nie rozstrzyga, sprawdziła
lokalnie, i zapisała źródła w swoim planie. Przed każdą grupą z §0 (A–D) tabela wyżej jest sprawdzana ponownie dla
kroków tej grupy.

### 8.5. Z10 — niezawodność i obserwowalność

Źródło: rozmowa 2026-11-03 (pytanie o obserwowalność, SLO/SLI/SLA, ADLC i uprząż). Luki w planie: (1) zmiana produktu
nie ma SLO ani budżetu błędów, więc etapy flag i pętla ulepszeń opierają się tylko na metrykach ochronnych z pasmami 3σ;
(2) przebieg agentów widać w logu fazy i `run.progress`, ale nie ma metryk ani śladów z samego Claude Code, a koszt ma
tylko limit na fazę (DL5), bez limitu na miesiąc; (3) pakiet dowodów (Z8d) nie ma listy składników (SBOM) ani licencji;
(4) cele zmiany (Z7b-1) nie obejmują jawnie dostępności i wydajności interfejsu. SLO, budżet błędów i alerty ShipScope
dla jego własnego serwera (`server/SLO.pl.md`) są wzorem; w tym kroku przenosimy je na produkty, a w etapie 16 na
platformę. Plików ShipScope w tej sesji nie czytano (brak dostępu), więc szczegóły wzoru sprawdza sesja kroku.

**Pojęcia w planie:** SLI to mierzona wielkość (np. odsetek udanych żądań, czas odpowiedzi p95); SLO to cel dla SLI
w oknie (np. 99,5% w 28 dni); budżet błędów to 100% − SLO; SLA to obietnica wobec klienta z konsekwencjami — u nas
zawsze decyzja człowieka (koszt i zobowiązanie), nigdy automat.

| Krok | Co | Repo | Zależy od | Gotowe, gdy |
|---|---|---|---|---|
| Z10a | **SLO produktu w planie wydania:** pole `slo` w `release.yaml` (kontrakt, wersja minor): SLI ze źródłem (ShipScope, analityka z G5 albo `/metrics` produktu), cel, okno; architekt (tomasz) proponuje SLO w planie razem z `targets`, człowiek zatwierdza w B3 (jak DZ7); ShipScope liczy SLI i pozostały budżet błędów dla każdego środowiska; wyczerpany budżet wysyła zdarzenie (np. `slo.budget_exhausted`) do pdi, które otwiera pętlę Z7b-2 z `return_to` i danymi SLI jako wejściem, a do czasu powrotu budżetu wstrzymuje kolejne etapy flag tej zmiany; produkt bez SLO dostaje ostrzeżenie w B3 i odmowę w B5 (DZ15) | pdi (kontrakt) + tf (tomasz) + ShipScope | Z1, Z7b-1 | w repo próbnym zmiana z SLO, które celowo wyczerpujemy w teście, wraca do wskazanej fazy z powodem, a etap flagi czeka |
| Z10b | **Alerty spalania budżetu i etapy flag:** alert, gdy budżet znika szybciej niż zakłada okno (kilka okien: szybkie i wolne spalanie), zamiast progu na jednej metryce; `flag.stage_advance` (A4) wymaga zapasu budżetu, a szybkie spalanie w trakcie etapu daje propozycję wycofania na poziomie 1 (jak dziś w etapie 7) | ShipScope + pdi | Z10a, G5 (etap 7) | w teście szybkie spalanie zatrzymuje etap flagi i proponuje wycofanie z dowodem |
| Z10c | **Obserwowalność przebiegu agentów:** w kontenerze fazy (Z8a) Claude Code wysyła telemetrię OpenTelemetry (`CLAUDE_CODE_ENABLE_TELEMETRY=1`, eksport OTLP) do kolektora uruchamianego przez `sdlc up` (adres kolektora na liście dozwolonych adresów Z8a); atrybuty zmiany, fazy i persony przy każdej metryce; boczny panel observability w konsoli (z A7, obok postępu z `run.progress`, DZ18) pokazuje koszt i tokeny (`claude_code.cost.usage`, `claude_code.token.usage`), błędy i odmowy API, decyzje o narzędziach na zmianę i fazę; ślady (beta) tylko opcjonalnie; treść promptów zostaje zredagowana (domyślnie); do tego **miesięczny budżet kosztu** całego ekosystemu z ostrzeżeniem przy 80% i zatrzymaniem nowych faz przy 100% (decyzja człowieka, żeby iść dalej) | pdi (`sdlc up`, konsola) + tf (`sdlc-phase.yml`) | Z8a, A7 | po przebiegu konsola pokazuje koszt i błędy każdej fazy z telemetrii, zgodne z logiem fazy; przekroczenie budżetu miesięcznego zatrzymuje kolejną fazę z pozycją w skrzynce |
| Z10d | **SBOM i licencje:** przy każdym PR talosa lista składników (SBOM w formacie CycloneDX albo SPDX) z menedżera pakietów i sprawdzenie licencji nowych zależności według listy dozwolonych w `standards.md` (Z5) albo w ustawieniach produktu; SBOM i wynik w pakiecie dowodów (Z8d) | tf (talos, `change-check.yml`) + ci_for_sdlc (ustalenie) + pdi (Z8d) | Z8c, Z8d | nowa zależność z licencją spoza listy zatrzymuje kawałek z wyjaśnieniem, a `export_evidence` zawiera SBOM |
| Z10e | **Wydajność i dostępność w celach zmiany:** w `targets` (Z7b-1) opcjonalne progi: czas odpowiedzi p95 dla zmienionych ścieżek, budżet rozmiaru paczki frontendu, automatyczny test dostępności (WCAG 2.2 AA, poziom do decyzji) zmienionych ekranów; natalia proponuje progi dostępności w design, tomasz wydajności w planie | tf (natalia, tomasz, testy) + ci_for_sdlc (reguła TEST) | Z7b-1 | ekran z brakującą etykietą pola albo zbyt wolna ścieżka zatrzymuje zmianę przed B4 |
| — | **SLO platformy i SLA dla partnerów:** w etapie 16; zaczyna od decyzji człowieka, co obiecujemy partnerom i ile to kosztuje (DZ17) | pdi + ShipScope + ci_for_sdlc | etap 15 | patrz [etap 16](polecenia-startowe-sdlc-lokalnie.md#etap-16--pdi--shipscope-ci_for_sdlc-utrzymanie-i-niezawodność-platformy) |

Poza zakresem Z10 (już w planie): wycofanie przy wybiciu metryki ochronnej (etap 7), incydenty (G8, etap 9), miary
DORA i przepływu (etap 12, Z8e), model zagrożeń w architekturze (B3 w tf).

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
| DZ15 | Czy brak SLO blokuje wydanie (Z10a) | **przyjęte 2026-11-03**: dla produktu z użytkownikami tak, na B5 (jak pas governance, DZ8); wcześniej ostrzeżenie w B3; repo próbne i zmiany bez wpływu na użytkowników zwolnione z jawnym powodem |
| DZ16 | Dokąd idzie telemetria agentów (Z10c) | **przyjęte 2026-11-03**: lokalnie kolektor OpenTelemetry w Dockerze z `sdlc up`, zapis do pliku czytanego przez konsolę, bez zewnętrznej usługi; backend (Grafana, Honeycomb, …) dopiero z usługą pdi po DA4 |
| DZ17 | Kto i kiedy ustala SLA | **przyjęte 2026-11-03**: tylko człowiek, jako typ chroniony (DA2), dopiero w etapie 16 dla platformy; produkty mają SLO, nie SLA, dopóki nie ma klienta z umową |
| DZ18 | Czy workflow ma się stać IDE (podgląd powstających plików, panel observability z boku) | **przyjęte 2026-11-03**: nie budujemy IDE; konsola dostaje panel „Pliki” w śladzie zmiany (artefakty i diff bieżącego cięcia na żywo, tylko do odczytu) i boczny panel observability (`run.progress`, potem Z10c); ręczna praca w istniejącym IDE z rozszerzeniem Claude Code i serwerem MCP pdi |
| DZ19 | Czy bramka A6 idzie przed A3–A5 | **przyjęte 2026-11-03**: tak; najpierw ponowny przebieg na `sdlc-proba` z tym, co już jest (Z1, Z8a, Z8c-1, Z8c-2), potem A3–A5 i A7 równolegle, a etap 2 (A8) po nich |
| DZ13 | Ile zadań w evalach przebiegu (N5) i jaki budżet | **przyjęte**: start: 20 zadań z repo próbnego i sprintdecka, budżet na jedno uruchomienie ustalony w tf; rozbudowa do ok. 200 po pierwszych wynikach |

## 10. Stan

Stan 2026-11-03 (pdi `53ec1bb`). Kolejność i bramki: §0; polecenia startowe i ich stan: [zespół](polecenia-startowe-zespol.md).

| Krok | Stan |
|---|---|
| Z1 | **zrobione 2026-11-02** (pdi #110, tf #135, #136, kontrakt 0.11.0); **potwierdzone w A6 2026-11-03–05** w artefaktach CHG-3 (pytania odpowiedziane przy B2 nie wróciły w plan.md ani design.md), [wynik](przebieg-lokalny.md#wynik-przebiegu-2026-11-03%E2%80%9305-a6) |
| Z2 | do zrobienia: Z2a (B1) może iść od razu (nie zależy od A6), Z2b (B2) po tagu kontraktu z Z2a; polecenia startowe odświeżone po Z1 i Z8a (pdi #117, #118) |
| Z3 | Z3-lokalnie (A7) do zrobienia, po A6; polecenie startowe odświeżone (pdi #116) i uzupełnione o panel „Pliki” i boczny panel observability (DZ18, pdi #122); usługa pdi (B5) po DA4 |
| Z4 | do zrobienia (C1, po Z2) |
| Z5 | do zrobienia (C2); repo do próby — sprintdeck albo ShipScope (DZ4), wybór przy Z5 |
| Z6 | do zrobienia (C3, po Z5); kolejność źródeł według DZ2 |
| Z7 | Z7b-1 (A4: Z7b-1a, potem Z7b-1b) do zrobienia, polecenia startowe w brzmieniu z 2026-11-02; Z7a razem z A7 (trzy pasy); Z7b-2 i Z7c w B3; Z7d przy pierwszym produkcie, który jest aplikacją AI |
| Z8 | **Z8a zrobione** (pdi #111, tf 5.56.0, [plan](plan-z8a-izolacja-faz.md)), **A6 2026-11-03–05 potwierdza §0a-1–3, 6 na żywo i §0a-4–5 testem CHG-2** ([wynik](przebieg-lokalny.md#wynik-przebiegu-2026-11-03%E2%80%9305-a6)); **Z8c-1 zrobione** (ci_for_sdlc #109); **Z8c-2 zrobione** (tf #138, razem z N3 i N10), kawałek talosa na `sdlc-proba` 2026-11-03 (sdlc-proba #10, [wynik](przebieg-lokalny.md#wynik-przebiegu-2026-11-03-z8c-2-talos-na-sdlc-proba)); **pętla Z8c-2 w fazie `delivery` pdi niepotwierdzona w A6: obraz `pdi-phase:2.1.310-73385c1e0195` nie ma `semgrep` (PRB-29), delivery CHG-3 dwukrotnie `failed`, diagnoza zablokowana przez PRB-28 (brak `detail` w `result.json`)**; Z8b, Z8d i Z8g w B3 (Z8g przed etapem 3); Z8e z etapem 12; Z8f po każdym przebiegu |
| Z9 | N3 i N10 zrobione z Z8c-2; N1 i N5 (A3) do zrobienia, po przebiegu A6 (DZ19); N2 (A5) po N1, razem z nim N12, N13 i N15 (polecenia gotowe 2026-11-03; po kolei, bo zmieniają te same pliki); N4 z Z7b-1; N14 i N18 z Z5; N16 z Z8f; N17 z N5 (A3); N19 z Z2 (B1, B2); N20 z Z7b-1 (A4); pozostałe z krokami, do których są przypięte (§8.3) |
| Z10 | do zrobienia (§8.5); decyzje DZ15–DZ17 przyjęte 2026-11-03; boczny panel z Z10c ma miejsce w konsoli od A7 (DZ18) |

## 11. Do rozważenia w przyszłości

Pomysły odłożone świadomie: nie wchodzą do kroków, dopóki nie pojawi się powód z przebiegu albo pilotażu.

- **Wyszukiwanie hybrydowe z embeddingami i rerankerem.** To kosztowna infrastruktura („with great power comes great
  bill”, wystąpienie T. Ducina), a dokument o harnessach (§8.3, uwaga pod N12–N16) pokazał, że w kodzie wystarcza
  wyszukiwanie deterministyczne. Do Z6 najpierw wyszukiwanie pełnotekstowe.
- **Tani model jako filtr tematu na wejściu.** Ma sens dopiero przy publicznym przyjmowaniu zgłoszeń. Triaż i tak jest
  u człowieka (typ chroniony DA2).
