Z tych materiałów jedna rzecz wymaga Twojej decyzji teraz, jedna jest ważnym kontekstem do inicjatywy (1), a dwie to drobne uwagi do sprawdzenia.

## 1. Wymaga działania: INT-233 (API przewoźnika Y v3) i panel statusu zamówienia (inicjatywa 2)

Zadanie jest techniczne i nie wspomina o panelu. Ma jednak bezpośredni wpływ na to, co panel może pokazać.

- Po migracji na API v3 dostajemy tylko zdarzenia „nadane" i „doręczone". Znikają „w doręczeniu" i awizacja.
- Przy planie Standard zdarzenia odświeżają się co ok. 12 h. Brak webhooków, więc pobieramy je pollingiem.
- Wpływ na panel: dla paczek Y panel nie pokaże „w doręczeniu" ani awizacji. Status „nadane" może być nieaktualny nawet o pół doby.
- Taki panel prawdopodobnie nie ograniczy kontaktów „gdzie jest moja paczka". Kupujący zobaczy „nadane" przez cały dzień doręczenia.
- Terminy się nakładają. Panel wychodzi 2026-12-10, migracja na v3 jest planowana do 2026-12-12, a v2 wygasa 2026-12-15. Panel wystartuje na v2, a po dwóch dniach dane zubożeją.
- Mapowanie zdarzeń v3 na statusy OMS jest „w toku". Nikt nie wie, że panel od niego zależy.

Co zrobić:
1. Wejdź w mapowanie statusów w INT-233 i potwierdź z Integracjami, jakie statusy panel obiecuje dla paczek Y. Nie wiem, co dokładnie obejmuje „zawężony zakres" panelu, więc to sprawdź. [założenie: panel zakłada co najmniej status „w doręczeniu"]
2. Zdecyduj, którą z dwóch ścieżek wybierasz.
   - **Standard:** panel dla Y ma dwa statusy i uczciwy komunikat o czasie odświeżania. Opis zakresu i kryteria sukcesu (spadek kontaktów) trzeba wtedy skorygować.
   - **Premium:** odświeżanie co 15 min kosztuje ok. +0,30 zł za paczkę i wymaga renegocjacji umowy. Zdarzenia „w doręczeniu" i awizacja nadal nie wrócą, bo to ograniczenie v3. Premium rozwiązuje więc tylko opóźnienie.
3. Policz koszt Premium. Potrzebny jest wolumen paczek Y, a tego w materiałach nie ma. [niezweryfikowane]
4. Sprawdź, czy panel w ogóle ma wejść na paczki Y 2026-12-10. Alternatywa to wyłączenie ich z zakresu do czasu rozstrzygnięcia.

## 2. Kontekst dla progu darmowej dostawy (inicjatywa 1): tygodnik danych, tydzień 47

- Średnia wartość koszyka to 158 zł (−4,8% t/t). To tylko 9 zł powyżej obecnego progu 149 zł i 59 zł powyżej nowego progu 99 zł.
- Koszt obniżki zależy od udziału zamówień w przedziale 99–149 zł. Dla nich dostawa stanie się darmowa. Tego rozkładu w tygodniku nie ma, więc warto go zamówić u analityków przed 2026-12-01.
- Spadek koszyka wypada w Black Week. Prawdopodobnie to efekt promocji, ale tego nie sprawdziłem [założenie]. Nie traktuj więc 158 zł ani konwersji 2,58% jako czystej bazy do oceny progu. Potrzebna jest baza spoza okresu promocji.
- Do inicjatywy 2 przyda się wskaźnik „udział kontaktów o status zamówienia" = 26% (−1 pp). To naturalna wartość odniesienia dla panelu. Warto ją zapisać jako stan wyjściowy.
- Wolumen paczek rośnie po obniżce progu, a to pogłębia punkt 1. Jeśli wybierzesz Premium, +0,30 zł za paczkę dotyczy większej liczby paczek.

## 3. Do sprawdzenia, niski priorytet

- **Sprint 32, zapisywanie danych karty (tokenizacja):** wdrożone tylko dla zalogowanych. Po wycofaniu płatności za pobraniem (2027-02-01) część klientów przejdzie na płatność kartą. Zapisana karta to ułatwia, ale nie obejmuje gości. Warto sprawdzić, jaką część klientów COD stanowią goście.
- **Sprint 32, kody rabatowe łączone (Q1):** ustal z Checkout, czy próg darmowej dostawy liczy się od wartości przed rabatem, czy po nim. Przy łączonych kodach koszyk łatwiej spadnie poniżej 99 zł.

Pozostałe materiały (etykiety przewoźnika X, ankieta pracownicza, koszty infrastruktury, plan treści) nie wpływają na Twoje inicjatywy.
