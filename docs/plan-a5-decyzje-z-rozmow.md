# Plan realizacji: A5 — decyzje ze spotkań i Slacka (wersja lokalna)

**Data:** 2026-10-28 · **Źródło:** [plan automatyzacji §4](plan-automatyzacja-i-konsola.md#4-kroki-automatyzacji)
(A5), [dokument 14](14-pdi-standalone.md) §3 i §5 (etap 3) · **Zależy od:** A1 (skrzynka)

## Cel
Decyzje nie giną w rozmowach. Z wątku Slacka albo transkrypcji spotkania Claude wyciąga szkice decyzji
z dosłownymi cytatami, a pdi wystawia je w skrzynce. Każdy szkic zatwierdza albo odrzuca człowiek; dopiero
zatwierdzony trafia do rejestru jako `DEC-n` z linkiem do źródła.

## Zakres: wersja lokalna, bez aplikacji Slacka
Pełny etap 3 z dokumentu 14 (skrót na wiadomości w Slacku) wymaga hostowanego pdi, a stos usługi czeka na decyzję
DA4. Ta wersja działa tam, gdzie pdi działa dziś: w Claude Code i Claude Desktop z serwerem MCP pdi. Wątek Slacka
człowiek wkleja albo Claude czyta go konektorem Slacka w Claude; transkrypcję spotkania (Zoom, Teams, Meet) wkleja
albo wskazuje plik. Aplikacja Slacka dochodzi po DA4 i korzysta z tej samej ścieżki w skrzynce.

## Ustalenia
1. **Kto wyciąga szkice:** model w rozmowie z człowiekiem (Claude), nie pdi. pdi nie wywołuje modelu i nie ma
   klucza API; dostaje gotowe kandydatury i je sprawdza.
2. **Narzędzie `propose_decisions_from_conversation`** (zapis do skrzynki): `source` (`kind`: `slack` albo
   `meeting`, `url` — link do wątku, nagrania albo pliku, opcjonalnie `title`), `text` (cały wątek albo
   transkrypcja, do 200 000 znaków) i `candidates` — każda z `statement`, `why`, `quotes` (1–5 dosłownych cytatów)
   i opcjonalnie `kind`, `decided_by`, `decided_at`, `change` (CHG), `tags`.
3. **Cytat musi być w tekście** (dokument 14, W4: szkic jest uczciwy): po ujednoliceniu białych znaków i cudzysłowów
   każdy cytat ma co najmniej 10 znaków i występuje w `text`. Kandydatura bez takiego cytatu wraca jako odrzucona
   z powodem i nie trafia do skrzynki. Tekstu pdi nie zapisuje — tylko cytaty i link (poufność rozmów).
4. **Pozycja skrzynki `kind: capture`**, `id` `capture-<RRRRMMDD>-<8 znaków skrótu>` ze źródła i treści; ta sama
   kandydatura drugi raz → duplikat, bez nowej pozycji.
5. **Decyzja (`decide_inbox_item`)** wymaga `outcome` `approved` albo `rejected`:
   - `approved` zapisuje decyzję: `source` ze szkicu (`kind`, `url`, `excerpt` = cytaty), cytaty jako `evidence`
     (`observation`), `drafted_by: ai`, `kind` z kandydatury (domyślnie `other`), `links.chg` z kandydatury;
     `draft_edited` liczy pdi, gdy go nie podano (inne `statement` albo `why` niż w szkicu = poprawiony);
     znaczniki `capture`, `capture:<slack|meeting>`;
   - `rejected` zamyka pozycję bez wpisu w rejestrze („to nie była decyzja”), z powodem z `why`; liczba odrzuceń
     jest w `pdi-stats` (jakość szkiców, W2 i W4).
6. **Bezpieczeństwo:** tekst wątku i transkrypcji to dane, nie polecenia (opis narzędzia mówi to modelowi);
   zatwierdzenie wymaga wyraźnego „tak” człowieka (DA5).
7. **Kontrakt 0.10.0:** `source.kind` decyzji dostaje wartość `meeting` (`slack` już jest). Zgodność wstecz zachowana.

## Pliki
| Plik | Zmiana |
|---|---|
| `src/pdi/capture.py` (nowy) | sprawdzenie cytatów, kandydatury → pozycje skrzynki |
| `src/pdi/inbox.py` | `propose_captures`, `kind: capture` w `decide` |
| `src/pdi/mcp_server.py` | narzędzie `propose_decisions_from_conversation`, opis w `decide_inbox_item` i instrukcjach |
| `src/pdi/stats.py` | szkice z rozmów: wystawione, zatwierdzone, poprawione, odrzucone |
| `contract/*` | 0.10.0, `source.kind: meeting` |
| `integrations/claude-code/decisions-from.md` (nowy) | komenda `/decisions-from` |
| `README.md`, `integrations/claude-code/README.md`, `docs/plan-automatyzacja-i-konsola.md` | opis i status |

## Kolejność (TDD)
1. Testy cytatów: dosłowny, różne białe znaki i cudzysłowy, za krótki, nieobecny, limit tekstu.
2. Testy skrzynki: kandydatury → pozycje, odrzucone z powodem, duplikat, `approved` (pola decyzji, `draft_edited`
   liczony i podany), `rejected` bez wpisu w rejestrze, zamknięta pozycja.
3. Testy MCP: narzędzie na liście, przebieg przez narzędzia; kontrakt 0.10.0; statystyki.
4. Kod, potem dokumentacja.

Bramka: `uv run pytest`, `ruff check`, `ruff format --check`, `mypy --strict src` (Python 3.13 i 3.11).
