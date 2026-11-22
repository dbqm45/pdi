# Plan budowy Delivery Intelligence Suite jako całości

Data: 2026-11-22 · Status: **propozycja; dwie decyzje właściciela z 2026-11-22 przyjęte** (osobne repozytorium
dla każdej części suity; usługa tożsamości suity), pozostałe pytania w §6 · Nic z tego planu nie jest rozpoczęte. · Opis stanu: artefakt „Delivery Intelligence Suite v3”,
https://claude.ai/artifact/ChP4fFzYQS95Pc8VPf8MG9

Ten dokument uzupełnia [`plan-program-ai-wg-aplikacji.md`](plan-program-ai-wg-aplikacji.md). Tamten rozpisuje
zadania programu AI na aplikacje i fale; ten odpowiada na trzy pytania: gdzie mieszka kod (repozytoria), w jakiej
kolejności budować to, co łączy aplikacje w suitę, i jakie są pierwsze kroki. Tam, gdzie oba plany się różnią,
różnica jest nazwana wprost (§7).

## 1. Stan wyjściowy (sprawdzony 2026-11-22)

Sposób sprawdzenia: przeczytane README, changelogi, TODO, plany i kod przy wątpliwych opisach; uruchomione testy
jednostkowe i proste polecenia. **Żadne połączenie między aplikacjami nie było sprawdzone na żywo**, nie był
uruchamiany `sdlc up`, nie były sprawdzane wdrożone instancje ani linia EV Intelligence.

| Produkt | Repo | Wersja | Uruchomione | Kopia kontraktu | Czego brakuje do roli w suicie |
|---|---|---|---|---|---|
| DI Decision | pdi | 0.10.0, kontrakt 0.14.0 | 1133 testy przeszły; konsola wstała na pustym rejestrze | źródło | usługa dla wielu osób (konsola tylko `127.0.0.1`, jeden token; MCP bez logowania), role, operating model; automatyczne stosowanie decyzji na poziomach 0–2 |
| DI Definition | ci_for_sdlc | 0.1.60 (2026-11-16) | 1363 testy + 115 testów skryptów przeszły | zestawy 0.4.0–0.12.0 | refinement R1–R9 (nic nie zbudowane); recenzent AI nigdy nie oceniony na modelu; logowanie tylko Atlassian |
| DI Release | evdt-service-shipscope | 0.2.67 (2026-11-01) | 297 testów aplikacji przeszło; z 431 testów serwera 1–2 nie przeszły (`flag-file-parser.test.js`, przyczyna niezbadana) | 0.4.0 | incydenty (CFR, MTTR), SSO, połączenie z DI Release Control |
| DI Release Control | evdt-shipscope-flags | 0.7.3 (2026-11-02) | 254 testy przeszły | brak | wdrożenie, pierwszy konsument, wiele organizacji, jakiekolwiek połączenie z suitą |
| DI Agent Factory | tf | 22.2.0 (2026-11-21) | ok. 100 ze 131 plików testów przeszło, reszta nieuruchomiona; `tf doctor` OK | 0.13.0 | bramki B4/B5 (dziś B1–B3 i design-review), pętla przeglądu PR w GitHub Actions, eksport dziennika, zgłaszanie przebiegów ręcznych |
| DI Quality (kandydat) | qa-platform | 0.1.0, MVP zamknięte, kod na `main` | 894 testy przeszły; przykładowy projekt od walidacji po raport | brak | każde połączenie z suitą; usługa, logowanie, UI |
| sprintdeck (poza suitą) | sprintdeck | 0.1.0 (2026-10-27) | 98 testów silnika przeszło; pokój nieuruchomiony | brak | API, konta, wdrożenie |
| DI Assistant, DI Team, DI Model Gateway, DI AI Registry, DI Channels | brak repo | — | — | — | wszystko (DI Team: makieta i kroki T1–T7) |

Pięć faktów, które ustawiają plan:

1. **Kontrakt jest jedynym spoiwem, a jego kopie są w tyle.** Źródło ma 0.14.0; fabryka 0.13.0, DI Definition
   najwyżej 0.12.0, DI Release 0.4.0. Każde nowe pole (np. „kto uruchomił przebieg”) dotrze do konsumentów dopiero,
   gdy nadrobią zaległość.
2. **Nie ma wspólnej tożsamości.** Cztery sposoby logowania: Atlassian (DI Definition, opcjonalnie), GitHub
   (DI Release), dowolny OIDC (DI Release Control), token w adresie (konsola DI Decision). Żadna aplikacja nie wie,
   że „Ola” w jednej to „Ola” w drugiej.
3. **Nie ma żadnej aplikacji Slacka ani Teams.** Są tylko webhooki wychodzące (DI Decision, DI Release Control).
4. **DI Decision, węzeł suity, działa dla jednej osoby na jej komputerze.** DI Team i „czyja kolej” wymagają usługi.
5. **DI Release i DI Release Control nie są połączone.** DI Release nie czyta flag z DI Release Control.

## 2. Repozytoria: każda część suity w osobnym repozytorium

### Decyzja właściciela (2026-11-22)

**Każda część suity ma własne repozytorium.** Powód: łatwiej aktualizować, zmieniać i korelować wersje
poszczególnych części. Pierwotna propozycja tego planu (jedno `di-platform` na wszystkie nowe usługi) jest
odrzucona; zostaje po niej tylko troska o koszt utrzymania wielu repo przez jedną osobę, na którą odpowiadają
trzy warunki niżej.

