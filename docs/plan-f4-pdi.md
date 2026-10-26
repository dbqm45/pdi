# Plan F4 — strona pdi (orkiestracja: maszyna stanów per CHG i skrzynka bramek)

Stan: 2026-10-26. Decyzje właściciela z 2026-10-26: **pdi zostaje w Pythonie** (rozbudowa rejestru w plikach i
serwera MCP; usługa z DA4 dopiero, gdy flow działa od początku do końca, zgodnie z „orkiestrator najpierw jako CLI”
z dokumentu 13) i **najpierw tylko pdi**: części F4 w tf (uruchamianie person bez interakcji, szablon
`sdlc-phase.yml`) i w ci_for_sdlc (pytania i zatwierdzenia przez pdi) idą osobnymi PR-ami po tym kroku. Krok buduje
na skrzynce z G1.5 ([plan](plan-g15-pdi.md)).

## Cel

Po decyzji człowieka na bramce następna faza startuje sama. pdi wie, na jakim etapie jest każda zmiana, co na nią
czeka i co zostało uruchomione.

## Przebieg zmiany (bramki w kolejności planu jednego flow, §2)

| Bramka | Kto prosi (`gate.requested`) | Po `approved` uruchamia fazę | Po `changes_requested` uruchamia ponownie |
|---|---|---|---|
| `B1` intencja i zakres | tf | `requirements` | `intent` |
| `B2` wymagania | tf | `architecture` | `requirements` |
| `B3` architektura i plan cięć | tf | `design` | `architecture` |
| `design-review` | tf | — (czeka na gotowość z ci_for_sdlc) | `design` |
| `approve-for-implementation` | ci_for_sdlc (`readiness.changed: ready` albo `gate.requested`) | `delivery` (Talos) | — (spec poprawia się w repo) |
| `B4` gotowość do wydania | tf | — | — |
| `B5` autoryzacja PROD | tf | — (dalej ShipScope) | — |

`B6` i bramki spoza listy (np. etap flagi z G1.5) są przyjmowane, ale nie przesuwają przebiegu. Merge zostaje
w GitHubie, włączenie flagi w ShipScope. `rejected` kończy zmianę (`status: rejected`).

Kolejności się nie wymusza: prośba o bramkę, przed którą poprzednie nie są zatwierdzone, trafia do skrzynki z
dopiskiem „poza kolejnością: brak B2” (tak jak w ShipScope spójność jest pokazywana, nie naprawiana). Nowa prośba o
tę samą bramkę zamyka starszą otwartą pozycję jako `superseded`.

## Elementy

1. **`src/pdi/flow.py`** (czyste reguły, bez plików): `GATES`, stan zmiany i przejścia —
   `gate_requested()`, `gate_decided()` (zwraca też fazę do uruchomienia), `readiness_changed()`,
   `feature_released()`, `impact_reviewed()`. Każde przejście dopisuje wpis do `history`.
2. **`src/pdi/changes.py`**: stan zmiany w `changes/<CHG>.yaml` w katalogu rejestru (obok `decisions/` i `inbox/`,
   ten sam commit co pozycja skrzynki). To stan orkiestracji, nie artefakt zmiany: intencja, plan i decyzje o
   zmianie dalej żyją w repo produktu (D2/R1).
3. **Skrzynka (`inbox.py`)** przyjmuje też:
   - `gate.requested` z tf i ci_for_sdlc → pozycja `gate` z nazwą bramki, artefaktem, linkiem i pytaniami;
   - `readiness.changed` z ci_for_sdlc: `ready` → pozycja `approve-for-implementation`; `not_ready` i `drift` →
     tylko wpis w stanie zmiany (przy `drift` po zatwierdzeniu: dopisek w stanie, że baseline się rozjechał);
   - `feature.released` (każda linia) → wpis w stanie; `R1` dalej otwiera ocenę skutku.
   Decyzja na bramce (`decide_inbox_item`) zapisuje decyzję `kind: gate`, przesuwa stan, zapisuje zdarzenie
   `gate.decided` (sprawdzone schematem kontraktu) w `outbox/<id>.json` i uruchamia fazę. Zamknięta ocena skutku
   kończy zmianę (`status: done`); bramki etapów flag dalszych linii (R2…) dalej przyjmują decyzje.
