# 5. Attention Intelligence — kiedy system się odzywa

System chroni uwagę ludzi równie świadomie, jak jakość decyzji. Narzędzie generujące szum pogorszy proces, nawet jeśli każde jego ostrzeżenie jest formalnie poprawne.

## 5.1. Cztery pytania filtrujące

Każde wykryte ryzyko lub sygnał przechodzi przez:

1. **Czy to rzeczywisty problem?** (oś `credibility`) — wystarczające dowody, czy tylko potencjalna rozbieżność?
2. **Czy ma znaczenie?** (oś `decision_impact` × `stakes`) — czy może zmienić decyzję, zakres, rezultat, koszt?
3. **Czy trzeba działać teraz?** (oś `urgency`) — czy blokuje aktualny krok?
4. **Czy człowiek musi interweniować?** — czy system może sam uzupełnić kontekst, sprawdzić źródła, odświeżyć analizę?

Jeśli odpowiedź na pytanie 4 brzmi „nie” — system działa sam i nie powiadamia.

## 5.2. Poziomy reakcji

| Poziom | Zachowanie | Kanał | Przykład |
|---|---|---|---|
| **0. Informacja** | Aktualizacja modelu bez powiadomienia | brak | Nowy dokument niezmieniający ustaleń |
| **1. Obserwacja** | Pokazana przy najbliższej okazji (gdy użytkownik otworzy inicjatywę) | w kontekście | Alternatywna interpretacja, która nie blokuje pracy |
| **2. Rekomendacja** | Konkretna proponowana czynność | zbiorczy digest | Brak danych do oceny, czy rozwiązanie odpowiada na problem |
| **3. Istotne ostrzeżenie** | Aktywne zwrócenie uwagi właściciela decyzji | powiadomienie | Nowe dowody podważają założenie nośne zatwierdzonej decyzji |

## 5.3. Reguły antyszumowe

- **Agregacja** — powiązane sygnały dotyczące tego samego założenia łączone w jeden komunikat.
- **Deduplikacja** — raz odrzucone ostrzeżenie (z uzasadnieniem) nie wraca, chyba że pojawi się nowy dowód.
- **Budżet uwagi** — limit komunikatów poziomu 2–3 na osobę/tydzień; po przekroczeniu system priorytetyzuje i resztę odkłada do digestu.
- **Kierowanie** — komunikat trafia do właściciela decyzji/luki, nie do wszystkich uczestników inicjatywy.
- **Wyciszanie** — użytkownik może wyciszyć wzorzec (np. R8) dla inicjatywy lub typu decyzji; wyciszenia są widoczne i odwracalne.
- **Pętla zwrotna** — każdy komunikat ma reakcję: *trafne / nietrafne / już wiedziałem / nieistotne teraz*. To główne źródło kalibracji progów.

## 5.4. Kiedy mówić „wszystko w porządku”

System umie powiedzieć *„Przeanalizowałem nowe informacje — nie znalazłem podstaw do zmiany ustaleń”*, ale pokazuje to **tylko** gdy:

- zamyka wcześniej zgłoszoną kwestię,
- użytkownik o to zapytał,
- zbliża się decyzja o wysokiej stawce i potwierdzenie zwiększa zaufanie do podstaw.

## 5.5. Format komunikatu (poziom 2–3)

Każdy komunikat ma stałą, krótką strukturę:

```
Co:          [jedno zdanie]
Dlaczego:    [który element uzasadnienia jest dotknięty + źródło]
Wpływ:       [co może wymagać ponownej oceny / co pozostaje aktualne]
Pewność:     [fakt / interpretacja / wniosek systemu]
Propozycja:  [jeden konkretny krok]
```

Rozdzielenie „co wymaga ponownej oceny” od „co pozostaje aktualne” jest obowiązkowe — chroni przed reakcją „otwieramy wszystko od nowa”.
