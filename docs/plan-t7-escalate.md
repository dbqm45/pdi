# DI Team T7 — „Escalate” — plan

Stan: 2026-11-26, decyzje 1–9 i OM2 przyjęte przez właściciela; kroki 1–4 zrobione, sprawdzone na żywo. Źródło: `TODO.md`, sekcja „DI Team”, krok T7 (pomysł właściciela z
2026-11-20): trzecia opcja na karcie decyzji, obok „Decide” i „Ask team”, żeby przekazać sprawę **powyżej zespołu
albo poza zespół**, gdy zespół nie może albo nie powinien rozstrzygać sam.

## Co jest dziś

Sprawdzone 2026-11-26 na `main` pdi:
- **Operating model OM1** (`docs/16-operating-model.md`, przyjęty 2026-11-22): wszystkie bramki zatwierdza jedna
  osoba, bez zastępcy. §5: „Przy jednym zatwierdzającym nie ma do kogo eskalować, więc model nie udaje eskalacji”.
  §9 mówi, kiedy model trzeba rozdzielić: między innymi, gdy dochodzi druga osoba z prawem decyzji. §10: przypisanie
  zatwierdzającego i zastępcy per typ decyzji (N1) nie jest zbudowane.
- **W konsoli** decyduje każda osoba z rolą `editor` albo `admin` w DI Decision; konsola nie wie, kto jest „tym”
  zatwierdzającym. „Ask team” (T4) zapisuje decydenta przy pytaniu, ale tylko jako tego, kto pytał.
- **Osoby:** konsola zna tylko tych, którzy się do niej logowali (`people.json`), z nazwą i `sub`, bez roli.
- **Kanały:** DI Channels umie dziś napisać do osoby suity po `sub` (T6).
- **Kontrakt 0.26.0:** decyzja ma `decided_by_id` i `consulted`; nie ma pola o eskalacji.

Wniosek: prawdziwa eskalacja **zmienia, kto decyduje o tej sprawie**. To odejście od OM1 i trzeba je zapisać
decyzją, a nie przemycić w kodzie.

## Decyzje do potwierdzenia (rekomendacja w każdej)

1. **Eskalacja przekazuje decyzję o jednej sprawie innej osobie.** Inaczej niż „Ask team”, gdzie zespół tylko
   doradza. Od chwili eskalacji tylko adresat może zdecydować (konsola i MCP odmawiają innym). Adresat może też
   **oddać sprawę** z notatką; wtedy decyduje znów ten, kto eskalował. Rekomendacja: tak. Bez tego „Escalate” to
   drugie „Ask team”.
2. **Zmiana OM1 jako nowa decyzja OM2** w `decyzje.md` i w `16-operating-model.md`: „eskalacja daje prawo decyzji o
   jednej sprawie osobie, do której eskalowano; reszta OM1 bez zmian”. To wypełnia §9 tylko dla eskalowanych spraw;
   pełny podział ról (N1) zostaje na później. Rekomendacja: tak.
3. **Do kogo:** osoba z suity z rolą `editor` albo `admin` w DI Decision, która logowała się już do konsoli. Konsola
   zapisuje odtąd także rolę przy logowaniu (`people.json`), żeby na liście byli tylko ci, którzy mogą decydować.
   Osoby spoza suity: nie w tym kroku (zaproszenie przez DI Admin daje im konto i rolę). Rekomendacja: tak.

   Odrzucona szersza droga: ścieżka eskalacji z konfiguracji (właściciel produktu, architekt, bezpieczeństwo). Wymaga
   N1, którego nie ma.
4. **Formularz:** adresat, powód (wymagany, jedno do trzech zdań) i opcjonalnie pytanie do adresata. Otwarte „Ask
   team” przy tej sprawie zamyka się z tym, co zebrano; adresat widzi odpowiedzi. Rekomendacja: tak.
5. **Termin:** zostaje termin sprawy z OM1, liczony od jej wpływu. Eskalacja go nie przedłuża; przypomnienia, stan
   „wstrzymana” i lista do przeglądu idą do adresata. Karta pokazuje „Escalated to X · since … · due …”.
   Rekomendacja: tak.
6. **Powiadomienie:** adresat dostaje wiadomość prywatną w Slacku przez DI Channels: kto eskaluje, sprawa, powód,
   termin, link „Decide in DI Decision”. W dziennym skrócie adresata: sekcja „Escalated to you”. Wymaga zmiany w DI
   Channels (nowe `team.escalated`). Rekomendacja: tak.
