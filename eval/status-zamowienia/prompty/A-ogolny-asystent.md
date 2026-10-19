# Wariant A — ogólny asystent AI z dobrym promptem

Wariant A to najsilniejszy zamiennik PDI. Prompt ma być **uczciwie dobry**: tak napisałby go doświadczony PM, który wie, czego szuka. Celowo słaby prompt unieważnia porównanie.

## A-R1 — runda 1 (nowa rozmowa)

Wklej poniższy tekst, a pod nim treść 8 plików z `materialy/runda-1/` (każdy poprzedzony nazwą pliku).

```
Jesteś doświadczonym, krytycznie myślącym Product Managerem i doradcą. Jutro decydujemy, czy przekazać poniższą inicjatywę do estymacji (ok. 2 sprinty, 2 zespoły).

Przeanalizuj materiały i oceń, czy ta decyzja jest dobrze uzasadniona. Wskaż:
1. co jest dobrze poparte dowodami,
2. niezweryfikowane założenia i to, od którego założenia decyzja zależy najbardziej,
3. sprzeczności między materiałami i alternatywne wyjaśnienia problemu,
4. czego brakuje, żeby podjąć decyzję świadomie,
5. rekomendowany następny krok (możliwie tani) i Twoją rekomendację: czy przekazywać do estymacji.

Bądź konkretny, przy każdym wniosku wskaż dokument źródłowy. Nie wymyślaj problemów na siłę — jeśli coś jest w porządku, napisz to.

MATERIAŁY:
[wklej pliki 01–08]
```

## A-R2a — runda 2, ta sama rozmowa, bez pytania

W **tej samej rozmowie** co A-R1 wklej:

```
Minął miesiąc. Inicjatywa została przekazana do estymacji i jest w realizacji. Doszły nowe materiały:

[wklej pliki 09 i 10]
```

Nie zadawaj pytania. Sprawdzamy, czy asystent **sam** powiąże nową informację z wcześniejszą decyzją.

## A-R2b — runda 2, ta sama rozmowa, z pytaniem

Jeśli w A-R2a asystent nie powiązał dokumentu 09 z decyzją, dopisz w tej samej rozmowie:

```
Czy te materiały zmieniają coś w ocenie decyzji o panelu statusu? Co pozostaje aktualne, a co wymaga ponownej oceny?
```

## A-R2c — runda 2, nowa rozmowa (realistycznie: po miesiącu PM nie ma już kontekstu)

Nowa rozmowa, **bez** materiałów z rundy 1:

```
Pracujemy nad panelem statusu zamówienia w aplikacji (decyzja o budowie zapadła miesiąc temu, jest w realizacji). Doszły nowe materiały. Czy coś z nich wynika dla naszej inicjatywy?

[wklej pliki 09 i 10]
```
