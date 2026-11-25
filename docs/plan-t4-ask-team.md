# DI Team T4 — „Ask team” online — plan

Stan: 2026-11-25, propozycja do zatwierdzenia przez właściciela. Źródło: `TODO.md`, sekcja „DI Team”, krok T4
(ustalenia z rozmowy 2026-11-19). Makieta: kadr „Discuss with team”. T1–T3 są gotowe: kontrakt przebiegów,
zgłaszanie sesji z tf, tablica `/now` tylko do odczytu.

## Co jest dziś

- Konsola pdi loguje przez suitę (`docs/plan-konsola-tozsamosc.md`). `editor` i `admin` decydują, `viewer` czyta.
  Decyzja z przycisku zapisuje `decided_by_id` z sesji (kontrakt 0.25.0).
- Pozycja skrzynki (bramka, ocena skutku, zgłoszenie, …) ma swój zestaw wyników, np. approve, changes requested,
  reject. Decyzja idzie przez `Inbox.decide()`, tą samą ścieżką co narzędzie MCP `decide_inbox_item`.
- Konsola nie zna listy ludzi organizacji. Osoby suity zna tylko z sesji, które są w pamięci procesu.
- Konsola działa tylko na `127.0.0.1`, więc kilka osób to dziś kilka przeglądarek na jednym komputerze. Prawdziwy
  zespół z różnych komputerów będzie możliwy dopiero z konsolą jako usługą (DA4, hosting).

## Decyzje do potwierdzenia (rekomendacja w każdej)

1. **„Ask team” na karcie pozycji skrzynki, tylko z logowaniem przez suitę.** Decydent, czyli `editor` albo `admin`,
   który otwiera „Ask team”, się nie zmienia: zespół doradza. Bez logowania przez suitę, czyli z tokenem w adresie,
   przycisku nie ma, bo nie ma prawdziwych osób. Rekomendacja: tak.
2. **Kogo można zapytać:** osoby, które logowały się już do tej konsoli przez suitę i mają rolę w DI Decision.
   - Konsola zapisuje je przy każdym logowaniu w `people.json` w rejestrze: `sub`, nazwa i data ostatniego
     logowania, bez e-maila (DI3).
   - Decydent wybiera z tej listy co najmniej jedną osobę, ale nie siebie.
   - Lista członków organizacji z di-identity przyjdzie razem z usługą, bo dziś wymagałaby nowego API.

   Rekomendacja: tak.
3. **Jak wygląda pytanie:**
   - opcje to wyniki tej pozycji plus „talk live” (wymaga rozmowy);
   - odpowiedź to opcja i jedno zdanie, oba wymagane;
   - **odpowiedzi są ukryte do zamknięcia dla wszystkich, także dla decydenta**, widać tylko „N z M odpowiedzi”;
   - pytanie zamyka się w terminie (4 h, 24 h domyślnie albo 3 dni), gdy odpowiedzą wszyscy albo gdy decydent
     zamknie je wcześniej;
   - odpowiedź można zmienić do zamknięcia.

   Rekomendacja: tak.
4. **Wynik po zamknięciu:**
   - **zgodność** (wszyscy wybrali tę samą opcję i nikt nie chce rozmowy): decydent widzi „Team agrees: X” i
     zatwierdza jednym kliknięciem, z gotowym szkicem decyzji;
   - **rozbieżność albo „talk live”:** pozycja dostaje znacznik „to discuss” i trafi do agendy w T5.

   Decydent zawsze może zdecydować sam, także przed zamknięciem albo wbrew zespołowi, ale konsultacja się wtedy
   zamyka. Decyzja idzie dotychczasową ścieżką (`Inbox.decide`, `decided_by_id` z sesji). Rekomendacja: tak.
5. **Zapis w decyzji (kontrakt, di-contract 0.26.0):** opcjonalne pole `consulted` w decyzji i w zdarzeniu
   `decision_recorded`. To lista wszystkich zapytanych: `person_id` (`sub`), `name`, `option` i `reason`, oba `null`
   dla tych, którzy nie odpowiedzieli. Zmiana jest zgodna wstecz i idzie według zasad kontraktu: nowa wersja, linia w
   historii, przykłady. Pin w pdi rośnie do 0.26.0. Rekomendacja: tak.
6. **Silnik w pdi, a nie sprintdeck jako usługa.** Reguły tego kroku są proste: ukryte do zamknięcia, zamknięcie,
   zgodność. Sprintdeck loguje anonimowo przez Supabase, poza tożsamością suity. Jego silnik rozbieżności i talie
   ryzyka wejdą z T5, przez DI Definition (refinement). Rekomendacja: tak.
7. **Skutki opcji od agenta:** narzędzie MCP `add_option_effects` (item, opcja, skutki: plan, koszt, testy).
   - Agent dopisuje przy opcji, co się stanie; nie głosuje.
   - Pytani widzą to przy opcjach.
   - Narzędzia odczytu dostają konsultacje w `list_inbox`, a zamknięcie zostaje człowiekowi.

   Rekomendacja: tak.
8. **Tablica „Now”:** karta w „Awaiting decision” dostaje znacznik „With team · N/M · closes in …”, a po zamknięciu
   „Team agrees: X” albo „To discuss”. Osoba zapytana widzi u siebie na stronie skrzynki sekcję „Asked of you”.
   Rekomendacja: tak.

## Kroki

1. di-contract 0.26.0: `consulted` w `decision.schema.json` i w `$defs/decision_recorded`, przykłady, historia w
   README, `decision-record.md`. Osobny PR i tag.
2. pdi:
   - pin 0.26.0, a `consulted` w `FIELD_ORDER` rejestru i w przekazywaniu w skrzynce;
   - czerwone testy: przechowywanie konsultacji (`consultations/<item>.json`), reguły zamknięcia i zgodności, ukrycie
     odpowiedzi, `people.json`, trasy konsoli z sesjami suity, `add_option_effects`;
   - potem kod.
3. Na żywo w lokalnej konsoli z logowaniem przez suitę:
   - `ola.test` (editor) pyta `adm.test` i trzecią osobę;
   - odpowiedzi są niewidoczne do zamknięcia;
   - przy zgodności decyzja jednym kliknięciem, z `consulted` w zapisanej decyzji;
   - przy rozbieżności znacznik „to discuss”.

## Ryzyka

- Lokalnie to wiele kont w jednej konsoli, a nie zespół. Prawdziwe użycie zaczyna się z konsolą jako usługą.
- `consultations/` w rejestrze jest na dysku właściciela. Ukrycie odpowiedzi dotyczy konsoli, a nie pliku.
  Wystarcza lokalnie; w usłudze to dane w bazie.
- Termin zamknięcia liczy się przy odczycie, bez osobnego procesu. Pytanie po terminie zamyka się przy pierwszym
  wejściu kogokolwiek.
