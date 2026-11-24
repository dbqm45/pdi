# DV1 — bramki do uproszczenia (AI Process Challenger + Deployment Policy Advisor)

Stan: 2026-11-24. Krok DV1 z `docs/plan-budowy-suity.md` §3d. Zależy od DV4 (#207: `pdi.delays`, czasy na bramkach).

## Cel
Proces sam wskazuje kroki, które nie zmniejszają ryzyka: bramka, która w ostatnich decyzjach prawie nigdy nie
zatrzymała zmiany, dostaje w skrzynce szkic decyzji „uprościć?”. Decyduje człowiek; pdi niczego nie zmienia samo.

## Ustalenia
1. **Pomiar** (`pdi.process.report`, z osi zmian DV4): dla każdej bramki — decyzje w ostatnich N (okno) według chwili
   decyzji, ile przeszło (`approved`), ile zatrzymało zmianę (`changes_requested`, `rejected`), udział „bez uwag”,
   mediana czekania. Okno i próg jak licznik akceptacji szkiców (kontrakt, `autonomy.lower_when`: 30 decyzji, 95%).
2. **Rekomendacja:** `challenge`, gdy okno pełne i udział „bez uwag” ≥ progu; inaczej `keep` z powodem (za mało
   danych, bramka zatrzymuje zmiany). Bramka chroniona (B5 — wydanie na PROD, typ chroniony `release.go`, DA2) zawsze
   `keep`.
3. **Skrzynka:** `Inbox.propose_process_changes()` tworzy pozycje `kind: process` („Bramka B1: 30/30 bez uwag,
   mediana czekania 4 h — uprościć: obniżyć poziom albo usunąć krok?”), najwyżej jedną otwartą na bramkę; po
   decyzji kolejna propozycja tej bramki dopiero po pełnym nowym oknie decyzji. Outcome `approved` albo `rejected`;
   decyzja trafia do rejestru (`kind: process`, typ `process.gate_change`, pomiar jako dowód). Zmiana samego
   przebiegu (`flow.GATES`, operating model) to osobna praca po decyzji.
4. **Gdzie widać:** narzędzia MCP `process_report` (odczyt) i `propose_process_changes`; na stronie „Przepływ”
   kolumna „zatrzymała” w tabeli bramek.

## Kolejność (TDD)
1. Testy (czerwone) `tests/test_process.py`: pomiar w oknie, próg, za mało danych, bramka chroniona, propozycje
   w skrzynce bez duplikatów i bez powtórki przed nowym oknem, decyzja w rejestrze; MCP; kolumna na stronie.
2. Kod, potem bramki: `uv run pytest`, ruff, `mypy --strict src`, Python 3.11.
