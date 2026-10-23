W tym tygodniu wymagają Twojej uwagi trzy rzeczy: aneks do umowy z przewoźnikiem X, zamrożenie wdrożeń i sprint review Integracji (INT-233). Jedna jest do wiadomości. Resztę pomijam.

## 1. Aneks nr 4 do umowy z przewoźnikiem X a opłacalność darmowej dostawy (wymaga pilnej uwagi)

**Co się zmieniło.** Od 2026-12-01, czyli w dniu startu progu 99 zł, u przewoźnika X obowiązują:
- dopłata paliwowa 9% do stawki bazowej (dotychczas 0%),
- nowa kategoria „paczka ciężka" (powyżej 10 kg): 19,90 zł zamiast 12,00 zł. Takich paczek jest ok. 14% naszego wolumenu u X.

Zakupy rekomendują akceptację. Alternatywnego przewoźnika dla tego wolumenu nie ma przed Q2 2027, a renegocjacje są możliwe dopiero w czerwcu 2027. Koszt zostaje więc na cały okres, który obejmie Twój przegląd po Q1 2027.

**Dlaczego to uderza w decyzję.** Wynik +22 600 zł miesięcznie z notatki z 2026-10-20 wynikał z kosztu paczki 11,80 zł (X: 12,00 zł, 65% paczek; Y: 11,40 zł, 35%) przy ok. 18 000 dodatkowych paczek. Po aneksie, przy tych samych proporcjach:
- standardowa paczka X: 12,00 zł × 1,09 = 13,08 zł,
- ciężka paczka X: 19,90 zł × 1,09 ≈ 21,69 zł,
- średnio X ≈ 14,29 zł (przy 14% ciężkich), a średnia ważona z Y ≈ 13,28 zł zamiast 11,80 zł,
- koszt 18 000 paczek ≈ 239 000 zł zamiast 212 400 zł, czyli ok. +26 600 zł miesięcznie.

Przy niezmienionej marży 235 000 zł wynik spada z +22 600 zł do ok. −4 000 zł miesięcznie. To rachunek przy założeniu, że udział ciężkich paczek wśród dodatkowych jest taki sam jak w całym wolumenie X [założenie]. Dodatkowe paczki przy koszykach 99–149 zł są raczej lżejsze. Jeśli wcale nie ma wśród nich ciężkich, sama dopłata paliwowa daje koszt ok. 12,49 zł za paczkę i wynik ok. +10 000 zł. Realny wynik leży więc w przedziale od mniej więcej −4 000 do +10 000 zł, tylko z samego aneksu.

Nałożone na wcześniejsze korekty (test A/B z tygodnia 2: +5,8% zamiast +6,1% i spadek koszyka −3,4%, oraz ewentualne +0,30 zł za paczkę Y z tygodnia 3) wynik prawdopodobnie schodzi poniżej zera. Nie umiem tego policzyć dokładnie bez danych o strukturze paczek. To zadanie dla kontrolera finansowego.

**Co proponuję.** Decyzję podjęliście razem z kontrolerem i Head of Product, a start jest za kilka dni. Proszę o przeliczenie modelu z nowymi stawkami przed 2026-12-01. Sam wniosek „wynik dodatni, ale niewielki" nie jest już prawdziwy. Do wyboru:
- wystartować zgodnie z planem z wcześniejszym przeglądem (np. po 4–6 tygodniach) i z jasnym kryterium wycofania,
- zmienić kształt oferty, np. wyłączyć z darmowej dostawy paczki ciężkie. To moja propozycja, której nie sprawdzałem pod kątem możliwości w koszyku (sprint 33), więc proszę zapytać Tech Leada,
- wrócić do progu 119 zł, który odrzuciłeś z powodu mniejszego efektu konwersji. Przy nowych kosztach taki kompromis może wyglądać inaczej, ale wymaga danych, których nie mam.

## 2. Zamrożenie wdrożeń 2026-12-20 – 2027-01-04 (wymaga uwagi)

**Co się zmieniło.** Zamrożenie wdrożeń obowiązuje od 2026-12-20 do 2027-01-04, wyjątki tylko za zgodą CTO. Grafik dyżurów to 2026-12-23 – 2027-01-02.

**Dlaczego to Cię dotyczy.** Start progu (2026-12-01) i release panelu (2026-12-10) mieszczą się przed zamrożeniem. Ale okno na poprawki po wdrożeniu panelu to tylko 10 dni. Wszystko, co pojawiło się w poprzednich tygodniach, a wymaga zmian w kodzie, musi wejść przed 2026-12-20, bo potem potrzebujesz zgody CTO:
- informacja o inwentaryzacji magazynu w koszyku i panelu (zamówienia po 2026-12-27 wysyłane 2026-12-31), do wprowadzenia od 2026-12-20,
- ewentualne dostosowanie panelu do Y po migracji na v3 (brak statusu „w doręczeniu", opóźnienia nawet ponad 12 h),
- ewentualna korekta progu po przeliczeniu z punktu 1.

Zamrożenie nie koliduje z wyłączeniem płatności za pobraniem 2027-02-01, ale kod tej zmiany (w tym ewentualna konfiguracja dla Czech) trzeba wdrożyć po 2027-01-04.

## 3. Sprint review Integracji: INT-233 (wymaga uwagi, kontynuacja z tygodnia 3)

**Co się zmieniło.** Mapowanie zdarzeń v3 na statusy OMS jest gotowe, testy na środowisku przedprodukcyjnym trwają, a termin 2026-12-12 jest niezagrożony. W materiałach nie ma wzmianki o planie Premium, więc migracja idzie w planie Standard.

**Dlaczego to ważne.** Mapowanie jest już zamknięte i nic w nim nie wskazuje, że uwzględniono panel statusu. Zakładam, że dla Y panel dostanie tylko „nadane" i „doręczone" z odświeżaniem co ok. 12 h. Nie wiem jednak, czy rozmawiałeś o tym z Integracjami i Tech Leadem po zeszłym tygodniu. Jeśli nie, okno na decyzję (czteroetapowa oś czasu dla Y, Premium, przesunięcie Y) właśnie się zamyka, bo release panelu to 2026-12-10, dwa dni przed migracją, i przed zamrożeniem. Proponuję ustalić to z Tech Leadem Zamówienia w tym tygodniu.

## 4. Do wiadomości

- **Konkurent Z obniżył próg do 79 zł, ale tylko dla dostawy do automatów paczkowych (od 2026-11-20); konkurent V ma abonament 19 zł/mies.** To dokładnie wariant „tylko paczkomaty", który odrzuciłeś z powodu złożoności komunikacji. Jeden ruch konkurenta nie jest dowodem na to, jak zareagowaliby nasi klienci, i nie zmienia Twojej decyzji. Warto jednak mieć to w głowie przy przeglądzie progu, a zwłaszcza jeśli z punktu 1 wyniknie potrzeba zmiany jego kształtu (paczkomaty są też zwykle tańsze w obsłudze, tego w materiałach nie widzę [niezweryfikowane]).

## Pominąłem

Wynik finansowy za październik (koszty logistyki 8,5% przychodów to tło, nie sygnał dla Twoich decyzji), badanie UX „Ulubione", newsletter wewnętrzny oraz pozostałe pozycje sprintu 33 (INT-241, wymiana biblioteki HTTP).
