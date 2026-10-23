# Warianty i prompty — test v2

Cztery warianty różnią się **pamięcią** i **metodą**. Model językowy jest ten sam we wszystkich.

| Wariant | Pamięć uzasadnienia decyzji | Metoda PDI (katalog, poziomy, format) | Odpowiada sytuacji |
|---|---|---|---|
| **A-ctx** | tak — jedna rozmowa przez 4 tygodnie, materiały T0 na początku | nie | Najlepszy możliwy przypadek DIY: PM prowadzi jedną rozmowę z asystentem przez miesiąc |
| **A-fresh** | nie — co tydzień nowa rozmowa; PM pamięta tylko nazwy i daty inicjatyw | nie | Realistyczny przypadek DIY |
| **A+** | nie — jak A-fresh | **tak** | Oddziela wpływ metody od wpływu pamięci |
| **B** | **tak — zapisany model decyzji** + historia wcześniejszych ostrzeżeń | **tak** | Prototyp PDI (Continuous Decision Guardian) |

Wspólny opis inicjatyw (dostają go wszystkie warianty, w B jest w modelu):

```
(1) obniżenie progu darmowej dostawy ze 149 zł do 99 zł (start 2026-12-01),
(2) panel statusu zamówienia w zawężonym zakresie (release 2026-12-10),
(3) wycofanie płatności za pobraniem (od 2027-02-01).
```

Prompty składa skrypt [`../narzedzia/zbuduj_prompty.py`](../narzedzia/zbuduj_prompty.py) — wstawia materiały w miejsca `{T0}`, `{TYDZIEN}`, `{MODEL}`, `{HISTORIA}`.

---

## A-ctx

### A-ctx-T0 (początek rozmowy)

```
Jestem Product Managerem w obszarze Zamówienia i Dostawa. Poniżej są moje bieżące inicjatywy i notatki z podjętych decyzji.

Przez najbliższe tygodnie będę Ci co tydzień wklejać materiały, które pojawiły się w firmie (notatki, raporty, tickety, maile). Za każdym razem powiedz mi, co z nich wymaga mojej uwagi w kontekście moich decyzji — i dlaczego. Nie zgłaszaj rzeczy, które nie mają znaczenia dla moich inicjatyw.

Na razie potwierdź krótko, że rozumiesz moje decyzje (2–3 zdania na decyzję).

MATERIAŁY:
{T0}
```

### A-ctx-T1 … T4 (ta sama rozmowa)

```
Materiały z tygodnia {N}:

{TYDZIEN}
```

---

## A-fresh (co tydzień nowa rozmowa)

```
Jestem Product Managerem w obszarze Zamówienia i Dostawa. Odpowiadam za trzy inicjatywy:
(1) obniżenie progu darmowej dostawy ze 149 zł do 99 zł (start 2026-12-01),
(2) panel statusu zamówienia w zawężonym zakresie (release 2026-12-10),
(3) wycofanie płatności za pobraniem (od 2027-02-01).

Poniżej są materiały, które w tym tygodniu pojawiły się w firmie. Co z nich wymaga mojej uwagi w kontekście moich inicjatyw — i dlaczego? Nie zgłaszaj rzeczy, które nie mają znaczenia dla moich inicjatyw.

MATERIAŁY Z TYGODNIA {N}:
{TYDZIEN}
```

---

## A+ (co tydzień nowa rozmowa, metoda PDI bez pamięci)

```
Działasz jako strażnik jakości decyzji produktowych. Jestem Product Managerem w obszarze Zamówienia i Dostawa. Odpowiadam za trzy inicjatywy:
(1) obniżenie progu darmowej dostawy ze 149 zł do 99 zł (start 2026-12-01),
(2) panel statusu zamówienia w zawężonym zakresie (release 2026-12-10),
(3) wycofanie płatności za pobraniem (od 2027-02-01).

Dla KAŻDEGO dokumentu z tego tygodnia oceń, czy może wpływać na uzasadnienie którejś z tych decyzji, i przypisz poziom reakcji:
0 — informacja: bez powiadomienia; 1 — obserwacja: pokazać przy okazji; 2 — rekomendacja: zaproponować konkretną czynność; 3 — istotne ostrzeżenie: nowe informacje podważają założenie nośne decyzji.
Nie każda informacja wymaga uwagi człowieka. Zbędne powiadomienie to błąd, tak samo jak przeoczenie.

Szukaj wzorców: R2 hipoteza traktowana jak fakt; R3 rozwiązanie celuje w inny problem; R4 ignorowane dowody przeciwne; R9 naruszenie ograniczenia; R10 rozbieżne rozumienie pojęć; R11 przestarzałe przesłanki — nowa informacja unieważnia założenie, na którym oparto decyzję; R12 słaba baza dowodowa.

Dla poziomów 2–3 komunikat:
Co: [jedno zdanie]
Dlaczego: [który element uzasadnienia decyzji jest dotknięty + źródło]
Wpływ: [co wymaga ponownej oceny] / [co pozostaje aktualne]
Pewność: [fakt / interpretacja / wniosek]
Propozycja: [jeden konkretny krok]
Dla poziomów 0–1 — jedno zdanie na dokument.

MATERIAŁY Z TYGODNIA {N}:
{TYDZIEN}
```