- **Istniejące produkty zostają w swoich repozytoriach**, bez przenoszenia kodu i bez zmiany nazw.
- **Kontrakt wychodzi do własnego repo `di-contract`** (D-P3, zadanie X3 planu programu).
- **Każda nowa usługa i każdy nowy produkt dostaje własne repo** z prefiksem `di-`.
- **DI Team nie dostaje repo na start**: zaczyna jako ekran konsoli DI Decision (T3); repo dopiero, jeśli zapadnie
  decyzja o osobnym produkcie (G6/P1).
- **tf zostaje osobno zawsze** (`15-jedna-platforma.md` §1).

### Trzy warunki, żeby osobne repo nie kosztowały za dużo

1. **Szablon repo usługi (`di-service-template`).** Jedno repo-wzorzec: CI, wydania z Conventional Commits,
   przypięta kopia kontraktu ze skryptem synchronizacji, weryfikacja tokenu usługi tożsamości, podpisywanie
   i odbiór zdarzeń, instrukcje dla agentów. Każde nowe repo powstaje z szablonu.
2. **Manifest suity.** Osobne repo same nie dają korelacji wersji. W `di-contract` powstaje plik `suite.yaml`:
   wydanie suity → wersja każdego produktu i wersja kontraktu, którą ten produkt ma przypiętą; test w CI sprawdza,
   że zestaw jest spójny. Dziś takiego miejsca nie ma i dlatego kopie kontraktu rozjechały się od 0.4.0 do 0.14.0.
3. **Repo powstaje wtedy, gdy jest co do niego włożyć**, nie na zapas.

### Lista repozytoriów

| Repo | Produkt | Stan | Kiedy założyć | Kto zakłada |
|---|---|---|---|---|
| pdi | DI Decision (+ ekran DI Team na start) | jest | — | — |
| ci_for_sdlc | DI Definition | jest | — | — |
| evdt-service-shipscope | DI Release | jest | — | — |
| evdt-shipscope-flags | DI Release Control | jest | — | — |
| tf | DI Agent Factory | jest | — | — |
| qa-platform | DI Quality (kandydat, pyt. 7) | jest | — | — |
| sprintdeck | poza suitą; pokój refinementu, jeśli D-P11 | jest | — | — |
| **di-contract** | kontrakt + manifest suity | do założenia | **teraz** (krok 6) | właściciel |
| **di-service-template** | szablon repo usługi (nie produkt) | do założenia | **teraz** (krok 13a), po decyzji o stosie | właściciel |
| **di-identity** | usługa tożsamości suity i Admin Console (usługi wspólne) | do założenia | **teraz** (krok 14) | właściciel |
| **di-channels** | DI Channels | do założenia | po D-P9 (krok 16) | właściciel |
| di-model-gateway | DI Model Gateway | później | start fali z bramką modeli | właściciel |
| di-ai-registry | DI AI Registry | później | razem z bramką modeli | właściciel |
| di-assistant | DI Assistant | później | po kanałach i bramce `operational-ai` | właściciel |
| di-team | DI Team | tylko jeśli osobny produkt | po pierwszym zespole (G6/P1) | właściciel |
| di-admin | DI Admin Console | tylko jeśli konsola zarządza kilkoma usługami | po AC3–AC4 (§2b) | właściciel |

Nazwy nowych repo różnią się od roboczych z planu programu (`ai-gateway`, `ai-registry`, `assistant`, `channels`,
`team`): prefiks `di-` i nazwa produktu z D-P8. Do potwierdzenia przy zakładaniu.

### Dlaczego nie monorepo „Suite”

| Powód | Szczegół (stan z repozytoriów) |
|---|---|
| Cztery stosy | Python + uv (pdi, qa-platform, tf), monorepo TypeScript z npm workspaces (ci_for_sdlc), Node + Fastify + Postgres (ShipScope), NestJS + Prisma (Flags), Next.js + Supabase (sprintdeck). Wspólne repo nie daje wspólnego kodu, tylko wspólny katalog |
| Wydania | ShipScope i Flags wydają się **przy każdym pushu na `main`** (commit `chore(release)`, tag `vX.Y.Z`, typ commita decyduje o wersji). W monorepo trzeba by przepisać oba mechanizmy na wydania per katalog z tagami z prefiksem i filtrami ścieżek; tf ma własne tagi `v22.x`, pdi taguje `contract-v…` |
| Przypięte kopie kontraktu | Trzy pliki przypięć wskazują `dbqm45/pdi` i konkretny commit. Po przeniesieniu wszystkie odwołania i skrypty synchronizacji trzeba zmienić naraz |
| Widoczność | pdi, ci_for_sdlc, ShipScope, tf, qa-platform są publiczne; Flags i sprintdeck prywatne. Monorepo ma jedną widoczność |
| Instalacja fabryki | tf instaluje się z adresu repo i referencji; użytkownicy fabryki musieliby klonować całą suitę |
| Reguły pracy | Każde repo ma własne instrukcje dla agentów i własne reguły commitów; ci_for_sdlc wymaga PR po każdej pracy. Jedno repo to jedne reguły albo reguły per katalog |
| Zasada produktu | „Każdy produkt da się uruchomić i sprzedać osobno” jest łatwiejsza do utrzymania, gdy granicą jest repo i kontrakt |

Koszt migracji do monorepo szacuję na 2–3 tygodnie pracy bez żadnej nowej funkcji [założenie; nie rozpisywałem
kroków], z ryzykiem zepsucia wydań w czterech repo.

### 2a. Tożsamość: jedna usługa dla całej suity (decyzja 2026-11-22)

Wzorzec wzięty z pakietów takich jak Adobe Creative Cloud (opis z ogólnej wiedzy o produkcie, bez sprawdzania
dokumentacji): aplikacje nie mają własnego logowania, tylko proszą centralną usługę tożsamości o token
(OAuth / OpenID Connect); konto może być federowane z dostawcą tożsamości firmy; administrator klienta w jednej
konsoli przypisuje ludziom produkty, a uprawnienie do produktu jest oddzielone od tożsamości.

