# 4. Knowledge Gap Closure (B — mechanizm działania)

Radar mówi, **gdzie** decyzja jest zagrożona. Knowledge Gap Closure (KGC) sprawia, że na tym się nie kończy: zamienia ryzyko w nazwaną lukę (`Unknown`) i prowadzi ją do rozstrzygnięcia — możliwie najtańszą drogą.

## 4.1. Cykl życia luki

```
 detected ──► framed ──► searching_existing ──┬──► resolved (odpowiedź już istniała)
                                               │
                                               └──► action_proposed ──► in_progress ──► evidence_received
                                                          │                                     │
                                                          ▼                                     ▼
                                                   accepted_risk                         resolved / reframed
                                            (świadoma decyzja człowieka)
```

| Stan | Co się dzieje |
|---|---|
| `detected` | Radar wskazał ryzyko, które wynika z braku wiedzy |
| `framed` | Luka sformułowana jako **rozstrzygalne pytanie** z kryterium rozstrzygnięcia („Na którym kroku i dlaczego rezygnuje > 50% użytkowników?”) |
| `searching_existing` | System **najpierw** przeszukuje dostępne źródła — odpowiedź często już istnieje w organizacji |
| `action_proposed` | Jeśli nie istnieje: propozycja najtańszego działania wystarczającego do rozstrzygnięcia |
| `in_progress` | Działanie ma właściciela i (opcjonalnie) termin |
| `evidence_received` | Nowy dowód trafia do modelu, radar ponownie ocenia ryzyko |
| `resolved` / `reframed` | Luka zamknięta lub przeformułowana (np. wynik ujawnił inne pytanie) |
| `accepted_risk` | Właściciel decyzji świadomie akceptuje niepewność — zapisane z uzasadnieniem; Guardian dalej monitoruje |

`accepted_risk` jest pełnoprawnym wynikiem. System ma pomagać podejmować **świadome** decyzje, nie zmuszać do analizy.

## 4.2. Drabina działań — od najtańszego

KGC proponuje działania w kolejności kosztu. Wyższy szczebel tylko wtedy, gdy niższy nie wystarczy do rozstrzygnięcia **na poziomie pewności wymaganym przez stawkę decyzji**.

| Szczebel | Działanie | Typowy koszt |
|---|---|---|
| 0 | Odpowiedź istnieje w połączonych źródłach — system ją wskazuje | minuty |
| 1 | Zapytanie do osoby, która prawdopodobnie zna odpowiedź (system wskazuje kogo i formułuje pytanie) | godziny |
| 2 | Analiza istniejących danych (zapytanie do analityki, przegląd zgłoszeń, logów) | dni |
| 3 | Szybka weryfikacja jakościowa (5 rozmów, przegląd nagrań sesji) | dni–tydzień |
| 4 | Eksperyment / prototyp / test | tygodnie |
| 5 | Pełne badanie | tygodnie–miesiące |

Wartość informacji: system szacuje, czy odpowiedź **może zmienić decyzję**. Jeśli żaden realistyczny wynik działania nie zmieni decyzji — działanie nie jest rekomendowane, nawet jeśli luka istnieje.

## 4.3. Tryb aktywny (Copilot)

W trybie Copilot KGC prowadzi użytkownika:

1. Pokazuje lukę i dlaczego jest istotna dla tej konkretnej decyzji.
2. Pokazuje, co znalazł w istniejących źródłach (szczebel 0).
3. Proponuje jeden rekomendowany krok + alternatywy.
4. Pomaga go wykonać (np. formułuje pytanie do analityka, przygotowuje zapytanie, przewodnik do 5 rozmów).
5. Gdy pojawi się wynik — interpretuje go w kontekście luki, pokazuje zmianę oceny radaru.

Przykład:

> **System:** Decyzja o estymacji panelu statusu opiera się na założeniu, że zgłoszenia wynikają z braku informacji w interfejsie. Nie znalazłem dowodów na to założenie.
> W danych supportu (export z Q3) zgłoszenia o status rosną w dniach opóźnień synchronizacji z przewoźnikiem — to wskazuje na konkurencyjne wyjaśnienie.
> **Rekomendacja (szczebel 2, ~2 dni):** porównać daty zgłoszeń z logiem opóźnień aktualizacji statusu. Jeśli korelacja jest silna, panel nie rozwiąże głównej przyczyny.
> Mogę przygotować specyfikację zapytania dla zespołu danych.

## 4.4. Tryb w tle (Guardian)

Guardian obserwuje otwarte luki i zaakceptowane ryzyka:

- nowy dokument / dane odpowiadające na otwartą lukę → propozycja zamknięcia (z dowodem) zamiast nowego powiadomienia o problemie;
- luka blokująca decyzję zbliżającą się do terminu → przypomnienie przy najbliższej okazji;
- sygnał podważający zaakceptowane ryzyko → ponowne otwarcie z wyjaśnieniem.

## 4.5. Kogo zapytać

KGC wskazuje osoby wyłącznie na podstawie jawnych sygnałów (autor dokumentu, właściciel obszaru, właściciel danych) i **proponuje** kontakt — nie wysyła wiadomości w imieniu użytkownika bez zgody (konfigurowalne w późniejszych etapach).
