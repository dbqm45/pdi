# DI Team T6 — skróty do Slacka — plan

Stan: 2026-11-26, decyzje 1–7 przyjęte przez właściciela; kroki 1–3 zrobione, sprawdzone na żywo bez prawdziwego Slacka. Źródło: `TODO.md`, sekcja „DI Team”, krok T6: dzienny skrót i
powiadomienie „czeka na Ciebie” z linkiem, przez wspólną aplikację kanałów suity (DI Channels), a nie własnym botem.

## Co jest dziś

Sprawdzone 2026-11-26 na `main` pdi i `dbqm45/di-channels`:
- **„Czeka na Ciebie” już działa** (krok 17, CH2, N3). pdi wysyła każdą nową pozycję skrzynki i każdy etap terminu
  na podpisany `POST <PDI_CHANNELS_URL>/pdi/waiting` (`src/pdi/waiting.py`). DI Channels wysyła wiadomość prywatną z
  linkiem „Decide in DI Decision” (`src/waiting.ts`). W godzinach ciszy (18:00–8:00, weekendy) Slack sam ją wstrzymuje.
- **Odbiorca jest jeden:** `DI_CHANNELS_APPROVER` (identyfikator Slacka). Tak mówi OM1 („jeden zatwierdzający, bez
  zastępcy”).
- **„Ask team” (T4) nie powiadamia nikogo.** Zapytana osoba dowiaduje się o pytaniu tylko wtedy, gdy sama wejdzie do
  konsoli. To dziś największa luka: pytanie z terminem 4 h, o którym nikt nie wie.
- **Dziennego skrótu nie ma.** Każda sprawa to osobna wiadomość; nie ma jednego „co dziś na Tobie”.
- **Osoby:** pdi zna osoby suity po `sub` (`people.json`, bez e-maila, DI3). DI Channels umie zamienić osobę ze Slacka
  na osobę suity (e-mail ze Slacka → `GET <di-identity>/api/people?email=`), ale nie odwrotnie. DI Channels jest jedyną
  aplikacją z `email: true` w realmie, więc tylko ona może poznać e-mail osoby.
- Teams: nie ma (DI Channels ma tylko Slacka).

## Decyzje do potwierdzenia (rekomendacja w każdej)

1. **Dzienny skrót dla zatwierdzającego.** Raz w dzień roboczy o 8:00 jedna wiadomość prywatna:
   - „Waiting for your decision”: liczba spraw i do 10 najpilniejszych (po terminie, termin dziś, wstrzymane) z
     terminem i linkiem;
   - „With the team”: otwarte pytania „Ask team” z liczbą odpowiedzi i czasem zamknięcia;
   - „To discuss”: liczba spraw na agendzie z linkiem do `/discuss`;
   - pusty dzień: brak wiadomości (nie „nic nie czeka”).

   Treść liczy pdi (to jego dane), DI Channels tylko ją formatuje i wysyła. Rekomendacja: tak.
2. **Wiadomość do zapytanej osoby przy „Ask team”.** Gdy decydent pyta zespół, każda zapytana osoba dostaje
   wiadomość prywatną: kto pyta, o co, do kiedy, link „Answer in DI Decision”. W dziennym skrócie tej osoby jest też
   „Asked of you”, dopóki nie odpowie. Rekomendacja: tak.
3. **Jak znaleźć osobę w Slacku, bez e-maila w pdi.** pdi wysyła `sub` osoby suity. DI Channels pyta di-identity o
   e-mail tej osoby (nowe `GET /api/people/<sub>`, tylko dla konta usługowego z rolą `di-identity:people-reader`, tylko
   dla aplikacji z `email: true`), potem Slacka `users.lookupByEmail` (zakres `users:read.email`, już wymagany przez
   §7 `slack-setup.md`). E-mail nie trafia do pdi ani do logów. Bez dopasowania: jedna linia w logu, wiadomość nie
   idzie, a skrót zatwierdzającego pokazuje „not reachable in Slack”. Rekomendacja: tak.

   Odrzucona prostsza droga: ręczna mapa `sub=U…` w ustawieniach DI Channels. Działa bez zmiany di-identity, ale ktoś
   musi ją utrzymywać.
4. **Zatwierdzający dalej z `DI_CHANNELS_APPROVER`.** Dzienny skrót decydenta idzie do niego, tak jak „czeka na
   Ciebie”. Decydent jako osoba suity (`decided_by_id` z sesji) zamiast jednej stałej zostaje na krok z wieloma
   decydentami (DA4, konsola jako usługa). Rekomendacja: tak.
