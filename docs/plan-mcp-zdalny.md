# Zdalny serwer MCP pdi z OAuth (etap 2 z `docs/14-pdi-standalone.md`) — plan

Stan: 2026-11-25, decyzje 1–8 przyjęte przez właściciela; kroki 1–4 zrobione (lokalnie), sprawdzone na żywo. Źródło zakresu: `TODO.md`, sekcja „Autoryzacja
zdalnego serwera MCP”, i ADR 17 (`docs/17-tozsamosc-suity.md`, wiersz DI Decision: „MCP z tokenem”). Wszystko
lokalnie: Keycloak z `dbqm45/di-identity` na `http://localhost:8180`, serwer MCP na `127.0.0.1`. Connector w Claude.ai
potrzebuje publicznego adresu https, więc przyjdzie razem z hostingiem (Hetzner). Do tego czasu klientem jest
Claude Code i klient MCP w testach.

## Co jest dziś

- `pdi-mcp` (`src/pdi/mcp_server.py`) działa tylko przez stdio. Nie ma logowania, a 33 narzędzia (17 do odczytu
  `_READ`, 16 do zapisu `_WRITE`) mają pełny dostęp do rejestru.
- Konsola loguje już przez suitę (`src/pdi/suite_login.py`, klient `di-decision` z rolami `viewer`, `editor`,
  `admin`). Ma tam weryfikację RS256 z JWKS wystawcy, sprawdzenie organizacji (`PDI_SUITE_ORGANIZATION`) i ról
  (`access()`: `viewer` czyta, `editor` i `admin` decydują). Ustala też `decided_by_id` z sesji (kontrakt 0.25.0).
- Sprawdzone 2026-11-25 w źródle:
  - SDK `mcp` 2.3.0 (w `.venv`) ma transport Streamable HTTP. Ma też tryb samego serwera zasobów: `AuthSettings` z
    `resource_server_url` i własny `TokenVerifier`. Serwuje wtedy metadane zasobu (RFC 9728) i odpowiada `401` z
    `WWW-Authenticate: … resource_metadata=…`. Zna wersje protokołu do `2026-07-28`, w tym bezstanowy rdzeń.
  - Claude Code 2.1.332 (`claude mcp add --help`): `--transport http`, `--client-id`, `--client-secret` i
    `--callback-port` dla serwerów z wcześniej zarejestrowanym adresem przekierowania.
  - W dystrybucji Keycloak 26.4.7 nie ma obsługi Client ID Metadata Documents. Lista funkcji (`Profile$Feature`) ma
    m.in. `CLIENT_POLICIES`, `DPOP` i `CLIENT_TYPES`, ale nic o dokumentach metadanych klienta. Jest za to
    dynamiczna rejestracja klientów (OIDC Client Registration z politykami).

## Decyzje do potwierdzenia (rekomendacja w każdej)

1. **Ten sam serwer, drugi transport.** `pdi-mcp --http` startuje `build_server()` przez Streamable HTTP pod
   `http://127.0.0.1:8790/mcp` (port w `PDI_MCP_PORT`). Narzędzia są te same co w stdio, a stdio zostaje bez
   logowania dla pracy na własnym komputerze. Serwer od razu działa bez sesji protokołu. Starsi klienci dostają
   obsługę `initialize` z SDK. Rekomendacja: tak.
2. **pdi jest tylko serwerem zasobów, a tokeny wydaje Keycloak suity** (realm `suite`). pdi nie ma własnego serwera
   autoryzacji. Metadane zasobu (`/.well-known/oauth-protected-resource/mcp`) wskazują wystawcę. Weryfikator
   sprawdza tylko RS256 z kluczem z JWKS wystawcy (nigdy wskazanym przez sam token), `iss`, `aud`, `exp` i `azp`.
   Opiera się na kodzie z `suite_login.py`, bez nowej zależności. Rekomendacja: tak.
