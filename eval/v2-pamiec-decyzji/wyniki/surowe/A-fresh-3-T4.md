Z siedmiu materiałów uwagi wymagają trzy (03, 06, 02), a jeden (01) warto mieć na radarze. Pozostałe trzy pomijam.

## Wymaga uwagi

### 1. Aneks nr 4 do umowy z przewoźnikiem X (03) – inicjatywa 1 (próg 99 zł)

Zmiany z aneksu wchodzą w życie 2026-12-01, czyli w dniu startu niższego progu darmowej dostawy. Nie przeczytałem ich jeszcze w żadnym modelu biznesowym progu, więc to trzeba sprawdzić.

- Dopłata paliwowa 9% dotyczy całego wolumenu u przewoźnika X.
- Paczka ciężka (powyżej 10 kg) kosztuje 19,90 zł zamiast 12,00 zł.
- Po obniżce progu do 99 zł więcej zamówień dostanie dostawę za darmo, a koszt tej dostawy ponosimy my. Jednostkowy koszt dostawy rośnie dokładnie wtedy, gdy rośnie liczba darmowych dostaw.

Szacunek (moje założenia, do potwierdzenia z Zakupami):

- Zakładam, że dopłata 9% liczy się od stawki bazowej także dla paczki ciężkiej.
- Paczka standardowa: 12,00 zł → ok. 13,08 zł.
- Paczka ciężka: 19,90 zł → ok. 21,69 zł.
- Przy udziale ok. 14% paczek ciężkich średni koszt przesyłki u przewoźnika X rośnie z 12,00 zł do ok. 14,29 zł, czyli o ok. 19%.
- Dotyczy to tylko wolumenu przewoźnika X. Nie wiem, jaki to udział wszystkich zamówień.

Co z tym zrobić:

- Przeliczyć uzasadnienie biznesowe progu 99 zł z nowymi stawkami przed 2026-12-01.
- Zdecydować, czy darmowa dostawa na progu 99 zł obejmuje paczki ciężkie. Jeśli tak, to każde zamówienie 99–149 zł z paczką ciężką kosztuje nas ok. 21,69 zł zamiast 12 zł.
- Wiemy, że Zakupy rekomendują akceptację aneksu, bo alternatywnego przewoźnika nie ma przed Q2 2027. Renegocjacja jest możliwa dopiero w czerwcu 2027. Te stawki obowiązują więc przez całe pierwsze miesiące działania nowego progu.
- Tło: wynik za październik pokazuje marżę brutto −0,6 pp r/r (presja promocji) i koszty logistyki na poziomie 8,5% przychodów (07). Samo to nie wymaga działania, ale pokazuje, że marża jest już obciążona.

### 2. Sprint review Integracji, INT-233 (06) – inicjatywa 2 (panel statusu)

Migracja przewoźnika Y na API v3 ma termin 2026-12-12, czyli dwa dni po release panelu statusu (2026-12-10). Zmieniają się mapowania zdarzeń przewoźnika, a panel statusu prawdopodobnie na nich się opiera [założenie, nie mam specyfikacji panelu].

Do sprawdzenia:

- Czy panel w zawężonym zakresie pokazuje statusy przesyłek przewoźnika Y?
- Jeśli tak, czy statusy będą poprawne przed i po cięciu 2026-12-12?
- Kto w zespole Integracje odpowiada za koordynację? Testy są jeszcze „w toku" na środowisku przedprodukcyjnym.

Termin migracji jest według zespołu niezagrożony, więc nie ma tu alarmu, tylko zależność do potwierdzenia. INT-241 (format faktur od przewoźnika X) nie dotyczy moich inicjatyw.

### 3. Zamrożenie wdrożeń (02) – inicjatywy 2 i 3

Zamrożenie trwa od 2026-12-20 do 2027-01-04. Wyjątki są możliwe tylko za zgodą CTO.

- Panel statusu (release 2026-12-10) ma 10 dni zapasu przed zamrożeniem. Każde opóźnienie powyżej tego zapasu, na przykład z powodu migracji z punktu 2, oznacza przesunięcie po 2027-01-04 albo prośbę o wyjątek do CTO.
- Poprawki po release panelu, w tym hotfixy, mają okno do 2026-12-20.
- Nowy próg 99 zł startuje 2026-12-01, przed zamrożeniem, więc sam start nie jest zagrożony. Ewentualne korekty progu po starcie też muszą zmieścić się przed 12-20.
- Inicjatywa 3 (wycofanie płatności za pobraniem od 2027-02-01) jest po zamrożeniu. Prace przygotowawcze trzeba jednak zaplanować tak, żeby nie wypadły w okresie zamrożenia i dyżurów świątecznych (2026-12-23 – 2027-01-02).

## Do wiadomości, bez pilnego działania

### Monitoring konkurencji (01) – inicjatywa 1

- Konkurent Z obniżył próg do 79 zł od 2026-11-20, ale tylko dla dostawy do automatów paczkowych. Nasz próg 99 zł nie jest więc ani najniższy, ani bezpośrednio porównywalny.
- Konkurent V ma abonament z darmową dostawą (19 zł/mies.).
- Konkurent W (199 zł) bez zmian.

To potwierdza kierunek obniżki progu, ale nie zmienia daty ani zakresu. Warto rozważyć, czy komunikacja progu 99 zł ma odnosić się do ofert Z i V. Ewentualne dostosowanie dla automatów paczkowych to osobna decyzja, której materiały nie wymagają.

## Pominięte (bez znaczenia dla Twoich inicjatyw)

- Badanie UX ekranu „Ulubione" (04).
- Newsletter wewnętrzny (05).

Uwaga: żaden z materiałów nie dotyczy bezpośrednio wycofania płatności za pobraniem (inicjatywa 3). Poza kwestią planowania wokół zamrożenia nie ma tu nic do zgłoszenia.
