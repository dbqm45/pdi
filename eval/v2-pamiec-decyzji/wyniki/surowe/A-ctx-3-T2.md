## Wymaga Twojej uwagi: 4 rzeczy (kolejność wg wagi)

### 1. Rozszerzony test A/B progu dostawy osłabia uzasadnienie finansowe (05-wyniki-ab-prog-dostawy.md)

- **Co się zmieniło.** Notatka z decyzji opierała się na pilotażu: +6,1% konwersji w koszykach 99–149 zł. Test w całej Polsce daje +5,8% (przedział 95%: +4,1% do +7,5%). Do tego dochodzi nowa informacja: średnia wartość koszyka spada o 3,4%, bo część klientów przestaje dobierać produkty do 149 zł. Spadku wartości koszyka nie było w szacunku kontrolera, a kontroler liczył tylko dodatkową marżę z konwersji.
- **Dlaczego to ważne.** Wynik ok. +22 600 zł miesięcznie to różnica dwóch dużych liczb (235 000 zł marży minus 212 400 zł kosztu paczek), więc jest bardzo wrażliwy. Moje szacunki proporcjonalne [założenie: marża rośnie liniowo z efektem konwersji, reszta bez zmian]:
  - przy +5,8% marża wynosi ok. 223 400 zł, a wynik ok. +11 000 zł;
  - przy dolnej granicy przedziału (+4,1%) marża wynosi ok. 158 000 zł, a wynik ok. -54 000 zł;
  - spadek wartości koszyka o 3,4% pogarsza to jeszcze bardziej.
- **To nie jest dowód, że decyzja jest zła.** Konwersja ogółem rośnie o 0,9%, zwroty bez zmian, a efekt się potwierdził. Ale margines, z jakim zatwierdzono decyzję, praktycznie zniknął, a przegląd jest dopiero po Q1 2027.
- **Co proponuję.** Poproś kontrolera finansowego o przeliczenie z danymi z testu (konwersja, wartość koszyka, liczba dodatkowych paczek). Zdecyduj teraz, czy zostajesz przy starcie 2026-12-01 i przeglądzie po Q1, czy dajesz twardsze kryterium wycofania. Start jest za mniej niż dwa tygodnie od dzisiejszych materiałów, więc czas na tę rozmowę jest teraz.

### 2. Inwentaryzacja magazynu psuje przewidywaną datę dostawy w panelu (06-magazyn-inwentaryzacja.md)

- Panel statusu wchodzi 2026-12-10 i liczy przewidywaną dostawę z SLA przewoźnika (X: D+1, Y: D+2). Zamówienia złożone po 2026-12-27 będą wysłane dopiero 2026-12-31, bo magazyn główny stoi 2026-12-28 – 30. Panel pokaże więc datę, która będzie nieprawdziwa o kilka dni, i to w szczycie świątecznym.
- To dokładnie ten problem, który panel miał rozwiązywać: aktualne i wiarygodne informacje o statusie. Pierwszy okres pomiaru metryki (27% do 20% w 8 tygodni) obejmie ten okres.
- Magazyn prosi zespoły produktowe o informację na stronie od 2026-12-20. Zapytaj Tech Leada, czy da się uwzględnić te dni w obliczaniu daty (kalendarz wyjątków) albo pokazać komunikat przy panelu. Wymaga to decyzji przed release'em 2026-12-10.

### 3. Design System v4 zawiera komponent „Timeline” (01-design-system-v4.md)

- Twój panel ma oś czasu (przyjęte, w kompletacji, nadane, w doręczeniu, doręczone). Biblioteka ma teraz gotowy komponent w wariantach pionowym i poziomym. Zapytaj Tech Leada i UX, czy zespół używa go zamiast budować własny. Oszczędza to czas przy release'u 2026-12-10 i zapewnia zgodność z tokenami.
- Wycofano „Badge v2”, a migracja komponentów do nowych tokenów trwa do 2027-01-31. Jeśli panel używa Badge v2 do statusów, trzeba to sprawdzić przed release'em. [niezweryfikowane: nie wiem, czy panel go używa]

### 4. Incydent BLIK: warto mieć na radarze (02-incydent-blik.md), niski priorytet

- Wycofanie płatności za pobraniem zakłada, że 62% klientów przejdzie na BLIK. 2026-11-12 BLIK był niedostępny przez 2 h 40 min (ok. 1 900 nieudanych prób, utrata ok. 240 zamówień). Przy 4,1% zamówień za pobraniem po 2027-02-01 ta grupa będzie zależna od BLIK i karty, więc podobna awaria będzie dotykać także ją.
- Dostawca deklaruje 99,95% dostępności miesięcznie, czyli ok. 22 minuty przestoju w miesiącu. Incydent trwał ok. 160 minut, więc przekracza tę deklarację wielokrotnie. [obliczenie własne, zakładam miesiąc 30 dni]. To pierwszy incydent w 2026 r., więc nie zmienia decyzji, ale warto zapytać Head of Payments o alternatywę dla płatności (np. przelew i karta jako zapas) w komunikacji w styczniu.

## Pominąłem

OKR marketingu, opinie w sklepach z aplikacjami i komunikat bezpieczeństwa o aktualizacji biblioteki logowania. Nie mają związku z Twoimi inicjatywami. [założenie dla ostatniego: dotyczy usług backendowych, nie checkoutu ani panelu; jeśli panel korzysta z tej biblioteki, termin 2026-11-20 go obejmuje]