Co z tego bierzemy:

- **Jeden wystawca tokenów.** Każda aplikacja suity ufa usłudze tożsamości suity, a ta federuje do dostawcy klienta
  (Atlassian, GitHub, Microsoft, Google). Aplikacja zna jeden adres i jeden format tokenu.
- **Trzy osobne rzeczy:** organizacja, osoba, uprawnienie do produktu („ta osoba ma DI Release jako edytor”).
  Dziś ci_for_sdlc trzyma organizacje i role u siebie, a Flags bierze rolę z tokenu dostawcy.
- **Jedno miejsce dla administratora klienta**: Admin Console (niżej).

Czego nie bierzemy: własnej bazy haseł i własnego silnika logowania pisanego od zera.

Przejście istniejących aplikacji jest stopniowe i każde to osobny PR: Flags (ma już ogólny OIDC, więc wystarczy
wskazać nowego wystawcę), konsola DI Decision przy przejściu na usługę, ci_for_sdlc (dziś Atlassian), ShipScope
(dziś GitHub). Dotychczasowe logowanie zostaje do czasu przełączenia.

### 2b. Admin Console (dopisane 2026-11-22)

Stan: nie istnieje. Ustawienia administratora są dziś rozproszone: organizacje, role i panel operatora
w DI Definition, ustawienia i audyt w DI Release, reguły i powiadomienia w DI Release Control; DI Decision nie ma
żadnych ustawień w interfejsie.

**Co to jest.** Jedno miejsce, w którym administrator klienta konfiguruje suitę. Nazwa produktu: DI Admin Console
[nazwa robocza, do potwierdzenia jak pozostałe]. Usługa wspólna, widoczna tylko dla administratorów.

**Gdzie mieszka.** Na start jako interfejs usługi tożsamości w repo `di-identity`: pierwsze rzeczy, którymi się
administruje (organizacja, ludzie, uprawnienia do produktów), to dane tej usługi. Osobne repo `di-admin` dopiero
wtedy, gdy konsola zacznie zarządzać ustawieniami kilku usług naraz.

**Zakres, w kolejności budowy:**

| Etap | Co administrator ustawia | Dane należą do |
|---|---|---|
| AC1 | organizacja, użytkownicy, zaproszenia; uprawnienie osoby do produktu z rolą; podłączenie dostawcy tożsamości klienta; dziennik zmian ustawień | di-identity |
| AC2 | połączenia między aplikacjami: tokeny usług, sekrety podpisywania zdarzeń, stan i wiek połączenia | di-identity (tokeny), aplikacje (stan) |
| AC3 | operating model: zatwierdzający i zastępca per typ decyzji, terminy, godziny ciszy | DI Decision |
| AC4 | kanały: instalacja Slacka albo Teams, polityka powiadomień | di-channels |
| później | lista zatwierdzonych modeli i limity kosztu; rozliczenia | DI Model Gateway i inne |

**Zasady.**

- Ustawienie ma jednego właściciela. Konsola pokazuje je i zmienia przez API aplikacji-właściciela; nie trzyma
  własnej kopii (ta sama zasada co przy decyzjach, §3a).
- Ustawienia specyficzne dla produktu (np. reguły flag, źródła w DI Definition) zostają w produkcie; konsola do
  nich odsyła.
- Każda zmiana ma autora z sesji i trafia do dziennika (wzorzec z DI Release Control); dostęp awaryjny jak tam.
- Aplikacja działająca poza suitą zachowuje własne ustawienia i własny ekran administratora.

### Co się dzieje z wydaniami, CI i kopiami kontraktu

| Obszar | Co zostaje | Co się zmienia |
|---|---|---|
| Wydania produktów | bez zmian w każdym repo | nic |
| Kontrakt | format, SemVer, tagi `contract-v<wersja>`, test zgodności bajt w bajt u konsumentów | źródłem staje się `di-contract`; workflow `contract-release.yml` przenosi się tam; w pdi zostaje przypięta kopia jak u innych |
| Przypięte kopie | mechanizm (`tools/pdi-contract.json` w tf, `scripts/pdi-contract.json` w ci_for_sdlc, schematy w `server/schemas/` ShipScope) | pole `repo` na `dbqm45/di-contract` i wersja na bieżącą: trzy małe PR; Flags i qa-platform dostają kopię dopiero przy pierwszym zdarzeniu |
| CI | bez zmian w każdym repo | każde nowe repo dostaje CI z szablonu; `di-contract` dostaje walidację schematów, przykładów i manifestu suity |
| Korelacja wersji | — | `suite.yaml` w `di-contract`: wydanie suity → wersje produktów i przypiętego kontraktu |
| Historia | zostaje | `di-contract` zaczyna z historią katalogu `contract/` (wyciętą z pdi) albo od zera z odnośnikiem; do decyzji przy X3 |

Koszt: wydzielenie kontraktu (rząd 2–3 dni razem z PR u konsumentów), szablon repo usługi (2–3 dni), potem każde
nowe repo z szablonu rząd godzin [założenia].

## 3. Co odblokowuje resztę

```
decyzje właściciela (§6)
   │
   ├─ A. kontrakt: konsumenci na bieżącej wersji → repo di-contract → 0.15 (przebiegi, konsultacja, wynik testów)
   │        │
   │        ├─ C. DI Team „Now” (odczyt) w konsoli DI Decision
   │        └─ E. DI Quality jako dowód na bramce
   │
   ├─ B. tożsamość: jedna osoba i organizacja w suicie (di-identity)
   │        │
   │        ├─ D. DI Channels: instalacja + „dodaj pytanie” + „czeka na Ciebie”
   │        └─ konsola DI Decision jako usługa dla zespołu (wymaga też DA4)
   │
   └─ P1. operating model: kto zatwierdza bramki (dokument, nie kod)
```