7. **Kontrakt di-contract 0.27.0:** opcjonalne pole `escalation` w decyzji i w `decision_recorded`:
   `{ by_id, by_name, to_id, to_name, reason, at, returned_at? }`. Zmiana zgodna wstecz, według zasad kontraktu:
   nowa wersja, linia w historii, przykłady. Pin pdi rośnie do 0.27.0. Rekomendacja: tak.
8. **Agent:** narzędzie MCP do odczytu pokazuje eskalację w `list_inbox` i `daily_digest`. Agent nie eskaluje sam.
   Rekomendacja: tak.
9. **Typy chronione** (np. `release.go` przy B5): eskalacja dozwolona, ale adresat musi mieć rolę `admin`.
   Rekomendacja: tak.

## Kroki

1. di-contract 0.27.0: `escalation` w `decision.schema.json` i `$defs/decision_recorded`, przykłady, historia w
   README, `decision-record.md`. Osobny PR i tag.
2. DI Channels: `POST /pdi/escalated` (jak `/pdi/asked`, jeden adresat) i sekcja „Escalated to you” w skrócie. Osobny
   PR.
3. pdi:
   - pin 0.27.0, OM2 w `decyzje.md` i `16-operating-model.md`;
   - czerwone testy: zapis eskalacji (`escalations/<pozycja>.json`), kto może decydować, oddanie sprawy, zamknięcie
     „Ask team”, role w `people.json`, typy chronione, termin, `escalation` w decyzji, wiadomość, skrót, MCP;
   - potem kod: formularz „Escalate” na karcie, `/inbox/<id>/escalate` i `/return`, odmowa decyzji innym.
4. Na żywo w lokalnej konsoli: `ola.test` (editor) eskaluje do `adm.test` (musi mieć `di-decision:admin`); `ola.test`
   nie może już zdecydować; `adm.test` decyduje; decyzja ma `escalation`. Drugi przebieg: `adm.test` oddaje sprawę.
5. README, instrukcja użytkownika (nowy rozdział), `TODO.md`.

## Ryzyka

- Eskalacja do osoby, która nie odpowiada, wstrzyma zmianę jak przy zatwierdzającym; oddanie sprawy jest jedynym
  wyjściem poza decyzją adresata. Rozważyć później: eskalujący może cofnąć eskalację, gdy adresat milczy.
- Lokalnie to dwie osoby w jednej konsoli; prawdziwe użycie zaczyna się z konsolą jako usługą.
- OM2 to pierwszy wyłom w „jednym zatwierdzającym”; przegląd modelu 2027-01-03 powinien go ocenić.

## Co wyszło przy wdrożeniu (2026-11-26)

- **Trzy PR:** dbqm45/di-contract#36 (kontrakt 0.27.0), dbqm45/di-channels#14 (`/pdi/escalated`, „Escalated to you”),
  pdi (ten krok).
- **Odmowa decyzji** jest w `Inbox.decide()`, więc obejmuje i konsolę, i MCP: decyzja bez `decided_by_id` adresata
  (np. z lokalnego serwera MCP bez logowania) jest odrzucana. Konsola odpowiada 403 jeszcze przed tym.
- **Oddana sprawa** zostaje w zapisie: decyzja eskalującego ma `escalation` z `returned_at` i `return_note`. Ponowna
  eskalacja po oddaniu przenosi poprzednią do `history`.
- **Role w `people.json`:** konsola zapisuje przy logowaniu `decides` i `admin` (z ID tokenu); osoby zapisane przed
  tą wersją nie są na liście adresatów, dopóki nie zalogują się ponownie.
- **Na żywo** (lokalny Keycloak 26.4.7, konsola z logowaniem przez suitę, Playwright; `adm.test` dostał na czas próby
  `di-decision:admin`, potem rolę cofnięto): `ola.test` eskalowała B2 do Adm Test; karta Oli: „Escalated to Adm Test”,
  jej decyzja → 403; Adm widział powód i pytanie, zdecydował (`DEC-0001`, `escalation` od Oli do Adma). B5 (typ
  chroniony): lista adresatów tylko z adminami; Adm oddał sprawę z notatką, Ola zdecydowała (`DEC-0002` z
  `returned_at` i `return_note`). Wiadomości w Slacku nie sprawdzono (brak testowego Slacka).
