# Plan kroku F5 — powiadomienia zgłaszającego (pdi)

Stan: 2026-10-26. Krok z planu jednego flow (`docs/plan-jeden-flow-sdlc.md` §6, F5: „pdi: powiadomienia”; rola pdi
w etapie 15: „powiadamia zgłaszającego”). Decyzje właściciela z 2026-10-26: **mały rejestr PRB** teraz (pełny intake
zgłoszeń zostaje w F3) i **podpisany webhook** jako kanał (odbiorca — workflow Slacka, przekaźnik e-mail, automatyzacja
Jiry — sam wybiera, jak dostarczyć wiadomość).

## Rejestr zgłoszeń
- `problems/PRB-n.yaml` w katalogu rejestru, zgodne z `contract/problem.schema.json` (sprawdzane przy każdym zapisie).
  `ProblemStore.record()` nadaje `id` (kolejny `PRB-n`, prefiks z `contract.json`), `reported_at` (dziś) i
  `status: new`; resztę (kind, title, who, cannot, impact, reporter, channel, …) podaje szkic.
- `triage(id, outcome, decyzja, change=…, …)`: `outcome` = `accepted` / `rejected` / `parked` / `duplicate`.
  Zapisuje decyzję `kind: triage` z `links.prb` (i `links.chg`, gdy podano zmianę) i tagami `problem:<wynik>`,
  ustawia w zgłoszeniu `status`, `triage_decision` i — zależnie od wyniku — `change`, `rejection_reason`/`rejection_note`,
  `return_when`, `duplicate_of` (wymagane: `change` przy accepted, `duplicate_of` przy duplicate).
- Narzędzia MCP: `record_problem`, `list_problems`, `get_problem`, `triage_problem`,
  `retry_problem_notifications`.

## Powiadomienia
- Kiedy: po triażu (`accepted`/`rejected`/`parked`/`duplicate`), po `feature.released` zmiany, z której wyszło
  zgłoszenie (`problem.change`, każda linia), po zamknięciu oceny skutku tej zmiany (wynik).
- Co: `POST $PDI_NOTIFY_URL` z ciałem `{id, type: "problem.notification", occurred_at, source: "pdi", problem, title,
  reporter, channel, what, message, change?, decision?, release?, outcome?}` (`message` — zdanie po polsku), podpis jak
  w pozostałych kierunkach: `X-PDI-Timestamp`, `X-PDI-Event: problem.notification`,
  `X-PDI-Signature: v1=HMAC-SHA256(PDI_NOTIFY_SIGNING_SECRET, "<ts>.<body>")`; https (http tylko localhost).
- ID powiadomienia jest stałe (`notify-<PRB>-<co>[-<linia>]`): wysłane drugi raz nie idzie. Wynik
  (`sent`/`skipped`/`failed` z powodem, bez sekretu) w `notifications/<PRB>.yaml`; błąd nie cofa triażu ani zdarzenia;
  `retry_problem_notifications` ponawia nieudane i pominięte.
- To nie jest zdarzenie kontraktu 0.4.0 (kontrakt nie ma odbiorcy „zgłaszający”), więc nie trafia do `outbox/`.

## Elementy
`src/pdi/problems.py` (rejestr, triaż, powiadomienia), `src/pdi/notify.py` (wspólna podpisana wysyłka,
`ReporterNotifyConfig`, `notify_reporter()`), `src/pdi/inbox.py` (`feature.released` i ocena skutku powiadamiają),
`src/pdi/mcp_server.py` (narzędzia), README.

## Testy (najpierw czerwone)
`tests/test_problems.py`: zapis (id, data, status, zgodność ze schematem, zły szkic), triaż każdego wyniku (decyzja,
pola zgłoszenia, wymagane pola), powiadomienie po triażu (podpis, treść), bez adresu → `skipped`, błąd → `failed` i
ponowienie, brak dubli; `tests/test_inbox.py`: wydanie i ocena skutku zmiany powiadamiają zgłaszającego;
`tests/test_notify.py`: dotychczasowe bez zmian po wydzieleniu wspólnej wysyłki; `tests/test_mcp_server.py`: narzędzia.

## Wynik (2026-10-26)
- `tests/test_problems.py` czerwony przed kodem, potem cały `pytest` 500/500, `ruff check`, `ruff format --check`,
  `mypy` (strict) czyste; `tests/test_notify.py` bez zmian po wydzieleniu wspólnej wysyłki (`_send()`).
- Poza zakresem (F3): intake zgłoszeń z kanałów (formularz, Slack), łączenie duplikatów, wzbogacanie, PR z
  `intent.md` po przyjęciu.
