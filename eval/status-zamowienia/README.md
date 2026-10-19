# Test praktyczny: panel statusu zamówienia

Pierwszy praktyczny test koncepcji PDI na przygotowanym przypadku. Odpowiada dniu 4 z [pierwszych pięciu dni planu](../../docs/08-plan-projektu.md#8-pierwsze-pięć-dni-dostosowane-do-braku-inicjatyw) i jest próbą generalną testu z Etapu 2.3.

## Co test ma na celu

Test odpowiada na cztery pytania. Każde wynika z wcześniejszych ustaleń projektu.

| # | Pytanie | Skąd się wzięło | Co rozstrzyga |
|---|---|---|---|
| **1** | **Czy metoda PDI w ogóle działa?** Czy model językowy prowadzony modelem decyzji, katalogiem wzorców R1–R12 i formatem Briefa wykrywa zaszyte w materiałach problemy, nie zgłaszając fałszywych alarmów? | Do tej pory metoda istniała tylko na papierze ([03](../../docs/03-decision-risk-radar.md)) | Czy schemat, katalog i prompt nadają się do pokazania design partnerom, czy trzeba je najpierw poprawić |
| **2** | **Czy PDI łączy rozproszone informacje lepiej niż ogólny asystent AI?** Kluczowy problem (nieaktualne statusy) nie jest nigdzie zapisany wprost — trzeba go złożyć z sygnałów w czterech różnych dokumentach | Rdzeń wizji: „połączyć informacje, których nikt nie łączy” ([01](../../docs/01-wizja.md)) | Czy wyróżnik „Knowledge Fusion” jest realny |
| **3** | **Czy przewagą PDI jest ciągłość, a nie jednorazowa analiza?** Analiza konkurencji wskazała, że jednorazową krytykę daje dziś każdy asystent AI, a luka leży w trwałym modelu decyzji i reakcji na nowe informacje ([10, U2–U3](../../docs/10-analiza-konkurencji.md#4-ustalenia)) | Analiza konkurencji | Czy wartość PDI ma uzasadnienie w praktyce — i czy kierunek komercyjny ma sens |
| **4** | **Czy system odróżnia ważne od nieważnego?** W rundzie 2 jeden dokument podważa decyzję, a drugi jest kosmetyczną zmianą projektu | Attention Intelligence ([05](../../docs/05-attention-intelligence.md)), luka S6 | Czy obietnica „nie przeszkadza” jest wykonalna |

Dodatkowo test sprawdza **samą procedurę testu**: klucz odpowiedzi, kartę oceny, czas pracy. Zanim użyjemy jej na prawdziwych inicjatywach design partnerów, chcemy znaleźć jej błędy na przypadku, który kontrolujemy.

## Czego ten test NIE dowodzi

- **Wartości dla PM-a.** Przypadek jest syntetyczny — sami zaszyliśmy w nim błędy. System, który je znajdzie, znajduje to, co do niego włożyliśmy ([09, K1](../../docs/09-weryfikacja-planu.md#k1-brak-źródła-przypadków-i-użytkowników--dodany-etap-0)). Wartość potwierdzą dopiero prawdziwe inicjatywy i ocena partnerów.
- **Przewagi rynkowej.** Jeden przypadek, jeden oceniający (autor projektu), brak pełnego zaślepienia.
- **Jakości przyszłego produktu.** Wariant B to prompt, nie system. Słaby wynik B może oznaczać słaby prompt, a nie słabą koncepcję.

Dobry wynik = zielone światło do pokazania metody partnerom. Zły wynik = sygnał do poprawy metody **przed** kontaktem z partnerami.

## Przypadek

Inicjatywa „panel statusu zamówienia” ([model wzorcowy](../../examples/status-zamowienia.yaml)), rozpisana na dokumenty, jakie PM miałby naprawdę:

| Runda | Pliki | Sytuacja |
|---|---|---|
| 1 | `materialy/runda-1/01`–`08` — opis inicjatywy, wywiady, analityka, raport obsługi, notatka z obsługi, OKR, notatka z decyzji, wymagania | Jutro decyzja o przekazaniu do estymacji |
| 2 | `materialy/runda-2/09`, `10` — analiza zespołu danych, aktualizacja projektu UX | Miesiąc później, inicjatywa w realizacji |

Co jest zaszyte i czego nie wolno zgłaszać: [klucz-odpowiedzi.md](klucz-odpowiedzi.md). **Nie czytaj klucza przed uruchomieniem przebiegów, jeśli to możliwe**, i nigdy nie wklejaj go do testowanych narzędzi.

## Warianty

| Wariant | Co to jest | Prompt |
|---|---|---|
| **A** | Ogólny asystent AI z uczciwie dobrym promptem — najsilniejszy zamiennik PDI | [prompty/A-ogolny-asystent.md](prompty/A-ogolny-asystent.md) |
| **B** | Prototyp PDI (Wizard of Oz): ten sam model, prowadzony metodą PDI; w rundzie 2 dostaje zapisany model decyzji zamiast materiałów | [prompty/B-pdi.md](prompty/B-pdi.md) |
| *opcjonalnie* | ProdPad CoPilot, Productboard Spark (wersje próbne) — te same materiały, pytanie z A-R1 | jak A |

Warunek uczciwości: **A i B na tym samym modelu** (ten sam produkt i wersja), żeby różnica wynikała z metody.

## Przebieg

1. **Przed startem** — przeczytaj kryteria (niżej) i nie zmieniaj ich po zobaczeniu wyników. Załóż katalog `wyniki/surowe/`.
2. **Runda 1** — A-R1 i B-R1, każdy **3 razy**, każdy w nowej rozmowie. Zapisz pełne odpowiedzi do `wyniki/surowe/`. Z B-R1 zachowaj JSON.
3. **Runda 2:**
   - A-R2a (ta sama rozmowa co A-R1, bez pytania) → jeśli brak reakcji, A-R2b (z pytaniem); 3 razy, w każdej z trzech rozmów A-R1;
   - A-R2c (nowa rozmowa, bez kontekstu), 3 razy;
   - B-R2 (nowa rozmowa + JSON z odpowiadającego przebiegu B-R1), 3 razy.
4. **Ocena** — dla każdego przebiegu karta [karta-oceny.md](karta-oceny.md) → `wyniki/<wariant>-<runda>-<nr>.md`. Oceniaj kolejność przebiegów pomieszaną (nie wszystkie A, potem wszystkie B).
5. **Drugi oceniający (opcjonalnie)** — sędzia LLM innego dostawcy według [prompty/C-sedzia.md](prompty/C-sedzia.md); policz zgodność.
6. **Raport** — [wyniki/raport-szablon.md](wyniki/raport-szablon.md).

Szacowany czas: ok. 18 rozmów × 5–10 min + ocena ok. 1,5 h = **ok. 3–4 h**. Koszt: w ramach zwykłego abonamentu asystenta AI.

## Kryteria (zapisane przed testem)

Progi są wstępne, ustalone przed uruchomieniem zgodnie z [regułą K2](../../docs/09-weryfikacja-planu.md#k2-bramki-gono-go-bez-progów--progi-ustalane-przed-testem-nie-po). Pass^3 = pozycja wykryta w pełni we **wszystkich trzech** powtórzeniach (miara spójności — PM nie może liczyć na szczęście).

| Kryterium | Pytanie | Spełnione, jeśli… |
|---|---|---|
| **K1 — metoda działa** | 1 | B: W1 i W2 pełnie w ≥ 2 z 3 przebiegów, W3 co najmniej częściowo w ≥ 2 z 3; średnio ≤ 1 fałszywy alarm na przebieg |
| **K2 — łączenie informacji** | 2 | B wykrywa W2 pełnie (≥ 2 sygnały z różnych dokumentów) w większej liczbie przebiegów niż A |
| **K3 — przewaga ciągłości** | 3 | B-R2: N1 pełnie w ≥ 2 z 3 **i** średnia N1–N3 w B-R2 wyższa niż w A-R2c o ≥ 2 pkt |
| **K4 — szum** | 4 | B-R2: N4 zaliczone w ≥ 2 z 3 |

### Jak czytać wynik

| Wynik | Interpretacja | Co dalej |
|---|---|---|
| K1 niespełnione | Metoda (prompt, katalog, schemat) nie działa nawet na kontrolowanym przypadku | Poprawić B, powtórzyć test; nie pokazywać partnerom |
| K1 spełnione, A ≈ B w rundzie 1 | **Oczekiwane** (analiza konkurencji, U2): jednorazowa analiza jest zastępowalna | Nie jest porażką; liczy się K3 |
| K3 spełnione, ale A-R2a ≈ B-R2 | Przewaga ciągłości istnieje tylko wtedy, gdy PM traci kontekst (nowa rozmowa) | Wartość = trwałość modelu w czasie; to argument słabszy, ale realny — sprawdzić u partnerów, jak często kontekst ginie |
| K3 i K4 spełnione, A-R2a wyraźnie słabsze | Hipoteza U3 wsparta: ciągłość i ochrona uwagi to rzeczywisty wyróżnik | Pokazać metodę partnerom; budować MVP wokół rundy 2, nie rundy 1 |
| K3 niespełnione | Ani trwały model, ani metoda nie dają przewagi w reakcji na nowe informacje | Zatrzymać się i przemyśleć propozycję wartości przed Etapem 0 |
| Dużo trafnych zgłoszeń spoza klucza | Klucz był niepełny albo przypadek bogatszy, niż zakładaliśmy | Uzupełnić klucz **po** teście, odnotować w raporcie |

## Ograniczenia, które trzeba wpisać do raportu

- Jeden oceniający, który zna klucz i jest autorem metody — ryzyko stronniczości na korzyść B. Częściowe zabezpieczenie: cytat jako dowód każdej oceny, pomieszana kolejność, sędzia LLM jako drugi oceniający.
- Format odpowiedzi B (Brief, JSON) zdradza wariant — pełne zaślepienie niemożliwe.
- Prompt B jest dłuższy i bardziej ustrukturyzowany niż A; część przewagi może wynikać z długości, nie z metody. W kolejnej iteracji można dodać wariant A+ (prompt A wzbogacony o katalog R1–R12 bez modelu decyzji), żeby oddzielić wpływ katalogu od wpływu modelu.
