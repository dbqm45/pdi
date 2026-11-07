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
- [ ] **Pole `applies_to` w decyzji** — wzorce ścieżek (`services/document-processing/**`) i/lub nazwy komponentów;
  opcjonalne, więc zgodne wstecz (podbicie minor kontraktu). Przykład w `contract/examples/`, README kontraktu.
- [ ] **Zapytanie „decyzje dla tych ścieżek”** w MCP (`find_decisions` z parametrem ścieżek albo osobne narzędzie):
  przyjęte decyzje, których `applies_to` pasuje do podanych plików, z `why` i założeniami. Agent woła je przed planem
  zmiany i podaje w podsumowaniu, które decyzje sprawdził.
- [ ] **`applies_to` przy zapisie decyzji** — `record_decision` przyjmuje pole; tf `decision add` je przekazuje (pozycja
  w tf przy następnej zmianie `mode-pdi`).
- [ ] **Sposób weryfikacji i odwracalność decyzji** (źródło: J. Wąsowski, „SDD — Missing Spec Decisions: The
  Two-Implementations Technique and a Decision Register”, 2026-10): sposób weryfikacji jest już w kontrakcie 0.14.0
  jako `confirmation` (`kind`: test / ci_check / review…, `ref`: np. id testu); zostaje opcjonalne `reversibility` (`local` — agent decyduje
  i zapisuje; `broad` — agent proponuje, człowiek akceptuje; `one_way` — właściciel rozstrzyga przed implementacją:
  usuwanie danych, migracja, uprawnienia produkcyjne, publiczny kontrakt API). Decyzja bez sposobu weryfikacji to
  życzenie; ci_for_sdlc może sprawdzić, że `verify` wskazuje istniejący test. Klasy decyzji, o które pytać, gdy
  specyfikacja milczy: skala, tryb wykonania (od razu / w tle), awaria i ponowienia, uprawnienia, migracja
  istniejących danych.
- [ ] **Szablon PR „Wpływ na decyzje”** (`.github/pull_request_template.md`): których decyzji dotyczy, czy zmienia
  przyjętą (nie / tak / nie wiem), uzasadnienie. Ten sam szablon w ci_for_sdlc i tf.

**Odbiorca:** ci_for_sdlc — reguła na PR, gdy zmienione pliki trafiają w `applies_to` przyjętej decyzji (pozycja w
`ci_for_sdlc/TODO.md`). Czego nie robić: osobnego `INDEX.md` decyzji w repo — rejestr pdi jest katalogiem, druga kopia
by się rozjeżdżała.

## Autoryzacja zdalnego serwera MCP (etap 2 z `docs/14-pdi-standalone.md`, zapisane 2026-10-29)

Dziś serwer MCP pdi działa przez stdio (lokalnie, bez autoryzacji). Etap 2 planu — ten sam serwer jako zdalny
connector Claude.ai / desktop (HTTP) — wymaga autoryzacji wg specyfikacji MCP. Źródło przeglądu: artykuł „MCP
Learnings” (C. Hobbs, 2026-10); wymagania sprawdzić w specyfikacji na modelcontextprotocol.io z datą przed planem.
- [ ] **Przed etapem 2:** OAuth 2.1 z PKCE i odkrywaniem serwera autoryzacji z metadanych zasobu; rejestracja
  klienta przez Client ID Metadata Documents oraz (dla starszych klientów) Dynamic Client Registration
  (sprawdzone 2026-10-29, specyfikacja `2026-07-28`: DCR przestarzałe, działa dla zgodności, usunięcie w przyszłej
  wersji bez daty; klient sprawdza `iss` wg RFC 9207 i podaje `application_type`); serwer MCP tylko waliduje tokeny (odbiorca, termin, zakresy),
  a wydawanie i odświeżanie zostawia zewnętrznemu dostawcy OAuth zamiast własnego serwera autoryzacji.
