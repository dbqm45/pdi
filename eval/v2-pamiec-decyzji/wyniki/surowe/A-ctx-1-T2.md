W tym tygodniu wymagają Twojej uwagi dwie rzeczy, a dwie kolejne są do wiadomości. Pozostałe materiały nie wpływają na Twoje decyzje.

## 1. Wyniki rozszerzonego testu A/B a próg darmowej dostawy (wymaga uwagi)

**Co się zmieniło.** Twoja decyzja z 2026-10-20 opierała się na pilotażu w 3 miastach (+6,1% konwersji w koszykach 99–149 zł). Test na całą Polskę przez 6 tygodni (zespół Danych, 2026-11-13) pokazuje:
- konwersja w koszykach 99–149 zł: +5,8% (95% CI: +4,1% do +7,5%),
- konwersja ogółem: +0,9%,
- **średnia wartość koszyka: −3,4%**, bo część klientów przestaje dobierać produkty do 149 zł,
- zwroty bez istotnych różnic.

**Dlaczego to ważne.** Wynik finansowy z notatki to tylko ok. +22 600 zł miesięcznie, czyli margines. Dwie zmiany mogą go zjeść:
- Efekt konwersji jest nieco niższy niż w pilotażu. Zakładam tu, że dodatkowa marża skaluje się z efektem konwersji. Jeśli koszt 18 000 dodatkowych paczek nie skaluje się razem z nią, wynik spada do ok. +11 000 zł (235 000 zł × 5,8/6,1 − 212 400 zł). Jeśli skalują się oba człony, wynik zmienia się niewiele. Nie wiem, jak kontroler wyliczył 18 000 paczek, więc nie rozstrzygam, który przypadek zachodzi [założenie].
- Spadek średniego koszyka o 3,4% nie występuje w szacunku z notatki, a to bezpośrednio ubytek marży na zamówieniach, które już mamy. Nie umiem go przeliczyć na złotówki, bo nie mam wolumenu zamówień ani marży na koszyk.
- Przedział ufności jest szeroki. Przy dolnej granicy (+4,1%) efekt konwersji jest ok. 30% niższy niż w pilotażu. Przy takim marginesie wynik mógłby być bliski zera lub ujemny. To scenariusz graniczny wyliczony tą samą prostą proporcją, nie prognoza.

**Co proponuję.** Poproś kontrolera finansowego o przeliczenie modelu na danych z testu krajowego, z uwzględnieniem spadku koszyka, zanim wystartujesz 2026-12-01. Decyzji nie trzeba z tego powodu odwoływać: wniosek zespołu Danych jest taki, że efekt się potwierdza, tylko słabiej. Przegląd po Q1 2027 warto jednak oprzeć na tym przeliczeniu, a nie na liczbach z notatki. Przy okazji ustal z Danych, jakie wartości koszyka i konwersji uznasz za sygnał do wycofania lub korekty progu (np. 119 zł, który odrzuciłeś ze względu na mniejszy efekt).

## 2. Inwentaryzacja magazynu a panel statusu i start darmowej dostawy (wymaga uwagi)

**Co się zmieniło.** Magazyn główny robi inwentaryzację 2026-12-28 – 2026-12-30. Zamówienia złożone po 2026-12-27 będą wysłane dopiero 2026-12-31. Zespoły produktowe są proszone o informację na stronie od 2026-12-20.

**Dlaczego to Cię dotyczy.**
- Panel statusu pokazuje przewidywaną datę dostawy liczoną z SLA przewoźnika (X: D+1, Y: D+2). Release jest 2026-12-10, więc w okresie inwentaryzacji panel będzie pokazywał daty zaniżone o 3–4 dni. Zamówienie z 2026-12-28 dostanie datę ok. 2026-12-29/30, a rzeczywista będzie dopiero po 2027-01-01. To dokładnie ten rodzaj nieaktualnej informacji, który według Twojej notatki wywołał kontakty o status w sierpniu. W okresie świątecznym tego ryzyka nie wolno lekceważyć, bo wtedy kontakty o status zwykle rosną [założenie, brak danych w materiałach].
- Metryka rezultatu panelu (z 27% do 20% w 8 tygodni po wdrożeniu) obejmie te dni. Ewentualny skok kontaktów w okresie inwentaryzacji trzeba będzie przy ocenie odseparować.
- Darmowa dostawa startuje 2026-12-01 i jest wprost związana z okresem świątecznym. Przy progu 99 zł wzrośnie liczba zamówień. Informacja o dłuższym czasie wysyłki powinna objąć też koszyk i checkout (to miejsce Twojej inicjatywy), a nie tylko stronę główną.

**Co proponuję.** Ustal z Tech Leadem Zamówienia, czy w zakresie panelu (jeszcze przed release) da się uwzględnić datę wysyłki zależną od kalendarza magazynu, a nie samo SLA przewoźnika. Jeśli nie da się tego zrobić do 2026-12-10, trzeba przynajmniej dodać komunikat w panelu dla zamówień po 2026-12-27. Wymagania na to nie wchodzą w dotychczasowy zawężony zakres, więc to zmiana zakresu do Twojej decyzji. Zdecyduj też, kto odpowiada za komunikat w koszyku od 2026-12-20.

## 3. Do wiadomości

- **Design System v4: komponent „Timeline" (oś czasu), warianty pionowy i poziomy.** Panel ma w zakresie oś czasu z pięcioma statusami, więc to gotowy komponent do wykorzystania. Warto, żeby Tech Lead i UX to sprawdzili. Wycofany „Badge v2" dotyczy Cię tylko, jeśli statusy w panelu go używają. Tego z materiałów nie wiem. Migracja komponentów trwa do 2027-01-31.
- **Incydent BLIK z 2026-11-12 (2 h 40 min, ok. 240 utraconych zamówień).** To pierwszy incydent w 2026 r. i nie zmienia decyzji, ale to konkretny punkt do monitorowania przy wycofaniu płatności za pobraniem. Zakładasz, że 62% klientów za pobraniem przejdzie na BLIK, więc zależność od tego jednego dostawcy rośnie. Z liczb w raporcie wynika też, że 160 minut w jednym miesiącu przekracza deklarowaną dostępność 99,95% (to ok. 22 minuty miesięcznie). Mogę się mylić co do sposobu liczenia umowy, więc to do sprawdzenia z Head of Payments, nie wniosek. Dodany alert na błędy BLIK > 5% w ciągu 10 min jest dobrą informacją.

## Pominąłem

Notatkę OKR Marketingu, opinie z App Store, komunikat bezpieczeństwa o aktualizacji bibliotek (termin 2026-11-20, dotyczy zespołów backendowych) oraz wcześniejsze materiały bez zmian w tej sprawie. Nie ma nowych informacji o Czechach ani o checkoucie z poprzedniego tygodnia.
