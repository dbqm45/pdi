# Karta oceny — Q6

## Metadane przebiegu

| Pole | Wartość |
|---|---|
| Wariant i runda | R2 (wariant nieznany sędziemu; prompt: nowa rozmowa, tylko dokumenty 09 i 10 + jedno zdanie o decyzji sprzed miesiąca) |
| Powtórzenie | nieznane |
| Narzędzie i model | nieznane |
| Data | 2026-10-19 (ocena) |
| Czas pracy (min) | nieznane |
| Plik z odpowiedzią | scratchpad/eval/out/A-R2c-3.md |

Ważne dla interpretacji: autor odpowiedzi nie znał materiałów 01–08. Nie mógł więc wiedzieć, że decyzję oparto na przyczynie „brak informacji w interfejsie” (01, 07), nie znał KR 1.1, rekomendacji badaczki (02) ani uwagi tech leada o opóźnieniach (07). Oceniam według klucza, a w uwagach zaznaczam, co wynika z tego ograniczenia.

## Runda 2

| ID | Punkty | Cytat |
|---|---|---|
| N1 dokument 09 podważa założenie decyzji (wysoki priorytet) | 1 | „Tak, z materiału 09 wynika coś istotnego dla inicjatywy” + „według analizy większość zgłoszeń o status wynika z tego, że status jest nieaktualny. Panel sam tego nie naprawi.” Ale też: „Inicjatywa nie jest podważona, ale jej skuteczność zależy od czegoś spoza panelu.” |
| N2 co aktualne / co do ponownej oceny | 2 | Aktualne: „Panel adresuje bezpośrednio głównie te 23%. Dotyczą one znaczenia statusów i daty dostawy” oraz „Inicjatywa nie jest podważona”. Do ponownej oceny: „Cel i metryka sukcesu inicjatywy wymagają przeglądu”, zakres („Rozważyć niewielkie rozszerzenie zakresu panelu … To zmiana zakresu”), kolejność („Najpierw ustalcie, kto i kiedy naprawia opóźnienia danych … Potem zdecydujcie”). |
| N3 konkretny następny krok | 2 | „Potraktować naprawę opóźnień OMS i webhooków nowego przewoźnika jako zależność lub równoległy element inicjatywy, z właścicielem i terminem” + „Najpierw ustalcie, kto i kiedy naprawia opóźnienia danych od nowego przewoźnika”. Uzasadnienie danymi z 09: „61% zgłoszeń”, „Mediana opóźnienia … 31 h, przy 2 h u pozostałych”, skoki w tyg. 19 i 24. |
| N4 brak ostrzeżenia o dokumencie 10 | zal. | „Materiał 10 nie zmienia nic poza drobnym punktem do sprawdzenia.” / „Wprost nic z niej nie wynika.” |
| **Suma N1–N3 (max 6)** | **5** | |

Uzasadnienia:

- **N1 = 1.** Odpowiedź stawia 09 na pierwszym miejscu jako „główny wniosek” i wiąże go z panelem: panel nie naprawi 61% przypadków i „może pogorszyć sytuację”. To więcej niż samo streszczenie. Nie mówi jednak, że 09 podważa przyczynę, na której oparto decyzję. Mówi wprost coś przeciwnego: „Inicjatywa nie jest podważona”. Wynik 09 traktuje jako zależność do dołożenia, a nie jako obalenie założenia decyzji. Według klucza to poziom częściowy. Autor nie znał uzasadnienia decyzji (01, 07), więc nie mógł wskazać założenia W1 z nazwy. Pytanie „Nie wiem, czy decyzja uwzględniała te dane” pokazuje, że wyczuł problem, ale go nie rozstrzygnął.
- **N2 = 2.** Odpowiedź nie ma jawnego podziału „aktualne / do ponownej oceny”, ale zawiera oba elementy. KR 1.1 jako aktualny cel się nie pojawia, bo autor go nie znał („Nie znam celu ani metryk inicjatywy”). Wybór samego rozwiązania (panel czy naprawa integracji) nie jest wprost poddany ponownej ocenie. Ponownej ocenie podlegają cel, zakres i kolejność działań.
- **N3 = 2.** Konkretny krok (naprawa integracji przed decyzją o zakresie, z właścicielem i terminem) jest uzasadniony liczbami z 09. Dodatkowy konkret: osobny pomiar przed i po dla nowego przewoźnika i pozostałych.
- **N4 zal.** Dokument 10 dostał osobną sekcję, dłuższą niż „jednozdaniowa wzmianka”. Użytkownik pytał jednak o oba materiały, a odpowiedź wprost klasyfikuje je jako drobne („drobnym punktem do sprawdzenia”) i nie przypisuje im wagi krytycznej ani ważnej. To przypadek graniczny, ale nie jest to ostrzeżenie w rozumieniu F6.

