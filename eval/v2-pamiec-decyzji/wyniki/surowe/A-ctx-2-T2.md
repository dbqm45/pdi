W tym tygodniu uwagi wymagają dwie rzeczy, trzecia jest drobniejsza.

## 1. Wyniki rozszerzonego testu A/B osłabiają uzasadnienie progu 99 zł (05-wyniki-ab-prog-dostawy.md)

**Co się zmieniło.** Test w całej Polsce dał +5,8% konwersji w koszykach 99–149 zł (przedział ufności 95%: +4,1% do +7,5%), a pilotaż w 3 miastach +6,1%. Zespół Danych pisze, że efekt się potwierdza, ale jest nieco niższy. Wprowadza też dwie nowe informacje. Średnia wartość koszyka spadła o 3,4%, bo część klientów nie dobiera produktów do 149 zł. Konwersja ogółem wzrosła tylko o 0,9%.

**Dlaczego to ważne dla decyzji.** Wynik finansowy z Twojej notatki to różnica dwóch dużych liczb: ok. 235 000 zł dodatkowej marży minus ok. 212 400 zł kosztu dostaw, czyli ok. +22 600 zł miesięcznie. Marża pochodziła z efektu +6,1%.
- Przy +5,8% marża spada do ok. 223 000 zł, a wynik do ok. +11 000 zł miesięcznie. Zakładam przy tym, że marża rośnie proporcjonalnie do efektu konwersji, a liczba dodatkowych paczek (ok. 18 000) i koszt paczki się nie zmieniają. To moje uproszczenie, nie przeliczenie kontrolera [założenie].
- Przy dolnej granicy przedziału (+4,1%) ta sama proporcja daje marżę ok. 158 000 zł i wynik ujemny rzędu −54 000 zł miesięcznie [założenie].
- Spadek wartości koszyka o 3,4% nie był w szacunku uwzględniony. Dla klientów, którzy i tak kupowaliby powyżej 149 zł, a teraz płacą mniej za zamówienie, ale dostawę mają za darmo, spadek marży jest dodatkowy. Nie umiem go policzyć bez danych Zespołu Danych [niezweryfikowane].

Decyzja została zatwierdzona jako dodatnia, ale niewielka, z przeglądem po Q1 2027. Nowe dane pokazują, że zapas jest mniejszy, niż zakładano, a wynik może być bliski zera lub ujemny.

**Co proponuję.** Poproś kontrolera finansowego o ponowne przeliczenie z wynikami testu krajowego (efekt +5,8% z przedziałem, spadek wartości koszyka, zwroty bez różnic). Zrób to przed startem 2026-12-01, bo wtedy decyzja jest jeszcze tania do zmiany. Warto też ustalić z Head of Product kryterium wycofania lub zmiany progu na przeglądzie po Q1.

## 2. Inwentaryzacja magazynu wpływa na przewidywaną datę dostawy w panelu (06-magazyn-inwentaryzacja.md)

**Co się stało.** W dniach 2026-12-28 – 2026-12-30 trwa inwentaryzacja. Zamówienia złożone po 2026-12-27 będą wysłane dopiero 2026-12-31. Magazyn prosi zespoły produktowe o informację na stronie od 2026-12-20.

**Dlaczego to ważne dla decyzji.** Panel statusu wchodzi 2026-12-10, a przewidywana data dostawy jest liczona z SLA przewoźnika (X: D+1, Y: D+2). Taka logika nie uwzględnia opóźnienia po stronie magazynu, więc w okresie inwentaryzacji panel będzie pokazywał zbyt wczesne daty. To odtworzy problem, który panel miał rozwiązać: klient widzi nieaktualną informację i kontaktuje się w sprawie statusu. Wypada to w szczycie świątecznym i w oknie 8 tygodni, w którym mierzysz metrykę rezultatu (27% do 20%). Okres inwentaryzacji może więc zaburzyć odczyt tej metryki.

**Co proponuję.** Ustal z Tech Leadem, czy da się dodać do wyliczenia daty dostawy wyjątek magazynowy (przesunięcie dla zamówień po 27.12) albo komunikat na osi czasu. Przy ocenie metryki panelu zaznacz ten okres jako zakłócony. Informacja na stronie od 20.12 jest też okazją, żeby uzgodnić komunikat z zespołem odpowiedzialnym za nią.

## 3. Drobniejsze, bez pilnej akcji

- **Design System v4: komponent „Timeline”.** Oś czasu z Twojego zakresu panelu (przyjęte, w kompletacji, nadane, w doręczeniu, doręczone) jest teraz dostępna w bibliotece w wariantach pionowym i poziomym. Warto zapytać UX i Tech Leada, czy użyć gotowego komponentu zamiast własnego. Migracja do nowych tokenów trwa do 2027-01-31, więc panel ma wyjść na tokenach, które są w trakcie wymiany [założenie: nie wiem, czy to zmiana dla panelu].
- **Incydent BLIK (2026-11-12, 2 h 40 min).** Nie zmienia decyzji o pobraniu: to pierwszy incydent w 2026 r., a utrata to ok. 240 zamówień. Warto jednak pamiętać, że 62% klientów płacących za pobraniem deklaruje przejście na BLIK, więc po wyłączeniu pobrania zależność od jednej metody wzrośnie. 2 h 40 min niedostępności w miesiącu to ok. 99,6%, czyli poniżej deklarowanych 99,95% (to moje wyliczenie, sprawdź je z Head of Payments).

## Pominąłem

Opinie ze sklepów z aplikacjami, OKR marketingu, komunikat bezpieczeństwa i aktualizację bibliotek. Nie dotyczą one Twoich trzech inicjatyw.
