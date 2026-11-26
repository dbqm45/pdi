# Do zrobienia

Rzeczy odłożone na później, z tym, co już ustalono. Kroki planów i ich stan: [plan jednego flow](docs/plan-jeden-flow-sdlc.md)
§8 („Co zostało”), [plan automatyzacji i konsoli](docs/plan-automatyzacja-i-konsola.md) §8.

## Instalacja tf w pdi (odłożona 2026-10-28)

Krok F0 planu jednego flow („tf w ShipScope i pdi … jeden sposób pracy agentów wszędzie”). Wstrzymane do decyzji
właściciela; nic nie jest zainstalowane.

**Co da:** te same zasady i zabezpieczenia pracy agentów w każdej sesji w pdi (także w chmurze), jak w ci_for_sdlc:
- `CLAUDE.md` z zasadami projektu (TDD, fakty po sprawdzeniu, plan przed kodem, SemVer, sekrety tylko w zmiennych
  środowiskowych, dziennik w `docs/project/`);
- hooki działające niezależnie od modelu: blokada niebezpiecznych poleceń powłoki (część wymaga zgody), ochrona plików
  z sekretami i konfiguracji zabezpieczeń, skan sekretów po każdym zapisie, strażnik TDD (kod produkcyjny dopiero po
  czerwonym teście), ostrzeżenie o długim kontekście, wykrycie stosu na starcie, dziennik zużycia tokenów;
- skille (rdzeń i pack-it: Python, pytest, testy, bezpieczeństwo, dokumentacja; pack-editorial-pl) i agenci do
  tańszej delegacji (`scout`, `quick-fixer`, `security-reviewer`).

**Czego nie zmienia:** kodu i bezpieczeństwa działającego pdi (odbiornik, podpisy, tokeny, rejestr) ani bramek
(`uv run pytest`, ruff, mypy). Workflow CI z tf nie ruszy, dopóki GitHub Actions nie działa (płatności).

**Ustalone:**
- Rekomendacja: instalacja zespołowa (pliki w repo), bo praca idzie w sesjach w chmurze; prywatna działałaby tylko
  na komputerze właściciela.
- Próba na sucho (tf 5.50.0, 2026-10-28): `--shared --packs pack-it --language pl --commit-language pl` → 956 nowych
  plików (głównie markdown skilli), scalenie `.gitignore` (13 wpisów), bez zmian w istniejących plikach pdi.
- Koszt: jednorazowo duży PR; sesje w pdi stają się bardziej rygorystyczne (TDD wymuszone, część poleceń git pyta
  o zgodę); aktualizacje tf (`python3 factory/update.py`) to od czasu do czasu PR z nowymi wersjami skilli.

**Jak zrobić, gdy zapadnie decyzja** (w klonie pdi, `$TEAM_FACTORY` = klon tf):
```bash
python3 "$TEAM_FACTORY/core/factory/install.py" --dry-run --yes --shared --packs pack-it --language pl --commit-language pl
python3 "$TEAM_FACTORY/core/factory/install.py" --yes --shared --packs pack-it --language pl --commit-language pl
uv run pytest && uv run ruff check src tests && uv run mypy src   # bramki pdi bez zmian
```
Potem przejrzeć wygenerowany `CLAUDE.md` (dopisać komendy pdi: `uv run pytest`, ruff, mypy, Python 3.11 i 3.13)
i otworzyć PR. Przy okazji: aktualizacja starszej instalacji w `ci_for_sdlc/.claude` (ten sam punkt planu).

## Decyzje przypięte do kodu: `applies_to` (zapisane 2026-10-29)

Źródło: artykuł „Teaching AI Agents to Remember: ADRs, Specs, Engineering Decisions” (A. Kokane, 2026-10-19).
Przypadek z niego: dwa PR-y, każdy poprawny, razem odwracają przyjętą decyzję, bo drugi agent jej nie znał.

**Co już jest w kontrakcie** (`contract/decision.schema.json`): uzasadnienie i opcje, `assumptions[]` z
`load_bearing` i `invalidated_if` („kiedy rozważyć ponownie”), `review_by`, `status: superseded` z `supersedes` /
`superseded_by`, `links` do PRB, CHG, TSK i PR. Brakuje jednego: **nic nie łączy decyzji z plikami**, więc ani agent,
ani bramka nie wiedzą, że zmiana rusza obszar objęty decyzją.

