# Klucz odpowiedzi — NIE WKLEJAĆ do testowanych narzędzi

> Ten plik i `examples/status-zamowienia.yaml` zawierają oczekiwane wyniki. Wklejenie któregokolwiek z nich do promptu lub rozmowy z testowanym narzędziem unieważnia przebieg (kontaminacja).

## Runda 1 — co powinno zostać wykryte

Waga: **K** — krytyczne (zmienia kierunek decyzji), **W** — ważne (zmienia zakres lub sposób oceny), **D** — drobne (obserwacja).

| ID | Waga | Wzorzec | Co jest zaszyte | Gdzie w materiałach | Pełne wykrycie (2 pkt) | Częściowe (1 pkt) |
|---|---|---|---|---|---|---|
| **W1** | K | R2 — hipoteza jako fakt | Przyczyna problemu („brak informacji w interfejsie”) jest podana jako fakt, choć żaden dowód jej nie potwierdza. Dowody potwierdzają **istnienie** problemu, nie jego **przyczynę**. | 01 („jest przyczyną”), 07 (uzasadnienie) | Wskazuje, że przyczyna jest założeniem / niepotwierdzona i że od niej zależy decyzja | Ogólnie: „warto zweryfikować założenia” bez wskazania tego konkretnego |
| **W2** | K | R5 / R4 — konkurencyjne wyjaśnienie, łączenie rozproszonych sygnałów | Problem może wynikać z **nieaktualnych statusów** (opóźnione zdarzenia od przewoźników), a nie z braku informacji. Sygnały są rozproszone w 4 dokumentach. | 02 (cytat U7), 04 (zmiana przewoźnika od tyg. 18, skoki w tyg. 19 i 24), 05 (paczka dotarła, a status „W przygotowaniu”), 07 (uwaga tech leada o opóźnieniach) | Formułuje alternatywne wyjaśnienie **i** łączy co najmniej 2 sygnały z różnych dokumentów | Wspomina jeden sygnał albo „mogą być inne przyczyny” bez konkretu |
| **W3** | W | R7 — nieweryfikowalny cel | Kryteria akceptacji sprawdzają działanie panelu („wyświetla się dla 100%”), nie rezultat (spadek kontaktów). Dodatkowo OKR wymaga metryki rezultatu powiązanej z KR. | 08, 06 („Zasady realizacji”), 01 | Wskazuje brak metryki rezultatu (np. KR 1.1 / udział kontaktów o status) | Ogólnie: „doprecyzować metryki sukcesu” |
| **W4** | W | R6 / R3 — brak alternatyw, pominięte rekomendacje badań | Rozważono tylko formę panelu (zakładka vs sekcja). Pominięto tańsze alternatywy, w tym rekomendacje badacza: ujednolicenie nazw statusów, widoczna przewidywana data dostawy. | 07, 02 (rekomendacje badacza, ustalenie 4) | Wskazuje brak rzeczywistych alternatyw **i** co najmniej jedną konkretną tańszą opcję | Tylko „rozważyć alternatywy” |
| **W5** | D | R12 — nadinterpretacja danych | „Klienci szukają informacji, których nie ma” to interpretacja. Częste otwarcia (4,7 na zamówienie w 2,8 dnia) pasują też do sprawdzania, czy status się zmienił (U5; link śledzenia dostępny dopiero od „Wysłane”). | 01, 03, 02 (U5) | Wskazuje alternatywną interpretację danych analitycznych | Tylko „dane analityczne są niejednoznaczne” |
| **W6** | W | Ryzyko rozwiązania | Panel korzysta z tych samych zdarzeń (OMS, webhooki przewoźników), które bywają opóźnione. Panel może bardziej eksponować nieaktualne dane. | 08 (wymaganie 5), 07 (uwaga tech leada) | Wskazuje, że opóźnione zdarzenia osłabią lub odwrócą efekt panelu | Wspomina ryzyko integracji tylko jako techniczne (estymacja) |

