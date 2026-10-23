W tym tygodniu wymaga Twojej uwagi jedna rzecz, która podważa założenie jednej z Twoich decyzji: ticket INT-233. Dwie drobne rzeczy są do wiadomości. Pozostałe materiały pomijam.

## 1. INT-233: migracja przewoźnika Y na API v3 (wymaga pilnej uwagi)

**Co się zmieniło.** Przewoźnik Y wygasza API v2 z dniem 2026-12-15. Integracje planują migrację na v3 w planie Standard do 2026-12-12. W v3:
- nie ma webhooków, zdarzenia pobieramy pollingiem,
- plan Standard pozwala odświeżać zdarzenia co ok. 12 h. Plan Premium (co 15 min) wymaga renegocjacji umowy i kosztowałby ok. +0,30 zł za paczkę,
- dostępne są tylko zdarzenia „nadane" i „doręczone" (bez „w doręczeniu" i bez awizacji).

**Dlaczego to uderza w decyzję o panelu statusu.** Uzasadnienie z 2026-10-27 brzmi: „Panel ma sens, bo dane o zdarzeniach od przewoźników są teraz aktualne". Opierało się na poprawionych webhookach Y (mediana opóźnienia 1,5 h, wcześniej 31 h). Przewoźnik Y to ok. 35% naszych paczek. Dla nich:
- Opóźnienie zdarzeń wzrośnie z mediany 1,5 h do rzędu godzin (odświeżanie co 12 h, więc średnio ok. 6 h, a w najgorszym razie ponad 12 h). To nadal lepiej niż 31 h z sierpnia, ale to inny poziom jakości niż ten, na którym oparłeś decyzję [szacunek z założenia równomiernego rozkładu, nie pomiar].
- Oś czasu w panelu ma pięć statusów, a dla Y w v3 zostają „nadane" i „doręczone". Status „w doręczeniu" nie będzie dostępny. Klient Y zobaczy „nadane" aż do doręczenia, a potem do ok. 12 h opóźnienia „doręczone". To może generować kontakty o status wcześniej, niż wskazuje na to Twoja metryka.
- Terminy się rozjeżdżają: release panelu jest 2026-12-10, a migracja na v3 do 2026-12-12 i wygaszenie v2 15 grudnia. Panel wystartuje na dobrych danych i po dwóch–pięciu dniach pogorszy się dla Y. Metryka rezultatu (z 27% do 20% w 8 tygodni po wdrożeniu) będzie mierzona już na gorszych danych. Bieżący udział kontaktów o status to 26% (tygodnik, tydzień 47).
- Zaletą jest znacznik „ostatnia aktualizacja", który jest w zakresie panelu i uczciwie pokaże świeżość danych. Przewidywana data dostawy z SLA (Y: D+2) nie zależy od zdarzeń, więc ta część panelu zostaje bez zmian.

**Co to znaczy dla Ciebie.** Nikt z tego ticketu nie wyciąga wniosków dla panelu. Zespół Integracje ma kryteria akceptacji dotyczące tylko zapisu zdarzeń w OMS, więc to Ty musisz zapytać, czy decyzja jest nadal aktualna. Mapowanie zdarzeń v3 na statusy OMS jest „w toku", więc jeszcze da się na nie wpłynąć. Proponuję rozmowę z Tech Leadem Zamówienia i Integracjami przed 2026-12-10. Do rozważenia:
- **A. Panel z osłabionym Y.** Dla Y pokazujesz cztery statusy zamiast pięciu i wyraźny „ostatnia aktualizacja". Dostosuj też cel metryki (20% może być nierealne).
- **B. Premium dla Y.** Przywraca odświeżanie co 15 min, ale kosztuje ok. 0,30 zł za paczkę Y (patrz niżej). Wymaga renegocjacji umowy, a termin 2026-12-15 jest bardzo bliski. Nie wiem, czy jest realny w tym czasie.
- **C. Przesunięcie lub wydzielenie Y.** Release panelu dla X najpierw, dla Y po rozwiązaniu problemu z danymi.

Nie rekomenduję jednej opcji bez danych od Integracji i o koszcie dla Y, ale A wymaga najmniej negocjacji.

**Wpływ na darmową dostawę.** Jeśli wybierzesz Premium, koszt 0,30 zł dotyczy wszystkich paczek Y, a nie tylko dodatkowych. Szacunek z notatki (22 600 zł miesięcznie) liczył średni koszt paczki 11,80 zł z Y po 11,40 zł. Nie znam miesięcznej liczby paczek Y, więc nie wyliczę kosztu. Dla skali: przy ok. 75 000 paczek Y miesięcznie (22 600 zł / 0,30 zł) sam Premium zjadłby cały wynik tej inicjatywy. To grubo uproszczone porównanie, ale pokazuje, że koszt trzeba sprawdzić, zanim zdecydujesz. Ten koszt nałoży się na korektę z poprzedniego tygodnia (test A/B: niższy efekt konwersji i spadek koszyka −3,4%).

## 2. Do wiadomości

- **Tygodnik danych, tydzień 47.** Udział kontaktów o status spadł do 26% (−1 pp). To dobry punkt odniesienia dla metryki panelu, ale na razie nic z niego nie wynika. Średnia wartość koszyka spadła o 4,8%, ale w tygodniu Black Week, więc nie czytam tego jako sygnału dla progu darmowej dostawy, który jeszcze nie działa.
- **Sprint 32 Checkout: zapis danych karty dla zalogowanych (tokenizacja).** To lekko wspiera założenie, że część klientów za pobraniem przejdzie na kartę. Dotyczy tylko zalogowanych, więc nie zmienia szacunku utraty zamówień.

## Pominąłem

Zmianę etykiet przewoźnika X (brak zmian w procesie nadawania i w cenniku), ankietę pracowniczą, koszty infrastruktury, plan treści oraz resztę notatki ze sprintu 32. Nie zmieniają one założeń Twoich decyzji.
