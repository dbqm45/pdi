# Raport z testu v2 — pamięć uzasadnienia decyzji

```
Test: v2-pamiec-decyzji | data: 2026-10-19 | powtórzeń: 3
Generowanie: Claude (model „sonnet”, ten sam dla wszystkich wariantów), każda rozmowa jako osobny agent bez dostępu do klucza
Ocena: sędzia LLM (Claude, model sesji głównej — inny niż generujący), jeden sędzia na przebieg (4 tygodnie)
Przebiegi: 12 (4 warianty × 3) · 54 odpowiedzi · 12 kart ocen
```

Surowe odpowiedzi: [surowe/](surowe/) (`<wariant>-<nr>-T<tydzień>.md`; `B-*-T0.md` to zapisane modele decyzji) · Karty ocen z cytatami: [oceny/](oceny/)

## Werdykt w jednym akapicie

Pamięć uzasadnienia decyzji daje przewagę **dokładnie tam, gdzie przewidział profil sygnałów** — przy sygnale, którego znaczenie zależy od liczb w uzasadnieniu (aneks do umowy z przewoźnikiem → rachunek progu darmowej dostawy). Warianty z pamięcią (B, A-ctx) wykryły go w pełni w 3/3 przebiegów i policzyły, że decyzja przestaje się opłacać; warianty bez pamięci (A-fresh, A+) — w 0/3, bo „nie mają dostępu do uzasadnienia”. Pozostałe dwa sygnały wykryły wszystkie warianty. W efekcie różnica w sumie punktów to 1 pkt, poniżej progów zapisanych przed testem: **K1 spełnione; K2, K3 i K4 niespełnione.** Drugie ważne ustalenie: **szum ogranicza metoda, nie pamięć** — wariant z metodą bez pamięci (A+) miał 0 fałszywych alarmów, a prototyp PDI (B) przez pamięć bywał nadwrażliwy.

## Wyniki zbiorcze

| Miara | A-ctx | A-fresh | A+ | B |
|---|---|---|---|---|
| Pamięć / metoda | tak / nie | nie / nie | nie / tak | tak / tak |
| **Sygnały, średnio (max 6)** | **6,0** | **5,0** | **5,0** | **6,0** |
| Sygnały, rozrzut | 6–6 | 5–5 | 5–5 | 6–6 |
| **S1 aneks → D1, pełne** (zależność od pamięci: wysoka) | **3/3** | **0/3** | **0/3** | **3/3** |
| S2 INT-233 → D2, pełne (średnia) | 3/3 | 3/3 | 3/3 | 3/3 |
| S3 brief CZ → D3, pełne (niska–średnia) | 3/3 | 3/3 | 3/3 | 3/3 |
| Bonus B1: aneks + wynik A/B razem | 3/3 | 0/3 | 0/3 | 3/3 |
| FA, średnio | 0,67 | 2,67 | **0** | 1,33 |
| DUP, średnio | 1,0 | 1,0 | **0** | 0,33 |
| FA + DUP | 1,67 | 3,67 | **0** | 1,67 |
| Obciążenie (pozycje „wymaga uwagi” w 4 tyg.), średnio | 7,7 | 10,0 | **5,0** | 5,7 |
| Wykrycie w tygodniu pojawienia się sygnału | 9/9 | 9/9 | 9/9 | 9/9 |

Wyniki per przebieg (sygnały / bonus / FA / DUP / obciążenie):
- A-ctx: 6/1/1/1/7 · 6/1/1/1/7 · 6/1/0/1/9
- A-fresh: 5/0/3/1/10 · 5/0/3/1/11 · 5/0/2/1/9
- A+: 5/0/0/0/5 · 5/0/0/0/5 · 5/0/0/0/5
- B: 6/1/2/1/7 · 6/1/1/0/5 · 6/1/1/0/5

## Werdykt względem kryteriów

| Kryterium | Spełnione? | Wartość |
|---|---|---|
| K1 — B działa (≥ 4/6 w ≥ 2/3; FA ≤ 2) | **tak** | 6/6 w 3/3; FA średnio 1,33 |
| K2 — B − A-fresh ≥ 2 | **nie** | 1,0 |
| K3 — B − A+ ≥ 1,5 | **nie** | 1,0 |
| K4 — mniej szumu (FA+DUP ≤ A-fresh i ≤ A+; obciążenie ≤ 5) | **nie** | B 1,67 ≤ A-fresh 3,67, ale > A+ 0; obciążenie 5,7 > 5 |

**Interpretacja według tabeli z README:** wiersz „K2 niespełnione → ogólny asystent bez pamięci wiąże ukryte sygnały z decyzjami równie dobrze; hipoteza pamięci obalona na tym przypadku”. W dosłownym brzmieniu reguły — tak. Zastrzeżenie poniżej.

## Co ten wynik znaczy

**1. Reguła mówi „obalone”, ale profil sygnałów pokazuje, gdzie pamięć działa.** Przed testem zapisano, że tylko S1 silnie zależy od pamięci, a S2 i S3 częściowo da się wykryć bez niej. Dokładnie tak wyszło: S2 i S3 wykryli wszyscy, S1 tylko warianty z pamięcią. Przy takim profilu maksymalna możliwa różnica w sumie wynosiła ok. 1 pkt na przebieg (S1: 2 vs 1) — **próg K2 = 2 pkt był nieosiągalny przy tej konstrukcji testu**. To błąd projektu kryteriów (powinny być liczone dla sygnałów zależnych od pamięci), a nie dowód, że pamięć nic nie daje. Kryteriów nie zmieniamy po fakcie — raportujemy oba odczyty.

