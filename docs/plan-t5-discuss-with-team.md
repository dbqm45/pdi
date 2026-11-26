# DI Team T5 — „Discuss with team” jako agenda — plan

Stan: 2026-11-26, decyzje 1–6 przyjęte przez właściciela; kroki 1–3 zrobione, sprawdzone na żywo. Źródło: `TODO.md`, sekcja „DI Team”, krok T5, oraz
powiązania z 2026-11-21. Kadr makiety: „Discuss with team”. T4 („Ask team”) jest gotowe
(dbqm45/pdi#226): pozycja z rozbieżnością albo z „talk live” dostaje znacznik „To discuss”.

## Co jest dziś

- Konsultacje T4 leżą w `consultations/`. Po zamknięciu każdy widzi, kto co odpowiedział, a wynik `discuss`
  oznacza sprawę do rozmowy.
- Skrzynka zna koszt czekania: `received_at`, terminy z operating modelu (`deadline_notices`, `paused_at`,
  `needs_review`), a przy bramkach zmianę i jej fazę.
- Kontrakt ma `source.kind: meeting` (0.10.0) dla decyzji ze spotkania.
- W DI Definition krok **R5** (zestaw historyjek ułożony pod rozmowę, przez API) **nie jest zbudowany**
  (`ci_for_sdlc/docs/REFINEMENT-PLAN.md`, stan 2026-11-21). Pokój na żywo z ukrytymi głosami ma sprintdeck.
- Sprintdeck (sprawdzone 2026-11-26 na `main` z 2026-10-27, `supabase/migrations/`, `docs/PLAN.md` §12.3):
  - pokój i jego zadania obsługują funkcje RPC w Postgresie (`create_room`, `add_item`, `reorder_items`,
    `start_round`, `reveal_round`, `finalize_item` i inne);
  - logowanie jest anonimowe przez Supabase;
  - zadania dodaje się ręcznie, a importu nie ma (poza MVP);
  - plan po MVP przewiduje sesję wyzwalaną z zewnątrz i „notatkę z zatwierdzenia jako decyzję w rejestrze pdi”.

  Agenda może więc później zakładać pokój z listą spraw przez te funkcje. Wymaga to kont w sprintdecku albo
  tożsamości suity, bo dziś logowanie jest anonimowe.

## Decyzje do potwierdzenia (rekomendacja w każdej)

1. **Agenda w konsoli pdi: strona `/discuss`, na start tylko z danych pdi.** Trafiają na nią otwarte pozycje skrzynki
   z konsultacją zamkniętą wynikiem „To discuss”. Sprawy z DI Definition dojdą, gdy R5 da API (decyzja 5).
   Rekomendacja: tak.
2. **Kolejność według tego, co sprawy blokują:**
   - pozycja z `needs_review` albo `paused_at` (wstrzymany agent albo przebieg);
   - pozycja po terminie;
   - bramka, która trzyma zmianę;
   - liczba osób, które wybrały „talk live”;
   - na końcu czas czekania.

   Karta pokazuje cenę czekania słowami („czeka od 2 dni · po terminie · zmiana CHG-1 stoi na B2”). Decydent może
   przesunąć sprawę w górę albo w dół, a kolejność zapisuje się w `agenda.json`. Rekomendacja: tak.
3. **Karta sprawy na agendzie** pokazuje pytanie, odpowiedzi zespołu (są już jawne, bo konsultacja jest zamknięta),
   skutki opcji od agenta i formularz decyzji. Decyzję zapisuje się z tej samej karty tą samą ścieżką co w skrzynce.
   Decyzja dostaje `source.kind: meeting` z odnośnikiem do agendy i datą, `consulted` z T4 i `decided_by_id` z
   sesji. Rekomendacja: tak.
4. **Eksport agendy:** przycisk „Copy as Markdown” (lista spraw w kolejności, pytanie, opcje, odpowiedzi), do
   zaproszenia albo notatki. Bez kalendarza, licznika czasu i parking lotu: te należą do pokoju spotkania
   (sprintdeck albo DI Definition, `REFINEMENT-PLAN.md` „Co z koncepcji nie ma dziś miejsca”). Rekomendacja: tak.
5. **Powiązanie z DI Definition i sprintdeckiem później,** każde osobno:
   - gdy R5 da API zestawu, agenda dopisze sprawy z historyjek (otwarte pytania ludzi i silnika) jako osobną sekcję,
     tylko z odczytu i z odnośnikiem do DI Definition;
   - sesja na żywo z głosowaniem zostaje w sprintdecku, a pdi daje do niej tylko listę spraw.

   Rekomendacja: tak.
6. **Uprawnienia:** agendę widzi każdy z rolą w DI Decision. Kolejność zmienia i decyduje tylko `editor` albo
   `admin`. Agent przez MCP tylko czyta: narzędzie `discussion_agenda`, ta sama lista i kolejność. Rekomendacja: tak.

## Kroki

1. Czerwone testy: wybór spraw na agendę, kolejność według blokad, ręczne przesunięcie, decyzja z karty z
   `source.kind: meeting` i `consulted`, eksport Markdown, uprawnienia, narzędzie MCP.
2. Kod: `src/pdi/agenda.py` (czysta funkcja: pozycje i konsultacje → lista z powodem miejsca), strona `/discuss`,
   link w menu konsoli, `discussion_agenda` w MCP, README i `TODO.md`.
3. Na żywo w lokalnej konsoli: dwie sprawy „To discuss”, kolejność według blokady, decyzja z agendy.

## Ryzyka

- Bez R5 agenda pokazuje tylko decyzje z pdi, a nie pytania z historyjek. Do zbudowania R5 to „połowa refinementu”.
- Lokalnie agenda działa dla kont w jednej konsoli. Z zespołem z różnych komputerów zadziała dopiero z konsolą jako
  usługą.

## Co wyszło przy wdrożeniu (2026-11-26)

- **Ręczna kolejność:** przesunięcie (↑/↓) zapisuje w `agenda.json` całą bieżącą kolejność. Sprawy, które
  pojawią się później, idą za ustawionymi, według tego, co blokują.
- **Bez skryptu:** Markdown dla zaproszenia jest w polu tekstowym tylko do odczytu, bo CSP konsoli nie pozwala
  na schowek przez skrypt.
- **Tryb z tokenem** (bez suity): formularze agendy niosą token konsoli, tak jak w skrzynce.
- **MCP:** `discussion_agenda` (odczyt); razem 35 narzędzi.
- **Na żywo** (lokalny Keycloak, konsola na `127.0.0.1:8788`, Playwright):
  - dwie bramki z „talk live” od `adm.test`;
  - sprawa CHG-2 z wstrzymanym przebiegiem wyszła na pierwsze miejsce przed starszą CHG-1, z powodem „the run is
    paused; CHG-2 waits at B2; 1 wants to talk live; waiting 1 h”;
  - decyzja z agendy (`DEC-0001`) ma `source.kind: meeting`, adres agendy i `consulted`;
  - po decyzji na agendzie została tylko CHG-1.
