# Plan: zespół jednoosobowy — greenfield od wywiadu, brownfield od poznania projektu, wszystko w przeglądarce

Data: 2026-11-02 · Status: **plan, do decyzji właściciela** (§9) · Stan wyjściowy: pdi `d66b4bf`, tf 5.55.0,
ShipScope 0.2.67, ci_for_sdlc 0.1.35+ · Powiązane: [plan `sdlc up`](plan-sdlc-lokalnie.md),
[przebieg lokalny](przebieg-lokalny.md#wynik-przebiegu-2026-10-31), [etapy 2–18](polecenia-startowe-sdlc-lokalnie.md),
[automatyzacja i konsola](plan-automatyzacja-i-konsola.md), [jedna platforma](15-jedna-platforma.md)

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
PRB-2, 4–10, 16–22. Otwarte zostają PRB-3 (odpowiedzi z bramek nie docierają do kolejnych faz), PRB-11–14 (tf) i
PRB-15 (repo próbne bez CI).

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
| Pamięć zespołu | rejestr decyzji pdi | jest; PRB-3 pokazuje, że kolejne fazy jej nie czytają |

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
| Dalej: intencja → … → skutek | jest | PRB-3: odpowiedzi z wywiadu i bramek muszą trafiać do kolejnych faz | Z1 |

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
| Z1 | **PRB-3:** decyzje z bramek i wywiadu docierają do kolejnych faz (`phase_run.py prompt` dostaje decyzje zmiany z rejestru i `decisions.md`; pytanie zamknięte w B2 nie wraca w B3) | tf + pdi | — | w powtórzonym przebiegu lokalnym te same pytania nie wracają |
| Z2 | **Wywiad (`discovery`):** faza rozmowy z `core-plan-interview` i `proc-product-discovery`; wynik `docs/project/changes/<CHG>/brief.md` (albo `docs/project/discovery/brief.md` dla produktu) i decyzje w rejestrze; bramka B0 w kontrakcie (wersja minor) | tf + pdi (kontrakt) | Z1, DZ1, DZ3 | wywiad w czacie Claude z MCP kończy się briefem i B0; intencja powstaje z briefu |
| Z3 | **Przeglądarka:** `run.progress` ze `stream-json`; usługa pdi z SSE; konsola v1 (tablica, skrzynka, na żywo) i rozmowa (wywiad, pytania z bramek); sygnał „czeka na Ciebie” | tf + pdi | DA4, DZ1, DZ2 | wywiad i cały przebieg widać i prowadzi się w przeglądarce, bez terminala i bez dopytywania |
| Z4 | **Greenfield do końca:** wybór stosu (`arch-tech-selection`, decyzja `stack`), bootstrap repo ze stosu z tf, lista kroków infrastruktury dla człowieka | tf + pdi (`sdlc new`) | Z2, DZ3 | nowy mały produkt od wywiadu do oceny skutku, bez szablonu `sdlc-sandbox` |
| Z5 | **Onboarding brownfield:** faza `onboarding` (rekonstrukcja z kodu + wyniki ci_for_sdlc z Jiry, Confluence, Figmy) → `standards.md` z dowodami, mapa wiedzy, pytania; B0; standardy w wejściu faz i reguła w ci_for_sdlc | tf + pdi + ci_for_sdlc | Z1 | na „obcym” repo (DZ4) pierwsza zmiana przechodzi zgodnie z jego standardami, a review nie znajduje naruszeń konwencji |
| Z6 | **Źródła rozmów:** Slack, potem Teams i Miro jako źródła wiedzy do onboardingu (cytat i link) | pdi (+ konektory) | Z5, DZ2 | mapa wiedzy cytuje wątki i tablice; sprzeczności z Confluence są w pytaniach |

Kolejność: Z1 → Z2 (w czacie Claude, bez nowej usługi) → Z3 → Z4 i Z5 równolegle → Z6.

**Miejsce w etapach 2–18:** Z1 to poprawka przed etapem 2 (zalecana w wyniku przebiegu). Z3 łączy etap 4 (usługa
i konsola K-2) z etapem 10 (rozmowa K-3) i przesuwa rozmowę wcześniej. Z2, Z4, Z5 i Z6 to nowe etapy, których w tej
tabeli nie ma. Zmianę kolejności etapów zatwierdza właściciel (DZ5).

## 9. Decyzje do podjęcia

| # | Pytanie | Rekomendacja |
|---|---|---|
| DZ1 | Gdzie najpierw wywiad: w czacie Claude z MCP czy od razu w przeglądarce? | najpierw czat Claude (Z2 bez nowej usługi, sprawdzamy sam wywiad); przeglądarka w Z3 |
| DZ2 | Które źródła brownfield najpierw? | Confluence i Jira (już w ci_for_sdlc), potem Slack (konektor dostępny); Teams i Miro po sprawdzeniu konektorów na koncie |
| DZ3 | Skille 10x czy skille tf? | skille tf (`core-plan-interview`, `proc-product-discovery`, `arch-tech-selection`, `eng-project-reconstruction`) jako podstawa — są w fabryce i w kontrakcie pracy agentów; ze skilli 10x przenieść tylko to, czego brakuje, po porównaniu |
| DZ4 | Na jakim repo sprawdzić brownfield? | sprintdeck albo ShipScope jako „obcy” projekt: mają dokumentację, standardy i historię |
| DZ5 | Czy zmienić kolejność etapów 2–18? | tak: Z1 przed etapem 2; Z2 i Z3 przed etapem 3; rozmowa (K-3) razem z konsolą (K-2) |
| DA4 | Stos usługi pdi (otwarte od etapu 4) | do rozstrzygnięcia przed Z3 |

## 10. Stan

| Krok | Stan |
|---|---|
| Z1 | do zrobienia (PRB-3 otwarte) |
| Z2 | do zrobienia, po DZ1 i DZ3 |
| Z3 | do zrobienia, po DA4 |
| Z4 | do zrobienia |
| Z5 | do zrobienia, po DZ4 |
| Z6 | do zrobienia, po DZ2 |
