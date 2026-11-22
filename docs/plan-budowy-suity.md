# Plan budowy Delivery Intelligence Suite jako całości

Data: 2026-11-22 · Status: **propozycja do decyzji właściciela** (pytania w §6) · Nic z tego planu nie jest
rozpoczęte. · Opis stanu: artefakt „Delivery Intelligence Suite v3”,
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

## 2. Repozytoria: osobne, monorepo czy wariant pośredni

### Rekomendacja: wariant pośredni

- **Istniejące produkty zostają w swoich repozytoriach** (pdi, ci_for_sdlc, evdt-service-shipscope,
  evdt-shipscope-flags, tf, qa-platform, sprintdeck). Bez przenoszenia kodu.
- **Kontrakt wychodzi do własnego repo `di-contract`** (D-P3, zadanie X3 planu programu). To jedyna migracja.
- **Wszystkie nowe usługi wspólne i nowe produkty powstają w jednym nowym repo `di-platform`** jako moduły:
  tożsamość, kanały (DI Channels), a później AI Registry, polityka Model Gateway, DI Assistant. Jedno repo, jeden
  stos, jedno CI, jedno wydanie. Moduł wychodzi do własnego repo dopiero wtedy, gdy ma innego właściciela albo inną
  granicę zaufania w praktyce, nie na zapas.
- **DI Team nie dostaje repo.** Zaczyna jako ekran konsoli DI Decision (T3), zgodnie z planem programu §3.6.
- **tf zostaje osobno zawsze** (decyzja z `15-jedna-platforma.md` §1: instalowane w repo klienta).

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

### Dlaczego nie osobne repo dla każdej nowej aplikacji

Plan programu przewiduje `ai-gateway`, `ai-registry`, `assistant`, `channels` i (później) `team`: pięć nowych repo
przy jednoosobowym zespole. Ryzyko jest w planie programu nazwane (§6: „trzy nowe repo naraz”). Każde nowe repo to
osobne CI, wydania, instrukcje, przypięta kopia kontraktu i osobne wdrożenie. Nowe usługi mają wspólne potrzeby,
których dziś nigdzie nie ma: tożsamość osoby i organizacji, tokeny usług, podpisywanie zdarzeń, audyt. Zbudowane
raz w `di-platform` służą wszystkim modułom.

### Co się dzieje z wydaniami, CI i kopiami kontraktu w wariancie pośrednim

| Obszar | Co zostaje | Co się zmienia |
|---|---|---|
| Wydania produktów | bez zmian w każdym repo | nic |
| Kontrakt | format, SemVer, tagi `contract-v<wersja>`, test zgodności bajt w bajt u konsumentów | źródłem staje się `di-contract`; workflow `contract-release.yml` przenosi się tam; w pdi zostaje przypięta kopia jak u innych |
| Przypięte kopie | mechanizm (`tools/pdi-contract.json` w tf, `scripts/pdi-contract.json` w ci_for_sdlc, schematy w `server/schemas/` ShipScope) | pole `repo` na `dbqm45/di-contract` i wersja na bieżącą: trzy małe PR; Flags i qa-platform dostają kopię dopiero przy pierwszym zdarzeniu |
| CI | bez zmian w każdym repo | `di-platform` dostaje jedno CI; `di-contract` dostaje walidację schematów i przykładów |
| Historia | zostaje | `di-contract` zaczyna z historią katalogu `contract/` (wyciętą z pdi) albo od zera z odnośnikiem; do decyzji przy X3 |

Koszt wariantu pośredniego: wydzielenie kontraktu (rząd 2–3 dni razem z trzema PR u konsumentów) i założenie
`di-platform` (1–2 dni na szkielet z CI) [założenia].

## 3. Co odblokowuje resztę