4. **`src/pdi/dispatch.py`**: `workflow_dispatch` szablonu fazy tf przez API GitHuba — repo, workflow i gałąź z
   `PDI_DISPATCH_REPO`, `PDI_DISPATCH_WORKFLOW` (domyślnie `sdlc-phase.yml`), `PDI_DISPATCH_REF` (domyślnie `main`),
   token z `PDI_GITHUB_TOKEN`, budżet fazy z `PDI_PHASE_BUDGET_USD` (D6). Wejścia (wszystkie tekstowe): `change`,
   `phase`, `gate`, `outcome`, `decision`, `rework`, `budget_usd`. Bez `PDI_DISPATCH_REPO` uruchomienie jest
   `skipped`; błąd GitHuba zapisuje się w stanie zmiany (`dispatch.status: failed`) i nie cofa decyzji;
   `retry_dispatch` ponawia. Token nigdy nie trafia do stanu, logu ani odpowiedzi.
5. **Odbiornik**: obok `/events/shipscope` (nagłówki `X-ShipScope-*`) ścieżki `/events/tf` i `/events/ci_for_sdlc`
   z nagłówkami `X-PDI-Timestamp`, `X-PDI-Event`, `X-PDI-Signature` (ten sam schemat podpisu v1 HMAC-SHA256),
   sekrety `PDI_TF_SIGNING_SECRET` i `PDI_CI_FOR_SDLC_SIGNING_SECRET`. Ścieżka bez ustawionego sekretu odpowiada 404;
   `source` zdarzenia musi zgadzać się ze ścieżką.
6. **MCP**: `list_changes(status)`, `get_change(change)`, `retry_dispatch(change)`; `list_inbox` i
   `decide_inbox_item` obsługują nowe bramki.
7. **Dokumentacja**: README (zmienne, ścieżki), stan F4 w planie jednego flow.

## Poza zakresem (następne PR-y)

- **tf:** `tf run <persona> --change CHG-n --phase …` i `core/workflows/sdlc-phase.yml` z wejściami jak wyżej;
  wysyłanie `gate.requested` na `/events/tf`; zapis decyzji z `gate.decided` do `changes/CHG-n/decisions.md` (D2/R1).
- **ci_for_sdlc:** wysyłanie `readiness.changed` i `gate.requested` na `/events/ci_for_sdlc`, `/api/decisions`
  z ID z pdi, `POST /api/items/:key/approve` wywoływane po `gate.decided`.
- **pdi:** polityka uwagi (dokument 05: poziomy 0–3, budżet, deduplikacja sygnałów), usługa z DA4, konsola.

## Testy (najpierw czerwone)

`tests/test_flow.py` (czyste przejścia: kolejność bramek, dopisek „poza kolejnością”, odrzucenie, ponowna praca,
gotowość, wydanie, ocena skutku), `tests/test_changes.py` i rozszerzone `tests/test_inbox.py` (pozycje z tf i
ci_for_sdlc, `superseded`, `gate.decided` w `outbox/` zgodne z kontraktem, stan po decyzji, commit),
`tests/test_dispatch.py` (żądanie do GitHuba z podstawionym klientem, `skipped`, `failed`, ponowienie, brak tokenu
w stanie), `tests/test_receiver.py` (nowe ścieżki, zły nagłówek źródła, ścieżka bez sekretu), `tests/test_mcp_server.py`.

## Dopisek 2026-10-26: wysyłka do ci_for_sdlc
Decyzja właściciela: decyzja z bramki dociera do ci_for_sdlc webhookiem z pdi. `src/pdi/notify.py`
(`notify_ci_for_sdlc()`, `PDI_CI_FOR_SDLC_URL`, `PDI_CI_FOR_SDLC_SIGNING_SECRET`): po decyzji na bramce
`approve-for-implementation` zdarzenie `gate.decided` z `outbox/` idzie na `/api/webhooks/pdi` ci_for_sdlc
(dbqm45/ci_for_sdlc#66); wynik w stanie zmiany (`ci_for_sdlc`), ponowienie przez `retry_dispatch`. Sprawdzone razem
z ci_for_sdlc na dwóch lokalnych serwerach: `readiness.changed: ready` → bramka w skrzynce → decyzja DEC-0001 →
historyjki zmiany zatwierdzone w ci_for_sdlc z numerem DEC-0001.
