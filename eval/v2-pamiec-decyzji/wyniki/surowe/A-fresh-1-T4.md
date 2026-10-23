Z siedmiu materiałów uwagi wymagają trzy (03, 01, 02), a czwarty (06) trzeba tylko sprawdzić. Pozostałe nie dotyczą Twoich inicjatyw. Nic z tygodnia nie dotyczy inicjatywy (3), wycofania płatności za pobraniem.

## 1. Aneks nr 4 do umowy z przewoźnikiem X (plik 03). Najważniejsze, dotyczy inicjatywy (1)

Aneks wchodzi w życie 2026-12-01, czyli tego samego dnia co niższy próg darmowej dostawy. Każda darmowa przesyłka u przewoźnika X będzie od tego dnia droższa. Business case dla progu 99 zł zakładał prawdopodobnie stare stawki.

- Paczka standardowa kosztuje 12,00 zł plus 9% dopłaty paliwowej, czyli ok. 13,08 zł (+9%).
- Paczka ciężka (powyżej 10 kg) kosztuje 19,90 zł plus 9%, czyli ok. 21,69 zł. To wzrost o ok. 81% względem dzisiejszych 12,00 zł.
- Ciężkie paczki to ok. 14% wolumenu u X. Średni koszt przesyłki u X rośnie według mojego wyliczenia z danych aneksu z ok. 12,00 zł do ok. 14,29 zł, czyli o ok. 19%. Zakładam, że udział 14% dotyczy też zamówień, które dostaną darmową dostawę po zmianie progu. [założenie]
- Obniżenie progu ze 149 do 99 zł zwiększy liczbę zamówień z darmową dostawą, a koszt każdego z nich rośnie. Nie wiem, jaki procent zamówień z przedziału 99–149 zł to paczki ciężkie. Warto to sprawdzić. [niezweryfikowane]
- Zakupy rekomendują akceptację aneksu, a alternatywny przewoźnik nie będzie dostępny przed Q2 2027. Stawek nie zmienisz do renegocjacji w czerwcu 2027. Możesz zmienić tylko własne założenia.

Co zrobić:
- Przeliczyć koszt progu 99 zł na nowych stawkach z aneksu.
- Rozważyć wyłączenie paczek ciężkich z darmowej dostawy albo osobny próg dla nich. Wyłączenie wymaga zmian w regulaminie i w systemie, więc trzeba je zacząć szybko.
- Zapytać Zakupy, czy aneks jest już podpisany, czy dopiero czeka na akceptację. Jeśli czeka, sprawdź, czy Twoje wyliczenia mogą jeszcze wpłynąć na decyzję.

## 2. Konkurent Z obniżył próg do 79 zł (plik 01). Dotyczy inicjatywy (1)

Konkurent Z ma od 2026-11-20 próg 79 zł, ale tylko dla dostawy do automatów paczkowych. To jest mniej, niż wynosi Twój planowany próg 99 zł.

- Nie oznacza to, że 99 zł jest błędną decyzją. Oferta Z jest węższa, bo dotyczy jednej metody dostawy.
- Sprawdź, czy Twój próg 99 zł obejmie wszystkie metody dostawy, w tym automaty paczkowe. Jeśli Z konkuruje głównie na automatach, rozważ próg niższy tylko dla nich. Dla Ciebie byłoby to też tańsze niż darmowa kurier, ale to decyzja do przeliczenia razem z punktem 1.
- Konkurent V (abonament 19 zł/mies.) i konkurent W (199 zł, bez zmian) nie wymagają działania. Przy W Twój próg 99 zł pozostaje wyraźnie lepszy.

## 3. Zamrożenie wdrożeń 2026-12-20 – 2027-01-04 (plik 02). Dotyczy inicjatyw (1) i (2)

- Panel statusu zamówienia (release 2026-12-10) ma 9 dni zapasu przed zamrożeniem. Opóźnienie dłuższe niż do 2026-12-19 wypycha release na 2027-01-05 albo wymaga zgody CTO.
- Niższy próg wejdzie 2026-12-01, w środku sezonu świątecznego. Jeśli po starcie okaże się, że koszty (patrz punkt 1) są za wysokie, korekta progu po 2026-12-20 wymaga wyjątku CTO. Warto mieć plan wycofania lub korekty gotowy przed zamrożeniem.
- Dyżury 2026-12-23 – 2027-01-02: sprawdź, czy ktoś z zespołu panelu i progu jest w grafiku, bo oba mają wystartować tuż przed zamrożeniem.
- Zamrożenie nie koliduje z inicjatywą (3), bo ta startuje 2027-02-01. Pamiętaj jednak, że prace przygotowawcze muszą się zmieścić przed 2026-12-20 albo po 2027-01-04.

## 4. INT-233 w sprint review Integracji (plik 06). Do sprawdzenia, dotyczy inicjatywy (2)

Migracja przewoźnika Y na API v3 ma termin 2026-12-12, dwa dni po release panelu statusu zamówienia. Mapowanie zdarzeń jest gotowe, a testy na środowisku przedprodukcyjnym trwają.

- Jeśli panel pokazuje status na podstawie zdarzeń od przewoźnika Y, to przez 2 dni działa na API v2, a potem przełączy się na v3. Każde niedopasowanie mapowania zdarzeń może pokazać klientom błędny status. Nie wiem, czy panel korzysta ze zdarzeń przewoźnika Y. [niezweryfikowane]
- Zapytaj zespół Integracje, czy panel jest odbiorcą zdarzeń Y i czy zakres „zawężony” obejmuje przewoźnika Y. Jeśli tak, dodaj sprawdzenie statusów w panelu po 2026-12-12 do planu testów.
- Termin 2026-12-12 jest „niezagrożony”, ale poślizg wpadłby w okres tuż przed zamrożeniem.

## Co pominąłem

- Plik 04, badanie UX ekranu „Ulubione”: nie dotyczy dostawy ani panelu zamówienia.
- Plik 05, newsletter: Wigilia firmowa i nowi pracownicy nie wpływają na inicjatywy.
- Plik 06, pozostałe punkty: INT-241 (format faktur od X) jest wdrożony i nie dotyczy statusu ani progu. Wymiana biblioteki HTTP przesunięta na styczeń też nie dotyczy.
- Plik 07, wynik finansowy za październik: ogólny kontekst. Marża brutto spadła o 0,6 pp przez promocje, a koszty logistyki to 8,5% przychodów. Warto o tym pamiętać przy punkcie 1, ale sam z siebie nie wymaga działania.
