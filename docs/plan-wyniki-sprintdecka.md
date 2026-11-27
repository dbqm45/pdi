# Wyniki pokoju sprintdecka z powrotem do agendy pdi — plan

Stan: 2026-11-27, zrobione i sprawdzone na żywo. Właściciel zlecił zrobić to według rekomendacji: głosy i notatki z pokoju trafiają przy sprawie na
agendę „Discuss with team” jako materiał do decyzji. Poprzedni krok: [`plan-pokoj-sprintdeck.md`](plan-pokoj-sprintdeck.md)
(pokój z agendy, decyzja 4: „powrót wyników ze sprintdecka do pdi — osobno”).

## Co jest dziś (sprawdzone 2026-11-27)

- Link z pdi zakłada w sprintdecku pokój z jednym zadaniem na sprawę, ale zadanie nie wie, z której sprawy pochodzi.
- Po sesji sprintdeck ma dla każdego zadania: ostateczną ocenę (`final_estimate`, w talii „Risk”: Low…Very high),
  liczbę rund, głosy ostatniej odkrytej rundy, stan zgody z Consensus Engine (`summarize()`) i notatki z zatwierdzenia;
  eksport tylko jako Markdown i CSV.
- Konsola pdi jest lokalna (`127.0.0.1`) i bez JavaScriptu, a zmiany przyjmuje tylko z własnej strony (nagłówek
  Origin): sprintdeck nie może jej wywołać ani wysłać formularza z innej domeny.

## Decyzje (według rekomendacji)

1. **Zadanie pamięta sprawę z pdi:** w sprintdecku kolumna `items.external_ref` (migracja), ustawiana przez
   prowadzącego funkcją `set_item_ref` przy zakładaniu pokoju z linku; link z pdi niesie `ref` = identyfikator pozycji
   skrzynki. Pokoje zakładane ręcznie nie mają powiązań.
2. **Powrót przez przeglądarkę, jak w drugą stronę:** w podsumowaniu pokoju prowadzący klika „Send results to DI
   Decision”. Serwer sprintdecka sam czyta stan pokoju tokenem tej osoby (tylko prowadzący), buduje wyniki tylko dla
   zadań z `external_ref` i podpisuje je HMAC-SHA256 tym samym wspólnym sekretem (`PDI_SPRINTDECK_SECRET`); treści z
   przeglądarki nie podpisuje. Przeglądarka przechodzi na `<pdi>/discuss/results?d=…&s=…`.
3. **pdi pokazuje i dopiero potem zapisuje:** strona `/discuss/results` sprawdza podpis i termin (godzina) i pokazuje,
   co przyjdzie i do których spraw; przycisk „Attach to the agenda” (formularz z tej samej strony, rola `editor` albo
   `admin`) zapisuje wyniki w `sprintdeck-results/<pozycja>.json`. Sprawy już zamknięte albo nieznane są pomijane i
   wymienione.
4. **Co widać na agendzie:** przy karcie sprawy blok „From the sprintdeck room”: ocena końcowa, głosy (ile osób na
   którą kartę, bez nazwisk), stan zgody, liczba rund, notatki i link do pokoju. Narzędzie MCP `discussion_agenda` daje
   to samo w polu `room`. Wyniki to materiał: decyzję i jej uzasadnienie dalej wpisuje człowiek.
5. **Bez zmiany kontraktu** (API pdi ↔ sprintdeck) i bez nowej zależności. Adres pdi w sprintdecku:
   `NEXT_PUBLIC_PDI_URL`.

## Kroki

1. sprintdeck: migracja `external_ref` + `set_item_ref` / `get_item_refs` (pgTAP), `ref` w linku z pdi,
   `/api/pdi-results` i przycisk w podsumowaniu, testy Vitest, README. PR.
2. pdi: `ref` w linku, `/discuss/results` (podgląd, zapis), blok na karcie, MCP, testy, README, instrukcja. PR.
3. Na żywo: pokój z agendy, głosowanie, ocena końcowa z notatką, wyniki z powrotem na agendzie.

## Co wyszło przy wdrożeniu (2026-11-27)

- **Dwa PR:** dbqm45/sprintdeck#16 (migracja `external_ref`, `/api/pdi-results`, przycisk) i pdi (ten krok).
- **Migracja bez zmiany istniejących funkcji:** zamiast nowego parametru `add_item` i przepisywania `get_room_state`
  sprintdeck ma dwie małe funkcje: `set_item_ref` (tylko prowadzący, raz) i `get_item_refs` (członkowie pokoju).
- **Query string, nie fragment:** konsola pdi nie ma JavaScriptu, więc wyniki przychodzą w zapytaniu
  `/discuss/results?d=…&s=…`. Konsola loguje tylko ścieżkę; zapis dopiero formularzem z tej samej strony, bo zmiany z
  innej domeny konsola odrzuca (Origin).
- **Tylko z logowaniem przez suitę:** w trybie z tokenem w adresie link ze sprintdecka nie może nieść tokenu konsoli.
- **Na żywo** (lokalny Keycloak 26.4.7, Supabase CLI 2.122.0, sprintdeck z #16, konsola pdi, Playwright; `ola.test` z
  rolą `sprintdeck:member` na czas próby): pokój z agendy dostał zadania z `ref` `evt-1` i `evt-2`; jedna runda, ocena
  „High” z notatką; „Send results to DI Decision” → podgląd w pdi z obiema sprawami → „Attach to the agenda” → na
  agendzie „From the sprintdeck room (Risk, 1 round · open the room): Final: High · votes High × 1 · …” przy CHG-1 i
  „Not finished (pending)” przy CHG-2.
