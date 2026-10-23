# Karta oceny

Jedna karta na **przebieg** (wariant × runda × powtórzenie). Punkty według [klucza odpowiedzi](klucz-odpowiedzi.md). Skopiuj do `wyniki/` jako `<wariant>-<runda>-<nr>.md`, np. `B-R1-2.md`.

## Metadane przebiegu

| Pole | Wartość |
|---|---|
| Wariant i runda | A-R1 / A-R2a / A-R2b / A-R2c / B-R1 / B-R2 / (inne narzędzie: …) |
| Powtórzenie | 1 / 2 / 3 |
| Narzędzie i model | np. Claude (nazwa modelu z interfejsu), ChatGPT (…) |
| Data | |
| Czas pracy (min) | |
| Plik z odpowiedzią | `wyniki/surowe/<nazwa>.md` |

## Runda 1

| ID | Punkty (0–2) | Cytat z odpowiedzi (dowód oceny) |
|---|---|---|
| W1 hipoteza o przyczynie jako fakt | | |
| W2 konkurencyjne wyjaśnienie (nieaktualne statusy), ≥ 2 sygnały | | |
| W3 brak metryki rezultatu | | |
| W4 brak alternatyw / pominięte rekomendacje badań | | |
| W5 nadinterpretacja analityki | | |
| W6 panel eksponuje opóźnione dane | | |
| Najtańszy krok | | |
| Werdykt proporcjonalny | | |
| **Suma (max 16)** | | |

Fałszywe alarmy (F1–F5 zgłoszone jako krytyczne lub ważne): lista ID: ……, **liczba: …**

Inne problemy zgłoszone przez wariant, których nie ma w kluczu (ocenić osobno: trafne / nietrafne):

| Zgłoszenie | Trafne? | Uwagi |
|---|---|---|
| | | |

> Trafne zgłoszenie spoza klucza nie jest błędem — może oznaczać lukę w kluczu. Dopisz je do klucza **po** zakończeniu wszystkich przebiegów, nie w trakcie.

## Runda 2

| ID | Punkty | Cytat |
|---|---|---|
| N1 dokument 09 podważa założenie decyzji (wysoki priorytet) | 0–2 | |
| N2 co aktualne / co do ponownej oceny | 0–2 | |
| N3 konkretny następny krok | 0–2 | |
| N4 brak ostrzeżenia o dokumencie 10 | zal. / niezal. | |
| **Suma N1–N3 (max 6)** | | |

Dla A-R2a dodatkowo: czy asystent **sam, bez pytania**, powiązał dokument 09 z decyzją? tak / nie

## Subiektywnie (wypełnić na końcu)

- Czy wynik pomógłby PM-owi podjąć lepszą decyzję? (1–5)
- Ile czasu zajęłoby PM-owi przeczytanie i zweryfikowanie wyniku? (min)
- Co było najbardziej, a co najmniej przydatne?
