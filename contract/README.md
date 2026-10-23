# Kontrakt pdi

Schematy i zasady wspólne dla pdi, tf, ci_for_sdlc i ShipScope ([decyzja D1](../docs/decyzje.md)).
Wersjonowany wg SemVer 2.0.0 w [`contract.json`](contract.json); zmiana niezgodna wstecz podnosi wersję główną
(w 0.x — drugą liczbę). Odbiorca zdarzeń przypina wersję przez pole `contract_version`.

Wersja: `0.3.0`. Historia: 0.3.0 — zgłoszenie, artefakt zmiany, cięcie, zdarzenia, wspólny wzorzec klucza;
0.2.0 — pole `project` w decyzji; 0.1.0 — schemat decyzji.

| Plik | Obiekt | Gdzie żyje | Przykład |
|---|---|---|---|
| [`decision.schema.json`](decision.schema.json) | decyzja `DEC` (pola: [dokument 14 §4.1](../docs/14-pdi-standalone.md#41-schemat-decyzji-contractdecisionschemajson)) | rejestr pdi; nagłówki wpisów w `changes/CHG-n/decisions.md` | [`examples/decision.json`](examples/decision.json) |
| [`problem.schema.json`](problem.schema.json) | zgłoszenie `PRB`: kto nie może czego → skutek, stan triażu | baza pdi | [`examples/problem.json`](examples/problem.json) |
| [`change.schema.json`](change.schema.json) | nagłówek YAML artefaktu w `docs/project/changes/CHG-n/` (nagłówek tf + `change`, `source`, `tasks`) | repo zmiany | [`examples/change.json`](examples/change.json) |
| [`task.schema.json`](task.schema.json) | cięcie `TSK` z rodzicem `CHG` | `plan.md` zmiany | [`examples/task.json`](examples/task.json) |
| [`event.schema.json`](event.schema.json) | koperta zdarzenia i treść dla każdego typu | wymiana między projektami | `examples/event-*.json` |

Walidacja w Pythonie: `from pdi import contract; contract.errors("problem", obj)` (pusta lista = poprawny).

## Identyfikatory ([D3](../docs/decyzje.md))

- Kształt klucza jak w Jirze: `^[A-Z][A-Z0-9]+-[0-9]+$` (`contract.json` → `key_pattern`). ShipScope wyciąga takie
  klucze z commitów bez zmiany parsera.
- Domyślne prefiksy: `PRB`, `CHG`, `TSK`, `DEC` (`contract.json` → `prefixes`), konfigurowalne per organizacja.
- **Ograniczenie:** schematy sprawdzają kształt klucza, nie prefiks (bo prefiks jest konfigurowalny). To, że w polu
  `change` stoi klucz zmiany, a nie zgłoszenia, sprawdza kod, który zna konfigurację organizacji.
- Numeracja globalna; zera wiodące tylko w nazwach plików (`DEC-0001` = `DEC-1`).

## Stany zgłoszenia i mapowanie na tf

Stany pdi według **rekomendacji R7** ([dokument 13](../docs/13-rola-pdi-w-sdlc.md#4-rozbieżności-między-wersjami-mapy-i-planem--do-rozstrzygnięcia))
— **do zatwierdzenia przez właściciela**; zmiana decyzji zmienia tylko listę stanów.

| Stan pdi | Wymaga | Stan tf `proc-issue-triage` |
|---|---|---|
| `new` | — | `needs-triage` |
| `clarifying` | — | `needs-info` |
| `ready_for_triage` | — | `needs-triage` (po wzbogaceniu) |
| `accepted` | `change` (utworzona zmiana) | `ready-for-agent` albo `ready-for-human` |
| `rejected` | `rejection_reason` z listy (+ `rejection_note`) | `wontfix` |
| `parked` | `return_when` (próg powrotu) | brak odpowiednika — w tf `needs-triage` z etykietą `deferred` |
| `duplicate` | `duplicate_of` | `wontfix` (z linkiem do oryginału) |

Powody odrzucenia: `out_of_strategy`, `works_as_designed`, `cost_disproportionate`, `already_exists`,
`out_of_scope_recorded` (wpis w `.out-of-scope/` tf), `other`.

## Zdarzenia

| Typ | Wysyła | Treść (wymagane) |
|---|---|---|
| `problem.accepted` | pdi | `problem`, `change`, `decision` |
| `gate.requested` | tf, ci_for_sdlc | `change`, `gate`, `summary` |
| `gate.decided` | pdi | `change`, `gate`, `outcome` (`approved` / `changes_requested` / `rejected`), `decision` |
| `readiness.changed` | ci_for_sdlc | `change`, `readiness` (`ready` / `not_ready` / `drift`) |
| `feature.released` | ShipScope | `change`, `released_at` |
| `metric.breached` | tf (pasma kontrolne) | `metric`, `value`, `threshold` |
| `decision.basis_invalidated` | pdi | `decision`, `assumption`, `signal`, `attention_level` (0–3) — propozycja z [dokumentu 12 §4.2](../docs/12-zmiana-kierunku-sdlc.md#42-nowe-zdarzenie-w-kontrakcie), używane od F5 |

Każde zdarzenie: `id` (do deduplikacji), `type`, `occurred_at` (UTC, `RRRR-MM-DDTGG:MM:SSZ`), `source`,
`contract_version`, `payload`.

## Artefakt zmiany

Nagłówek pozostaje „prostym YAML” jak w tf `core-project-record` (`klucz: wartość`, `klucz: [a, b]`), bez obiektów
zagnieżdżonych. Szczegóły cięć są w treści `plan.md`; w nagłówku tylko lista `tasks`.
