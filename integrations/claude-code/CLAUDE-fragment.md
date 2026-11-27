<!-- Fragment do ~/.claude/CLAUDE.md albo CLAUDE.md projektu: odczyt decyzji w trakcie pracy (dokument 14 §4.5). -->
## Decyzje (pdi)
- Zanim zaproponujesz rozwiązanie w obszarze, który mógł być już rozstrzygnięty, sprawdź `find_decisions` (pdi) —
  najpierw z filtrem `project` = nazwa bieżącego repo, potem bez filtra.
  Gdy propozycja przeczy wcześniejszej decyzji, powiedz to wprost, podaj jej ID i zaproponuj zastąpienie
  (`present_decision_draft` z `supersedes`) zamiast cichej zmiany kursu.
- Decyzje zapisujesz tylko na prośbę człowieka (`/record-decision`): szkic (`present_decision_draft`), zatwierdzenie
  przez człowieka w konsoli pdi, dopiero potem `record_decision`.
