W tym tygodniu uwagi wymagają trzy rzeczy. Pierwsza jest najważniejsza: wraz z wynikami testu z tygodnia 2 może przesunąć wynik progu 99 zł na zero lub poniżej.

## 1. Aneks nr 4 do umowy z przewoźnikiem X podnosi koszt paczki w Twoim szacunku dla progu 99 zł (03-aneks-umowy-przewoznik-x.md)

**Co się stało.** Od 2026-12-01, czyli w dniu startu progu 99 zł, u przewoźnika X obowiązuje dopłata paliwowa 9% do stawki bazowej (dotąd 0%) oraz nowa stawka 19,90 zł za paczki powyżej 10 kg (dotąd 12,00 zł). Takich paczek jest ok. 14% wolumenu X. Zakupy rekomendują akceptację. Alternatywnego przewoźnika nie będzie przed Q2 2027, a renegocjacje są możliwe w czerwcu 2027.

**Dlaczego to ważne dla Twojej decyzji.** Wynik z notatki (ok. +22 600 zł miesięcznie) opiera się na średnim koszcie paczki 11,80 zł, z X po 12,00 zł (65% paczek) i Y po 11,40 zł (35%). Koszt X jest teraz inny. Moje przeliczenie [założenie: stawka 12,00 zł to stawka bazowa paczki standardowej, a dopłata 9% dotyczy wszystkich paczek X, także ciężkich]:
- Średni koszt paczki X: 0,86 × 12,00 + 0,14 × 19,90 = 13,11 zł, po dopłacie 9% ok. 14,29 zł (+19%).
- Średni koszt paczki łącznie: 0,65 × 14,29 + 0,35 × 11,40 = ok. 13,28 zł (zamiast 11,80 zł).
- Koszt 18 000 dodatkowych paczek: ok. 239 000 zł miesięcznie (zamiast 212 400 zł). Przy marży z notatki (235 000 zł) wynik to ok. **−4 000 zł miesięcznie**. Przy marży przeliczonej na efekt z testu krajowego (+5,8%, ok. 223 000 zł) wynik to ok. **−15 500 zł miesięcznie**.
- Zastrzeżenie: dodatkowe paczki pochodzą z koszyków 99–149 zł i mogą być lżejsze niż średnia, więc udział paczek ciężkich może być niższy niż 14%. Gdyby w ogóle nie było tych paczek (tylko dopłata 9%), koszt wynosi ok. 224 900 zł, a wynik ok. +10 000 zł (marża z notatki) lub ok. −1 400 zł (marża z testu). Nie mam danych o wadze dodatkowych paczek [niezweryfikowane].

Wniosek: po obu zmianach (wynik testu krajowego z tygodnia 2 i aneks X) wynik inicjatywy mieści się mniej więcej między −16 000 a +10 000 zł miesięcznie, a nie w obiecywanych +22 600 zł. Zatwierdzono ją jako „dodatnią, ale niewielką”, więc ten zapas zniknął. Dochodzi do tego to, co pisałem tydzień temu o koszcie Premium u Y (+0,30 zł za paczkę, jeśli zdecydujesz się na ten plan) i o spadku średniej wartości koszyka (−3,4%), którego szacunek nie uwzględniał.

**Co proponuję.** Poproś kontrolera finansowego o jedno ponowne przeliczenie, które uwzględni naraz: efekt +5,8% z przedziałem ufności, nowe stawki X (z rzeczywistym udziałem paczek ciężkich w koszykach 99–149 zł), spadek wartości koszyka i ewentualnie Premium u Y. Zrób to przed 2026-12-01, bo wtedy start jest jeszcze tani do zmiany. Do rozważenia z Head of Product i kontrolerem: przesunięcie startu, próg 119 zł (odrzucony wcześniej z powodu słabszego efektu, ale przy wyższym koszcie paczki może wypaść inaczej) albo kryterium wycofania przed przeglądem po Q1.

## 2. Zamrożenie wdrożeń 20.12–04.01 zawęża czas na poprawki panelu (02-swieta-dyzury.md)

**Co się stało.** Zamrożenie wdrożeń trwa od 2026-12-20 do 2027-01-04, wyjątki tylko za zgodą CTO. Panel wychodzi 2026-12-10, więc mieści się w terminie, ale zostaje 10 dni na poprawki.

**Dlaczego to ważne dla Twojej decyzji.** Z poprzednich tygodni masz dwie rzeczy, które mogą wymagać zmian w panelu, a jedna z nich ma termin w środku zamrożenia:
- Inwentaryzacja magazynu: zamówienia złożone po 2026-12-27 są wysyłane dopiero 2026-12-31, a panel liczy datę dostawy z SLA przewoźnika. Wyjątek magazynowy musi więc trafić na produkcję przed 20.12 albo potrzebna jest zgoda CTO.
- Migracja przewoźnika Y na API v3 (INT-233): dane Y pogorszą się po 2026-12-15, czyli już przy zamrożeniu. Ewentualne zmiany panelu (usunięcie etapu „w doręczeniu” dla Y, zmiana komunikatu) trzeba zrobić przed 20.12.

Zamrożenie dotyczy też ewentualnej zmiany progu 99 zł, jeśli po przeliczeniu z pkt 1 zdecydujesz się go wycofać lub zmienić po starcie. W praktyce decyzje o tych zmianach trzeba podjąć w ciągu około dwóch tygodni.

## 3. INT-233: termin jest niezagrożony, ale nic nie wskazuje, że wpływ na panel został rozwiązany (06-sprint-review-integracje.md)

**Co się stało.** Zespół Integracji potwierdza, że mapowanie zdarzeń jest gotowe, testy trwają, a termin 2026-12-12 jest niezagrożony.

**Dlaczego to ważne dla Twojej decyzji.** Tydzień temu zgłosiłem, że v3 daje zdarzenia tylko „nadane” i „doręczone”, a odświeżanie co ok. 12 h w planie Standard. Przegląd sprintu nie wspomina o panelu ani o planie Premium, więc migracja idzie według pierwotnego planu (Standard), a przesłanka panelu (aktualne dane Y) przestaje działać po 2026-12-15. Nie wiem, czy rozmowa z Tech Leadem, UX i Head of Product już się odbyła [niezweryfikowane]. Jeśli nie, termin 10 grudnia jest coraz bliżej, a opcje (węższy zakres dla Y, Premium, przesunięcie release'u) wymagają kilku dni.

## 4. Konkurencja: kontekst, bez pilnej akcji (01-konkurent-prog-dostawy.md)

Konkurent Z obniżył próg do 79 zł od 2026-11-20, ale tylko dla dostawy do automatów paczkowych. Jest to zbliżone do wariantu, który odrzuciłeś (darmowa dostawa tylko do paczkomatów, ze względu na złożoność komunikacji). Test A/B zakończył się przed tą zmianą (wyniki z 2026-11-13), więc nie wiem, czy efekt progu 99 zł pozostanie taki sam [niezweryfikowane]. Nie traktowałbym tego jako argumentu za obniżeniem progu, bo ekonomika jest już cienka (pkt 1). Gdyby dane z przeliczenia kazały zmienić wariant, warto wtedy sprawdzić, jak wypada wersja paczkomatowa. Pozostali konkurenci (V z abonamentem, W bez zmian) nie zmieniają decyzji.

## Pominąłem

Badanie użyteczności ekranu „Ulubione”, newsletter wewnętrzny, wynik finansowy za październik (marża i koszty logistyki są zbyt ogólne, by dotyczyć Twoich decyzji; koszty X policzyłem z aneksu), INT-241 i dług techniczny z przeglądu sprintu 33.