**Do zrobienia** (TDD, wersja kontraktu wg SemVer; tag `contract-v…` po merge'u):
- [x] **Pole `applies_to` w decyzji** (zrobione 2026-11-24: kontrakt 0.22.0, `paths` i `components`, dopasowanie w `decision-record.md` §4a; [plan](docs/plan-applies-to.md)) — wzorce ścieżek (`services/document-processing/**`) i/lub nazwy komponentów;
  opcjonalne, więc zgodne wstecz (podbicie minor kontraktu). Przykład w `contract/examples/`, README kontraktu.
- [x] **Zapytanie „decyzje dla tych ścieżek”** (zrobione 2026-11-24: `find_decisions` z `paths` i `components`, pole `matched`) w MCP (`find_decisions` z parametrem ścieżek albo osobne narzędzie):
  przyjęte decyzje, których `applies_to` pasuje do podanych plików, z `why` i założeniami. Agent woła je przed planem
  zmiany i podaje w podsumowaniu, które decyzje sprawdził.
- [x] **`applies_to` przy zapisie decyzji** (zrobione 2026-11-24: `record_decision` i `decision.recorded`; tf `decision add --applies-to`) — `record_decision` przyjmuje pole; tf `decision add` je przekazuje (pozycja
  w tf przy następnej zmianie `mode-pdi`).
- [x] **Sposób weryfikacji i odwracalność decyzji** (zrobione 2026-11-24: `reversibility` `local` / `broad` / `one_way` i `provisional` w kontrakcie 0.19.0, N2; terminy z bramek w pdi #206) (źródło: J. Wąsowski, „SDD — Missing Spec Decisions: The
  Two-Implementations Technique and a Decision Register”, 2026-10): sposób weryfikacji jest już w kontrakcie 0.14.0
  jako `confirmation` (`kind`: test / ci_check / review…, `ref`: np. id testu); zostaje opcjonalne `reversibility` (`local` — agent decyduje
  i zapisuje; `broad` — agent proponuje, człowiek akceptuje; `one_way` — właściciel rozstrzyga przed implementacją:
  usuwanie danych, migracja, uprawnienia produkcyjne, publiczny kontrakt API). Decyzja bez sposobu weryfikacji to
  życzenie; ci_for_sdlc może sprawdzić, że `verify` wskazuje istniejący test. Klasy decyzji, o które pytać, gdy
  specyfikacja milczy: skala, tryb wykonania (od razu / w tle), awaria i ponowienia, uprawnienia, migracja
  istniejących danych.
- [x] **Szablon PR „Wpływ na decyzje”** (zrobione 2026-11-25: pdi#214, ci_for_sdlc#151, tf#442; bramka ci_for_sdlc czyta odpowiedź, ci_for_sdlc#152) (`.github/pull_request_template.md`): których decyzji dotyczy, czy zmienia
  przyjętą (nie / tak / nie wiem), uzasadnienie. Ten sam szablon w ci_for_sdlc i tf.

**Odbiorca:** ci_for_sdlc — reguła na PR, gdy zmienione pliki trafiają w `applies_to` przyjętej decyzji (pozycja w
`ci_for_sdlc/TODO.md`). Czego nie robić: osobnego `INDEX.md` decyzji w repo — rejestr pdi jest katalogiem, druga kopia
by się rozjeżdżała.

## Autoryzacja zdalnego serwera MCP (etap 2 z `docs/14-pdi-standalone.md`, zapisane 2026-10-29)

Dziś serwer MCP pdi działa przez stdio (lokalnie, bez autoryzacji). Etap 2 planu — ten sam serwer jako zdalny
connector Claude.ai / desktop (HTTP) — wymaga autoryzacji wg specyfikacji MCP. Źródło przeglądu: artykuł „MCP
Learnings” (C. Hobbs, 2026-10); wymagania sprawdzić w specyfikacji na modelcontextprotocol.io z datą przed planem.
- [x] **Przed etapem 2:** OAuth 2.1 z PKCE i odkrywaniem serwera autoryzacji z metadanych zasobu; serwer MCP tylko
  waliduje tokeny, a wydaje je zewnętrzny dostawca (zrobione 2026-11-25, lokalnie: `pdi-mcp --http`,
  [plan](docs/plan-mcp-zdalny.md); wystawcą jest Keycloak suity). Rejestracja klienta inaczej, niż zapisano tu
  2026-10-29: klient zarejestrowany z góry `di-decision-mcp` w `dbqm45/di-identity`. W Keycloak 26.4.7 nie ma Client
  ID Metadata Documents, a anonimowa dynamiczna rejestracja otwierałaby realm. Wrócić do CIMD, gdy Keycloak go
  obsłuży.
- [x] Zakresy dopasowane do narzędzi, zrobione rolami zamiast zakresów OAuth: `viewer` odczyt, `editor`/`admin` zapis
  (z `supersede_decision`), agent tylko odczyt. Zakres OAuth jest jeden (`openid`), bo klient MCP inaczej prosi o całą
  listę wystawcy.
- [ ] Zapis decyzji i zastępowanie jako narzędzia wysokiego ryzyka z potwierdzeniem (wzorzec „zgoda związana z
  argumentami”, pozycja w `tf/docs/todo.md`, sekcja wzorców bezpieczeństwa) — razem z kartą MCP Apps niżej.
- [x] Bez sesji protokołu: `pdi-mcp --http` działa bezstanowo (`stateless_http`, odpowiedzi JSON). Stan (np. szkic
  przed zatwierdzeniem) to jawny identyfikator z narzędzia. Przestarzałych Sampling/Roots/Logging nie używa.
- [ ] Przed hostingiem: connector w Claude.ai (publiczny https, adres zwrotny Claude.ai w `di-decision-mcp`).
  `offline_access` rozstrzygnięte 2026-11-25: tylko ten klient, sesja offline 24 h bez użycia, najwyżej 14 dni.

## Karta zatwierdzenia decyzji jako MCP App (etap 2, zapisane 2026-10-29)

Źródło: artykuł „Stop Returning JSON. Start Shipping UI with MCP Apps” (A. Tkachuk, 2026-09-14). Rozszerzenie MCP
Apps pozwala serwerowi dołączyć do narzędzia interfejs (`ui://…`), który host (Claude.ai, desktop, VS Code)
renderuje w rozmowie; przyciski wołają narzędzia przez hosta. Obsługę w hostach i pola specyfikacji sprawdzić
na apps.extensions.modelcontextprotocol.io z datą przed planem [niezweryfikowane]. Dotyczy etapu 2 (zdalny connector).
- [ ] **„AI szkicuje, człowiek zatwierdza” jako karta, nie jako „tak” w czacie:** `present_decision_draft` pokazuje
  szkic (stwierdzenie, uzasadnienie, opcje, założenia ze statusami epistemicznymi) z przyciskami Zatwierdź / Popraw /
  Odrzuć. `record_decision` z widocznością tylko dla App (`_meta.ui.visibility: ["app"]`), więc model nie zapisze
  decyzji bez kliknięcia człowieka — to wzmacnia zasadę z §2 `docs/14-pdi-standalone.md` mechanizmem zamiast prośbą.
- [ ] Zatwierdzenie przez ID szkicu i jego wersję (hash pól), nie przez przesłanie całego tekstu: karta sprzed
  poprawki zostaje odrzucona. Powód odrzucenia wraca do kontekstu modelu, żeby kolejny szkic go uwzględnił.
- [ ] Fallback: host bez MCP Apps dostaje szkic jako treść strukturalną i dotychczasowe potwierdzenie w rozmowie.
- [ ] Pomiar: karta ma skrócić czas zapisu (W2, mediana ≤ 60 s) — porównać z `/record-decision` w dogfoodingu.

## Zatwierdzenie bramki związane z dowodem (zapisane 2026-10-29)

Źródło: artykuł o Accension („How to Verify AI-Generated Code: Checks, Review and Receipts”, 2026-10) — zgoda człowieka
dotyczy konkretnego dowodu, a zmieniony dowód unieważnia zgodę. Dziś `gate.requested` z tf niesie ścieżkę artefaktu
i link do PR, bez skrótu treści.
- [x] (zrobione 2026-11-24: kontrakt 0.21.0, tf wysyła skrót i commit, pdi zapisuje go i odsyła w `gate.decided`; porównanie w tf przed następną fazą zrobione tego samego dnia: pdi przekazuje zatwierdzony skrót do fazy, tf zapisuje go w `decisions.md` i nie zaczyna fazy na zmienionym artefakcie) Kontrakt zdarzenia `gate.requested`: pole ze skrótem SHA-256 artefaktu i SHA commita (zmiana wstecznie zgodna —
  pole opcjonalne, potem wymagane). Zatwierdzenie bramki w pdi zapisuje ten skrót; zdarzenie zwrotne do tf niesie go
  z powrotem, a tf przed następną fazą porównuje go z bieżącym artefaktem (pozycja w `tf/docs/todo.md`).
- [x] (zrobione 2026-11-24: konsola pokazuje skrót i commit, zatwierdzenie zmienionego artefaktu → 409; skrót liczony z końcami linii LF) UI zatwierdzenia pokazuje skrót i datę artefaktu; zgoda na nieaktualną wersję jest odrzucana z komunikatem
  „artefakt zmienił się po wysłaniu prośby”. TDD: test zgody na zmieniony artefakt.

## Propozycja do G7 „miary przepływu”: wskaźniki wyprzedzające w parze z opóźnionymi (zapisane 2026-10-30)

Źródło: artykuł „SDD Factory Dashboard: The Leading and Lagging Indicators That Actually Matter” (J. Wąsowski,
2026-08-12). Kokpit pokazujący tylko aktywność (liczbę wdrożeń, PR) pozostaje zielony aż do zatoru. Według artykułu
najlepiej udokumentowanym sygnałem wyprzedzającym przy kodzie od agentów jest kolejka czekająca na przegląd człowieka
(liczby z artykułu [niezweryfikowane]). pdi ma już dane do takiej kolejki: każda pozycja `inbox/` i
`changes/<CHG>.yaml` niesie historię bramek.
- [x] (zrobione 2026-11-24 w DV4: strona „Przepływ”, `flow_delays`; p90 od 2026-11-25) Miara kolejki bramek z istniejących plików skrzynki i zmian, bez nowego źródła danych:
  - liczba pozycji czekających na decyzję;
  - wiek najstarszej pozycji;
  - mediana i p90 czasu od `gate.requested` do `gate.decided`, w podziale na bramki B1–B5.

  Najpierw test na plikach w katalogu tymczasowym.
- [ ] Para z wskaźnikiem opóźnionym z ShipScope: rollbacki i hotfiksy na wydanie (CFR) oraz nowe PRB po wydaniu
  (defekty u użytkownika). Rosnąca kolejka przy rosnącym CFR to sygnał zatoru przeglądu, a nie „więcej pracy”.
- [ ] Dryf specyfikacji jako drugi wskaźnik wyprzedzający: sygnał z ci_for_sdlc (rozjazd definicji ze stanem) albo
  z `plan_drift.py` w tf. Do ustalenia, kto go emituje jako zdarzenie kontraktu.
- [ ] Zasady:
  - miary liczone dla systemu i zmiany, nigdy dla osoby;
  - każda miara prędkości ma obok miarę jakości;
  - eksport przez API usług (pozycja F5: rollbacki, dryf, czas realizacji) w trzech widokach o różnej częstotliwości:
    tydzień (zespół), miesiąc, kwartał.

  Rozstrzygnięcie G7 zapisać jako decyzję w rejestrze.

## Format Decision Record (przyjęte 2026-11-07, DR1–DR4)

Ustalenia: [propozycja](docs/propozycja-decision-record.md), decyzje DR1–DR4 w [`decyzje.md`](docs/decyzje.md).
Kroki (TDD, wersja kontraktu wg SemVer, tag `contract-v…` po merge'u):
- [x] **Kontrakt 0.14.0** (2026-11-07, [plan](docs/plan-kontrakt-0140.md)): opcjonalne `record` (`decision`),
  `schema` i `contract_version`; `consequences` (`text`, `effect`: good / bad / neutral) i `confirmation` (`how`,
  `kind`: test / ci_check / review / metric / manual, `ref`) — `confirmation` obejmuje planowane `verify` z sekcji
  „Decyzje przypięte do kodu” (zostaje tam tylko `reversibility`). Rejestr zapisuje nowe pola; przyjmowanie ich
  w narzędziach MCP (`record_decision`, `decide_inbox_item`) i wyświetlanie w treści pliku — razem z krokiem „Zapis
  ze znacznikiem”.
- [x] **Specyfikacja `contract/decision-record.md`** (2026-11-07, [plan](docs/plan-spec-i-walidator-dr.md)):
  plik, rozpoznanie po `record: decision`, znacznik, pola, nazwa pliku, katalogi, zastąpienia, wersjonowanie,
  sprawdzanie, przykład (test pilnuje, że przechodzi walidator). Do opisania: znaczenie `status: reverted`.
- [x] **Zapis ze znacznikiem** (2026-11-07, [plan](docs/plan-zapis-decision-record.md)): rejestr pdi nadaje znacznik
  przy każdym zapisie (klient go nie podaje); `pdi-records migrate` dopisuje go w istniejących rejestrach w miejscu,
  jednym commitem; treść pliku pokazuje „Skutki” i „Jak sprawdzić”; `record_decision`, `supersede_decision`
  i `decide_inbox_item` przyjmują `consequences` i `confirmation`. tf bez zmian: `decisions.md` zmiany to dziennik
  wpisów, do rejestru trafia eksportem i wtedy dostaje znacznik od pdi.
- [x] **Walidator `pdi-validate <plik|katalog>...`** (2026-11-07): katalogi rekurencyjnie (pliki bez `record`
  pomijane), plik podany wprost musi być DR; nagłówek, znacznik, wersja nie nowsza niż walidator, schemat, nazwa
  pliku; powtórzone `id` i spójność zastąpień; komunikaty bez treści decyzji; kod wyjścia 1 dla CI.
- [x] **Eksport do MADR** (DR3, 2026-11-07, [plan](docs/plan-eksport-madr.md)): `pdi-records export-madr --out
  <katalog> [--project P] [--format 4|2]` — decyzje `kind: technical` jako `NNNN-<slug>.md`; domyślnie MADR 4.0.0,
  `--format 2` układ 2.1.2 dla adr-log, ADR Manager, Log4brains, pyadr i Backstage (`adr.github.io/adr-tooling/`,
  2026-11-07; 3.x nie osobno). Nadpisuje tylko własne pliki (komentarz `<!-- pdi: DEC-n -->`). Log4brains woli
  nazwy bez numerów — jeśli zespół go użyje, dodać opcję nazwy bez `NNNN-`. Import ADR-ów — dopiero przy zespole
  z istniejącymi ADR.
- [x] **Znaczenie `status: reverted`** (zrobione 2026-11-25: usunięty w kontrakcie 0.23.0, wycofanie to nowa decyzja zastępująca; decyzja właściciela) (specyfikacja §7): opisać albo usunąć z kontraktu; dziś pdi go nie nadaje,
  a eksport MADR go pomija.

## DI Team: tablica „Now” i „Ask team” (zapisane 2026-11-19, pomysł właściciela, do zrobienia w suicie)

Nowy element Delivery Intelligence Suite. Makieta (dane przykładowe, nic nie jest podłączone):
https://claude.ai/artifact/Kc1VN22yesnp44jbRQ2Jhy — kadry „Now board”, „Discuss with team”, „My turn” (telefon).
Miejsce w planie programu: [`docs/plan-program-ai-wg-aplikacji.md`](docs/plan-program-ai-wg-aplikacji.md) §3.6 i §9.

**Co da:** jedno miejsce, w którym cały zespół widzi na bieżąco, co się dzieje: które zadania są w toku, kto uruchomił
AI, który agent nad czym pracuje i co robi teraz, jakie decyzje i pytania czekają i na kogo, co się nie zgadza
(ustalenia DI Definition), co jest w przeglądzie i co zrobiono. Dziś każda aplikacja ma własny ekran, a lokalna
konsola pdi (`src/pdi/console.py`: tablica zmian, ślad, postęp fazy na żywo, skrzynka) jest dla jednej osoby.

**Ustalone (rozmowa 2026-11-19):**
- **To widok tego, co dzieje się teraz, nie komunikator.** Bez kanałów, wiadomości prywatnych i ogólnego czatu;
  skróty mogą iść do Slacka/Teams z linkiem z powrotem.
- **Tablica „Now” z czterema kolumnami:** In progress, Awaiting decision, In review, Done. Karta = zadanie
  (TSK/cięcie w zmianie CHG) i zawsze pokazuje „Started by” — osobę, która uruchomiła AI. Dalej zależnie od kolumny:
  agent i jego bieżąca czynność, cięcie, testy, koszt wobec budżetu (In progress); na co zadanie czeka — pytanie
  agenta, niezgodność z Definition albo bramka — i kto decyduje (Awaiting decision); PR, wynik przeglądu AI, ryzyko
  zmiany, recenzent (In review); kiedy scalono lub wydano i na którym środowisku (Done). Filtr „Started by”.
- **„Started by” i „Decides” to różne pola:** jedna osoba uruchamia zadanie, a pytanie może trafić do innej.
- **Nie jest źródłem prawdy:** czyta zdarzenia aplikacji suity przez kontrakt; zapis idzie zawsze przez aplikację
  właścicielską (decyzja → DI Decision, odpowiedź na ustalenie → DI Definition).
- **„Ask team” przy decyzji:** decydent może zdecydować sam („Decide”) albo wysłać sprawę do zespołu („Ask team”).
  Sprawa zostaje w „Awaiting decision” ze znacznikiem „With team · N z M odpowiedzi · zamknięcie za …” i pojawia się
  w widoku „Discuss with team”. Dwie drogi:
  - *online (asynchronicznie):* każdy wybiera opcję i dopisuje jedno zdanie; odpowiedzi ukryte do zamknięcia (żeby
    nikt nie kotwiczył się na pierwszej); agent nie głosuje, tylko dokłada skutki każdej opcji (plan, koszt, testy);
    zgodność → decydent zatwierdza jednym kliknięciem; rozbieżność albo „wymaga rozmowy” → agenda refinementu;
  - *refinement:* „Discuss with team” jest agendą najbliższego spotkania, ułożoną według tego, co sprawy blokują;
    decyzję zapisuje się z tej samej karty.
- **Zasady „Ask team”:** decydent się nie zmienia (zespół doradza); każde pytanie ma czas zamknięcia, po nim decydent
  rozstrzyga z tym, co zebrał; karta pokazuje cenę czekania (wstrzymany agent, nierozpoczęte cięcia, termin bramki);
  pytanie idzie do wybranych osób, nie do wszystkich; decyzja w DI Decision zapisuje, kogo zapytano i co odpowiedział.
- **Silnik głosowania:** sprintdeck już ma głosy w ciemno, odkrycie i wykrywanie rozbieżności (D-E1: konsensus co do
  zrozumienia i ryzyka) — „Ask team” to jego użycie dla pojedynczej decyzji.

**Czego brakuje w danych (sprawdzone w kontrakcie 0.14 i kodzie 2026-11-19):**
- **Kto uruchomił przebieg.** Kontrakt ma `decided_by` w decyzji i `actor` w historyjce; nie ma pola „kto wystartował
  fazę/przebieg” w zdarzeniach. Potrzebne nowe pole (np. `started_by`) i zdarzenia startu oraz końca przebiegu.
- **Praca poza pdi.** Postęp na żywo (`last_progress`) istnieje dla faz uruchamianych przez pdi; sesja uruchomiona
  ręcznie w terminalu nie wysyła nic. Potrzebny hook w fabryce, który zgłasza start, postęp i koniec także takich sesji.
- **Wspólna tożsamość.** „Ola” na karcie musi być tą samą osobą w każdej aplikacji — to samo, czego wymaga G6/P1
  (jedna platforma) i Z7 planu programu.
- **Stan przeglądu.** Wynik przeglądu AI i ryzyko zmiany (`tf risk`, `ai-review/verdict`) są w repo i na PR, nie
  w zdarzeniach kontraktu.

**Kroki (każdy osobno, kolejność do potwierdzenia):**
- [x] **T1 — kontrakt** (zrobione 2026-11-22: di-contract 0.15.0/0.15.1 — `run.started`, `run.finished`, `run`, `started_by`, `activity` w `run.progress`, `review` w `run.finished`; pdi przyjmuje je od tf do `agent-runs/`, `pdi.runs`; wersja z planu poniżej zostaje dla historii): `started_by` oraz zdarzenia `run.started` / `run.progress` / `run.finished` (zadanie, zmiana,
  agent, czynność, cięcie, koszt, budżet); stan przeglądu PR (werdykt AI, ryzyko, recenzent) w zdarzeniu.
- [x] **T2 — fabryka:** hook zgłaszający start, postęp i koniec przebiegu także dla sesji ręcznych (dziś tylko fazy
  uruchamiane przez pdi mają postęp); tożsamość z gita albo z konta suity. (sprawdzone 2026-11-25: tf `run_report.py`
  zgłasza każdą sesję — `run.started`, `run.progress`, `run.finished` — z tożsamością z `git config user.name`;
  tożsamość z konta suity dopiero z di-identity, krok 14)
- [x] **T3 — „Now” tylko do odczytu** (zrobione 2026-11-22: `/now` w lokalnej konsoli, `pdi.console._now_body`; dla wielu osób dopiero z konsolą jako usługą — DA4): nowy ekran w istniejącej konsoli pdi (cztery kolumny, „Started by”, filtr po
  osobie, linia stanu u góry), dla wielu osób; świeżość karty widoczna (kiedy ostatnio się zmieniła).
- [x] **T4 — „Ask team” online** (zrobione 2026-11-25 w lokalnej konsoli z logowaniem przez suitę, [plan](docs/plan-t4-ask-team.md); dla zespołu z różnych komputerów — z konsolą jako usługą): przycisk na karcie decyzji, wybór osób, opcje z pytania, odpowiedzi ukryte do
  zamknięcia, skutki opcji od agenta, czas zamknięcia; wynik jako szkic decyzji z listą zapytanych; typ decyzji
  w kontrakcie dostaje pole konsultacji (`consulted`: kto, opcja, uzasadnienie).
- [x] **T5 — „Discuss with team” jako agenda** (zrobione 2026-11-26: `/discuss` w konsoli z danych pdi, [plan](docs/plan-t5-discuss-with-team.md); sprawy z historyjek DI Definition — gdy R5 da API, pokój sprintdecka — osobno): sprawy z rozbieżnością i oznaczone „talk live”, kolejność według
  blokad, zapis decyzji ze spotkania; opcjonalnie eksport agendy.
- [x] **T6 — skróty do Slacka/Teams** (zrobione 2026-11-26 dla Slacka: wiadomość do zapytanych przy „Ask team” i dzienny skrót, [plan](docs/plan-t6-skroty-slack.md); Teams osobno): dzienny skrót i powiadomienie „czeka na Ciebie” z linkiem. Nie własnym
  botem: przez wspólną aplikację kanałów suity (plan programu §3.7, krok CH2), zapisaną 2026-11-21.
- [x] **T7 — „Escalate”** (zrobione 2026-11-26: przekazanie decyzji o jednej sprawie, OM2, kontrakt 0.27.0, [plan](docs/plan-t7-escalate.md); pomysł właściciela zapisany 2026-11-20): trzecia opcja
  na karcie decyzji, obok „Decide” i „Ask team”. Służy do zgłoszenia sprawy **powyżej zespołu albo poza zespół** —
  gdy zespół nie może albo nie powinien rozstrzygać sam. Nie wchodzi do zakresu T4/T5; robimy dopiero po „Ask team”.
  Do ustalenia przy planie (to są pytania, nie decyzje):
  - do kogo trafia eskalacja (przełożony, właściciel produktu, architekt, bezpieczeństwo, inny zespół) i skąd
    tablica zna tę ścieżkę — najpewniej z operating modelu (P1 planu programu: kto zatwierdza i co, gdy nie zatwierdzi);
  - czy eskalacja **zmienia decydenta** (inaczej niż „Ask team”, gdzie zespół tylko doradza), czy tylko prosi o głos
    z zewnątrz;
  - jak adresat spoza zespołu dostaje sprawę, skoro może nie mieć dostępu do tablicy (link, Slack/Teams z T6, e-mail)
    i ile kontekstu widzi;
  - co widać na karcie w „Awaiting decision” (np. „Escalated to … · od kiedy · termin”) i co się dzieje po terminie;
  - zapis w DI Decision: kto eskalował, do kogo, dlaczego i z jakim wynikiem; pole w kontrakcie obok `consulted`.

**Powiązania (dopisane 2026-11-21):** pytania zespołu przed spotkaniem i wynik per historyjka są zaplanowane
w DI Definition (dbqm45/ci_for_sdlc `docs/REFINEMENT-PLAN.md`); pokój do sesji na żywo z ukrytymi głosami i pytaniami
silnika ma już sprintdeck. „Discuss with team” (T5) ma z nich korzystać, a nie budować własne. Rozkład całej koncepcji
„Refinement Intelligence”: plan programu §3.8.

**Otwarte:**
- Czy DI Team jest osobnym produktem, czy powłoką całej suity, która zastępuje planowaną usługę konsoli pdi (Z3)
  i ekran „Now” z [`docs/15-jedna-platforma.md`](docs/15-jedna-platforma.md) — rekomendacja: zacząć jako ekran
  w konsoli pdi (T3), decyzję o osobnym produkcie podjąć po pierwszym zespole, który z tego korzysta.
- Granica z DI Assistant (rozmowa z Claude dla ludzi spoza IT) — DI Team rozmowy nie ma.
- Czy głosowanie w „Ask team” używa silnika sprintdecka jako usługi, czy jego reguły zostają przeniesione.
- Poziom szczegółu postępu agenta widoczny dla całego zespołu (czynność w zwykłych słowach tak; treść promptów nie).

## Checki PR jako Definition of Done (zapisane 2026-11-25, pomysł właściciela — do zrobienia na samym końcu)

> **Plan przyjęty 2026-11-25, wdrożenie odłożone:** [`docs/plan-dod-checki.md`](docs/plan-dod-checki.md) (pilot w pdi, nazwy po
> angielsku, zbiorczy `Definition of Done`, punkt 9 najpierw tylko informuje, zmiana w dwóch krokach bez zerwania
> wymaganych checków). Pytania „Do rozstrzygnięcia” niżej mają odpowiedzi w planie.

**Pomysł:** lista checków w PR mówi, czy zmiana jest *skończona*, a nie tylko, które zadania CI przeszły. Zadania
techniczne zostają (macierz Pythona, shardy tf), dostają nazwy punktów DoD (`DoD 2 · Testy (Python 3.11)`), a jeden
zbiorczy check **„Definition of Done”** ma tabelę wszystkich punktów w szczegółach i jako jedyny jest wymagany
w ochronie gałęzi. Para z gotowością definicji (Definition of Ready) z bramki ci_for_sdlc.

**Punkty DoD (propozycja):**

| # | Punkt | Jak sprawdzane | Stan 2026-11-25 |
|---|---|---|---|
| 1 | Opis zmiany w formacie Conventional Commits (≤ 72 znaki) | `conventional-commit` | jest (tf, ci_for_sdlc) |
| 2 | Testy przechodzą na wspieranych wersjach | pdi `test (3.11/3.13)`, tf `workspace (…)`, `repo`, ci `test` | jest |
| 3 | Jakość kodu: lint, format, typy | ruff, `mypy --strict`, `typecheck` | jest, wewnątrz zadań testowych |
| 4 | Build działa | `npm run build`, kontener tf | jest (ci, tf) |
| 5 | Kontrakt suity zgodny z przypiętym tagiem | `sync_contract.py check`, `contract:check` | jest |
| 6 | Definicja gotowa (cięcia z weryfikacją i kryteriami) | `analyze --repo . --fail-on critical` | w projektach opcjonalne |
| 7 | Cele zmiany spełnione (pokrycie, mutacje — TGT) | `analyze --coverage … --mutation …` | gdy `release.yaml` ma cele |
| 8 | Bezpieczeństwo: skan bez błędów (SEC-001) | `analyze --sarif …` | gdy podłączony skaner |
| 9 | Wpływ na decyzje wypełniony; „tak” tylko z decyzją zastępującą | sekcja w opisie PR + `analyze --base` | dziś tylko informuje (blokowanie: następny krok reguły w ci_for_sdlc) |
| 10 | Skille przeszły bramkę (tf) | `skill_gate.py --status` | jest, wewnątrz `workspace` |
| 11 | Dokumentacja i plan zaktualizowane | pole w opisie PR (przypomnienie) | ręczne |
| 12 | Przegląd człowieka | review na GitHubie (nie check) | — |

**Do rozstrzygnięcia przed startem:**
- zakres: wszystkie cztery repozytoria czy najpierw szablon `change-check.yml` w tf (trafia do każdego projektu);
- nazwy checków po polsku czy po angielsku (tf jest publiczne, po angielsku);
- czy punkt 9 blokuje od razu, czy po odczycie odpowiedzi z opisu PR;
- zmiana nazw zrywa wymagane checki w ochronie gałęzi: właściciel przestawia „required status checks” w ustawieniach
  repozytoriów w tym samym momencie (z sesji agenta nie ma do nich dostępu), inaczej PR-y czekają na „Expected”.
