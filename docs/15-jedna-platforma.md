# Jedna platforma — pdi, tf, ci_for_sdlc i ShipScope jako jeden produkt

Data: 2026-10-27 · Status: **propozycja** (do decyzji właściciela: G6 i P1) · Makieta:
[`design/platforma/`](../design/platforma/README.md), podgląd: https://claude.ai/artifact/5hUnjQX6HN19gp41LLf5rV

Dziś człowiek pracuje w czterech aplikacjach: pdi, ci_for_sdlc, ShipScope i pliki z tf w repo. Każda ma własne
logowanie i własny widok, a widok produktowy ShipScope opiera się na Jirze (PI, sprinty, Epiki). Propozycja: **jeden
produkt dla ludzi**, w którym źródłem pracy jest proces (zgłoszenie → zmiana → cięcia → wydanie → skutek), a nie
Jira. Do tego katalog funkcjonalności z przełącznikami per środowisko i miejsce, w którym można opisać problem
i porozmawiać z Claude.

## 1. Co jest jednym produktem, a co nie

| Warstwa | Jedna? | Dlaczego |
|---|---|---|
| Nazwa, menu, UI, logowanie, obszar roboczy, cennik | **tak**, od razu | użytkownik nie ma widzieć czterech aplikacji |
| Backend pdi i warstwy pdi w ShipScope | stopniowo | najwięcej kodu integracji (tokeny usług, podpisane zdarzenia, potwierdzanie połączenia) jest właśnie między nimi |
| ShipScope (wdrożenia, flagi, drift) i ci_for_sdlc (spójność definicji) | osobne silniki, wspólny produkt | działają, są przetestowane i mają wartość same: ShipScope bez pdi, ci_for_sdlc z samą Jirą |
| tf | **zawsze osobno** | fabryka instalowana w repo klienta i uruchamiana w jego CI, z dostępem do jego kodu |

Rekomendacja: jedna powłoka (konsola pdi) czyta istniejące API (pdi, ci_for_sdlc, API usług ShipScope), a backend
łączy się moduł po module tam, gdzie integracja kosztuje więcej, niż daje. Kontrakt w `contract/` jest granicą
między modułami, więc łączenie nie wymaga przepisywania. Przeciw przepisaniu wszystkiego naraz: trzy różne stosy
(Node + Fastify + Postgres z RLS, monorepo TypeScript, Python), kilkaset testów, które musiałyby przejść od nowa,
i różne granice zaufania (worker ShipScope trzyma zaszyfrowane tokeny klientów, ci_for_sdlc czyta Confluence
i Figmę, tf ma kod).

## 2. Menu według pytań, nie według aplikacji

| Sekcja | Pytanie | Dane |
|---|---|---|
| **Now** (start) | Co czeka na mnie? | pdi: bramki, pytania z ci_for_sdlc, decyzje, oś zdarzeń; uwagi (rozjazd FE/BE, prognoza z wątpliwością) |
| **Problems** | Co zgłoszono i co z tym zrobiliśmy? | pdi: zgłoszenie „kto, czego nie może, jaki skutek”, pytania doprecyzowujące, duplikaty, wynik triażu |
| **Work** | Co jest w budowie i na jakim etapie? | pdi + tf: zmiany jako przebiegi przez fazy (zamiast tablicy jak w Jirze), prognoza G3 |
| **Product** | Co mają użytkownicy, gdzie, i czy mogę to wyłączyć? | **nowe:** domena → funkcjonalność → części w serwisach, stan per środowisko, przełączniki |
| **Releases** | Co jest wdrożone technicznie? | ShipScope: środowiska, historia wdrożeń, flagi techniczne, plan wydania |
| **Consistency** | Czy wiemy, co budujemy? | ci_for_sdlc: gotowość, pytania z decyzją (rozwiązanie, ryzyko, odrzucenie), pokrycie ścieżek ramkami Figmy, kryteria akceptacji ↔ testy (§5) |
| **Outcomes** | Czy to dało efekt i ile trwa? | pdi i ShipScope: ocena skutku, trafność prognoz, lead time |
| **Decisions**, **Autonomy** | Kto, co i dlaczego zdecydował? | pdi (ekrany w [makiecie konsoli](../design/konsola/README.md)) |

Rozmowa z Claude jest panelem na każdym ekranie (K-3 z planu automatyzacji). Product i Releases są osobno celowo:
PO pyta, co ma użytkownik, a dev i ops, co leży na środowisku. ShipScope ma ten podział już dziś (widok produktowy
i techniczny); w jednym produkcie widok produktowy traci Jirę jako źródło, a techniczny dzieli się na kilka ekranów.

### Prosty model: czyja kolej

Ekrany szczegółowe (makieta: 1–7) są dla specjalistów. Dla właściciela produktu każda zmiana przechodzi przez osiem
etapów nazwanych zwykłymi słowami, a ekran mówi przede wszystkim, czyja jest kolej i jaki jest jeden następny krok:

| # | Etap | Kto |
|---|---|---|
| 1 | Problem described | zgłaszający |
| 2 | Direction agreed | człowiek |
| 3 | AI plans | AI |
| 4 | You approve the plan | człowiek (decyzja) |
| 5 | AI builds | AI |
| 6 | You check and release | człowiek (decyzja) |
| 7 | On TEST · QA · PROD | automatycznie |
| 8 | With users | człowiek włącza przełącznik |

Cztery kolory stanu: **Your turn** (żółty: czeka na decyzję człowieka), **AI working** (granat w wersji prostej, indygo w Pro), **Waiting**
(szary: czeka na kogoś z zewnątrz) i **With users** (zielony). Decyzja na etapie 4 lub 6 to pytanie z opcjami
i skutkiem każdej z nich; „jeszcze nie wiem” jest opcją zapisywaną jako zaakceptowane ryzyko z terminem przeglądu.
AI nie zaczyna budować bez tej decyzji. Szczegóły (spójność, wdrożenia, przełączniki) są linkami „for specialists”.

