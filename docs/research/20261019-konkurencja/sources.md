# Źródła i metoda — analiza konkurencji

- **Data odniesienia:** 2026-10-19. Okno: brak (fakty o stanie produktów), preferowane źródła z lat 2025–2026.
- **Pytanie:** czy istniejące narzędzia pokrywają scenariusze S1–S6 z [planu, Etap 2.2](../../08-plan-projektu.md#etap-2-walidacja-koncepcji-i-przewagi), i co z tego wynika dla wyboru: produkt komercyjny czy narzędzie wewnętrzne.
- **Procedura:** skill `core-source-research` (tryb głębokiego badania) z repozytorium `dbqm45/claude-team-factory`: 5 kątów równolegle (PM/discovery, wymagania/traceability, decision intelligence + założenia, ogólni asystenci AI, kąt przeciwny: popyt i krytyka), dowody zapisane przed raportem, kluczowe twierdzenia sprawdzane drugim wyszukiwaniem.
- **Wykonawcy:** 5 agentów badawczych + 6 wyszukiwań weryfikacyjnych (ProdPad, Cloverpop, Dovetail, Productboard Spark, Zeda.io, wyszukiwanie przeciwne „czy istnieje narzędzie wykrywające sprzeczność wymagań z badaniami”).

## Źródła niedostępne

Polityka sieci środowiska odrzuca połączenia do stron dostawców (`CONNECT tunnel failed, response 403`, `getaddrinfo ENOTFOUND`). W efekcie:

- **żadna strona nie została otwarta**, także dokumentacja dostawców i abstrakty Gartnera;
- wszystkie „cytaty” to omówienia z podsumowań wyszukiwarki;
- niezbadane lub zbadane powierzchownie: Coda, Cycle, Enterpret, Pendo, Amplitude (po przejęciu Kraftful — niepotwierdzonym), Chisel, Strategyzer, oficjalna dokumentacja Atlassian / Linear / Anthropic, pełne raporty „state of product management” (Productboard, Pendo, Atlassian, Mind the Product).

## Jak domknąć luki

1. Otworzyć strony źródłowe z tabeli dowodów w przeglądarce (lub dopuścić hosty w ustawieniach sieci środowiska) i zmienić werdykty C → P / S.
2. Test praktyczny (najważniejszy): przykład `examples/status-zamowienia.yaml` w formie dokumentów (opis inicjatywy, notatka z supportu, wynik badań, PRD z kryterium „panel się wyświetla”) przepuścić przez: ogólny LLM z dobrym promptem, ProdPad CoPilot (trial), Productboard Spark (trial), Notion / Rovo agent. Sprawdzić, czy wykrywają R2, R5 i R7 i czy po dodaniu nowego dowodu reagują bez ponownego pytania.
