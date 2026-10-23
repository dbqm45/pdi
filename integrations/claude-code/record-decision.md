---
description: Zapisz decyzję z bieżącej rozmowy w rejestrze pdi (szkic → zatwierdzenie → zapis)
argument-hint: "[opcjonalnie: której decyzji dotyczy zapis]"
allowed-tools: Bash(git rev-parse --show-toplevel), mcp__pdi__find_decisions, mcp__pdi__get_decision, mcp__pdi__record_decision, mcp__pdi__supersede_decision
---

Zapisz w rejestrze pdi decyzję z tej rozmowy. $ARGUMENTS

1. **Ustal, która decyzja.** Jeśli w rozmowie zapadło kilka decyzji, a argument nie wskazuje jednej, wypisz je
   w punktach i zapytaj, którą zapisać. Jeśli nic nie zostało zdecydowane (tylko omówione), powiedz to i nie zapisuj.
2. **Ustal projekt:** nazwa bieżącego repo (`basename` z `git rev-parse --show-toplevel`; poza repo — nazwa
   katalogu roboczego). Jeśli decyzja dotyczy innego projektu albo jest ogólna (np. sposób pracy), użyj tej nazwy
   albo pomiń `project`. Pokaż projekt w szkicu — człowiek może go zmienić.
3. **Sprawdź wcześniejsze decyzje:** `find_decisions` z 2–4 słowami kluczowymi tematu (bez filtra projektu —
   decyzje z innych projektów też mogą być ważne). Jeśli nowa decyzja zmienia
   wcześniejszą, zaproponuj zastąpienie (`supersede_decision`) zamiast nowego wpisu.
4. **Przygotuj szkic** wyłącznie z treści rozmowy:
   - `statement` — co zdecydowano, jedno zdanie; `why` — 1–5 zdań uzasadnienia;
   - `options` — rozważane opcje, jeśli padły, z oznaczeniem wybranej;
   - `evidence` — z `epistemic_status`: `observation` (fakt, liczba, cytat ze źródła), `interpretation`,
     `hypothesis` albo `ai_inference` (Twój wniosek, nie człowieka);
   - `assumptions` — założenia, na których decyzja stoi; `load_bearing: true`, gdy ich upadek zmienia decyzję,
     `invalidated_if` — konkretny sygnał, że założenie przestało być prawdziwe;
   - `kind`, `tags`, `dependencies`, `success_metric`, `review_by`, `links` — tylko jeśli wynikają z rozmowy;
   - `source`: `{kind: "claude-cli", excerpt: <krótki cytat z rozmowy, w którym zapadła decyzja>}`;
     `drafted_by: "ai"`.
   **Nie dopisuj uzasadnień, liczb ani założeń, których nie było w rozmowie.** Jeśli dla decyzji typu
   `product` lub `intent` brakuje założenia nośnego albo uzasadnienia — zadaj najwyżej 2 krótkie pytania.
5. **Pokaż szkic zwięźle** (jedna linia na pole, bez pustych pól) i zapytaj: „Zapisać? (tak / popraw: …)”.
6. **Zapisz dopiero po wyraźnym „tak”** przez `record_decision` (albo `supersede_decision`). Poprawki nanieś
   i zapisz w jednym kroku, bez ponownego pytania, chyba że poprawka zmienia treść decyzji.
7. Odpowiedz jedną linią: `Zapisano DEC-nnnn: <statement>` (przy duplikacie: „już zapisane jako DEC-nnnn”).