```
decyzje właściciela (§6)
   │
   ├─ A. kontrakt: konsumenci na bieżącej wersji → repo di-contract → 0.15 (przebiegi, konsultacja, wynik testów)
   │        │
   │        ├─ C. DI Team „Now” (odczyt) w konsoli DI Decision
   │        └─ E. DI Quality jako dowód na bramce
   │
   ├─ B. tożsamość: jedna osoba i organizacja w suicie (di-platform)
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
3. **Etap 2, równolegle:** tożsamość (B) w `di-platform`; „Now” tylko do odczytu w lokalnej konsoli (C, kroki
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

- `di-platform` (zależy od §6 pyt. 1, 4, 5);
- czegokolwiek ze Slackiem albo Teams (pyt. 2, 3);
- warstwy spotkania refinementu (pyt. 6);
- zdarzenia `test-result` i połączeń DI Quality (pyt. 7);
- konsoli jako usługi (pyt. 5 i DA4).

## 4. Pierwsze kroki: każdy to jeden PR

Kolejność w tabeli jest kolejnością pracy. Kroki 1–8 nie wymagają żadnej otwartej decyzji poza D-P3 przy kroku 6.
Szacunki tygodni przy jednej osobie pracującej w sesjach, jak dotąd [założenie].

| # | Tydz. | Repo | PR | Wynik | Zależy od |
|---|---|---|---|---|---|
| 1 | 1 | pdi | ten plan + linia stanu w README na 0.14.0 | plan w repo, README mówi prawdę | — |
| 2 | 1 | tf | przypięta kopia kontraktu 0.13.0 → 0.14.0 (`sync_contract.py`) | fabryka na bieżącym kontrakcie | — |
| 3 | 1 | ci_for_sdlc | zestaw przypięcia 0.14.0 obok istniejących | DI Definition zna bieżący kontrakt | — |
| 4 | 1–2 | evdt-service-shipscope | schematy zdarzeń 0.4.0 → 0.14.0 z testem zgodności | DI Release na bieżącym kontrakcie | sprawdzić, czy zmiany 0.5–0.14 są dla niego zgodne wstecz |
| 5 | 1–2 | evdt-service-shipscope | zbadanie i naprawa `flag-file-parser.test.js` | zielone testy serwera | — |
| 6 | 2 | di-contract (nowe) | wydzielenie `pdi/contract/` z workflow wydań | `contract-v0.14.0` z nowego repo | D-P3 (pyt. 1) |
| 7 | 2 | pdi, tf, ci_for_sdlc, ShipScope | po jednym PR: pole `repo` przypięcia na `di-contract` | wszyscy konsumenci czytają z jednego źródła | 6 |
| 8 | 2–3 | pdi | `docs/16-operating-model.md`: kto zatwierdza B1–B5, SLA, eskalacja (P1) | bramki mają zatwierdzających | treść od właściciela (pyt. 9) |
| 9 | 3 | di-contract | 0.15.0: `started_by`, zdarzenia `run.started` / `run.finished`, stan przeglądu PR (T1) | dane dla tablicy „Now” | 6 |
| 10 | 3 | pdi | odbiornik przyjmuje `run.started` / `run.progress` / `run.finished` z fabryki | przebiegi spoza pdi widoczne w rejestrze | 9 |
| 11 | 3–4 | tf | hook zgłaszający start, postęp i koniec przebiegu także dla sesji ręcznych (T2) | karta „In progress” ma dane | 9 |
| 12 | 4 | pdi | ekran `/now` w lokalnej konsoli, tylko odczyt, cztery kolumny, „Started by” (T3) | pierwsza wersja DI Team | 10 |
| 13 | 4 | pdi | zapis decyzji: sposób logowania i identyfikator osoby w suicie (ADR) | podstawa pod B | pyt. 4 |
| 14 | 4–5 | di-platform (nowe) | szkielet: CI, moduł tożsamości (organizacja, osoba, powiązanie kont), tokeny usług | jedna osoba w suicie | pyt. 1, 4 |
| 15 | 5 | ci_for_sdlc | R1a: pytanie od człowieka przy historyjce (pochodzenie `human` obok `rule`/`ai`/`drift`), w aplikacji | początek refinementu bez komunikatora | — |
| 16 | 5–6 | di-platform | CH1: instalacja aplikacji na jednej platformie + akcja „dodaj pytanie” do DI Definition | pierwszy test refinementu z komunikatora | 14, 15, pyt. 2 |
| 17 | 6 | di-platform, pdi | CH2: „czeka na Ciebie” z bramek DI Decision | powiadomienie z linkiem do konsoli | 8, 16 |

Poza tabelą, do wstawienia po decyzjach: `consulted` w decyzji i „Ask team” (T4), zdarzenie `test-result`
i wysyłka z `qa summary` (DI Quality), konektor DI Release → DI Release Control, bramki B4/B5 z fabryki.

Kryterium po sześciu tygodniach: wszyscy konsumenci na jednej wersji kontraktu z jednego repo; tablica „Now”
pokazuje prawdziwy przebieg uruchomiony ręcznie i przez pdi; jedna osoba dodała pytanie do historyjki
z komunikatora; bramka ma nazwanego zatwierdzającego, który dostał „czeka na Ciebie”.

## 5. Ryzyka tego planu

| Ryzyko | Zabezpieczenie |
|---|---|
| Krok 4 (DI Release z 0.4.0 na 0.14.0) okaże się większy niż jeden PR | najpierw porównanie schematów zdarzeń między wersjami; jeśli są zmiany niezgodne, podział na PR per zdarzenie |
| `di-platform` stanie się workiem na wszystko | moduły z własnym katalogiem, własnymi testami i zakazem importu między modułami poza wspólną biblioteką tożsamości i zdarzeń |
| Tożsamość bez dostawcy (IdP) | krok 13 jest decyzją na piśmie przed kodem; Flags ma już ogólny OIDC, który może być wzorcem |
| Kanał zbudowany przed operating modelem | CH2 w tabeli zależy od kroku 8 |
| GitHub Actions dalej zablokowane płatnością konta (wg `TODO.md`; nie sprawdzałem bieżącego stanu) | wszystkie kroki 1–17 dają się sprawdzić lokalnie; wydzielenie kontraktu wymaga jednak działającego workflow wydań albo ręcznego tagu |
| Plan oparty na stanie niesprawdzonym na żywo | przed krokiem 9 jeden pełny przebieg `sdlc up` na repo próbnym jako punkt odniesienia |

## 6. Pytania do właściciela

Odpowiedzi na 1–4 są potrzebne przed etapem 2; pozostałe przed krokiem, który wskazują.

| # | Pytanie | Rekomendacja | Co blokuje |
|---|---|---|---|
| 1 | Model repozytoriów: osobne, monorepo czy pośredni? W tym D-P3: kontrakt do osobnego repo | **pośredni**: istniejące repo zostają, `di-contract` teraz, jedno `di-platform` na wszystkie nowe usługi | kroki 6, 7, 14 |
| 2 | D-P9: Slack czy Teams na start | **ta platforma, której używa pierwszy zespół pilotażu**; potrzebuję nazwy platformy i dostępu do przestrzeni testowej | krok 16 |
| 3 | D-P10: kanały jako osobna usługa wspólna czy część DI Assistant; nazwa | **osobna usługa wspólna, moduł `channels` w `di-platform`**, nazwa DI Channels | krok 16 |
| 4 | Z7: wspólna tożsamość. Własny dostawca tożsamości suity, czy logowanie przez dostawcę klienta (OIDC) z powiązaniem kont w suicie | **OIDC klienta + moduł powiązania kont w `di-platform`** (osoba, organizacja, rola); bez własnej bazy haseł | kroki 13, 14 |
| 5 | G6/P1: DI Team jako osobny produkt czy powłoka suity; oraz DA4: stos usługi pdi | **zacząć jako ekran konsoli DI Decision; decyzja po pierwszym zespole**; DA4 rozstrzygnąć przed etapem 4 | etap 4 |
| 6 | D-P11: gdzie mieszka warstwa spotkania refinementu | **sprintdeck jako pokój refinementu, ale dopiero po R1–R4 w DI Definition**; sprintdeck nie ma dziś API, kont ani wdrożenia, więc to nie jest tani krok | warstwa spotkania |
| 7 | Czy DI Quality wchodzi do planu programu jako produkt suity | **tak, jako produkt, z jednym połączeniem na start**: wynik testów jako dowód dla bramki B4/B5 przez kontrakt; usługa centralna później | `test-result` w kontrakcie |
| 8 | DI Release Control: zostaje produktem suity mimo braku wdrożenia i konsumenta, czy staje się modułem DI Release | **zostaje osobno, ale przed FL1 potrzebuje wdrożenia i jednego serwisu-konsumenta**; inaczej flaga `ai-feature` nie ma czego przełączać | FL1, konektor flag |
| 9 | D-P4: kto zatwierdza bramki B1–B5 i w jakim SLA | potrzebna treść od właściciela; mogę przygotować szkic z jednym zatwierdzającym i domyślnymi SLA | krok 8, 17 |
| 10 | Czy nazwy repo zmieniają się przy wydzielaniu kontraktu (plan programu §9, konsekwencja 2) | **nie teraz**; nowe repo dostają prefiks `di-`, stare zostają | krok 6 |
| 11 | Kolejność wobec planu programu: fala 1 tamtego planu to Model Gateway i AI Registry; ten plan stawia przed nimi kontrakt, tożsamość, „Now” i kanał | **najpierw to, co łączy istniejące aplikacje** (ten plan), potem bramka modeli; do potwierdzenia, bo zmienia to kolejność fal | §7 |

## 7. Różnice wobec planu programu

- **Repozytoria:** plan programu zakłada osobne repo `ai-gateway`, `ai-registry`, `assistant`, `channels`; ten plan
  proponuje jedno `di-platform` z modułami.
- **Kolejność:** plan programu zaczyna od bramki modeli i inwentarza; ten plan od kontraktu, tożsamości, tablicy
  „Now” i kanału. Operating model (P1) jest w obu na początku.
- **Stan fabryki:** plan programu mówi o tf 20.1.0 i o T4/T6 czekających na gałęzi; na `main` fabryki 22.2.0 oba są
  (`eval_gate.py`, `models_approved`).
- **DI Quality:** w planie programu go nie ma; tutaj jest pytaniem nr 7.
- **Stan kopii kontraktu, tożsamości i połączenia DI Release z DI Release Control** nie jest w planie programu
  opisany; §1 tego dokumentu go dopisuje.