**2. Bez pamięci asystent sam mówi, czego mu brakuje.** A+: „Nie mam dostępu do uzasadnień (business case) tych decyzji”. A-fresh: uzasadnienie „zakładało prawdopodobnie stare stawki”. Wariant z pamięcią: „cały zapas 22 600 zł znika, wynik ok. −4 000 zł miesięcznie”. Różnica jakościowa jest duża: PM bez pamięci dostaje polecenie „przelicz business case”, z pamięcią — odpowiedź, że decyzja przestała się opłacać, zanim weszła w życie.

**3. Szum ogranicza metoda, a pamięć potrafi go zwiększyć.** A+ (poziomy 0–3, zasada „zbędne powiadomienie to błąd”, bez pamięci) — 0 fałszywych alarmów, 0 duplikatów, 5 pozycji w 4 tygodnie. A-fresh bez metody — 10 pozycji. B miał FA głównie na wyniku testu A/B (poziom 3 zamiast ≤ 2): **znając „cienki” rachunek decyzji, reagował zbyt mocno na niewielkie odchylenie**. Pamięć bez kalibracji progu istotności zamienia się w nadwrażliwość.

**4. Zdyscyplinowany PM z jedną długą rozmową (A-ctx) osiąga to samo co B** w wykrywaniu sygnałów, przy nieco większym szumie (7,7 vs 5,7 pozycji). Przewaga PDI nad A-ctx w tym teście jest mała — sprowadza się do tego, czy PM rzeczywiście prowadzi jedną rozmowę przez miesiąc i wkleja do niej wszystko, co pojawia się w firmie.

**5. „Pamięć” w prototypie to plik JSON.** Wariant B to prompt + zapisany model decyzji przekazywany między rozmowami. To, co dało przewagę przy S1, jest technicznie proste do odtworzenia — co ma znaczenie dla pytania „produkt czy narzędzie” (niżej).

## Odstępstwa od procedury

- **Kalibracja oceną człowieka nie została wykonana** (README zakładało ręczną ocenę 4 przebiegów przez autora). Zamiast tego orkiestrator testu sprawdził wyrywkowo sygnał S1 w czterech przebiegach (A-fresh-1, A+-1, B-2, A-ctx-1) — oceny sędziów były zgodne z treścią odpowiedzi. To nie zastępuje kalibracji przez człowieka.
- Sędziowie nie znali modelu generującego (wpisywali „nieznany”) — zgodnie z intencją, ale niezgodnie z polem w karcie.
- Kilka ocen granicznych (FA dla P1 na poziomie 3, duplikaty INT-233, obciążenie przy pozycjach „niski priorytet”) — opisane w kartach; żadna nie zmienia werdyktu K1–K4.

## Ograniczenia

- Generator i sędzia to modele tej samej rodziny; brak oceny człowieka.
- Przypadek syntetyczny, zaprojektowany przez autora metody; trzy sygnały na 28 dokumentów to gęstość wyższa niż w realnej organizacji.
- Wariant A-fresh dostawał nazwy i terminy inicjatyw w każdym prompcie — to hojne założenie o pamięci PM-a; w praktyce mogłoby być gorzej.
- Wariant A-ctx miał wklejane wszystkie dokumenty firmy co tydzień — w praktyce PM nie widzi i nie wkleja wszystkiego; test nie mierzy, które dokumenty PM w ogóle by zauważył.

## Wnioski

**Dla propozycji wartości:**
1. Węższa, ale potwierdzona na tym przypadku wartość: **strażnik rachunku i warunków decyzji** — wykrywa informacje, które unieważniają liczby lub warunki, na których oparto decyzję, i podaje skutek (np. „decyzja przestaje się opłacać”), a nie tylko „sprawdź”. Ogólny asystent bez pamięci tego nie robi.
2. Ochrona uwagi wynika z metody (poziomy, zasada kosztu zbędnego powiadomienia) i działa bez pamięci. Pamięć trzeba połączyć z kalibracją progu, inaczej B będzie nadwrażliwy przy decyzjach z cienkim marginesem.
3. **Kluczowe pytanie do design partnerów:** jak często w realnej organizacji pojawiają się informacje typu S1 — zmieniające liczby lub warunki decyzji, nie wspominając jej — i ile kosztowało ich późne wykrycie. Od odpowiedzi zależy, czy ta wąska wartość wystarcza.

**Dla decyzji „produkt komercyjny czy narzędzie wewnętrzne”:** przewaga pochodzi z prostego mechanizmu (zapisany model decyzji w pliku + prompt z metodą). Taki mechanizm łatwo odtworzyć — także dostawcom narzędzi (Productboard Spark, ProdPad) i samym PM-om (skill, projekt w asystencie AI). Wynik **przesuwa rekomendację w stronę narzędzia wewnętrznego / skilla**, a nie osobnego produktu, chyba że wywiady pokażą, że wartość leży w czymś trudniejszym do skopiowania (automatyczne zasilanie z wielu źródeł firmy, zarządzanie wieloma decyzjami i PM-ami, kalibracja na wynikach decyzji).

**Dla następnych kroków (do decyzji właściciela projektu):**
- Zaktualizować propozycję wartości do „strażnika rachunku i warunków decyzji” i przepisać [propozycję dla PM-ów](../../../outreach/propozycja-dla-pm.md).
- W wywiadach z partnerami zebrać przykłady sygnałów typu S1 z ich organizacji — to jednocześnie dane do testu v3 na prawdziwych materiałach.
- Poprawić prompt B: przejąć kalibrację szumu z A+ i dodać regułę „odchylenie mniejsze niż X% założenia = poziom ≤ 1”.
- Przy kolejnym teście liczyć kryteria osobno dla sygnałów zależnych i niezależnych od pamięci.
