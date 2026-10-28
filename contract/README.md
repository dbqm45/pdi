# Kontrakt pdi

Schematy i zasady wspólne dla pdi, tf, ci_for_sdlc i ShipScope ([decyzja D1](../docs/decyzje.md)).
Wersjonowany wg SemVer 2.0.0 w [`contract.json`](contract.json); zmiana niezgodna wstecz podnosi wersję główną
(w 0.x — drugą liczbę). Odbiorca zdarzeń przypina wersję przez pole `contract_version`.

Wersja: `0.10.0`. Historia: 0.10.0 — `source.kind: meeting` w decyzji (decyzje z transkrypcji spotkań, A5);
0.9.0 — format tabeli ramek w `design.md` (etap 07 Design, F6): konwencje, schemat
odczytanej tabeli, parser referencyjny `pdi.design`; 0.8.0 — eksport rekonstrukcji z kodu (format tf → ci_for_sdlc, F2) i wydania kontraktu
jako tagi `contract-v<wersja>`; 0.7.0 — zdarzenie `decision.recorded` (decyzja podjęta w aplikacji nadawcy do zapisu
w rejestrze pdi, A2b, decyzja D-A2) i `source.kind: ci_for_sdlc` w decyzji; 0.6.0 — rekomendacja triażu zgłoszenia (schemat przeniesiony z tf, F3);
0.5.0 — poziomy autonomii (polityka, pola decyzji, zdarzenia skrzynki i postępu pracy
agenta; DA1, DA2), `source_reported_at` w nagłówku zmiany (lead time od zgłoszenia w ShipScope); 0.4.0 — historyjka z kryteriami (G2), plan wydania (G1), nowe pola cięcia,
`release` w `feature.released`, zdarzenie `release.stage_changed`, zestaw wzorcowy kształtu historyjki, konwencje;
0.3.0 — zgłoszenie, artefakt zmiany, cięcie, zdarzenia, wspólny wzorzec klucza;
0.2.0 — pole `project` w decyzji; 0.1.0 — schemat decyzji.

