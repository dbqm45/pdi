# 3. Decision Risk Radar (A — główna wartość)

Radar odpowiada na pytanie: **gdzie jakość nadchodzącej decyzji jest zagrożona, jak bardzo i dlaczego?**

Działa na Living Decision Model i zawsze w kontekście konkretnej **następnej decyzji** (`Initiative.next_decision`), np. „czy przechodzimy do estymacji”, „czy uruchamiamy eksperyment”, „czy zatwierdzamy zakres”.

## 3.1. Katalog wzorców ryzyka

Radar nie szuka „błędów w dokumentacji”. Szuka wzorców w **strukturze grafu**, które zapowiadają błędną decyzję. Każdy wzorzec jest jawny, nazwany i testowalny.

| Kod | Wzorzec | Wykrycie w grafie | Przykład |
|---|---|---|---|
| **R1** | Skok od obserwacji do rozwiązania | `Option addresses Problem` bez pośredniej `Hypothesis` o przyczynie lub hipoteza bez `supports` | Wysoki churn → „nowy ekran”, bez ustalenia, gdzie i dlaczego użytkownicy odchodzą |
| **R2** | Hipoteza traktowana jak fakt | `Hypothesis` o krytyczności wysokiej, bez dowodów, a od niej zależą `Decision`/`Requirement` przez `assumes` | „Użytkownicy chcą X” zapisane w wymaganiach jako fakt |
| **R3** | Rozwiązanie celuje w inny problem | `Option addresses` węzeł inny niż ten wspierany przez dowody | Badania: problem zaufania; projekt: redukcja liczby kroków |
| **R4** | Ignorowane dowody przeciwne | `Evidence contradicts` wybranej opcji/hipotezy, bez odniesienia w uzasadnieniu decyzji | Wynik testu A/B przeczący hipotezie pominięty w dokumencie decyzyjnym |
| **R5** | Brak konkurencyjnych wyjaśnień | Krytyczna `Hypothesis` bez `competes_with` przy niejednoznacznych dowodach | Jedno wyjaśnienie spadku konwersji, choć dane pasują do trzech |
| **R6** | Brak alternatyw | `Decision` bez `rejects` przy wysokim koszcie / niskiej odwracalności | Kosztowna przebudowa bez rozważenia prostszej opcji |
| **R7** | Nieweryfikowalny cel | `Goal` bez `SuccessCriterion` lub kryterium niezwiązane z mechanizmem rozwiązania | Cel: „mniej zgłoszeń”, kryterium akceptacji: „panel się wyświetla” |
| **R8** | Wymaganie bez uzasadnienia | `Requirement` bez ścieżki `derives_from` do decyzji lub potrzeby | Pole formularza, którego nikt nie potrafi uzasadnić |
| **R9** | Naruszenie warunku | `violates Constraint` | Strategia „uproszczenie procesu”, wymagania dodają 2 kroki |
| **R10** | Rozbieżne rozumienie pojęć | `diverging_concept` między zespołami | „Aktywny użytkownik” liczony inaczej przez produkt i marketing |
| **R11** | Przestarzałe przesłanki | Dowód, na którym opiera się decyzja, przekroczył `valid_until` lub został podważony przez `Signal` | Decyzja oparta na badaniu sprzed zmiany cennika |
| **R12** | Słaba baza dowodowa | Kluczowy dowód: mała próba, jeden kanał, anegdota, opinia interesariusza | „Trzech dużych klientów prosiło o to” jako jedyna przesłanka |

Katalog jest otwarty — kolejne wzorce dodajemy, gdy pilotaż pokaże powtarzalne klasy błędów, których katalog nie pokrywa.

## 3.2. Ocena: bez jednego wyniku procentowego

Pojedynczy „readiness score” maskuje krytyczne braki wysoką kompletnością. Zamiast tego każde wykryte ryzyko ma **cztery jawne osie**:

