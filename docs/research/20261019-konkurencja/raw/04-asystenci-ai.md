# Kąt 4: ogólni asystenci AI i platformy agentów (surowe ustalenia wykonawcy)

Stan na: 2026-10-19. Metoda wykonawcy: 7 wyszukiwań, **bez otwierania stron** — wszystko z podsumowań wyników wyszukiwania; cytaty niezweryfikowane ze źródłem. Traktować jako „według doniesień”.

| Narzędzie | Ustalenie | Źródło | Data | Ranga |
|---|---|---|---|---|
| Atlassian Rovo | Agenci przypisywalni do zadań, @wzmianki, osadzanie w workflow Jira; Rovo Studio (no-code) GA; brak dowodów na wbudowanego agenta przeglądu wymagań lub agenta proaktywnego | buzzclan.com/atlassian/atlassian-rovo/; crgsolutions.co/how-atlassian-rovo-is-rewriting-the-playbook-for-jira-confluence-teams-in-2026/; eesel.ai/blog/rovo-ai-actions | 2026, b.d. | wtórne (blogi) |
| Notion AI | Custom Agents uruchamiane „on a schedule or on triggers” | notion.com/releases/2025-09-18 | 2025-09-18 | pierwotne (dostawca) |
| Notion AI | Custom Agents GA 2026-05-04, ok. 10 USD / 1000 kredytów | slite.com/en/learn/how-to-use-notion-ai | 2026 | wtórne, jedno źródło |
| Glean | Agenci uruchamiani harmonogramem; polityki bezpieczeństwa dla agentów wyzwalanych automatycznie („flag for review”) | docs.glean.com/release-notes/releases/2026-05-06-may-release | 2026-05-06 | pierwotne |
| Glean | Eksperymentalne Triggers API — webhooki o zmianach treści w podłączonych źródłach | docs.glean.com/release-notes/releases/2026-08-18-august-release | 2026-08-18 | pierwotne |
| M365 Copilot | Zaplanowane prompty w Agent Builder, GA planowane na 09.2026, tylko per użytkownik; wg jednego mirrora wdrożenie wstrzymane | mc.merill.net/message/MC1302906 | 2026-07-31 | wtórne (mirror komunikatu MS) |
| M365 Copilot | Wyzwalacze zdarzeń w Copilot Studio GA od 06.2025 | m365admin.handsontek.net/?p=13734 | 2025 | wtórne |
| ChatPRD | Wklejenie PRD → informacja zwrotna; brak śledzenia założeń, sprzeczności między dokumentami, monitoringu | chatprd.ai/blog/whats-new-april-22-2024 | 2024-04-22 | pierwotne |
| ChatPRD | Ok. 15 USD/mies. (Pro) | banani.co/blog/chatprd-ai-review | b.d. | wtórne |
| Thinkr, review-prd (skill) | Statyczne przeglądy PRD według rubryki (11 przebiegów / PASS-WARN-FAIL), bez monitoringu | hunted.space/product/thinkr; skills.sh/generaljerel/chalk-skills/review-prd | b.d. | dostawca / społeczność |
| Linear | Linear Agent (asystent z kontekstem roadmapy, zgłoszeń i kodu); „Product Intelligence” w planie Business — bez szczegółów | releases.sh/…; pricingsaas.com/companies/linear/diffs/2025Q3 | 2025 | wtórne |
| ChatGPT | Zaplanowane zadania (Go/Plus/Pro/Business/Enterprise) | gigazine.net/gsc_news/en/20260619-chatgpt-scheduled-tasks/ | 2026-06-19 | wtórne |
| Gemini | Scheduled Actions | tomsguide.com/ai/google-gemini/… | 2025 | wtórne, status bieżący niezweryfikowany |

Nie zbadano: Coda; oficjalna dokumentacja Atlassian, Linear, Anthropic; NotebookLM (brak automatyzacji wg wyszukiwania).

Wnioski wykonawcy (oznaczone przez niego jako częściowo spekulacja):
1. Rozumowanie S1–S4 jest w dużej mierze zastępowalne przez dobry prompt w ogólnym LLM — ale bezstanowe (trzeba za każdym razem dostarczać kontekst).
2. Brak trwałego obiektu decyzji (fakty vs hipotezy, alternatywy, status założeń) w żadnym narzędziu — wniosek z braku dowodów.
3. S5 (monitoring) możliwy tylko DIY; infrastruktura (wyzwalacze, harmonogramy) szybko dojrzewa — przewaga „nikt nie monitoruje” zanika.
4. S6 (zarządzanie uwagą) to najwyraźniejsza luka — brak źródeł o progach istotności, deduplikacji, uczeniu na odrzuceniach.
5. Rekomendacja: test praktyczny — PRD z celowo wstawionym niezweryfikowanym założeniem i sprzecznym badaniem przepuszczony przez Rovo, Notion, Glean, ChatGPT/Claude.
