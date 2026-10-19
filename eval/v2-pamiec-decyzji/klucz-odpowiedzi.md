# Klucz odpowiedzi v2 — NIE WKLEJAĆ do testowanych narzędzi

> Wklejenie tego pliku (albo nazw sygnałów z niego) do promptu unieważnia przebieg.

Jednostką oceny jest **cała sekwencja czterech tygodni** jednego przebiegu (wariant × powtórzenie). Sędzia widzi wszystkie cztery odpowiedzi tygodniowe danego przebiegu.

## Decyzje i ich założenia nośne (stan T0)

| Decyzja | Założenie nośne / warunek sensowności | Gdzie zapisane |
|---|---|---|
| **D1** próg darmowej dostawy 99 zł | Średni koszt paczki 11,80 zł (X 12,00 zł / Y 11,40 zł); wynik decyzji tylko ok. +22,6 tys. zł/mies. — „cienki” | t0/02 |
| **D2** panel statusu (zawężony) | Zdarzenia od przewoźników są aktualne (Y po naprawie webhooków: mediana 1,5 h); oś czasu zawiera „w doręczeniu”; data dostawy z SLA | t0/03 |
| **D3** wycofanie płatności za pobraniem z **wspólnego** checkoutu od 2027-02-01 | Udział pobrania 4,1% (rynek polski); jeden rynek | t0/04, t0/05 |

## Sygnały zaszyte (powinny zostać wykryte)

Żaden z tych dokumentów nie wspomina decyzji, której dotyczy. Związek widać tylko, jeśli zna się uzasadnienie decyzji.

| ID | Tydzień / plik | Co podważa | Pełne (2 pkt) | Częściowe (1 pkt) | 0 pkt |
|---|---|---|---|---|---|
| **S1** | 4 / `03-aneks-umowy-przewoznik-x.md` | **D1**: koszt paczki rośnie (dopłata 9% + paczki ciężkie 19,90 zł przy 14% udziale). Rachunek: średni koszt ok. 13,28 zł (+1,48 zł), 18 tys. paczek → +26,6 tys. zł/mies. > 22,6 tys. zł zysku → **decyzja przestaje się opłacać** (ok. −4 tys. zł/mies.) | Wiąże aneks z decyzją o progu **i** wskazuje, że wzrost kosztu jest porównywalny z zakładanym zyskiem decyzji lub go przewyższa (liczbowo albo z odwołaniem do „cienkiego” wyniku z uzasadnienia); oznacza jako wymagające uwagi (poziom 2–3 lub odpowiednik). Ogólne „wzrosną koszty darmowej dostawy / sprawdź opłacalność” bez odniesienia do rachunku decyzji = 1 pkt | Wiąże aneks z kosztami darmowej dostawy ogólnie, bez wskazania, że rachunek decyzji może stać się ujemny / bez priorytetu | Brak powiązania z D1 |
| **S2** | 3 / `06-INT-233-api-przewoznika-y.md` | **D2**: od 12/15.12 zdarzenia Y odświeżane co ok. 12 h (zamiast ok. 1,5 h), brak „w doręczeniu” — panel (release 10.12) pokaże nieaktualne dane dla ok. 35% paczek i niepełną oś czasu; to dokładnie warunek, od którego zależał sens panelu | Wiąże INT-233 z panelem **i** wskazuje utratę aktualności danych / brak etapu „w doręczeniu” jako podważenie warunku decyzji; poziom 2–3 | Wiąże z panelem tylko technicznie (np. „trzeba zmapować statusy”), bez wskazania, że podważa sens / metrykę panelu | Brak powiązania |
| **S3** | 1 / `04-brief-kampanii-cz.md` | **D3**: wejście do CZ (2027-03-01), gdzie pobranie to ok. 30% płatności; checkout wspólny → wyłączenie pobrania 2027-02-01 obejmie CZ; założenie „4,1%, jeden rynek” przestaje obowiązywać | Wiąże brief z decyzją o wycofaniu pobrania **i** wskazuje konflikt (wspólny checkout / inny udział na rynku CZ); poziom 2–3 | Zauważa znaczenie pobrania w CZ, ale bez powiązania z decyzją D3 lub bez wniosku | Brak powiązania |

**Bonus B1 (+1 pkt, maks. 1):** w tygodniu 4 łączy aneks (S1) z wynikiem rozszerzonego testu A/B z tygodnia 2 (niższy efekt +5,8% zamiast +6,1%, niższa wartość koszyka) jako dwa czynniki obniżające wynik D1.

Suma sygnałów: **max 6** (+1 bonus).

## Dokumenty, które NIE powinny wywołać ostrzeżenia

Fałszywy alarm (FA) = dokument oznaczony jako wymagający działania PM-a / poziom 2–3 / „wymaga Twojej uwagi” z sugestią zmiany decyzji.

| ID | Tydzień / plik | Dlaczego to pułapka | Dopuszczalna reakcja |
|---|---|---|---|
| **P1** | 2 / `05-wyniki-ab-prog-dostawy.md` | Potwierdza założenie D1 (z nieco niższym efektem) | Poziom 0–1, zdanie „potwierdza / lekko osłabia” — **poziom 2 dopuszczalny, jeśli wskazuje cieńszy wynik D1**; FA, jeśli twierdzi, że sam podważa decyzję |
| **P2** | 2 / `02-incydent-blik.md` | Kusi powiązaniem z D3 (klienci mają przejść na BLIK), ale to jednorazowy incydent przy deklarowanej dostępności 99,95% | Poziom 0–1 (np. „warto pamiętać przy D3”); FA, jeśli zaleca ponowną ocenę D3 |
| **P3** | 3 / `03-przewoznik-x-etykiety.md` | Wspomina przewoźnika X, ale zmienia tylko wygląd etykiet („brak zmian w cenniku”) | Poziom 0; FA przy jakimkolwiek ostrzeżeniu |
| **P4** | 4 / `01-konkurent-prog-dostawy.md` | Dotyczy progu dostawy, ale nie podważa rachunku D1 (konkurent: tylko automaty paczkowe) | Poziom 0–1 (obserwacja rynkowa); FA, jeśli zaleca zmianę D1 na tej podstawie |

**Duplikat (DUP):** tydzień 4 / `06-sprint-review-integracje.md` ponownie wspomina INT-233. Ponowne pełne ostrzeżenie o tej samej sprawie, bez nowej informacji = 1 duplikat (miara szumu, nie FA). Krótkie „bez zmian w sprawie INT-233” — nie jest duplikatem.

**Pogranicze (bez kary):** tydzień 2 / `06-magazyn-inwentaryzacja.md` (przesunięcie wysyłek 28–30.12 wpływa na datę dostawy w panelu D2) i tydzień 2 / `01-design-system-v4.md` (komponent Timeline) — reakcja poziomu 0–2 jest poprawna, poziom 3 = FA.

Pozostałe 18 dokumentów to szum: każde ostrzeżenie (poziom 2–3 / „wymaga uwagi”) = FA.

## Miary na przebieg

| Miara | Definicja |
|---|---|
| **Sygnały** | S1 + S2 + S3 (0–6) + B1 (0–1) |
| **FA** | liczba fałszywych alarmów w 4 tygodniach (P1–P4, szum, pogranicze na poziomie 3) |
| **DUP** | liczba duplikatów |
| **Obciążenie** | liczba wszystkich pozycji oznaczonych jako wymagające uwagi PM-a w 4 tygodniach (idealnie: 3, maks. rozsądne: 5) |
| **Opóźnienie** | dla każdego wykrytego sygnału: czy w tygodniu, w którym się pojawił (tak / później) |
