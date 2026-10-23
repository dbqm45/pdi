# Walidacja na sobie: 10 dni roboczych

Protokół i kryteria: [dokument 14 §6](../../docs/14-pdi-standalone.md#6-walidacja-dwa-tygodnie-na-sobie-kryteria-zapisane-przed-startem).
Start: dzień pierwszego zapisu w `pdi-decisions`.

## Co dzień (2–3 minuty, na koniec dnia)

Skopiuj [`szablon-dnia.md`](szablon-dnia.md) do `dni/RRRR-MM-DD.md` i wypełnij.
**Bez treści decyzji** — tylko ID (`DEC-0007`), liczby i krótkie opisy sytuacji bez nazw klientów, kwot i danych
osobowych. Treść decyzji jest w prywatnym `pdi-decisions`.

## Co tydzień i na koniec

1. `PDI_REGISTRY_PATH=~/pdi-decisions uv run --directory <pdi> pdi-stats` — liczba zapisów w tygodniu (W1),
   rodzaje, zastąpienia.
2. Na koniec 10 dni: wypełnij [`podsumowanie.md`](podsumowanie.md) — wynik każdego kryterium i decyzja,
   co dalej (tabela w dokumencie 14 §6). Wynik zapisz też jako decyzję w rejestrze (`/record-decision`).

## Co mierzy który zapis

| Kryterium | Skąd |
|---|---|
| W1 — ≥ 5 decyzji tygodniowo bez przymusu | `pdi-stats` + rubryka „zapisy porzucone / wymuszone” |
| W2 — mediana ≤ 60 s; ≥ 70% szkiców z ≤ 1 poprawką | notatka dzienna: czas i liczba poprawek dla każdego zapisu |
| W3 — ≥ 2 przypadki, gdy `find_decisions` coś zmieniło lub potwierdziło | notatka dzienna: rubryka „odczyt” |
| W4 — brak zmyślonych uzasadnień i założeń | notatka dzienna: rubryka „zmyślenia” (każdy przypadek) |
