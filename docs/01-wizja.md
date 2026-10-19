# 1. Wizja i pozycjonowanie

## Definicja

**Product Decision Intelligence** to system wspierający jakość decyzji produktowych poprzez łączenie dowodów z wielu źródeł, rekonstruowanie uzasadnienia decyzji, identyfikowanie istotnych sprzeczności i niewiadomych oraz wskazywanie działań, które ograniczają ryzyko podjęcia błędnej decyzji.

Celem jest umożliwienie organizacji rozpoznania i rozwiązania istotnych problemów na możliwie wczesnym etapie — zanim przełożą się na kosztowne zmiany, niepotrzebną pracę lub wdrożenie niewłaściwego rozwiązania.

## Pytanie, na które odpowiada system

Typowe narzędzie odpowiada na pytanie: *„Jak przygotować tę inicjatywę?”*

PDI odpowiada na pytanie:

> *„Czy ta inicjatywa jest wystarczająco dobrze rozpoznana, uzasadniona i spójna, żeby podjąć **kolejną konkretną decyzję** — a jeśli nie, co konkretnie musimy zrobić, aby to zmienić?”*

Kluczowe są słowa „kolejną konkretną decyzję”. Gotowość nie jest cechą inicjatywy, tylko relacją między stanem wiedzy a decyzją, którą chcemy teraz podjąć. Ta sama inicjatywa może być gotowa do eksperymentu i jednocześnie niegotowa do estymacji pełnej implementacji.

## Kompletność ≠ jakość decyzji

Organizacja może mieć kompletną dokumentację, dopracowane makiety i szczegółowe wymagania — i jednocześnie nie mieć podstaw, by uzasadnić samo rozwiązanie. PDI mierzy jakość **uzasadnienia**, nie kompletność **artefaktów**.

## Trzy komponenty rdzenia

```
                ┌──────────────────────────────────────────┐
  Użytkownik ◄──┤  A. Decision Risk Radar  (wartość)        │  „gdzie decyzja jest zagrożona?”
                ├──────────────────────────────────────────┤
  Użytkownik ◄─►│  B. Knowledge Gap Closure (działanie)     │  „co zrobić, żeby to zmienić?”
                ├──────────────────────────────────────────┤
                │  C. Decision Integrity Graph (fundament)  │  „co wiemy, skąd, co od czego zależy?”
                │     = Living Decision Model               │
                └──────────────────────────────────────────┘
                         ▲                      ▲
             Tryb A: Active Copilot   Tryb B: Continuous Guardian
             (na żądanie, prowadzi)   (w tle, reaguje na zmiany)
                         └──── Attention Intelligence ────┘
                               (czy, kiedy i jak się odezwać)
```

- **Użytkownik kupuje A** — wczesne wykrycie ryzyka błędnej decyzji.
- **B sprawia, że A nie kończy się na raporcie** — luka jest prowadzona aż do rozstrzygnięcia.
- **C sprawia, że A i B są wiarygodne** — każde ostrzeżenie ma pochodzenie, każda rekomendacja ma uzasadnienie w grafie.
- **Oba tryby pracy (Copilot i Guardian) korzystają z tego samego modelu** — nie budujemy dwóch produktów ani dwóch obrazów sytuacji.

## Czym PDI nie jest

- Nie jest systemem zatwierdzania (nie blokuje, nie nadaje statusu „gotowe”).
- Nie jest generatorem treści (PRD, user stories, podsumowań) — może je czytać, nie jest to jego wartość.
- Nie jest narzędziem do traceability wymagań w sensie compliance (to robi np. Jama Connect).
- Nie jest repozytorium insightów (to robią narzędzia discovery, np. Productboard, Dovetail).

## Hipoteza wartości (do weryfikacji)

> Istnieje przestrzeń dla systemu, który w sposób ciągły pomaga organizacji utrzymywać jakość uzasadnienia decyzji — łącząc (1) proaktywne rozpoznawanie ryzyka decyzyjnego, (2) aktywne zamykanie luk w wiedzy i (3) ciągłą ocenę aktualności uzasadnienia.

Poszczególne zdolności mają odpowiedniki na rynku. Hipoteza dotyczy ich **połączenia wokół decyzji jako obiektu centralnego**. Weryfikacja: [MVP i pilotaż](06-mvp-i-pilotaz.md), [ryzyka](07-ryzyka-i-otwarte-pytania.md).

## Ścieżka rozwoju

| Etap | Zakres | Warunek przejścia |
|---|---|---|
| 0. Pilotaż retrospektywny | Analiza zakończonych inicjatyw, porównanie z ekspertami | System wykrywa istotne problemy przeoczone przez ludzi przy akceptowalnym odsetku fałszywych alarmów |
| 1. Copilot | Aktywna praca nad bieżącymi inicjatywami (A+B na żądanie) | Zespoły wracają do systemu bez przymusu; rekomendacje są realizowane |
| 2. Guardian | Monitoring źródeł i ocena wpływu zmian na zatwierdzone decyzje | Powiadomienia poziomu 2–3 są w większości uznawane za trafne |
| 3. Organizational DI | Wzorce na poziomie portfolio, uczenie na wynikach decyzji | Dostępne wiarygodne dane o rezultatach wdrożeń |
