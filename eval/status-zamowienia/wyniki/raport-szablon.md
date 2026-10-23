# Raport z testu praktycznego — status zamówienia

Wypełnić po zakończeniu wszystkich przebiegów. Kryteria oceny zostały zapisane w README **przed** testem i nie wolno ich zmieniać po zobaczeniu wyników. Jeśli coś trzeba zmienić, zapisz zmianę w sekcji „Odstępstwa”.

```
Test: status-zamowienia | data: RRRR-MM-DD | model: … | powtórzeń: 3
Warianty: A (ogólny asystent, dobry prompt), B (prototyp PDI), [inne: …]
```

## Wyniki zbiorcze

| Miara | A | B | Uwagi |
|---|---|---|---|
| R1: średnia suma (max 16) | | | |
| R1: rozrzut (min–max z 3) | | | |
| W1 wykryte pełnie — pass^3 (we wszystkich 3 przebiegach) | | | |
| W2 wykryte pełnie (≥ 2 sygnały) — pass^3 | | | |
| W3 wykryte pełnie — pass^3 | | | |
| R1: średnia liczba fałszywych alarmów | | | |
| R2: N1–N3 średnio (max 6) — A-R2a / A-R2c / B-R2 | | | |
| R2: sam powiązał 09 z decyzją bez pytania (x/3) — A-R2a / B-R2 | | | |
| R2: N4 zaliczone (x/3) | | | |
| Czas pracy PM-a na przebieg (min) | | | |
| Zgłoszenia trafne spoza klucza | | | |

Zgodność z sędzią LLM (jeśli użyty): …%

## Werdykt względem kryteriów z README

| Kryterium | Spełnione? | Dowód |
|---|---|---|
| K1 — metoda działa | | |
| K2 — łączenie informacji | | |
| K3 — przewaga ciągłości | | |
| K4 — szum | | |

**Interpretacja (wiersz z tabeli w README):** …

## Odstępstwa od procedury

…

## Wnioski i zmiany

- Zmiany w katalogu wzorców / schemacie / prompcie B: …
- Nowe przypadki do zbioru testowego: …
- Co zmienia się w planie (Etap 2.3, MVP): …