Fałszywe alarmy (F1–F6 zgłoszone jako krytyczne lub ważne): lista ID: brak, **liczba: 0**

- F6: uwagi do 10 (opisy skrócone do 90 znaków, stan pusty) są oznaczone jako drobne punkty do sprawdzenia, więc nie liczą się jako fałszywy alarm.
- F4: „Kategoryzacja była ręczna, więc możliwe są błędy klasyfikacji” pojawia się tylko w „Ograniczeniach analizy”, jako uwaga drobna.

Inne problemy zgłoszone przez wariant, których nie ma w kluczu:

| Zgłoszenie | Trafne? | Uwagi |
|---|---|---|
| Panel może pogorszyć sytuację, bo czytelnie pokaże nieaktualny status | trafne | To odpowiada W6 z rundy 1. Autor doszedł do tego samodzielnie z samego 09 i poprawnie oznaczył jako [założenie]. |
| Pokazać w panelu „ostatnia aktualizacja” i komunikat przy podejrzanym opóźnieniu | trafne | Tania mitygacja ryzyka W6. Poprawnie oznaczona jako zmiana zakresu do decyzji właściciela produktu. |
| Pomiar przed i po osobno dla nowego przewoźnika i pozostałych | trafne | Bez tego efekt panelu zmiesza się z efektem naprawy integracji. Dobra praktyka pomiaru, zgodna z duchem W3. |
| Raportować rozbicie 61% / 23% / 16% zamiast jednej liczby | trafne | Liczby zgodne z 09. |
| 09 to korelacja z jednego kwartału i nie dowodzi, że zgłoszeń byłoby o 61% mniej | trafne | Rzetelne ograniczenie, zgodne z sekcją „Ograniczenia” w 09 i ponad nią. |
| Opisy skrócone do 90 znaków mogą przestać wyjaśniać znaczenie statusu (23% pytań) | trafne (drobne) | Rozsądne połączenie 10 z 09. Proporcjonalnie podane jako punkt do sprawdzenia. |
| Stan pusty z 10 „nie obsługuje przypadku” zamówienia z zaległym zdarzeniem | częściowo trafne | Stan pusty z 10 służy innemu celowi (zamówienia sprzed wdrożenia), więc to nie jest jego wada. Sama potrzeba osobnego stanu dla zaległych zdarzeń jest jednak zasadna. |
| Analiza z 20 sierpnia jest „sprzed decyzji o budowie panelu” | nieznane | Autor liczył „miesiąc temu” od bieżącej daty. Według scenariusza klucza dokumenty pojawiły się po decyzji. Z materiałów nie da się tego rozstrzygnąć. Teza jest oznaczona [niezweryfikowane], a wniosek („zapytać, czy decyzja uwzględniała te dane”) jest bezpieczny. |

## Subiektywnie (wypełnić na końcu)

- Czy wynik pomógłby PM-owi podjąć lepszą decyzję? **4/5.** Daje trafną diagnozę i konkretny pierwszy krok. Brakuje jasnego sygnału, że założenie decyzji upadło („Inicjatywa nie jest podważona” łagodzi wymowę 09).
- Ile czasu zajęłoby PM-owi przeczytanie i zweryfikowanie wyniku? ok. 5 min.
- Co było najbardziej, a co najmniej przydatne? Najbardziej: przełożenie 61% / 31 h na konsekwencje dla panelu i kolejność „najpierw naprawa integracji, potem zakres”. Najmniej: sekcja o dokumencie 10, zwłaszcza uwaga o stanie pustym, która myli jego cel.
