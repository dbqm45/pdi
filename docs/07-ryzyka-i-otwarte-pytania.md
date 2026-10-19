# 7. Ryzyka projektu i otwarte pytania

Stosujemy do własnego projektu tę samą zasadę, którą PDI ma stosować wobec inicjatyw: nazywamy założenia nośne i to, co mogłoby je obalić.

## 7.1. Założenia nośne projektu

| # | Założenie | Co by je obaliło | Jak sprawdzić | Status |
|---|---|---|---|---|
| Z1 | Błędne decyzje produktowe w istotnej mierze wynikają z wad uzasadnienia (a nie np. z polityki, egzekucji, zmian rynku) | Analiza nieudanych inicjatyw pokazuje, że przyczyny leżały poza uzasadnieniem | Retrospektywa 10–15 inicjatyw, klasyfikacja przyczyn | hipoteza |
| Z2 | Materiały wystarczają do zrekonstruowania logiki decyzji | Uzasadnienia żyją głównie w rozmowach i głowach; rekonstrukcja jest zgadywaniem | Metryka trafności rekonstrukcji w pilotażu | hipoteza — **największe ryzyko techniczne** |
| Z3 | System znajduje rzeczy, których eksperci nie widzą | Eksperci znajdują wszystko, co system — system tylko przyspiesza | Metryka „wartość dodana” w pilotażu | hipoteza |
| Z4 | Ludzie przyjmą zakwestionowanie swojej decyzji od systemu | Ostrzeżenia odbierane jako atak / biurokracja; system jest ignorowany lub wyłączany | Pilotaż na żywo: reakcje, powroty | hipoteza — **największe ryzyko adopcyjne** |
| Z5 | Połączenie A+B+C wokół decyzji nie jest już oferowane przez istniejące narzędzia | Konkurencja (lub funkcje AI w Productboard/Jira/Notion) pokrywa tę wartość | Analiza konkurencji (patrz 7.3) | **niezweryfikowane** |

## 7.2. Główne ryzyka

**Ryzyko „wymyślonego uzasadnienia”.** System zrekonstruuje hipotezę, której zespół nigdy nie przyjął, i zbuduje na niej ostrzeżenie. Mitygacja: pochodzenie `reconstructed` vs `confirmed`, niższa wiarygodność dla rekonstrukcji, komunikat w formie pytania („Czy decyzja zakłada X?”), metryka trafności rekonstrukcji.

**Ryzyko teatru jakości.** Zespoły uczą się „karmić” system dokumentami tak, żeby radar był zielony, zamiast lepiej rozumieć problem. Mitygacja: brak jednego wyniku, brak bramek, nacisk na luki nośne zamiast kompletności; obserwować w pilotażu.

**Ryzyko szumu.** Za dużo trafnych, ale nieistotnych uwag → system jest ignorowany. Mitygacja: Attention Intelligence, budżet uwagi, precyzja jako metryka progowa.

**Ryzyko polityczne.** Ujawnianie słabego uzasadnienia decyzji kierownictwa. Do ustalenia: kto widzi Briefy, czy są prywatne dla właściciela decyzji do momentu udostępnienia, jak komunikować krytykę decyzji podjętych wyżej.

**Ryzyko danych i uprawnień.** Tryb Guardian wymaga szerokiego dostępu do źródeł; ryzyko ujawnienia informacji osobom bez uprawnień przez wnioski łączone z wielu źródeł. Model uprawnień musi dziedziczyć uprawnienia źródeł — także dla wniosków pochodnych.

**Ryzyko fałszywej pewności.** Użytkownik traktuje brak ostrzeżeń jako dowód, że decyzja jest dobra. Mitygacja: Brief zawsze pokazuje zakres analizy (jakie źródła widział system, jakich nie).

## 7.3. Analiza konkurencji — do wykonania

Dotychczasowe odniesienia do rynku (Productboard — AI w product discovery; Jama Connect — traceability i analiza wpływu zmian; podejścia „AI-native product discovery”) pochodzą z wcześniejszej rozmowy i **nie zostały zweryfikowane** w tym repozytorium (odnośniki źródłowe nie zachowały się).

Do zrobienia w Etapie 0–2 [planu](08-plan-projektu.md):

- [ ] Mapa: narzędzia discovery (Productboard, Dovetail, Enterpret, …), traceability (Jama, Polarion, …), decision records / ADR, funkcje AI w Jira/Confluence/Notion/Linear.
- [ ] Dla każdego: czy modeluje **decyzję** jako obiekt? czy rozróżnia fakt/hipotezę? czy kwestionuje decyzje? czy ocenia proporcjonalność do stawki? czy działa w tle?
- [ ] Wnioski: gdzie realnie jest luka i czy jest wystarczająco duża, by na niej budować.

## 7.4. Otwarte pytania produktowe

1. ~~**Dla kogo pierwszego?**~~ **Rozstrzygnięte:** PM jako właściciel decyzji. Konsekwencje: [09 §9.3](09-weryfikacja-planu.md#93-konsekwencje-wyboru-pm-jako-właściciel-decyzji).
2. **Gdzie żyje system?** Osobna aplikacja, czy warstwa w istniejących narzędziach (komentarz w Confluence, panel w Jira, bot w Slacku)? Hipoteza: Guardian powinien żyć tam, gdzie ludzie już pracują.
3. **Kto utrzymuje model?** Jeśli wymaga ręcznego potwierdzania rekonstrukcji — jak ograniczyć ten koszt do minimum?
4. ~~**Jaki kontekst pilotażu?**~~ **Rozstrzygnięte:** brak dostępu do inicjatyw. Rozwiązanie: Etap 0 — design partnerzy ([plan](08-plan-projektu.md#etap-0-design-partnerzy-i-przypadki-k1-k3)).
6. **Charakter projektu:** produkt komercyjny, narzędzie wewnętrzne czy projekt badawczy? Zmienia kryteria walidacji przewagi.
7. **Skąd design partnerzy?** Sieć kontaktów, społeczności PM, poprzedni pracodawcy?
5. **Jak domyślnie traktować widoczność Briefów?** (patrz ryzyko polityczne)

## 7.5. Proponowane następne kroki

Zastąpione planem projektu: [08-plan-projektu.md](08-plan-projektu.md), zaczynając od sekcji 8 („Pierwsze pięć dni”).
