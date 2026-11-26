# Instrukcja użytkownika DI Suite

Instrukcja dla osób, które pracują w konsoli pdi (DI Decision) i w pozostałych produktach suity. Opisuje, jak
wykonać zadanie od początku do końca, a nie jak działa kod. Szczegóły techniczne są w [`README.md`](../README.md) i w
planach w `docs/`.

Spis treści:
- [Jak przedyskutować sprawę z zespołem](#jak-przedyskutować-sprawę-z-zespołem)

## Jak przedyskutować sprawę z zespołem

Sprawa to pozycja w skrzynce pdi, która czeka na decyzję człowieka, na przykład prośba o bramkę B2 dla zmiany CHG-1,
ocena skutku albo zgłoszony problem. Jedna osoba decyduje, ale przed decyzją może zapytać zespół. Gdy zespół się
zgadza, decyzja zajmuje jedno kliknięcie. Gdy zdania są podzielone albo ktoś chce rozmawiać, sprawa trafia na
agendę spotkania „Discuss with team”, a decyzja zapada na spotkaniu.

### Ścieżka w skrócie

1. Sprawa pojawia się w **Skrzynce** konsoli pdi.
2. Decydent klika **Ask team**, wybiera osoby i czas na odpowiedź.
3. Każda zapytana osoba odpowiada: opcja i jedno zdanie uzasadnienia. Odpowiedzi są ukryte do zamknięcia pytania.
4. Pytanie się zamyka: po terminie, po komplecie odpowiedzi albo gdy decydent je zamknie.
5. Wynik:
   - **Team agrees: X**: decydent zatwierdza gotowy szkic decyzji w Skrzynce;
   - **To discuss**: sprawa trafia na agendę **Discuss** (krok 6);
   - **Nobody answered**: decydent decyduje sam albo pyta jeszcze raz.
6. Decydent wysyła zespołowi agendę, ustala kolejność i prowadzi spotkanie.
7. Na spotkaniu decyzja zapada wprost z karty sprawy na agendzie. Zapisuje się jako decyzja ze spotkania, z listą
   zapytanych i ich odpowiedziami.

### Kto co może

Konsola pdi rozpoznaje osoby przez logowanie suity (Google albo dostawca tożsamości organizacji, nigdy hasło w pdi).
Uprawnienia daje rola w produkcie **DI Decision** (klient `di-decision`):

| Rola | Co może |
| --- | --- |
| `viewer` | czyta Skrzynkę, tablice i agendę; **odpowiada**, gdy ktoś go zapyta |
| `editor` | to samo, a także **pyta zespół, decyduje i ustala kolejność agendy** |
| `admin` | to samo co `editor` |

Rolę nadaje administrator organizacji w konsoli DI Admin (strona ról osób, lokalnie `http://127.0.0.1:3200/admin`)
albo zaproszeniem linkiem z tą rolą. Osoba bez roli w DI Decision albo spoza organizacji zobaczy po zalogowaniu
odmowę dostępu (403).

Zapytać można tylko osoby, które **choć raz zalogowały się do tej konsoli**. Konsola zapamiętuje je przy logowaniu
(identyfikator i wyświetlana nazwa, bez adresu e-mail). Zanim zapytasz kogoś nowego, poproś go o jedno zalogowanie.

### Krok 1. Zaloguj się i znajdź sprawę

1. Otwórz konsolę pdi. Lokalnie po `uv run sdlc up` jest pod `http://127.0.0.1:8788/`; adres otwiera też
   `uv run sdlc open`.
2. Konsola przekieruje Cię do logowania suity. Keycloak pyta najpierw o nazwę użytkownika albo e-mail, potem o
   hasło albo przekierowuje do dostawcy organizacji.
3. W menu wybierz **Skrzynka**. Każda karta to jedna sprawa: identyfikator, pas, rodzaj (np. `gate`), opis, ryzyko i
   formularz decyzji.

Sprawy, które dotyczą Ciebie, widać też na tablicy **Now** w części „Awaiting decision”.

### Krok 2. Zapytaj zespół (decydent: `editor` albo `admin`)

1. Na karcie sprawy rozwiń **Ask team**.
2. Zaznacz osoby, które mają doradzić; siebie nie zaznaczasz. Lista pokazuje tylko osoby, które logowały się już do
   konsoli. Jeśli nikogo na niej nie ma, zobaczysz „Ask team: nobody else has signed in to this console yet”.
3. W **Closes in** wybierz czas na odpowiedź: **4 h**, **24 h** (domyślnie) albo **3 days**.
4. Kliknij **Ask**.

Od tej chwili karta pokazuje znacznik **With team · 0/N · closes …**: ile osób odpowiedziało z ilu zapytanych i do
kiedy. Ten sam znacznik jest na tablicy **Now**.

Pamiętaj:
- **Zespół doradza, decydujesz Ty.** Możesz zdecydować w każdej chwili, także przed zamknięciem pytania albo wbrew
  zespołowi. Decyzja zamyka wtedy pytanie, a odpowiedzi, które już przyszły, zapisują się przy decyzji.
- **Odpowiedzi są ukryte dla wszystkich, także dla Ciebie**, do zamknięcia pytania. Dzięki temu nikt nie sugeruje się
  zdaniem innych. Widać tylko liczbę odpowiedzi.

### Krok 3. Odpowiedz, gdy ktoś Cię zapyta (każda rola)

1. Zaloguj się do konsoli i otwórz **Skrzynkę**.
2. Na karcie sprawy zobaczysz sekcję **Asked of you**.
3. Wybierz jedną opcję. Są to możliwe wyniki sprawy, np. dla bramki `approved`, `changes_requested` albo `rejected`,
   oraz dodatkowa opcja **`talk_live`**: „ta sprawa wymaga rozmowy”.
4. W polu **One sentence: why** napisz jedno zdanie uzasadnienia (do 300 znaków). Opcja i zdanie są wymagane.
5. Kliknij **Answer**.

Odpowiedź możesz zmienić, dopóki pytanie jest otwarte: wybierz inną opcję albo popraw zdanie i kliknij **Answer**
jeszcze raz. Po zamknięciu pytania odpowiedzi już się nie przyjmuje.

Jeśli przy opcjach jest sekcja **Agent on the options**, to agent (Claude przez MCP) opisał, co się stanie przy danej
opcji: plan, koszt, testy. Agent nie głosuje; to tylko informacja dla Ciebie.

### Krok 4. Zamknięcie pytania

Pytanie zamyka się, gdy spełni się pierwszy z warunków:
- minie wybrany czas;
- odpowiedzą wszyscy zapytani;
- decydent kliknie **Close the question now**;
- decydent podejmie decyzję.

Po zamknięciu wszyscy widzą odpowiedzi: kto, jaką opcję i dlaczego. Osoba, która nie zdążyła, ma przy nazwisku „—”.

### Krok 5. Wynik

| Znacznik na karcie | Kiedy | Co dalej |
| --- | --- | --- |
| **Team agrees: X** | wszyscy, którzy odpowiedzieli, wybrali tę samą opcję X i nikt nie wybrał `talk_live` | w **Skrzynce** treść decyzji i uzasadnienie są już wypełnione z odpowiedzi zespołu; sprawdź je i kliknij przycisk opcji X |
| **To discuss** | zdania są podzielone albo ktoś wybrał `talk_live` | sprawa trafia na agendę **Discuss**; przejdź do kroku 6 |
| **Nobody answered** | nikt nie odpowiedział przed zamknięciem | zdecyduj sam albo zapytaj jeszcze raz, np. z dłuższym terminem |

Przy zgodności liczą się tylko osoby, które odpowiedziały; kto nie odpowiedział, widać na liście.

### Krok 6. Przygotuj spotkanie: agenda „Discuss”

1. W menu wybierz **Discuss**. Strona **Discuss with team** pokazuje wszystkie otwarte sprawy z wynikiem
   **To discuss**, ponumerowane.
2. Kolejność ustala konsola według tego, co sprawa blokuje. Wyżej jest sprawa, która:
   1. wstrzymuje przebieg (przebieg zatrzymany albo wymaga przeglądu);
   2. jest po terminie;
   3. trzyma zmianę na bramce (np. „CHG-1 waits at B2”);
   4. ma więcej osób chętnych do rozmowy na żywo;
   5. czeka dłużej.

   Powód miejsca jest napisany słowami pod tytułem, w linii **Why now**, np. „the run is paused; CHG-2 waits at B2;
   1 wants to talk live; waiting 1 h”.
3. Jako `editor` albo `admin` możesz zmienić kolejność przyciskami **↑** i **↓** przy tytule. Twoja kolejność się
   zapisuje i obowiązuje wszystkich. Nowe sprawy dochodzą pod spodem, w kolejności według blokad.
4. Na dole strony rozwiń **Markdown for the invitation or notes** i skopiuj tekst. To gotowa agenda: sprawy w
   kolejności, powód miejsca, opcje i odpowiedzi zespołu. Wklej ją do zaproszenia na spotkanie albo do notatki.
5. Wyślij zaproszenie osobom, które odpowiadały. Konsola nie wysyła zaproszeń sama.

Na agendzie widać też, kto zadał pytanie (**asked by**), wszystkie odpowiedzi i opisy opcji od agenta.

### Krok 7. Spotkanie i decyzja

1. Na spotkaniu otwórz stronę **Discuss** i omawiajcie sprawy od góry.
2. Gdy zespół ustali wynik sprawy, decydent wpisuje na jej karcie:
   - **Treść decyzji (statement)**: co postanowiono;
   - **Dlaczego (why)**: uzasadnienie z rozmowy.
3. Decydent klika przycisk wyniku, np. `approved`, `changes_requested` albo `rejected`.

Decyzja zapisuje się w rejestrze decyzji pdi jako decyzja ze spotkania. Ma w sobie:
- źródło „meeting”, z adresem agendy i datą („Discuss with team, <data>: <opis sprawy>”);
- listę zapytanych (`consulted`): kto, jaką opcję wybrał i dlaczego, a przy osobach bez odpowiedzi puste pola;
- osobę, która zdecydowała (z jej logowania).

Sprawa znika z agendy i ze Skrzynki. Decyzję znajdziesz w menu **Decyzje**. Dalej działa tak samo jak każda decyzja
pdi, np. przepuszcza zmianę przez bramkę.

Jeśli spotkanie nie rozstrzygnie sprawy, zostaw ją na agendzie; będzie tam do decyzji.

### Agent w procesie

Agent, np. Claude Code połączony z serwerem MCP pdi, może pomóc, ale nie decyduje:
- `add_option_effects`: dopisuje przy opcjach sprawy, co się stanie (plan, koszt, testy); zapytani widzą to przy
  odpowiadaniu;
- `list_inbox`: widzi stan pytania (liczby odpowiedzi, termin), ale nie widzi odpowiedzi przed zamknięciem;
- `discussion_agenda`: czyta agendę, np. żeby przygotować podsumowanie przed spotkaniem.

Agent nie odpowiada na pytanie zespołu, nie zamyka go i nie decyduje. To zawsze robi człowiek.

### Ograniczenia dziś

- Konsola działa lokalnie, na `127.0.0.1`. Zespół z różnych komputerów będzie mógł z niej korzystać dopiero z konsolą
  jako usługą. Do prób lokalnych zaloguj każdą osobę w osobnym profilu przeglądarki albo oknie prywatnym, bo sesja
  jest w ciasteczku.
- **Ask team** i odpowiadanie działają tylko z logowaniem przez suitę. W trybie z tokenem w adresie (bez suity) nie
  ma prawdziwych osób, więc nie ma też pytania do zespołu, a agenda zostaje pusta.
- Konsola nie wysyła powiadomień o pytaniu ani zaproszeń. Daj znać zapytanym sam, np. na czacie zespołu.
- Na agendzie są tylko sprawy ze Skrzynki pdi. Sprawy z historyjek DI Definition i pokój planowania w sprintdecku
  dojdą osobno.
