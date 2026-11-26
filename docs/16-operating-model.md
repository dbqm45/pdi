# Operating model — kto zatwierdza, w jakim terminie i co, gdy nie zatwierdzi

Data: 2026-11-22 · Status: **przyjęty 2026-11-22 (decyzja właściciela, OM1)**, eskalacja dopisana 2026-11-26 (OM2), wariant z jednym zatwierdzającym · Realizuje
P1 z [`plan-program-ai-wg-aplikacji.md`](plan-program-ai-wg-aplikacji.md) i krok 8 / N1 z
[`plan-budowy-suity.md`](plan-budowy-suity.md) · Po przyjęciu: wpis w [`decyzje.md`](decyzje.md).

Wartości z §2–§8 przyjęte 2026-11-22 bez zmian względem szkicu (§11); zmienia je przegląd modelu.

## 1. Zakres

Dokument mówi, kto podejmuje decyzje na bramkach przebiegu zmiany w DI Decision, w jakim terminie, co się dzieje
po terminie i kto jest o czym informowany. Dotyczy zespołu, w którym **wszystkie bramki zatwierdza jedna osoba**.
Nie dotyczy decyzji operacyjnych AI (bramka `operational-ai`, P2/P3 planu programu) ani zobowiązań wobec klientów
(SLA ustala tylko człowiek i dopiero dla platformy z klientem, DZ17).

## 2. Role

| Rola | Kto | Co robi |
|---|---|---|
| **Zatwierdzający** | właściciel projektu (dbqm45) | decyduje na każdej bramce i przy każdym typie chronionym; jedyna osoba, która może obniżyć poziom autonomii |
| **Zastępca** | brak (2026-11-22): przy nieobecności bramki czekają, zmiany przechodzą w stan „wstrzymana” (§5) | decyduje zamiast zatwierdzającego tylko w czasie zapisanej nieobecności (§5) |
| **Zgłaszający** | każdy, kto opisał problem | odpowiada na pytania doprecyzowujące; dostaje wynik triażu i informację o wydaniu |
| **Pytany** | osoba wskazana przez zatwierdzającego przy konkretnej sprawie | doradza w terminie; nie decyduje |
| **Agenci** (persony fabryki) | DI Agent Factory | przygotowują artefakt i rekomendację, proszą o bramkę; nie zatwierdzają niczego |

Zasady stałe:

- Zatwierdzający się nie zmienia przez to, że kogoś zapytał (ustalenie „Ask team”, `TODO.md`).
- Każdy typ decyzji startuje na poziomie autonomii 3 (decyzja człowieka); obniżenie poziomu jest zawsze decyzją
  zatwierdzającego (DA1, DA2). Typy chronione nigdy nie schodzą poniżej 3: `triage`, `scope.r1`, `release.go`,
  `outcome.assessment`, `review.sensitive`, `migration`.

## 3. Bramki

Bramki z `src/pdi/flow.py`. Kolumna „odwracalność” decyduje o terminie (§4) i o tym, co się dzieje po terminie (§5).

| Bramka | Co zatwierdza | Na podstawie czego | Odwracalność | Termin |
|---|---|---|---|---|
| triaż zgłoszenia | przyjąć, odrzucić albo odłożyć zgłoszenie | zgłoszenie, duplikaty, rekomendacja | łatwa (typ chroniony) | 2 dni robocze |
| B1 | kierunek zmiany | `intent.md` | łatwa | 2 dni robocze |
| B2 | wymagania i zakres | `requirements.md`, ustalenia DI Definition | łatwa | 2 dni robocze |
| B3 | plan rozwiązania i cele zmiany (`targets`) | `plan.md`; dla produktów AI progi ewaluacji (DZ7) | **trudna** (architektura) | 5 dni roboczych |
| design-review | projekt interfejsu | `design.md` z ramkami | łatwa | 2 dni robocze |
| approve-for-implementation | start budowy; od tej chwili zmiana ma punkt odniesienia dla driftu | gotowość z DI Definition, blokady przyjęte jako ryzyko | łatwa, ale uruchamia koszt agentów | 2 dni robocze |
| B4 | gotowość do wydania | wynik przeglądu, testy, stan celów | łatwa | 2 dni robocze |
| B5 | autoryzacja wydania na PROD | pas governance (DZ8), SLO (DZ15), plan wydania | **trudna** (typ chroniony `release.go`) | 1 dzień roboczy |
| ocena skutku | czy zmiana dała efekt (`met` / `not_met`) | metryki po wydaniu | łatwa (typ chroniony) | 5 dni roboczych |
| zmiana poziomu autonomii | obniżenie albo podniesienie poziomu dla typu decyzji | licznik akceptacji (próg 95% z 30 decyzji) | łatwa | 5 dni roboczych |
| zmiana etapu flagi na PROD | włączenie funkcji użytkownikom | stan wdrożenia i flag | łatwa (jest wyłącznik) | 1 dzień roboczy |

