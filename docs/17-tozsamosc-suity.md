# Tożsamość suity — jedna usługa logowania dla wszystkich aplikacji (ADR)

Data: 2026-11-22 · Status: **silnik przyjęty 2026-11-22 (Keycloak, DI1); pierwszy dostawca, stos i e-mail przyjęte 2026-11-23 (DI2, DA4, DI3); hosting Hetzner Cloud przyjęty 2026-11-23 (DA4a); tożsamość agenta (§2.6, AN1) — propozycja** · Krok 13 z
[`plan-budowy-suity.md`](plan-budowy-suity.md) (§2a, §2b, pytanie 4a) · Po przyjęciu: wpis w [`decyzje.md`](decyzje.md).

Miejsca oznaczone **[do decyzji]** wymagają odpowiedzi właściciela; **[niezweryfikowane]** — fakt, którego nie
sprawdziłem w dokumentacji ani w kodzie.

## 1. Kontekst

Przyjęte 2026-11-22: **jedna usługa tożsamości, której ufają wszystkie aplikacje suity** (wzorzec pakietów takich
jak Adobe Creative Cloud), z **Admin Console** jako jej interfejsem dla administratora klienta. Repozytorium:
`dbqm45/di-identity` (założone, prywatne, puste).

Stan dziś (sprawdzony w kodzie 2026-11-22):

| Aplikacja | Logowanie | Role i organizacje |
|---|---|---|
| DI Decision (pdi) | token sesji w adresie konsoli; serwer MCP bez logowania | brak |
| DI Definition (ci_for_sdlc) | Atlassian, opcjonalnie (`CI_AUTH_MODE=accounts`) | własne organizacje, role, zaproszenia |
| DI Release (ShipScope) | GitHub (OAuth aplikacji GitHub) | najemcy w bazie (RLS), członkostwo |
| DI Release Control (Flags) | dowolny dostawca OIDC (Keycloak w `docker-compose` do testów) | rola z roszczeń tokenu; jedna organizacja |
| DI Quality, sprintdeck | brak (sprintdeck: anonimowe logowanie Supabase) | brak |

Żadna aplikacja nie wie, że „Ola” w jednej to „Ola” w drugiej; pole `started_by.id` w kontrakcie 0.15 czeka właśnie
na ten identyfikator.

## 2. Decyzja (propozycja)

### 2.1 Silnik: Keycloak

**Przyjęte 2026-11-22 (decyzja właściciela, DI1): Keycloak**, uruchamiany jako usługa w `di-identity`, z konfiguracją w repozytorium (eksport realmu
albo narzędzie typu keycloak-config-cli [niezweryfikowane: wybór narzędzia]).

| Kandydat | Licencja | Za | Przeciw |
|---|---|---|---|
| **Keycloak** | Apache-2.0; projekt CNCF (incubating od 2023-04) | dojrzały; OIDC i SAML; federacja z zewnętrznymi dostawcami; od 26.x „Organizations” — drugi poziom najemców w jednym realmie, pod SaaS B2B; Flags już go używa lokalnie | ciężki (JVM), trzeba go utrzymywać i aktualizować; własny interfejs administracyjny jest dla specjalisty, nie dla administratora klienta |
| Zitadel | **AGPL-3.0 od v3 (2025-03)**; licencja komercyjna osobno | wielonajemność od początku, lekki | AGPL przy suicie SaaS to ryzyko prawne przy modyfikacjach; klient gRPC może podlegać AGPL (FAQ producenta) |
| authentik | rdzeń MIT, funkcje „Enterprise” (m.in. dziennik audytu) na osobnej licencji | prosty, dobry interfejs | część potrzebnych funkcji płatna; granica licencji mniej czytelna |
| Ory (Kratos, Hydra) | Apache-2.0 | elastyczny, lekki | trzeba złożyć kilka komponentów; więcej pracy własnej |
| usługa zarządzana (Auth0, WorkOS, Entra External ID) | komercyjna | zero utrzymania | koszt per użytkownik, zależność od dostawcy, dane poza nami [niezweryfikowane: ceny] |

Dlaczego Keycloak: jedyny kandydat z licencją bez warunków dla SaaS, z najemcami B2B i federacją w rdzeniu, a w suicie
już obecny. Koszt utrzymania (aktualizacje, kopie, dostępność) bierzemy na siebie; aplikacje rozmawiają z nim przez
OpenID Connect, więc silnik da się później wymienić bez przepisywania aplikacji.

