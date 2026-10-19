# Test v2: pamięć uzasadnienia decyzji

> **Wykonano 2026-10-19 — [raport z wynikami](wyniki/raport.md).** K1 spełnione, K2–K4 niespełnione. Pamięć daje przewagę tylko przy sygnale zależnym od liczb w uzasadnieniu (S1: 3/3 vs 0/3); szum ogranicza metoda, nie pamięć.

Druga wersja testu praktycznego. Powstała na podstawie [wyników v1](../status-zamowienia/wyniki/raport.md). Test v1 pokazał, że jednorazowa analiza i reakcja na nowy dokument w tej samej rozmowie nie odróżniają PDI od ogólnego asystenta AI. Jedynym kandydatem na wyróżnik okazała się **pamięć uzasadnienia decyzji w czasie**. Wersja 2 sprawdza wyłącznie ten wyróżnik.

## Co test ma na celu

Jedno główne pytanie:

> **Czy system, który pamięta, *dlaczego* podjęto decyzje, zauważa informacje podważające te decyzje — także wtedy, gdy informacja przychodzi z innego miejsca w firmie, nie wspomina decyzji i ginie w strumieniu nieistotnych dokumentów — i robi to wyraźnie lepiej niż ogólny asystent AI?**

Rozbite na cztery pytania szczegółowe:

| # | Pytanie | Porównanie | Po co |
|---|---|---|---|
| 1 | Czy prototyp PDI w ogóle wykrywa ukryte sygnały, nie zalewając PM-a fałszywymi alarmami? | B względem klucza | Warunek wstępny |
| 2 | **Czy pamięć daje przewagę nad realistycznym użyciem asystenta?** PM pamięta nazwy i terminy swoich inicjatyw, ale nie wkleja co tydzień ich uzasadnień | B vs **A-fresh** | Główna hipoteza wartości po v1 |
| 3 | **Czy przewaga wynika z pamięci, a nie z samej metody** (katalog wzorców, poziomy, format)? | B vs **A+** (metoda bez pamięci) | Czy budować system z trwałym modelem, czy wystarczy dobry prompt |
| 4 | Czy pamięć zmniejsza szum (fałszywe alarmy, duplikaty)? | B vs A-fresh, A+ | Obietnica „nie przeszkadza” |

Dodatkowo raportujemy **A-ctx**, czyli najlepszy możliwy przypadek DIY: jedna rozmowa prowadzona przez miesiąc z pełnym kontekstem. Pokazuje, ile z wartości PDI PM uzyskałby sam, gdyby był zdyscyplinowany. Nie ma dla niego progu.

## Czym v2 różni się od v1

| Słabość v1 | Zmiana w v2 |
|---|---|
| Nowy dokument sam wyjaśniał swój związek z decyzją | Żaden z zaszytych dokumentów nie wspomina decyzji, której dotyczy. Związek widać tylko wtedy, gdy zna się jej uzasadnienie (np. aneks do umowy z przewoźnikiem a rachunek progu darmowej dostawy) |
| Jedna decyzja, 10 dokumentów — wszystko mieści się w jednej rozmowie | 3 decyzje i strumień 28 dokumentów w 4 tygodniach; 3 sygnały, 1 dokument potwierdzający, 4 pułapki, 1 duplikat, 18 dokumentów szumu |
| Nie dało się oddzielić wpływu metody od wpływu pamięci | Wariant A+ (metoda bez pamięci) |
| Klucz dawał pełne punkty za samo powiązanie dokumentu z inicjatywą | Pełne punkty tylko za nazwanie podważonego założenia lub warunku decyzji |
| Brak oceny człowieka | Kalibracja: autor ocenia ręcznie co najmniej 1 przebieg każdego wariantu |

## Profil sygnałów — ile każdy wymaga pamięci

Nie wszystkie sygnały da się jednakowo wykryć bez pamięci. Profil określono przed testem, żeby wynik dało się czytać po sygnałach, a nie tylko po sumie.

| Sygnał | Co trzeba wiedzieć, żeby dostać pełne punkty | Zależność od pamięci |
|---|---|---|
| S1 aneks → D1 | Że wynik decyzji to tylko ok. +22,6 tys. zł/mies. przy koszcie paczki 11,80 zł | **wysoka** — bez rachunku z T0 można najwyżej powiedzieć „wzrosną koszty” |
| S2 INT-233 → D2 | Że sens panelu zależał od aktualności zdarzeń od przewoźnika Y | **średnia** — częściowo do wywnioskowania z samej nazwy „panel statusu” |
| S3 brief CZ → D3 | Że checkout jest wspólny dla wszystkich rynków | **niska–średnia** — konflikt „pobranie 30% w CZ” vs „wycofanie pobrania” widać bez T0, ale wspólny checkout jest tylko w T0 |

Oczekiwanie: jeśli pamięć ma znaczenie, różnica B vs A-fresh / A+ będzie największa dla S1. Raport podaje wyniki po sygnałach.

## Czego test NIE dowodzi

