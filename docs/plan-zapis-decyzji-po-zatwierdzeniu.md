# Zapis decyzji tylko po zatwierdzeniu szkicu w konsoli — plan

Stan: 2026-11-27, zrobione i sprawdzone na żywo. Właściciel zlecił zrobić to według rekomendacji: wymóg
zatwierdzenia **zawsze**, także lokalnie w Claude Code. Źródła: `TODO.md` („Zapis decyzji i zastępowanie jako narzędzia wysokiego ryzyka z potwierdzeniem”,
„Karta zatwierdzenia decyzji jako MCP App”), wzorzec „zgoda związana z argumentami” z tf
(`sec-llm-security/references/agent-design-patterns.md` §4).

## Co jest dziś

- Narzędzia MCP `record_decision` i `supersede_decision` zapisują decyzję od razu. Zasada „tylko po zatwierdzeniu
  przez człowieka” to prośba w instrukcji serwera; model może zapisać decyzję bez człowieka.
- MCP Apps (sprawdzone 2026-11-27 na apps.extensions.modelcontextprotocol.io): specyfikacja stabilna z 2026-01-26,
  obsługa w Claude, ChatGPT i VS Code; o Claude Code CLI strona nie mówi. Pola ukrywania narzędzia przed modelem
  i zasad dla hostów bez obsługi nie udało się potwierdzić (tekst specyfikacji niedostępny) [niezweryfikowane].
  Pełna karta wymaga connectora w Claude.ai, czyli hostingu.

## Decyzje (według rekomendacji)

1. **Szkic, zatwierdzenie w konsoli, jednorazowy zapis.**
   - `present_decision_draft` (pola jak dotąd w `record_decision`, plus opcjonalne `supersedes`) sprawdza szkic
     z kontraktem i zapisuje go w `decision-drafts/DRF-n.yaml` z SHA-256 kanonicznej treści. Zwraca numer, skrót
     i link do konsoli (`PDI_CONSOLE_URL`, bez tokenu).
   - Konsola `/drafts/DRF-n` pokazuje surową treść szkicu (nie opis modelu) i skrót. Zatwierdza albo odrzuca
     z powodem tylko człowiek z prawem decyzji: rola `editor`/`admin` w DI Decision albo token konsoli.
   - `record_decision(draft_id, sha256)` zapisuje dokładnie zatwierdzoną treść: szkic zatwierdzony, ten sam skrót,
     zgoda nie starsza niż godzina, użyta raz. Szkic z `supersedes` zastępuje starą decyzję.
     `supersede_decision` znika.
   - Zatwierdzić można szkic nie starszy niż 7 dni. Powód odrzucenia wraca w błędzie `record_decision`, żeby kolejny
     szkic go uwzględnił.
2. **Kto zdecydował:** `decided_by` ze szkicu, a bez niego osoba, która zatwierdziła (z `decided_by_id` z sesji
   suity). Zatwierdzający, czas i skrót zostają w pliku szkicu.
3. **Zawsze**, także przez stdio. `decision.recorded` z ci_for_sdlc, decyzje przyciskami w konsoli i `tf decision add`
   nie idą przez te narzędzia i zostają bez zmian. `decide_inbox_item` — osobny krok (pozycja w `TODO.md`).
4. Karta MCP App później, na tym samym magazynie szkiców: przycisk karty = zatwierdzenie w konsoli.
5. Bez zmiany kontraktu i bez nowej zależności.

## Kroki

1. Czerwone testy: magazyn szkiców (skrót, zatwierdzenie, odrzucenie, wygaśnięcie, jednorazowość), narzędzia MCP,
   konsola (strona szkicu, przyciski, role).
2. Kod: `src/pdi/drafts.py`, `Registry.check`, narzędzia MCP, konsola.
3. Na żywo: agent przez MCP tworzy szkic, człowiek zatwierdza w konsoli, `record_decision` zapisuje.
4. README, instrukcja użytkownika, `integrations/claude-code`, `TODO.md`.

## Co wyszło przy wdrożeniu (2026-11-27)

- **Na żywo** (klient MCP przez stdio, konsola z tokenem, Playwright):
  - agent wystawił dwa szkice (zapis przed zatwierdzeniem sprawdzają testy; na żywo ten krok nie przeszedł
    z powodu błędu w skrypcie próby, nie w pdi);
  - DRF-1: **Approve** w konsoli, potem `record_decision` zapisał DEC-0001 z `decided_by` osoby z konsoli;
  - DRF-2: **Reject** z powodem; `record_decision` zwrócił „odrzucony: <powód>”;
  - drugi zapis DRF-1: „już zapisany jako DEC-0001”.
- **Python 3.11:** `locals()` w wyrażeniu listowym zwraca zmienne wyrażenia, nie funkcji; argumenty narzędzia są
  kopiowane przed odfiltrowaniem `supersedes`.
- **Nie zmienione:** `decide_inbox_item` i `triage_problem` dalej zamykają pozycje po odpowiedzi w czacie — osobna
  pozycja w `TODO.md`.
