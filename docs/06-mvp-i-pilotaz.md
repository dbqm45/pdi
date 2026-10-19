# 6. MVP i protokół pilotażu

## 6.1. Zakres MVP

Jeden cykl decyzyjny: **od pojawienia się inicjatywy do decyzji o dalszym postępowaniu.**

MVP musi wykonać cztery zadania:

1. **Ingestia** — przyjąć materiały inicjatywy z kilku źródeł (w MVP: upload plików / eksport: opis inicjatywy, badania, feedback, dokumenty biznesowe, wymagania, opis designu, notatki z decyzji).
2. **Rekonstrukcja** — zbudować Living Decision Model inicjatywy z oznaczeniem statusu epistemicznego i pochodzenia każdego elementu; pozwolić człowiekowi potwierdzić/poprawić rekonstrukcję.
3. **Radar + KGC** — wygenerować Decision Readiness Brief dla wskazanej następnej decyzji i zaproponować najbardziej wartościowy krok (z przeszukaniem istniejących materiałów jako szczeblem 0).
4. **Reakcja na zmianę** — po dodaniu nowego materiału ocenić, czy podważa on istotne ustalenie, i odpowiednio do poziomu istotności zareagować (lub nie).

Poza zakresem MVP: integracje na żywo (Jira, Confluence, Figma, Amplitude…), monitoring ciągły, poziom portfolio, wysyłanie wiadomości do ludzi, uczenie na wynikach.

## 6.2. Architektura MVP (szkic)

```
 Materiały ──► Ekstrakcja (LLM, ustrukturyzowane wyjście wg schematu LDM)
                    │
                    ▼
            Living Decision Model (graf + historia wersji)
                    │
       ┌────────────┼──────────────────┐
       ▼            ▼                  ▼
  Detektory     Stress test       Wyszukiwanie w źródłach
  wzorców R1–R12  (LLM, z wymogiem   (szczebel 0 KGC)
  (reguły na grafie   wskazania węzła)
   + ocena LLM)
       └────────────┬──────────────────┘
                    ▼
     Ocena osi → istotność → Attention policy
                    ▼
     Decision Readiness Brief / komunikat
```

Zasada konstrukcyjna: **wykrywanie wzorców w możliwie dużej części deterministyczne, na grafie**; LLM odpowiada za ekstrakcję, ocenę semantyczną (np. „czy ta opcja rzeczywiście adresuje tę hipotezę”) i sformułowanie wyniku. Dzięki temu każde ostrzeżenie da się prześledzić do węzłów i krawędzi, a jakość da się testować regresyjnie.

## 6.3. Protokół pilotażu (etap 0 — retrospektywny)

**Cel:** sprawdzić, czy system wykrywa istotne problemy decyzyjne, zanim zrobi się to kosztowne — zanim zbudujemy cokolwiek więcej.

**Materiał:** 8–15 zakończonych inicjatyw z dostępnymi materiałami z chwili decyzji, znaną historią decyzji i obserwowalnym rezultatem. Celowo mieszanka: inicjatywy udane, nieudane i takie, w których decyzja została później zmieniona.

**Procedura:**

1. Odtworzyć **stan materiałów z chwili decyzji** (bez późniejszych dokumentów — inaczej test jest bezwartościowy).
2. System generuje Brief dla tej decyzji.
3. Niezależnie 2–3 doświadczonych PM/UX/analityków ocenia te same materiały (bez dostępu do wyniku systemu ani do późniejszego rezultatu).
4. Panel oceniający — **zaślepiony** co do źródła zarzutu (system vs. ekspert) — klasyfikuje każdy zarzut: *istotny i trafny / trafny, ale nieistotny / nietrafny*.
5. Dopiero potem porównanie z faktycznym przebiegiem: czy istotne zarzuty pokrywają się z tym, co rzeczywiście poszło źle?

**Kontrola hindsight bias:** oceniający w kroku 4 nie znają rezultatu inicjatywy. Ocena trafności „ex post” (krok 5) jest raportowana osobno.

## 6.4. Metryki

| Metryka | Definicja | Próg sukcesu (wstępny, do dyskusji) |
|---|---|---|
| **Wartość dodana** (główna) | Odsetek inicjatyw, w których system wskazał ≥1 istotny problem nieznaleziony przez ekspertów | ≥ 30% |
| Precyzja | Odsetek zarzutów poziomu 2–3 ocenionych jako istotne i trafne | ≥ 60% |
| Pokrycie | Odsetek istotnych problemów (znalezionych przez kogokolwiek) wskazanych przez system | ≥ 70% |
| Trafność ex post | Odsetek inicjatyw nieudanych/zmienionych, w których przyczyna była w krytycznych ryzykach Briefa | raportowana, bez progu (mała próba) |
| Koszt uwagi | Liczba komunikatów 2–3 na inicjatywę i czas ich przejrzenia | ≤ 5 komunikatów, ≤ 15 min |
| Trafność rekonstrukcji | Odsetek zrekonstruowanych hipotez/założeń potwierdzonych przez autorów | ≥ 70% |

Jeśli wartość dodana i precyzja nie przekroczą progów, nie przechodzimy do etapu 1 — wracamy do katalogu wzorców i reguł oceny.

## 6.5. Etap 1 — pilotaż na żywo (po pozytywnym etapie 0)

2–3 zespoły, 6–8 tygodni, bieżące inicjatywy. Dodatkowe metryki:

- czas od wykrycia luki do jej rozstrzygnięcia (lub świadomej akceptacji ryzyka),
- odsetek rekomendacji zrealizowanych,
- odsetek decyzji zmienionych / zawężonych w wyniku pracy z systemem (sama zmiana nie jest celem — oceniamy ją jakościowo),
- powroty do systemu bez przymusu (proxy dla wartości),
- reakcje na komunikaty (*trafne / nietrafne / już wiedziałem / nieistotne*).

Główny miernik długoterminowy: **odsetek istotnych problemów decyzyjnych wykrytych przed podjęciem kosztownego lub trudno odwracalnego działania.** Szybka korekta po nowych dowodach to oznaka dobrego procesu, nie porażki.