- [ ] Zakresy (scopes) dopasowane do narzędzi: odczyt rejestru osobno od zapisu decyzji i od `supersede_decision`;
  zapis decyzji i zastępowanie jako narzędzia wysokiego ryzyka z potwierdzeniem (wzorzec „zgoda związana z
  argumentami”, pozycja w `tf/docs/todo.md`, sekcja wzorców bezpieczeństwa).

- [ ] Specyfikacja `2026-07-28` ma bezstanowy rdzeń (bez `initialize` i `Mcp-Session-Id`, nagłówki `Mcp-Method`
  i `Mcp-Name`): zdalny serwer pdi projektować od razu bez sesji protokołu; stan (np. szkic decyzji przed
  zatwierdzeniem) jako jawny identyfikator zwracany z narzędzia. Przestarzałe Sampling/Roots/Logging nie używać.

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
- [ ] Kontrakt zdarzenia `gate.requested`: pole ze skrótem SHA-256 artefaktu i SHA commita (zmiana wstecznie zgodna —
  pole opcjonalne, potem wymagane). Zatwierdzenie bramki w pdi zapisuje ten skrót; zdarzenie zwrotne do tf niesie go
  z powrotem, a tf przed następną fazą porównuje go z bieżącym artefaktem (pozycja w `tf/docs/todo.md`).
- [ ] UI zatwierdzenia pokazuje skrót i datę artefaktu; zgoda na nieaktualną wersję jest odrzucana z komunikatem
  „artefakt zmienił się po wysłaniu prośby”. TDD: test zgody na zmieniony artefakt.

## Propozycja do G7 „miary przepływu”: wskaźniki wyprzedzające w parze z opóźnionymi (zapisane 2026-10-30)

Źródło: artykuł „SDD Factory Dashboard: The Leading and Lagging Indicators That Actually Matter” (J. Wąsowski,
2026-08-12). Kokpit pokazujący tylko aktywność (liczbę wdrożeń, PR) pozostaje zielony aż do zatoru. Według artykułu
najlepiej udokumentowanym sygnałem wyprzedzającym przy kodzie od agentów jest kolejka czekająca na przegląd człowieka
(liczby z artykułu [niezweryfikowane]). pdi ma już dane do takiej kolejki: każda pozycja `inbox/` i
`changes/<CHG>.yaml` niesie historię bramek.
- [ ] Miara kolejki bramek z istniejących plików skrzynki i zmian, bez nowego źródła danych:
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
- [ ] **Specyfikacja `contract/decision-record.md`:** znacznik, reguła rozpoznania (`.md` z `record: decision`),
  łańcuch zastąpień, katalogi, wersjonowanie, przykład.
- [x] **Zapis ze znacznikiem** (2026-11-07, [plan](docs/plan-zapis-decision-record.md)): rejestr pdi nadaje znacznik
  przy każdym zapisie (klient go nie podaje); `pdi-records migrate` dopisuje go w istniejących rejestrach w miejscu,
  jednym commitem; treść pliku pokazuje „Skutki” i „Jak sprawdzić”; `record_decision`, `supersede_decision`
  i `decide_inbox_item` przyjmują `consequences` i `confirmation`. tf bez zmian: `decisions.md` zmiany to dziennik
  wpisów, do rejestru trafia eksportem i wtedy dostaje znacznik od pdi.
- [ ] **Walidator `pdi-validate <plik|katalog>`:** plik bez znacznika = nie Decision Record; ze znacznikiem —
  nagłówek przechodzi schemat; kod wyjścia dla CI.
- [ ] **Eksport do MADR** (DR3) decyzji `kind: technical` do `docs/decisions/nnnn-title.md`: najpierw ustalić wersję
  docelową (4.0.0 albo układ 2.1.2 / 3.x, który czytają adr-log, ADR Manager, Log4brains, pyadr i Backstage —
  `adr.github.io/adr-tooling/`, 2026-11-07). Import ADR-ów — dopiero przy zespole z istniejącymi ADR.
