# Plan kroku G1.5 — strona pdi (odbiór zdarzeń ShipScope)

Stan: 2026-10-26. Strona ShipScope jest gotowa (dbqm45/evdt-service-shipscope#109): worker wysyła podpisane
`release.stage_changed` i `feature.released` na adresy dodane w Settings → General. Ten krok odbiera je w pdi.

## Zakres (decyzja właściciela z 2026-10-26: „cienka skrzynka”)

Plan G1/G2 (§5.7) zakłada skrzynkę bramek z F4. Pełnej maszyny stanów per CHG jeszcze nie ma, więc krok buduje
najmniejszą skrzynkę dla dwóch zdarzeń ShipScope. F4 może potem dobudować na niej maszynę stanów i inne źródła
(`gate.requested` z tf i ci_for_sdlc).

| Zdarzenie | Pozycja w skrzynce | Zamknięcie |
|---|---|---|
| `release.stage_changed` | `kind: gate` — „CHG-12 R1: flaga payment-retry na etapie 10% (10%), przejść dalej?” | decyzja `kind: gate` z `links.chg` i wynikiem `approved` / `changes_requested` / `rejected` |
| `feature.released` z `release: R1` | `kind: impact_review` — „CHG-12: MVP (R1) u ludzi, ocena skutku” | decyzja `kind: product` z `links.chg` (zwykle z `success_metric` i `review_by`) |
| `feature.released` z inną linią albo bez `release` | brak (przyjęte, pominięte) | — |

## Elementy

1. **`src/pdi/inbox.py`** (czyste reguły + pliki):
   - `verify_signature(secret, timestamp, body, signature, now, tolerance=300)`: `v1=` + hex HMAC-SHA256 z
     `"<timestamp>.<surowe body>"`, porównanie w stałym czasie (`hmac.compare_digest`), znacznik czasu najwyżej
     5 minut od teraz (w obie strony).
   - `Inbox(registry)`: pozycje w `inbox/<ID zdarzenia>.yaml` obok `decisions/` w katalogu rejestru (to samo repo
     git, ten sam commit). `receive(event)` sprawdza kopertę i treść schematem `contract/event.schema.json`, przyjmuje
     tylko `source: shipscope` i dwa typy wyżej; ponowione zdarzenie o tym samym `id` nie tworzy drugiej pozycji.
     `items(status)` listuje, `decide(item_id, draft, outcome)` zapisuje decyzję w rejestrze i zamyka pozycję
     (`status: decided`, `decision: DEC-n`); pozycji zamkniętej nie da się zamknąć drugi raz.
   - ID zdarzenia trafia do nazwy pliku tylko po sprawdzeniu wzorca `^[A-Za-z0-9._-]{1,128}$` (bez `..`).
2. **`src/pdi/receiver.py`** — odbiornik HTTP z biblioteki standardowej (`http.server`), komenda `pdi-receiver`:
   `POST /events/shipscope`, sekret z `PDI_SHIPSCOPE_SIGNING_SECRET`, rejestr z `PDI_REGISTRY_PATH`, adres
   `PDI_RECEIVER_HOST` (domyślnie `127.0.0.1`) i `PDI_RECEIVER_PORT` (domyślnie `8787`). Treść najwyżej 64 KB.
   Odpowiedzi: 202 nowa pozycja, 200 duplikat albo zdarzenie pominięte, 400 zły JSON lub schemat (bez treści
   zdarzenia w komunikacie), 401 zły lub stary podpis, 404 inna ścieżka, 413 za duża treść. ShipScope wysyła tylko
   na publiczne `https://`, więc przed odbiornikiem stoi proxy TLS albo tunel — opisane w README.
   Kod 2xx kończy ponowienia po stronie ShipScope; 4xx i 5xx ShipScope ponawia (do 10 razy).
3. **Serwer MCP** — dwa nowe narzędzia: `list_inbox(status="open")` i `decide_inbox_item(item_id, statement, why,
   source, drafted_by, outcome?, …pola decyzji)`. Rodzaj decyzji i `links.chg` nadaje skrzynka, nie model.
   Instrukcja serwera: decyzję w skrzynce zapisuje się tylko po zatwierdzeniu szkicu przez człowieka, jak każdą inną.
4. **Dokumentacja**: README (uruchomienie odbiornika), `contract/README.md` bez zmian (kontrakt się nie zmienia),
   status G1.5 w `docs/plan-g1-g2.md`.

## Poza zakresem

Maszyna stanów per CHG, `gate.decided` wysyłane dalej, `gate.requested` z tf i ci_for_sdlc, powiadomienia i budżet
uwagi (dokument 05), licznik oceny skutku — F4 i F5.

## Testy (najpierw czerwone)

`tests/test_inbox.py`: podpis (dobry, zły, stary, z przyszłości, brak `v1=`), przyjęcie obu typów z przykładów
kontraktu, deduplikacja, pominięcie `feature.released` bez R1, odrzucenie innego źródła i złego schematu, złe ID
zdarzenia, zamknięcie bramki decyzją `kind: gate` z `links.chg`, ponowne zamknięcie odrzucone, commit w repo git.
`tests/test_receiver.py`: prawdziwy serwer na losowym porcie, kody odpowiedzi jak wyżej.
`tests/test_mcp_server.py`: sześć narzędzi, `list_inbox` i `decide_inbox_item` przez serwer.
