# 8. Plan projektu: Product Decision Intelligence

> Wersja po weryfikacji. Zmiany względem wersji wstępnej są oznaczone **[K1]**, **[M3]** itd. i wyjaśnione w [09-weryfikacja-planu.md](09-weryfikacja-planu.md).

**Wizja:** system, który pomaga organizacji podejmować lepsze decyzje produktowe, wykrywa zagrożenia dla ich jakości i wskazuje działania potrzebne do ich rozwiązania — zanim błędy przełożą się na niepotrzebną pracę, koszty lub niewłaściwe rozwiązania.

**Główna zasada:** nie automatyzujemy wyłącznie przygotowania dokumentacji. Podnosimy jakość procesu myślenia, uzasadniania decyzji i działania na podstawie dowodów.

**Pierwszy użytkownik:** Product Manager jako właściciel decyzji. System jest jego sparingpartnerem, nie audytorem — wyniki są domyślnie prywatne dla PM-a. ([9.3](09-weryfikacja-planu.md#93-konsekwencje-wyboru-pm-jako-właściciel-decyzji))

**Stan wyjściowy:** nie mamy jeszcze dostępu do inicjatyw ani organizacji pilotażowej. Pierwszym zadaniem jest ich pozyskanie. **[K1]**

---

## 1. Cel i zakres projektu

### Problem, który chcemy rozwiązać

Informacje potrzebne do podjęcia decyzji produktowej są rozproszone między zespołami, dokumentami, narzędziami i historią wcześniejszych ustaleń.

W efekcie organizacja może:

- podejmować decyzje na podstawie niepełnych lub nieaktualnych informacji;
- traktować hipotezy jak potwierdzone fakty;
- przechodzić do projektowania rozwiązania przed wystarczającym rozpoznaniem problemu;
- nie dostrzegać sprzeczności między strategią, wymaganiami i designem;
- rozpoczynać refinement i estymację mimo istotnych niewiadomych;
- zbyt późno rozpoznawać, że nowe informacje podważają wcześniejsze decyzje.

Problemem nie jest wyłącznie brak informacji. Jest nim również brak mechanizmu, który potrafi połączyć dostępne informacje, ocenić ich znaczenie i zainicjować właściwe działanie.

### Cel projektu

Zaprojektować i zweryfikować system, który:

1. Łączy dowody z różnych źródeł.
2. Odtwarza uzasadnienie decyzji produktowych.
3. Wykrywa istotne luki, sprzeczności i nieuzasadnione założenia.
4. Ocenia gotowość do kolejnych kroków procesu. **[M8]**
5. Aktywnie pomaga zamykać luki w wiedzy.
6. Monitoruje nowe informacje i ich potencjalny wpływ na wcześniejsze decyzje.
7. Angażuje człowieka tylko wtedy, gdy jego uwaga jest rzeczywiście potrzebna.

### Czego projekt nie robi na początku

- Nie buduje kolejnego narzędzia do zarządzania backlogiem.
- Nie zastępuje istniejących systemów produktowych.
- Nie podejmuje decyzji za Product Managerów.
- Nie tworzy kompletnej platformy integrującej wszystkie narzędzia organizacji.
- Nie traktuje generowania dokumentacji jako głównej wartości.

Dokumentacja jest jednym z rezultatów działania systemu, a nie jego główną wartością.

---

## 2. Docelowa koncepcja rozwiązania

| Mechanizm | Rola | Główna wartość | Specyfikacja |
|---|---|---|---|
| **Decision Risk Radar** | Wykrywa zagrożenia dla jakości decyzji | Wcześniejsze rozpoznawanie ryzyka | [03](03-decision-risk-radar.md) |
| **Knowledge Gap Closure** | Pomaga rozwiązywać problemy wynikające z brakującej wiedzy | Przejście od wykrycia problemu do działania | [04](04-knowledge-gap-closure.md) |
| **Decision Integrity Graph** | Utrzymuje powiązania między dowodami, hipotezami, decyzjami i rozwiązaniem | Spójność i ciągłość rozumowania | [02](02-living-decision-model.md) |

Wspólnym elementem jest model decyzji produktowej (Living Decision Model), który przechowuje nie tylko treść ustaleń, ale również ich uzasadnienie. O tym, kiedy system angażuje człowieka, decyduje Attention Intelligence ([05](05-attention-intelligence.md)).

### Cykl działania

1. **Zrozumienie** — system ustala, co organizacja wie, czego się domyśla i czego jeszcze nie rozstrzygnęła.
2. **Ocena** — identyfikuje brakujące dowody, sprzeczności, ryzyka i nieaktualne założenia.
3. **Priorytetyzacja** — waży wpływ na decyzję, koszt błędu i odwracalność decyzji.
4. **Działanie** — proponuje najbardziej wartościowy następny krok: sam sprawdza źródła, prosi PM-a o wyjaśnienie lub sugeruje dodatkową analizę.
5. **Weryfikacja** — po uzyskaniu nowych informacji aktualizuje analizę i sprawdza, czy problem został rozwiązany.
6. **Monitorowanie** — w tle ocenia znaczenie nowych informacji dla wcześniejszych ustaleń i reaguje proporcjonalnie do ryzyka.

---

## 3. Plan realizacji — siedem etapów

Harmonogram liczony jest **od zamknięcia Etapu 0**, bo bez design partnerów etapy 1, 2 i 5 nie mogą się odbyć. Szacunek 12–16 tygodni po Etapie 0 zakłada niewielki zespół (patrz sekcja 6) i wykorzystanie istniejących modeli AI. Nie jest zobowiązaniem terminowym. **[M9]**

### Etap 0. Design partnerzy i przypadki **[K1] [K3]**

**Czas: tygodnie 0–3** (równolegle: analiza konkurencji z Etapu 2.1 **[M6]**)

**Cel:** pozyskać ludzi i materiały, bez których nie da się zwalidować wartości.

**Zadania:**

- **0.1. Profil design partnera.** PM odpowiedzialny za decyzje o inicjatywach, w organizacji z co najmniej kilkoma zespołami produktowymi, gotowy poświęcić ok. 3–4 godziny w miesiącu i udostępnić materiały.
- **0.2. Propozycja dla partnera.** Jednostronicowy opis: co PM dostaje (analiza swojej bieżącej inicjatywy według modelu PDI, prywatnie), czego oczekujemy (wywiad, materiały, ocena wyników), jak chronimy poufność.
- **0.3. Zasady poufności.** Prosta umowa poufności, anonimizacja, jawna informacja o dostawcy modelu i warunkach przetwarzania (bez trenowania na danych), prawo do usunięcia materiałów.
- **0.4. Rekrutacja.** Lista 15–20 kandydatów, kontakt, rozmowy kwalifikacyjne.
- **0.5. Zbiór przypadków.** Od partnerów: inicjatywy bieżące i zakończone, z materiałami z chwili podjęcia decyzji. Dodatkowo: przypadki z własnego doświadczenia i syntetyczne — wyłącznie do kalibracji i testów regresyjnych, **nie** do wykazania wartości ([9.2 K1](09-weryfikacja-planu.md#k1-brak-źródła-przypadków-i-użytkowników--dodany-etap-0)).

**Rezultaty:** propozycja dla partnerów, zasady poufności, lista partnerów, rejestr przypadków (`cases/` — bez poufnych treści w repozytorium).

**Warunek przejścia:**

- ≥ 3 PM-ów z ≥ 2 organizacji potwierdziło udział,
- ≥ 6 przypadków z materiałami z chwili decyzji,
- zasady poufności zaakceptowane przez partnerów.

**Jeśli warunku nie uda się spełnić w 6 tygodni:** to sygnał o samym produkcie (PM-owie nie widzą wystarczającej wartości, żeby udostępnić materiały, lub bariera poufności jest za wysoka). Decyzja: zmienić propozycję dla partnerów, zawęzić segment albo wstrzymać projekt.

### Etap 1. Discovery i diagnoza problemu

**Czas: tygodnie 1–2 po Etapie 0**

**Cel:** zrozumieć, gdzie w rzeczywistym procesie produktowym powstają problemy, które PDI miałby rozwiązywać.

**1.1. Rekonstrukcja rzeczywistego procesu** — u każdego partnera prześledzić drogę od pojawienia się inicjatywy do rozpoczęcia realizacji: kiedy zapadają decyzje, jakie informacje są wtedy dostępne, kto je interpretuje, gdzie pojawiają się niewiadome, kiedy wykrywane są sprzeczności, co powoduje powroty do wcześniejszych etapów.

**1.2. Analiza przypadków** — w zebranych inicjatywach szukać sytuacji, w których zmieniono zakres z powodu późno odkrytej informacji, rozwiązanie nie odpowiadało na pierwotny problem, estymacja była nietrafna z powodu brakujących ustaleń, sprzeczność wymaganie–design wykryto późno, dodatkowa analiza zmieniła decyzję.

**1.3. Wywiady** — z PM-ami (rdzeń), a gdzie to możliwe także z designerami, analitykami, developmentem i decydentami biznesowymi. Pytać o konkretne sytuacje, nie o oczekiwania wobec AI: kiedy organizacja nie wiedziała czegoś, co powinna była wiedzieć; miała informacje, ale ich nie połączyła; podjęła decyzję na podstawie błędnej interpretacji; wykryła problem zbyt późno.

**Rezultaty:** mapa procesu (u co najmniej 2 partnerów), lista najważniejszych problemów decyzyjnych z częstością, ocena dostępności danych, **potwierdzenie lub korekta** wybranego procesu pilotażowego (od pojawienia się inicjatywy do decyzji o dalszym postępowaniu) **[M1]**, aktualizacja katalogu wzorców R1–R12.

**Kryterium zakończenia:** potrafimy wskazać konkretny problem, który powtarza się u więcej niż jednego partnera, ma istotne konsekwencje i może być ograniczony przez lepsze łączenie informacji oraz wcześniejsze wykrywanie ryzyka.

### Etap 2. Walidacja koncepcji i przewagi

**Czas: tygodnie 2–4 po Etapie 0** (2.1 może rozpocząć się już w Etapie 0)

**2.1. Analiza konkurencji** — co najmniej cztery kategorie:

| Kategoria | Co sprawdzić |
|---|---|
| Product discovery i product management | Jak narzędzia łączą feedback, badania, strategię i decyzje? |
| Zarządzanie wymaganiami i śledzenie powiązań | Jak wykrywają sprzeczności i analizują wpływ zmian? |
| Asystenci AI do pracy z wiedzą | Czy łączą dowody i rekonstruują uzasadnienie decyzji? |
| Platformy automatyzacji i agentów AI | Czy proaktywnie wykrywają problemy i inicjują działania? |

Punkty wyjścia: Productboard, Jama Connect, funkcje AI w narzędziach do pracy z wiedzą — bez traktowania ich jako pełnej listy. Kryteria porównania z [07 §7.3](07-ryzyka-i-otwarte-pytania.md#73-analiza-konkurencji--do-wykonania).

**Analiza konkurencji rozstrzyga też charakter projektu** (ustalenie: produkt komercyjny, jeśli jest potencjał rynkowy i luka; narzędzie wewnętrzne, jeśli konkurencja jest silna). Żeby ta decyzja nie była intuicyjna, przyjmujemy regułę:

| Wynik | Charakter |
|---|---|
| Żadne narzędzie nie radzi sobie dobrze z ≥ 3 z 6 scenariuszy z 2.2 **i** partnerzy wykazują zainteresowanie dalszym korzystaniem (patrz Etap 5, grupa mierników D) | Kierunek komercyjny — kontynuujemy walidację rynkową |
| Istniejące narzędzia pokrywają większość scenariuszy, ale wariant PDI wygrywa w teście 2.3 | Narzędzie wewnętrzne / metoda pracy — wartość jest, ale nie jako osobny produkt |
| Istniejące narzędzia pokrywają scenariusze, a wariant PDI nie wygrywa w 2.3 | Zatrzymanie lub zmiana koncepcji |

Uwaga: „silna konkurencja” mierzymy pokryciem **scenariuszy**, nie liczbą firm w kategorii. Wiele narzędzi z funkcjami AI nie oznacza, że któreś rozwiązuje ten sam problem.

**2.2. Porównanie na scenariuszach**, nie na listach funkcji: wykrycie nieuzasadnionego założenia, sprzeczności badanie–rozwiązanie, brakującej informacji, propozycja działania zamykającego lukę, wykrycie zmiany podważającej decyzję, ograniczanie niepotrzebnych powiadomień.

**2.3. Test wartości** na 3–6 przypadkach partnerów. Trzy warianty analizy tych samych materiałów:

1. analiza standardowa (PM / zespół),
2. ogólny asystent AI — **te same materiały i sensowny, nie celowo słaby prompt** **[M2]**,
3. „prototyp PDI” = analiza według modelu PDI (schemat LDM + katalog R1–R12 + format Briefa), wykonana przez LLM z ustrukturyzowanym promptem i poprawiona ręcznie (Wizard of Oz) **[M3]**.

Oceniający (partnerzy, nie autor projektu) nie wiedzą, który wariant jest który **[M2]**. Oceniają istotność i trafność wykrytych problemów, zasadność rekomendacji, użyteczność wyników.

**Rezultaty:** mapa konkurencji, lista istniejących funkcji i nierozwiązanych problemów, hipoteza przewagi, wyniki porównania, decyzja o budowie MVP.

**Kryterium zakończenia:** potrafimy wykazać konkretną przewagę wariantu 3 nad wariantem 2 w określonym scenariuszu — a nie tylko opisać produkt jako „bardziej inteligentny” lub „bardziej proaktywny”. Jeśli wariant 2 jest równie dobry, wartość PDI leży w czymś innym niż analiza (np. ciągłość, monitoring, przepływ pracy) — albo jej nie ma.

### Etap 3. Projekt modelu decyzji i architektury

**Czas: tygodnie 4–6 po Etapie 0**

**3.1. Model decyzji** — punkt wyjścia: [schemat LDM](../model/living-decision-model.schema.json). Weryfikacja na przypadkach partnerów: czy pokrywa problem, cel, potrzeby użytkowników, dowody, hipotezy, założenia, decyzje, alternatywy, wymagania, design, ograniczenia, ryzyka, otwarte pytania, wyniki i mierniki sukcesu.

**3.2. Reguły jakości informacji** — rozróżnienie: fakt potwierdzony w źródle, obserwacja, interpretacja, hipoteza, rekomendacja AI, decyzja zatwierdzona przez człowieka; pochodzenie, data aktualizacji, ograniczenia interpretacji, status rekonstrukcji ([02 §2.1](02-living-decision-model.md#21-zasada-epistemiczna--najważniejsza-reguła-modelu)).

**3.3. Architektura** — siedem warstw, z zakresem minimalnym dla MVP **[M4]**:

| Warstwa | Docelowo | W MVP |
|---|---|---|
| 1. Źródła | Dokumenty, wymagania, badania, decyzje, dane | Pliki przekazane przez PM-a |
| 2. Pozyskiwanie | Integracje, import, ekstrakcja | Import plików + ekstrakcja LLM do schematu |
| 3. Wiedza | Dowody i powiązania z historią wersji | Model JSON per inicjatywa + wersjonowanie |
| 4. Analiza | Sprzeczności, luki, ryzyka | Detektory R1–R12 na grafie + ocena LLM + stress test |
| 5. Orkiestracja | Planowanie działań, monitorowanie wyników | Stan luk (KGC) + ponowna analiza po nowym materiale |
| 6. Interakcja | Rekomendacje, pytania, alerty, widok inicjatywy | Brief + rozmowa z Copilotem + prosty widok modelu |
| 7. Kontrola | Uprawnienia, audyt, bezpieczeństwo, ocena jakości | Izolacja danych per partner, log analiz, zbiór testowy |

Nie zakładamy z góry bazy grafowej ani wielu agentów AI. Graf jest modelem pojęciowym; technologię dobieramy do przypadków użycia.

**Rezultaty:** model danych i relacji, prototyp modelu na 2–3 przypadkach, architektura koncepcyjna, zasady kontroli jakości, projekt interakcji z PM-em.

**Kryterium zakończenia:** system potrafi przedstawić inicjatywę jako powiązany zbiór dowodów, hipotez, decyzji i ryzyk, z możliwością sprawdzenia źródeł, a PM-owie potwierdzają ≥ 70% zrekonstruowanych założeń.

### Etap 4. Budowa MVP

**Czas: tygodnie 6–10 po Etapie 0**

**Cel:** działający prototyp rozwiązujący jeden rzeczywisty problem produktowy.

**Zakres — pięć funkcji:**

1. **Evidence Fusion** — ustrukturyzowany obraz: co wiemy, jakie dowody to potwierdzają, jakie założenia przyjęto, czego nie wiemy.
2. **Decision Risk Radar** — sprzeczności, brak uzasadnienia, nieweryfikowane założenia, niezgodność rozwiązania z problemem, brak krytycznych informacji.
3. **Active Copilot** — praca z PM-em, która nie kończy się na odpowiedziach, lecz proponuje kolejne kroki (w tym gotowe prośby do analityki / supportu / badań).
4. **Readiness Assessment** — realizowane jako Decision Readiness Brief, wynik radaru dla konkretnej następnej decyzji; bez osobnego „wyniku gotowości”.
5. **Change Impact Monitor** — w MVP: PM dodaje nowy lub zmieniony materiał, system ocenia jego wpływ na wcześniejsze ustalenia. Automatyczne monitorowanie źródła — dopiero w Etapie 6. **[M5]**

**Poza zakresem MVP:** integracje ze wszystkimi systemami, automatyczne zatwierdzanie decyzji, dashboard zarządczy, pełna automatyzacja workflow, własny model językowy, uczenie się na wynikach portfolio.

**Rezultaty:** działający prototyp, testy na przypadkach partnerów, zbiór przykładów poprawnych i błędnych analiz (zbiór testowy regresji), pierwsza wersja polityki powiadomień, raport z jakości działania.

### Etap 5. Pilotaż i walidacja efektów

**Czas: tygodnie 10–13 po Etapie 0**

**Cel:** sprawdzić, czy system rzeczywiście poprawia jakość decyzji, a nie tylko generuje przekonująco brzmiące analizy.

**Przebieg:** 5–10 inicjatyw partnerów, porównanie z dotychczasowym procesem. Tam, gdzie znany jest późniejszy rezultat — ocena retrospektywna według protokołu z [06 §6.3](06-mvp-i-pilotaz.md#63-protokół-oceny-retrospektywnej) (stan wiedzy z chwili decyzji, zaślepienie oceniających).

Dla każdej inicjatywy: jakie problemy wykrył system; które potwierdzili eksperci; które przeoczył standardowy proces; które rekomendacje doprowadziły do działań; ile trwało rozstrzygnięcie najważniejszych niewiadomych; ile powiadomień było niepotrzebnych; **co PM zrobił inaczej dzięki systemowi** (9.3 pkt 4).

**Zasada:** system, który wskazuje 50 drobnych problemów, może być mniej wartościowy niż taki, który wykrywa jeden istotny błąd przed kosztowną realizacją.

**Rezultaty:** raport z pilotażu, ocena jakości analiz, lista najważniejszych błędów systemu, wyniki testów monitorowania zmian, decyzja o dalszym rozwoju.

### Etap 6. Rozwój w kierunku ciągłej inteligencji organizacyjnej

**Czas: od tygodnia 14 po Etapie 0 — tylko jeśli MVP potwierdzi wartość.**

Kierunki: więcej źródeł i integracji; monitorowanie zmian w czasie zbliżonym do rzeczywistego; grupowanie powiązanych problemów w jeden sygnał; automatyczne wyszukiwanie odpowiedzi w dostępnej wiedzy; kierowanie pytań do właściwych osób; monitorowanie zamykania luk; wpływ zmian na wiele inicjatyw; porównywanie założeń z rezultatami wdrożeń; rozpoznawanie powtarzających się problemów w procesie.

Poziom portfolio wymaga osobnej decyzji o widoczności danych: wnioski organizacyjne oparte na agregatach, nie na ocenie poszczególnych PM-ów (9.3 pkt 3).

Docelowo system wskazuje nie tylko słabości pojedynczej decyzji, ale też organizacyjne przyczyny ich powstawania — np. że w wielu inicjatywach decyzja o rozwiązaniu zapada przed ustaleniem przyczyny problemu.

---

## 4. Harmonogram, punkty kontrolne i kryteria zatrzymania

| Okres | Etap | Główny rezultat | Decyzja na koniec | Zatrzymaj / zmień kierunek, jeśli… **[K2]** |
|---|---|---|---|---|
| Tyg. 0–3 (max 6) | 0. Partnerzy | ≥ 3 PM-ów, ≥ 6 przypadków | Czy mamy na czym walidować? | Po 6 tygodniach brak partnerów lub materiałów |
| Tyg. 1–2 po E0 | 1. Discovery | Rozpoznany problem, potwierdzony proces | Czy problem jest istotny? | Problemy decyzyjne nie powtarzają się lub ich przyczyny leżą poza uzasadnieniem (np. polityka, egzekucja) |
| Tyg. 2–4 | 2. Walidacja | Hipoteza przewagi, wyniki porównania | Czy budować MVP? | Ogólny asystent AI (wariant 2) wypada równie dobrze jak wariant PDI |
| Tyg. 4–6 | 3. Projekt | Model decyzji, architektura | Czy da się wiarygodnie połączyć informacje? | Trafność rekonstrukcji założeń wyraźnie poniżej 70% |
| Tyg. 6–10 | 4. MVP | Działający prototyp | Czy system wykrywa rzeczywiste problemy? | Precyzja ostrzeżeń 2–3 wyraźnie poniżej progu na zbiorze testowym |
| Tyg. 10–13 | 5. Pilotaż | Wyniki na inicjatywach partnerów | Czy rozwiązanie poprawia proces? | PM-owie nie zmieniają działań pod wpływem systemu i nie wracają do niego |
| Tyg. 14+ | 6. Rozwój | Monitorowanie i integracje | Czy skalować? | — |

Progi liczbowe są wstępne ([06 §6.4](06-mvp-i-pilotaz.md#64-metryki)). Mogą zostać skorygowane po zebraniu danych bazowych w Etapie 1, ale **każdy próg musi zostać zapisany w repozytorium przed rozpoczęciem testu, którego dotyczy** — nie po zobaczeniu wyników.

---

## 5. Mierniki sukcesu

### A. Jakość decyzji

- Odsetek istotnych problemów wykrytych przed podjęciem kosztownego działania.
- Odsetek rekomendacji uznanych przez ekspertów za trafne i użyteczne.
- Liczba istotnych problemów przeoczonych przez standardowy proces, a wykrytych przez system.
- Odsetek decyzji, których kluczowe założenia mają wskazane źródła i poziom pewności.

### B. Efektywność procesu

- Czas rozstrzygnięcia istotnych niewiadomych.
- Liczba zmian zakresu wynikających z wcześniej przeoczonych informacji.
- Częstotliwość powrotów do wcześniejszych etapów z powodu braków w przygotowaniu.
- Czas od pojawienia się nowego dowodu do oceny jego wpływu na decyzję.

### C. Jakość działania systemu

- Odsetek istotnych ostrzeżeń potwierdzonych przez ekspertów (precyzja).
- Liczba fałszywych alarmów.
- Odsetek problemów, które system pomógł rozwiązać.
- Liczba niepotrzebnych interakcji wymaganych od użytkownika.
- Trafność rekonstrukcji założeń.

### D. Wartość dla PM-a (nowa grupa, 9.3)

- Odsetek analiz, po których PM zmienił, zawęził lub odroczył decyzję albo zamknął lukę.
- Powroty do systemu przy kolejnej inicjatywie bez zachęty.
- Odsetek próśb przygotowanych przez system (np. do analityki), które PM faktycznie wysłał.

---

## 6. Zespół

| Rola | Odpowiedzialność |
|---|---|
| Product Lead | Wizja, priorytety, decyzje projektowe, relacje z partnerami |
| PM lub ekspert procesowy | Modelowanie procesu, walidacja problemów |
| AI/Backend Engineer | Pozyskiwanie danych, analiza, logika systemu |
| UX/Product Designer | Projekt interakcji, ograniczenie obciążenia użytkownika |
| Ekspert domenowy | Ocena jakości rekomendacji i trafności problemów |
| Bezpieczeństwo (konsultacyjnie) | Dostęp do danych, prywatność, uprawnienia |

**Stan faktyczny: projekt prowadzi jedna osoba.** Autor łączy role Product Leada, PM-a / eksperta procesowego, inżyniera AI i projektanta. Role eksperta domenowego i oceniających pełnią design partnerzy; konsultacja bezpieczeństwa — doraźnie przed Etapem 0 (zasady poufności).

Konsekwencje:

1. **Harmonogram przy jednej osobie** (szacunek, przy pracy w niepełnym wymiarze należy go odpowiednio wydłużyć):

   | Etap | Szacunek przy jednej osobie |
   |---|---|
   | 0. Partnerzy | 3–6 tygodni (zależy od odzewu, nie od pracy) |
   | 1–2. Discovery i walidacja | 4–5 tygodni |
   | 3. Projekt | 2–3 tygodnie |
   | 4. MVP | 6–8 tygodni |
   | 5. Pilotaż | 4–6 tygodni |
   | **Razem po Etapie 0** | **ok. 16–22 tygodni** |

2. **Wizard of Oz jest ograniczony czasem autora.** Jedna ręczna analiza to szacunkowo 4–6 godzin. Przy 6 przypadkach jest to wykonalne; przy większej liczbie trzeba wcześniej zautomatyzować ekstrakcję.
3. **Autor nie może być oceniającym własnego systemu.** Wszystkie oceny trafności i istotności w Etapach 2 i 5 wykonują partnerzy (zaślepieni co do źródła).
4. **Etapy 1 i 2 wykonywane po kolei, nie równolegle** — poza analizą konkurencji (2.1), którą można prowadzić w czasie oczekiwania na odpowiedzi partnerów w Etapie 0.
5. **MVP ma być możliwie najprostszy technicznie** — jeden język, pliki zamiast bazy danych, gotowe API modelu, brak własnej infrastruktury.

Najważniejsze nie jest zbudowanie dużego zespołu technicznego, lecz dostęp do rzeczywistych przypadków i ekspertów potrafiących ocenić, czy system dostarcza wartości.

---

## 7. Największe ryzyka

| Ryzyko | Sposób ograniczenia |
|---|---|
| **Brak design partnerów i przypadków** **[K1]** | Etap 0 z twardym warunkiem przejścia i limitem czasu; [profil partnera](../outreach/profil-design-partnera.md) i [propozycja](../outreach/propozycja-dla-pm.md) |
| **Projekt prowadzi jedna osoba** | Wąski zakres, oceny wykonują partnerzy, analiza konkurencji w czasie oczekiwania na partnerów, proste MVP |
| **Poufność blokuje udostępnienie materiałów** **[K3]** | Zasady poufności i anonimizacji przed rekrutacją |
| **PM odbiera system jako audyt swojej pracy** | Brief prywatny dla PM-a, ton sparingpartnera, PM decyduje o udostępnianiu |
| System generuje przekonujące, ale nieprawdziwe wnioski | Źródła dla istotnych twierdzeń, oznaczanie rekonstrukcji, testy na rzeczywistych przypadkach |
| Zbyt wiele fałszywych alarmów | Priorytetyzacja, ocena istotności, budżet uwagi, testy powiadomień |
| Niska jakość lub niespójność danych | Ograniczony zbiór źródeł na start |
| Brak przewagi nad ogólnym AI | Uczciwe, zaślepione porównanie na tych samych przypadkach (Etap 2.3) |
| Brak zaufania do rekomendacji | Przejrzyste uzasadnienie, weryfikowalne źródła |
| System zwiększa ilość pracy | Pomiar czasu, liczby interakcji i wartości działań |
| Zbyt szeroki zakres MVP | Jeden proces, ograniczone źródła, kilka scenariuszy |
| Przesuwanie poprzeczki przy ocenie własnego pomysłu **[K2]** | Progi zapisane przed testami, oceniający spoza projektu |

Pełna lista założeń nośnych projektu: [07](07-ryzyka-i-otwarte-pytania.md).

---

## 8. Pierwsze pięć dni (dostosowane do braku inicjatyw)

Nie zaczynamy od kodowania ani wyboru technologii.

**Dzień 1 — opisz proces i listę kandydatów.** Opisz typową drogę od pomysłu do refinementu i estymacji (z własnego doświadczenia), zaznacz momenty istotnych decyzji. Profil design partnera jest gotowy: [outreach/profil-design-partnera.md](../outreach/profil-design-partnera.md) — na jego podstawie spisz listę 15–20 kandydatów.

**Dzień 2 — zbierz przypadki z własnego doświadczenia.** Trzy sytuacje, w których brak informacji, sprzeczność lub błędne założenie spowodowały problem. Zaznacz, że to rekonstrukcja z pamięci — przydatna do kalibracji, nie jako dowód wartości.

**Dzień 3 — zrekonstruuj decyzje.** Dla każdego przypadku: co było wiadomo w chwili decyzji, czego nie wiedziano, co odkryto później. Zapisz jeden z nich w schemacie LDM (wzorem `examples/status-zamowienia.yaml`) i sprawdź, czy schemat i katalog R1–R12 go pokrywają.

**Dzień 4 — ręczny test koncepcji.** Na przykładzie z dnia 3 i na `status-zamowienia`: porównaj (a) ogólnego asystenta AI z dobrym promptem i (b) asystenta AI prowadzonego modelem PDI (schemat + katalog wzorców + format Briefa). Zapisz różnice. To pierwsza, wstępna wersja testu z Etapu 2.3.

**Dzień 5 — pierwszy kontakt.** Propozycja ([outreach/propozycja-dla-pm.md](../outreach/propozycja-dla-pm.md)), zasady poufności i szablony wiadomości są gotowe. Uzupełnij miejsca `[…]` (kontakt, dostawca modelu AI) i wyślij do pierwszych 5 kandydatów.

**Rezultat pięciu dni:** krótki dokument z opisem problemu, hipotezą wartości, wynikiem testu z dnia 4, propozycją dla partnerów i listą kontaktów.

---

## 9. Najważniejsza rekomendacja

Na tym etapie nie budujemy jeszcze całego Product Decision Intelligence.

Najpierw sprawdzamy, czy na konkretnym, **prawdziwym** przykładzie system potrafi:

1. połączyć informacje, których zespół wcześniej nie połączył;
2. wykryć istotne zagrożenie dla decyzji;
3. wyjaśnić, dlaczego problem ma znaczenie;
4. zaproponować działanie, które go rozwiąże;
5. rozpoznać, kiedy problem został rozwiązany;
6. nie wymagać ciągłej uwagi użytkownika.

**Celem pierwszego etapu nie jest stworzenie inteligentnego asystenta. Jest nim udowodnienie, że system potrafi wykryć i pomóc rozwiązać problem, który w obecnym procesie zostałby przeoczony albo odkryty zbyt późno.**

Pierwszym warunkiem takiego dowodu jest dostęp do prawdziwych inicjatyw i PM-ów, którzy ocenią wynik — dlatego projekt zaczyna się od Etapu 0.