| Element | Dlaczego blokuje | Co blokuje |
|---|---|---|
| **A. Kontrakt** | każde nowe połączenie to nowe pole albo zdarzenie; konsumenci są 1–10 wersji w tyle | DI Team (T1), DI Quality w suicie, DI Channels (akcje idą przez kontrakt), Registry |
| **B. Tożsamość** | karta „Started by”, „czeka na Ciebie”, powiązanie osoby z komunikatora i decyzja z komunikatora wymagają jednej osoby w całej suicie | DI Channels, DI Team dla wielu osób, konsola jako usługa, DI Assistant |
| **P1. Operating model** | bramki nie mają nazwanych zatwierdzających ani SLA | powiadomienia „czeka na Ciebie” (do kogo?), eskalacja (T7), bramka operacyjna |
| **Konsola jako usługa (DA4)** | DI Decision działa lokalnie dla jednej osoby | DI Team poza jednym komputerem, decyzja z komunikatora (CH3) |
| **Kanał (D-P9)** | nie wiadomo, Slack czy Teams | cały moduł kanałów |

### Kolejność

1. **Etap 0, decyzje** (§6). Bez nich nie zaczynać B, D i E.
2. **Etap 1, porządek w kontrakcie** (A): konsumenci na 0.14.0, potem wydzielenie `di-contract`, potem 0.15.
   Nie zależy od żadnej otwartej decyzji poza D-P3.
3. **Etap 2, równolegle:** tożsamość (B) w `di-identity`; „Now” tylko do odczytu w lokalnej konsoli (C, kroki
   T1–T3); operating model (P1); pytania od ludzi w aplikacji DI Definition (R1, bez komunikatora).
4. **Etap 3, kanał** (D): CH1 (instalacja, powiązanie tożsamości, „dodaj pytanie”), potem CH2 („czeka na Ciebie”).
5. **Etap 4:** konsola DI Decision jako usługa (po DA4), „Ask team” (T4), decyzja z komunikatora (CH3).
6. **Później, wg planu programu:** Model Gateway, AI Registry, bramka `operational-ai`, flaga `ai-feature`,
   DI Assistant.

### Co można robić równolegle, niezależnie od powyższego

- DI Release: zbadanie niestabilnego testu parsera pliku flag; konektor odczytu flag z DI Release Control (jest
  w roadmapie ShipScope jako „flag-platform connector”).
- DI Release Control: decyzja o hostingu i pierwszy konsument (otwarte pytanie nr 2 w PRD).
- DI Agent Factory: prośby o bramki B4/B5 z fazy dostawy; `tf standard` (odłożone, do porównania z `tf status`).
- DI Definition: pierwszy płatny przebieg ewaluacji recenzenta (wstrzymany, brak klucza); termin przeglądu przy
  zaakceptowanym ryzyku (opisany w dokumentach, nieobecny w kodzie).
- DI Decision: aktualizacja linii stanu w README (mówi o kontrakcie 0.13.0 i dacie 2026-10-28).

### Czego nie zaczynać przed decyzją

- `di-identity` przed zapisem decyzji o silniku i stosie (krok 13; pyt. 4a);
- czegokolwiek ze Slackiem albo Teams (pyt. 2, 3);
- warstwy spotkania refinementu (pyt. 6);
- zdarzenia `test-result` i połączeń DI Quality (pyt. 7);
- konsoli jako usługi (pyt. 5 i DA4).

## 3a. Decyzje: każda aplikacja u siebie, suita widzi wszystkie (dopisane 2026-11-22)

Zasada właściciela: aplikacje takie jak DI Agent Factory i DI Definition działają także poza suitą, więc **każda
trzyma swoje decyzje u siebie**; jako członek suity **udostępnia je pozostałym**.

### Stan (sprawdzony w kodzie pdi i tf, bez uruchamiania)

| Skąd decyzja | Gdzie jest zapisana | Czy widzi ją wyszukiwarka suity (`find_decisions` w pdi) |
|---|---|---|
| bramka zatwierdzona w DI Decision | rejestr pdi (`DEC-n.md`) | tak |
| decyzja o zmianie w trybie pdi fabryki | `docs/project/changes/CHG-n/decisions.md` w repo produktu | tylko gdy sesja miała serwer MCP pdi i agent ją przesłał (`record_decision`); inaczej czeka jako niewysłana |
| decyzja w zwykłej sesji fabryki | `docs/project/decisions.md` (D-NNN), `decisions.md` zadania, ADR | nie |
| decyzja przy pytaniu w DI Definition | baza DI Definition | tylko decyzje o odpowiedziach znalezionych przez AI (`decision.recorded`, typ `finding.auto_close`), gdy przestrzeń jest połączona z pdi; wysyłki pozostałych nie znalazłem |

- `find_decisions` przeszukuje tylko pliki rejestru pdi: ustalenie, uzasadnienie, rodzaj, opcje, założenia,
  zależności, tagi; dopasowanie fragmentów słów, bez dowodów i skutków, bez szukania po znaczeniu.
- Decyzja D2/R1 („pdi indeksuje decyzje z repo, nie kopiuje”) nie jest tak zrealizowana: w pdi nie ma kodu, który
  czyta `decisions.md` z repozytoriów; działa kopiowanie przez MCP.
- Ile decyzji faktycznie jest w rejestrze, nie dało się policzyć: rejestr leży na komputerze właściciela.

### Model

1. **Źródłem prawdy jest aplikacja, w której decyzja zapadła.** Zapis lokalny zawsze, także bez suity. Fabryka i
   DI Definition już to mają.
