# Tożsamość suity — jedna usługa logowania dla wszystkich aplikacji (ADR)

Data: 2026-11-22 · Status: **propozycja do przyjęcia przez właściciela** · Krok 13 z
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

**Rekomendacja: Keycloak**, uruchamiany jako usługa w `di-identity`, z konfiguracją w repozytorium (eksport realmu
albo narzędzie typu keycloak-config-cli [niezweryfikowane: wybór narzędzia]).

| Kandydat | Licencja | Za | Przeciw |
|---|---|---|---|
| **Keycloak** | Apache-2.0; projekt CNCF (incubating od 2023-04) | dojrzały; OIDC i SAML; federacja z zewnętrznymi dostawcami; od 26.x „Organizations” — drugi poziom najemców w jednym realmie, pod SaaS B2B; Flags już go używa lokalnie | ciężki (JVM), trzeba go utrzymywać i aktualizować; własny interfejs administracyjny jest dla specjalisty, nie dla administratora klienta |
| Zitadel | **AGPL-3.0 od v3 (2025-03)**; licencja komercyjna osobno | wielonajemność od początku, lekki | AGPL przy suicie SaaS to ryzyko prawne przy modyfikacjach; klient gRPC może podlegać AGPL (FAQ producenta) |
| authentik | rdzeń MIT, funkcje „Enterprise” (m.in. dziennik audytu) na osobnej licencji | prosty, dobry interfejs | część potrzebnych funkcji płatna; granica licencji mniej czytelna |
| Ory (Kratos, Hydra) | Apache-2.0 | elastyczny, lekki | trzeba złożyć kilka komponentów; więcej pracy własnej |
| usługa zarządzana (Auth0, WorkOS, Entra External ID) | komercyjna | zero utrzymania | koszt per użytkownik, zależność od dostawcy, dane poza nami [niezweryfikowane: ceny] |

Dlaczego Keycloak: jedyny kandydat z licencją bez warunków dla SaaS, z najemcami B2B i federacją w rdzeniu, a w suicie
już obecny. Koszt utrzymania jest realny; jeśli właściciel woli go nie ponosić, rozsądną alternatywą jest usługa
zarządzana — **[do decyzji]**.

### 2.2 Model: organizacja, osoba, uprawnienie do produktu

- **Jeden realm** `suite` na wdrożenie; **organizacja Keycloak = klient suity (najemca)**.
- **Osoba = użytkownik Keycloak.** Jej identyfikator w suicie to `sub` tokenu (stały UUID) — to wartość pola
  `actor.id` w kontrakcie i klucz powiązania kont w aplikacjach.
- **Uprawnienie do produktu = rola klienta (aplikacji)**: każdy produkt jest klientem OIDC (`di-decision`,
  `di-definition`, `di-release`, `di-release-control`, …) z własnymi rolami (`viewer`, `editor`, `admin`; produkt może
  mieć własne). Przypisanie roli w organizacji = „ta osoba ma DI Release jako edytor w organizacji Acme”.
- **Token dla aplikacji** niesie: `sub`, nazwę wyświetlaną, identyfikator organizacji, role tej aplikacji. E-mail
  tylko tam, gdzie aplikacja go potrzebuje (zaproszenia, powiadomienia).
- **Bez własnej bazy haseł:** logowanie zawsze przez dostawcę klienta (§2.3). Wyjątek: konto awaryjne administratora
  realmu, jak dostęp awaryjny w Flags (osobne hasło, każde użycie w dzienniku).

### 2.3 Federacja z dostawcą klienta

Organizacja ma przypisanego dostawcę tożsamości (Keycloak: dostawca powiązany z organizacją i domeną e-mail).
Na start: **ten dostawca, którym loguje się zespół pilotażu** — **[do decyzji]**. Kandydaci: Microsoft Entra ID
i Google (OIDC), GitHub (OAuth), Atlassian (OAuth 2.0; czy wystarcza jako dostawca w Keycloak bez dodatków —
[niezweryfikowane]).

### 2.4 Aplikacja do aplikacji

- **Tokeny usług:** każda aplikacja ma konto usługowe (client credentials) do wywołań API innych aplikacji.
- **Zdarzenia** zostają podpisane HMAC jak dziś (sekret per para nadawca–odbiorca); przejście na podpis tokenem
  usługi to osobna decyzja, gdy będzie więcej niż kilku nadawców.

### 2.5 Admin Console

AC1 (plan §2b) to interfejs `di-identity` nad Keycloak: organizacja, użytkownicy, zaproszenia, role w produktach,
podłączenie dostawcy klienta, dziennik zmian. Na start, przed własnym interfejsem, wystarczy wbudowana konsola
Keycloak dla właściciela suity; administratorowi klienta trzeba dać własny ekran, bo konsola Keycloak jest dla
specjalisty [niezweryfikowane: na ile Keycloak 26 pozwala ograniczyć administratora do jego organizacji].

## 3. Przejście aplikacji

Każde przejście to osobny PR w repozytorium aplikacji; dotychczasowe logowanie zostaje do przełączenia.

| Kolejność | Aplikacja | Co się zmienia | Uwagi |
|---|---|---|---|
| 1 | DI Release Control | wskazanie nowego wystawcy OIDC i mapowanie ról z roli klienta | ma już ogólny OIDC; najtańszy dowód |
| 2 | DI Definition | logowanie OIDC obok Atlassian; organizacje z tokenu zamiast własnych | dostęp do Jiry i Confluence dalej przez połączenie Atlassian przestrzeni — to nie logowanie |
| 3 | DI Release | logowanie OIDC zamiast OAuth GitHub; najemca z organizacji | aplikacja GitHub zostaje do czytania repozytoriów i wdrożeń |
| 4 | DI Decision | konsola jako usługa (DA4) z logowaniem OIDC; MCP z tokenem | razem z decyzją DA4 |
| 5 | fabryka (tf) | `started_by.id` z konta suity, gdy sesja ma token; inaczej tylko nazwa z gita | bez wymogu logowania w terminalu |

## 4. Konsekwencje

- Jedna osoba w całej suicie: „Started by”, „czeka na Ciebie”, kanał w komunikatorze i Admin Console mają na czym stać.
- Nowa usługa do utrzymania i nowy pojedynczy punkt awarii logowania: potrzebne SLO, kopie bazy Keycloak, plan
  aktualizacji (Keycloak wydaje często [niezweryfikowane: rytm wydań]) i dostęp awaryjny.
- Aplikacje działające poza suitą zachowują własne logowanie (zasada produktów sprzedawanych osobno).

## 5. Do decyzji właściciela

1. Silnik: Keycloak (rekomendacja) czy usługa zarządzana.
2. Pierwszy dostawca tożsamości klienta (ten, którego używa zespół pilotażu).
3. Hosting `di-identity` i stos szablonu usługi (`di-service-template`), razem z DA4.
4. Czy e-mail osoby może trafiać do aplikacji (zaproszenia, powiadomienia), czy tylko nazwa i `sub`.

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
