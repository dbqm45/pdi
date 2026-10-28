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
