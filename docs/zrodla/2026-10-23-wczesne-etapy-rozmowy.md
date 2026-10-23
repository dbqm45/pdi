# Wczesne etapy rozmowy o flow SDLC — notatki źródłowe (2026-10-23)

Etapy rozmowy **wcześniejsze** niż [mapa procesu](2026-10-23-mapa-sdlc.md) i [plan jednego flow](../plan-jeden-flow-sdlc.md): wizja greenfield (etap 2 w [kontekście rozmowy](../kontekst-rozmowy.md)) i moduł „Report a problem” dla brownfieldu (etap 3). Zapisane jako źródło dla [dokumentu 13](../13-rola-pdi-w-sdlc.md). Schemat ID z tego etapu (`INT-7 → SPEC-7 → TASK-7.3`, dopisek `Task:`) został później zastąpiony przez `PRB → CHG → TSK` z dopiskiem `Change:`.

---

## Część A — wizja greenfield: repo zamiast Jiry, PR jako bramka

### Główna zasada

Nie budować jednej dużej aplikacji, która robi wszystko. Zbudować **orkiestrator nad łańcuchem artefaktów w gicie**. Kod piszą sesje Claude Code uruchamiane bez interakcji (Agent SDK albo `claude -p`), a człowiek zatwierdza każdy etap przez zwykły **Pull Request**.

- **Źródłem prawdy jest repo, nie Jira.** Każdy etap kończy się plikiem markdown z frontmatterem, zacommitowanym w repo.
- **Bramka to PR.** Agent otwiera PR z artefaktem, człowiek klika Approve. Audit trail, historia i powiadomienia za darmo, bez własnego UI na start.
- **Każdy artefakt ma stałe ID**: `INT-7 → SPEC-7 → TASK-7.3 → PR → deploy`; commity niosą dopisek `Task: TASK-7.3` — zastępuje to ShipScope wyciąganie kluczy Jiry.
- **Jira:** przy greenfieldzie niepotrzebna (tablica = widok na `tasks/*.md`), najwyżej jednokierunkowy eksport; przy brownfieldzie jedno ze źródeł wejściowych (jak dziś w ci_for_sdlc).

### Proces

```
 POMYSŁ ──► 1 Grill/brainstorm ──► intent.md            [CZŁOWIEK: akceptuje intencję]
            2 Shape ──► spec.md (cele, non-goals, metryki, ryzyka, model domeny)
            3 Architektura ──► ADR-y, stack, threat model   [CZŁOWIEK: spec + stack]
            4 Design system ──► tokeny + komponenty (Figma ↔ kod)
            5 Ekrany ──► ramki Figma per user journey      [CZŁOWIEK: review designu]
            6 Dekompozycja ──► milestones/*.md, tasks/*.md
   SILNIK SPÓJNOŚCI (ci_for_sdlc) — przy KAŻDEJ zmianie artefaktu:
   intent ↔ spec ↔ ekrany ↔ taski ↔ kod ↔ produkcja; luki/konflikty → pytania → decisions/*.md [CZŁOWIEK, async]
            7 Szkielet: repo, lintery, CI, CLAUDE.md, hooki (z factory), pierwszy pusty deploy
            8 Build per task: plan mode → plan.md → kod w worktree, równolegle
            9 Weryfikacja: testy, screenshoty vs Figma, AI review     [CZŁOWIEK: merge, stopniowo według ryzyka]
           10 Release: CI/CD, flagi, release notes z łańcucha, status ShipScope   [CZŁOWIEK: autoryzacja PROD]
           11 Operate: progi deterministyczne → diagnoza Claude → nowy intent.md (pętla)
```

### Gdzie człowiek

Zasada: **człowiek decyduje, co budujemy i czy to ma sens; agent decyduje, jak; deterministyczne checki sprawdzają wynik.** Człowiek tam, gdzie decyzja jest nieodwracalna albo wymaga oceny wartości: akceptacja intencji; spec + stack; review designu; odpowiedzi na pytania silnika spójności; merge (na start każdy, później automatycznie dla niskiego ryzyka — pełne pokrycie testami, bez auth, płatności i migracji); wydanie na PROD; incydent powyżej progu. 5–7 punktów dotyku na feature. W UI jedna **skrzynka bramek**: „czeka na Ciebie: 2 akceptacje, 3 pytania, 1 wydanie”.

### Projekty

| Komponent | Skąd |
|---|---|
| Orkiestrator + aplikacja (czat z pomysłem, skrzynka bramek, graf śladu) | **pdi** — „nazwa pasuje do roli powłoki” |
| Silnik spójności | ci_for_sdlc (+ markdown w repo, OpenAPI, kod) |
| Skills / hooki / agenci w generowanym repo | claude-team-factory (później: tf) |
| Status release i release notes | ShipScope (`Task:` z commitów, notatki z łańcucha) |

