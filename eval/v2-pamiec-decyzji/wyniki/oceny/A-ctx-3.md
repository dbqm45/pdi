# Karta oceny v2 — A-ctx-3

## Metadane

| Pole | Wartość |
|---|---|
| Wariant | A-ctx |
| Powtórzenie | 3 |
| Model generujący | nieznane |
| Oceniający | sędzia LLM (model: claude-opus-5-5) |
| Data | 2026-10-19 |

## Sygnały

| ID | Punkty (0–2) | Tydzień wykrycia | Poziom / sposób oznaczenia | Cytat (dowód) |
|---|---|---|---|---|
| S1 aneks X → rachunek D1 | 2 | T4 (w tygodniu pojawienia się) | „Wymaga Twojej uwagi”, pozycja 1 | „średni koszt ważony z Y: ok. 13,28 zł zamiast 11,80 zł”; „ok. +26 600 zł miesięcznie”; „wynik przy marży z pilotażu (235 000 zł): ok. -4 000 zł miesięcznie”; „Pierwotna decyzja zatwierdziła wynik dodatni, a przesłanka właśnie zniknęła.” |
| S2 INT-233 → warunek aktualności D2 | 2 | T3 (w tygodniu pojawienia się) | „Wymaga Twojej uwagi: 1 rzecz, ale poważna” | „migracja przewoźnika Y na API v3 podważa założenie, na którym oparto decyzję o panelu statusu”; „Po migracji opóźnienie dla Y wróci do rzędu 12 h”; „Dla paczek Y ten status [„w doręczeniu”] nie będzie dostępny w żadnym planie” |
| S3 brief CZ → zakres D3 (wspólny checkout) | 2 | T1 (w tygodniu pojawienia się) | „Wymaga Twojej uwagi: 1 rzecz” | „Wyłączenie płatności za pobraniem od 2027-02-01 dotyczy wspólnego checkoutu, który obsługuje wszystkie rynki”; „Uzasadnienie wycofania opierało się na polskich danych: 4,1% zamówień”; „Przy 30% udziału w Czechach to ryzyko jest znacznie większe” |
| B1 bonus: aneks + wynik A/B razem (0–1) | 1 | T4 | w ramach pozycji 1 | „a przy marży z testu krajowego (+5,8%, ok. 223 400 zł): ok. -15 500 zł miesięcznie”; „Do tego dochodzą wcześniej opisane spadek wartości koszyka o 3,4%” |
| **Suma (max 6 + 1)** | **6 + 1** | | | |

## Szum

| Miara | Wartość | Lista (tydzień / plik / cytat) |
|---|---|---|
| FA — fałszywe alarmy (P1–P4, szum, pogranicze na poziomie 3) | 0 | Brak. Uzasadnienie dla pozycji granicznych: **P1** (T2/05): pozycja 1 „wymaga uwagi”, ale wskazuje cieńszy wynik D1 i wprost „To nie jest dowód, że decyzja jest zła” — poziom 2 dopuszczalny wg klucza. **P2** (T2/02): „niski priorytet”, „nie zmienia decyzji” — nie zaleca ponownej oceny D3. **P3** (T3/03): w „Pominąłem” („brak zmian w procesie i cenniku”) — poziom 0. **P4** (T4/01): „Nie wymaga to działania teraz”, „do wiadomości przy przeglądzie po Q1” — nie zaleca zmiany D1. **Pogranicze** T2/06 magazyn i T2/01 Design System: oznaczone jako wymagające uwagi (odpowiednik poziomu 2), bez sugestii zmiany decyzji D2 — bez kary. |
| DUP — duplikaty ostrzeżeń | 1 | T4 / 06-sprint-review-integracje.md: pozycja 2 „wymaga uwagi” — „INT-233 postępuje […] to nadal otwarta sprawa z zeszłego tygodnia (dane o Y co ok. 12 h, brak „w doręczeniu”)”. Krótsze niż pierwotne ostrzeżenie i z niewielką nową informacją (mapowanie gotowe, okno zamrożenia), ale ponownie wystawione jako osobna pozycja do uwagi o tej samej sprawie, a nie jako „bez zmian”. Przypadek graniczny; łagodniejsza interpretacja dałaby 0. |
| Obciążenie — wszystkie pozycje „wymaga uwagi” w 4 tygodniach | 9 | T1: brief CZ (1). T2: A/B progu, magazyn, Design System, BLIK (4). T3: INT-233 (1). T4: aneks X, INT-233 + zamrożenie wdrożeń, konkurenci (3). Uwaga: pozycje BLIK („niski priorytet”) i konkurenci („Nie wymaga to działania teraz”) same obniżają swój priorytet; bez nich obciążenie efektywne = 7. Obie wartości powyżej „maks. rozsądnego” 5. |

Opóźnienie: S1 — tak (T4), S2 — tak (T3), S3 — tak (T1); wszystkie wykryte w tygodniu pojawienia się.

Trafne zgłoszenia spoza klucza (np. powiązania, których autor klucza nie przewidział):

| Tydzień / plik | Zgłoszenie | Trafne? | Uzasadnienie |
|---|---|---|---|
| T3 / 06-INT-233 (w ramach S2) | Plan Premium Y (+0,30 zł/paczkę) obciążyłby też rachunek D1: „ok. 1 900 zł miesięcznie, czyli niemało przy wyniku +11–22 tys. zł” | tak | Poprawne powiązanie kosztu opcji naprawczej D2 z cienkim rachunkiem D1; nie jest to osobny alarm. |
| T4 / 02-swieta-dyzury.md | Zamrożenie wdrożeń 2026-12-20 – 2027-01-04 ogranicza okno na poprawki panelu po migracji Y | częściowo | Rzeczowe ograniczenie harmonogramu dla poprawek D2, nie podważa decyzji; wplecione w pozycję o INT-233, nie liczone jako FA. |
| T3 / 01-notatka-sprint-32-checkout.md | Zapisywanie kart „lekko wspiera przejście klientów z płatności za pobraniem na kartę” — oznaczone „Do wiadomości, bez działania” | tak (poziom 0–1) | Trafna, poprawnie zaszeregowana obserwacja dot. D3. |

## Subiektywnie

- Czy PM zauważyłby dzięki temu wynikowi coś, czego inaczej by nie zauważył? tak — wszystkie trzy sygnały wykryte w tygodniu pojawienia się, z rachunkiem i wskazaniem podważonego założenia.
- Ile czasu tygodniowo PM poświęciłby na przeczytanie wyników? ok. 3–6 min (T2 i T4 najdłuższe, 4 i 3 pozycje).

SYGNALY=6/6 BONUS=1 FA=0 DUP=1 OBCIAZENIE=9
