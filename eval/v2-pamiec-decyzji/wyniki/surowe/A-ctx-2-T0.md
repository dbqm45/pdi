Rozumiem. Oto Twoje trzy decyzje, tak jak je odczytuję.

**1. Darmowa dostawa od 99 zł (zatwierdzona 2026-10-20, start 2026-12-01)**
Obniżamy próg ze 149 zł do 99 zł. Podstawą jest test A/B (+6,1% konwersji dla koszyków 99–149 zł) oraz szacunek kontrolera. Szacunek zakłada ok. 18 000 dodatkowych paczek miesięcznie po średnim koszcie 11,80 zł (przewoźnik X 12,00 zł i ok. 65% paczek, przewoźnik Y 11,40 zł i ok. 35% paczek), czyli ok. 212 400 zł. Dodatkowa marża wynosi ok. 235 000 zł, więc wynik to ok. +22 600 zł miesięcznie. Wynik jest dodatni, ale niewielki, dlatego decyzja ma przegląd po Q1 2027. Odrzuciliśmy próg 119 zł (słabszy efekt w teście) oraz darmową dostawę tylko do paczkomatów (złożoność komunikacji). Wdrożenie progu w koszyku jest w sprincie 33.

**2. Panel statusu zamówienia, zakres zawężony (zatwierdzony 2026-10-27, release 2026-12-10)**
Panel ma sens tylko dlatego, że dane o zdarzeniach od przewoźników są teraz aktualne. We wrześniu poprawiono webhooki przewoźnika Y: mediana opóźnienia spadła z 31 h do 1,5 h, a udział kontaktów o status z 38% do 27%. Zakres obejmuje czytelne nazwy statusów, przewidywaną datę dostawy z SLA przewoźnika (X: D+1, Y: D+2), oś czasu z pięcioma etapami i znacznik „ostatnia aktualizacja”. Metryka rezultatu to spadek udziału kontaktów o status z 27% do 20% w 8 tygodni po wdrożeniu.

**3. Wycofanie płatności za pobraniem (zatwierdzone 2026-10-29, wyłączenie 2027-02-01)**
Wyłączamy tę metodę w checkoucie. Płatność za pobraniem to 4,1% zamówień (Q3 2026), a kosztuje nas 3,50 zł opłaty przewoźnika za zamówienie oraz zwroty (9% zamówień za pobraniem jest nieodbieranych). Według ankiety (n=640) 62% klientów przejdzie na BLIK, a 21% na kartę. Szacowana utrata to ok. 0,7% zamówień, pokryta oszczędnościami. Zaakceptowane ryzyko to rezygnacja części starszych klientów. Checkout jest wspólną aplikacją dla całej platformy, a komunikacja do klientów jest planowana na styczeń.

Od następnego razu, gdy wkleisz materiały, wskażę tylko to, co wymaga Twojej uwagi w kontekście tych trzech decyzji, i podam dlaczego. Pominę resztę.