Makieta ma dwie wersje tego modelu: prostą w kolorach ci_for_sdlc (0a–0c) i dopracowaną wizualnie „Pro” (0d–0f:
Overview, My changes, jedna zmiana z interaktywną decyzją).

## 3. Źródło: proces zamiast Jiry

Po połączeniu z pdi ShipScope już czyta zmiany i cięcia z repo, pokazuje przyrost „Changes (repo)” i plan wydania
z `release.yaml` (warstwa pdi, ShipScope #115–#118). Tryb Jira zostaje dla organizacji, które go potrzebują (D4).
Brakuje dwóch rzeczy:

1. **Funkcjonalność jako trwały byt.** Zmiana (CHG) kończy się po wydaniu; funkcjonalność („Edycja taryfy”) żyje
   dalej i kolejne zmiany ją rozwijają. Katalog: domena (z modelu domeny tf) → funkcjonalność → części w serwisach
   (FE, BE, worker) z ich flagami. Zmiana deklaruje funkcjonalność w nagłówku `intent.md` (np. `feature:
   tariff-edit`) — nowe pole kontraktu.
2. **Dwa rodzaje flag.** Flaga wydaniowa należy do zmiany i znika po pełnym wydaniu; przełącznik trwały steruje
   funkcjonalnością na stałe. Ekran Product pokazuje oba, ale przełącza głównie trwałe.

## 4. Przełącznik funkcjonalności

- Jeden przełącznik na funkcjonalność i środowisko zamiast osobnych flag w każdym serwisie.
- Przełącznik tworzy **plan przełączenia**: włączanie najpierw BE, potem FE; wyłączanie odwrotnie. Plan sprawdza,
  czy kod każdej części jest wdrożony na tym środowisku — jeśli nie, przełącznik jest nieaktywny i mówi dlaczego.
- TEST i QA: automat z logiem (poziom autonomii 1–2). PROD: pozycja w skrzynce pdi i decyzja człowieka (typ
  `flag.stage_advance`, poziom 3).
- Wykonanie zależy od tego, gdzie flaga żyje: flaga runtime — wykonawca dostawcy flag (pierwszy kandydat:
  evdt-shipscope-flags, który ma środowiska, serwisy, kolejność i dziennik); flaga w kodzie — PR do pliku flag przez
  tf (zmiana wchodzi z wdrożeniem).
- ShipScope potwierdza wynik z odczytu: ekran pokazuje to, co odczytano, nie to, co zlecono; rozjazd jest widoczny.
- To zmienia zasadę „ShipScope tylko obserwuje” (ShipScope ADR-001, DA6) — wymaga nowego ADR w ShipScope.

## 5. Spójność (ci_for_sdlc) w jednym produkcie

Sekcja Consistency ma dwa poziomy (makieta: ekrany 6 i 7):

- **Lista:** gotowość zmian i historyjek w ośmiu wymiarach ci_for_sdlc (wymagania, design, dokumentacja,
  architektura, ścieżki użytkownika, obsługa błędów, zależności, plan wydania), kolejka pytań do decyzji,
  odpowiedzi znalezione w źródłach (A2a: cytat słowo w słowo, akceptuj / popraw / odrzuć) i zaakceptowane ryzyka
  z terminem przeglądu.
- **Zmiana:** każde ustalenie (GAP, CONFLICT, AMBIGUITY, OUTDATED, MISSING_COVERAGE, DRIFT) z dowodami ze źródeł
  obok siebie — historyjka w Jirze, strona w Confluence, ramka w Figmie, kod z rekonstrukcji tf, wynik testu.
  Decyzja ma trzy skutki z ci_for_sdlc (`resolve`, `accept_risk`, `dismiss`): wybór jednej z opcji pytania,
  akceptacja ryzyka z powodem i terminem przeglądu albo odrzucenie z powodem; trafia do rejestru pdi jako DEC-n.
  Pod spodem macierz ścieżka użytkownika × stan interfejsu z ramkami z tabeli `design.md` (kontrakt 0.9.0)
  i karta kryteriów akceptacji ↔ testów (G4). Zmiana niegotowa może poprosić pdi o zatwierdzenie mimo to
  (`gate.requested` z blokadami, ci_for_sdlc #84).

## 6. Kolejność

1. Decyzja G6/P1 na piśmie: menu z §2, wspólna tożsamość i obszar roboczy, konsola pdi jako powłoka, stack usługi
   pdi (DA4).
2. ADR-004 w ShipScope: zapis stanu flag przez wykonawców, ShipScope jako dashboard i plan przełączenia.
3. Kontrakt: katalog funkcjonalności (`feature` w nagłówku zmiany, domena, części w serwisach).
4. Powłoka z ekranami tylko do odczytu na istniejących API (Now, Problems, Work, Product, Releases).
5. Plan przełączenia na sucho i decyzja w pdi; potem pierwszy wykonawca zapisu.
6. Łączenie backendu moduł po module, zaczynając od pdi i warstwy pdi w ShipScope.

## 7. Otwarte pytania

- Gdzie dziś żyją flagi w serwisach (evdt-shipscope-flags, inny dostawca, pliki w kodzie)? Od tego zależy pierwszy
  wykonawca.
- Czy evdt-shipscope-flags zostaje backendem flag pod platformą, czy platforma go zastępuje?
- Czy przełączenie na PROD zawsze idzie przez decyzję w pdi, czy wystarczą role i dziennik?
- Nazwa produktu (roboczo „Product Intelligence Suite”, `pis` w makiecie).