| Oś | Pytanie | Skala |
|---|---|---|
| **Wiarygodność** (`credibility`) | Na ile jesteśmy pewni, że to rzeczywisty problem, a nie artefakt ekstrakcji lub różnica perspektyw? | niska / średnia / wysoka |
| **Wpływ na decyzję** (`decision_impact`) | Gdyby ryzyko się zmaterializowało, czy zmieniłoby to decyzję? | nie zmienia / zmienia zakres / zmienia kierunek |
| **Stawka** (`stakes`) | Koszt błędu × nieodwracalność decyzji | niska / średnia / wysoka |
| **Pilność** (`urgency`) | Czy dotyczy *następnej* decyzji, czy późniejszej? | teraz / przed kolejnym etapem / później |

Z tych osi wynika **istotność** (`severity`): `info`, `observation`, `recommendation`, `critical` — mapowana bezpośrednio na poziomy Attention Intelligence ([05](05-attention-intelligence.md)).

Reguła proporcjonalności (kluczowa):

> **Wymagana siła uzasadnienia rośnie ze stawką decyzji.** Ta sama luka dowodowa jest `critical` dla nieodwracalnej przebudowy architektury i `info` dla dwutygodniowego, odwracalnego eksperymentu.

Szkic reguły:

```
jeśli decision_impact == "nie zmienia"            → info  (zapisz, nie pokazuj)
jeśli credibility == niska                         → co najwyżej observation (sformułuj jako pytanie)
jeśli decision_impact == "zmienia kierunek"
   i stakes == wysoka i urgency == teraz           → critical
jeśli decision_impact != "nie zmienia"
   i (stakes >= średnia lub urgency == teraz)      → recommendation
w pozostałych przypadkach                          → observation
```

Wagi i progi są konfigurowalne per organizacja i będą kalibrowane w pilotażu.

## 3.3. Wynik radaru: Decision Readiness Brief

Dla danej następnej decyzji radar zwraca zwięzły dokument o stałej strukturze:

1. **Decyzja, której dotyczy ocena** — i jej stawka (koszt, odwracalność).
2. **Co jest wystarczająco uzasadnione** — z dowodami.
3. **Krytyczne ryzyka** (max 3) — każde: wzorzec, dlaczego, źródła, co by zmieniło ocenę.
4. **Konkurencyjne wyjaśnienia / alternatywy**, których nie rozważono.
5. **Założenie najbardziej „nośne”** — to, które jeśli jest fałszywe, unieważnia decyzję.
6. **Werdykt proporcjonalny**: *można decydować teraz* / *można decydować w węższym zakresie (np. eksperyment)* / *warto odroczyć do zamknięcia luki X*.
7. **Najbardziej wartościowy następny krok** — przekazany do Knowledge Gap Closure ([04](04-knowledge-gap-closure.md)).

Brief zawsze rozróżnia fakt, interpretację, hipotezę i wniosek systemu. Werdykt jest rekomendacją dla właściciela decyzji, nie bramką.

## 3.4. Stress test decyzji

Dla decyzji o wysokiej stawce radar uruchamia dodatkowo adwersaryjny przebieg:

- Jakie założenie, jeśli fałszywe, unieważni decyzję?
- Jakie dowody przemawiają przeciw?
- Czy istnieje prostsza / tańsza alternatywa?
- Czy wybór wynika z potrzeb użytkownika, czy z ograniczeń organizacyjnych?
- Co musiałoby się wydarzyć, żebyśmy wybrali inaczej?

Zabezpieczenie przed „szukaniem sprzeczności na siłę”: każdy zarzut stress testu musi wskazać konkretny węzeł grafu lub konkretny brak, inaczej jest odrzucany przed pokazaniem użytkownikowi. Różnice perspektyw (dwa uprawnione punkty widzenia) są raportowane jako takie, nie jako sprzeczności.

## 3.5. Czego radar świadomie nie robi

- Nie ocenia, czy pomysł jest „dobry” biznesowo — ocenia, czy jest **uzasadniony**.
- Nie wymaga maksymalnej ilości analizy — wymaga analizy proporcjonalnej do stawki.
- Nie raportuje każdej bezproblemowej kontroli.
