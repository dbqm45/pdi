## Wymaga Twojej uwagi: 3 rzeczy (kolejność wg wagi)

### 1. Aneks nr 4 do umowy z przewoźnikiem X zmienia ekonomię darmowej dostawy (03-aneks-umowy-przewoznik-x.md)

**Co się zmienia.** Od 2026-12-01, czyli w dniu startu progu 99 zł, przewoźnik X wprowadza dopłatę paliwową 9% do stawki bazowej (dotąd 0%). Paczki powyżej 10 kg dostają stawkę bazową 19,90 zł (dotąd 12,00 zł) i stanowią ok. 14% wolumenu X. Zakupy rekomendują akceptację, bo alternatywnego przewoźnika nie ma przed Q2 2027, a renegocjacja jest możliwa przy odnowieniu w czerwcu 2027. Aneks wchodzi w życie tak czy inaczej, więc decyzja o akceptacji jest realnie po stronie Zakupów, ale skutek spada na Twój wynik.

**Dlaczego to ważne.** Notatka z decyzji liczyła średni koszt paczki jako 11,80 zł (X: 12,00 zł przy ok. 65% paczek, Y: 11,40 zł przy ok. 35%) i wynik +22 600 zł miesięcznie. Moje przeliczenie [założenia: dopłata 9% dotyczy także stawki 19,90 zł, struktura wagowa dodatkowych paczek jak całego wolumenu X, 18 000 dodatkowych paczek, bez zmian po stronie Y]:
- średni koszt paczki X: 0,86 × 13,08 zł + 0,14 × 21,69 zł, czyli ok. 14,29 zł (dziś 12,00 zł, czyli ok. +19%);
- średni koszt ważony z Y: ok. 13,28 zł zamiast 11,80 zł;
- koszt 18 000 paczek: ok. 239 000 zł zamiast 212 400 zł, czyli ok. +26 600 zł miesięcznie;
- wynik przy marży z pilotażu (235 000 zł): ok. -4 000 zł miesięcznie, a przy marży z testu krajowego (+5,8%, ok. 223 400 zł): ok. -15 500 zł miesięcznie.

**Czułość na założenie o wadze.** Dodatkowe paczki pochodzą z koszyków 99–149 zł, więc mogą być lżejsze niż średnia. Jeśli żadna nie przekracza 10 kg, średni koszt to ok. 12,49 zł, a koszt ok. 224 900 zł. Wynik wynosi wtedy ok. +10 100 zł (marża 235 000 zł) albo ok. -1 400 zł (marża 223 400 zł). Do tego dochodzą wcześniej opisane spadek wartości koszyka o 3,4% oraz ewentualne +0,30 zł za paczkę Y w planie Premium. We wszystkich wariantach wynik jest bliski zera lub ujemny.

**Co proponuję.**
1. Poproś kontrolera finansowego o przeliczenie z nowymi stawkami X i danymi z testu krajowego, w tym o strukturę wagową paczek z koszyków 99–149 zł. To powinno być przed 2026-12-01.
2. Zdecyduj z Head of Product i kontrolerem, czy start 2026-12-01 zostaje. Opcje: start z twardszym kryterium wycofania (np. miesięczny przegląd zamiast czekania do końca Q1), wariant z progiem 119 zł (odrzucony wcześniej za mniejszy efekt konwersji, ale tańszy) albo przesunięcie startu. Pierwotna decyzja zatwierdziła wynik dodatni, a przesłanka właśnie zniknęła.
3. Zapytaj Zakupy, czy da się wynegocjować łagodniejsze warunki dla paczek ciężkich lub dopłaty paliwowej przed akceptacją. Czy aneks jest już podpisany, tego nie wiem.

### 2. INT-233 postępuje, ale zamrożenie wdrożeń zawęża Twoje pole manewru (06-sprint-review-integracje.md, 02-swieta-dyzury.md)

- Integracje: mapowanie zdarzeń v3 na statusy OMS jest gotowe, testy przedprodukcyjne w toku, termin 2026-12-12 niezagrożony. Przegląd nie wspomina o planie Premium ani o wpływie na panel. Zapytaj, jak wygląda mapowanie dla Y i czy status „w doręczeniu” został z osi usunięty lub zastąpiony, bo to nadal otwarta sprawa z zeszłego tygodnia (dane o Y co ok. 12 h, brak „w doręczeniu”).
- Zamrożenie wdrożeń trwa od 2026-12-20 do 2027-01-04 (wyjątki za zgodą CTO). Release panelu 2026-12-10 i start progu 2026-12-01 są przed nim. Ewentualne poprawki panelu po migracji Y (data dostawy w czasie inwentaryzacji magazynu, ograniczenia osi czasu) muszą wejść do 2026-12-19 albo wymagają wyjątku. Komunikacja o wycofaniu płatności za pobraniem w styczniu wypada po zamrożeniu, więc nie ma konfliktu.

### 3. Konkurenci i próg dostawy: do wiadomości przy przeglądzie po Q1 (01-konkurent-prog-dostawy.md)

- Konkurent Z obniżył próg do 79 zł tylko dla automatów paczkowych, a V wprowadził abonament z darmową dostawą (19 zł miesięcznie). Wariant „darmowa dostawa tylko do paczkomatów” był w Twojej decyzji odrzucony z powodu złożoności komunikacji. Ruch Z pokazuje, że rynek idzie w tę stronę. Nie wymaga to działania teraz, ale jeśli aneks X pogorszy wynik, wariant z paczkomatami (zwykle tańszy w obsłudze, [założenie: nie mam danych o kosztach u naszych przewoźników]) warto przeanalizować przy przeglądzie. W teście progu nie mierzono reakcji konkurencji.

## Pominąłem

Badanie UX ekranu „Ulubione”, newsletter wewnętrzny i wynik finansowy za październik (marża brutto -0,6 pp r/r to tło, nie sygnał dla Twoich decyzji). W sprincie Integracji pominąłem INT-241 (faktury X) i dług techniczny.
