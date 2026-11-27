---
description: Zapisz decyzję z bieżącej rozmowy w rejestrze pdi (szkic → zatwierdzenie w konsoli → zapis)
argument-hint: "[opcjonalnie: której decyzji dotyczy zapis]"
allowed-tools: Bash(git rev-parse --show-toplevel), mcp__pdi__find_decisions, mcp__pdi__get_decision, mcp__pdi__present_decision_draft, mcp__pdi__record_decision
---

Zapisz w rejestrze pdi decyzję z tej rozmowy. $ARGUMENTS

1. **Ustal, która decyzja.** Jeśli w rozmowie zapadło kilka decyzji, a argument nie wskazuje jednej, wypisz je
   w punktach i zapytaj, którą zapisać. Jeśli nic nie zostało zdecydowane (tylko omówione), powiedz to i nie zapisuj.
2. **Ustal projekt:** nazwa bieżącego repo (`basename` z `git rev-parse --show-toplevel`; poza repo — nazwa
   katalogu roboczego). Jeśli decyzja dotyczy innego projektu albo jest ogólna (np. sposób pracy), użyj tej nazwy
   albo pomiń `project`. Pokaż projekt w szkicu — człowiek może go zmienić.
3. **Sprawdź wcześniejsze decyzje:** `find_decisions` z 2–4 słowami kluczowymi tematu (bez filtra projektu —
   decyzje z innych projektów też mogą być ważne). Jeśli nowa decyzja zmienia
   wcześniejszą, zaproponuj zastąpienie (`supersedes: DEC-n` w szkicu) zamiast nowego wpisu.
4. **Przygotuj szkic** wyłącznie z treści rozmowy:
   - `statement` — co zdecydowano, jedno zdanie; `why` — 1–5 zdań uzasadnienia;
   - `options` — rozważane opcje, jeśli padły, z oznaczeniem wybranej;
   - `evidence` — z `epistemic_status`: `observation` (fakt, liczba, cytat ze źródła), `interpretation`,
     `hypothesis` albo `ai_inference` (Twój wniosek, nie człowieka);
   - `assumptions` — założenia, na których decyzja stoi; `load_bearing: true`, gdy ich upadek zmienia decyzję,
     `invalidated_if` — konkretny sygnał, że założenie przestało być prawdziwe;
   - `consequences` — skutki z `effect` `good` / `bad` / `neutral`, i `confirmation` — jak sprawdzić, że decyzję
     wykonano (`how`, opcjonalnie `kind` i `ref`, np. id testu) — tylko jeśli padły w rozmowie;
   - `kind`, `tags`, `dependencies`, `success_metric`, `review_by`, `links` — tylko jeśli wynikają z rozmowy;
   - `source`: `{kind: "claude-cli", excerpt: <krótki cytat z rozmowy, w którym zapadła decyzja>}`;
     `drafted_by: "ai"`.
   **Nie dopisuj uzasadnień, liczb ani założeń, których nie było w rozmowie.** Jeśli dla decyzji typu
   `product` lub `intent` brakuje założenia nośnego albo uzasadnienia — zadaj najwyżej 2 krótkie pytania.
5. **Pokaż szkic zwięźle** (jedna linia na pole, bez pustych pól) i zapytaj: „Wystawić do zatwierdzenia? (tak /
   popraw: …)”. Poprawki nanieś przed wystawieniem.
6. **Wystaw szkic** przez `present_decision_draft` (z `supersedes`, gdy zastępuje decyzję). Podaj `draft_edited`:
   `false`, gdy człowiek przyjął Twój szkic bez zmian, `true`, gdy cokolwiek poprawił — z tego pdi liczy, które typy
   decyzji są gotowe do automatyzacji (`autonomy_report`). Jeśli decyzja ma znany typ (katalog w `autonomy_report`,
   np. `review.light`), podaj też `decision_type`. Podaj człowiekowi `approve_url` (albo: konsola pdi, `sdlc open`
   → Drafts → DRF-n) i poczekaj. **Zatwierdza tylko człowiek, w konsoli — „tak” w czacie nie wystarcza.**
7. **Zapisz** przez `record_decision` z `draft_id` i `sha256`, gdy człowiek powie, że zatwierdził. Odrzucenie wraca
   z powodem — popraw szkic według niego i wystaw nowy. Zgoda jest ważna godzinę.
8. Odpowiedz jedną linią: `Zapisano DEC-nnnn: <statement>` (przy duplikacie: „już zapisane jako DEC-nnnn”).
