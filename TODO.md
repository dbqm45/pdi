# Do zrobienia

Rzeczy odłożone na później, z tym, co już ustalono. Kroki planów i ich stan: [plan jednego flow](docs/plan-jeden-flow-sdlc.md)
§8 („Co zostało”), [plan automatyzacji i konsoli](docs/plan-automatyzacja-i-konsola.md) §8.

## Instalacja tf w pdi (odłożona 2026-10-28)

Krok F0 planu jednego flow („tf w ShipScope i pdi … jeden sposób pracy agentów wszędzie”). Wstrzymane do decyzji
właściciela; nic nie jest zainstalowane.

**Co da:** te same zasady i zabezpieczenia pracy agentów w każdej sesji w pdi (także w chmurze), jak w ci_for_sdlc:
- `CLAUDE.md` z zasadami projektu (TDD, fakty po sprawdzeniu, plan przed kodem, SemVer, sekrety tylko w zmiennych
  środowiskowych, dziennik w `docs/project/`);
- hooki działające niezależnie od modelu: blokada niebezpiecznych poleceń powłoki (część wymaga zgody), ochrona plików
  z sekretami i konfiguracji zabezpieczeń, skan sekretów po każdym zapisie, strażnik TDD (kod produkcyjny dopiero po
  czerwonym teście), ostrzeżenie o długim kontekście, wykrycie stosu na starcie, dziennik zużycia tokenów;
- skille (rdzeń i pack-it: Python, pytest, testy, bezpieczeństwo, dokumentacja; pack-editorial-pl) i agenci do
  tańszej delegacji (`scout`, `quick-fixer`, `security-reviewer`).

**Czego nie zmienia:** kodu i bezpieczeństwa działającego pdi (odbiornik, podpisy, tokeny, rejestr) ani bramek
(`uv run pytest`, ruff, mypy). Workflow CI z tf nie ruszy, dopóki GitHub Actions nie działa (płatności).

**Ustalone:**
- Rekomendacja: instalacja zespołowa (pliki w repo), bo praca idzie w sesjach w chmurze; prywatna działałaby tylko
  na komputerze właściciela.
- Próba na sucho (tf 5.50.0, 2026-10-28): `--shared --packs pack-it --language pl --commit-language pl` → 956 nowych
  plików (głównie markdown skilli), scalenie `.gitignore` (13 wpisów), bez zmian w istniejących plikach pdi.
- Koszt: jednorazowo duży PR; sesje w pdi stają się bardziej rygorystyczne (TDD wymuszone, część poleceń git pyta
  o zgodę); aktualizacje tf (`python3 factory/update.py`) to od czasu do czasu PR z nowymi wersjami skilli.

**Jak zrobić, gdy zapadnie decyzja** (w klonie pdi, `$TEAM_FACTORY` = klon tf):
```bash
python3 "$TEAM_FACTORY/core/factory/install.py" --dry-run --yes --shared --packs pack-it --language pl --commit-language pl
python3 "$TEAM_FACTORY/core/factory/install.py" --yes --shared --packs pack-it --language pl --commit-language pl
uv run pytest && uv run ruff check src tests && uv run mypy src   # bramki pdi bez zmian
```
Potem przejrzeć wygenerowany `CLAUDE.md` (dopisać komendy pdi: `uv run pytest`, ruff, mypy, Python 3.11 i 3.13)
i otworzyć PR. Przy okazji: aktualizacja starszej instalacji w `ci_for_sdlc/.claude` (ten sam punkt planu).

## Decyzje przypięte do kodu: `applies_to` (zapisane 2026-10-29)

Źródło: artykuł „Teaching AI Agents to Remember: ADRs, Specs, Engineering Decisions” (A. Kokane, 2026-10-19).
Przypadek z niego: dwa PR-y, każdy poprawny, razem odwracają przyjętą decyzję, bo drugi agent jej nie znał.

**Co już jest w kontrakcie** (`contract/decision.schema.json`): uzasadnienie i opcje, `assumptions[]` z
`load_bearing` i `invalidated_if` („kiedy rozważyć ponownie”), `review_by`, `status: superseded` z `supersedes` /
`superseded_by`, `links` do PRB, CHG, TSK i PR. Brakuje jednego: **nic nie łączy decyzji z plikami**, więc ani agent,
ani bramka nie wiedzą, że zmiana rusza obszar objęty decyzją.

**Do zrobienia** (TDD, wersja kontraktu wg SemVer; tag `contract-v…` po merge'u):
- [ ] **Pole `applies_to` w decyzji** — wzorce ścieżek (`services/document-processing/**`) i/lub nazwy komponentów;
  opcjonalne, więc zgodne wstecz (podbicie minor kontraktu). Przykład w `contract/examples/`, README kontraktu.
- [ ] **Zapytanie „decyzje dla tych ścieżek”** w MCP (`find_decisions` z parametrem ścieżek albo osobne narzędzie):
  przyjęte decyzje, których `applies_to` pasuje do podanych plików, z `why` i założeniami. Agent woła je przed planem
  zmiany i podaje w podsumowaniu, które decyzje sprawdził.
- [ ] **`applies_to` przy zapisie decyzji** — `record_decision` przyjmuje pole; tf `decision add` je przekazuje (pozycja
  w tf przy następnej zmianie `mode-pdi`).
- [ ] **Szablon PR „Wpływ na decyzje”** (`.github/pull_request_template.md`): których decyzji dotyczy, czy zmienia
  przyjętą (nie / tak / nie wiem), uzasadnienie. Ten sam szablon w ci_for_sdlc i tf.

**Odbiorca:** ci_for_sdlc — reguła na PR, gdy zmienione pliki trafiają w `applies_to` przyjętej decyzji (pozycja w
`ci_for_sdlc/TODO.md`). Czego nie robić: osobnego `INDEX.md` decyzji w repo — rejestr pdi jest katalogiem, druga kopia
by się rozjeżdżała.