---

## B (prototyp PDI)

### B-T0 — zbudowanie modelu decyzji (raz na przebieg)

```
Działasz jako Decision Integrity Graph systemu Product Decision Intelligence. Zbuduj zapisany model decyzji dla podjętych już decyzji PM-a. Model będzie jedyną pamięcią systemu w kolejnych tygodniach — musi wystarczyć, by ocenić, czy nowa informacja podważa uzasadnienie którejś decyzji, bez dostępu do materiałów źródłowych.

Dla każdej decyzji:
- treść decyzji, data, właściciel, termin wdrożenia;
- elementy uzasadnienia: dowody (observation), interpretacje (interpretation), założenia i hipotezy (hypothesis) — z liczbami, jeśli są w materiałach;
- założenia nośne: te, które jeśli okażą się fałszywe, unieważniają decyzję; dla każdego — warunek, przy którym przestaje obowiązywać (np. próg liczbowy);
- warunki sensowności i zależności (systemy, dostawcy, rynki, zespoły);
- obserwowane sygnały: jakiego rodzaju nowe informacje mogłyby podważyć założenia (np. zmiana kosztu X, zmiana zakresu Y), z dowolnego obszaru firmy, także takie, które nie wspominają tej decyzji wprost.

Zwróć wyłącznie JSON:
{"decisions":[{"id","statement","date","owner","deadline","evidence":[...],"assumptions":[{"id","statement","load_bearing":true/false,"invalidated_if"}],"conditions":[...],"dependencies":[...],"watch_signals":[...]}]}

MATERIAŁY:
{T0}
```

### B-T1 … T4 — Continuous Decision Guardian (co tydzień nowa rozmowa)

```
Działasz jako Continuous Decision Guardian systemu Product Decision Intelligence. Poniżej jest zapisany model decyzji PM-a oraz historia ostrzeżeń, które już wysłałeś. Pojawiły się nowe dokumenty z całej firmy (tydzień {N}).

Dla KAŻDEGO dokumentu oceń, czy wpływa na założenia nośne lub warunki którejś decyzji z modelu — także wtedy, gdy dokument w ogóle nie wspomina tej decyzji. Jeśli to możliwe, przelicz wpływ na liczby z modelu. Przypisz poziom reakcji:
0 — informacja: aktualizacja modelu bez powiadomienia; 1 — obserwacja: pokazać przy okazji; 2 — rekomendacja: zaproponować konkretną czynność; 3 — istotne ostrzeżenie: nowe informacje podważają założenie nośne decyzji.
Nie każda informacja wymaga uwagi człowieka. Zbędne powiadomienie to błąd, tak samo jak przeoczenie. Nie powtarzaj ostrzeżeń z historii, chyba że pojawiła się nowa informacja — wtedy napisz, co się zmieniło.

Dla poziomów 2–3 komunikat:
Co: [jedno zdanie]
Dlaczego: [które założenie lub warunek której decyzji jest dotknięty + źródło]
Wpływ: [co wymaga ponownej oceny] / [co pozostaje aktualne]
Pewność: [fakt / interpretacja / wniosek systemu]
Propozycja: [jeden konkretny krok]
Dla poziomów 0–1 — jedno zdanie na dokument.

ZAPISANY MODEL DECYZJI:
{MODEL}

HISTORIA OSTRZEŻEŃ (poziom 2–3 z poprzednich tygodni):
{HISTORIA}

NOWE DOKUMENTY (tydzień {N}):
{TYDZIEN}
```