2. **Jeden format:** Decision Record z kontraktu (znacznik `record: decision` w nagłówku, DR1). Lokalny
   identyfikator zostaje (`D-012`, `CHG-12/D1`); wpis dostaje pole pochodzenia: aplikacja, repo albo przestrzeń,
   ścieżka, commit.
3. **W suicie aplikacja publikuje decyzję zdarzeniem `decision.recorded`** (jest w kontrakcie; DI Definition już
   je wysyła). Poza suitą nie wysyła nic i nic nie traci.
4. **DI Decision jest indeksem suity, nie drugim źródłem prawdy.** Przyjmuje zdarzenie, nadaje numer `DEC-n`,
   trzyma treść do wyszukiwania i link do źródła. Zmiana decyzji idzie zawsze przez aplikację-właściciela.
5. **Pozostali członkowie czytają z indeksu i trzymają lokalną pamięć podręczną tylko do odczytu** (decyzja
   właściciela 2026-11-22). Wyszukiwanie przez MCP i API DI Decision; aplikacja, której decyzja dotyczy, dostaje
   zdarzenie (`decision.recorded`, `decision.basis_invalidated`). Pamięć podręczna pozwala pracować bez połączenia
   z suitą, a nie jest drugim rejestrem:
   - **zawartość:** decyzje innych aplikacji z tego samego zakresu (organizacja, projekt albo repo), w formacie
     Decision Record, z numerem `DEC-n`, pochodzeniem i datą pobrania;
   - **tylko odczyt:** aplikacja nie edytuje cudzej decyzji; zmiana idzie do aplikacji-właściciela, a pamięć
     podręczna dostaje nową wersję przy następnym odświeżeniu. Każdy plik ma znacznik „kopia, nie edytuj”,
     a sprawdzenie w CI aplikacji odrzuca ręczną zmianę;
   - **odświeżanie:** przy starcie sesji albo zadania i na żądanie, przyrostowo od ostatniego pobrania; decyzje
     zastąpione i unieważnione też są pobierane, żeby kopia nie pokazywała nieaktualnej decyzji jako obowiązującej;
   - **bez połączenia:** aplikacja używa ostatniej kopii i pokazuje jej wiek; własne decyzje zapisuje lokalnie
     i dosyła po powrocie połączenia (pkt 6);
   - **poza gitem:** pamięć podręczna leży poza plikami śledzonymi (w fabryce obok `.tf/cache/`), więc nie trafia
     do historii repo i nie rozjeżdża się tak jak przypięte kopie kontraktu;
   - **poza suitą:** pamięci podręcznej nie ma i aplikacja widzi tylko własne decyzje.
6. **Dołączenie do suity i przerwy w łączności:** aplikacja dosyła zaległe decyzje (fabryka ma już listę
   „niewysłanych”); zapis jest idempotentny po pochodzeniu, więc ponowne wysłanie niczego nie dubluje.
7. **Spec, plany i taski zostają w gicie przy zmianie**, bez indeksowania w suicie; fabryka przeszukuje je lokalnie
   przed nowym zadaniem.

### Kroki (każdy to jeden PR; niezależne od otwartych decyzji, równolegle z etapem 2)

| # | Repo | PR | Wynik | Zależy od |
|---|---|---|---|---|
| D1 | di-contract (albo pdi przed wydzieleniem) | pole pochodzenia w Decision Record i w `decision.recorded`; reguła idempotencji | decyzja z dowolnej aplikacji ma jednoznaczne źródło | krok 9 planu albo osobne wydanie kontraktu |
| D2 | pdi | odbiornik przyjmuje `decision.recorded` od każdego członka suity i indeksuje wpis z linkiem do źródła | jeden indeks decyzji suity | D1 |
| D3 | tf | rdzeń zapisuje D-NNN i ADR w formacie Decision Record; w suicie wysyła `decision.recorded`, poza suitą tylko zapis lokalny; dosyłanie zaległych | decyzje z codziennej pracy fabryki trafiają do indeksu | D1 |
| D4 | pdi | `find_decisions` szuka też w dowodach i skutkach, filtruje po aplikacji źródłowej, zwraca link do źródła | wyszukiwarka obejmuje całą suitę | D2 |
| D5 | ci_for_sdlc | `decision.recorded` w nowej wersji kontraktu z polem pochodzenia, także dla rozstrzygnięcia pytania, przyjęcia ryzyka i odrzucenia (dziś tylko odpowiedzi znalezione przez AI) | wszystkie decyzje DI Definition w indeksie | D1, krok 3 planu |
| D7 | pdi | odczyt przyrostowy indeksu: decyzje zmienione od podanego znacznika, z filtrem zakresu, razem z zastąpionymi i unieważnionymi | źródło dla pamięci podręcznej | D2 |
| D8 | tf | lokalna pamięć podręczna decyzji suity tylko do odczytu: pobranie przy starcie sesji i na żądanie, wiek kopii widoczny, przeszukiwana razem z lokalnymi `decisions.md` przed zadaniem | fabryka zna decyzje innych aplikacji także bez połączenia | D3, D7 |
| D9 | ci_for_sdlc | ta sama pamięć podręczna w DI Definition: decyzje spoza aplikacji widoczne przy ustaleniu i pytaniu, oznaczone jako pochodzące z suity | spójność definicji uwzględnia decyzje z fabryki i z bramek | D5, D7 |
| D6 | pdi | uzgodnienie zapisu D2/R1 w `decyzje.md` z tym modelem (publikacja zdarzeniem zamiast odczytu z repo) | dokumenty mówią to, co robi kod | — |

Później: DI Release, DI Release Control i DI Quality publikują swoje decyzje tym samym zdarzeniem i dostają tę samą
pamięć podręczną, gdy będą miały
co publikować (np. zmiana flagi na PROD, przyjęcie wyniku testów). Szukanie po znaczeniu dopiero, gdy DI Decision
będzie usługą z bazą (DA4).

