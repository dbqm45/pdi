# Notatka z decyzji — panel statusu zamówienia (zakres zawężony)

**Data:** 2026-10-27 · **Decydujący:** PM Zamówienia i Dostawa, Head of Product · **Obecni:** Tech Lead Zamówienia, UX

## Kontekst

Analiza z sierpnia pokazała, że większość zgłoszeń o status wynikała z opóźnionych zdarzeń od przewoźnika Y (obecnie ok. 35% naszych paczek). Zespół integracji naprawił webhooki przewoźnika Y we wrześniu — mediana opóźnienia zdarzeń spadła z 31 h do 1,5 h. Udział kontaktów o status spadł z 38% do 27%.

## Decyzja

Kontynuujemy panel w zawężonym zakresie:
- czytelne nazwy statusów (zgodnie z rekomendacją badań),
- przewidywana data dostawy liczona z SLA przewoźnika (X: D+1, Y: D+2),
- oś czasu: przyjęte, w kompletacji, nadane, w doręczeniu, doręczone,
- znacznik „ostatnia aktualizacja”.

## Uzasadnienie

Panel ma sens, bo dane o zdarzeniach od przewoźników są teraz aktualne. Bez tego panel pokazywałby nieaktualne informacje, co w sierpniu było główną przyczyną kontaktów.

Metryka rezultatu: udział kontaktów o status z 27% do 20% w 8 tygodni po wdrożeniu.
