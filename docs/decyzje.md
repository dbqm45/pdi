# Decyzje właściciela projektu

Rejestr decyzji podjętych przez właściciela pdi. Do czasu zbudowania rejestru z [dokumentu 14](14-pdi-standalone.md)
prowadzony ręcznie; po zbudowaniu — pierwsze wpisy do przeniesienia.

| ID | Data | Decyzja | Uzasadnienie | Źródło rekomendacji |
|---|---|---|---|---|
| D1 | 2026-10-23 | Kontrakt (schematy i zasady ID wspólne dla pdi, tf, ci_for_sdlc i ShipScope) żyje w `pdi/contract/`, z numerem wersji (SemVer). Osobne repo dopiero, gdy pojawi się czwarty konsument. | najmniej infrastruktury; jeden właściciel | [plan, §9](plan-jeden-flow-sdlc.md#9-decyzje-do-podjęcia) |
| D2 / R1 | 2026-10-23 | **Podział rejestru decyzji według życia decyzji:** decyzje niezwiązane z konkretną zmianą (triaż, odrzucenia, decyzje zapisane w trybie standalone) mają źródło prawdy w pdi; decyzje o zmianie (B1–B6, odpowiedzi na pytania ci_for_sdlc) — w repo, w `changes/CHG-n/decisions.md`; pdi je indeksuje (odczyt z repo), nie kopiuje. Zastępuje pierwotną rekomendację D2 („pdi jedynym właścicielem”). | decyzje o zmianie mają audyt w gicie i są dostępne dla agentów; zgłoszenia i odrzucenia nie trafiają do repo | [dokument 13, R1](13-rola-pdi-w-sdlc.md#4-rozbieżności-między-wersjami-mapy-i-planem--do-rozstrzygnięcia) |

Otwarte: D3 (format ID; związane z R2 — globalne `DEC-n`), D4–D7, R7, decyzje z [dokumentu 14 §9](14-pdi-standalone.md#9-decyzje-do-podjęcia-przed-budową).
