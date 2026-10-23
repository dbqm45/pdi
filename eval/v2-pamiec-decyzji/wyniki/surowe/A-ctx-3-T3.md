## Wymaga Twojej uwagi: 1 rzecz, ale poważna

### INT-233: migracja przewoźnika Y na API v3 podważa założenie, na którym oparto decyzję o panelu statusu

**Co się dzieje.** Przewoźnik Y wygasza API v2 z dniem 2026-12-15. Zespół Integracji planuje migrację na v3 w planie Standard do 2026-12-12. W v3 nie ma webhooków, a zdarzenia pobiera się zapytaniami. Plan Standard pozwala odświeżać je co ok. 12 h, a v3 udostępnia tylko zdarzenia „nadane” i „doręczone” (bez „w doręczeniu” i bez awizacji).

**Dlaczego to uderza w Twoją decyzję.**
- Notatka z 2026-10-27 mówi wprost: panel ma sens, bo dane od przewoźników są teraz aktualne (po naprawie webhooków Y opóźnienie spadło z 31 h do 1,5 h), a bez tego panel pokazywałby nieaktualne informacje, co w sierpniu było główną przyczyną kontaktów. Po migracji opóźnienie dla Y wróci do rzędu 12 h, czyli blisko poziomu, który wtedy powodował problem. Y to ok. 35% paczek.
- Oś czasu w panelu ma pięć statusów, w tym „w doręczeniu”. Dla paczek Y ten status nie będzie dostępny w żadnym planie, bo to ograniczenie v3, a nie planu. Premium przyspieszyłby odświeżanie co 15 min, ale tego zdarzenia nadal nie da.
- Terminy się rozjeżdżają. Release panelu jest 2026-12-10, a przełączenie Y na v3 do 2026-12-12 (v2 działa do 12-15). Panel wystartuje więc z dobrymi danymi, które po kilku dniach się pogorszą. Pierwsze 8 tygodni pomiaru metryki (27% do 20%) przypadnie w całości na okres z danymi z v3. Ostatni odczyt przed zmianą to 26% (tydzień 47, Black Week), więc cel 20% jest już teraz ambitny.
- Przewidywana data dostawy z SLA (Y: D+2) nie zależy od zdarzeń, więc ten element zakresu zostaje. Zagrożone są oś czasu i znacznik „ostatnia aktualizacja”, który przy 12 h często pokaże starą godzinę.

**Czego nie wiem.** Nie wiem, czy Integracje i Tech Lead wiedzą, że ticket zmienia przesłankę decyzji o panelu. Ticket nie wspomina o panelu. Mapowanie zdarzeń v3 na statusy OMS jest „w toku”, więc zakres statusów można jeszcze wpłynąć. [założenie: nikt tego nie połączył]

**Co proponuję (decyzje do podjęcia przed 2026-12-10).**
1. Zdecyduj o zakresie osi czasu dla Y: oś bez „w doręczeniu” tylko dla Y (przyjęte, w kompletacji, nadane, doręczone) albo wspólna oś bez tego statusu dla obu przewoźników, żeby nie było różnic między paczkami. Ustal z UX, jak pokazać opóźnienie danych („ostatnia aktualizacja” już jest w zakresie).
2. Zapytaj Integracje i osobę odpowiedzialną za umowy z przewoźnikami o Premium: +0,30 zł za paczkę Y. Jeśli to wybierzesz, potrzebujesz renegocjacji umowy przed 2026-12-15, a to zostaje niewiele czasu. Pamiętaj, że koszt ten dotknie też darmowej dostawy: na dodatkowych ok. 18 000 paczek miesięcznie to przy 35% udziale Y ok. 1 900 zł miesięcznie, czyli niemało przy wyniku +11–22 tys. zł. [obliczenie własne]
3. Zdecyduj, czy metryka sukcesu (20% w 8 tygodni) zostaje, czy ją zmieniasz, i czy przesuwasz release albo wdrażasz panel etapami. Bez tego ocena panelu po 8 tygodniach nie będzie miarodajna.
4. Poproś o udział w mapowaniu statusów v3 na OMS, bo od niego zależy, co panel może pokazać.

## Pominąłem

Zmiana etykiet przewoźnika X (brak zmian w procesie i cenniku), ankieta pracownicza, koszty infrastruktury, plan treści i tygodnik danych (poza odczytem 26% kontaktów o status, użytym wyżej). Do wiadomości, bez działania: Checkout wdrożył zapisywanie kart dla zalogowanych, co lekko wspiera przejście klientów z płatności za pobraniem na kartę.