### 2.2 Model: organizacja, osoba, uprawnienie do produktu

- **Jeden realm** `suite` na wdrożenie; **organizacja Keycloak = klient suity (najemca)**.
- **Osoba = użytkownik Keycloak.** Jej identyfikator w suicie to `sub` tokenu (stały UUID) — to wartość pola
  `actor.id` w kontrakcie i klucz powiązania kont w aplikacjach.
- **Uprawnienie do produktu = rola klienta (aplikacji)**: każdy produkt jest klientem OIDC (`di-decision`,
  `di-definition`, `di-release`, `di-release-control`, …) z własnymi rolami (`viewer`, `editor`, `admin`; produkt może
  mieć własne). Przypisanie roli w organizacji = „ta osoba ma DI Release jako edytor w organizacji Acme”.
- **Token dla aplikacji** niesie: `sub`, nazwę wyświetlaną, identyfikator organizacji, role tej aplikacji. E-mail
  tylko tam, gdzie aplikacja go potrzebuje (zaproszenia, powiadomienia) — **przyjęte 2026-11-23 (DI3)**: zakres
  `email` przypisany tylko klientom tych aplikacji w Keycloak (na start DI Channels i Admin Console).
- **Bez własnej bazy haseł:** logowanie zawsze przez dostawcę klienta (§2.3). Wyjątek: konto awaryjne administratora
  realmu, jak dostęp awaryjny w Flags (osobne hasło, każde użycie w dzienniku).

### 2.3 Federacja z dostawcą klienta

Organizacja ma przypisanego dostawcę tożsamości (Keycloak: dostawca powiązany z organizacją i domeną e-mail).
**Pierwszy dostawca: Google (OIDC) — przyjęte 2026-11-23 (DI2).** W Keycloak to dostawca wbudowany.

- **Klient OAuth** w Google Cloud (typ „Web application”), adres przekierowania Keycloak
  (`…/realms/suite/broker/google/endpoint`), zakresy `openid email profile`.
- **Weryfikacja aplikacji nie jest potrzebna** dla samych zakresów podstawowych. W stanie „Testing” Google
  ogranicza aplikację do 100 użytkowników testowych z listy, a ich zgody wygasają po 7 dniach; jedna strona
  Google mówi, że przy samych `openid email profile` logować się może każdy (z ostrzeżeniem o trybie
  testowym) — **[niezweryfikowane na naszym projekcie]**, sprawdzić przy kroku 14. Na pilotaż wystarcza każdy
  wariant; przed pierwszym klientem — stan „In production” (dla zakresów podstawowych bez przeglądu Google).
- **Organizacja po domenie:** konto Google Workspace ma w tokenie `hd` (domena); organizacja Keycloak ma
  przypisaną domenę, więc osoba z `@acme.com` trafia do organizacji Acme. Konto bez Workspace (gmail.com) nie ma
  `hd` i nie dostaje organizacji automatycznie — tylko przez zaproszenie z Admin Console (AC1).
- **Kolejni dostawcy później**, każdy osobnym krokiem: Microsoft Entra ID (wymaga administratora tenanta klienta),
  GitHub (OAuth, bez domeny w tokenie), Atlassian (OAuth 2.0; czy wystarcza jako dostawca w Keycloak bez
  dodatków — [niezweryfikowane]).

### 2.4 Aplikacja do aplikacji

- **Tokeny usług:** każda aplikacja ma konto usługowe (client credentials) do wywołań API innych aplikacji. Konto
  usługowe aplikacji to nie agent: działa w imieniu aplikacji (synchronizacja, odczyt), nie wykonuje pracy za
  człowieka. Agenci mają osobne konta (§2.6).
- **Zdarzenia** zostają podpisane HMAC jak dziś (sekret per para nadawca–odbiorca); przejście na podpis tokenem
  usługi to osobna decyzja, gdy będzie więcej niż kilku nadawców.

### 2.5 Admin Console

