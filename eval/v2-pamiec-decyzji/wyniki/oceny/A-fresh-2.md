# Karta oceny v2 — A-fresh-2

## Metadane

| Pole | Wartość |
|---|---|
| Wariant | A-fresh |
| Powtórzenie | 2 |
| Model generujący | nieznane |
| Oceniający | sędzia LLM (model: claude-opus-5-5) |
| Data | 2026-10-19 |

## Sygnały

| ID | Punkty (0–2) | Tydzień wykrycia | Poziom / sposób oznaczenia | Cytat (dowód) |
|---|---|---|---|---|
| S1 aneks X → rachunek D1 | 1 | T4 (w tygodniu pojawienia się) | Pozycja nr 1 „Wymagają Twojej uwagi” | „Aneks wchodzi w życie 2026-12-01, czyli tego samego dnia co niższy próg. Podnosi koszt każdej przesyłki, a przy progu 99 zł darmową dostawę sfinansujesz częściej” oraz „Przelicz business case progu 99 zł na nowych stawkach”. Wiąże aneks z progiem i liczy wzrost kosztu paczki (ok. +2,30 zł), ale nie porównuje go z zakładanym zyskiem decyzji (+22,6 tys. zł/mies.) ani nie stwierdza, że rachunek może stać się ujemny. To ogólne „sprawdź opłacalność”, więc 1 pkt. |
| S2 INT-233 → warunek aktualności D2 | 2 | T3 (w tygodniu pojawienia się) | Pozycja nr 1 „wymaga działania” | „Odświeżanie w planie Standard co ok. 12 h … Status w panelu może się spóźniać o pół doby” oraz „Nie będzie „w doręczeniu” ani awizacji … To uderza w cel panelu, czyli redukcję kontaktów o status” |
| S3 brief CZ → zakres D3 (wspólny checkout) | 2 | T1 (w tygodniu pojawienia się) | Pozycja nr 1 „Wymaga Twojej uwagi”, „konflikt z inicjatywą (3)” | „płatność przy odbiorze (dobírka) to ok. 30% płatności w czeskim e-commerce” oraz „Start w Czechach to 2027-03-01, czyli miesiąc po wycofaniu COD (od 2027-02-01)” oraz „Ustal … czy wycofanie COD dotyczy Czech”. Nie mówi wprost o wspólnym checkoucie (traktuje zasięg jako [założenie] do potwierdzenia), ale nazywa konflikt: inny udział pobrania na rynku CZ. |
| B1 bonus: aneks + wynik A/B razem (0–1) | 0 | — | — | W T4 brak odwołania do wyniku A/B (+5,8%, spadek koszyka). |
| **Suma (max 6 + 1)** | **5 + 0** | | | |

## Szum

| Miara | Wartość | Lista (tydzień / plik / cytat) |
|---|---|---|
| FA — fałszywe alarmy (P1–P4, szum, pogranicze na poziomie 3) | 3 | (1) T3 / 04-dane-tygodniowe (szum): „Tygodnik danych (tydz. 47) — wymaga uwagi dla inicjatywy 1 … Sprawdź przed startem 1 grudnia założenia modelu”; (2) T4 / 01-konkurent-prog-dostawy (P4): „Rozważ, czy dla automatów paczkowych próg powinien być niższy”, czyli sugestia zmiany D1 na tej podstawie, pozycja „wymaga uwagi”; (3) T4 / 02-swieta-dyzury (szum): „Wymagają Twojej uwagi cztery materiały: 03, 06, 01 i 02 … Traktuj 19 grudnia jako twardy termin awaryjny dla panelu”. |
| DUP — duplikaty ostrzeżeń | 1 | T4 / 06-sprint-review-integracje: pełne ostrzeżenie nr 2 o INT-233 („Panel wyjdzie więc na dwa dni przed cutoverem …”). Ta sama sprawa co w T3, bez nowej istotnej informacji. To nie jest „bez zmian w sprawie INT-233”. |
| Obciążenie — wszystkie pozycje „wymaga uwagi” w 4 tygodniach | 11 | T1: 1 (brief CZ); T2: 4 (A/B, inwentaryzacja, BLIK, Design System v4 — „Z 7 materiałów uwagi wymagają cztery”); T3: 2 (INT-233, tygodnik danych); T4: 4 (aneks, INT-233, konkurent, dyżury). |

Uwagi do klasyfikacji (bez kary):
- T1 / 06-dane-tygodniowe: stoi pod nagłówkiem „Wymaga Twojej uwagi”, ale sama odpowiedź obniża mu rangę („Nie jest to alarm, tylko dane do Twojej analizy”). Liczę go jako poziom 1, czyli bez FA i bez obciążenia. Przy najściślejszym odczycie byłby to 4. FA, a obciążenie wyniosłoby 12.
- T3 / 01-notatka-sprint-32-checkout: oznaczona jako „informacyjnie”, więc poziom 1, bez FA i bez obciążenia.
- T2 / 05 (P1): poziom 2 („Test potwierdza efekt pilotażu, ale trochę słabszy”, „Test mierzył konwersję, a o sensie progu 99 zł decyduje marża”). Odpowiedź wskazuje cieńszy wynik D1 i warunkowo zaleca weryfikację marży. Nie twierdzi, że test sam podważa decyzję, więc to nie jest FA.
- T2 / 02 (P2): „ryzyko do obserwacji (bez pilnej akcji)”, „Nie wnioskuję z jednego incydentu, że plan jest zły”. Nie zaleca ponownej oceny D3, więc to nie jest FA (liczę go w obciążeniu, bo autor wymienia go wśród czterech pozycji).
- T2 / 06 (inwentaryzacja) i T2 / 01 (Design System v4): pogranicze, poziom 2, więc bez kary.
- T3 / 03 (P3, etykiety X): pominięty („brak zmian w procesie i cenniku”), poprawnie.

Trafne zgłoszenia spoza klucza:

| Tydzień / plik | Zgłoszenie | Trafne? | Uzasadnienie |
|---|---|---|---|
| T4 / 02-swieta-dyzury | Zamrożenie wdrożeń 20.12–04.01 a release panelu 10.12 | Nie (FA) | Release panelu wypada przed zamrożeniem. Dokument nie podważa założenia żadnej decyzji, to tylko informacja o harmonogramie. |
| — | — | — | — |

## Subiektywnie

- Czy PM zauważyłby dzięki temu wynikowi coś, czego inaczej by nie zauważył? Tak. Chodzi o konflikt CZ/COD w T1 i utratę aktualności danych Y dla panelu w T3. Aneks X został powiązany z progiem, ale bez wniosku, że decyzja przestaje się opłacać.
- Ile czasu tygodniowo PM poświęciłby na przeczytanie wyników? Ok. 5–8 min.

SYGNALY=5/6 BONUS=0 FA=3 DUP=1 OBCIAZENIE=11
