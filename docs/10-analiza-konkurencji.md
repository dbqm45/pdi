# 10. Analiza konkurencji

**Stan na:** 2026-10-19 · **Etap planu:** 2.1 ([plan](08-plan-projektu.md#etap-2-walidacja-koncepcji-i-przewagi)) · **Dowody:** [evidence.md](research/20261019-konkurencja/evidence.md) · **Metoda i luki:** [sources.md](research/20261019-konkurencja/sources.md)

> **Ograniczenie, które trzeba znać przed lekturą.** Środowisko, w którym wykonano badanie, blokuje pobieranie stron. Wszystkie ustalenia pochodzą z podsumowań wyników wyszukiwarki, bez otwierania źródeł. Większość dowodów to materiały dostawców. Wnioski o **braku** funkcji opierają się na tym, że jej nie znaleziono, a to słaby dowód. Raport jest wystarczający do ukierunkowania dalszej pracy, ale nie do ogłoszenia, że luka rynkowa istnieje.

## 1. Pytanie i decyzja

- **Pytanie:** czy istniejące narzędzia obsługują scenariusze S1–S6, na których opiera się wartość PDI?
- **Decyzja, której służy:** PDI jako produkt komercyjny czy narzędzie wewnętrzne (reguła w planie, Etap 2.1).

Scenariusze:

| | Scenariusz |
|---|---|
| S1 | Wykrycie niezweryfikowanego założenia traktowanego jak fakt |
| S2 | Wykrycie sprzeczności między dowodami (np. badaniem) a proponowanym rozwiązaniem |
| S3 | Ustalenie, jakiej informacji brakuje do podjęcia konkretnej decyzji |
| S4 | Propozycja działania, które zamknie lukę w wiedzy |
| S5 | Wykrycie nowej informacji, która podważa wcześniej podjętą decyzję |
| S6 | Ograniczanie niepotrzebnych powiadomień (zarządzanie uwagą) |

## 2. Mapa rynku

Zbadano 5 kategorii i ok. 40 narzędzi.

| Kategoria | Przykłady | Co robi AI | Kupujący | Relacja do PDI |
|---|---|---|---|---|
| **Product management / discovery** | Productboard Spark, ProdPad CoPilot, Aha!, Jira Product Discovery, Vistaly, Dovetail, Dragonboat, Unwrap | Synteza feedbacku, generowanie specyfikacji i PRD, wykrywanie trendów w sygnałach klientów | Zespoły produktowe, PM | **Najbliższa konkurencja** i główne ryzyko przejęcia pomysłu przez dostawców |
| **Wymagania i identyfikowalność** | Jama Connect, Polarion, Codebeamer, IBM DOORS Next, Visure, Copilot4DevOps | Ocena jakości sformułowania wymagań, analiza wpływu zmian po powiązaniach | Inżynieria regulowana (motoryzacja, medycyna, lotnictwo) | Inna kategoria i inny kupujący |
| **„Decision intelligence” (wg Gartnera)** | Aera, IBM, Quantexa, FICO, Tellius, Pyramid | Modelowanie i automatyzacja decyzji operacyjnych na danych | Liderzy danych i analityki | **Ta sama nazwa, inny problem** |
| **Rejestry decyzji i narzędzia do założeń** | Cloverpop, DecTrack, Decision Desk, mapy założeń (Miro), skille typu devil's advocate i pre-mortem | Zapis decyzji, przypomnienia, jednorazowe kwestionowanie | Zespoły, kadra kierownicza | Częściowo zbieżne, płytkie |
| **Ogólni asystenci AI** | ChatGPT, Claude, Notion Agents, Glean, Rovo, M365 Copilot, ChatPRD | Dowolna analiza na żądanie; od 2025–2026 także zadania według harmonogramu i wyzwalaczy | Wszyscy | **Najsilniejszy zamiennik** |

## 3. Macierz scenariuszy (najbliższe narzędzia)

Oznaczenia:
- **tak** — funkcja wbudowana, potwierdzona w źródłach;
- **częściowo** — wbudowana, ale w węższym sensie;
- **DIY** — możliwe tylko wtedy, gdy PM sam napisze prompt lub zbuduje agenta;
- **?** — brak informacji;
- **nie** — źródła opisują wyłącznie inną funkcję.

| Narzędzie | S1 | S2 | S3 | S4 | S5 | S6 | Decyzja jako obiekt | Fakt / hipoteza | Działa w tle |
|---|---|---|---|---|---|---|---|---|---|
| ProdPad CoPilot | częściowo¹ | ? | ? | częściowo¹ | nie | ? | częściowo (historia decyzji jako kontekst) | ? | nie |
| Productboard Spark | ? | ? | ? | ? | częściowo² | ? | nie | ? | częściowo |
| Vistaly | częściowo³ | nie | nie | częściowo³ | nie | ? | częściowo | częściowo | nie |
| Dovetail Agents | ? | ? | ? | ? | częściowo² | częściowo⁴ | nie | ? | tak |
| Jama Connect | nie | częściowo⁵ | częściowo⁶ | nie | częściowo⁷ | częściowo⁸ | nie | nie | częściowo |
| Cloverpop | ? | ? | częściowo⁹ | częściowo⁹ | ? | ? | **tak** | ? | ? |
| Rejestry decyzji | nie | nie | nie | nie | nie | częściowo (przypomnienia) | **tak** | nie | nie |
| Ogólny LLM z dobrym promptem | DIY | DIY | DIY | DIY | DIY¹⁰ | nie | nie | DIY | DIY¹⁰ |
| **PDI (koncepcja)** | tak | tak | tak | tak | tak | tak | tak | tak | tak |

Przypisy:
1. „Challenge a decision before you commit” — interaktywnie, na żądanie PM-a; jakość niezweryfikowana niezależnie.
2. Monitoruje szanse produktowe (Spark) albo skoki w sygnałach klientów (Dovetail), a nie aktualność uzasadnienia konkretnej decyzji.
3. Ręczne testy założeń i status „czy testowano” w drzewie szans; brak automatycznego wykrywania.
4. Kierowanie alertów do właściwego zespołu; brak mechanizmów ograniczania szumu.
5. Jakość sformułowania wymagania (INCOSE, EARS), a nie zgodność z dowodami.
6. Brakujące powiązania między elementami, a nie brakująca wiedza.
7. Strukturalnie: zmiana elementu oznacza powiązane elementy jako podejrzane. Działa tylko wewnątrz narzędzia, bez interpretacji znaczenia zmiany.
8. Administrator konfiguruje, które pola wywołują oznaczenie.
9. AI decision coach proponujący działania „with the least effort” — źródło z 2018 r., aktualność niepotwierdzona.
10. Notion Custom Agents, Glean (harmonogramy, eksperymentalne Triggers API), zaplanowane zadania w ChatGPT (06.2026). Ponowne uruchomienie promptu jest możliwe, ale bez modelu tego, co już było wiadomo.

## 4. Ustalenia

**U1. Nie znaleziono narzędzia, które łączy cztery elementy: decyzję jako obiekt, rozróżnienie dowodów i hipotez, wykrywanie ryzyk dla uzasadnienia oraz monitoring powiązany z konkretną decyzją.** Każdy element z osobna istnieje:
- decyzja jako obiekt: Cloverpop, rejestry decyzji;
- założenia: Vistaly;
- kwestionowanie decyzji: ProdPad;
- monitoring w tle: Dovetail, Spark;
- analiza wpływu zmian: Jama.

Wyszukiwanie przeciwne („czy istnieje narzędzie, które sygnalizuje sprzeczność wymagań z badaniami”) zwróciło tylko zestawy promptów i ogólne poradniki. *Siła dowodu: umiarkowana. Brak wyniku wyszukiwania to nie dowód braku produktu.*

**U2. Najsilniejszym zamiennikiem nie jest konkurent z kategorii, tylko ogólny asystent AI z dobrym promptem.** Scenariusze S1–S4 to rdzeń Decision Risk Radar. PM może je uzyskać jednorazowo w ChatGPT lub Claude, jeśli wklei materiały i dobrze zada pytanie. Istnieją już otwarte zestawy promptów, które robią dokładnie to. Przykładem jest Assumption-Loop-Toolkit, który oznacza każde wymaganie jako „validated” albo „assumed”. **Jednorazowa analiza nie może więc być główną przewagą PDI.** *Potwierdzone testem praktycznym 2026-10-19 ([raport](../eval/status-zamowienia/wyniki/raport.md)): ogólny asystent z dobrym promptem uzyskał ten sam wynik co prototyp PDI, także w reakcji na nowe informacje w tej samej rozmowie.*

**U3. Prawdziwa luka leży w tym, co jest trwałe i ciągłe:**
- model decyzji, który zachowuje się między sesjami: co było wiadomo, co jest hipotezą, co zaakceptowano;
- S5 w sensie „ta nowa informacja podważa *to* założenie *tej* decyzji”;
- S6, czyli ochrona uwagi.

Żadne narzędzie nie ma S6 w sensie progów istotności, deduplikacji i uczenia się na odrzuconych alertach. Monitoring w Dovetail, Spark czy Dragonboat dotyczy sygnałów klientów i realizacji, a nie aktualności uzasadnienia.

**U4. Infrastruktura monitoringu szybko staje się powszechna.** Wyzwalacze i harmonogramy agentów wprowadziły Notion (2025-09), Glean (2026-05 i 2026-08) oraz ChatGPT (2026-06). Argument „nikt nie monitoruje” traci ważność. Ważny pozostaje argument „nikt nie wie, *co* monitorować i kiedy to jest istotne”, ale ten wymaga trwałego modelu decyzji.

**U5. Najbliżej ruchu w stronę PDI są Productboard Spark i ProdPad.**
- **Spark** automatycznie ładuje strategię, OKR i historię, deklaruje identyfikowalność wyników do źródeł klientów, ma agentów i serwer MCP.
- **ProdPad** reklamuje kwestionowanie decyzji z użyciem wcześniejszych decyzji jako kontekstu.

Każdy z nich może dodać ocenę uzasadnienia relatywnie tanio. **Ryzyko „to tylko funkcja, nie produkt” jest realne.** *Ocena.*

**U6. Narzędzia do wymagań i identyfikowalności to inna kategoria.**
- Oceniają formę artefaktu (sformułowanie, testowalność, kompletność powiązań), a nie to, czy artefakt jest uzasadniony.
- Analiza wpływu zmian jest strukturalna i działa tylko wewnątrz ich grafu.
- Sprzedają do inżynierii regulowanej.

To nie jest bezpośrednia konkurencja. Wiele z nich (Jama, Visure) udostępnia jednak serwery MCP, więc w przyszłości mogą być źródłem danych dla PDI.

**U7. Nazwa „Decision Intelligence” jest zajęta.** Gartner opublikował 2026-01-26 pierwszy Magic Quadrant dla platform Decision Intelligence. Kategoria oznacza tam automatyzację decyzji operacyjnych na danych, a kupującymi są liderzy danych i analityki. Używanie tej nazwy na rynku wprowadzałoby w błąd i stawiało PDI obok IBM, FICO czy Aera.

**U8. Dowody popytu są słabe, a sygnały ostrzegawcze konkretne.**
- Dane o problemie pochodzą z ankiet dostawców, np. „92% — the loudest voice often wins”, n=169, jedno źródło.
- Praktycy opisują rejestry decyzji jako „busywork”, którego PM-owie nie prowadzą. Każdy model wymagający ręcznego prowadzenia podzieli ich los.
- Badania nad AI jako głosem sprzeciwu dają wyniki mieszane: poprawa satysfakcji i elastyczności grupy, ale słabnący efekt u osób starszych stażem i ryzyko dla bezpieczeństwa psychologicznego.
- Finansowanie startupów „AI dla zespołów produktowych” to małe rundy (do ok. 6 mln USD w 2025 r.).

## 5. Krytyka ustaleń

| Głos | Zarzut | Odpowiedź |
|---|---|---|
| Sceptyczny praktyk | „PM wklei PRD do ChatGPT i dostanie 80% tej wartości.” | Prawdopodobnie tak dla jednorazowej analizy (U2). Dlatego test w Etapie 2.3 musi obejmować **drugi przebieg po pojawieniu się nowej informacji**, a nie tylko pierwszą analizę. |
| Wrogi recenzent | „Nie otworzyliście ani jednej strony. «Nie znaleziono» to nie dowód braku.” | Słusznie. Werdykty C w tabeli dowodów wymagają otwarcia źródeł, a test praktyczny na trialach ProdPad i Spark jest obowiązkowy przed decyzją o kierunku komercyjnym. |
| Inżynier wdrażający | „Monitoring wymaga dostępu do źródeł partnerów, a jednoosobowy projekt nie zbuduje integracji.” | Dostawcy coraz częściej udostępniają serwery MCP (Productboard, Craft.io, Jama, Visure, Dovetail). PDI jako **warstwa nad istniejącymi narzędziami** przez MCP jest dla jednej osoby wykonalne. Budowa integracji od zera nie jest. |

## 6. Wnioski dla decyzji: produkt komercyjny czy narzędzie wewnętrzne

Reguła z planu: kierunek komercyjny, jeśli żadne narzędzie nie radzi sobie dobrze z co najmniej 3 z 6 scenariuszy **i** partnerzy wykazują zainteresowanie.

| Warunek | Stan |
|---|---|
| Gotowe produkty nie pokrywają ≥ 3 scenariuszy | **Spełniony wstępnie.** S2, S3, S5 (w sensie decyzji) i S6 nie są wbudowane w żadnym znalezionym narzędziu. |
| …licząc ogólnego asystenta AI z promptem | **Niespełniony dla S1–S4** (DIY). Pozostają S5 i S6 oraz trwałość modelu. |
| Partnerzy wykazują zainteresowanie | **Niesprawdzony** (Etap 0). |

**Werdykt: kierunek komercyjny pozostaje otwarty, ale tylko w wąskiej postaci i nie rozstrzygamy go teraz.** Jeśli PDI ma być produktem, jego wartością musi być ciągłość: trwały model decyzji, wykrywanie zdarzeń podważających konkretne założenia i ochrona uwagi. Nie może nią być jednorazowa krytyka inicjatywy, bo tę daje dziś każdy asystent AI. Ostatecznie rozstrzygnie to test 2.3 i odzew partnerów.

Reguła wymaga doprecyzowania. Proponuję uznawać scenariusz za pokryty przez narzędzie, jeśli PM uzyskuje wynik **bez budowania własnego agenta i bez ponownego dostarczania kontekstu**. Przy takiej definicji ogólny asystent AI pokrywa S1–S4 tylko częściowo.

## 7. Rekomendacje

Rekomendacje, oddzielone od faktów:

1. **Przesunąć akcent wartości z radaru na ciągłość.** W komunikacji i w MVP wyróżnikiem mają być S5, S6 i trwały model decyzji. Radar (S1–S4) zostaje, bo bez niego nie ma modelu, ale nie jest argumentem sprzedażowym.
2. **Zaostrzyć test 2.3.** Przypadek z zaszytymi błędami (`examples/status-zamowienia.yaml` jako dokumenty) przepuścić przez ogólny LLM z dobrym promptem, ProdPad CoPilot i Productboard Spark (triale). Potem dodać nowy dowód i sprawdzić, które narzędzie samo zauważy, że podważa on założenie decyzji. To właściwy test przewagi.
3. **Nie używać nazwy „Decision Intelligence” na rynku.** Wewnętrzna nazwa robocza PDI może zostać. Przy ewentualnej komercjalizacji potrzebna jest nazwa kategorii bez kolizji z Gartnerem, np. w kierunku „decision quality” lub „decision assurance” *[propozycja do sprawdzenia]*.
4. **Architektura jako warstwa przez MCP**, a nie samodzielna platforma. Pasuje do jednoosobowego zespołu i do faktu, że PM-owie nie chcą kolejnego miejsca do prowadzenia dokumentacji.
5. **Żadnego ręcznego prowadzenia modelu.** Model musi powstawać z istniejących materiałów, a PM tylko potwierdza rekonstrukcję. To już jest w specyfikacji, a analiza (U8) to potwierdza.
6. **Obserwować:** Productboard Spark, ProdPad CoPilot, Dovetail Agents i Cloverpop (czy coach jeszcze istnieje). Ponowić przegląd przed Etapem 4.
7. **Domknąć luki dowodowe:** otworzyć źródła z werdyktem C, sprawdzić pełne raporty „state of product management” (Productboard, Pendo, Atlassian) pod kątem danych o problemie.
