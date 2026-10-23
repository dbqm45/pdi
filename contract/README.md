# Kontrakt pdi

Schematy i zasady wspólne dla pdi, tf, ci_for_sdlc i ShipScope ([decyzja D1](../docs/decyzje.md)).
Wersjonowany wg SemVer 2.0.0; zmiana niezgodna wstecz podnosi wersję główną.

Wersja: `0.1.0`.

| Plik | Zawartość | Stan |
|---|---|---|
| `decision.schema.json` | decyzja (pola: [dokument 14 §4.1](../docs/14-pdi-standalone.md#41-schemat-decyzji-contractdecisionschemajson)) | **0.1.0** — `recorded_at` dodane do pól z §4.1 (znacznik zapisu, nadaje rejestr); `kind` ma też `other` |
| `problem.schema.json` | zgłoszenie `PRB` | później (F0) |
| `change.schema.json` | zmiana `CHG`, zadanie `TSK` | później (F0) |
| `event.schema.json` | zdarzenia (`gate.requested`, `feature.released`, …) | później (F0) |

Rejestr decyzji jest podzielony ([D2/R1](../docs/decyzje.md)): ten sam schemat opisuje wpisy w pdi
i nagłówki wpisów w `changes/CHG-n/decisions.md` w repo zmian.
