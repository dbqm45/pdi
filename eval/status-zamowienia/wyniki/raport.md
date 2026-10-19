# Raport z testu praktycznego — status zamówienia

```
Test: status-zamowienia | data: 2026-10-19 | powtórzeń: 3
Generowanie: Claude (model „sonnet”, ten sam dla A i B), każdy przebieg jako osobny agent bez dostępu do klucza
Ocena: sędzia LLM (Claude, model sesji głównej — inny niż generujący), jeden przebieg = jeden sędzia, z kluczem i kartą oceny
Warianty: A (ogólny asystent, dobry prompt), B (prototyp PDI)
```

Surowe odpowiedzi: [surowe/](surowe/) · Karty ocen z cytatami: [oceny/](oceny/)

## Werdykt w jednym akapicie

Na tym przypadku **ogólny asystent AI z dobrym promptem wypadł tak samo jak prototyp PDI** — w rundzie 1 oba warianty dostały maksimum we wszystkich przebiegach, w rundzie 2 różnica wynosi 0,33 pkt. Według kryteriów zapisanych przed testem: **K1 i K4 spełnione, K2 i K3 niespełnione**. Główną przyczyną jest **efekt sufitu**: przypadek okazał się za łatwy dla obecnych modeli, a dokument 09 w rundzie 2 sam wyjaśniał swój związek z decyzją. Jedyna wyraźna różnica jest jakościowa i nie była zapisana w kryteriach: tylko wariant z zapisanym modelem decyzji (B-R2) **we wszystkich 3 przebiegach** wprost nazwał podważone założenie decyzji; ogólny asystent bez kontekstu (A-R2c) **w żadnym** — w dwóch przebiegach uznał, że inicjatywa nie jest podważona.

## Wyniki zbiorcze

| Miara | A | B | Uwagi |
|---|---|---|---|
| R1: średnia suma (max 16) | **16,0** | **16,0** | |
| R1: rozrzut (min–max z 3) | 16–16 | 16–16 | efekt sufitu |
| W1 pełnie — pass^3 | 3/3 | 3/3 | |
| W2 pełnie (≥ 2 sygnały) — pass^3 | 3/3 | 3/3 | oba warianty łączyły sygnały z 4 dokumentów |
| W3 pełnie — pass^3 | 3/3 | 3/3 | |
| R1: średnia liczba fałszywych alarmów | 0 | 0 | F2 (KR 2.2) oba warianty wprost odrzucały |
| R1: trafne zgłoszenia spoza klucza (na przebieg) | 5–7 | 5 | m.in. „KR 1.1 wymaga ok. 48% mniej kontaktów o status”, „ORD-412 daje datę kolejnego etapu, a klienci chcą daty dostawy” |
| R2: N1–N3 średnio (max 6) | A-R2a: **6,0** · A-R2c: **5,67** | B-R2: **6,0** | |
| R2: sam powiązał 09 z decyzją bez pytania | A-R2a: 3/3 | 3/3 | A-R2b (pytanie uzupełniające) nie było potrzebne |
| R2: wprost nazwał podważone założenie decyzji *(obserwacja po teście, poza kryteriami)* | A-R2a: 3/3 · **A-R2c: 0/3** | **3/3** | A-R2c-3: „Inicjatywa nie jest podważona”; A-R2c-1: „Nie ma powodu, żeby przerywać budowę panelu” |
| R2: N4 zaliczone (brak ostrzeżenia o dok. 10) | A-R2a: 2/3* · A-R2c: 3/3 | 3/3 | *A-R2a-1 sporny — patrz „Odstępstwa” |
| Czas generowania przebiegu R1 | ok. 105–150 s | ok. 100–155 s | czas agentów, nie czas pracy PM-a |

Zgodność z drugim oceniającym: **nie mierzona** — oceniał tylko sędzia LLM, bez kalibracji do ocen człowieka (patrz ograniczenia).