## 3b. Kto dostaje sprawę i co, gdy zespół milczy (dopisane 2026-11-22)

Pytania właściciela: jak sprawić, żeby wiadomości trafiały do właściwych osób, a nie do wszystkich; co zrobić, gdy
z dziesięciu osób odpowiedzą dwie i sprawa wisi tydzień; czy decyzje mają termin ważności; czy wisząca decyzja
blokuje zadanie.

### Zasady

1. **Decyduje jedna, nazwana osoba; zespół doradza.** To nie jest głosowanie, więc nie ma progu głosów ani kworum.
   Dwie odpowiedzi z dziesięciu to dwie opinie, a milczenie pozostałych to brak sprzeciwu. (Zgodne z ustaleniami
   „Ask team” w `TODO.md`: decydent się nie zmienia.)
2. **Powiadomienie wynika z roli w sprawie, nie z bycia w zespole:**

   | Rola w sprawie | Ile osób | Jak dociera |
   |---|---|---|
   | decydujesz | jedna | od razu, osobnym kanałem, z terminem i jedną akcją |
   | jesteś pytany | 2–4 wskazane | od razu, z terminem zamknięcia |
   | informowany | reszta | skrót zbiorczy raz dziennie albo tylko tablica, bez powiadomienia |

3. **Skąd wiadomo, kto jest kim:** decydent z operating modelu (typ decyzji → rola → osoba); pytani wskazani przez
   decydenta albo wynikający z własności (kto uruchomił zadanie, właściciel modułu); reszta nie dostaje nic.
4. **Kanał „decydujesz” musi być czysty:** każda wiadomość w nim wymaga działania. Miara: odsetek takich
   wiadomości zamkniętych bez decyzji; gdy rośnie, routing jest zły.
5. **Każde pytanie ma termin zamknięcia zależny od odwracalności** [wartości wyjściowe do potwierdzenia
   w operating modelu]: 1–2 dni robocze dla decyzji łatwej do cofnięcia, 3–5 dla trudnej. Tydzień nie jest
   wartością domyślną.
6. **Opcja domyślna po terminie:** pytający podaje ją przy pytaniu („jeśli do czwartku nikt nie zaprotestuje,
   robimy A”). Po terminie obowiązuje bez dodatkowego kroku, o ile decyzja jest łatwa do cofnięcia; przy trudnej
   decydent musi ją potwierdzić.
7. **Gdy milczy decydent:** eskalacja według operating modelu (zastępca, potem przełożony), nie czekanie.
8. **Pytanie wygasa, decyzja nie.** Decyzja ma datę przeglądu (`review_by`) i warunki unieważnienia przy założeniach
   (`invalidated_if`); oba pola są już w Decision Record.
9. **Blokowanie zależy od odwracalności:** przy decyzji łatwej do cofnięcia agent idzie dalej z opcją rekomendowaną,
   oznaczoną jako tymczasowa (najlepiej za flagą), i poprawia, jeśli decyzja wyjdzie inna. Decyzja trudna do
   cofnięcia (wydanie na PROD, model danych, bezpieczeństwo, koszt) blokuje, ale tylko tę część pracy, która od
   niej zależy. Koszt czekania jest widoczny na karcie.

### Skąd ten wzór

Praktyki znane z innych organizacji (z ogólnej wiedzy, bez sprawdzania źródeł): lazy consensus w projektach Apache
(brak sprzeciwu w 72 godziny oznacza zgodę), okres ostatnich uwag w procesie RFC Rusta, „rough consensus” w IETF
(liczą się nierozwiązane sprzeciwy, nie głosy), podział decyzji na odwracalne i nieodwracalne w Amazonie, jedna
osoba bezpośrednio odpowiedzialna (DRI w GitLabie, modele DACI i RAPID), pytanie o sprzeciw zamiast o poparcie
w socjokracji. Wspólne: jeden decydent, termin, milczenie jako zgoda, tempo zależne od odwracalności.

### Kroki (każdy to jeden PR)

| # | Repo | PR | Wynik | Zależy od |
|---|---|---|---|---|
| N1 | pdi | operating model (krok 8) dostaje: decydenta i zastępcę per typ decyzji, domyślne terminy per odwracalność, ścieżkę eskalacji | routing i terminy mają źródło | treść od właściciela (pyt. 9) |
| N2 | di-contract (albo pdi przed wydzieleniem) | pole `reversibility` w decyzji (jest na liście w `TODO.md`, niezrobione); w pytaniu: `closes_at`, `default_option`, lista pytanych; znacznik decyzji tymczasowej | dane dla terminów, opcji domyślnej i blokowania | razem z `consulted` (T4) |
| N3 | pdi | skrzynka zamyka pytanie po terminie: opcja domyślna przy decyzji łatwej do cofnięcia, eskalacja przy trudnej albo przy milczeniu decydenta | nic nie wisi bez końca | N1, N2 |
| N4 | tf | faza idzie dalej z opcją rekomendowaną jako tymczasową, gdy decyzja jest łatwa do cofnięcia; zatrzymuje tylko zależną część przy trudnej | wisząca decyzja nie blokuje całości | N2 |
| N5 | di-channels | trzy poziomy powiadomień (decydujesz, jesteś pytany, informowany) w polityce powiadomień; miara czystości kanału „decydujesz” | wiadomości trafiają do właściwych osób | krok 17 (CH2), N1 |

## 4. Pierwsze kroki: każdy to jeden PR

Kolejność w tabeli jest kolejnością pracy. Kroki 1–12 nie wymagają żadnej otwartej decyzji poza treścią operating modelu przy kroku 8.
Szacunki tygodni przy jednej osobie pracującej w sesjach, jak dotąd [założenie].

