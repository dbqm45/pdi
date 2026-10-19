# Karta oceny — Q4

## Metadane przebiegu

| Pole | Wartość |
|---|---|
| Wariant i runda | A-R2c |
| Powtórzenie | 1 |
| Narzędzie i model | nieznane (sędzia nie zna wariantu/metody) |
| Data | 2026-10-19 (data oceny) |
| Czas pracy (min) | nieznane |
| Plik z odpowiedzią | `scratchpad/eval/out/A-R2c-1.md` |

Kontekst przebiegu: nowa rozmowa; autor znał tylko dokumenty 09 i 10 oraz zdanie, że trwają prace nad panelem (decyzja sprzed miesiąca). Nie znał materiałów 01–08: uzasadnienia decyzji (07, 01 — przyczyna „brak informacji w interfejsie”), KR 1.1, rekomendacji badacza (02), raportu obsługi (04) ani wymagań (08). Oceniam według klucza, w uwagach zaznaczam, czego nie mógł wiedzieć.

## Runda 2

| ID | Punkty | Cytat |
|---|---|---|
| N1 dokument 09 podważa założenie decyzji (wysoki priorytet) | 2 | „**Panel statusu nie rozwiąże głównej przyczyny zgłoszeń.**” + „Przyczyna leży w integracji z nowym przewoźnikiem, nie w sposobie prezentacji statusu.” + „Zakładam, że uzasadnienie decyzji sprzed miesiąca zawierało takie założenie [niezweryfikowane: nie widziałem tego uzasadnienia]. Warto je zestawić z tymi liczbami”. Dokument 09 jest pierwszym i głównym punktem odpowiedzi, a dokument 10 uznany za neutralny, więc priorytet wysoki. Uwaga: powiązanie z założeniem decyzji jest warunkowe, bo autor nie znał 01/07 — oznaczył to uczciwie jako [niezweryfikowane]; tego nie można było zrobić lepiej bez materiałów. Rekomenduje kontynuację budowy („Nie ma powodu, żeby przerywać budowę panelu”), ale klucz N1 tego nie ocenia. |
| N2 co aktualne / co do ponownej oceny | 2 | Aktualne: „23% zgłoszeń dotyczyło zamówień z aktualnym statusem […] Tu czytelny panel z opisami etapów i datą dostawy może realnie odciążyć obsługę.” Do ponownej oceny: „**Cel i miara sukcesu.** […] ustalić realistyczny cel, np. odciążenie głównie w tych 23%” oraz zakres/kolejność: „Naprawa integracji z przewoźnikiem jako zależność lub równoległy wątek”. Uwaga (ocena graniczna): rozdzielenie nie jest podane jako dwie wprost nazwane listy, a sam wybór rozwiązania nie jest poddany ponownej ocenie (panel ma być budowany dalej, zmieniają się oczekiwania i zakres). Oba elementy są jednak obecne. KR 1.1 nie mógł być wymieniony — autor go nie znał. |
| N3 konkretny następny krok | 2 | „Naprawa integracji z przewoźnikiem jako zależność lub równoległy wątek. Potrzebny jest właściciel, termin i monitoring opóźnień webhooków. Bez tego panel działa na złych danych.” + zawężenie: „Wyjaśnienie statusów i widoczna przewidywana data dostawy”. Uzasadnienie danymi z 09: 61%, „31 godzin dla nowego przewoźnika i 2 godziny dla pozostałych”, tygodnie 19 i 24. Uwaga: naprawa jako „zależność lub równoległy wątek”, nie jednoznacznie „przed lub zamiast pełnego panelu” — mieści się w pełnym wykryciu (konkret + dane). Rekomendacje „data dostawy / opisy statusów” pokrywają się z rekomendacjami badacza z 02, których autor nie znał. |
| N4 brak ostrzeżenia o dokumencie 10 | zal. | „Aktualizacja UX (10) nie zmienia zakresu funkcjonalnego, więc dla inicjatywy jest neutralna.” Odpowiedź ma osobną sekcję o 10 (kilka punktów, więcej niż jednozdaniowa wzmianka), ale bez ostrzeżenia; jedyne powiązanie — „warto sprawdzić, czy skrócenie do 90 znaków nie wycina informacji” — jest drobną, uzasadnioną danymi z 09 sugestią, nie alarmem. |
| **Suma N1–N3 (max 6)** | **6** | |

Fałszywe alarmy rundy 2 (F6 — ostrzeżenie o dokumencie 10): **brak, liczba: 0**. Wzmianka o ręcznej kategoryzacji pojawia się w „Zastrzeżeniach do danych” jako ograniczenie analizy 09 podane przez jej autorów — drobna uwaga, nie liczy się.

Inne zgłoszenia spoza klucza:

| Zgłoszenie | Trafne? | Uwagi |
|---|---|---|
| Znacznik „ostatnia aktualizacja” i komunikat o podejrzanie starym statusie w panelu | trafne | Bezpośrednio adresuje ryzyko W6 (panel eksponuje nieaktualne dane); tani i konkretny środek łagodzący. |
| Brak punktu odniesienia dla 61% (odsetek wszystkich zamówień z nieaktualnym statusem) | trafne | Słuszna uwaga metodyczna — bez bazowej częstości 61% nie mówi o sile związku. |
| Próba obejmuje pierwsze tygodnie nowego przewoźnika; sprawdzić, czy sytuacja zmieniła się od Q2 | trafne | Rozsądne zastrzeżenie, oznaczone [niezweryfikowane]. |
| „Analiza pokazuje związek, nie dowodzi przyczynowości” | trafne | Poprawnie; wskazuje też mocniejsze argumenty (tygodnie awarii, 31 h vs 2 h). |
| Przekazanie wniosku Kierownikowi Obsługi Klienta | trafne (drobne) | Sensowny krok komunikacyjny, nie zmienia decyzji. |
| Sprawdzenie, czy skrócenie opisów do 90 znaków nie wycina informacji potrzebnych dla 23% | trafne (drobne) | Logiczne połączenie 10 z 09, podane bez alarmu. |

## Subiektywnie

- Czy wynik pomógłby PM-owi podjąć lepszą decyzję? **4/5** — jasno rozdziela 61% (integracja) od 23% (panel), daje konkretne kroki. Minus: wniosek końcowy „nie ma powodu przerywać budowy” jest słabszy niż oczekiwane w kluczu „przed lub zamiast pełnego panelu”; brak wezwania do ponownego przeglądu decyzji ze sponsorem.
- Czas przeczytania i weryfikacji: ok. 5–7 min (wszystkie liczby da się sprawdzić w 09; poprawnie zacytowane).
- Najbardziej przydatne: rozbicie 61/23/16 z przełożeniem na to, co panel może, a czego nie może rozwiązać, oraz znacznik świeżości danych. Najmniej: sekcja o dokumencie 10 (poprawna, ale dłuższa niż potrzeba).