3. **Rejestracja klienta: jeden wcześniej zarejestrowany klient publiczny `di-decision-mcp`** (PKCE S256, bez
   sekretu, bez e-maila — DI3). Adres przekierowania to pętla zwrotna Claude Code na stałym porcie
   (`http://localhost:33418/callback`, `--callback-port`). Adres Claude.ai dojdzie przy hostingu. Na razie bez
   dynamicznej rejestracji: anonimowa rejestracja w realmie `suite` to nowa powierzchnia ataku. Client ID Metadata
   Documents wrócą, gdy Keycloak je obsłuży. Zmiana w `dbqm45/di-identity` (`keycloak/suite.json`, `configure`)
   jako osobny, pierwszy PR. Rekomendacja: tak.
4. **Odbiorca tokenu:** mapper odbiorcy w kliencie `di-decision-mcp` dodaje `aud: di-decision`. Serwer MCP przyjmuje
   tylko tokeny z tym odbiorcą i z `azp: di-decision-mcp`. Role czyta z `resource_access.di-decision.roles`, czyli
   tych samych ról, które admin nadaje w Admin Console. Nie wiem jeszcze, czy Keycloak 26.4.7 przyjmuje parametr
   `resource` (RFC 8707) [niezweryfikowane], więc serwer go nie wymaga. Sprawdzę to testem na prawdziwym Keycloaku.
   Rekomendacja: tak.
5. **Uprawnienia do narzędzi wynikają z ról, nie z osobnych zakresów OAuth:**
   - `viewer`: narzędzia `_READ`;
   - `editor` i `admin`: także `_WRITE` (zapis decyzji, skrzynka, zgłoszenia, `supersede_decision`).

   Bez roli albo spoza `PDI_SUITE_ORGANIZATION` serwer odpowiada `403`. Przy `tools/list` osoba widzi tylko
   narzędzia, których może użyć. Zakresy z `TODO.md` (odczyt osobno od zapisu i od `supersede_decision`) dają to
   samo bez drugiego systemu uprawnień, który trzeba by trzymać w zgodzie z rolami. Karta zatwierdzenia (MCP Apps)
   zostaje osobnym krokiem. Rekomendacja: tak.
6. **Kto zdecydował, ustala token, nie argument.** Przez HTTP `decided_by_id` zawsze bierze się z `sub` tokenu.
   `decided_by` z argumentu zostaje (nazwisko podane przez człowieka), a bez niego bierze się nazwę z tokenu.
   Argument `decided_by_id` przez HTTP jest odrzucany. Rekomendacja: tak.
7. **Agenci (DI4) tylko czytają.** Token agenta (konto usługowe z właścicielem) dostaje wyłącznie `_READ`, bez
   względu na role. Zapisy zostają dla ludzi („AI szkicuje, człowiek zatwierdza”). Rekomendacja: tak.
8. **Tylko lokalnie w tym kroku:** nasłuch na `127.0.0.1`, http tylko z wystawcą na localhost (jak w `suite_login`).
   `sdlc up` startuje serwer HTTP obok konsoli, gdy suita jest skonfigurowana, i wypisuje polecenie
   `claude mcp add --transport http --client-id di-decision-mcp --callback-port 33418 pdi http://127.0.0.1:8790/mcp`.
   Rekomendacja: tak.

## Kroki

1. di-identity: klient `di-decision-mcp` w `keycloak/suite.json` i `configure` (publiczny, PKCE, mapper odbiorcy,
   bez e-maila). Do tego test na prawdziwym Keycloaku: token z kodu z PKCE ma `aud` `di-decision`, `azp`
   `di-decision-mcp` i role, a nie ma e-maila. Osobny PR, potem wydanie i `suite.yaml`.
2. pdi, czerwone testy: weryfikator (zły podpis, `alg`, `iss`, `aud`, `azp`, termin, brak organizacji, brak roli,
   agent), `401` z metadanymi zasobu, `403` dla narzędzia zapisu z rolą `viewer`, `tools/list` według roli,
   `decided_by_id` z tokenu. Klient MCP SDK z tokenami podpisanymi kluczem testowym, bez Keycloaka.
