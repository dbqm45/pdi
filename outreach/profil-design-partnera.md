# Profil design partnera

> **Wstrzymane 2026-10-23** — pdi rozwijane jest jako warstwa decyzji we własnym flow SDLC, z pilotem na własnych problemach ([dokument 12](../docs/12-zmiana-kierunku-sdlc.md)). Materiał zostaje na wypadek, gdyby po F5 wróciło pytanie o użycie pdi poza tym flow.

Dokument roboczy do Etapu 0 ([plan](../docs/08-plan-projektu.md#etap-0-design-partnerzy-i-przypadki-k1-k3)). Służy do wyboru kandydatów i prowadzenia rozmów kwalifikacyjnych. Nie wysyłać partnerom — dla nich jest [propozycja](propozycja-dla-pm.md).

## 1. Kim jest design partner

PM, który **sam odpowiada za decyzje o inicjatywach produktowych**, ma decyzje w trakcie wdrażania, a jego praca zależy od innych działów firmy. Chce sprawdzić, czy pilnowanie podstaw jego decyzji — liczb, założeń i warunków — wyłapuje coś, czego sam by nie zauważył na czas.

Design partner nie jest klientem ani testerem interfejsu. Jest współautorem odpowiedzi na dwa pytania:

1. *Jak często w realnej organizacji decyzja traci podstawy przez informację z innego działu, która jej nie wspomina?* (pytanie o problem)
2. *Czy pilnowanie zapamiętanego uzasadnienia wyłapuje takie sytuacje na czas, bez zalewania PM-a szumem?* (pytanie o rozwiązanie)

Dlaczego tak wąsko: testy ([v1](../eval/status-zamowienia/wyniki/raport.md), [v2](../eval/v2-pamiec-decyzji/wyniki/raport.md)) pokazały, że jednorazową krytykę decyzji daje dziś każdy asystent AI, a przewagę daje dopiero pamięć uzasadnienia — przy informacjach zmieniających liczby lub warunki decyzji.

## 2. Kryteria obowiązkowe

Kandydat musi spełnić wszystkie. Bez nich nie ma na czym walidować.

| # | Kryterium | Dlaczego | Jak sprawdzić |
|---|---|---|---|
| O1 | Odpowiada za decyzje o kierunku inicjatyw (co i dlaczego budować), nie tylko za realizację backlogu | Pilnujemy uzasadnienia decyzji — bez właściciela decyzji nie ma komu ostrzegać | P1, P2 |
| O2 | Ma **1–3 decyzje już podjęte**, w trakcie wdrażania przez co najmniej 4–6 kolejnych tygodni | Obserwujemy, co dzieje się z decyzją po jej podjęciu | P3 |
| O3 | Uzasadnienie decyzji jest choć częściowo **zapisane** (notatka z decyzji, business case, PRD, OKR, maile) i zawiera konkrety: liczby, warunki, zależności | Bez spisanych podstaw nie ma czego pilnować; w MVP nie rekonstruujemy uzasadnień z rozmów | P4 |
| O4 | Praca PM-a **zależy od innych działów** (zakupy, logistyka, integracje, finanse, marketing, prawo) i PM ma wgląd w część ich dokumentów | Sygnały, które testujemy, przychodzą właśnie stamtąd | P5 |
| O5 | Może przez 4–6 tygodni co tydzień przekazywać (po anonimizacji) wybrane materiały z firmy — ok. 10–15 min tygodniowo | Bez strumienia nowych informacji nie ma czego sprawdzać | P6 |
| O6 | Gotowość, by system powiedział, że decyzja straciła podstawy | Ostrzeżenia z góry odrzucane niczego nie walidują | P7 — obserwacja reakcji |

## 3. Kryteria pożądane

| # | Kryterium | Wartość dla projektu |
|---|---|---|
| D1 | Pamięta **konkretny przypadek**, w którym decyzja straciła podstawy przez informację z innego działu, a dowiedział się o tym za późno | Najcenniejsze dane o problemie i materiał do testu v3 na prawdziwym przypadku |
| D2 | Organizacja z kilkoma zespołami i działami, które zmieniają warunki pracy produktu (umowy, dostawcy, rynki) | Tam takie sytuacje są najbardziej prawdopodobne |
| D3 | Decyzje z policzalnym uzasadnieniem (koszt, marża, udział, SLA, termin) | Na takich sygnałach pamięć dawała w testach największą przewagę |
| D4 | Ma dostęp do kanałów, którymi płyną informacje w firmie (Confluence, Jira, Slack, wiki, newsletter) | Realistyczny strumień do przeglądu |
| D5 | Może polecić innego PM-a | Rozwiązuje problem pozyskiwania kolejnych partnerów |

## 4. Kogo nie zapraszamy (na tym etapie)

- PM-ów, którzy realizują roadmapę ustaloną w całości przez kogoś innego (brak O1).
- PM-ów, których decyzje nie zależą od innych działów (np. czysto wewnętrzne zmiany UI) — sygnałów tego typu po prostu nie będzie (brak O4).
- Osób szukających gotowego narzędzia do codziennej pracy — rozczarują się prototypem, a ich ocena będzie mierzyć dojrzałość produktu, nie wartość koncepcji.
- Bliskich znajomych, którzy z grzeczności ocenią wszystko pozytywnie — mogą pomóc w poleceniach, ale nie powinni stanowić większości partnerów.
- Organizacji, w których udostępnienie materiałów wymaga długiej ścieżki prawnej (> 2–3 tygodnie) — chyba że kandydat jest wyjątkowo dobry.

## 5. Skład grupy partnerów

Cel: **3–5 PM-ów z co najmniej 2 organizacji**, łącznie **co najmniej 6 obserwowanych decyzji**. Dobór celowo zróżnicowany:

- co najmniej 2 różne organizacje (najlepiej 3),
- różne typy produktów (np. e-commerce, B2B SaaS, platforma wewnętrzna),
- decyzje różnego rodzaju (ceny i koszty, integracje, zakres rynku, zmiany procesu),
- co najmniej 2 partnerów z przypadkiem D1.

## 6. Pytania kwalifikacyjne (rozmowa 20–30 min)

| # | Pytanie | Czego słuchamy |
|---|---|---|
| P1 | Opowiedz o ostatniej decyzji produktowej, którą podjąłeś lub przeforsowałeś. Kto ostatecznie zdecydował? | Czy kandydat jest właścicielem decyzji (O1) |
| P2 | Jak w Twoim zespole zapadają decyzje i gdzie zapisuje się ich uzasadnienie? | Proces; czy uzasadnienia w ogóle są spisywane (ryzyko Z2) |
| P3 | Jakie decyzje są teraz w trakcie wdrażania i jak długo jeszcze? | O2 — konkretne decyzje i horyzont |
| P4 | Na czym opiera się jedna z nich — jakie liczby, założenia, warunki? Gdzie to jest zapisane? | O3, D3 — czy jest czego pilnować |
| P5 | Od których działów zależy, czy ta decyzja się sprawdzi? Skąd się dowiadujesz, co u nich się zmienia? | O4, D4 — skąd mogą przyjść sygnały i czy PM je widzi |
| P6 | Czy możesz raz w tygodniu przekazywać wybrane materiały (po anonimizacji)? Kogo musiałbyś zapytać o zgodę? | O5 — realna ścieżka |
| P7 | Gdyby w trzecim tygodniu przyszło ostrzeżenie, że decyzja przestała się opłacać — co byś zrobił? Komu byś to pokazał? | O6 — reakcja; czy odpowiedź jest konkretna, czy obronna |
| P8 | **Czy w ostatnich 6–12 miesiącach zdarzyło się, że decyzja straciła podstawy przez coś, co wydarzyło się w innym dziale, a Ty dowiedziałeś się za późno? Co to było, kiedy się zorientowałeś, ile to kosztowało?** | D1 — **najważniejsze pytanie walidacyjne** |
| P9 | Czy znasz innego PM-a, dla którego to mogłoby być ciekawe? | D5 |

**P8 zadaj każdemu rozmówcy**, także temu, kto nie zostanie partnerem, i zapisz odpowiedź w rejestrze (bez danych identyfikujących): czy był przypadek (tak/nie), ile w ciągu roku, przybliżony koszt, czas od zmiany do wykrycia. To są **dane o częstości problemu** — od nich zależy, czy zawężona propozycja wartości ma sens.

## 7. Ocena kandydata

- Którekolwiek z O1–O5 niespełnione → **nie teraz** (zapisz, może wrócić przy kolejnej decyzji). Odpowiedź na P8 i tak zapisz.
- O6 budzi wątpliwość → partner możliwy, ale nie jako jedyny oceniający w danej organizacji.
- Wszystkie O1–O6 + ≥ 2 kryteria pożądane → **priorytet**.

## 8. Kanały pozyskiwania

Źródło partnerów nie jest jeszcze ustalone. Proponowana kolejność testowania — od najcieplejszego kanału:

| Kanał | Zalety | Wady | Pierwszy krok |
|---|---|---|---|
| Własna sieć kontaktów (byli współpracownicy, LinkedIn — 1. i 2. stopień) | Najwyższe zaufanie, łatwiej o materiały | Ryzyko ocen z grzeczności; mała skala | Lista 15–20 osób, wiadomość z [szablonu](wiadomosc-kontaktowa.md) |
| Polecenia od pierwszych partnerów (D5) | Zaufanie przeniesione, dobre dopasowanie | Działa dopiero po pierwszych partnerach | P9 na każdej rozmowie |
| Społeczności i meetupy PM (lokalne spotkania product managerów, grupy na LinkedIn / Slacku) | Zasięg, ludzie zainteresowani tematem | Niższe zaufanie, trudniej o materiały | Krótki post z opisem problemu (nie produktu) i zaproszeniem do rozmowy |
| Treści eksperckie (artykuł / post o decyzjach, które tracą podstawy przez zmiany w innych działach) | Przyciąga osoby, które mają ten problem | Wolne, wymaga regularności | Jeden tekst oparty na przykładzie aneksu do umowy z testu v2 |

**Wskaźniki do obserwowania:** odsetek kontaktów, które kończą się rozmową kwalifikacyjną; odsetek rozmów, które kończą się udostępnieniem materiałów; **odsetek rozmówców, którzy na P8 podają konkretny przypadek**. To pierwsze rynkowe dane o tym, czy problem jest dla PM-ów wystarczająco ważny — **także sygnał do decyzji „produkt komercyjny czy narzędzie wewnętrzne”**.

## 9. Rejestr kandydatów

Prowadzić poza repozytorium (dane osobowe). Minimalne pola: inicjały / kod, organizacja (kategoria, nie nazwa), kanał, data kontaktu, status (`kontakt` → `rozmowa` → `partner` / `nie teraz` / `odmowa`), spełnione kryteria, powód odmowy, **odpowiedź na P8** (był przypadek: tak/nie; liczba w roku; przybliżony koszt; czas od zmiany do wykrycia). W repozytorium — wyłącznie zagregowane liczby.
