# Instrukcja użytkownika DI Suite

Instrukcja dla osób, które pracują w Delivery Intelligence Suite (DI Suite): co suita daje, z jakich produktów się
składa i jak przejść każdy proces od początku do końca. Opisuje to, co widzi użytkownik, a nie to, jak działa kod.
Szczegóły techniczne są w README każdego produktu i w planach w `docs/`.

Stan opisu: 2026-11-26, wydanie suity 2026.11 (`dbqm45/di-contract`, `suite.yaml`). Nazwy przycisków i stron są
przepisane z kodu produktów. Interfejsy są po angielsku, a konsola pdi częściowo po polsku, więc etykiety podaję tak,
jak je widać na ekranie. Miejsca, których nie sprawdzono w kodzie, są oznaczone „(nie sprawdzono)”.

## Spis treści

1. [Co daje DI Suite](#co-daje-di-suite)
2. [Logowanie i dostęp](#logowanie-i-dostęp)
3. [Administracja organizacji](#administracja-organizacji)
4. [Cała ścieżka: od problemu do oceny skutku](#cała-ścieżka-od-problemu-do-oceny-skutku)
5. [Jak zgłosić problem albo pomysł](#jak-zgłosić-problem-albo-pomysł)
6. [Jak przyjąć albo odrzucić zgłoszenie (triaż)](#jak-przyjąć-albo-odrzucić-zgłoszenie-triaż)
7. [Jak prowadzić zmianę z agentem](#jak-prowadzić-zmianę-z-agentem)
8. [Jak sprawdzić gotowość historyjki](#jak-sprawdzić-gotowość-historyjki)
9. [Jak podjąć decyzję na bramce](#jak-podjąć-decyzję-na-bramce)
10. [Jak przedyskutować sprawę z zespołem](#jak-przedyskutować-sprawę-z-zespołem)
    - [Jak eskalować sprawę poza zespół](#jak-eskalować-sprawę-poza-zespół)
11. [Jak śledzić wdrożenia i status wydania](#jak-śledzić-wdrożenia-i-status-wydania)
12. [Jak zarządzać flagami funkcji](#jak-zarządzać-flagami-funkcji)
13. [Jak ocenić skutek wydania i pilnować metryk](#jak-ocenić-skutek-wydania-i-pilnować-metryk)
14. [Jak zobaczyć, co się dzieje](#jak-zobaczyć-co-się-dzieje)
15. [Rejestr decyzji](#rejestr-decyzji)
16. [Praca z agentem Claude (MCP)](#praca-z-agentem-claude-mcp)
17. [Slack](#slack)
18. [Sprintdeck](#sprintdeck)
19. [Cała suita na jednym komputerze](#cała-suita-na-jednym-komputerze)
20. [Słowniczek](#słowniczek)

## Co daje DI Suite

DI Suite prowadzi zmianę w produkcie od problemu zgłoszonego przez człowieka do sprawdzenia, czy wydanie coś
poprawiło. Agenci AI wykonują pracę: piszą intencję, wymagania, plan, kod i PR. Ludzie podejmują decyzje na
bramkach. Każda decyzja jest zapisana z uzasadnieniem i śladem, skąd przyszła. Suita odpowiada na pytania:
- co czeka na moją decyzję i do kiedy;
- czy historyjka jest gotowa do realizacji i czego w niej brakuje;
- gdzie jest kod tej zmiany i czy funkcja jest już widoczna dla użytkowników na PROD;
- dlaczego coś postanowiliśmy, kto i kiedy;
- czy wydanie dało efekt, który obiecywała intencja.

| Produkt | Repozytorium | Co daje | Gdzie |
| --- | --- | --- | --- |
| **DI Decision** (pdi) | `dbqm45/pdi` | skrzynka decyzji i bramek, rejestr decyzji, zgłoszenia, ocena skutku, prognoza, tablice postępu, pytanie zespołu i agenda dyskusji | konsola w przeglądarce, lokalnie `http://127.0.0.1:8788/` |
| **DI Agent Factory** (tf) | `dbqm45/tf` | agenci Claude Code, którzy przeprowadzają zmianę przez fazy i zadania aż do PR | Claude Code w repozytorium produktu |
| **DI Definition** | `dbqm45/ci_for_sdlc` | gotowość historyjek i epików w ośmiu wymiarach, ustalenia z dowodami, drift po zatwierdzeniu; w interfejsie marka „Quorum” | przeglądarka, lokalnie `http://localhost:4317` |
| **DI Release** (ShipScope) | `dbqm45/evdt-service-shipscope` | wdrożenia, flagi i zadania Jiry w jednym widoku: co jest na którym środowisku i czy jest widoczne dla użytkowników | przeglądarka, lokalnie `http://localhost:3000/` |
| **DI Release Control** (ShipScope Flags) | `dbqm45/evdt-shipscope-flags` | zarządzanie flagami funkcji w środowiskach test → qa → prod, z kolejnością i zależnościami | przeglądarka, lokalnie `http://localhost:5173` |
| **DI Channels** | `dbqm45/di-channels` | Slack: pytanie do historyjki z wiadomości, prywatne „czeka na Twoją decyzję” | Slack |
| **DI Identity** | `dbqm45/di-identity` | jedno logowanie do wszystkich produktów, organizacje, role, agenci; konsola administratora | logowanie suity; konsola `http://127.0.0.1:3200/admin` |

Produkty wymieniają zdarzenia według wspólnego kontraktu (`dbqm45/di-contract`): tf i DI Definition proszą pdi o
decyzję na bramce, pdi odsyła decyzję, a DI Release zgłasza zmianę etapu flagi i wydanie.

## Logowanie i dostęp

Wszystkie produkty logują przez **DI Identity** (Keycloak, realm `suite`). Nie ma osobnych haseł w produktach ani
samodzielnej rejestracji: do suity wchodzi tylko osoba dodana do organizacji.

Jak się zalogować:
1. Otwórz produkt i wybierz logowanie przez suitę (w DI Release i DI Definition przycisk „Log in with the suite”
   albo strona wyboru; konsola pdi przekierowuje od razu).
2. Keycloak pyta najpierw o nazwę użytkownika albo adres e-mail.
3. Jeśli Twoja organizacja ma własnego dostawcę tożsamości, a adres jest w jej domenie, trafisz do niego. W
   przeciwnym razie logujesz się przez Google.
4. Po zalogowaniu wracasz do produktu. Dostęp zależy od roli w tym produkcie.

Role w produktach (`keycloak/suite.json`):

| Produkt | Role |
| --- | --- |
| DI Decision | `viewer`, `editor`, `admin` |
| DI Definition | `viewer`, `editor`, `admin` |
| DI Release | `viewer`, `editor`, `admin` |
| DI Release Control | `viewer`, `editor`, `admin` |
| DI Channels | `viewer`, `admin` |
| DI Admin (konsola administratora) | `admin` |

Ogólnie: `viewer` czyta, `editor` zmienia i decyduje, `admin` także ustawia produkt. Szczegóły są przy każdym
procesie. Osoba bez roli w produkcie albo spoza organizacji zobaczy odmowę dostępu.

Produkty dostają tylko to, czego potrzebują: e-mail osoby trafia wyłącznie do DI Channels i konsoli administratora.
Pozostałe znają Cię po identyfikatorze i wyświetlanej nazwie.

## Administracja organizacji

Dla administratora organizacji (rola `di-admin:admin`). Konsola: `http://127.0.0.1:3200/admin`, adres strony
`/admin/o/<organizacja>/<strona>`. Lokalnie i przez tunel; z hostingiem dostanie osobną domenę.

| Strona | Co na niej zrobisz |
| --- | --- |
| **People** | lista osób organizacji z rolami; **Add a person by e-mail** (osoba musi się raz zalogować); **Grant** i odebranie roli w produkcie; usunięcie osoby |
| **Invitations** | **Create an invitation link**: wybierasz role, konsola pokazuje link raz; link działa raz i przez 7 dni; otwarte zaproszenie można odwołać |
| **Agents** | agenci organizacji z właścicielem, celem i datą przeglądu; wyłączenie i włączenie agenta; wyłącznik wszystkich agentów organizacji |
| **Sign-in** | własny dostawca tożsamości organizacji, OpenID Connect (wystawca, identyfikator i sekret klienta) albo SAML 2.0 (adres metadanych), oraz domena; **Save** |
| **Change log** | kto, co i kiedy zmienił (When, Who, What, About) |

### Jak zaprosić osobę

1. **Invitations** → wybierz role w produktach → **Create an invitation link**.
2. Skopiuj link od razu, bo konsola pokaże go tylko raz. Wyślij go sam: poczty jeszcze nie ma.
3. Osoba otwiera link i loguje się przez suitę. Trafia do organizacji i dostaje role z zaproszenia. Widzi stronę
   „You joined <organizacja>”.
4. W **Change log** pojawiają się utworzenie i przyjęcie zaproszenia.

### Jak podłączyć logowanie organizacji

Organizacja ma jednego dostawcę: OpenID Connect albo SAML 2.0. Zapisanie drugiego rodzaju zastępuje poprzedniego.

**OpenID Connect:**

1. **Sign-in** → podaj wystawcę (https), identyfikator i sekret klienta u swojego dostawcy, wybierz domenę → **Save**.
2. Od tej chwili osoby z tej domeny przy logowaniu trafiają do Waszego dostawcy. Przy pierwszym logowaniu powstaje
   nowe konto członka organizacji; konta, które już istnieją (np. z Google), logują się po staremu.
3. Role nadajesz dalej w konsoli, nie u dostawcy. Sekret zostaje w Keycloaku i nie jest nigdzie pokazywany.

**SAML 2.0** (np. AD FS, Entra ID, Okta):

1. U swojego dostawcy dodaj suitę jako usługodawcę z jej metadanych. Adres metadanych pokazuje strona **Sign-in**
   (`…/broker/org-<organizacja>/endpoint/descriptor`); odpowiedź idzie przez HTTP-POST na adres `…/endpoint`.
   Ustaw trwały identyfikator (NameID `persistent`) i podpisuj asercje. Jeśli możesz, wysyłaj e-mail, imię i
   nazwisko (atrybuty X.500 albo roszczenia Microsoftu); inaczej osoba poda je raz przy pierwszym logowaniu.
2. **Sign-in** → w części **SAML 2.0 provider** podaj adres metadanych swojego dostawcy (https), wybierz domenę →
   **Save**. Metadane bez certyfikatu podpisu są odrzucane.
3. Dalej jak przy OpenID Connect: nowe konto członka organizacji przy pierwszym logowaniu, role z konsoli.

### Agenci

Agent to osobny podmiot z właścicielem (osobą), celem i datą przeglądu (90 dni). Nigdy nie dostaje roli `admin`.
Agenta zakłada się poleceniem (`npm run identity -- agent create …`), a w konsoli się go wyłącza. Wyłącznik
organizacji zatrzymuje wszystkich agentów naraz.

Bez konsoli to samo robią polecenia w repo di-identity:

```bash
npm run identity -- role grant di-decision:editor <osoba>
```

Pozostałe: `org create`, `org add-member`, `role revoke`, `agent create`, `agent list`, `agent disable`,
`agent enable`, `agent disable-all` (README di-identity, „Polecenia”).

## Cała ścieżka: od problemu do oceny skutku

Tak wygląda jedna zmiana w suicie. Każdy krok ma osobny rozdział niżej.

1. **Zgłoszenie.** Ktoś zgłasza problem albo pomysł (PRB-n) w formularzu albo przez agenta.
2. **Triaż.** Decydent w Skrzynce DI Decision przyjmuje zgłoszenie (powstaje zmiana CHG-n) albo je odrzuca z
   powodem.
3. **Intencja → B1.** Agent tf pisze `intent.md`: problem, opcje z kosztem, wybór, metryka sukcesu. pdi dostaje
   prośbę o bramkę B1 (kierunek).
4. **Wymagania → B2.** Agent pisze wymagania; DI Definition sprawdza gotowość. Bramka B2.
5. **Plan → B3.** Agent dzieli zmianę na cięcia TSK-n i linie wydania R1…Rn (`plan.md`, `release.yaml`). Bramka B3
   (plan i cele), przy niej prognoza czasu.
6. **Design** (gdy potrzebny) → `design-review`, potem **approve-for-implementation**.
7. **Budowa.** Agent przechodzi cięcia: test, kod, commit, PR. Człowiek scala PR.
8. **Wdrożenie.** Pipeline wdraża na test, qa, prod; DI Release pokazuje, co jest gdzie i czy funkcja jest
   widoczna (flagi).
9. **Wydanie.** B4 (gotowość do wydania) i B5 (autoryzacja wydania na PROD). Dziś tf o nie nie prosi, więc
   decydent wpisuje je w Skrzynce sam. Potem flaga przechodzi etapy na PROD; każdy etap na PROD to bramka w pdi.
10. **Ocena skutku.** Po wydaniu linii R1 (MVP) pdi otwiera ocenę: decydent ustala `met`, `not_met` albo `unknown`.
    Zgłaszający dostaje powiadomienia po triażu, wydaniu i ocenie.

W każdej chwili, gdy sprawa jest sporna, decydent może zapytać zespół i przenieść ją na spotkanie (rozdział 10).

Bramka nigdy nie zatwierdza się sama. Każda ma termin (rozdział 9); po przekroczeniu suita przypomina, a potem
wstrzymuje zmianę.

## Jak zgłosić problem albo pomysł

Dla każdego, kto widzi problem: użytkownika, wsparcia, członka zespołu.

Sposoby:
- **Formularz w przeglądarce** `/problems/new?t=<token>` w konsoli pdi (gdy administrator ustawił `PDI_FORM_TOKEN`;
  `uv run sdlc open` otwiera go razem z konsolą). Wpisujesz: kto ma problem, czego nie może zrobić, jaki jest
  skutek.
- **Przez agenta Claude** z serwerem MCP pdi: poproś o zapisanie zgłoszenia (narzędzie `record_problem`, rodzaj
  `problem` albo `idea`).
- **Automatycznie:** gdy metryka PROD wyjdzie poza pasmo kontrolne, tf zgłasza problem sam (rozdział 13).

Co dalej: zgłoszenie dostaje numer PRB-n i trafia do triażu. Agent może dopytać (do 5 pytań, status `clarifying`) i
poszukać podobnych zgłoszeń. Zgłaszający dostaje powiadomienie po triażu, po wydaniu i po ocenie skutku.

## Jak przyjąć albo odrzucić zgłoszenie (triaż)

Dla decydenta (`editor` albo `admin` w DI Decision).

1. Konsola pdi → **Skrzynka** → sekcja **Zgłoszenia do triażu** (statusy `new`, `clarifying`,
   `ready_for_triage`).
2. Przeczytaj zgłoszenie. Agent tf może dać rekomendację, ale decydujesz Ty.
3. Wybierz:
   - **accept (załóż CHG)**: powstaje zmiana CHG-n i rusza faza intencji;
   - **reject** z powodem z listy: poza strategią, działa zgodnie z założeniem, koszt nieproporcjonalny, już
     istnieje, poza zakresem, bez kodu, inny. Przy „bez kodu” podaj rodzaj (konfiguracja, zmiana procesu,
     istniejąca funkcja) i opis.
4. Zgłaszający dostaje powiadomienie.

Na tej samej karcie są też **park** (wpisz warunek powrotu, np. „3 nowe zgłoszenia”) i **duplicate** (wpisz
oryginał, np. PRB-1). Triaż robisz tylko Ty, w konsoli — agent go nie wykona. Zgłoszenia odłożone ponad 90
dni wracają w sekcji **Zgłoszenia porzucone**: **zamknij** albo **zwaliduj ponownie**.

## Jak prowadzić zmianę z agentem

Dla osoby, która pracuje w repozytorium produktu z Claude Code i DI Agent Factory (tf).

### Instalacja (raz)

1. Zainstaluj `tf` na komputerze (instrukcja w `dbqm45/tf`, `docs/setup.md`; Python 3.9+ i git).
2. W repozytorium produktu:

```bash
tf install
```

```bash
tf add mode-pdi
```

```bash
tf onboard --yes
```

`tf doctor` pokazuje stan instalacji, `tf update` aktualizuje. Tryb `mode-pdi` łączy tf z suitą: zmiany mają dziennik
w `docs/project/changes/CHG-n/`, a bramki zatwierdza człowiek w pdi.

### Fazy zmiany

Zmiana CHG-n przechodzi fazy; po każdej agent prosi pdi o bramkę i czeka:

| Faza | Agent (persona) | Wynik | Bramka |
| --- | --- | --- | --- |
| intent | maja | `intent.md`: problem, opcje z kosztem, wybór, metryki, poza zakresem | B1 |
| requirements | ewa | wymagania | B2 |
| architecture | tomasz | `plan.md` (cięcia TSK-n) i `release.yaml` (linie R1…Rn, flagi) | B3 |
| design | natalia | projekt | `design-review` |
| delivery | `tf-task` | kod cięć, PR | bez bramki fazy |

Prośba o bramkę niesie podsumowanie, ścieżkę artefaktu, link do PR, pytania z sekcji `## Gate questions` i ocenę
ryzyka. Po Twojej decyzji w pdi workflow w repozytorium zapisuje ją w `decisions.md` i uruchamia następną fazę. PR
fazy scala człowiek, zanim ruszy kolejna. Jeśli ktoś zmieni artefakt po zatwierdzeniu, następna faza się nie
uruchomi.

### Zadanie (cięcie)

W Claude Code:
- `/tf-task TSK-n` (albo tekst zadania): kryteria akceptacji, specyfikacja, plan kawałków, dla każdego kawałka test,
  kod i commit, przegląd zakresu, na końcu PR z dowodami i raport kosztu;
- `/tf-task … --plan` kończy na planie, `--auto --budget <USD>` pracuje bez zatrzymań w limicie kosztu;
- `/tf <tekst>` to jednorazowe polecenie bez pętli, `/tf-design <temat>` to projekt.

Commity kawałka mają stopkę `Change: TSK-n`, a kawałek za flagą także `Flag: <klucz>`. Dzięki temu DI Release łączy
wdrożenie z zadaniem i flagą. tf nie scala, nie wdraża i nie cofa wdrożenia: to robi człowiek albo pipeline.

### Decyzja w rozmowie

Gdy w rozmowie z agentem coś ustalicie, agent pokazuje szkic decyzji. Po Twojej zgodzie zapisuje ją w
`decisions.md` i w rejestrze pdi.

## Jak sprawdzić gotowość historyjki

Dla Product Ownera, analityka i zespołu. Produkt: **DI Definition** (interfejs „Quorum”, lokalnie
`http://localhost:4317`, `docker compose up -d --build` w repo ci_for_sdlc).

DI Definition czyta Jirę, Confluence i Figmę i mówi, czy historyjka albo epik jest gotowy do realizacji. Kodu nie
analizuje.

### Osiem wymiarów gotowości

Requirements, Design, Documentation, Architecture, User Journeys, Error Handling, Dependencies oraz Release plan (ten
ostatni tylko dla epików i feature). Wynik: `ready`, `not_ready` albo `needs_attention`. Ustalenie krytyczne
ustawia status niezależnie od średniej. Epik jest tak gotowy jak jego historyjki.

Rodzaje ustaleń: **Gap**, **Conflict**, **Ambiguity**, **Outdated**, **Missing coverage**, **Drift**. Ważność:
critical, warning, info.

### Krok po kroku

1. Zaloguj się: **Log in with the suite** albo **Log in with Atlassian**.
2. **Project health** → **Analyze now**: analiza wszystkich elementów.
3. **Backlog** → wybierz historyjkę. Widzisz gotowość, zakładkę **Acceptance criteria** i ustalenia.
4. Przy ustaleniu:
   - **WHY? — N sources**: dowody z cytatami ze źródeł;
   - odpowiedz na pytanie ustalenia i kliknij **Record decision**;
   - gdy wolno: **Accept risk** albo **Not applicable**;
   - ustalenie od AI potwierdź przyciskiem **Confirm AI finding**, zanim zacznie się liczyć.
5. Gdy odpowiedź znalazła się w źródle, DI Definition proponuje zamknięcie: **Accept**, **Edit** albo **Reject**.
   Zamknięte ma znacznik **Auto-closed**; decyzja trafia też do rejestru pdi.
6. **Challenge this feature (N)**: przegląd „adwokata diabła” przed zatwierdzeniem.
7. Gdy wszystko jest gotowe: **Approve for implementation**. Przy `not_ready` jest tylko **Force approve…** z
   obowiązkowym powodem, zapisanym w audycie.
8. Zatwierdzenie zamraża stan. Gdy ktoś później zmieni historyjkę w źródle, pojawia się **DRIFT DETECTED**:
   **Re-approve after review** albo **Withdraw approval**.
9. Dla historyjki zmiany CHG-n gotowość idzie do pdi sama (`readiness.changed`). Przycisk **Ask pdi to approve
   CHG-n** prosi pdi o bramkę, gdy chcesz decyzji mimo braków.

Pytania od ludzi (np. ze Slacka) mają znacznik **Not accepted yet**. Liczą się do gotowości dopiero po **Accept for
refinement** przez Product Ownera.

Pozostałe ekrany: **Decisions** (decyzje), **Drift** (zmiany po zatwierdzeniu), **Impact analysis** (wpływ zmiany),
**Settings** (**Test connections**, **Save & re-analyze**, reguły w Policy), **Audit log**. Bramkę w CI daje
`npm run analyze -- --fail-on critical`.

## Jak podjąć decyzję na bramce

Dla decydenta (`editor` albo `admin` w DI Decision). Konsola pdi, lokalnie `http://127.0.0.1:8788/`.

### Skąd biorą się sprawy w Skrzynce

| Rodzaj | Skąd | Przyciski |
| --- | --- | --- |
| `gate` (bramka B1–B5, `design-review`, `approve-for-implementation`) | tf, DI Definition | **approve**, **changes requested**, **reject** |
| `gate` etapu flagi na PROD | DI Release (`release.stage_changed`) | jak wyżej |
| `impact_review` (ocena skutku) | DI Release po wydaniu R1 | **met**, **not met**, **unknown** |
| `problem` (zgłoszenie, przekroczona metryka) | formularz, agent, tf | triaż (rozdział 6) |
| `autonomy` (zmiana poziomu autonomii) | agent (`propose_autonomy_changes`) | decyzja człowieka |
| `pr_ready` (PR gotowy do przeglądu) | pętla PR agenta | odpowiedź w PR |

### Krok po kroku

1. Zaloguj się do konsoli i wejdź w **Skrzynka**. Karta pokazuje identyfikator, pas, rodzaj, opis, doradczą ocenę
   ryzyka (low/medium/high, nie zmienia bramki) i pytania z prośby.
2. Kliknij identyfikator, żeby zobaczyć **Ślad zmiany**: kroki, pliki zmiany (`intent.md`, `plan.md`,
   `release.yaml`…), diff i postęp.
3. Wpisz **Treść decyzji (statement)** (do 800 znaków) i **Dlaczego (why)** (do 2000 znaków). Oba pola są wymagane.
4. Kliknij wynik. Konsola pokaże numer decyzji DEC-n z linkiem do śladu.
5. Decyzja wraca do produktu, który prosił (`gate.decided`), i rusza następna faza.

Zabezpieczenia: jeśli ktoś zdecydował wcześniej albo strona jest nieaktualna, dostaniesz odmowę i trzeba odświeżyć.
Jeśli artefakt zmienił się po prośbie, zatwierdzenie zostanie odrzucone.

Gdy nie jesteś pewien, zapytaj zespół przed decyzją (rozdział 10).

### Terminy

| Bramka | Termin |
| --- | --- |
| triaż, B1, B2, `design-review`, `approve-for-implementation`, B4 | 2 dni robocze |
| B3 (plan i cele, trudna do odwrócenia) | 5 dni roboczych |
| B5 i etap flagi na PROD | 1 dzień roboczy |
| ocena skutku, zmiana autonomii | 5 dni roboczych |

Godziny ciszy: 18:00–8:00 i weekendy. Po terminie przychodzi przypomnienie, po 2 × termin zmiana jest
**wstrzymana** (agent nie zaczyna następnego cięcia), a po 4 × termin trafia na listę **do przeglądu**. Gdy
skonfigurowano Slack, dostajesz prywatne „Waiting for your decision” z linkiem **Decide in DI Decision** (rozdział
17).

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

**Pokój w sprintdecku** (gdy administrator połączył pdi ze sprintdeckiem): przycisk **Open a room in sprintdeck** nad
agendą otwiera pokój planowania, w którym każda sprawa z agendy to jedno zadanie z talią „Risk”, a Ty prowadzisz
spotkanie. Sprintdeck poprosi o **Sign in with the suite**; potrzebna jest rola `member` w Sprintdecku (nadaje ją
administrator organizacji). Link działa 50 minut. W pokoju zespół głosuje w ciemno i omawia rozbieżności.

Po sesji kliknij w podsumowaniu pokoju (**Summary**) **Send results to DI Decision**. Wrócisz do pdi na stronę
**Results from sprintdeck**, która pokazuje dla każdej sprawy ocenę końcową, głosy (ile osób na którą kartę, bez
nazwisk), stan zgody, liczbę rund i notatki. **Attach to the agenda** dołącza je do kart. Na agendzie przy sprawie
pojawia się blok **From the sprintdeck room** z linkiem do pokoju. Decyzję wpisujesz potem na karcie sprawy (krok 7):
wyniki z pokoju to materiał, nie decyzja.

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

### Jak eskalować sprawę poza zespół

Gdy zespół nie może albo nie powinien rozstrzygać sam (np. sprawa dotyka bezpieczeństwa, budżetu albo innego
zespołu), decydent przekazuje decyzję o **tej jednej sprawie** komuś innemu. Inaczej niż przy „Ask team”, od tej
chwili decyduje adresat, nie Ty (decyzja OM2).

1. Na karcie sprawy w **Skrzynce** rozwiń **Escalate**.
2. Wybierz adresata z listy **To**. Są na niej osoby z rolą `editor` albo `admin` w DI Decision, które logowały się do
   konsoli. Przy decyzjach chronionych (triaż, ocena skutku, wydanie B5) tylko osoby z rolą `admin`.
3. Wpisz powód (wymagany) i, jeśli chcesz, pytanie do adresata. Kliknij **Escalate**.
4. Karta pokazuje „Escalated to <adresat> · since …”. Ty już nie możesz zdecydować; otwarte pytanie do zespołu się
   zamyka, a adresat widzi odpowiedzi.
5. Adresat dostaje wiadomość w Slacku (gdy jest skonfigurowany) i widzi na karcie „<Ty> escalated this to you” z
   powodem i pytaniem. Decyduje tak samo jak na każdej bramce: treść, uzasadnienie, przycisk wyniku.
6. Jeśli adresat uzna, że to nie jego decyzja, klika **Give it back** z notatką. Wtedy karta pokazuje „<adresat> gave
   it back: …” i decydujesz znów Ty.

Termin sprawy się nie zmienia: przypomnienia i wstrzymanie zmiany idą do adresata. Decyzja zapisuje, kto eskalował, do
kogo i dlaczego, a po oddaniu także notatkę adresata.

## Jak śledzić wdrożenia i status wydania

Produkt: **DI Release** (ShipScope), lokalnie `http://localhost:3000/`. Odpowiada na pytanie: czy funkcja jest
naprawdę widoczna dla użytkowników, czy tylko wdrożona z wyłączoną flagą. Łączy trzy sygnały: zadania z Jiry
(albo zmiany z repozytorium), wdrożenia z GitHub Deployments i stan flag w środowiskach test, qa, prod.

### Pierwsze uruchomienie (administrator przestrzeni)

1. Zaloguj się (GitHub albo suita) i na stronie `/start` załóż przestrzeń (workspace).
2. Settings → **Getting started** prowadzi przez kroki:
   1. **Install the GitHub App** (wymagany);
   2. **Choose repositories to track** (wymagany): Settings → GitHub → **Track repository** → **Track**;
   3. **First deployments arrive** (wymagany): pipeline musi tworzyć GitHub Deployments ze środowiskiem test, qa
      albo prod;
   4. **Connect Jira** (opcjonalny);
   5. **Choose Jira boards** (opcjonalny);
   6. **Send feature flags** (opcjonalny);
   7. **Invite your team** (opcjonalny): Settings → Members → **Create invitation link** (rola member albo admin,
      link raz, 7 dni).
3. Po wymaganych krokach: **Open the dashboard**.

Role w przestrzeni: **member** widzi wszystko, **admin** zmienia ustawienia. Osoba z suity dostaje je z roli w DI
Release przy każdym logowaniu: `admin` → admin, `editor` i `viewer` → member, w przestrzeniach, które admin powiązał
z organizacją suity. Admin może potem w Settings → General → Sign-in zostawić tylko logowanie przez suitę.

### Ustawienia repozytorium

Settings → GitHub → ołówek przy repozytorium:
- **GitHub environments**: które środowisko GitHub to test, qa, prod, a które pominąć (`production` → prod,
  `dev` → test, `preprod` nigdy prod);
- **Version file**: plik z wersją wdrożenia (np. `version=v1.6.0`), gdy wersja nie przychodzi w samym wdrożeniu;
- **Paths not counted as drift**: ścieżki pomijane przy porównaniu środowisk;
- **Role**: np. „Frontend (what users see)”; potrzebne do ostrzeżenia „FE on, BE off”;
- **This repository has no feature flags**, gdy repo flag nie ma;
- **Sync deployments again**: odczyt wdrożeń od nowa.

### Jira

Settings → Jira → **Connect Jira** (logowanie Atlassian, tylko odczyt) → **Use this site** → zaznacz tablice →
**Save selection** → **Sync now**. Rytm tablicy: **Auto-detect**, **Program increments (SAFe)**, **Sprints
(Scrum)**, **Releases (Fix Version)**, **Monthly flow (Kanban)**. Powiązanie zadań z flagami: **Feature flags in
Jira** (etykieta z prefiksem `flag:` albo pole).

### Flagi w DI Release

Settings → **Sources**: źródło flag ma rodzaj **build** (wartość w buildzie) albo **runtime** (przełączana na żywo),
priorytet i usługi, których dotyczy. Zalecana droga:
1. **Add source** → token pokazany raz.
2. W pipeline adapter flag (GitHub Action albo CLI z `adapters/flags`) wysyła pełny stan flag na każde środowisko.
   Zacznij od `dry-run: true`, który niczego nie wysyła. Zamiast tokenu działa też OIDC z GitHub Actions.
3. W Sources widać ostatni przyjęty i ostatni odrzucony komunikat.

**Advanced sources**: odczyt flag wprost z plików w repo (**Find flags files**, **Preview**, **Read from code**)
albo z adresu https (**Test**, sekret podpisu).

### Dashboard

| Zakładka | Co pokazuje |
| --- | --- |
| **Product view** | zadania pogrupowane w epiki, z pigułką statusu na każde środowisko; kafelki **Released to PROD**, **Deployed to PROD (hidden)**, **Partially on PROD**, **Not on PROD**; filtry i wybór PI oraz sprintu |
| **Technical view** | karty środowisk, macierz usługa × środowisko, różnice między środowiskami (**Diff to TEST/QA**), historia wdrożeń (domyślnie 90 dni), lista flag |
| **Delivery summary** | co trafiło na PROD w każdym sprincie, funkcje i poprawki osobno; **Copy as Markdown** do notatki wydania |
| **Release plan** | linie R1…Rn (R1 = MVP) z ich statusem na PROD; flagi z ekspozycją i etapami z `release.yaml` |
| **Insights** | wykresy (status per sprint i priorytet, czas Done → PROD, stare flagi, wycofania i drift); włącza admin w Settings → General → **Show Insights on the dashboard** |

Znaczenie pigułek statusu:

| Pigułka | Znaczy |
| --- | --- |
| **Not deployed** | kodu nie ma na tym środowisku |
| **Deployed (hidden)** | kod jest, ale wszystkie flagi wyłączone: użytkownicy nie widzą |
| **Released** | kod jest i wszystkie flagi włączone: użytkownicy widzą |
| **Partial** | część usług albo rollout poniżej 100% |
| **Code deployed** | kod jest, nie ma flagi, która by to potwierdziła |
| **?** przy pigułce | pewności brak: usługa bez źródła flag albo dane flag nieaktualne; szczegóły w podpowiedzi |
| czerwony obrys i ⚠ | frontend ma flagę włączoną, a backend wyłączoną („FE on, BE off”) |

Dodatkowo: wycofanie wdrożenia (rollback) i pominięte środowisko („skipped QA”) są oznaczone w historii; flaga
włączona długo po zakończeniu zadań ma notkę 🧹 (stara flaga).

Jak FAQ liczy każdą liczbę i znacznik: `FAQ.md` w repo DI Release.

### Połączenie z DI Decision

Settings → Integrations → **pdi**: adres odbiornika pdi → **Connect**. Konsola pokaże raz trzy zmienne
(`PDI_SHIPSCOPE_URL`, `PDI_SHIPSCOPE_TOKEN`, `PDI_SHIPSCOPE_SIGNING_SECRET`) do wpisania w pdi. Stany: **Not
connected**, **Waiting for pdi**, **Connected**, **Connected, with problems**, **Disconnected**. Lokalnie `sdlc up`
robi to samo. Dopiero z połączeniem działają: plan wydania z repozytorium, zdarzenia do pdi, tokeny usługi i API dla
agenta.

Inne ustawienia: **Settings activity** (dziennik zmian, admin), czas przechowywania historii wdrożeń (7–730 dni,
domyślnie 90), **Danger zone** → **Delete workspace** (po wpisaniu nazwy). Publiczna strona stanu usługi: `/status`.

## Jak zarządzać flagami funkcji

Produkt: **DI Release Control** (ShipScope Flags), lokalnie `http://localhost:5173` (albo `http://localhost:8080`
w Dockerze). Jedno miejsce z flagami i ich stanem w test → qa → prod: kto utworzył flagę, kto i kiedy ją zmienił.
Pilnuje kolejności włączania i zależności, a przed usunięciem flagi ostrzega, że funkcja mogłaby się cicho wyłączyć.

DI Release Control to osobna aplikacja. DI Release czyta stan flag ze swoich źródeł (rozdział 11); czy dziś łączy
się z DI Release Control — nie sprawdzono.

| Rola | Co może |
| --- | --- |
| Viewer | czyta |
| Editor | tworzy flagi, zmienia stan i szczegóły, usuwa flagi |
| Admin | także rejestruje serwisy i wydaje im poświadczenia, ustawia próg usuwania i powiadomienia |

Z suitą rola to `di-release-control:<rola>`. Rola jest czytana przy logowaniu, więc jej zmiana działa po ponownym
zalogowaniu (najpóźniej po 12 h).

### Krok po kroku

1. **Sign in with SSO**.
2. Zakładka **Flags**: wyszukiwarka, widok **By flag** albo **By service**, sortowanie **Needs attention first**.
   Etapy flagi: new, in testing, live, to clean up.
3. **Create flag**: Key, Description, Type, **Requires flag (optional)** (zależność), Owner, **Review by
   (optional)**, Tags, **Assign to services**.
4. Otwórz flagę → **Environment state** → przełącznik Test, QA albo Prod. Reguły:
   - włączasz w kolejności test → qa → prod („Enable in qa first — flags promote test → qa → prod in order.”);
   - flaga zależna włącza się dopiero tam, gdzie wymagana jest włączona;
   - wyłączasz od góry: prod → qa → test.

   Zablokowany przełącznik ma kłódkę i powód. Odmowa też trafia do dziennika.
5. **Assigned services**: które serwisy czytają flagę i jak (runtime, build-time albo oba).
6. Powiadomienia o zmianach na PROD: Settings → **Production change notifications** → **Webhook URL** (np. Slack) →
   **Send test message**; przy fladze **Notify about prod changes of this flag**.
7. Usunięcie: **Removing this flag** → **Retire flag** → **Confirm — remove <klucz>**. Gdy usunięcie nie jest
   bezpieczne, przycisk jest nieaktywny, a lista mówi dlaczego („Not safe to remove yet — a feature could silently
   switch off”), np. serwis wciąż czyta flagę w czasie działania. Usunięcie nie zmienia kodu serwisów.
8. Kandydaci do usunięcia: flaga typu release włączona wszędzie dłużej niż próg (Settings → **Removal
   candidates**, domyślnie 30 dni).
9. **Audit log**: kto, kiedy, co, na czym; przechowywany 2 lata.

### Serwisy (admin)

Zakładka **Services** → podaj **Service key** → poświadczenie pokazuje się raz. Serwis pobiera swoje flagi:
`GET /api/v1/sdk/flags?env=prod` z nagłówkiem `Authorization: Bearer <poświadczenie>` i dostaje
`{ env, flags: { klucz: true/false } }`. Rotacja zostawia stare poświadczenie ważne przez 24 h; przy wycieku
**Revoke & reissue**.

Bez serwera dashboard działa w trybie demo (baner, rola do wyboru w „Viewing as”). Gdy dostawca tożsamości nie
działa, admin wchodzi przez **Emergency access** (break-glass): sesja na godzinę, każde użycie jest w dzienniku.

## Jak ocenić skutek wydania i pilnować metryk

### Ocena skutku

1. Gdy DI Release zgłosi wydanie linii R1 (MVP), pdi planuje ocenę skutku: na dzień `review_by` z decyzji o
   intencji, albo na dzień wydania plus horyzont metryki sukcesu, albo za 30 dni.
2. W terminie w **Skrzynce** pojawia się pozycja `impact_review` z danymi z DI Release.
3. Decydent wpisuje treść i uzasadnienie i klika **met**, **not met** albo **unknown**.
4. Zgłaszający dostaje powiadomienie z wynikiem.

Lokalnie zaległe oceny otwiera `uv run sdlc impact-review`.

### Pasma kontrolne metryk

tf codziennie czyta z DI Release dzienną serię PROD: wycofania, nieudane wdrożenia, medianę czasu realizacji i
liczbę wdrożeń. Punkt poza 3σ w ostatnich 7 dniach to zgłoszenie problemu (`metric.breached`) w Skrzynce pdi, do
triażu. Słabsze sygnały: 2 z 3 punktów poza 2σ to „diagnose”, 8 z rzędu po jednej stronie to tylko wpis w logu.
Włączenie: `metric_watch.py workflow install` w repozytorium z tf.

### Prognoza

Przy `approve-for-implementation` pdi liczy prognozę zmiany: liczba cięć × mediana dni na cięcie, z przedziałem
P25–P75 i powodami wątpliwości. Widać ją w stanie zmiany. Trafność prognoz: `uv run sdlc forecast` albo agent
(`forecast_report`).

## Jak zobaczyć, co się dzieje

Strony konsoli pdi tylko do odczytu, dla każdej roli:

| Menu | Co pokazuje |
| --- | --- |
| **Now** | przebiegi agentów teraz: In progress, Awaiting decision, In review, Done; filtr po osobie |
| **Discuss** | agenda spraw do omówienia (rozdział 10) |
| **Tablica** | trzy pasy: „Zaprojektuj i zbuduj”, „Oceń i wydaj”, „Wdróż, obserwuj, ulepszaj”; karty zmian z „czeka na Ciebie” |
| **Skrzynka** | sprawy czekające na decyzję |
| **Decyzje** | ostatnie 100 decyzji |
| **Autonomia** | poziom autonomii każdego typu decyzji |
| **Drafts** | szkice decyzji od agenta; zatwierdzasz albo odrzucasz z powodem, dopiero potem agent zapisuje decyzję |
| **Przepływ** | gdzie zmiany czekają, czas bramek (mediana, p90), czekanie i praca; „Kolejka a jakość”: tydzień po tygodniu kolejka bramek obok wdrożeń na PROD, CFR i nowych zgłoszeń |
| Ślad zmiany (`/trace/CHG-n`, z karty) | kroki, pliki zmiany, diff, postęp na żywo, pętla PR |

### Kolejka a jakość

Na stronie **Przepływ** tabela „Kolejka a jakość” pokazuje ostatnie 8 tygodni:
- prośby o bramkę, decyzje, medianę czekania i kolejkę na koniec tygodnia;
- z ShipScope udane i nieudane wdrożenia na PROD, rollbacki oraz CFR (odsetek nieudanych wdrożeń i rollbacków);
- nowe zgłoszenia problemów.

Jeśli w ostatnim pełnym tygodniu kolejka i CFR wzrosły razem, nad tabelą pojawia się podpowiedź „przegląd może nie
nadążać”. To temat do rozmowy, nie alarm, i dotyczy całego zespołu, nie osób. Bez połączenia z ShipScope kolumny
wdrożeń są puste, a strona mówi dlaczego. Agent widzi to samo w narzędziu `flow_quality`.

### Autonomia

Każdy typ decyzji ma poziom: 3 (decyduje człowiek), 2 (automat z prawem weta), 1 (automat z logiem), 0 (automat po
cichu). Wszystko startuje od 3. Poziom obniża tylko człowiek, decyzją w Skrzynce, gdy agent zaproponuje zmianę na
podstawie licznika akceptacji (95% z 30 decyzji). Typy chronione nie schodzą poniżej 3: triaż, zakres R1, wydanie
na PROD, ocena skutku, przegląd wrażliwy, migracja.

## Rejestr decyzji

Każda decyzja w suicie ma numer DEC-n, treść, uzasadnienie, autora, datę, źródło i powiązania (zmiana, zadania,
zgłoszenie). Decyzji się nie cofa: nowa decyzja zastępuje starą (`supersede`).

Skąd biorą się decyzje:
- przyciski w Skrzynce i na agendzie Discuss;
- decyzje z tf (`decisions.md` zmiany) i z DI Definition (zamknięcia ustaleń);
- rozmowa: agent proponuje szkice decyzji z wątku Slacka albo transkrypcji spotkania (z cytatami), a one czekają w
  Skrzynce na zatwierdzenie;
- agent na Twoje polecenie (`/record-decision`). Agent wystawia szkic, a Ty zatwierdzasz go w konsoli: menu
  **Drafts** → szkic → **Approve** albo **Reject** z powodem. Samo „tak” w czacie nie zapisze decyzji. Zgoda dotyczy
  dokładnie pokazanej treści i jest ważna godzinę; zatwierdza rola `editor` albo `admin`.

Gdzie szukać: menu **Decyzje** albo agent (`find_decisions`, `get_decision`).

## Praca z agentem Claude (MCP)

W Claude Code możesz rozmawiać z suitą przez serwery MCP:

| Serwer | Co daje |
| --- | --- |
| **pdi** | 34 narzędzia: 20 do odczytu (decyzje, Skrzynka, zmiany, ślad, zgłoszenia, przepływ, kolejka a jakość, prognozy, autonomia, agenda, dzienny skrót) i 14 do zapisu (szkice decyzji i zapis po zatwierdzeniu, zgłoszenia, terminy, skutki opcji, propozycje); decyzje o Skrzynce i triaż tylko przyciskiem w konsoli |
| **shipscope** (DI Release) | sześć narzędzi tylko do odczytu nad API usługi: zmiany, plan wydania, flagi, środowiska, status elementu, metryki (nazw narzędzi nie sprawdzono); potrzebny token usługi `shps_…` z Settings → General → Service tokens |
| DI Definition | odczyt gotowości (opis w `packages/mcp/README.md` repo ci_for_sdlc; nie sprawdzono) |

Zdalny serwer pdi (`pdi-mcp --http`, `http://127.0.0.1:8790/mcp`) loguje Cię przez suitę: `viewer` tylko czyta,
`editor` i `admin` też zapisują, a agent tylko czyta. Lokalnie: `uv run sdlc mcp pdi` albo `uv run sdlc mcp
shipscope`.

Przykłady próśb: „co czeka na moją decyzję?”, „pokaż ślad CHG-12”, „zapisz zgłoszenie: …”, „przygotuj podsumowanie
agendy na spotkanie”, „czy EBO-123 jest już na PROD?”.

Agent nie decyduje na bramkach, nie zamyka spraw w Skrzynce, nie triażuje zgłoszeń i nie odpowiada za zespół —
to zawsze przycisk w konsoli. Zapisy przez agenta niosą Twój identyfikator z logowania.

## Slack

Produkt: **DI Channels**.

### Pytanie do historyjki z wiadomości

1. Najedź na wiadomość → **⋮** → **Add question to a story**.
2. W oknie **Question for a story** wpisz **Story key** (np. `PAY-123`) i **Question or thought** → **Add question**.
3. Albo komendą:

   ```
   /di-question PAY-123 Czy to działa offline?
   ```

4. Tylko Ty widzisz wynik: „Added: your question is on PAY-123 — <link>…”. Pytanie widzi cały zespół z Twoim
   nazwiskiem. Liczy się do gotowości, gdy Product Owner przyjmie je w DI Definition.

### „Czeka na Ciebie”

Zatwierdzający dostaje wiadomość prywatną, gdy sprawa czeka na jego decyzję, a potem przypomnienia: „Waiting for your
decision”, „Reminder…”, „Due today…”, „Overdue…”, „Overdue twice the deadline: the change is paused”, „Overdue four
times the deadline: on the review list”. Wiadomość podaje, co i przy jakiej zmianie, termin i link **Decide in DI
Decision**. W godzinach ciszy (18:00–8:00, weekendy) czeka do 8:00 następnego dnia roboczego. W Slacku nie ma
przycisków decyzji: decyzja zapada w DI Decision.

### Pytanie od zespołu i dzienny skrót

- **Gdy ktoś zapyta Cię przez „Ask team”**, dostajesz wiadomość prywatną: kto pyta, o co, jakie są opcje, do kiedy, i
  link **Answer in DI Decision**. Odpowiadasz w konsoli (rozdział 10). Działa, gdy w Slacku masz ten sam e-mail co w
  suicie; jeśli nie, decydent widzi przy pytaniu „Not reachable in Slack: <Twoje imię>”.
- **Dzienny skrót** przychodzi w dni robocze o 8:00, tylko gdy coś na Ciebie czeka. Zatwierdzający widzi:
  - **Waiting for your decision (N)**: do 10 najpilniejszych spraw (po terminie, wstrzymane, termin dziś) z
    przyciskiem **Decide**;
  - **With the team**: pytania do zespołu w toku, ile osób odpowiedziało i kiedy pytanie się zamyka;
  - **To discuss**: ile spraw jest na agendzie, z linkiem **Open the agenda**;
  - **Not reachable in Slack**: kogo nie udało się powiadomić.

  Osoba zapytana widzi w swoim skrócie **Asked of you**, dopóki nie odpowie.

Agent pokaże ten sam skrót w rozmowie (narzędzie `daily_digest`).

Konfigurację robi administrator raz (`slack-setup.md` w repo di-channels): aplikacja Slack z manifestu, sekrety,
adres usługi, identyfikator zatwierdzającego, połączenie z pdi i opcjonalnie z suitą (autor pytania jako osoba z
suity). Dziś jeden zatwierdzający na instalację; dzienny skrót wysyła `sdlc digest` z crona. Teams, głosowanie i odpowiedzi w
wątku jeszcze nie działają.

## Sprintdeck

Sprintdeck (`dbqm45/sprintdeck`) to planning poker z „Consensus Engine”: zespół głosuje ukrytymi kartami, a aplikacja
pomaga zrozumieć rozbieżności i dojść do wspólnej decyzji. Ma też talię ryzyka.

Stan: MVP w budowie. Pokój można założyć anonimowo albo po **Sign in with the suite** (klient `sprintdeck`, rola
`member`, bez e-maila). Z agendy „Discuss with team” w pdi pokój powstaje jednym przyciskiem (rozdział 10). Zadania
poza tym dodaje się ręcznie, bez importu z Jiry. Uruchomienie lokalne: README repozytorium (`npm run dev`, baza w
Dockerze).

## Cała suita na jednym komputerze

Do prób i pracy lokalnej, z repozytorium pdi. Wymagania: Docker, `gh` (zalogowany), `claude`, Node z `npm`, `uv` i
klony pdi, DI Release i DI Definition obok siebie.

```bash
uv run sdlc init
```

Raz: klony, klucze, opcjonalnie tożsamość suity (Keycloak) i Slack.

```bash
uv run sdlc up
```

Startuje i łączy wszystko, kończy się linią „gotowe”. Porty: DI Release 3000, DI Channels 3100, DI Identity 3200,
DI Definition 4317, Keycloak 8180, konsola pdi 8788.

```bash
uv run sdlc open
```

Otwiera konsolę pdi, DI Release i formularz zgłoszeń.

Pozostałe polecenia:

| Polecenie | Co robi |
| --- | --- |
| `sdlc status` | procesy, połączenia, sekrety (tylko ustawione/brak), Skrzynka |
| `sdlc sandbox <nazwa>` | repozytorium próbne z szablonu, śledzone w DI Release, z tf |
| `sdlc deploy prod` | próbne wdrożenie (GitHub Deployment) repo próbnego |
| `sdlc check` | ponownie wysyła gotowość zmian z DI Definition do pdi |
| `sdlc deadlines` | terminy Skrzynki: przypomnienia, wstrzymanie, lista do przeglądu |
| `sdlc digest` | dzienny skrót do Slacka (cron w dni robocze przed 8:00) |
| `sdlc impact-review` | oceny skutku, których termin minął |
| `sdlc forecast` | wyniki prognoz |
| `sdlc mcp pdi` / `sdlc mcp shipscope` | serwer MCP dla Claude |
| `sdlc down` | zatrzymuje procesy; dane zostają |
| `sdlc reset` | usuwa dane po wpisaniu „usuń” |

Cały przebieg na repozytorium próbnym, krok po kroku z oczekiwanymi wynikami: [`przebieg-lokalny.md`](przebieg-lokalny.md).

## Słowniczek

| Pojęcie | Znaczenie |
| --- | --- |
| **PRB-n** | zgłoszenie problemu albo pomysłu |
| **CHG-n** | zmiana: jednostka pracy od intencji do wydania, z dziennikiem w `docs/project/changes/CHG-n/` |
| **TSK-n** | zadanie (cięcie) w zmianie; jeden PR |
| **DEC-n** | decyzja w rejestrze |
| **Bramka** | punkt, w którym praca czeka na decyzję człowieka (triaż, B1–B5, `design-review`, `approve-for-implementation`, ocena skutku, etap flagi) |
| **Skrzynka** | lista spraw czekających na decyzję w konsoli pdi |
| **Pas** | jedna z trzech części procesu na Tablicy: zaprojektuj i zbuduj; oceń i wydaj; wdróż, obserwuj, ulepszaj |
| **Linia wydania R1…Rn** | grupa zadań wydawana razem; R1 to MVP |
| **Flaga funkcji** | przełącznik, który pokazuje albo chowa funkcję użytkownikom bez nowego wdrożenia |
| **Drift** | rozjazd: między środowiskami (DI Release) albo między zatwierdzoną historyjką a jej źródłem (DI Definition) |
| **Ocena skutku** | sprawdzenie po wydaniu MVP, czy zmiana dała efekt (`met`, `not_met`, `unknown`) |
| **Autonomia** | poziom 0–3: jak bardzo dany typ decyzji może iść bez człowieka |
| **Termin** | czas na decyzję w dniach roboczych; po 2 × termin zmiana jest wstrzymana, po 4 × trafia do przeglądu |
| **Kontrakt** | wspólny format zdarzeń i plików między produktami (`dbqm45/di-contract`) |