| # | Tydz. | Repo | PR | Wynik | Zależy od |
|---|---|---|---|---|---|
| 1 | 1 | pdi | ten plan + linia stanu w README na 0.14.0 | plan w repo, README mówi prawdę | — |
| 2 | 1 | tf | przypięta kopia kontraktu 0.13.0 → 0.14.0 (`sync_contract.py`) | fabryka na bieżącym kontrakcie | — |
| 3 | 1 | ci_for_sdlc | zestaw przypięcia 0.14.0 obok istniejących | DI Definition zna bieżący kontrakt | — |
| 4 | 1–2 | evdt-service-shipscope | schematy zdarzeń 0.4.0 → 0.14.0 z testem zgodności | DI Release na bieżącym kontrakcie | sprawdzić, czy zmiany 0.5–0.14 są dla niego zgodne wstecz |
| 5 | 1–2 | evdt-service-shipscope | zbadanie i naprawa `flag-file-parser.test.js` | zielone testy serwera | — |
| 6 | 2 | di-contract (nowe) | wydzielenie `pdi/contract/` z workflow wydań | `contract-v0.14.0` z nowego repo | założenie repo przez właściciela |
| 7 | 2 | pdi, tf, ci_for_sdlc, ShipScope | po jednym PR: pole `repo` przypięcia na `di-contract` | wszyscy konsumenci czytają z jednego źródła | 6 |
| 8 | 2–3 | pdi | `docs/16-operating-model.md`: kto zatwierdza B1–B5, SLA, eskalacja (P1) | bramki mają zatwierdzających | treść od właściciela (pyt. 9) |
| 9 | 3 | di-contract | 0.15.0: `started_by`, zdarzenia `run.started` / `run.finished`, stan przeglądu PR (T1) | dane dla tablicy „Now” | 6 |
| 10 | 3 | pdi | odbiornik przyjmuje `run.started` / `run.progress` / `run.finished` z fabryki | przebiegi spoza pdi widoczne w rejestrze | 9 |
| 11 | 3–4 | tf | hook zgłaszający start, postęp i koniec przebiegu także dla sesji ręcznych (T2) | karta „In progress” ma dane | 9 |
| 12 | 4 | pdi | ekran `/now` w lokalnej konsoli, tylko odczyt, cztery kolumny, „Started by” (T3) | pierwsza wersja DI Team | 10 |
| 13 | 4 | pdi | zapis decyzji (ADR): usługa tożsamości suity, silnik, identyfikator osoby i organizacji, uprawnienie do produktu | podstawa pod B | pyt. 4a |
| 13a | 4 | di-service-template (nowe) | szablon: CI, wydania, przypięcie kontraktu, weryfikacja tokenu, zdarzenia | wzorzec dla nowych repo | stos (pyt. 4a, DA4) |
| 14 | 4–5 | di-identity (nowe) | usługa tożsamości: organizacja, osoba, uprawnienie do produktu, federacja z jednym dostawcą klienta, tokeny usług | jedna osoba w suicie | 13, 13a |
| 14b | 5–6 | di-identity | Admin Console AC1: organizacja, użytkownicy, uprawnienia do produktów, dostawca tożsamości, dziennik zmian (§2b) | administrator klienta ma jedno miejsce | 14 |
| 14a | 5 | di-contract | `suite.yaml` z testem spójności wersji | korelacja wersji w jednym miejscu | 6, 7 |
| 15 | 5 | ci_for_sdlc | R1a: pytanie od człowieka przy historyjce (pochodzenie `human` obok `rule`/`ai`/`drift`), w aplikacji | początek refinementu bez komunikatora | — |
| 16 | 5–6 | di-channels (nowe) | CH1: instalacja aplikacji na jednej platformie + akcja „dodaj pytanie” do DI Definition | pierwszy test refinementu z komunikatora | 14, 15, pyt. 2 |
| 17 | 6 | di-channels, pdi | CH2: „czeka na Ciebie” z bramek DI Decision | powiadomienie z linkiem do konsoli | 8, 16 |

Stan 2026-11-22: zrobione kroki 1–13, 15 i 16; krok 8 przyjęty jako OM1 (`decyzje.md`). Krok 16 sprawdzony na
żywo 2026-11-22: `/di-question` w testowej przestrzeni Slacka zapisał pytanie przy historyjce w DI Definition
(di-channels uruchomione lokalnie przez tunel; instrukcja: `di-channels/slack-setup.md`). Otwarte: 13a, 14, 14a,
14b, 17 (w toku: pdi wysyła `gate.waiting`, di-channels pisze w Slacku).

Równolegle z tą tabelą idą kroki D1–D9 z §3a (decyzje widoczne w całej suicie). Kroki N1–N5 z §3b (routing i terminy) idą za krokami 8 i 17. Etapy AC2–AC4 Admin Console (§2b) idą za krokami 14b, 8 i 16. Poza tabelą, do wstawienia po decyzjach: `consulted` w decyzji i „Ask team” (T4), zdarzenie `test-result`
i wysyłka z `qa summary` (DI Quality), konektor DI Release → DI Release Control, bramki B4/B5 z fabryki.

Kryterium po sześciu tygodniach: wszyscy konsumenci na jednej wersji kontraktu z jednego repo; tablica „Now”
pokazuje prawdziwy przebieg uruchomiony ręcznie i przez pdi; jedna osoba dodała pytanie do historyjki
z komunikatora; bramka ma nazwanego zatwierdzającego, który dostał „czeka na Ciebie”.

## 5. Ryzyka tego planu

