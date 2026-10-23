# Co wymaga Twojej uwagi (tydzień 3)

## 1. INT-233 (API przewoźnika Y v3) — wymaga działania, dotyka inicjatywy 2 i 1

**Panel statusu zamówienia (release 2026-12-10)**
- Migracja na v3 ma być gotowa do 2026-12-12, a API v2 wygasa 2026-12-15. Panel wyjdzie więc dwa dni przed migracją, ale większość jego życia przypadnie na świat v3.
- Po migracji dla przesyłek Y będą tylko zdarzenia „nadane" i „doręczone". Nie będzie „w doręczeniu" ani awizacji.
- Odświeżanie w planie Standard co ok. 12 h (polling, bez webhooków). Status w panelu może się spóźniać o pół doby.
- Panel zaprojektowany na bogatszą ścieżkę statusów będzie dla Y pokazywał „dziurę" między nadaniem a doręczeniem. Najbardziej wrażliwy moment, czyli dzień doręczenia i awizo, zostaje bez informacji. To uderza w cel panelu, czyli redukcję kontaktów o status (26% w tygodniu 47).
- Mapowanie zdarzeń v3 na statusy OMS jest „w toku" — to właśnie ono ustala, co panel może pokazać.

**Decyzje po Twojej stronie**
1. Czy Twój zawężony zakres panelu zakłada statusy, których Y po migracji nie dostarczy? Sprawdź to z zespołem Integracje.
2. Jak panel ma komunikować przesyłki Y (np. „nadano / doręczono", bez obietnic „w doręczeniu", z informacją o możliwym opóźnieniu)?
3. Czy warto płacić za plan Premium (odświeżanie co 15 min, ok. +0,30 zł za paczkę)? Zwróć uwagę, że Premium poprawia tylko częstotliwość. Brakujących zdarzeń „w doręczeniu" i awizacji nie przywraca.

**Darmowa dostawa (start 2026-12-01)**
- Obniżenie progu do 99 zł zwiększy odsetek zamówień z darmową dostawą, a więc i koszt przewoźnika po Twojej stronie. Dopłata +0,30 zł za paczkę dla Premium dojdzie do tego kosztu. Uwzględnij to w rachunku opłacalności, jeśli Premium wchodzi w grę. [Udziału Y w wolumenie nie znam — do sprawdzenia.]

## 2. Tygodnik danych (tydz. 47) — wymaga uwagi dla inicjatywy 1

- Średnia wartość koszyka to 158 zł, a w tygodniu spadła o 4,8%. Jest tuż nad obecnym progiem 149 zł i zbliża się do niego. [Zastrzeżenie: to tydzień Black Week, więc trend może być sezonowy.]
- Przy progu 99 zł wiele koszyków przestanie „dobijać" do darmowej dostawy. Zniknie część efektu zwiększania koszyka, a koszt dostawy w zamówieniach 99–149 zł przejdzie na firmę.
- Sprawdź przed startem 1 grudnia założenia modelu: rozkład koszyków w przedziale 99–149 zł, spodziewany spadek AOV i marżę na tych zamówieniach.
- Dla inicjatywy 2: udział kontaktów o status zamówienia (26%, −1 pp) i NPS po dostawie (43, −1) to dobra baza przed/po do oceny panelu.

## 3. Sprint 32 Checkout — tylko jedna pozycja, informacyjnie dla inicjatywy 3

- Zapisywanie karty (tokenizacja) dla zalogowanych użytkowników ułatwi migrację klientów z płatności za pobraniem (od 2027-02-01) na płatność kartą. Zakres obejmuje tylko zalogowanych, więc klienci kupujący jako goście nie skorzystają. Warto uwzględnić to w planie komunikacji i w ocenie ryzyka spadku konwersji po wycofaniu COD.

## Pominięte jako niemające znaczenia dla Twoich inicjatyw
Ankieta pracownicza, etykiety przewoźnika X (brak zmian w procesie i cenniku, dotyczy magazynu), koszty infrastruktury, plan treści poradnikowych, pozostałe punkty sprintu 32 (test przycisku, kody łączone).