## Werdykt względem kryteriów z README

| Kryterium | Spełnione? | Dowód |
|---|---|---|
| K1 — metoda działa (B: W1, W2 pełnie ≥ 2/3; W3 ≥ częściowo; ≤ 1 FA) | **tak** | B: 16/16 w 3/3, 0 FA |
| K2 — łączenie informacji (B wykrywa W2 pełnie częściej niż A) | **nie** | remis 3/3 vs 3/3 — A łączy sygnały równie dobrze |
| K3 — przewaga ciągłości (B-R2: N1 ≥ 2/3 i średnia o ≥ 2 pkt wyższa niż A-R2c) | **nie** | N1 3/3 spełnione, ale różnica 6,0 − 5,67 = 0,33 pkt |
| K4 — szum (B-R2: N4 ≥ 2/3) | **tak** | 3/3; dokument 10 zawsze poziom 0 |

**Interpretacja według tabeli z README:** wiersz „K3 niespełnione → zatrzymać się i przemyśleć propozycję wartości przed Etapem 0”. Szczegóły i zastrzeżenie — niżej.

## Co ten wynik znaczy

**1. Jednorazowa analiza nie jest wyróżnikiem — potwierdzone mocniej, niż zakładaliśmy.** Ogólny asystent z dobrym promptem wykrył wszystkie zaszyte problemy, połączył sygnały rozproszone w czterech dokumentach, nie dał się złapać na żadną pułapkę i dodał kilka trafnych uwag spoza klucza. Ustalenie U2 z analizy konkurencji jest teraz poparte testem, nie tylko oceną.

**2. Reakcja na nowe informacje w tej samej rozmowie też nie jest wyróżnikiem.** A-R2a (kontynuacja rozmowy, bez pytania) we wszystkich przebiegach sam powiązał nowy dokument z decyzją. Dopóki PM ma kontekst w jednej rozmowie, ogólny asystent wystarcza.

**3. Różnica pojawia się dopiero, gdy kontekst ginie — i jest jakościowa.** Bez materiałów z rundy 1 (A-R2c) asystent poprawnie odczytał nowe dane, ale **nie mógł powiedzieć, że podważają one uzasadnienie decyzji**, bo go nie znał. Dwa z trzech przebiegów doszły do wniosku przeciwnego niż klucz („inicjatywa nie jest podważona”). Wariant z zapisanym modelem decyzji trzy razy na trzy wskazał wprost: „podważa założenie nośne decyzji”. Klucz tej różnicy nie wychwycił (N1 dawało 2 pkt za samo powiązanie dokumentu z panelem) — to słabość klucza, opisana niżej.

**4. Test nie miał siły rozróżniania.** Wynik 16/16 we wszystkich przebiegach rundy 1 oznacza, że przypadek nie odróżnia wariantów (saturacja w terminologii skilla `ai-evals`). Dokument 09 sam opisywał związek opóźnień z kontaktami — nie trzeba było pamiętać decyzji, żeby zrozumieć, że jest ważny. Wynik „remis” jest więc w dużej części wynikiem konstrukcji testu.

## Odstępstwa od procedury

- **Oceniający:** wszystkie oceny wykonał sędzia LLM (zamiast autora + sędzia jako drugi oceniający). Brak kalibracji do ocen człowieka.
- **N4 w A-R2a-1:** sędzia uznał komentarz o dokumencie 10 za fałszywy alarm F6, sam określając to jako przypadek graniczny. W A-R2a-2 i A-R2c-2/3 sędziowie podobne komentarze zaliczyli. Komentarz brzmi: „Zmiany są sensowne i niewinne […] Ale «Brak zmian w zakresie funkcjonalnym» to dokładnie ten problem” — zarzut wynika z dokumentu 09 (brak stanu „dane nieaktualne”), nie z treści dokumentu 10. Ocena sporna; nie wpływa na kryteria (K4 dotyczy B).
- **Obserwacja „wprost nazwał podważone założenie”** nie była kryterium zapisanym przed testem. Raportuję ją osobno jako ustalenie po teście, nie jako spełnienie K3.
- **A-R2b nie wykonano** — nie było potrzebne (A-R2a reagował sam we wszystkich przebiegach).