| Ryzyko | Zabezpieczenie |
|---|---|
| Krok 4 (DI Release z 0.4.0 na 0.14.0) okaże się większy niż jeden PR | najpierw porównanie schematów zdarzeń między wersjami; jeśli są zmiany niezgodne, podział na PR per zdarzenie |
| Kilka nowych repo przy jednej osobie | szablon repo usługi, manifest suity, repo zakładane dopiero przy starcie pracy (§2) |
| Usługa tożsamości jako pojedynczy punkt awarii i nowa granica zaufania | gotowy silnik zamiast własnego kodu logowania; bez własnej bazy haseł; krok 13 jest decyzją na piśmie przed kodem; Flags ma już ogólny OIDC i dostęp awaryjny jako wzorzec |
| Kanał zbudowany przed operating modelem | CH2 w tabeli zależy od kroku 8 |
| GitHub Actions dalej zablokowane płatnością konta (wg `TODO.md`; nie sprawdzałem bieżącego stanu) | wszystkie kroki 1–17 dają się sprawdzić lokalnie; wydzielenie kontraktu wymaga jednak działającego workflow wydań albo ręcznego tagu |
| Plan oparty na stanie niesprawdzonym na żywo | przed krokiem 9 jeden pełny przebieg `sdlc up` na repo próbnym jako punkt odniesienia |

## 6. Pytania do właściciela

Odpowiedzi na 1–4 są potrzebne przed etapem 2; pozostałe przed krokiem, który wskazują.

| # | Pytanie | Rekomendacja | Co blokuje |
|---|---|---|---|
| 1 | Model repozytoriów; w tym D-P3: kontrakt do osobnego repo | **rozstrzygnięte 2026-11-22: osobne repo dla każdej części**, z szablonem i manifestem suity (§2) | — |
| 2 | D-P9: Slack czy Teams na start | **rozstrzygnięte 2026-11-22: Slack**; tożsamość na start bez di-identity (autor z nazwy w Slacku) | — |
| 3 | D-P10: kanały jako osobna usługa wspólna czy część DI Assistant; nazwa | **osobna usługa wspólna we własnym repo `di-channels`**, nazwa DI Channels | krok 16 |
| 4 | Z7: wspólna tożsamość | **rozstrzygnięte 2026-11-22: usługa tożsamości suity** (§2a): aplikacje ufają jednemu wystawcy tokenów, który federuje do dostawcy klienta | — |
| 4a | Silnik i stos usługi tożsamości; pierwszy federowany dostawca | **gotowy silnik OIDC (klasa Keycloak; Flags używa go już lokalnie) + cienka warstwa organizacji i uprawnień; bez własnej bazy haseł; pierwszy dostawca ten, którym loguje się zespół pilotażu** | kroki 13, 13a, 14 |
| 5 | G6/P1: DI Team jako osobny produkt czy powłoka suity; oraz DA4: stos usługi pdi | **zacząć jako ekran konsoli DI Decision; decyzja po pierwszym zespole**; DA4 rozstrzygnąć przed etapem 4 | etap 4 |
| 6 | D-P11: gdzie mieszka warstwa spotkania refinementu | **sprintdeck jako pokój refinementu, ale dopiero po R1–R4 w DI Definition**; sprintdeck nie ma dziś API, kont ani wdrożenia, więc to nie jest tani krok | warstwa spotkania |
| 7 | Czy DI Quality wchodzi do planu programu jako produkt suity | **tak, jako produkt, z jednym połączeniem na start**: wynik testów jako dowód dla bramki B4/B5 przez kontrakt; usługa centralna później | `test-result` w kontrakcie |
| 8 | DI Release Control: zostaje produktem suity mimo braku wdrożenia i konsumenta, czy staje się modułem DI Release | **zostaje osobno, ale przed FL1 potrzebuje wdrożenia i jednego serwisu-konsumenta**; inaczej flaga `ai-feature` nie ma czego przełączać | FL1, konektor flag |
| 9 | D-P4: kto zatwierdza bramki B1–B5 i w jakim SLA | **rozstrzygnięte 2026-11-22 (OM1)**: właściciel, bez zastępcy, terminy ze szkicu ([16-operating-model.md](16-operating-model.md)) | — |
| 10 | Nazwy repo: czy stare się zmieniają; czy nowe dostają prefiks `di-` (lista w §2) | **stare zostają; nowe z prefiksem `di-`** | zakładanie repo |
| 11 | Kolejność wobec planu programu: fala 1 tamtego planu to Model Gateway i AI Registry; ten plan stawia przed nimi kontrakt, tożsamość, „Now” i kanał | **najpierw to, co łączy istniejące aplikacje** (ten plan), potem bramka modeli; do potwierdzenia, bo zmienia to kolejność fal | §7 |

## 7. Różnice wobec planu programu

- **Repozytoria:** zgodnie z planem programu każda nowa aplikacja ma osobne repo; ten plan dodaje szablon repo
  usługi, manifest suity, repo usługi tożsamości i nazwy z prefiksem `di-`.
- **Tożsamość:** plan programu zostawia ją jako Z7 poza zakresem; tutaj jest usługą wspólną budowaną przed kanałami.
- **Kolejność:** plan programu zaczyna od bramki modeli i inwentarza; ten plan od kontraktu, tożsamości, tablicy
  „Now” i kanału. Operating model (P1) jest w obu na początku.
- **Stan fabryki:** plan programu mówi o tf 20.1.0 i o T4/T6 czekających na gałęzi; na `main` fabryki 22.2.0 oba są
  (`eval_gate.py`, `models_approved`).
- **DI Quality:** w planie programu go nie ma; tutaj jest pytaniem nr 7.
- **Stan kopii kontraktu, tożsamości i połączenia DI Release z DI Release Control** nie jest w planie programu
  opisany; §1 tego dokumentu go dopisuje.
