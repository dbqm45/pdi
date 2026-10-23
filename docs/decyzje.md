# Decyzje właściciela projektu

Rejestr decyzji podjętych przez właściciela pdi. Do czasu zbudowania rejestru z [dokumentu 14](14-pdi-standalone.md)
prowadzony ręcznie; po zbudowaniu — pierwsze wpisy do przeniesienia.

| ID | Data | Decyzja | Uzasadnienie | Źródło rekomendacji |
|---|---|---|---|---|
| D1 | 2026-10-23 | Kontrakt (schematy i zasady ID wspólne dla pdi, tf, ci_for_sdlc i ShipScope) żyje w `pdi/contract/`, z numerem wersji (SemVer). Osobne repo dopiero, gdy pojawi się czwarty konsument. | najmniej infrastruktury; jeden właściciel | [plan, §9](plan-jeden-flow-sdlc.md#9-decyzje-do-podjęcia) |
| D2 / R1 | 2026-10-23 | **Podział rejestru decyzji według życia decyzji:** decyzje niezwiązane z konkretną zmianą (triaż, odrzucenia, decyzje zapisane w trybie standalone) mają źródło prawdy w pdi; decyzje o zmianie (B1–B6, odpowiedzi na pytania ci_for_sdlc) — w repo, w `changes/CHG-n/decisions.md`; pdi je indeksuje (odczyt z repo), nie kopiuje. Zastępuje pierwotną rekomendację D2 („pdi jedynym właścicielem”). | decyzje o zmianie mają audyt w gicie i są dostępne dla agentów; zgłoszenia i odrzucenia nie trafiają do repo | [dokument 13, R1](13-rola-pdi-w-sdlc.md#4-rozbieżności-między-wersjami-mapy-i-planem--do-rozstrzygnięcia) |
| D-S1 | 2026-10-23 | Rejestr decyzji trybu standalone w **osobnym prywatnym repo** (np. `pdi-decisions`), nie w repo pdi. Tworzone, gdy serwer MCP i `/record-decision` przejdą testy — przed startem walidacji na sobie. | treść decyzji może być poufna; kod pdi i dane rozdzielone | [dokument 14 §4.2](14-pdi-standalone.md#42-przechowywanie) |
| D-S2 | 2026-10-23 | Serwer MCP pdi w **Pythonie** (oficjalne SDK MCP). | bardziej uniwersalny (decyzja właściciela) | [dokument 14 §4.3](14-pdi-standalone.md#43-serwer-mcp-pdi-lokalny-stdio) |
| D-S3 | 2026-10-23 | Pola schematu decyzji zgodnie z dokumentem 14 §4.1. | wymagane tylko pola podstawowe; reszta opcjonalna | [dokument 14 §4.1](14-pdi-standalone.md#41-schemat-decyzji-contractdecisionschemajson) |

Otwarte: D3 (format ID; związane z R2 — globalne `DEC-n`), D4–D7, R7. Decyzje blokujące krok 1 dokumentu 14 — podjęte.
