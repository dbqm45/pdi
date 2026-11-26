# Pokój sprintdecka z agendy „Discuss with team” — plan

Stan: 2026-11-26, zrobione i sprawdzone na żywo. Właściciel zlecił zrobić to według rekomendacji: **sprintdeck loguje przez suitę**. Źródło:
`TODO.md`, DI Team T5 („pokój sprintdecka — osobno”), [`plan-t5-discuss-with-team.md`](plan-t5-discuss-with-team.md)
decyzja 5 (sesja na żywo z głosowaniem zostaje w sprintdecku, pdi daje do niej tylko listę spraw), decyzja D-P11.

## Co sprawdzono (2026-11-26, lokalnie: Keycloak 26.4.7, Supabase CLI 2.122.0 z GoTrue v2.197.0)

- Sprintdeck (`dbqm45/sprintdeck`, `main` z 2026-10-27) loguje dziś anonimowo przez Supabase Auth; pokój i zadania
  zakładają funkcje RPC `create_room(p_title, p_display_name, p_deck)` i `add_item(p_room_id, p_title,
  p_description)`, obie wymagają zalogowanego `auth.uid()`.
- **Dostawca `keycloak` w Supabase Auth (przekierowanie) nie działa z realmem `suite`:** GoTrue zawsze prosi o zakresy
  `profile email openid`, a realm odmawia zakresu `email` aplikacjom bez prawa do e-maila (DI3): `invalid_scope`.
- **Działa logowanie ID tokenem:** sprintdeck sam prowadzi logowanie w Keycloaku (kod z PKCE, zakres `openid`,
  klient `sprintdeck` w realmie), a ID token przekazuje Supabase Auth (`grant_type=id_token`, `provider: keycloak`,
  `email_optional = true`). GoTrue sprawdza podpis, wystawcę, odbiorcę i `nonce`; powstaje nieanonimowy użytkownik z
  nazwą z suity i bez e-maila.
- Wystawca musi być ten sam dla przeglądarki i dla GoTrue w kontenerze. Lokalnie: `host.docker.internal:8180`
  (wpis w `/etc/hosts` hosta).

## Decyzje (według rekomendacji)

1. **Nowa aplikacja suity `sprintdeck`** w `keycloak/suite.json` (di-identity): klient poufny, rola `member`, bez
   e-maila (DI3). Rolę nadaje administrator organizacji w DI Admin albo zaproszeniem.
2. **Logowanie w sprintdecku:** przycisk „Sign in with the suite”; serwer sprintdecka prowadzi kod z PKCE (stan,
   weryfikator i `nonce` w ciasteczku HttpOnly), wymienia kod z sekretem klienta, sprawdza organizację
   (`SUITE_ORGANIZATION`) i rolę `member`, a potem zakłada sesję Supabase ID tokenem. Logowanie anonimowe zostaje dla
   pokoi bez suity.
3. **Pokój z agendy:** na stronie `/discuss` w pdi (dla `editor` i `admin`) przycisk „Open a room in sprintdeck”,
   gdy ustawione są `PDI_SPRINTDECK_URL` i `PDI_SPRINTDECK_SECRET`. Link niesie listę spraw w części `#` adresu
   (nie trafia do logów serwerów), podpisaną HMAC-SHA256 wspólnym sekretem i ważną godzinę. Sprintdeck sprawdza podpis
   na serwerze, wymaga sesji z suity i zakłada pokój z talią „Risk”: jedna sprawa = jedno zadanie (tytuł = opis
   sprawy, opis = zmiana, bramka, powody miejsca i odpowiedzi zespołu). Prowadzący to osoba, która otworzyła link.
4. **Decyzja dalej w pdi:** sprintdeck służy do rozmowy i głosowania; decyzję zapisuje się na agendzie w pdi, jak w T5.
   Powrót wyników ze sprintdecka do pdi: osobno.
5. **Bez zmiany kontraktu** (link to API pdi ↔ sprintdeck) i bez nowej zależności w czasie działania.

## Kroki

1. di-identity: klient `sprintdeck` w `suite.json`, README. PR.
2. sprintdeck: `config.toml` (dostawca `keycloak`, `email_optional`), trasy `/auth/suite/login` i
   `/auth/suite/callback`, przycisk logowania, `/from-pdi` i `/api/pdi-agenda` (sprawdzenie podpisu), testy Vitest,
   README. PR.
3. pdi: podpisany link na `/discuss` (`src/pdi/sprintdeck.py`), testy, README, instrukcja użytkownika. PR.
4. Na żywo: `ola.test` z rolą `sprintdeck:member` loguje się w sprintdecku przez suitę i z agendy pdi otwiera pokój ze
   sprawami.

## Co wyszło przy wdrożeniu (2026-11-26)

- **Trzy PR:** dbqm45/di-identity#14 (klient `sprintdeck`), dbqm45/sprintdeck#13 (logowanie przez suitę, `/from-pdi`),
  pdi (przycisk na agendzie).
- **Role sprawdzane przed Supabase:** ID token przychodzi wprost z punktu tokenów suity, wymieniony z sekretem klienta
  (OIDC Core 3.1.3.7), więc organizacja i rola są sprawdzane, zanim Supabase założy konto; Supabase i tak weryfikuje
  podpis. Wcześniejsza kolejność zakładała konto także osobie bez roli.
- **Cache Components w Next.js 16:** trasy `/auth/suite/login` i `/callback` wołają `connection()`; bez tego build
  zapisywał jedną odpowiedź (z jednym `state`) dla wszystkich.
- **React w trybie deweloperskim** uruchamia efekt dwa razy: strony `/auth/suite/done` i `/from-pdi` mają strażnika,
  inaczej pokój powstawał dwa razy.
- **Adres zwrotny:** `next dev` podaje origin jako `localhost`; sprintdeck bierze nagłówek `Host`, chyba że ustawiono
  `SPRINTDECK_PUBLIC_URL`.
- **Na żywo** (lokalny Keycloak 26.4.7, Supabase CLI 2.122.0 / GoTrue v2.197.0, konsola pdi, Playwright): `ola.test` (na
  czas próby z rolą `sprintdeck:member`, potem cofniętą) zapytała zespół o dwie bramki, `adm.test` odpowiedział „talk
  live”. Z agendy Ola kliknęła **Open a room in sprintdeck**, zalogowała się przez suitę i trafiła do pokoju „Discuss
  with team — 2026-11-26” (talia `risk`) z obiema sprawami jako prowadząca. W bazie jeden pokój i użytkownik bez e-maila.
  `adm.test` bez roli: komunikat „no role in Sprintdeck”, bez konta.
- Poza zakresem: Next.js 16.4.3 zgłasza znaną podatność przy `next dev` i `next build` (także na `main` sprintdecka);
  aktualizacja osobnym PR.
