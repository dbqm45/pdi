# INT-233: Migracja integracji z przewoźnikiem Y na API v3

**Typ:** Zadanie techniczne · **Zespół:** Integracje · **Utworzono:** 2026-11-18 · **Priorytet:** Wysoki

## Opis

Przewoźnik Y wygasza API v2 z dniem 2026-12-15. API v3 różni się od v2:

- brak webhooków — zdarzenia pobieramy zapytaniami (polling),
- w planie Standard limit zapytań pozwala odświeżać zdarzenia przesyłek co ok. 12 h; plan Premium (odświeżanie co 15 min) wymaga renegocjacji umowy (szacunek: +0,30 zł za paczkę),
- w v3 dostępne są tylko zdarzenia „nadane” i „doręczone” (bez „w doręczeniu” i bez awizacji).

## Plan

Migracja na v3 w planie Standard do 2026-12-12. Mapowanie zdarzeń v3 na statusy OMS — w toku.

## Kryteria akceptacji

- Zdarzenia „nadane” i „doręczone” zapisywane w OMS dla 100% przesyłek Y.
- Brak błędów integracji przez 7 dni po przełączeniu.
