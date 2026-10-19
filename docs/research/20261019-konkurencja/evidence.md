# Dowody — analiza konkurencji (stan na 2026-10-19)

Legenda werdyktu (pierwsza kolumna):
- **P** — potwierdzone w ≥ 2 niezależnych źródłach lub w źródle pierwotnym (dostawca) + niezależnym,
- **C** — częściowo: jedno źródło lub tylko źródła dostawcy,
- **N** — niepotwierdzone: twierdzenie wykonawcy, którego nie udało się potwierdzić,
- **S** — sprzeczne: źródła się różnią.

Uwaga metodologiczna: polityka sieci środowiska blokuje pobieranie stron (`CONNECT 403` / `ENOTFOUND`). **Żadna strona nie została otwarta** — wszystkie ustalenia pochodzą z podsumowań wyników wyszukiwarki. Cytaty to omówienia, nie dosłowny tekst źródeł. Dostawca = źródło pierwotne, ale marketingowe.

## Kategoria 1: platformy product management / discovery

| W | Ustalenie | Źródło | Data | Ranga |
|---|---|---|---|---|
| P | ProdPad CoPilot ma pomagać „sanity-check a plan and challenge a decision before you commit”, korzystając z roadmapy, pomysłów, OKR, feedbacku i **wcześniejszych decyzji**; działa na API OpenAI; interaktywny (na żądanie) | prodpad.com/features/ai/; prodpad.com/product-management-ai/; justcall.io/ai-agent-directory/prodpad-copilot-for-product-managers/ | b.d. | dostawca + katalog (powiela dostawcę) |
| C | ProdPad: brak niezależnych recenzji jakości „pressure-testingu” | wyszukiwanie własne | 2026-10-19 | — |
| P | Productboard Spark: system agentów od discovery po specyfikację; kontekst (strategia, OKR, persony, historia) ładowany automatycznie; wyniki „traceable to a real customer source”; od 06.2026 tworzenie encji z rozmowy; publiczna beta 10.2025 → GA | productboard.com/blog/introducing-spark-ai-product-management-agent/ (2025-10-02); productboard.com/blog/introducing-spark-agentic-product-system/ (2026-06); businesstechnavigator.com/news/productboard-spark-agentic-product-system-2026 (2026-07-31) | 2025–2026 | dostawca + niezależna analiza |
| C | Spark: cotygodniowe odświeżanie wykrywanych szans produktowych; brak powiązania z zatwierdzoną decyzją | productboard.com/spark/ | b.d. | dostawca |
| P | Dovetail Agents: działają w tle, obserwują sygnały klientów, wysyłają alerty (Slack/Teams/e-mail), tworzą zgłoszenia; beta 10.2025, rozszerzone w „Sun's Out” 2026-07-14 | dovetail.com/blog/2025-fall-launch/; dovetail.com/blog/suns-out-summer-launch-26/; martechseries.com (komunikat); techintelpro.com | 2025-10, 2026-07 | dostawca + przedruki komunikatu |
| C | Vistaly: drzewo szans (OST) z testami założeń przy rozwiązaniach i statusem „czy testowano”; AI syntetyzuje wywiady do drzewa; zespół miał problemy z kalibracją sędziego LLM | producttalk.org/tools-of-the-trade-vistaly/ (2025-01); zenml.io/llmops-database/ai-assisted-customer-discovery-and-opportunity-mapping | 2025 | niezależne (Product Talk) |
| C | Aha!: asystent Elle i agent badawczy (Q1–Q2 2026) — synteza, szkice strategii, wymagania dla agentów kodujących | aha.io/blog/most-popular-new-aha-features-launched-in-q2-2026 | 2026-07-01 | dostawca |
| C | Jira Product Discovery: AI generuje i porządkuje treść (Premium); brak pola siły dowodu | support.atlassian.com/jira-product-discovery/docs/explore-atlassian-intelligence-in-jira-product-discovery/; eesel.ai/blog/jira-product-discovery-ai-features | 2026-01 | dostawca + niezależne |
| C | Dragonboat: asystenci AI monitorują zdrowie realizacji i postęp strategii („detect risks before they surface”) — ryzyka wykonania, nie decyzji | dragonboat.io/dragonboat-apps/ai-assistants/ | b.d. | dostawca |
| C | Unwrap: alerty o nowych trendach w feedbacku, tylko w planie enterprise (ok. 24 tys. USD/rok) | toolradar.com/tools/unwrap | 2026-08 | katalog |
| C | airfocus: współzałożyciel opisuje narzędzie jako identyfikowalny „decision log” | linkedin.com/in/maltescholz | b.d. | powiązane z dostawcą |
| N | Zeda.io zamyka działalność — tylko blog konkurenta (BuildBetter); własne wyszukiwanie nie znalazło potwierdzenia | blog.buildbetter.ai/zeda-io-is-shutting-down-…; wyszukiwanie własne | b.d. | konkurent |
| N | Kraftful przejęty przez Amplitude w 2025 — tylko blog konkurenta | sleekplan.com/blog/kraftful-alternatives-in-2026-… | 2026 | konkurent |

