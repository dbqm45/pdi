Wymagają Twojej uwagi cztery materiały: 03, 06, 01 i 02. Poniżej są ułożone od najważniejszego.

## 1. Aneks nr 4 do umowy z przewoźnikiem X (03) – inicjatywa 1, próg darmowej dostawy

**Dlaczego to ważne.** Aneks wchodzi w życie 2026-12-01, czyli tego samego dnia co niższy próg. Podnosi koszt każdej przesyłki, a przy progu 99 zł darmową dostawę sfinansujesz częściej. Rekomendacja Zakupów to akceptacja, bo alternatywnego przewoźnika nie będzie przed Q2 2027. Renegocjacja jest możliwa dopiero w czerwcu 2027. Przez co najmniej pół roku przyjmij więc nowe stawki jako stałe.

**Szacunek wpływu.** Zakładam, że dopłata 9% liczy się od stawki bazowej danej kategorii. Zakładam też, że udział 14% paczek ciężkich dotyczy także zamówień objętych darmową dostawą. Oba założenia są niezweryfikowane.

| Rodzaj paczki | Koszt dotąd | Koszt od 2026-12-01 | Zmiana |
|---|---|---|---|
| Standardowa | 12,00 zł | ok. 13,08 zł | +1,08 zł |
| Ciężka (powyżej 10 kg) | 12,00 zł | ok. 21,69 zł | +9,69 zł (ok. +80%) |
| Średnio (86% standardowych, 14% ciężkich) | 12,00 zł | ok. 14,30 zł | ok. +2,30 zł (ok. +19%) |

**Co z tym zrobić.**
- Przelicz business case progu 99 zł na nowych stawkach. Paczka ciężka kosztuje ok. 21,69 zł, a zamówienie z przedziału 99–149 zł często ma niską marżę.
- Sprawdź, jaki udział paczek ciężkich mają zamówienia w przedziale 99–149 zł. Tych danych w materiałach nie ma.
- Ustal z Zakupami, czy akceptacja aneksu jest już zdecydowana. Jeśli nie, dostarcz im swoje wyliczenie przed decyzją.
- Rozważ, czy przy progu 99 zł wyłączyć paczki ciężkie z darmowej dostawy albo dać im inny próg. To moja propozycja do oceny, nie wniosek z materiałów.

## 2. Sprint 33, Integracje: INT-233 (06) – inicjatywa 2, panel statusu zamówienia

**Dlaczego to ważne.** Migracja przewoźnika Y na API v3 ma termin 2026-12-12, a release panelu jest 2026-12-10. Panel statusu zależy od zdarzeń przewoźników. Mapowanie zdarzeń jest gotowe, ale testy na środowisku przedprodukcyjnym trwają. Panel wyjdzie więc na dwa dni przed cutoverem, i to dla przewoźnika, którego zdarzenia się zmieniają.

**Co z tym zrobić.**
- Ustal z zespołem Integracje, czy panel w zawężonym zakresie czyta zdarzenia przewoźnika Y.
- Jeśli czyta, sprawdź, czy w dniach 10–12 grudnia statusy będą poprawne, i kto odpowiada za cutover.
- Zapytaj, czy po 12 grudnia mogą pojawić się różnice w statusach i czy trzeba to uwzględnić w testach akceptacyjnych.
- Termin INT-233 jest oceniany jako niezagrożony, ale zależność od Twojego release'u nie została w materiale nazwana.

## 3. Konkurent Z (01) – inicjatywa 1, próg darmowej dostawy

**Dlaczego to ważne.** Konkurent Z od 2026-11-20 oferuje darmową dostawę od 79 zł, czyli poniżej Twojego planowanego progu 99 zł. Obniżka dotyczy tylko dostawy do automatów paczkowych. To zawęża porównanie: dla dostawy kurierskiej Z nie zmienił progu, a Twoja zmiana obejmuje pewnie obie formy.

**Co z tym zrobić.**
- Uwzględnij to w uzasadnieniu progu 99 zł. Nie jesteś już najtańszy w automatach paczkowych.
- Rozważ, czy dla automatów paczkowych próg powinien być niższy. Automaty to zwykle tańsza dostawa i mogą nie podlegać nowej kategorii „paczka ciężka”, ale to założenie wymaga sprawdzenia.
- Pozostałe wpisy z monitoringu (abonament konkurenta V, brak zmian u W) pomijam. Nie zmieniają nic w Twoich decyzjach.

## 4. Dyżury i zamrożenie wdrożeń (02) – inicjatywa 2, w mniejszym stopniu 1 i 3

**Dlaczego to ważne.** Zamrożenie wdrożeń trwa od 2026-12-20 do 2027-01-04, a wyjątki wymagają zgody CTO. Release panelu 2026-12-10 ma więc zapas tylko 10 dni. Jeśli się opóźni o więcej niż około tydzień, praktycznie przejdzie na 5 stycznia 2027 lub później, chyba że CTO zgodzi się na wyjątek. Start progu 1 grudnia jest przed zamrożeniem. Wycofanie płatności za pobraniem od 1 lutego 2027 jest po nim.

**Co z tym zrobić.**
- Traktuj 19 grudnia jako twardy termin awaryjny dla panelu.
- Ewentualne poprawki po starcie progu 99 zł planuj do 19 grudnia, bo potem możliwe są tylko wyjątki.
- Zaplanuj dyżur lub kontakt na okres 23 grudnia – 2 stycznia, gdy ruch świąteczny wzmocni efekt nowego progu.

## Pominięte

Nie flaguję materiałów 04 (badanie ekranu „Ulubione”), 05 (newsletter) ani 07 (wynik finansowy za październik). Nie dotyczą Twoich trzech inicjatyw. Z materiału 06 pomijam też INT-241 (format faktur przewoźnika X) i dług techniczny dotyczący biblioteki HTTP. Żaden z tych wpisów nie wpływa na wycofanie płatności za pobraniem, a wycofanie jest inicjatywą, której w tym tygodniu nic nie dotyczy bezpośrednio.