AC1 (plan §2b) to interfejs `di-identity` nad Keycloak: organizacja, użytkownicy, zaproszenia, role w produktach,
podłączenie dostawcy klienta, dziennik zmian. Na start, przed własnym interfejsem, wystarczy wbudowana konsola
Keycloak dla właściciela suity; administratorowi klienta trzeba dać własny ekran, bo konsola Keycloak jest dla
specjalisty [niezweryfikowane: na ile Keycloak 26 pozwala ograniczyć administratora do jego organizacji].

### 2.6 Agent jako podmiot (AN1, dopisane 2026-11-23)

Propozycja; punkty **[do decyzji]** niżej. Powód: audyt musi odróżniać pracę agenta od pracy człowieka i zawsze
wskazać człowieka odpowiedzialnego; macierz uprawnień agentów (T8 planu programu) i wyłącznik agentów (AN6) potrzebują
podmiotu, któremu nadaje się i odbiera uprawnienia. Dziś agent występuje tylko jako nazwa persony w `run.started`
(`agent`) i jako aplikacja GitHub dla commitów (DZ10).

**Model.**

- **Agent = konto w Keycloak typu klient z kontem usługowym** (client credentials), z identyfikatorem
  `agent-<nazwa>` w realmie `suite`. Jego `sub` w tokenie to identyfikator agenta w suicie, jak `sub` osoby.
- **Jednostka: jedna definicja agenta w jednej organizacji**, nie jeden przebieg. Przykład: persona fabryki
  `tomasz` w organizacji Acme to jedno konto; każdy przebieg tej persony używa tego samego konta, a przebieg odróżnia
  pole `run` w zdarzeniach. **[do decyzji]** Rekomendacja: konto per persona i organizacja; konto per repozytorium
  dopiero, gdy uprawnienia agenta muszą się różnić między repozytoriami.
- **Atrybuty konta (obowiązkowe):** `kind: agent`, `owner` (`sub` człowieka odpowiedzialnego), organizacja, cel
  jednym zdaniem, `review_by` (data przeglądu; domyślnie 90 dni). Bez właściciela agenta nie da się utworzyć.
- **Uprawnienia:** role klientów aplikacji, jak u osoby, ale **nigdy `admin`** i nigdy role, które pozwalają
  zatwierdzać. Zakres na start: `viewer` w aplikacjach, które agent czyta, i wąskie role robocze (np. wysyłka
  zdarzeń do DI Decision).

**Token agenta.**

- Niesie `sub` agenta, `kind: agent`, `owner`, organizację i role (mappery atrybutów w Keycloak). Aplikacja zawsze
  sprawdza `kind`; token bez `kind` traktuje jak token osoby tylko wtedy, gdy pochodzi z logowania osoby.
- **Krótki:** czas życia 10 minut **[do decyzji]**, bez tokenu odświeżania; kolejny pobiera się przy potrzebie.
- **Uwierzytelnienie klienta agenta podpisanym JWT** (`private_key_jwt`) zamiast współdzielonego sekretu, jeśli
  Keycloak na to pozwala dla kont usługowych [niezweryfikowane]; klucz prywatny poza kontenerem fazy.
- **Zgodnie z DZ9 poświadczenia zostają poza kontenerem fazy:** token pobiera proces na hoście (pdi albo tf), a do
  kontenera trafia tylko krótki token dostępu dla konkretnej wywoływanej aplikacji, nigdy klucz klienta.
- **W czyim imieniu:** przebieg uruchomiony przez człowieka niesie go w `started_by` (kontrakt 0.15), jak dziś.
  Delegacja w samym tokenie (wymiana tokenu, roszczenie `act` z RFC 8693) dopiero, gdy aplikacja będzie musiała
  sprawdzać uprawnienia człowieka, a nie agenta [niezweryfikowane: obsługa `act` w Keycloak 26].

**Zasady w aplikacjach.**

1. Agent nie zatwierdza bramek ani decyzji poziomu 3 (DA1) i typów chronionych (DA2): trasa zatwierdzania odrzuca
   token z `kind: agent`, niezależnie od ról.
2. Każdy zapis zmian w aplikacji zapamiętuje `sub` agenta i jego `owner`; dziennik pokazuje oba.
3. Agent czyta tylko dane swojej organizacji; dane spoza niej nie istnieją dla jego tokenu.