- Wartości dla PM-a w prawdziwej organizacji — przypadek jest nadal syntetyczny i zaprojektowany przez autora metody.
- Że PM-owie realnie tracą kontekst decyzji. Test zakłada, że tak (wariant A-fresh). Jak często to się zdarza, trzeba sprawdzić w wywiadach z design partnerami.
- Jakości przyszłego produktu — B to nadal prompty, a „pamięć” to plik JSON przekazywany między rozmowami.

## Struktura

```
materialy/t0/            5 dokumentów: portfel inicjatyw, 3 notatki z decyzji, kontekst organizacji
materialy/tydzien-1..4/  po 7 dokumentów na tydzień (kolejność wymieszana)
prompty/warianty.md      prompty czterech wariantów
prompty/sedzia.md        instrukcja dla sędziego LLM
narzedzia/zbuduj_prompty.py  składa prompty z materiałów
klucz-odpowiedzi.md      NIE WKLEJAĆ do testowanych narzędzi
karta-oceny.md           jedna karta na przebieg
wyniki/                  surowe odpowiedzi, oceny, raport
```

## Przebieg

Każdy wariant uruchamiamy w **3 powtórzeniach**, na tym samym modelu.

1. Złożenie promptów: `python3 narzedzia/zbuduj_prompty.py <katalog>`.
2. **A-ctx:** jedna rozmowa na powtórzenie: T0, potem T1–T4 jako kolejne wiadomości w tej samej rozmowie.
3. **A-fresh** i **A+:** dla każdego tygodnia osobna, nowa rozmowa.
4. **B:**
   - B-T0 w nowej rozmowie: odpowiedź to model decyzji (JSON);
   - dla tygodnia N: `python3 narzedzia/zbuduj_prompty.py <katalog> --b-tydzien N --model <odpowiedź B-T0> --historia <odpowiedzi B-T1..T(N-1)>`, potem nowa rozmowa.
5. Zapis wszystkich odpowiedzi do `wyniki/surowe/<wariant>-<nr>-T<n>.md`.
6. **Ocena:** sędzia LLM na każdy przebieg (12 przebiegów) według [prompty/sedzia.md](prompty/sedzia.md). **Kalibracja:** autor ocenia ręcznie 4 przebiegi (po jednym z każdego wariantu) i liczy zgodność z sędzią dla sygnałów i FA.
7. Raport według [wyniki/raport-szablon.md](wyniki/raport-szablon.md).

**Koszt:** ok. 54 rozmowy generujące (B: 15, A-ctx: 15 wiadomości w 3 rozmowach, A-fresh: 12, A+: 12) + 12 ocen sędziego. Przy uruchomieniu przez agentów ok. 1–1,5 h, ręcznie ok. 5–6 h.

## Kryteria (zapisane przed testem)

Sygnały: max 6 na przebieg. Średnie liczone z 3 powtórzeń.

| Kryterium | Pytanie | Spełnione, jeśli… |
|---|---|---|
| **K1 — B działa** | 1 | B: ≥ 4/6 pkt za sygnały w co najmniej 2 z 3 przebiegów **i** średnio ≤ 2 FA na przebieg (4 tygodnie) |
| **K2 — pamięć > brak pamięci** | 2 | średnia sygnałów B − średnia A-fresh ≥ 2 pkt |
| **K3 — pamięć, nie metoda** | 3 | średnia sygnałów B − średnia A+ ≥ 1,5 pkt |
| **K4 — mniej szumu** | 4 | średnie (FA + DUP) w B ≤ średnie w A-fresh i ≤ w A+ **oraz** średnie obciążenie B ≤ 5 pozycji w 4 tygodniach |

### Jak czytać wynik

| Wynik | Interpretacja | Co dalej |
|---|---|---|
| K1 niespełnione | Prototyp nie radzi sobie z ukrytymi sygnałami nawet z pamięcią | Poprawić model decyzji (B-T0) i prompt Guardiana, powtórzyć; nie budować MVP |
| K1, K2, K3 spełnione | **Pamięć uzasadnienia jest realnym wyróżnikiem**, którego nie zastąpi dobry prompt | Propozycja wartości = pamięć i obrona uzasadnienia decyzji w czasie; przepisać propozycję dla PM-ów; MVP wokół trwałego modelu i monitorowania |
| K2 spełnione, K3 niespełnione | Przewagę daje metoda (katalog, poziomy), nie pamięć | Wartość może być w formie „dobrego promptu / skilla”, a nie systemu — słaby argument za produktem; raczej narzędzie wewnętrzne lub skill |
| K2 niespełnione | Ogólny asystent bez pamięci wiąże ukryte sygnały z decyzjami równie dobrze | Hipoteza pamięci obalona na tym przypadku; zatrzymać rozwój PDI jako produktu i wrócić do pytania o problem |
| K4 niespełnione przy spełnionych K1–K3 | Pamięć pomaga wykrywać, ale nie filtrować | Dopracować politykę uwagi przed pokazaniem partnerom |
| A-ctx ≈ B | Wartość zależy od tego, czy PM sam utrzymuje kontekst przez tygodnie | Pytanie do wywiadów: jak często PM-owie to robią; jeśli rzadko — argument za PDI |
