Rozumiem. Poniżej Twoje trzy decyzje w skrócie, razem z tym, na co będę zwracać uwagę w materiałach.

**1. Darmowa dostawa od 99 zł (zatwierdzona 2026-10-20, start 2026-12-01)**
Obniżasz próg ze 149 zł do 99 zł. Podstawą jest test A/B (+6,1% konwersji w koszykach 99–149 zł) oraz szacunek kontrolera: ok. 18 000 dodatkowych paczek miesięcznie przy średnim koszcie 11,80 zł (przewoźnik X 12,00 zł, ok. 65% paczek; przewoźnik Y 11,40 zł, ok. 35%) daje ok. 212 400 zł kosztu i ok. 235 000 zł dodatkowej marży. Wynik to ok. +22 600 zł miesięcznie, czyli dodatni, ale wrażliwy na założenia. Zatwierdzono z przeglądem po Q1 2027, a następny krok to zmiana progu w koszyku w sprincie 33. Odrzuciłeś próg 119 zł (słabszy efekt w teście) i wariant tylko dla paczkomatów (złożona komunikacja).

**2. Panel statusu zamówienia, zakres zawężony (zatwierdzony 2026-10-27, release 2026-12-10)**
Kontynuujesz panel tylko w zawężonym zakresie: czytelne nazwy statusów, przewidywana data dostawy z SLA przewoźnika (X: D+1, Y: D+2), oś czasu z pięcioma statusami i znacznik „ostatnia aktualizacja". Decyzja opiera się na tym, że zespół integracji naprawił we wrześniu webhooki przewoźnika Y (mediana opóźnienia zdarzeń spadła z 31 h do 1,5 h), a udział kontaktów o status spadł z 38% do 27%. Panel ma sens tylko dopóki dane od przewoźników są aktualne. Metryka rezultatu to spadek udziału kontaktów o status z 27% do 20% w 8 tygodni po wdrożeniu.

**3. Wycofanie płatności za pobraniem (zatwierdzone 2026-10-29, wyłączenie 2027-02-01)**
Wyłączasz płatność za pobraniem w checkoucie od 2027-02-01. Płatność ta to 4,1% zamówień (Q3 2026). Kosztuje 3,50 zł opłaty przewoźnika za zamówienie plus 9% nieodebranych zamówień (zwrot i ponowne magazynowanie). Z ankiety (n=640) wynika, że 62% tych klientów przejdzie na BLIK, a 21% na kartę, więc szacowana utrata to ok. 0,7% zamówień, pokrywana oszczędnościami. Zaakceptowane ryzyko to rezygnacja części starszych klientów. Komunikacja do klientów jest planowana na styczeń. Checkout jest jedną wspólną aplikacją dla całej platformy, więc ta zmiana dotyka wszystkich kanałów i rynków, nie tylko Twojego obszaru.

**Jak będę oceniać materiały.** Co tydzień wskażę tylko to, co wpływa na założenia lub terminy tych trzech decyzji, i napiszę dlaczego. Dotyczy to zwłaszcza:
- kosztów paczek i udziału przewoźników X/Y,
- jakości danych od przewoźników,
- konwersji i kontaktów o status,
- płatności i checkoutu,
- terminów: 2026-12-01, 2026-12-10, 2027-02-01 i przeglądu po Q1 2027.

Resztę pominę.
