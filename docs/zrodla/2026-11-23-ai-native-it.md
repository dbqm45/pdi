# AI Native IT — opis kierunku transformacji (notatka źródłowa, 2026-11-23)

Tekst przekazany przez właściciela 2026-11-23 jako materiał do oceny, czego brakuje w Delivery Intelligence Suite.
Zapisany bez zmian treści (tylko formatowanie markdown: nagłówki, listy, tabele). Odnośniki do źródeł zewnętrznych
(McKinsey, Deloitte, BCG, IBM) były w oryginale linkami; adresów nie przepisano, a treści tych źródeł nie sprawdzano.

Wnioski dla suity i decyzja o zakresie: [plan budowy suity §3c](../plan-budowy-suity.md#3c-ai-native-it-czego-brakuje-w-suicie-dopisane-2026-11-23)
i decyzja DS1 w [`decyzje.md`](../decyzje.md).

---

Jeśli korporacja chce stać się AI Native, nie powinna zaczynać od zakupu licencji na Copilota czy ChatGPT dla pracowników. Powinna zmienić sposób, w jaki działa IT: jak buduje oprogramowanie, obsługuje użytkowników, zarządza infrastrukturą, podejmuje decyzje i rozwija kompetencje.

W IT celem jest przejście od organizacji, w której AI jest dodatkiem do pracy człowieka, do organizacji, w której procesy, zespoły, systemy i architektura są projektowane od początku z założeniem, że AI jest integralną częścią pracy.

## 1. Co oznacza AI Native dla korporacyjnego IT?

Od tradycyjnego IT → AI Native IT

Zmiana modelu operacyjnego, nie tylko technologii.

**Tradycyjne IT**

- Człowiek wykonuje większość zadań
- AI jest narzędziem pomocniczym
- Automatyzacja głównie regułowa
- Ticket jest jednostką pracy
- Wiedza rozproszona między ludźmi

**AI Native IT**

- AI wykonuje znaczną część pracy operacyjnej
- Człowiek definiuje, nadzoruje i podejmuje decyzje
- Agentic workflows i automatyzacja end-to-end
- Outcome jest jednostką pracy
- Wiedza dostępna dla AI i ludzi w systemach

Najważniejsza zmiana mentalna:

Nie pytamy „gdzie wdrożyć AI?”, tylko „dlaczego ten proces nadal wymaga tyle pracy człowieka i jak przeprojektować go z AI w centrum?”.

## 2. Gdzie szukać zmian w IT? – 8 kluczowych obszarów

Największy potencjał: operacje, software delivery, service management i knowledge management.

### ① IT Service Desk i End User Support

To jeden z najlepszych obszarów na start, ponieważ ma duży wolumen powtarzalnych zdarzeń i danych.

Co wdrożyć:

- AI Agent do obsługi zgłoszeń L1.
- Automatyczne diagnozowanie problemów użytkownika.
- Rozwiązywanie typowych problemów bez tworzenia ticketu.
- AI analizujące ticket, logi, historię użytkownika i KB.
- Automatyczne klasyfikowanie, priorytetyzowanie i routing zgłoszeń.
- AI samodzielnie wykonujące dozwolone akcje, np. reset konfiguracji, instalację aplikacji, naprawę VPN.
- Copilot dla analityka Service Desk, który podpowiada rozwiązanie i tworzy odpowiedź.

Przykładowy proces AI Native:

Użytkownik zgłasza problem z VPN → agent AI identyfikuje problem → analizuje urządzenie, logi i znane incydenty → wykonuje bezpieczne działanie naprawcze → testuje rezultat → komunikuje rozwiązanie → zamyka zgłoszenie.

Człowiek angażuje się dopiero wtedy, kiedy AI nie potrafi rozwiązać problemu lub potrzebna jest decyzja/zgoda.

KPI:

- % ticketów rozwiązanych bez udziału człowieka
- First Contact Resolution
- MTTR
- Liczba ticketów per użytkownik
- Koszt obsługi ticketu
- CSAT / User Experience

### ② Software Engineering i Application Development

To nie powinno ograniczać się do Copilota generującego linijki kodu.

Zmiana powinna obejmować cały cykl Software Development Lifecycle (SDLC).

| Obszar | Co wdrożyć |
|---|---|
| Requirements | AI analizuje wymagania, tworzy user stories, wykrywa braki |
| Architecture | AI wspiera analizę architektury i proponuje rozwiązania |
| Development | AI coding agents tworzą kod, testy i dokumentację |
| Code review | AI review, analiza jakości, security i compliance |
| Testing | Generowanie i wykonywanie testów automatycznych |
| DevOps | AI wspiera pipelines, deployment i troubleshooting |
| Maintenance | AI analizuje legacy code, błędy, zależności, podatności |

**Docelowy model**

Developer przestaje być wyłącznie osobą piszącą kod.

Staje się AI-enabled engineer, który:

- deleguje zadania do agentów,
- rozbija problem na mniejsze taski,
- reviewuje kod i rozwiązania AI,
- odpowiada za architekturę i jakość,
- zarządza wieloma strumieniami pracy jednocześnie.

KPI:

- Lead Time for Changes
- Deployment Frequency
- Change Failure Rate
- MTTR
- % kodu/testów/dokumentacji generowanego lub wspieranego przez AI
- czas realizacji feature’a od pomysłu do produkcji

### ③ IT Operations / Infrastructure / Cloud / SRE

Tu należy rozwijać AIOps i agentic operations.

Co wdrożyć:

- AI analizujące telemetrykę, logi, metryki i trace’y.
- Korelację alertów i redukcję alert fatigue.
- AI wykrywające anomalie przed wystąpieniem awarii.
- Automatyczną analizę root cause.
- Runbook automation wykonywaną przez agentów.
- Automatyczne remediation dla wybranych zdarzeń.
- AI optymalizujące cloud costs, capacity i wykorzystanie zasobów.

**Przykład**

Występuje wzrost latency aplikacji.

Zamiast 50 alertów i 3 zespołów analizujących problem:

- AI koreluje metryki aplikacji, bazy danych i infrastruktury.
- Identyfikuje prawdopodobną przyczynę.
- Analizuje ostatnie deploymenty i zmiany konfiguracji.
- Proponuje lub wykonuje rollback.
- Potwierdza stabilizację.
- Tworzy post-incident report.

KPI:

- MTTD / MTTR
- Liczba alertów wymagających manualnej analizy
- % incidentów z automatyczną diagnozą
- % incidentów z automatycznym remediation
- Availability
- Cloud cost per service

### ④ ITSM i procesy IT – przeprojektowanie, a nie tylko automatyzacja

Warto przeanalizować wszystkie procesy ITSM, szczególnie:

- Incident Management
- Request Management
- Problem Management
- Change Management
- Knowledge Management
- Asset Management
- Access Management

Największy błąd to wdrażanie AI na starym procesie.

**Przykład: Access Request**

Stary proces

Użytkownik → formularz → manager → IT → ręczna weryfikacja → nadanie dostępu

AI Native

Użytkownik opisuje potrzebę → AI rozpoznaje kontekst i role → weryfikuje politykę oraz uprawnienia → sprawdza approval rules → automatycznie realizuje request lub kieruje do właściwego approvera → audytuje działanie.

Szukaj procesów, które mają:

- dużo manualnych kroków,
- dużo kopiowania informacji między systemami,
- wysoką powtarzalność,
- jasne reguły biznesowe,
- długi czas oczekiwania,
- dużą liczbę handoffów między zespołami.

### ⑤ Knowledge Management – fundament AI Native IT

Bez uporządkowanej wiedzy AI będzie generować odpowiedzi, ale niekoniecznie poprawne dla konkretnej korporacji.

Co warto zbudować:

- Enterprise AI knowledge layer.
- Jeden dostęp do wiedzy z Confluence, SharePoint, CMDB, ITSM, repozytoriów, dokumentacji.
- Wyszukiwanie semantyczne.
- RAG (Retrieval-Augmented Generation).
- Automatyczne tworzenie i aktualizacja knowledge articles.
- Knowledge graph usług, systemów, ownerów i zależności.
- Mechanizm oceny aktualności, jakości i wiarygodności wiedzy.

Cel: AI ma rozumieć nie tylko ogólną wiedzę IT, ale również jak działa Twoja korporacja.

### ⑥ Cybersecurity – AI dla Security i Security dla AI

Dwa równoległe kierunki:

**AI for Security**

- AI SOC Analyst
- Triage alertów
- Threat hunting
- Analiza phishingu
- Analiza malware i logów
- Incident response copilots
- Automatyczna korelacja zdarzeń

**Security for AI**

- AI Security Policy
- AI access management
- Ochrona danych i DLP
- Prompt injection defense
- Ochrona przed data leakage
- Agent identity
- Least privilege dla agentów
- Audyt działań AI
- Zarządzanie modelami i dostawcami

Nie można budować AI Native, jeśli Security każdą innowację blokuje. Jednocześnie nie można pozwolić agentom na swobodny dostęp do systemów produkcyjnych.

### ⑦ Enterprise Architecture i platformy technologiczne

IT musi zapewnić platformę, dzięki której AI można wdrażać skalowalnie, a nie każdy zespół buduje własne rozwiązanie.

Warto zbudować wspólne komponenty:

- AI Gateway / Model Gateway
- Dostęp do modeli i zarządzanie modelami
- Agent orchestration platform
- API i tool integrations
- Identity dla agentów
- Logging, observability i monitoring AI
- Prompt/version management
- AI evaluation framework
- Guardrails
- Reusable AI components
- Secure sandbox dla agentów

Zasada: zespoły biznesowe i IT powinny korzystać ze wspólnej platformy, a nie za każdym razem rozpoczynać projekt AI od zera.

### ⑧ IT Organization, role i kompetencje

AI Native oznacza również zmianę struktury pracy i odpowiedzialności.

| Dzisiaj | Kierunek AI Native |
|---|---|
| Service Desk Analyst | AI Operations Supervisor |
| Manual Tester | AI Quality & Test Orchestrator |
| Developer | AI-enabled Engineer / Agentic Developer |
| System Administrator | Platform & Automation Engineer |
| Business Analyst | AI Product / Process Designer |
| Operations Engineer | Autonomous Operations Engineer |
| Knowledge Manager | AI Knowledge & Data Steward |

Nie oznacza to koniecznie likwidacji tych ról. Oznacza przesunięcie kompetencji od wykonywania rutynowych czynności do zarządzania systemami, automatyzacją, jakością i wyjątkami.

## 3. Jak szukać potencjału? – AI Opportunity Discovery w IT

Nie zaczynałbym od listy technologii. Zrobiłbym przegląd całego IT pod kątem potencjału AI, najlepiej wspólnie z liderami poszczególnych obszarów.

W każdym zespole szukaj 5 rodzajów marnotrawstwa:

1. Repetitive work — powtarzalne czynności wykonywane codziennie
2. Information hunting — szukanie informacji w wielu systemach
3. Analysis bottlenecks — człowiek analizuje dane, logi, dokumenty i incydenty
4. Decision waiting — procesy czekają na decyzje lub akceptacje
5. Handoffs — przekazywanie zadań między zespołami i systemami

**Pytania, które zadałbym każdemu managerowi IT**

- Jakie 10 czynności zabiera najwięcej czasu Twojemu zespołowi?
- Co robicie ręcznie, co powinno być automatyczne?
- Jakie decyzje podejmujecie na podstawie danych, które już są w systemach?
- Co wymaga kopiowania informacji między aplikacjami?
- Jakie zgłoszenia, problemy lub zadania powtarzają się każdego dnia?
- Co spowalnia delivery?
- Co jest zależne od wiedzy konkretnego eksperta?
- Jakie zadania mogłyby być realizowane bez udziału człowieka?
- Jakie zadania AI mogłoby realizować samodzielnie, ale dziś nie ma dostępu do odpowiednich narzędzi?
- Gdybyśmy mogli zbudować zespół z 5 AI Agentów, jakie zadania byśmy im delegowali?

To często pozwala odkryć znacznie większy potencjał niż klasyczne warsztaty „AI use cases”.

## 4. Co konkretnie wdrożyć – katalog inicjatyw IT

Poniżej przykładowy backlog transformacji.

**AI Native IT – przykładowy portfolio backlog**

Priorytet proponowany: szybkie efekty + budowanie zdolności platformowych

Quick wins (0–3 miesiące)

- AI IT Support Assistant
- AI Ticket Classification & Routing
- Knowledge Assistant dla IT
- Developer Copilot / Coding Agent pilot
- AI Meeting & Documentation Assistant
- AI Incident Summary
- AI dla tworzenia testów i dokumentacji

Transformational initiatives (3–6 miesięcy)

- Agentic Service Desk
- AI-assisted Software Delivery lifecycle
- AIOps & Root Cause Analysis
- AI Access Request Automation
- Automated Testing Agents
- AI Change Risk Assessment
- AI Problem Management

Strategic initiatives (6–12 miesięcy)

- Autonomous IT Operations
- Agentic Software Factory
- Self-healing Infrastructure
- Enterprise AI Agent Platform
- AI Native IT Operating Model
- Outcome-based IT capacity model

## 5. Zmiana architektury IT – co musi powstać

Nie rekomenduję budowania setek odseparowanych chatbotów. Zbudowałbym wspólne capability, na których opierają się use case’y.

**Experience Layer**

AI Assistant • Chat • IDE • IT Portal • Voice

**Agent Layer**

Service Desk Agent • Dev Agent • Ops Agent • Security Agent • QA Agent

**AI Platform Layer**

Model Gateway • Agent Orchestration • Evaluation • Guardrails • Observability • Memory

**Integration & Action Layer**

API • MCP/Tools • IAM • Workflow • RPA • Event Bus

**Enterprise Systems & Data**

ITSM • CMDB • ERP • CRM • Cloud • Monitoring • Git • HR • Knowledge Base

**Kluczowe capability, które powinny być rozwijane centralnie**

| Capability | Po co? |
|---|---|
| AI Gateway | Kontrola modeli, kosztów, dostępu i polityk |
| Agent Platform | Budowa i zarządzanie agentami |
| Agent Identity | Każdy agent ma tożsamość, uprawnienia i właściciela |
| Tool/API Registry | Bezpieczne udostępnianie agentom działań |
| Knowledge Layer | Dostęp do kontekstu korporacyjnego |
| Evaluation Framework | Testowanie jakości, bezpieczeństwa i skuteczności |
| Observability | Monitoring tokenów, kosztów, działań, błędów i jakości |
| Guardrails | Kontrola działań, danych i ryzyka |
| Human Approval | Akceptacje dla krytycznych operacji |
| Reusable Components | Wspólne wzorce, narzędzia i agent skills |

## 6. Governance – bez tego AI Native IT się nie skaluje

Potrzebny jest nowy model zarządzania AI w IT. Nie kolejna komisja zatwierdzająca każdy prompt, tylko governance dostosowane do poziomu ryzyka i autonomii.

| Poziom | Autonomia AI | Przykład | Kontrola |
|---|---|---|---|
| L0 | Informuje | Knowledge Assistant | Standardowe |
| L1 | Rekomenduje | Proponuje rozwiązanie incidentu | Człowiek decyduje |
| L2 | Przygotowuje akcję | Przygotowuje zmianę, ale nie wykonuje | Approval |
| L3 | Wykonuje ograniczone akcje | Restart usługi / reset ustawień | Policy-based |
| L4 | Autonomicznie realizuje proces | Auto-diagnosis & remediation | Monitoring + wyjątki |
| L5 | Koordynuje proces end-to-end | Autonomiczny proces operacyjny | Ścisłe granice, audyt, rollback |

Nie traktowałbym poziomów jako obowiązkowej liniowej ścieżki. Niektóre procesy mogą osiągnąć wysoką autonomię szybko, inne nigdy nie powinny jej osiągnąć ze względu na ryzyko.

W governance powinny znaleźć się:

- AI Risk Classification dla use case’ów.
- Zasady dostępu do danych.
- Agent identity i permissions.
- Approval rules.
- Audit log wszystkich działań agentów.
- Monitoring jakości i błędów.
- Testy agentów przed wdrożeniem i po zmianach.
- Kill switch.
- Mechanizmy rollback.
- Odpowiedzialność biznesowa i techniczna za każdego agenta.

## 7. Roadmap transformacji IT do AI Native

Nie wdrażałbym wszystkiego jednocześnie. Zbudowałbym transformację w 4 falach.

**Fala 1 — Discover & Prove**

0–90 dni

Cel: znaleźć realną wartość i udowodnić ją.

- AI opportunity assessment w całym IT
- Baseline KPI
- AI policy i bezpieczne środowisko
- Pilotaże w Service Desk
- Pilotaż AI-assisted development
- Knowledge assistant
- AI champions w zespołach

Deliverable: 3–5 pilotów, baseline i business case.

**Fala 2 — Build Foundations**

3–6 miesięcy

Cel: zbudować wspólne fundamenty.

- Enterprise AI platform
- Agent framework
- Integration & tool layer
- Knowledge platform
- Evaluation framework
- AI observability
- Agent security & governance
- Nowy model SDLC

Deliverable: reusable AI capabilities + pierwsze produkcyjne agenty.

**Fala 3 — Transform Workflows**

6–9 miesięcy

Cel: przeprojektować całe procesy.

- Agentic ITSM
- AI Software Factory
- AIOps
- Automated request fulfillment
- AI Problem Management
- Autonomous testing
- AI-driven incident response

Deliverable: AI wykonujące procesy end-to-end.

**Fala 4 — AI Native Operating Model**

9–18 miesięcy

Cel: zmienić sposób działania IT.

- Agent-enabled teams
- AI-first process design
- Human supervision model
- Capacity reallocation
- Outcome-based KPIs
- Continuous agent optimization
- Portfolio i budget transformation

Deliverable: IT organizacja zaprojektowana pod współpracę człowiek–AI.

To podejście jest spójne z obecnym kierunkiem transformacji opisywanym przez branżę: przejście od pojedynczych copilots do przebudowy procesów, operating model, governance, platform i sposobu mierzenia efektów. Deloitte Insights +3

## 8. Jak mierzyć, czy IT naprawdę staje się AI Native?

Nie mierzyłbym sukcesu liczbą licencji, promptów, szkoleń czy agentów.

Mierzyłbym zmianę efektywności całego IT.

| KPI | Tradycyjne IT | AI Native ambition |
|---|---|---|
| Service Desk | Tickets per analyst | % autonomicznie rozwiązanych problemów |
| Software Engineering | Liczba developerów / story points | Delivery speed i outcome |
| Operations | Liczba incydentów obsłużonych manualnie | Autonomous detection & recovery |
| Testing | Manual test effort | Autonomous test coverage & quality |
| ITSM | Czas realizacji procesu | End-to-end automation rate |
| Knowledge | Liczba artykułów | Knowledge reuse, freshness, AI retrieval quality |
| Productivity | Wykorzystanie pracownika | Outcome per team / cycle time |
| Cost | IT cost / headcount | Cost per service / transaction |
| AI | Liczba licencji | Realized value, adoption, trust, autonomy |

**KPI transformacji, które wprowadziłbym na poziomie CIO**

- AI Adoption in Workflows – procent procesów, w których AI jest integralną częścią workflow.
- AI Autonomy Rate – procent pracy wykonanej przez AI bez manualnej interwencji.
- Human Intervention Rate – jak często człowiek musi interweniować.
- AI Resolution Rate – procent problemów rozwiązanych przez AI.
- AI Value Realization – realna korzyść finansowa lub odzyskana capacity.
- Cycle Time Reduction – skrócenie czasu end-to-end.
- Quality & Reliability – jakość pracy AI, błędy, rework.
- AI Cost per Outcome – koszt AI w przeliczeniu na rozwiązany problem, dostarczony feature lub proces.

Ważne: autonomię zawsze mierzyć razem z jakością. Agent rozwiązujący 80% ticketów, ale generujący dużo błędów lub eskalacji, nie jest sukcesem.

## 9. Jak priorytetyzować inicjatywy?

Stworzyłbym jeden scoring dla całego IT. Każdy use case oceniany w skali 1–5.

**Proponowany AI Opportunity Score**

\text{Score}=\frac{3V+2F+2R+D}{S+G}

V – Value, F – Feasibility, R – Repetitiveness, D – Data Readiness, S – Security/Risk, G – Governance Complexity

| Kryterium | Co oceniamy? |
|---|---|
| Value (×3) | Wpływ na koszt, jakość, szybkość, biznes |
| Feasibility (×2) | Czy jesteśmy w stanie wdrożyć to szybko? |
| Repetitiveness (×2) | Czy zadanie powtarzalne i skalowalne? |
| Data readiness (×1) | Czy AI ma dostęp do danych i kontekstu? |
| Security/Risk (×1) | Jakie ryzyko niesie automatyzacja? |
| Governance complexity (×1) | Czy potrzebne są złożone approvals i kontrole? |

To przykładowy model, nie standard branżowy. Można go zmodyfikować pod strategię firmy.

## 10. Co zrobiłbym w pierwszych 90 dniach?

**Plan działania dla CIO / IT Leadership**

**Dni 1–30**

Discover & Assess

- Przegląd wszystkich obszarów IT
- Warsztaty z managerami i zespołami
- Analiza procesów, ticketów, workloadów
- Baseline kosztów i KPI
- Lista 30–50 use case’ów
- Wybór top 5

**Dni 31–60**

Experiment & Build

- Uruchomienie 3 pilotów
- AI Service Desk
- AI Software Engineering
- AI Operations
- AI governance
- Przygotowanie platformy i integracji

**Dni 61–90**

Measure & Scale

- Ocena wyników pilotów
- Porównanie z baseline
- Business case
- Plan skalowania
- AI Native IT strategy
- Zmiana operating model i capacity plan

**Moje 5 priorytetów dla korporacyjnego IT**

Gdybym miał wybrać tylko pięć inicjatyw, wybrałbym:

1. **Agentic IT Service Desk**

   Najszybszy potencjał redukcji manualnej pracy i transformacji modelu support.

2. **AI Native Software Engineering**

   Transformacja od copilota do agent-driven SDLC.

3. **Autonomous IT Operations**

   AI diagnozuje, koreluje i automatycznie naprawia incydenty.

4. **Enterprise IT Knowledge Layer**

   Udostępnienie AI wiedzy o aplikacjach, usługach, infrastrukturze, procedurach i problemach.

5. **Enterprise Agent Platform & Governance**

   Wspólna platforma i zasady, dzięki którym agenci mogą bezpiecznie działać w skali.

Te pięć inicjatyw powinno działać jako jeden program, nie pięć niezależnych projektów. Software Engineering, Operations i Service Desk mogą wykorzystywać wspólne knowledge, security, agent platform, evaluation i integration capabilities.

## 11. Gdzie szukać inspiracji i benchmarków?

Polecam obserwować te obszary, a nie tylko nowości produktowe AI:

- McKinsey – Rewiring Software Delivery for the Agentic Era – zmiana modelu delivery, współpraca agentów z developerami, ciągła praca agentów.
- Deloitte – The Great Rebuild: How AI Is Re-Architecting the Tech Organization – przyszłość organizacji IT i ról technologicznych.
- BCG – Reinventing the Operating System of Work with AI – redesign pracy i operating model.
- IBM – AI-driven Enterprise Operating Model – AI-driven development i modernizacja.
- BCG – Scaling Agents Without Creating Your Next Tech Legacy – platforma, governance i kontrola skali agentów.

Wspólny mianownik tych kierunków jest taki, że realny efekt nie wynika tylko z udostępnienia narzędzi AI, ale z przebudowy procesów, ról, platform i sposobu zarządzania. mckinsey.com +4

**Moja rekomendacja: zbudować program „AI Native IT Transformation”**

Ja zorganizowałbym to w 6 workstreamach:

AI Native IT Transformation

Program prowadzony przez CIO, z ownerami poszczególnych strumieni.

01. AI & Automation Opportunities
02. AI Native SDLC
03. Agentic IT Operations
04. AI Native Service Management
05. AI Platform, Data & Architecture
06. People, Governance & Operating Model

Najważniejsze: nie zaczynać od pytania, ile osób uda się zastąpić AI. Zacząć od tego, jaką część pracy IT można wyeliminować, przyspieszyć, przeprojektować lub delegować agentom — i jak odzyskaną capacity wykorzystać do modernizacji, innowacji, poprawy jakości i szybszego delivery.

Jeżeli chcesz, mogę w kolejnym kroku przygotować Ci konkreny AI Native IT Transformation Blueprint – jako materiał dla CIO/IT Leadership, z 20–30 inicjatywami, priorytetami, KPI, roadmapą 12 miesięcy i docelowym operating modelem IT.