| Plik | Obiekt | Gdzie żyje | Przykład |
|---|---|---|---|
| [`decision.schema.json`](decision.schema.json) | decyzja `DEC` (pola: [dokument 14 §4.1](../docs/14-pdi-standalone.md#41-schemat-decyzji-contractdecisionschemajson)) | rejestr pdi; nagłówki wpisów w `changes/CHG-n/decisions.md` | [`examples/decision.json`](examples/decision.json) |
| [`problem.schema.json`](problem.schema.json) | zgłoszenie `PRB`: kto nie może czego → skutek, stan triażu | baza pdi | [`examples/problem.json`](examples/problem.json) |
| [`change.schema.json`](change.schema.json) | nagłówek YAML artefaktu w `docs/project/changes/CHG-n/` (nagłówek tf + `change`, `source`, od 0.5.0 opcjonalnie `source_reported_at`, `tasks`) | repo zmiany | [`examples/change.json`](examples/change.json) |
| [`task.schema.json`](task.schema.json) | cięcie `TSK` z rodzicem `CHG` | `plan.md` zmiany | [`examples/task.json`](examples/task.json) |
| [`event.schema.json`](event.schema.json) | koperta zdarzenia i treść dla każdego typu | wymiana między projektami | `examples/event-*.json` |
| [`story.schema.json`](story.schema.json) | historyjka `US-n` (albo klucz z Jiry) ze scenariuszami `AC-n` w formacie `gwt`, `ears` albo `free` | eksport z tf, konektor repo ci_for_sdlc | [`examples/story.json`](examples/story.json) |
| [`release-plan.schema.json`](release-plan.schema.json) | plan wydania zmiany: MVP z miarą, linie `R1…Rn` z cięciami, flagi z etapami udostępniania | `changes/CHG-n/release.yaml` | [`examples/release-plan.json`](examples/release-plan.json) |
| [`autonomy.schema.json`](autonomy.schema.json) | polityka autonomii organizacji: typ decyzji → poziom 0–3, okno weta, warunek, progi obniżenia i podniesienia | konfiguracja organizacji (zmiana polityki to decyzja człowieka) | [`examples/autonomy.json`](examples/autonomy.json) |
| [`triage-recommendation.schema.json`](triage-recommendation.schema.json) | rekomendacja triażu `PRB`: stan pdi z polami, których wymaga, i stan tf z tabeli mapowania; decyzję podejmuje człowiek w pdi | wyjście triażu tf (`triage_pdi.py recommend`) dla pdi | [`examples/triage-recommendation.json`](examples/triage-recommendation.json) |
| [`reconstruction.schema.json`](reconstruction.schema.json) | eksport rekonstrukcji z kodu: reguły, wymagania i słownik z dowodami `plik:linia` (format `tf-reconstruction`, wersja 1) | `docs/project/00-reconstruction/reconstruction.json` w repo produktu; pisze tf (`recon_export.py`), czyta ci_for_sdlc (konektor rekonstrukcji) | [`examples/reconstruction.json`](examples/reconstruction.json) |
| [`design-links.schema.json`](design-links.schema.json) | tabela ramek z `design.md`: wymaganie → ścieżka → stan → ramka Figmy (`file_key`, `node_id`); `missing` i `not_applicable` z uwagą | `docs/project/changes/CHG-n/design.md`; pisze tf (faza design), czyta ci_for_sdlc (konektor repo) | [`examples/design.md`](examples/design.md) → [`examples/design-links.json`](examples/design-links.json) |
| [`fixtures/story-shape/`](fixtures/story-shape/README.md) | zestaw wzorcowy reguł STORY i AC: historyjki, oczekiwane wyniki, wspólne słownictwo | testy tf i ci_for_sdlc | — |

Walidacja w Pythonie: `from pdi import contract; contract.errors("problem", obj)` (pusta lista = poprawny);
nazwy: `decision`, `problem`, `change`, `task`, `event`, `story`, `release_plan`, `autonomy`,
`triage_recommendation`, `reconstruction`, `design_links`. Tabela z `design.md`: `from pdi.design import
parse_design_md`.

Zgodność wstecz: 0.9.0 dodaje nowy schemat i konwencję; 0.8.0 dodaje tylko nowy schemat; 0.7.0 dodaje tylko nowy typ zdarzenia i wartość `source.kind`; 0.6.0 dodaje tylko nowy schemat; wszystkie pola dodane w 0.5.0 są opcjonalne, a zdarzenia
z `contract_version` 0.4.0–0.6.0 dalej przechodzą walidację. Zestaw wzorcowy `fixtures/story-shape/` ma wersję 0.4.0 — tę, w której zmienił się ostatnio.

## Wydania i kopie u konsumentów (od 0.8.0)

- **Jedno źródło:** schematy edytuje się tylko tu. Po wejściu zmiany `contract/` na `main` workflow
  `contract-release.yml` zakłada tag `contract-v<wersja>` (wersja z `contract.json`). Tag jest niezmienny — nowa treść
  wymaga nowej wersji.
- **Konsumenci** (tf, ci_for_sdlc) trzymają kopie potrzebnych plików przypięte do wersji, bo działają bez dostępu do
  pdi (skrypty tf u użytkownika, serwer ci_for_sdlc). Kopie są **generowane** skryptem synchronizacji z tagu i nigdy
  nie edytowane ręcznie; CI konsumenta sprawdza, że są bajt w bajt równe plikom z tagu.
- Aktualizacja u konsumenta: zmiana wersji w pliku przypięcia, uruchomienie synchronizacji, testy, PR.

## Poziomy autonomii (0.5.0, decyzje [DA1 i DA2](../docs/decyzje.md))

| Poziom | Nazwa | Co się dzieje |
|---|---|---|
| 3 | człowiek | decyzja czeka w skrzynce; bez kliknięcia nic się nie dzieje |
| 2 | automat z wetem | automat przygotowuje decyzję i wykona ją po oknie weta; człowiek może zatrzymać |
| 1 | automat z logiem | automat wykonuje od razu; wpis w rejestrze i w osi zdarzeń |
| 0 | automat po cichu | tylko czynności bez skutków dla produktu |

- **Każdy typ startuje na poziomie 3.** Obniżenie: co najmniej 95% szkiców zatwierdzonych bez zmian w ostatnich
  30 decyzjach typu (`contract.json` → `autonomy.lower_when`), zawsze jako decyzja człowieka. Powrót wyżej, gdy odsetek
  poprawek przekroczy 10% (`raise_when`). Polityka organizacji może nadpisać progi per typ.
- **Typy chronione** (`triage`, `scope.r1`, `release.go`, `outcome.assessment`, `review.sensitive`, `migration`)
  mają w `autonomy.schema.json` wymuszony poziom 3.
- **Decyzja** dostaje: `decision_type` (klucz z kropkami; katalog znanych typów w `contract.json` → `autonomy.decision_types`,
  organizacja może dodać własne), `automation` (tylko decyzje automatu: poziom 0–2, `rule`, `veto_until` — wymagane
  na poziomie 2, `vetoed_by`), `draft_edited` (czy człowiek zmienił szkic AI; wymaga `drafted_by: ai`) i źródło
  `console`. Odsetek akceptacji liczy się z `drafted_by: ai` i `draft_edited`.

## Konwencje (0.4.0) — wartości domyślne do czasu decyzji DG1–DG7

`contract.json` → `conventions` (plan G1/G2 §2; decyzje jeszcze nieprzyjęte, zmiana decyzji zmienia tylko wartości):

| Konwencja | Domyślnie | Decyzja |
|---|---|---|
| Format kryteriów akceptacji | `gwt`; dozwolone `ears` i `free` | DG1 |
| Słowa kluczowe | EN: Given/When/Then/And/But; PL: Zakładając (że), Mając / Gdy, Kiedy, Jeżeli, Jeśli / Wtedy / Oraz, I / Ale — `fixtures/story-shape/vocabulary.json` | DG2 |
| Linia wydania w Jirze | etykieta z prefiksem `release:` (np. `release:R1`); konfigurowalne: etykieta, fixVersion, pole | DG4 |
| Plan wydania w repo | osobny plik `changes/CHG-n/release.yaml` | DG6 |

Schemat planu wydania sprawdza strukturę. Spójność (`mvp.release` wśród linii, zbiór TSK zgodny z `plan.md`, flaga
z etapami i `remove_by`) sprawdzają tf (`check`) i ci_for_sdlc (REL-001…008).

### Projekt zmiany: tabela ramek w `design.md` (0.9.0, `conventions.design`)

Pierwsza tabela z nagłówkiem `Wymaganie | Ścieżka | Stan | Ramka | Uwagi` (albo `Requirement | Journey | State |
Frame | Notes`). Stan z `conventions.design.states` (te same co `UiState` w ci_for_sdlc). Ramka: link do figma.com
z `node-id` (ramka, nie cały plik), `brak` / `missing` albo `nie dotyczy` / `n/a` — przy dwóch ostatnich uwaga
z powodem lub pytaniem jest wymagana. Odczytana postać: `design-links.schema.json`. Wzorzec dla parserów tf
i ci_for_sdlc: `examples/design.md` daje dokładnie `examples/design-links.json` (sprawdza to też `pdi.design`).
Domyślnie projektant robi ramki, a agent je dopasowuje; szkic ramek przez agenta tylko na żądanie (D-F1).

## Identyfikatory ([D3](../docs/decyzje.md))

- Kształt klucza jak w Jirze: `^[A-Z][A-Z0-9]+-[0-9]+$` (`contract.json` → `key_pattern`). ShipScope wyciąga takie
  klucze z commitów bez zmiany parsera.
- Domyślne prefiksy: `PRB`, `CHG`, `TSK`, `DEC` (`contract.json` → `prefixes`), konfigurowalne per organizacja.
- **Ograniczenie:** schematy sprawdzają kształt klucza, nie prefiks (bo prefiks jest konfigurowalny). To, że w polu
  `change` stoi klucz zmiany, a nie zgłoszenia, sprawdza kod, który zna konfigurację organizacji.
- Numeracja globalna; zera wiodące tylko w nazwach plików (`DEC-0001` = `DEC-1`).

## Stany zgłoszenia i mapowanie na tf

Stany biznesowe pdi — **R7, przyjęte 2026-10-23** ([decyzje](../docs/decyzje.md)). pdi jest źródłem prawdy o stanie
zgłoszenia. tf zostaje przy swoich stanach (etykiety zgłoszeń na GitHubie); **tłumaczenie tylko na granicy, według tej
tabeli**: gdy tf wykonuje triaż dla pdi (F3), jego rekomendacja jest wyrażona stanem pdi z kontraktu. `parked`
i `duplicate` tf tylko rekomenduje; decyzję i pilnowanie progu powrotu przejmuje pdi.

| Stan pdi | Wymaga | Stan tf `proc-issue-triage` |
|---|---|---|
| `new` | — | `needs-triage` |
| `clarifying` | — | `needs-info` |
| `ready_for_triage` | — | `needs-triage` (po wzbogaceniu) |
| `accepted` | `change` (utworzona zmiana) | `ready-for-agent` albo `ready-for-human` |
| `rejected` | `rejection_reason` z listy (+ `rejection_note`) | `wontfix` |
| `parked` | `return_when` (próg powrotu) | brak odpowiednika — w tf `needs-triage` z etykietą `deferred` |
| `duplicate` | `duplicate_of` | `wontfix` (z linkiem do oryginału) |

Rekomendacja triażu (`triage-recommendation.schema.json`, od 0.6.0) ma ten sam stan i te same pola co zgłoszenie
(test pilnuje list): `clarifying` z pytaniami, `accepted` z briefem i wykonawcą (`agent` → `ready-for-agent`,
`human` → `ready-for-human`; bez `change` — zmianę tworzy pdi po decyzji), `rejected` z powodem
(`out_of_scope_recorded` także z plikiem `.out-of-scope/*.md`), `parked` z progiem powrotu, `duplicate`
z oryginałem. `tf_state` musi zgadzać się z tabelą wyżej.

Powody odrzucenia: `out_of_strategy`, `works_as_designed`, `cost_disproportionate`, `already_exists`,
`out_of_scope_recorded` (wpis w `.out-of-scope/` tf), `other`.

## Zdarzenia

| Typ | Wysyła | Treść (wymagane) |
|---|---|---|
| `problem.accepted` | pdi | `problem`, `change`, `decision` |
| `gate.requested` | tf, ci_for_sdlc | `change`, `gate`, `summary` |
| `gate.decided` | pdi | `change`, `gate`, `outcome` (`approved` / `changes_requested` / `rejected`), `decision` |
| `readiness.changed` | ci_for_sdlc | `change`, `readiness` (`ready` / `not_ready` / `drift`) |
| `feature.released` | ShipScope | `change`, `released_at` (od 0.4.0 opcjonalnie `release`: R1 wydane = MVP u ludzi) |
| `metric.breached` | tf (pasma kontrolne) | `metric`, `value`, `threshold` |
| `release.stage_changed` | ShipScope | `change`, `flag`, `to_stage` (opcjonalnie `release`, `from_stage`, `rollout` 0–100) — od 0.4.0 |
| `decision.proposed` | pdi, ci_for_sdlc, tf | `decision_type`, `level` (0–3), `summary`; na poziomie 2 także `veto_until` — od 0.5.0 |
| `decision.auto_applied` | pdi | `decision`, `decision_type`, `level` (0–2) — od 0.5.0 |
| `decision.vetoed` | pdi | `decision_type`, `vetoed_by` — od 0.5.0 |
| `decision.recorded` | ci_for_sdlc | `decision_type`, `ref`, `statement`, `decided_by`, `drafted_by`; opcjonalnie `draft_edited` (człowiek) albo `automation` (automat, nigdy oba), `evidence` (cytaty), `supersedes`, `url`, `change`, `problem`. Decyzja już podjęta u nadawcy; pdi zapisuje ją w rejestrze i odpowiada numerem `DEC` — od 0.7.0 |
| `run.progress` | tf | `phase`, `status` (`started` / `in_progress` / `waiting_gate` / `done` / `failed`); opcjonalnie `cost_usd`, `budget_usd` — od 0.5.0 |
| `decision.basis_invalidated` | pdi | `decision`, `assumption`, `signal`, `attention_level` (0–3) — przyjęte 2026-10-23 ([dokument 12 §4.2](../docs/12-zmiana-kierunku-sdlc.md#42-nowe-zdarzenie-w-kontrakcie)), używane od F5 |

Każde zdarzenie: `id` (do deduplikacji), `type`, `occurred_at` (UTC, `RRRR-MM-DDTGG:MM:SSZ`), `source`,
`contract_version`, `payload`.

## Artefakt zmiany

Nagłówek pozostaje „prostym YAML” jak w tf `core-project-record` (`klucz: wartość`, `klucz: [a, b]`), bez obiektów
zagnieżdżonych. Szczegóły cięć są w treści `plan.md`; w nagłówku tylko lista `tasks`.
