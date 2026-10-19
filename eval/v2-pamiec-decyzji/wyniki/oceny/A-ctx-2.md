# Karta oceny v2 — A-ctx-2

## Metadane

| Pole | Wartość |
|---|---|
| Wariant | A-ctx (jedna rozmowa przez 4 tygodnie, materiały T0 na początku) |
| Powtórzenie | 2 |
| Model generujący | nieznany |
| Oceniający | sędzia LLM (model: claude-opus-5-5) |
| Data | 2026-10-19 |

## Sygnały

| ID | Punkty (0–2) | Tydzień wykrycia | Poziom / sposób oznaczenia | Cytat (dowód) |
|---|---|---|---|---|
| S1 aneks X → rachunek D1 | 2 | T4 (w tygodniu pojawienia się) | Pozycja nr 1 „najważniejsza” spośród „uwagi wymagają trzy rzeczy” | „Średni koszt paczki łącznie: 0,65 × 14,29 + 0,35 × 11,40 = ok. 13,28 zł (zamiast 11,80 zł)” … „Przy marży z notatki (235 000 zł) wynik to ok. **−4 000 zł miesięcznie**” |
| S2 INT-233 → warunek aktualności D2 | 2 | T3 (w tygodniu pojawienia się) | „jedna sprawa jest pilna i dotyczy podstaw decyzji o panelu statusu” | „W notatce z 2026-10-27 napisałeś, że panel ma sens, bo dane o zdarzeniach od przewoźników są teraz aktualne […] Ta przesłanka przestaje być prawdziwa dla przewoźnika Y, czyli ok. 35% paczek”; „Dla przesyłek Y ten etap nie będzie miał danych” |
| S3 brief CZ → zakres D3 (wspólny checkout) | 2 | T1 (w tygodniu pojawienia się) | Jedyna pozycja „wymaga Twojej uwagi” w T1 | „Wycofanie płatności za pobraniem koliduje ze startem w Czechach”; „checkout jest wspólny dla całej platformy. Wyłączenie metody w checkoucie obejmie więc także Czechy”; „ok. 30% wobec 4,1%” |
| B1 bonus: aneks + wynik A/B razem (0–1) | 1 | T4 | W pozycji o aneksie | „wraz z wynikami testu z tygodnia 2 może przesunąć wynik progu 99 zł na zero lub poniżej”; „Przy marży przeliczonej na efekt z testu krajowego (+5,8%, ok. 223 000 zł) wynik to ok. **−15 500 zł miesięcznie**”; wspomina też „spadku średniej wartości koszyka (−3,4%)” |
| **Suma (max 6 + 1)** | **6 + 1** | | | |

Opóźnienie: wszystkie trzy sygnały wykryte w tygodniu pojawienia się (S3 – T1, S2 – T3, S1 – T4).

## Szum

| Miara | Wartość | Lista (tydzień / plik / cytat) |
|---|---|---|
| FA — fałszywe alarmy (P1–P4, szum, pogranicze na poziomie 3) | 1 | T4 / `02-swieta-dyzury.md` (dokument z listy szumu) — pozycja nr 2 z „uwagi wymagają trzy rzeczy”: „Zamrożenie wdrożeń 20.12–04.01 zawęża czas na poprawki panelu”. Powiązanie jest logiczne (termin na poprawki z magazynu i INT-233), ale dotyczy harmonogramu realizacji, a nie założeń decyzji, więc zgodnie z kluczem liczę FA. |
| DUP — duplikaty ostrzeżeń | 1 | T4 / `06-sprint-review-integracje.md` — pełna, osobna pozycja nr 3 „uwagi wymagają”: „INT-233: termin jest niezagrożony, ale nic nie wskazuje, że wpływ na panel został rozwiązany”. Ponawia ostrzeżenie z T3; nowa informacja jest tylko pośrednia (brak wzmianki o Premium/panelu), więc to nie jest krótkie „bez zmian”. |
| Obciążenie — wszystkie pozycje „wymaga uwagi” w 4 tygodniach | 7 | T1: brief CZ (1). T2: wyniki A/B (P1), inwentaryzacja magazynu (pogranicze) (2). T3: INT-233 (1). T4: aneks X, święta/zamrożenie, sprint review INT-233 (3). Nie liczę pozycji oznaczonych jako „drobniejsze, bez pilnej akcji” / „bez pilnej akcji” / „nie wymaga to teraz działania”: T2 Design System v4 i incydent BLIK, T3 tygodnik danych, T4 konkurent. |

Uwagi do pułapek (bez FA):
- **P1** (T2 `05-wyniki-ab-prog-dostawy.md`): oznaczony jako wymagający uwagi („osłabiają uzasadnienie progu 99 zł”), z przeliczeniem do ok. +11 tys. zł i wnioskiem „zapas jest mniejszy, niż zakładano, a wynik może być bliski zera lub ujemny”. Wskazuje cieńszy wynik D1 i proponuje ponowne przeliczenie, nie zmianę decyzji na podstawie samego testu → poziom 2 dopuszczalny według klucza. Przypadek graniczny: przeliczenie dolnej granicy przedziału (−54 tys. zł) jest ostrzejsze niż „lekko osłabia”, ale odpowiedź oznacza je jako [założenie].
- **P2** (T2 BLIK): „Nie zmienia decyzji o pobraniu” — w części „drobniejsze, bez pilnej akcji”, poziom 1. Bez FA.
- **P3** (T3 etykiety X): pominięty („bez wpływu na proces i cennik”), poziom 0.
- **P4** (T4 konkurent): „kontekst, bez pilnej akcji”; „Nie traktowałbym tego jako argumentu za obniżeniem progu” — poziom 1. Bez FA.
- **Pogranicze magazyn** (T2): pozycja „wymaga uwagi” z propozycją wyjątku w wyliczeniu daty, bez sugestii zmiany decyzji → poziom 2, bez FA.
- **Pogranicze Design System v4** (T2): „bez pilnej akcji”, poziom 1.

Trafne zgłoszenia spoza klucza:

| Tydzień / plik | Zgłoszenie | Trafne? | Uzasadnienie |
|---|---|---|---|
| T3 / `06-INT-233-api-przewoznika-y.md` | Koszt planu Premium u Y (+0,30 zł/paczkę) podnosi też koszt paczki w rachunku D1 (ok. +1 700 zł/mies.) | Tak (drobne) | Poprawne powiązanie dwóch decyzji, rachunek się zgadza (0,35 × 0,30 ≈ 0,105 zł); nie oznaczone jako osobna pozycja do działania. |
| T4 / `02-swieta-dyzury.md` | Zamrożenie wdrożeń ogranicza czas na poprawki panelu | Częściowo | Użyteczne operacyjnie, ale nie podważa założeń żadnej decyzji — policzone jako FA zgodnie z kluczem. |

## Subiektywnie

- Czy PM zauważyłby dzięki temu wynikowi coś, czego inaczej by nie zauważył? **tak** — wszystkie trzy ukryte powiązania wykryte w terminie, z poprawnym rachunkiem dla S1 (−4 tys. zł/mies., zgodnie z kluczem).
- Ile czasu tygodniowo PM poświęciłby na przeczytanie wyników? ok. 3–5 min (T1–T3), ok. 6–7 min (T4, najdłuższa odpowiedź).

SYGNALY=6/6 BONUS=1 FA=1 DUP=1 OBCIAZENIE=7