### Uwagi

1. Stack z ograniczonej listy (2–3 „golden paths” z szablonami i evalami).
2. Figma: źródłem prawdy w projektowaniu, po zbudowaniu — kod (Storybook); silnik spójności pilnuje rozjazdu.
3. Evale całego pipeline'u: 20–50 przykładowych pomysłów przy każdej zmianie skills, promptów, hooków.
4. Koszty: limity per feature i etap; analiza tylko zmian.

### Kolejność

1. Schemat artefaktów i struktura repo, ID, dopisek w commitach.
2. **Orkiestrator jako CLI, bramki jako PR-y, bez własnego UI**; jeden mały pomysł przez cały proces.
3. ci_for_sdlc jako check CI na PR-ach z artefaktami.
4. ShipScope na dopiskach i z notatkami z łańcucha.
5. **Aplikacja pdi dopiero, gdy proces działa end-to-end.**
6. Pętla Operate → intent, automatyczny merge według ryzyka.

---

## Część B — „Report a problem” (brownfield)

Moduł w pdi z **dwiema bramkami**: tania („czy warto analizować?”) i droga („czy budujemy?”).

### 1. Zgłoszenie: problem, nie rozwiązanie

Forma **[kto] nie może [co] → [jaki skutek]**. Zawiera: kto ma problem, czego nie może, jak radzi sobie dziś, jak często, ile to kosztuje. Zgłoszenie z rozwiązaniem („dodajcie przycisk bulk update”) agent przeformułowuje na problem, krótka runda grill-me: 3–5 pytań. Sito lekkie dla zgłaszającego.

Kanały: formularz, Slack/Teams, support, post-mortemy, pętla Operate (agent sam zakłada zgłoszenie po przekroczeniu progu). Wszystko jako `PRB-123`.

### 2. Wzbogacenie (agent, tylko odczyt, przed triażem)

- duplikaty grupowane — pięć podobnych to jedno zgłoszenie z pięcioma dowodami; liczba zgłaszających to sygnał,
- kod i dokumentacja: czy coś już istnieje, czy ADR lub decyzja to wyklucza (ci_for_sdlc: „Confluence mówi, że to świadomie poza zakresem”),
- dowody: incydenty, logi, dane, skala,
- otwarte pytania i hipotezy.

Przykłady (ilustracja):

| Zgłoszenie | Co agent dopisuje |
|---|---|
| Control Tower: brak operacji na wielu ładowarkach naraz | czy istnieje operacja per ładowarka; czego dotyczy „bulk” (konfiguracja, restart, firmware); typowa partia; częściowa porażka (retry, raport, rollback); przepustowość; planowanie |
| Network team: uptime jako czas dostępności dla kierowców | online vs złącze `Available` vs udana sesja; wyłączenia (serwis, sieć energetyczna, zajęte); historia statusów; czy definicję narzuca regulacja (AFIR, NEVI) — do weryfikacji, nie rozstrzygnięcia |

### 3. Bramka 1: triaż (tania decyzja)

PO lub mały zespół dostaje zgłoszenie z **rekomendacją i uzasadnieniem** agenta. Agent rekomenduje, nie decyduje.

`New → Clarifying → Ready for triage →` **Accepted for analysis** / **Rejected** (powód obowiązkowy z listy: poza strategią / działa jak zaprojektowano / koszt nieproporcjonalny / …) / **Parked** (wraca, gdy przybędzie dowodów, np. 3 nowe zgłoszenia albo incydent) / **Duplicate of PRB-x**.

Odrzucenie zawsze wraca do zgłaszającego z powodem — inaczej ludzie przestaną zgłaszać.

### 4. Analiza → Bramka 2: decyzja o budowie

Agent robi discovery i szkic `intent.md`: 2–3 warianty (np. dla uptime: definicja i raport / dashboard / alerty), zgrubny koszt i ryzyka, dotknięte komponenty, otwarte decyzje. Po akceptacji człowieka — dalej proces z części A.

### 5. Przechowywanie

- **Zgłoszenia w bazie pdi, nie w gicie** — dużo, zaszumione, większość odrzucona; historia odrzuconych cenna dla duplikatów i zasady „wróć, gdy przybędzie dowodów”.
- **Do repo trafia dopiero zaakceptowany `intent.md`** z `Source: PRB-123`.

### 6. Domknięcie pętli

ShipScope powiadamia zgłaszającego, gdy funkcja jest **wydana**, nie tylko wdrożona za flagą: „PRB-123 rozwiązany, na PROD od v2.4”. Buduje zaufanie do procesu bardziej niż cokolwiek innego.

### Ludzie w tym fragmencie

Trzy punkty, wszystkie decyzyjne: zgłaszający odpowiada na pytania; triaż; akceptacja szkicu intencji. Resztę robi agent.