**Najtańszy krok (ocena rekomendacji, 0–2 pkt):** pełne punkty, jeśli główna rekomendacja przed estymacją to sprawdzenie przyczyny na istniejących danych (np. zestawienie zgłoszeń z opóźnieniami statusów / logiem webhooków). Jedna kategoria, jeśli rekomenduje nowe badania lub eksperyment zamiast analizy istniejących danych. Zero, jeśli rekomenduje kontynuację bez weryfikacji albo brak konkretnego kroku.

**Werdykt proporcjonalny (0–2 pkt):** pełne punkty za „nie przekazywać pełnego zakresu do estymacji przed rozstrzygnięciem przyczyny” (lub „decydować w węższym zakresie”). Zero za „gotowe do estymacji” bez zastrzeżeń albo za „wstrzymać całą inicjatywę / problem nie istnieje”.

## Runda 1 — czego NIE powinno się zgłaszać jako istotnego problemu (fałszywe alarmy)

| ID | Fałszywy alarm | Dlaczego to błąd |
|---|---|---|
| **F1** | „Problem nie jest udowodniony / 8 wywiadów to za mało” | Istnienie problemu potwierdzają dane obsługi (12 410 kontaktów, 38%) i wywiady — siła dowodów jest wystarczająca dla **istnienia** problemu |
| **F2** | „Panel narusza KR 2.2 (nie zwiększać liczby ekranów)” | KR 2.2 dotyczy ścieżki zakupu (koszyk → potwierdzenie), a panel jest w szczegółach zamówienia po zakupie |
| **F3** | „Konflikt z KR 1.2 (NPS)” | Brak sprzeczności — panel nie pogarsza doświadczenia |
| **F4** | „Ręczna kategoryzacja podważa dane obsługi” zgłoszone jako ryzyko krytyczne | Ograniczenie warte wzmianki, ale nie zmienia decyzji; dopuszczalne jako uwaga drobna |
| **F5** | „Brak powiadomień push to krytyczna luka” | Świadoma decyzja o zakresie, opisana w materiałach |

Fałszywym alarmem jest zgłoszenie F1–F5 jako problemu **krytycznego lub ważnego**. Wzmianka jako drobna uwaga nie jest liczona.

## Runda 2 — reakcja na nowe informacje

Kontekst: decyzja o estymacji zapadła; po miesiącu pojawiają się dwa dokumenty.

| ID | Co powinno nastąpić | Pełne (2 pkt) | Częściowe (1 pkt) |
|---|---|---|---|
| **N1** | Dokument 09 zostaje rozpoznany jako **podważający założenie decyzji** (W1) — wysoki priorytet | Wprost: „podważa przyczynę, na której oparto decyzję o panelu” + wysoki priorytet | Streszcza wyniki bez powiązania z decyzją |
| **N2** | Rozdzielenie: **co pozostaje aktualne** (problem istnieje, cel KR 1.1, 23% zgłoszeń dot. znaczenia statusu / daty dostawy) i **co wymaga ponownej oceny** (wybór rozwiązania, zakres, kolejność działań) | Oba elementy | Tylko jeden |
| **N3** | Konkretny następny krok: naprawa / monitoring integracji z nowym przewoźnikiem przed lub zamiast pełnego panelu; ewentualnie zawężenie panelu (nazwy statusów, data dostawy) | Konkret + uzasadnienie danymi z 09 | Ogólne „zrewidować decyzję” |
| **N4** | Dokument 10 **nie** wywołuje ostrzeżenia (poziom 0 — aktualizacja bez powiadomienia; dopuszczalna jednozdaniowa wzmianka) | Brak ostrzeżenia o dokumencie 10 | — (ostrzeżenie o dokumencie 10 = fałszywy alarm F6) |

## Punktacja

- Runda 1: W1–W6 (max 12) + najtańszy krok (2) + werdykt (2) = **max 16**; fałszywe alarmy liczone osobno.
- Runda 2: N1–N3 (max 6) + N4 (zaliczone / niezaliczone) + fałszywe alarmy.
