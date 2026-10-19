# Profil design partnera

Dokument roboczy do Etapu 0 ([plan](../docs/08-plan-projektu.md#etap-0-design-partnerzy-i-przypadki-k1-k3)). Służy do wyboru kandydatów i prowadzenia rozmów kwalifikacyjnych. Nie wysyłać partnerom — dla nich jest [propozycja](propozycja-dla-pm.md).

## 1. Kim jest design partner

PM, który **sam odpowiada za decyzje o inicjatywach produktowych** i chce sprawdzić, czy zewnętrzna, krytyczna analiza uzasadnienia jego decyzji pomaga mu decydować lepiej.

Design partner nie jest klientem ani testerem interfejsu. Jest współautorem odpowiedzi na pytanie: *czy PDI wykrywa rzeczy, których PM sam by nie zobaczył — i czy to coś zmienia w jego działaniu?*

## 2. Kryteria obowiązkowe

Kandydat musi spełnić wszystkie. Bez nich nie ma na czym walidować.

| # | Kryterium | Dlaczego | Jak sprawdzić |
|---|---|---|---|
| O1 | Odpowiada za decyzje o kierunku inicjatyw (co i dlaczego budować), nie tylko za realizację backlogu | PDI ocenia uzasadnienie decyzji — bez decyzji nie ma czego oceniać | P1, P2 |
| O2 | Ma **bieżącą** inicjatywę przed istotną decyzją (discovery, wybór rozwiązania, przed estymacją) w ciągu najbliższych 4–8 tygodni | Test prospektywny nie wymaga znanych rezultatów | P3 |
| O3 | Inicjatywa ma **materiały pisemne** z co najmniej 3 różnych źródeł (np. opis problemu, badania/feedback, dane, wymagania, notatki z decyzji) | Bez materiałów nie da się zrekonstruować uzasadnienia | P4 |
| O4 | Może udostępnić materiały (po anonimizacji) zgodnie z zasadami swojej organizacji | Bariera poufności to ryzyko K3 | P5 |
| O5 | Gotowość na ok. 3–4 godziny w ciągu 6–8 tygodni | Mniej nie wystarczy do wywiadu, materiałów i oceny | P6 |
| O6 | Otwartość na zakwestionowanie własnej decyzji | System, którego wyniki są z góry odrzucane, niczego nie walidujemy | P7 — obserwacja reakcji |

## 3. Kryteria pożądane

| # | Kryterium | Wartość dla projektu |
|---|---|---|
| D1 | Ma też **zakończoną** inicjatywę ze znanym rezultatem i materiałami z chwili decyzji | Umożliwia ocenę retrospektywną ([06 §6.3](../docs/06-mvp-i-pilotaz.md#63-protokół-oceny-retrospektywnej)) |
| D2 | Organizacja z kilkoma zespołami produktowymi | Rozproszenie wiedzy — główny problem, który PDI ma rozwiązywać — jest tam wyraźniejsze |
| D3 | Pamięta konkretną sytuację, w której problem wykryto za późno | Dobry materiał do wywiadu i sygnał, że problem jest realny |
| D4 | Ma dostęp do danych ilościowych (analityka, support) | Pozwala testować wzorce oparte na dowodach ilościowych |
| D5 | Może polecić innego PM-a | Rozwiązuje problem pozyskiwania kolejnych partnerów |

## 4. Kogo nie zapraszamy (na tym etapie)

- PM-ów, którzy realizują roadmapę ustaloną w całości przez kogoś innego (brak O1).
- Inicjatyw, których jedynym źródłem jest prezentacja lub jedno zdanie w backlogu (brak O3).
- Osób szukających gotowego narzędzia do codziennej pracy — rozczarują się prototypem koncepcyjnym, a ich ocena będzie mierzyć dojrzałość produktu, nie wartość koncepcji.
- Bliskich znajomych, którzy z grzeczności ocenią wszystko pozytywnie — mogą pomóc w poleceniach, ale nie powinni stanowić większości oceniających.
- Organizacji, w których udostępnienie materiałów wymaga długiej ścieżki prawnej (> 2–3 tygodnie) — chyba że kandydat jest wyjątkowo dobry.

## 5. Skład grupy partnerów

Cel: **3–5 PM-ów z co najmniej 2 organizacji.** Dobór celowo zróżnicowany, żeby wynik nie zależał od jednej kultury pracy:

- co najmniej 2 różne organizacje (najlepiej 3),
- różne typy produktów (np. B2C i B2B / platforma wewnętrzna),
- różne etapy następnej decyzji (discovery vs. przed estymacją),
- co najmniej 1 partner z zakończoną inicjatywą (D1).

## 6. Pytania kwalifikacyjne (rozmowa 20–30 min)

| # | Pytanie | Czego słuchamy |
|---|---|---|
| P1 | Opowiedz o ostatniej decyzji produktowej, którą podjąłeś lub przeforsowałeś. Kto ostatecznie zdecydował? | Czy kandydat jest właścicielem decyzji (O1) |
| P2 | Jak w Twoim zespole wygląda droga od pomysłu do decyzji, że coś budujecie? | Proces, momenty decyzji — materiał do Etapu 1 |
| P3 | Jaka ważna decyzja czeka Cię w najbliższych tygodniach? | O2 — konkretna inicjatywa i termin |
| P4 | Jakie materiały istnieją na jej temat i gdzie leżą? | O3 — liczba i rodzaj źródeł |
| P5 | Czy możesz udostępnić te materiały po anonimizacji? Kogo musiałbyś zapytać? | O4 — realna ścieżka zgody |
| P6 | Czy znajdziesz 3–4 godziny w ciągu najbliższych 6–8 tygodni? | O5 |
| P7 | Gdyby analiza pokazała, że kluczowe założenie Twojej decyzji nie ma potwierdzenia w danych — co byś z tym zrobił? | O6 — otwartość; czy odpowiedź jest konkretna, czy obronna |
| P8 | Czy przypominasz sobie sytuację, w której ważną informację odkryto za późno? Co się stało? | D3 — sygnał realności problemu |
| P9 | Czy znasz innego PM-a, dla którego to mogłoby być ciekawe? | D5 |

Uwaga: P8 to również **dane do Etapu 1** — notuj odpowiedzi niezależnie od tego, czy kandydat zostanie partnerem.

## 7. Ocena kandydata

- Którekolwiek z O1–O5 niespełnione → **nie teraz** (zapisz, może wrócić przy następnej inicjatywie).
- O6 budzi wątpliwość → partner możliwy, ale nie jako jedyny oceniający w danej organizacji.
- Wszystkie O1–O6 + ≥ 2 kryteria pożądane → **priorytet**.

## 8. Kanały pozyskiwania

Źródło partnerów nie jest jeszcze ustalone. Proponowana kolejność testowania — od najcieplejszego kanału:

| Kanał | Zalety | Wady | Pierwszy krok |
|---|---|---|---|
| Własna sieć kontaktów (byli współpracownicy, LinkedIn — 1. i 2. stopień) | Najwyższe zaufanie, łatwiej o materiały | Ryzyko ocen z grzeczności; mała skala | Lista 15–20 osób, wiadomość z [szablonu](wiadomosc-kontaktowa.md) |
| Polecenia od pierwszych partnerów (D5) | Zaufanie przeniesione, dobre dopasowanie | Działa dopiero po pierwszych partnerach | P9 na każdej rozmowie |
| Społeczności i meetupy PM (lokalne spotkania product managerów, grupy na LinkedIn / Slacku) | Zasięg, ludzie zainteresowani tematem | Niższe zaufanie, trudniej o materiały | Krótki post z opisem problemu (nie produktu) i zaproszeniem do rozmowy |
| Treści eksperckie (artykuł / post o tym, jak decyzje produktowe opierają się na niesprawdzonych założeniach) | Przyciąga osoby, które mają ten problem | Wolne, wymaga regularności | Jeden tekst oparty na przykładzie `status-zamowienia` |

**Wskaźnik do obserwowania:** odsetek kontaktów, które kończą się rozmową kwalifikacyjną, i odsetek rozmów, które kończą się udostępnieniem materiałów. To pierwsze rynkowe dane o tym, czy problem jest dla PM-ów wystarczająco ważny — **także sygnał do decyzji „produkt komercyjny czy narzędzie wewnętrzne”**.

## 9. Rejestr kandydatów

Prowadzić poza repozytorium (dane osobowe). Minimalne pola: inicjały / kod, organizacja (kategoria, nie nazwa), kanał, data kontaktu, status (`kontakt` → `rozmowa` → `partner` / `nie teraz` / `odmowa`), spełnione kryteria, powód odmowy. W repozytorium — wyłącznie zagregowane liczby.