## Kategoria 2: wymagania, identyfikowalność, analiza wpływu zmian

| W | Ustalenie | Źródło | Data | Ranga |
|---|---|---|---|---|
| P | Jama Connect Advisor ocenia **jakość sformułowania** wymagań (INCOSE, EARS); IBM RQA ocenia jakość i niejednoznaczność; **żadne nie sprawdza wymagań względem badań użytkowników** | jamasoftware.com/blog/2025/03/20/…jama-connect-advisor/; jamasoftware.com/blog/ai-requirements-management/; ibm.com/products/requirements-quality-assistant; wyszukiwanie własne (extended) | 2025–2026 | dostawca + podsumowanie wyszukiwania |
| C | Jama Impact Analysis i „suspect links”: zmiana pola elementu nadrzędnego oznacza powiązane elementy do przeglądu; administrator konfiguruje, które pola wyzwalają oznaczenie | help.jamasoftware.com/…/impact-analysis.html; help.jamasoftware.com/…/clear-suspect-links.html | b.d. | dostawca |
| C | PTC Codebeamer AI 1.0 (01.2026): Requirements Assistant wykrywa problemy jakościowe wymagań (INCOSE/ISTQB) | ptc.com/en/news/2026/ptc-delivers-new-ai-functionality-with-new-alm-releases | 2026-01 | dostawca |
| C | Polarion X na Azure (11.2025): „AI … for requirement analysis, risk detection, and predictive insights” — mechanizm nieopisany | itbrief.com.au/story/siemens-brings-polarion-x-alm-platform-to-microsoft-azure | 2025-11 | prasa (przedruk) |
| C | Visure Vivia: „flags inconsistencies”; analiza wpływu „one-click” | visuresolutions.com/features/ai-requirements-management/; Product Sheet 2025 | 2025–2026 | dostawca |
| C | Copilot4DevOps (Modern Requirements): „gap analysis”, „impact assessment” — znaczenie niejasne | getapp.com/…/copilot4devops/ | 2026 | katalog |
| C | Dostawcy uruchamiają serwery MCP (Jama, Visure, społecznościowy dla Polarion) | aqua-cloud.io/jama-connect-review-features-pricing/; yespress.io/visure-solutions | 2026 | wtórne |

## Kategoria 3: decision intelligence, rejestry decyzji, założenia

