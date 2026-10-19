# PDI — Product Decision Intelligence

> System, który rozpoznaje, kiedy organizacja jeszcze nie rozumie problemu wystarczająco dobrze, aby bezpiecznie przejść do rozwiązania — i aktywnie pomaga tę lukę zamknąć.

PDI nie jest kolejnym narzędziem do zarządzania wymaganiami, generatorem PRD ani asystentem do dokumentacji. Jego centralnym obiektem jest **decyzja produktowa wraz z pełnym uzasadnieniem**, a celem — jakość tego uzasadnienia: od pierwszej hipotezy, przez realizację, aż po ocenę rezultatu.

## Ustalenia (stan na teraz)

| Obszar | Decyzja |
|---|---|
| Problem do wyeliminowania | **E** — wszystkie cztery (niepełne przesłanki, rozproszona wiedza, utrata spójności, zbyt szybkie przejście do rozwiązania), z naciskiem na wykrywanie zagrożeń dla jakości decyzji, zanim staną się kosztownymi błędami |
| Poziom ambicji | Poziom 2 (Product Decision Intelligence) jako cel, poziom 3 (Organizational Decision Intelligence) jako wizja |
| Autonomia | Wariant 2 (**Active Decision Copilot**) na start + wariant 3 (**Continuous Decision Guardian**) jako kierunek docelowy |
| Rdzeń pierwszej wersji | **A. Decision Risk Radar** — główna wartość · **B. Knowledge Gap Closure** — mechanizm działania · **C. Decision Integrity Graph** — fundament |
| Pierwszy użytkownik | **PM jako właściciel decyzji** — system jest jego sparingpartnerem; wyniki domyślnie prywatne dla PM-a |
| Punkt startu | Brak dostępu do inicjatyw → projekt zaczyna się od pozyskania design partnerów (Etap 0) |
| Zespół | Jedna osoba — plan dostosowany ([§6 planu](docs/08-plan-projektu.md#6-zespół)) |
| Charakter projektu | Warunkowy: komercyjny przy luce rynkowej, wewnętrzny przy silnej konkurencji — rozstrzyga Etap 2 |
| Zasada nadrzędna | System ujawnia, uzasadnia i proponuje. Nie blokuje inicjatyw i nie podejmuje decyzji za ludzi. Chroni uwagę ludzi równie świadomie jak jakość decyzji. |

## Dokumentacja

1. [Wizja i pozycjonowanie](docs/01-wizja.md)
2. [Living Decision Model — model wiedzy (fundament C)](docs/02-living-decision-model.md)
3. [Decision Risk Radar (A)](docs/03-decision-risk-radar.md)
4. [Knowledge Gap Closure (B)](docs/04-knowledge-gap-closure.md)
5. [Attention Intelligence — kiedy system się odzywa](docs/05-attention-intelligence.md)
6. [MVP i protokół pilotażu](docs/06-mvp-i-pilotaz.md)
7. [Ryzyka projektu i otwarte pytania](docs/07-ryzyka-i-otwarte-pytania.md)
8. **[Plan projektu](docs/08-plan-projektu.md)** — etapy 0–6, bramki, kryteria zatrzymania, pierwsze 5 dni
9. [Weryfikacja planu](docs/09-weryfikacja-planu.md) — co poprawiono w planie wstępnym i dlaczego
10. **[Analiza konkurencji](docs/10-analiza-konkurencji.md)** — mapa rynku, macierz scenariuszy S1–S6, wnioski dla decyzji komercyjny / wewnętrzny ([dowody](docs/research/20261019-konkurencja/evidence.md))

Materiały do pozyskania design partnerów (Etap 0):

- [Profil design partnera](outreach/profil-design-partnera.md) — kryteria, pytania kwalifikacyjne, kanały (dokument wewnętrzny)
- [Propozycja dla PM-ów](outreach/propozycja-dla-pm.md) — jednostronicowe zaproszenie
- [Szablony pierwszego kontaktu](outreach/wiadomosc-kontaktowa.md)
- [Zasady poufności](outreach/zasady-poufnosci.md) — wersja robocza

Artefakty techniczne:

- [`model/living-decision-model.schema.json`](model/living-decision-model.schema.json) — schemat danych modelu decyzji (JSON Schema)
- [`examples/status-zamowienia.yaml`](examples/status-zamowienia.yaml) — przykład roboczy: inicjatywa „panel statusu zamówienia” wraz z oczekiwanym wynikiem radaru
- [`eval/status-zamowienia/`](eval/status-zamowienia/README.md) — **test praktyczny**: ogólny asystent AI vs prototyp PDI na tym przypadku, w dwóch rundach (analiza i reakcja na nowe informacje)

## Status

Faza koncepcyjna. Następny krok: [test praktyczny](eval/status-zamowienia/README.md) i [pierwsze pięć dni planu](docs/08-plan-projektu.md#8-pierwsze-pięć-dni-dostosowane-do-braku-inicjatyw). Teza o luce rynkowej jest **hipotezą do weryfikacji**, a nie ustaleniem — patrz [ryzyka](docs/07-ryzyka-i-otwarte-pytania.md).