5. **Wyzwalanie:** `pdi-digest` (nowe polecenie, jak `pdi-deadlines`) i `uv run sdlc digest`. Cron raz dziennie, np.
   o 7:55 w dni robocze; wiadomość ma identyfikator `digest-<osoba>-<dzień>`, więc drugie uruchomienie tego samego
   dnia niczego nie powtarza (DI Channels pamięta wysłane identyfikatory do końca dnia). Narzędzie MCP do odczytu
   `daily_digest`, żeby agent mógł pokazać to samo w rozmowie. Rekomendacja: tak.
6. **Bez zmiany kontraktu.** `gate.waiting` jest własnym API pdi ↔ DI Channels; skrót i pytanie zespołu też
   (`POST /pdi/digest`, `POST /pdi/asked`), z tym samym podpisem `X-PDI-Signature`. Rekomendacja: tak.
7. **Teams nie w tym kroku.** DI Channels ma tylko Slacka; Teams to osobny adapter, gdy będzie pierwszy zespół na
   Teams. Rekomendacja: tak.

## Kroki

1. di-identity: `GET /api/people/<sub>` (osoba, nazwa, zweryfikowany e-mail; 404 dla agenta albo braku), test na
   Keycloak. Osobny PR.
2. DI Channels: czerwone testy, potem kod:
   - `POST /pdi/asked` (wiadomość do zapytanej osoby) i `POST /pdi/digest` (skrót), oba z podpisem i parsowaniem jak
     `parseWaiting`;
   - osoba suity → Slack (`suite.ts`, pamięć jak dziś);
   - teksty i godziny ciszy z `waiting.ts`.

   Osobny PR.
3. pdi: czerwone testy, potem kod:
   - `consult.ask()` wysyła `asked` do DI Channels, gdy `PDI_CHANNELS_URL` jest ustawiony; błąd wysyłki nie
     blokuje pytania (zapis w konsultacji, jak `waiting`);
   - `digest.py`: czysta funkcja „co jest na osobie” ze skrzynki, konsultacji i agendy, wysyłka, `pdi-digest`,
     `sdlc digest`, narzędzie MCP `daily_digest`.
4. Na żywo: lokalny Keycloak, DI Channels z tunelem do Slacka testowego, `ola.test` pyta `adm.test`; wiadomość
   do `adm.test`, potem `sdlc digest` z obiema sekcjami. Wymaga konta Slack testowego z adresem e-mail osoby z realmu
   (nie sprawdzono, czy jest; bez niego krok 4 tylko z udawanym Slackiem w testach).
5. README pdi, `slack-setup.md`, instrukcja użytkownika (rozdział „Slack”), `TODO.md`.

## Ryzyka

- Osoba w Slacku musi mieć ten sam e-mail co w suicie. Inaczej wiadomość nie dojdzie; skrót powie, kogo nie
  znaleziono.
- Lokalna konsola pdi ma adres `127.0.0.1`, więc link z wiadomości działa tylko na tym samym komputerze. Prawdziwy
  użytek zaczyna się z konsolą jako usługą.
- Nowe API di-identity podaje e-mail. Dostaje je tylko konto usługowe z `people-reader`; dziś to tylko DI Channels.

## Co wyszło przy wdrożeniu (2026-11-26)

- **Trzy PR:** dbqm45/di-identity#13 (`GET /api/people/<sub>`, tylko klienci z `email: true`), dbqm45/di-channels#13
  (`/pdi/asked`, `/pdi/digest`), pdi (ten krok).
- **Moduł w pdi** nazywa się `team_notify.py` (nie `digest.py`), bo trzyma obie wiadomości.
- **Etap terminu w skrócie** liczony jest z czasu (`waiting.stages()`), a nie z zapisanych przypomnień, więc skrót jest
  dokładny także bez crona `sdlc deadlines`.
- **„Not reachable in Slack”** obejmuje i brak osoby w Slacku, i błąd po drodze (np. Slack nie odpowiada); powód jest w
  logu DI Channels, bez e-maila.
- **Na żywo** (lokalny Keycloak 26.4.7, di-identity na 3200, di-channels na 3100, pdi): token usługi `di-channels` →
  `GET /api/people/<sub>` dał osobę z e-mailem (200), konto bez zweryfikowanego adresu i nieznany `sub` 404, klient
  spoza `OIDC_SERVICE_CLIENTS` 401; `team.asked` z pdi przeszło podpis, DI Channels zapytał di-identity, a pdi zapisał
  obie osoby jako nieosiągalne, bo ta maszyna nie łączy się ze slack.com; skrót dał 502 i `failed` w pdi. **Prawdziwej
  wiadomości w Slacku nie sprawdzono** (brak testowego workspace’u Slack).