Stan na 2026-11-22: prośby o B4 i B5 nie przychodzą z fabryki (zgłasza tylko B1–B3 i `design-review`), więc te
dwie bramki są dziś decyzją wpisywaną ręcznie w skrzynce.

## 4. Terminy

Terminy są wewnętrzne (to nie SLA wobec klienta). Liczone w dniach roboczych od chwili, gdy prośba trafiła do
skrzynki.

| Rodzaj sprawy | Termin | Przypomnienie |
|---|---|---|
| bramka łatwa do cofnięcia | 2 dni robocze | po 1 dniu i w dniu terminu |
| bramka trudna do cofnięcia (B3) | 5 dni roboczych | po 3 dniach i w dniu terminu |
| wydanie na PROD (B5), etap flagi na PROD | 1 dzień roboczy | w połowie terminu |
| pytanie do osób pytanych („Ask team”) | ustala zatwierdzający; domyślnie 2 dni robocze | w dniu terminu |
| pytanie agenta w trakcie fazy | jak bramka, przy której padło | razem z bramką |

Godziny ciszy: **18:00–8:00 i weekendy** (Europe/Warsaw); powiadomienia z tego czasu czekają do 8:00 najbliższego dnia roboczego. Terminy liczone w dniach roboczych pomijają weekendy.

## 5. Co się dzieje po terminie

Przy jednym zatwierdzającym nie ma do kogo eskalować, więc model nie udaje eskalacji. Zamiast niej są trzy reguły.
Wyjątek od 2026-11-26 (**OM2**, DI Team T7): decydent może sam przekazać decyzję o jednej sprawie innej osobie z
rolą `editor` albo `admin` w DI Decision („Escalate”; przy typach chronionych tylko `admin`). Od tej chwili decyduje
tylko adresat, dopóki nie odda sprawy z notatką. Termin się nie zmienia: przypomnienia, „wstrzymana” i lista do
przeglądu idą do adresata. Decyzja zapisuje, kto eskalował, do kogo i dlaczego (`escalation`, kontrakt 0.27.0).

**1. Bramka nigdy nie zatwierdza się sama.** Po terminie bramka zostaje otwarta. Dzieje się tyle:

| Chwila | Co robi system |
|---|---|
| termin | powiadomienie „po terminie” do zatwierdzającego; karta zmiany pokazuje, od kiedy czeka i co stoi |
| 2 × termin | zmiana przechodzi w stan „wstrzymana”: agent kończy bieżące cięcie i nie zaczyna następnego, budżet fazy jest zwalniany |
| 4 × termin | sprawa trafia na listę „do przeglądu” w skrócie tygodniowym; zatwierdzający decyduje: zatwierdzić, odrzucić albo odłożyć zmianę z progiem powrotu |

**2. Pytanie w trakcie fazy nie blokuje całości.**

- Decyzja łatwa do cofnięcia: agent idzie dalej z opcją rekomendowaną, oznaczoną jako **tymczasowa** (najlepiej za
  flagą). Zatwierdzający potwierdza ją albo zmienia przy najbliższej bramce; zmiana oznacza poprawkę, nie nowe
  zgłoszenie.
- Decyzja trudna do cofnięcia (model danych, publiczne API, granica bezpieczeństwa, dostawca, koszt): agent
  zatrzymuje tylko tę część pracy, która od niej zależy, i robi resztę.
- Pytanie do osób pytanych zamyka się w terminie z tym, co zebrano; milczenie znaczy brak sprzeciwu. Decyzję i tak
  podejmuje zatwierdzający.

**3. Nieobecność jest zapisywana, nie domyślana.**

- Planowana nieobecność: zatwierdzający wyznacza zastępcę na określony czas i zakres bramek; wyznaczenie jest
  decyzją w rejestrze (kto, od kiedy, do kiedy, które bramki).
- Zastępca nie zatwierdza typów chronionych, chyba że wyznaczenie mówi o tym wprost.
- Bez zastępcy bramki czekają, a zmiany przechodzą w stan „wstrzymana” jak w tabeli wyżej.

## 6. Kto co dostaje

