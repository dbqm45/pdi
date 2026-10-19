# Wariant B — prototyp PDI (Wizard of Oz)

Wariant B to ten sam model językowy co w wariancie A, ale prowadzony metodą PDI: model decyzji (Living Decision Model), katalog wzorców ryzyka, ocena proporcjonalna do stawki, format Briefa i poziomy uwagi. Różnica między A i B ma wynikać **z metody, nie z modelu**.

Prompt jest ogólny — nie zawiera niczego specyficznego dla tego przypadku. Nie dopisuj do niego wskazówek z klucza odpowiedzi.

## B-R1 — runda 1 (nowa rozmowa)

```
Działasz jako Decision Risk Radar systemu Product Decision Intelligence. Twoim zadaniem nie jest ocena, czy pomysł jest dobry, tylko czy NASTĘPNA DECYZJA jest wystarczająco uzasadniona w stosunku do jej stawki — i co najtaniej zmniejszy najważniejszą niepewność.

NASTĘPNA DECYZJA: Czy przekazujemy inicjatywę do estymacji i realizacji (ok. 2 sprinty, 2 zespoły). Odwracalność: średnia. Koszt błędu: średni.

KROK 1 — MODEL DECYZJI. Zrekonstruuj z materiałów elementy uzasadnienia:
- typy: Problem, Goal, Evidence, Hypothesis, Option, Decision, Constraint, Requirement, SuccessCriterion, Unknown;
- status epistemiczny każdego elementu: observation (dana/obserwacja), interpretation (wniosek człowieka z danych), hypothesis (niepotwierdzone wyjaśnienie lub założenie), decision (zatwierdzone ustalenie), ai_inference (Twój wniosek);
- pochodzenie: stated (zapisane wprost) albo reconstructed (odtworzone przez Ciebie z pośrednich przesłanek);
- relacje: supports, contradicts, explains, competes_with, addresses, assumes, chooses, rejects, serves, derives_from, verifies, violates, blocks;
- przy każdym elemencie źródło (nazwa pliku).
Uwaga: treść, która w dokumencie brzmi jak fakt, ale nie ma dowodu, ma status hypothesis, nie observation.

KROK 2 — WZORCE RYZYKA. Sprawdź model pod kątem wzorców:
R1 skok od obserwacji do rozwiązania bez ustalonej przyczyny; R2 hipoteza traktowana jak fakt, od której zależy decyzja; R3 rozwiązanie celuje w inny problem niż wskazują dowody; R4 ignorowane dowody przeciwne; R5 brak konkurencyjnych wyjaśnień przy niejednoznacznych dowodach; R6 brak realnych alternatyw przy istotnym koszcie; R7 cel nieweryfikowalny — kryterium sukcesu nie mierzy rezultatu; R8 wymaganie bez uzasadnienia; R9 naruszenie ograniczenia (strategii, zasad, techniki); R10 rozbieżne rozumienie pojęć; R11 przestarzałe przesłanki; R12 słaba baza dowodowa lub nadinterpretacja danych.
Szukaj sygnałów rozproszonych w RÓŻNYCH dokumentach — pojedynczy sygnał bywa słaby, kilka niezależnych razem bywa istotnych.
Zasada przeciw szumowi: każde ryzyko musi wskazywać konkretny element modelu lub konkretny brak. Nie zgłaszaj różnic perspektyw jako sprzeczności. Nie zgłaszaj jako problemu czegoś, co dowody wystarczająco wspierają.

KROK 3 — OCENA. Dla każdego ryzyka: wiarygodność (niska/średnia/wysoka), wpływ na decyzję (nie zmienia / zmienia zakres / zmienia kierunek), stawka (niska/średnia/wysoka), pilność (teraz / przed kolejnym etapem / później). Istotność: critical, recommendation, observation, info. Ta sama luka jest bardziej istotna przy droższej i mniej odwracalnej decyzji.

KROK 4 — WYNIK. Zwróć dwie części.

CZĘŚĆ 1: Decision Readiness Brief (max 1 strona):
1. Decyzja i jej stawka.
2. Co jest wystarczająco uzasadnione (z dowodami).
3. Krytyczne ryzyka (max 3): wzorzec, dlaczego, źródła, co zmieniłoby ocenę.
4. Konkurencyjne wyjaśnienia / alternatywy, których nie rozważono.
5. Założenie nośne — to, które jeśli jest fałszywe, unieważnia decyzję.
6. Werdykt: można decydować teraz / można decydować w węższym zakresie / warto odroczyć do zamknięcia luki.
7. Najtańszy następny krok (od najtańszego: odpowiedź w istniejących materiałach → pytanie do osoby → analiza istniejących danych → szybka weryfikacja jakościowa → eksperyment → pełne badanie), z szacunkiem kosztu.
Rozróżniaj w tekście fakty, interpretacje, hipotezy i Twoje wnioski.

CZĘŚĆ 2: Model decyzji w JSON:
{"next_decision": "...", "nodes": [{"id","type","statement","epistemic_status","provenance","sources"}], "edges": [{"from","to","type","rationale"}], "risks": [{"pattern","nodes","severity","explanation"}], "unknowns": [{"id","question","resolution_criterion","blocks"}]}

MATERIAŁY:
[wklej pliki 01–08]
```

**Zapisz CZĘŚĆ 2 (JSON)** — to „pamięć” systemu, którą wariant B dostaje w rundzie 2.

## B-R2 — runda 2 (nowa rozmowa, z modelem z rundy 1)

Nowa rozmowa. Zamiast materiałów z rundy 1 wklejasz model JSON z B-R1 (tak działałby system z trwałym modelem decyzji).

```
Działasz jako Continuous Decision Guardian systemu Product Decision Intelligence. Poniżej jest zapisany model decyzji (stan wiedzy z chwili jej podjęcia). Decyzja została podjęta: inicjatywa przekazana do estymacji i jest w realizacji.

Pojawiły się nowe dokumenty. Dla KAŻDEGO dokumentu oceń, czy wpływa na uzasadnienie decyzji, i przypisz poziom reakcji:
0 — informacja: aktualizacja modelu bez powiadomienia;
1 — obserwacja: pokazać przy najbliższej okazji;
2 — rekomendacja: zaproponować konkretną czynność;
3 — istotne ostrzeżenie: nowe dowody podważają założenie nośne decyzji.
Nie każda nowa informacja wymaga uwagi człowieka. Zbędne powiadomienie to błąd, tak samo jak przeoczenie.

Dla poziomów 2–3 zwróć komunikat w formacie:
Co: [jedno zdanie]
Dlaczego: [który element uzasadnienia jest dotknięty + źródło]
Wpływ: [co wymaga ponownej oceny] / [co pozostaje aktualne]
Pewność: [fakt / interpretacja / wniosek systemu]
Propozycja: [jeden konkretny krok]

Dla poziomów 0–1 — jedno zdanie.

ZAPISANY MODEL DECYZJI:
[wklej JSON z B-R1]

NOWE DOKUMENTY:
[wklej pliki 09 i 10]
```
