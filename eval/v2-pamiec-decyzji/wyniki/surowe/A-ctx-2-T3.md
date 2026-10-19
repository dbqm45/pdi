W tym tygodniu jedna sprawa jest pilna i dotyczy podstaw decyzji o panelu statusu. Jest też jedna drobniejsza uwaga o danych.

## 1. INT-233: migracja przewoźnika Y na API v3 podważa założenie, na którym oparłeś panel statusu (06-INT-233-api-przewoznika-y.md)

**Co się stało.** Przewoźnik Y wygasza API v2 z dniem 2026-12-15. W API v3:
- nie ma webhooków, zdarzenia pobiera się zapytaniami (polling),
- w planie Standard zdarzenia odświeżają się co ok. 12 h, a plan Premium (co 15 min) wymaga renegocjacji umowy i kosztuje ok. +0,30 zł za paczkę,
- dostępne są tylko zdarzenia „nadane” i „doręczone”, bez „w doręczeniu” i bez awizacji.

Zespół Integracji planuje migrację na v3 w planie Standard do 2026-12-12 i dopiero pracuje nad mapowaniem zdarzeń. Kryteria akceptacji obejmują tylko „nadane” i „doręczone”.

**Dlaczego to ważne dla Twojej decyzji.** W notatce z 2026-10-27 napisałeś, że panel ma sens, bo dane o zdarzeniach od przewoźników są teraz aktualne, a bez tego panel pokazywałby nieaktualne informacje, co w sierpniu było główną przyczyną kontaktów. Ta przesłanka przestaje być prawdziwa dla przewoźnika Y, czyli ok. 35% paczek.
- Opóźnienie zdarzeń wróci z 1,5 h do ok. 12 h. To bliżej sierpnia (mediana 31 h) niż obecnego stanu.
- Oś czasu w zakresie panelu ma etap „w doręczeniu”. Dla przesyłek Y ten etap nie będzie miał danych, więc oś będzie przeskakiwać z „nadane” na „doręczone”.
- Kolejność dat jest niekorzystna. Panel wychodzi 2026-12-10, migracja Y kończy się 2026-12-12, a v2 wygasa 2026-12-15. Panel zadebiutuje na starych, dobrych danych, a po kilku dniach pogorszy się dla ok. 35% zamówień. Początek 8-tygodniowego okna pomiaru metryki zbiegnie się więc z pogorszeniem.
- Metryka rezultatu (27% do 20% kontaktów o status) jest zagrożona. Dla przesyłek Y panel będzie pokazywał dane starsze niż to, z czym podejmowałeś decyzję. Nie umiem oszacować, o ile to zmieni wynik, ale kierunek jest jasny [założenie: nie mam danych o rozkładzie kontaktów między przewoźników].

**Koszt opcji z planem Premium.** Dodatkowe +0,30 zł za paczkę Y podniosłoby też koszt paczki w szacunku dla progu 99 zł. Dla Y z 11,40 zł do 11,70 zł średni koszt paczki rośnie z ok. 11,80 zł do ok. 11,90 zł. Przy 18 000 dodatkowych paczek to ok. +1 700 zł miesięcznie, czyli niewiele, ale wynik tej inicjatywy jest już niski (ok. +11 000 zł według moich przeliczeń z zeszłego tygodnia). Pełny koszt Premium zależy od całkowitej liczby paczek Y, której w materiałach nie mam [niezweryfikowane].

**Co proponuję.** Zwołaj w tym tygodniu Tech Leada, UX, zespół Integracji i Head of Product, bo do 10 grudnia zostało niewiele czasu. Opcje do rozważenia:
1. Zawęzić panel dla Y: bez etapu „w doręczeniu”, z wyraźnym znacznikiem „ostatnia aktualizacja” (który już jest w zakresie) i z szerszym zakresem przewidywanej daty dostawy. Najtańsze i najszybsze.
2. Zapłacić za plan Premium dla Y (+0,30 zł za paczkę). Przywraca jakość danych, ale wymaga renegocjacji umowy, która może nie zdążyć przed 2026-12-15.
3. Przesunąć release panelu do czasu rozstrzygnięcia integracji.
4. Zmienić cel metryki (20%) albo mierzyć ją osobno dla X i Y.

Nie rozstrzygam, która opcja jest najlepsza. To zależy od kosztu i terminów po stronie Integracji, których nie znam. Warto też poprosić Integracje o dopisanie do INT-233 wprost wpływu na panel, bo teraz ticket go nie wymienia.

## 2. Tygodnik danych: nowy punkt odniesienia dla metryki panelu

Udział kontaktów o status zamówienia wynosi 26% (−1 pp t/t). To jest Twoja metryka rezultatu, a punkt startowy w notatce to 27%. Jeśli pomiar ma być uczciwy, warto zapisać aktualną wartość bazową. Nie wymaga to teraz działania, ale w świetle pkt 1 baza może się zmienić przed wdrożeniem panelu. Nie wyciągałbym wniosków z tego tygodnia, bo Black Week zaburza większość metryk (sesje +6,3%, średnia wartość koszyka −4,8%). Dotyczy to też spadku koszyka, który obserwowałeś w teście progu 99 zł, więc nie mieszaj ich.

## Pominąłem

Notatkę ze sprintu 32 (Checkout), ankietę pracowniczą, zmianę etykiet przewoźnika X (bez wpływu na proces i cennik), koszty infrastruktury i plan treści. Nie wpływają na Twoje trzy inicjatywy.