3. pdi, kod: `src/pdi/mcp_auth.py` (weryfikator, dostęp z ról), transport HTTP w `mcp_server.py`, `pdi-mcp --http`,
   `sdlc up`, README i `TODO.md` (odhaczone pozycje).
4. Na żywo: Claude Code z lokalnym Keycloakiem. `ola.test` (editor) zapisuje decyzję z `decided_by_id`, osoba z
   rolą `viewer` tylko czyta, `bez.roli` dostaje odmowę.

## Ryzyka

- Dziś każdy, kto ma lokalne stdio, ma pełny zapis. HTTP z OAuth tego nie zmienia; stdio zostaje dla jednej
  osoby na własnym komputerze.
- Tokeny osób żyją `personTokenSeconds` (realm). Odebranie roli w Admin Console działa dopiero od następnego tokenu.
- Specyfikacja i SDK zmieniają się szybko. Wersje sprawdzone wyżej mają datę 2026-11-25, a przed hostingiem trzeba
  je sprawdzić ponownie (Claude.ai, CIMD w Keycloaku).

## Co wyszło przy wdrożeniu (2026-11-25)

- **Zakresy.** Klient MCP z SDK (`OAuthClientProvider`, `mcp` 2.3.0) wybiera zakresy najpierw z `WWW-Authenticate`,
  potem ze `scopes_supported` w metadanych zasobu, a na końcu z całej listy wystawcy. Bez własnych prosił więc o
  wszystko, z `email`, a Keycloak odmawiał (`invalid_scope`). Dlatego metadane zasobu ogłaszają i serwer wymaga tylko
  `openid`. Role i organizacja przychodzą w domyślnych zakresach klienta.
- **`offline_access`: rozstrzygnięte przez właściciela 2026-11-25 (wariant a).** Ten sam klient dopisuje
  `offline_access`, gdy wystawca go ogłasza, a klient ma odświeżanie tokenów (SEP-2207). Bez tego zakresu u klienta
  Keycloak odrzuca logowanie. Zakres jest dozwolony tylko dla `di-decision-mcp` (dbqm45/di-identity#10). Sesja offline
  kończy się po 24 h bez użycia i najpóźniej po 14 dniach. Sprawdzone na żywo: klient prosi o `openid offline_access`
  i dostaje token odświeżania typu `Offline` na 24 h. Czy Claude Code też prosi o ten zakres, nie sprawdziłem
  [niezweryfikowane]; działa w obu przypadkach.
- **Odmowa zamiast `403`.** Osoba bez roli albo spoza organizacji dostaje pustą listę narzędzi, a wywołanie zwraca
  błąd narzędzia z powodem. Token bez `openid` dostaje `403` (`insufficient_scope`).
- **Parametr `resource` (RFC 8707).** Klient go wysyła, a Keycloak 26.4.7 przyjmuje go bez błędu. Odbiorcę i tak
  ustala mapper (`aud: di-decision`), więc serwer go nie wymaga.
- **Na żywo** (lokalny Keycloak, klient MCP z SDK z OAuth, przeglądarka przez Playwright):
  - `ola.test` (`editor`) widzi 33 narzędzia i zapisała decyzję z `decided_by_id` = `sub` i `decided_by`
    „Ola Test” z tokenu;
  - `adm.test` (`viewer`) widzi 17 narzędzi, a zapis dostał odmowę;
  - `bez.roli` i `bez.organizacji` nie widzą narzędzi i dostają odmowę z powodem;
  - token ma `azp: di-decision-mcp`, `aud: di-decision`, tylko role DI Decision i nie ma e-maila.
- Nie sprawdzone: logowanie z samego Claude Code (potrzebna przeglądarka na komputerze właściciela) i adres zwrotny
  `/callback` Claude Code [niezweryfikowane].