**Cykl życia.** Tworzy administrator organizacji w Admin Console (rozszerzenie AC1), z właścicielem i celem.
Wyłączenie właściciela w organizacji zawiesza jego agentów. Przy `review_by` właściciel potwierdza albo agent jest
zawieszany. **Wyłącznik (AN6):** wyłączenie konta agenta w Keycloak blokuje nowe tokeny od razu, a wydane wygasają
w ciągu czasu życia tokenu; wyłącznik organizacji wyłącza naraz wszystkie konta z `kind: agent` w organizacji.

**Związek z aplikacją GitHub (DZ10).** Commity i PR podpisuje aplikacja GitHub dla agentów: to tożsamość w GitHubie.
Tożsamość suity dotyczy API suity. Łączy je przebieg: `run.started` niesie `sub` agenta, a PR z tego przebiegu jest
zapisany w `run.finished`, więc audyt wiąże commit z agentem i właścicielem.

**Zmiany potrzebne poza tym dokumentem.**

| Gdzie | Zmiana | Kiedy |
|---|---|---|
| `di-contract` | `actor.kind` dostaje wartość `agent` i opcjonalne `owner` (`sub` człowieka); `run.started` może nieść `sub` agenta w nowym polu `agent_id` obok nazwy persony; zgodnie wstecz | przed pierwszym agentem z kontem (po kroku 14) |
| `di-service-template` | `Identity` z `kind` i `owner`; `requireHuman` do tras zatwierdzania | razem z krokiem 14 |
| `di-identity` (krok 14) | mappery `kind` i `owner`, typ konta agenta, wyłącznik organizacji | krok 14 i AC1 |
| tf | pobieranie tokenu agenta na hoście, `agent_id` w zdarzeniach przebiegu | po zmianie kontraktu |

## 3. Przejście aplikacji

Każde przejście to osobny PR w repozytorium aplikacji; dotychczasowe logowanie zostaje do przełączenia.

| Kolejność | Aplikacja | Co się zmienia | Uwagi |
|---|---|---|---|
| 1 | DI Release Control | wskazanie nowego wystawcy OIDC i mapowanie ról z roli klienta | ma już ogólny OIDC; najtańszy dowód |
| 2 | DI Definition | logowanie OIDC obok Atlassian; organizacje z tokenu zamiast własnych | dostęp do Jiry i Confluence dalej przez połączenie Atlassian przestrzeni — to nie logowanie |
| 3 | DI Release | logowanie OIDC zamiast OAuth GitHub; najemca z organizacji | aplikacja GitHub zostaje do czytania repozytoriów i wdrożeń |
| 4 | DI Decision | konsola jako usługa (DA4) z logowaniem OIDC; MCP z tokenem | razem z decyzją DA4 |
| 5 | fabryka (tf) | `started_by.id` z konta suity, gdy sesja ma token; inaczej tylko nazwa z gita; persony z kontem agenta (§2.6) | bez wymogu logowania w terminalu |

## 4. Konsekwencje

- Jedna osoba w całej suicie: „Started by”, „czeka na Ciebie”, kanał w komunikatorze i Admin Console mają na czym stać.
- Nowa usługa do utrzymania i nowy pojedynczy punkt awarii logowania: potrzebne SLO, kopie bazy Keycloak, plan
  aktualizacji (Keycloak wydaje często [niezweryfikowane: rytm wydań]) i dostęp awaryjny.
- Agent ma tożsamość, właściciela i wyłącznik w jednym miejscu (§2.6); koszt: konto do utrzymania dla każdej persony
  w każdej organizacji i przegląd co 90 dni.
- Aplikacje działające poza suitą zachowują własne logowanie (zasada produktów sprzedawanych osobno).

## 5. Do decyzji właściciela