| W | Ustalenie | Źródło | Data | Ranga |
|---|---|---|---|---|
| C | Gartner: platformy DI „combine explicit decision modeling, AI, analytics … to support, augment or automate decision making”; pierwszy Magic Quadrant DI 2026-01-26; liderzy m.in. IBM, Quantexa, FICO, Aera | gartner.com/en/documents/5599159 (abstrakt); gartner.com/doc/7363830 (abstrakt); quantexa.com/press/…; marketplace.fico.com/blogs/… | 2024-07, 2026-01 | abstrakt analityka + komunikaty dostawców |
| C | Kategoria „decision intelligence” wg Gartnera dotyczy automatyzacji decyzji operacyjnych na danych (ryzyko, łańcuch dostaw), kupujący: liderzy danych i analityki | jw. + businesswire.com (Aera, 2026-05-04) | 2026 | wniosek z abstraktów |
| C | Cloverpop: „system of record” dla decyzji (kto, jakie opcje, wynik vs oczekiwania), **AI decision coach** proponujący działania „with the least effort” — **opis z 2018 r.**, aktualność niepotwierdzona; obecnie silnik D-Sight | cloverpop.com/resources/product-update-system-of-record-for-decisions; destinationcrm.com/…128035; cloverpop.com/decision-platform | 2018 / b.d. | dostawca + prasa 2018 |
| C | Rejestry decyzji (DecTrack, Decision Desk, DecisionOS, Decidary): decyzja jako rekord, uzasadnienie, właściciel, przypomnienia; bez powiązania z dowodami i bez wykrywania ryzyk | startbase.com/organization/dectrack/; g2.com/products/decision-desk/discuss; getapp.com/all-software/a/decidary-com/ | 2026 | katalogi |
| C | Narzędzia do kwestionowania decyzji to głównie prompty / skille (devil's advocate, pre-mortem), jednorazowe, bez trwałego modelu decyzji | onewave-ai.com/resources/claude-skills/devils-advocate; github.com/georgeplendl/Assumption-Loop-Toolkit | 2026 | społeczność |
| P | Nie znaleziono dojrzałego produktu, który automatycznie porównuje wymagania / rozwiązanie z repozytorium badań i sygnalizuje sprzeczności | wykonawca 3 + wyszukiwanie własne (extended) | 2026-10-19 | brak dowodu (słaby sygnał) |

## Kategoria 4: ogólni asystenci AI

Szczegóły: [raw/04-asystenci-ai.md](raw/04-asystenci-ai.md). Kluczowe:

| W | Ustalenie | Źródło | Data | Ranga |
|---|---|---|---|---|
| C | Notion Custom Agents uruchamiane harmonogramem lub wyzwalaczem | notion.com/releases/2025-09-18 | 2025-09-18 | dostawca |
| C | Glean: agenci harmonogramowi; eksperymentalne Triggers API (webhooki o zmianach treści) | docs.glean.com/release-notes/…2026-05-06…; …2026-08-18… | 2026 | dostawca |
| C | ChatGPT: zaplanowane zadania (06.2026) | gigazine.net/gsc_news/en/20260619-chatgpt-scheduled-tasks/ | 2026-06 | wtórne |
| C | Brak wbudowanego agenta przeglądu decyzji / wymagań w Rovo; Rovo Studio (no-code) dostępne | buzzclan.com/atlassian/atlassian-rovo/; eesel.ai/blog/rovo-ai-actions | 2026 | wtórne |
| C | ChatPRD i podobne (Thinkr, skill review-prd): przegląd pojedynczego PRD według rubryki, bez monitoringu | chatprd.ai/blog/whats-new-april-22-2024; hunted.space/product/thinkr | 2024–2026 | dostawca / społeczność |

## Kategoria 5: popyt, krytyka, dynamika rynku

| W | Ustalenie | Źródło | Data | Ranga |
|---|---|---|---|---|
| C | 10% respondentów „very confident” co do dokładności danych; 92% — „the loudest voice often wins” (n=169) | airfocus.com/resources/ebooks/great-product-ops-report/ | ok. 2025 | ankieta dostawcy, jedno źródło |
| C | 36% — strategię definiuje najwyższe kierownictwo | productplan.com/blog/trends-shaping-product-management-in-2025 | 2025 | ankieta dostawcy |
| C | Praktycy: rejestry decyzji to „busywork”; „I've never seen a product manager use a decision log” | amycmitchell.substack.com/p/product-manager-decision-log | b.d. | społeczność, anegdota |
| C | Problem „ponownego otwierania decyzji” (relitigation) opisywany przez dostawców narzędzi | fabric.so/blog/why-product-decisions-get-relitigated | b.d. | dostawca |
| C | Badania: kontrargumenty LLM poprawiają satysfakcję i elastyczność grupy, zwłaszcza dla mniejszości; efekt słabnie u starszych stażem; mediowany sprzeciw może obniżać bezpieczeństwo psychologiczne | arXiv 2503.14263; arXiv 2606.31762 | 2025–2026 | preprinty (niezrecenzowane) |
| C | Służalczość (sycophancy) powszechna w 17 LLM; ramowanie w trzeciej osobie zmniejsza ją do 63,8% | SYCON Bench, EMNLP 2025 (underline.io/lecture/131998-…) | 2025 | akademickie |
| C | Małe rundy finansowania „AI dla zespołów produktowych”: ProductNow 6 mln USD (07.2025) i inne < 4 mln | finder.techleap.nl/news/feed/productnow-raises-6m-for-ai-os | 2025 | wtórne |
| N | Brak potwierdzonych zamknięć startupów z kategorii „decision log / assumption testing dla PM” — wyszukiwarka zwracała szum | wykonawca 5 | — | brak dowodu |