| Rola w sprawie | Kto (w tym modelu) | Jak |
|---|---|---|
| decydujesz | zatwierdzający albo zastępca w czasie nieobecności | od razu, z terminem i linkiem do decyzji |
| jesteś pytany | osoby wskazane przy sprawie | od razu, z terminem zamknięcia |
| informowany | zgłaszający (wynik triażu, wydanie), reszta zespołu | skrót zbiorczy albo tablica; bez powiadomienia |

Każda wiadomość „decydujesz” ma wymagać działania. Do czasu aplikacji kanałów (DI Channels) powiadomienia idą
istniejącym webhookiem i przez skrzynkę w konsoli.

## 7. RACI

R — wykonuje, A — odpowiada i zatwierdza, C — konsultowany, I — informowany.

| Czynność | Zatwierdzający | Zastępca | Pytani | Zgłaszający | Agenci |
|---|---|---|---|---|---|
| opis problemu | I | — | — | R | C (pytania doprecyzowujące) |
| triaż | A | — | C | I | R (rekomendacja) |
| kierunek, wymagania, plan, design (B1–B3, design-review) | A | A w czasie nieobecności | C | I przy B1 | R (artefakt) |
| start budowy | A | A w czasie nieobecności | — | — | R |
| budowa i przegląd | I | — | C przy pytaniu | — | R |
| gotowość i wydanie (B4, B5) | A | tylko gdy wyznaczenie obejmuje B5 | C | I | R (przegląd gotowości) |
| ocena skutku | A | — | C | I | R (dane) |
| poziom autonomii | A | — | — | — | R (propozycja z licznika) |

Podział CoE ↔ zespoły z P1 planu programu nie ma tu zastosowania: przy jednym zatwierdzającym CoE i zespół to ta
sama osoba. Wraca przy pierwszym zespole spoza autora (§9).

## 8. Miary

| Miara | Cel | Skąd |
|---|---|---|
| odsetek bramek zatwierdzonych w terminie | ≥ 80% | wymaga metryk kolejki bramek (G7 w `TODO.md`, niezrobione) |
| mediana czasu oczekiwania bramki | ≤ 1 dzień roboczy | jw. |
| liczba zmian w stanie „wstrzymana” dłużej niż 4 × termin | 0 | jw. |
| odsetek wiadomości „decydujesz” zamkniętych bez decyzji | ≤ 5% | DI Channels (N5) |
| odsetek decyzji tymczasowych zmienionych przy bramce | obserwować, bez celu | rejestr |

Przegląd modelu: **pierwszy 2027-01-03** (6 tygodni od przyjęcia), potem przy warunkach z §9.

## 9. Kiedy ten model przestaje wystarczać

Jeden zatwierdzający to świadome uproszczenie i pojedynczy punkt zatrzymania. Model trzeba rozdzielić, gdy zajdzie
jedno z poniższych:

- do zespołu dochodzi druga osoba z prawem decyzji albo pierwszy zespół spoza autora;
- odsetek bramek w terminie spada poniżej celu przez dwa kolejne przeglądy;
- pojawia się klient z umową (wtedy także SLA, DZ17).

Naturalny podział: właściciel produktu (triaż, B1, B2, ocena skutku), architekt (B3), projektant (design-review),
właściciel wydania (B4, B5, etapy flag), a obniżanie poziomu autonomii zostaje u jednej osoby.

## 10. Co trzeba zbudować, żeby model działał

Dokument opisuje zachowanie docelowe; dziś skrzynka nie zna terminów ani stanu „wstrzymana”.

| Element | Stan | Krok planu budowy suity |
|---|---|---|
| zatwierdzający i zastępca per typ decyzji w konfiguracji | brak | N1 |
| termin, odwracalność, opcja tymczasowa w kontrakcie | brak (`reversibility` na liście w `TODO.md`) | N2 |
| przypomnienia i stan „wstrzymana” po terminie | brak | N3 |
| agent idzie dalej z opcją tymczasową | brak | N4 |
| trzy poziomy powiadomień | brak | N5 |
| metryki kolejki bramek | brak (G7) | do dopisania |

## 11. Przyjęte 2026-11-22

1. Zatwierdzający: właściciel projektu (§2).
2. Zastępca: brak (§2, §5).
3. Terminy z §3 i §4: jak w szkicu.
4. Mnożniki z §5 (2 × i 4 × termin): jak w szkicu.
5. Godziny ciszy: 18:00–8:00 i weekendy, Europe/Warsaw (§4).
6. Cele miar z §8; pierwszy przegląd 2027-01-03.
