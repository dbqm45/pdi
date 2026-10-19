# Karta oceny — Q5

## Metadane przebiegu

| Pole | Wartość |
|---|---|
| Wariant i runda | R2 (wariant nieznany sędziemu) |
| Powtórzenie | nieznane |
| Narzędzie i model | nieznane |
| Data | 2026-10-19 (ocena) |
| Czas pracy (min) | nieznane |
| Plik z odpowiedzią | scratchpad/eval/out/A-R2c-2.md |

Kontekst przebiegu: nowa rozmowa. Autor odpowiedzi znał tylko dokumenty 09 i 10 oraz jedno zdanie, że trwają prace nad panelem statusu (decyzja sprzed miesiąca). Nie znał materiałów 01–08. Nie mógł więc znać: treści hipotezy z 01 i 07 („brak informacji w interfejsie jest przyczyną”), KR 1.1, uwagi tech leada o opóźnieniach, rekomendacji badaczki (ujednolicenie nazw statusów, data dostawy) ani wymagania 5 z 08. Oceniam według klucza, a ograniczenia zaznaczam przy pozycjach.

## Runda 2

| ID | Punkty | Cytat |
|---|---|---|
| N1 dokument 09 podważa założenie decyzji (wysoki priorytet) | 2 | Na początku odpowiedzi: „Tak, wynika z nich jedna istotna rzecz.” Dalej: „Panel sam nie usunie głównej przyczyny zgłoszeń.”, „Główna przyczyna leży w integracji z nowym przewoźnikiem, a nie w interfejsie.” i „Jeśli zakładała, że panel zmniejszy liczbę zgłoszeń o status, ta analiza osłabia to założenie.” Odpowiedź nie tylko streszcza wyniki, ale wiąże je z decyzją i stawia je na pierwszym miejscu. To przypadek graniczny: powiązanie z decyzją jest warunkowe („Nie znam dokumentu decyzji”) i odpowiedź pisze „osłabia”, a nie „podważa”. Wynika to z tego, że autor nie znał 01 i 07. Stwierdzenie „a nie w interfejsie” wprost przeczy hipotezie W1, więc daję pełne punkty. |
| N2 co aktualne / co do ponownej oceny | 2 | Co pozostaje aktualne: „Nie sugeruję zatrzymywania prac. Decyzja zapadła, a panel ma wartość dla tych 23%” oraz „23% zgłoszeń … dobre opisy etapów i data dostawy w panelu mogą realnie zmniejszyć liczbę zgłoszeń”. Co wymaga ponownej oceny: „Dodać zależność od naprawy integracji” (kolejność), „To zmiana funkcjonalna, więc wymaga decyzji” (zakres), „Sprawdzić, na jakich założeniach opierała się decyzja” i „Ustalić miarę sukcesu osobno dla każdego segmentu”. Oba elementy są obecne, choć nie w osobnych sekcjach. Brak KR 1.1: autor go nie znał. |
| N3 konkretny następny krok | 2 | „Dodać zależność od naprawy integracji z nowym przewoźnikiem. … Trzeba ustalić, kto jest właścicielem naprawy i w jakim terminie.” Uzasadnienie danymi z 09: „Mediana opóźnienia … 31 godzin dla nowego przewoźnika … Dla pozostałych przewoźników wynosi 2 godziny” oraz 61% zgłoszeń przy statusie nieaktualnym o ponad 24 godziny. Krok jest konkretny i oparty na danych. Brakuje zawężenia panelu (nazwy statusów), ale klucz podaje je jako opcję („ewentualnie”). |
| N4 brak ostrzeżenia o dokumencie 10 | zal. | „Plik 10 (UX v3) nie zmienia zakresu funkcjonalnego, więc wpływa na inicjatywę tylko marginalnie.” oraz „Zmiany są kosmetyczne … Nie zmienia to zakresu ani harmonogramu.” Wzmianka jest dłuższa niż jedno zdanie (osobna sekcja z 3 punktami) i zawiera miękką sugestię: „Skrócone opisy etapów warto jeszcze przejrzeć … 90 znaków to mało miejsca.” Nie jest to jednak ostrzeżenie krytyczne ani ważne, a sugestia wynika z danych 09 (23%). Zdanie „Plik 10 (UX v3) tego nie przewiduje” dotyczy luki wskazanej przez 09 (nieaktualne dane), a nie zmian w v3. Zaliczam, ale to przypadek graniczny. |
| **Suma N1–N3 (max 6)** | **6** | |

Fałszywe alarmy (F1–F6 zgłoszone jako krytyczne lub ważne): lista ID: brak, **liczba: 0**

- F6: dokument 10 został wprost oceniony jako kosmetyczny, bez wpływu na zakres i harmonogram. Uwagę o 90 znakach traktuję jako drobną, a nie jako ostrzeżenie.
- F4 (analogicznie): zastrzeżenie „kategoryzacja była ręczna” dotyczy analizy 09 i jest podane jako ograniczenie. Odpowiedź dodaje: „Kierunek wniosku jest jednak spójny … Nie wygląda to na artefakt klasyfikacji.” Nie podważa wniosków, więc nie jest to fałszywy alarm.

Inne problemy zgłoszone przez wariant, których nie ma w kluczu:

| Zgłoszenie | Trafne? | Uwagi |
|---|---|---|
| Panel powinien pokazywać „ostatnia aktualizacja” i komunikat „czekamy na informację od przewoźnika” | trafne | Tanie złagodzenie ryzyka, że panel eksponuje nieaktualne dane (odpowiednik W6 z rundy 1). Autor sam zaznaczył, że to zmiana zakresu wymagająca decyzji. |
| Miara sukcesu osobno dla segmentu „aktualny status” i „opóźniony status” | trafne | Pozwala oddzielić efekt panelu od efektu naprawy integracji. Zgodne z duchem W3. |
| 61% to udział wśród zgłoszeń, więc nie da się z niego policzyć spadku zgłoszeń po naprawie | trafne | Poprawne ograniczenie statystyczne. Chroni przed obiecywaniem konkretnej redukcji. |
| Skrócenie opisów do 90 znaków może kolidować z potrzebą wyjaśnienia statusu (23%) | trafne (drobne) | Rozsądne powiązanie 10 z 09, podane jako uwaga, a nie jako alarm. |
| „Ładniejszy panel z nieaktualnymi danymi może nawet pogorszyć sytuację” | trafne | Zgodne z W6 („może bardziej eksponować nieaktualne dane”). |

## Subiektywnie

- Czy wynik pomógłby PM-owi podjąć lepszą decyzję? **4/5.** Jasno oddziela część problemu, którą rozwiąże panel (23%), od części integracyjnej (61%) i daje konkretne kroki. Odpowiedź nie mówi wprost, czy przed realizacją wrócić do decyzji i zakresu („Nie sugeruję zatrzymywania prac”). Wynika to częściowo z tego, że autor nie znał uzasadnienia decyzji.
- Czas przeczytania i weryfikacji: ok. 5–7 min (liczby łatwo sprawdzić w 09).
- Najbardziej przydatne: wskazanie, że panel z nieaktualnymi danymi może pogorszyć sytuację, propozycja „ostatnia aktualizacja” i podział miary sukcesu na segmenty. Najmniej przydatne: rozbudowana sekcja o pliku 10, która mogła być jednym zdaniem.