1. ~~Silnik~~ — przyjęte: Keycloak (DI1).
2. ~~Pierwszy dostawca tożsamości~~ — przyjęte 2026-11-23: Google (DI2, §2.3).
3. Stos — przyjęte 2026-11-23 (DA4): usługi suity w **TypeScript + Fastify + Postgres** z wzorcami ShipScope,
   serwer MCP pdi w Pythonie; Keycloak, di-identity i później usługa pdi na **jednym tanim hostingu kontenerów**.
   **Dostawca hostingu: Hetzner Cloud — przyjęte 2026-11-23 (DA4a)**: maszyna wirtualna w UE, Docker Compose,
   Caddy z certyfikatem TLS; wzór w `dbqm45/di-service-template` (`compose.yaml`). Rozważane propozycje (ceny z porównań w sieci
   z 2026, **nie sprawdzone na stronach dostawców**; Keycloak potrzebuje ok. 1–2 GB RAM, cały zestaw z Postgresem
   ok. 4 GB):

   | Dostawca | Model | Szacunkowy koszt / mies. | Za | Przeciw |
   |---|---|---|---|---|
   | **Hetzner Cloud** (wybrany) | maszyna wirtualna (np. CX22, 2 vCPU / 4 GB) + Docker Compose + reverse proxy z TLS | ok. 4–5 EUR za maszynę, 8–15 EUR z większą maszyną i kopiami | najtańszy; centra danych w UE (RODO); Docker już jest w stosie lokalnym (DL2, DZ9), więc ten sam Compose | aktualizacje systemu, kopie bazy i monitoring po naszej stronie; ceny rosły w 2026 |
   | **Fly.io** | maszyny z obrazów, Postgres zarządzany albo własny | rzędu 20–80 USD przy Keycloak + Postgres | wdrożenie z obrazu, TLS i regiony w UE bez administrowania maszyną | koszt rośnie z RAM (Keycloak jest pamięciożerny); cennik zmieniał się w 2026 |
   | **Railway** | kontenery i Postgres jednym kliknięciem, rozliczenie za zużycie | 5 USD planu + zużycie, rzędu 20–40 USD | najmniej konfiguracji, podgląd z gałęzi | koszt trudniejszy do przewidzenia; mniej kontroli nad regionem i kopiami |

4. ~~E-mail osoby~~ — przyjęte 2026-11-23 (DI3, §2.2): tylko dla aplikacji, które go potrzebują.
5. Tożsamość agenta (§2.6, AN1): konto per persona i organizacja czy per repozytorium; czas życia tokenu agenta
   (rekomendacja: 10 minut). Do przyjęcia przed krokiem 14, bo zmienia model danych `di-identity`.

Kolejne kroki planu po przyjęciu: 13a `di-service-template`, 14 `di-identity` (usługa + AC1), potem przejście
aplikacji wg §3, zaczynając od DI Release Control.

## Źródła (sprawdzone 2026-11-22)

- Keycloak: licencja Apache-2.0, projekt CNCF od 2023-04, „Organizations” w 26.x —
  [cncf.io/projects/keycloak](https://www.cncf.io/projects/keycloak),
  [porównanie Keycloak i Zitadel](https://skycloak.io/blog/keycloak-vs-zitadel-comparison/).
- Zitadel: AGPL-3.0 od v3 (2025-03), licencja komercyjna osobno, uwaga o klientach gRPC —
  [zitadel.com/blog/apache-to-agpl](https://zitadel.com/blog/apache-to-agpl),
  [zitadel.com/license-faq](https://zitadel.com/license-faq).
- authentik: rdzeń MIT, kod Enterprise na osobnej licencji —
  [docs.goauthentik.io/enterprise](https://docs.goauthentik.io/enterprise/),
  [github.com/goauthentik/authentik](https://github.com/goauthentik/authentik).
- Stan logowania w aplikacjach: przeglądy repozytoriów 2026-11-22 (artefakt „Delivery Intelligence Suite v3”).
- Google (sprawdzone 2026-11-23): limit 100 użytkowników testowych i wygasanie zgód po 7 dniach —
  [support.google.com/cloud/answer/15549945](https://support.google.com/cloud/answer/15549945); zakresy podstawowe
  bez listy użytkowników testowych —
  [developers.google.com/identity/protocols/oauth2/production-readiness/overview](https://developers.google.com/identity/protocols/oauth2/production-readiness/overview);
  aplikacje niezweryfikowane — [support.google.com/cloud/answer/7454865](https://support.google.com/cloud/answer/7454865).
- Hosting (porównania z 2026, nie strony cenników dostawców):
  [getdeploying.com/flyio-vs-hetzner](https://getdeploying.com/flyio-vs-hetzner),
  [getdeploying.com/hetzner-vs-railway](https://getdeploying.com/hetzner-vs-railway),
  [betterstack.com — Hetzner Cloud Review 2026](https://betterstack.com/community/guides/web-servers/hetzner-cloud-review/).