## Ograniczenia

- Generator i sędzia to modele tej samej rodziny (Claude) — sędzia może podzielać styl rozumowania generatora.
- Autor klucza (orkiestrator testu) zna metodę PDI; klucz mógł nieświadomie odzwierciedlać to, co metoda łatwo wykrywa — a mimo to ogólny asystent wykrył to samo.
- Przypadek syntetyczny, jeden, krótki (10 dokumentów, ok. 2 strony każdy). W tej skali cała wiedza mieści się w jednym prompcie — a to właśnie warunek, w którym ogólny asystent jest najsilniejszy.
- Format odpowiedzi B zdradzał wariant; sędziowie wiedzieli, czy oceniają Brief z JSON.

## Wnioski i zmiany

**Dla propozycji wartości** (to jest rzeczywisty wynik testu, mimo efektu sufitu):
- Wartości PDI nie da się bronić jakością pojedynczej analizy ani reakcją na nowy dokument w tej samej rozmowie. Robi to dziś ogólny asystent z dobrym promptem.
- Jedyny kandydat na wyróżnik, który test pokazał, to **pamięć uzasadnienia decyzji w czasie**: system wie, *dlaczego* zdecydowano, więc potrafi powiedzieć, że nowa informacja to uzasadnienie podważa — także wtedy, gdy PM nie ma już kontekstu i nie wkleja materiałów. To jest węższe i bardziej konkretne niż pierwotna wizja „Decision Risk Radar jako główna wartość”.
- Do sprawdzenia, czy to wystarczy jako produkt: **jak często w praktyce PM traci kontekst decyzji** (zmiana osoby, upływ tygodni, wiele równoległych inicjatyw, informacje przychodzące z miejsc, których PM nie obserwuje). To pytanie do wywiadów z design partnerami — dopisane do Etapu 1.

**Dla testu (wersja 2):**
1. **Trudniejsza runda 2:** nowa informacja, której związek z decyzją **nie wynika z niej samej** — np. notatka z umowy z przewoźnikiem o zmianie API, zmiana procesu w magazynie, ticket inżynierski o kolejce webhooków. Bez pamięci uzasadnienia nie da się jej powiązać z panelem.
2. **Skala:** 30–60 dokumentów i strumień nowych dokumentów, w większości nieistotnych — test S6 (szum) i sytuacji, w której PM nie wkleja wszystkiego do jednej rozmowy.
3. **Klucz:** N1 pełne tylko za wprost nazwane podważone założenie decyzji (nie za samo powiązanie dokumentu z inicjatywą); N4 doprecyzować — „komentarz o dokumencie 10 wynikający z innego dokumentu nie jest fałszywym alarmem”.
4. **Wariant A+** (prompt A + katalog R1–R12, bez modelu decyzji), żeby oddzielić wpływ katalogu od wpływu trwałego modelu.
5. **Ocena człowieka** na co najmniej 5 przebiegach do kalibracji sędziego.

**Decyzja do podjęcia przez właściciela projektu:** reguła z README każe przy niespełnionym K3 zatrzymać się i przemyśleć propozycję wartości przed Etapem 0. Rekomendacja: **potraktować to dosłownie, ale wąsko** — zawęzić propozycję wartości do „pamięci i obrony uzasadnienia decyzji w czasie” i sprawdzić ją testem w wersji 2 **przed** wysłaniem propozycji do design partnerów, bo obecna propozycja ([outreach/propozycja-dla-pm.md](../../../outreach/propozycja-dla-pm.md)) obiecuje głównie jednorazową analizę — czyli dokładnie to, co test pokazał jako łatwo zastępowalne.
