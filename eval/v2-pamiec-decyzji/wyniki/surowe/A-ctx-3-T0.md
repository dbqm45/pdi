Rozumiem. Poniżej krótkie potwierdzenie każdej z trzech decyzji.

**1. Darmowa dostawa od 99 zł (zamiast 149 zł)**
Od 2026-12-01 próg spada ze 149 zł do 99 zł. Podstawą jest test A/B (+6,1% konwersji w koszykach 99–149 zł) i szacunek kontrolera: ok. 18 000 dodatkowych darmowych paczek miesięcznie kosztuje ok. 212 400 zł (średnio 11,80 zł za paczkę, przewoźnik X 12,00 zł i ok. 65% paczek, Y 11,40 zł i ok. 35%), a dodatkowa marża to ok. 235 000 zł. Wynik to ok. +22 600 zł miesięcznie, czyli dodatni, ale niewielki, więc zatwierdzono go z przeglądem po Q1 2027. Odrzucone warianty to próg 119 zł (mniejszy efekt) i darmowa dostawa tylko do paczkomatów (złożona komunikacja). Zysk jest wrażliwy na koszt paczki i liczbę dodatkowych paczek, więc będę zwracać uwagę na wszystko, co je zmienia, np. stawki przewoźników, zmiany ich udziałów i konwersję.

**2. Panel statusu zamówienia (zakres zawężony)**
Panel kontynuujemy tylko dlatego, że we wrześniu naprawiono webhooki przewoźnika Y: mediana opóźnienia zdarzeń spadła z 31 h do 1,5 h, a udział kontaktów o status z 38% do 27%. Zakres obejmuje czytelne nazwy statusów, przewidywaną datę dostawy z SLA przewoźnika (X: D+1, Y: D+2), oś czasu z pięcioma statusami i znacznik „ostatnia aktualizacja”. Release jest 2026-12-10, a metryka sukcesu to spadek kontaktów o status z 27% do 20% w 8 tygodni po wdrożeniu. Warunkiem sensu panelu są aktualne dane od przewoźników, więc zareaguję na sygnały o ich pogorszeniu albo zmianie SLA lub integracji.

**3. Wycofanie płatności za pobraniem**
Płatność za pobraniem wyłączamy w checkoucie od 2027-02-01. Stanowi 4,1% zamówień i kosztuje 3,50 zł opłaty przewoźnika za zamówienie oraz zwroty (9% takich zamówień jest nieodbierane). Według ankiety (n=640) 62% klientów przejdzie na BLIK, a 21% na kartę. Szacowana utrata to ok. 0,7% zamówień, a zaakceptowanym ryzykiem jest rezygnacja części starszych klientów. Checkout jest wspólny dla całej platformy, więc będę zwracać uwagę na wszystko, co dotyka checkoutu i innych kanałów lub rynków, także w kontekście terminu 2027-02-01 i komunikacji w styczniu.

Przy kolejnych materiałach wskażę tylko to, co realnie wpływa na te trzy decyzje, i wyjaśnię dlaczego. Resztę pominę.
