# Jedna platforma — makieta

Data: 2026-10-27 · Status: **makieta** (dane przykładowe, nic nie jest podłączone) · Podgląd:
https://claude.ai/artifact/5hUnjQX6HN19gp41LLf5rV · Opis pomysłu:
[`docs/15-jedna-platforma.md`](../../docs/15-jedna-platforma.md)

Ekrany jednego produktu z menu ułożonym według pytań, po angielsku. Dane przykładowe: sprintdeck budowany przez cały
ekosystem, jak w [makiecie konsoli](../konsola/README.md). Wartości w nawiasach, np. `[COST]`, są do ustalenia.

| Ekran | PNG | Źródło | Co pokazuje |
|---|---|---|---|
| Now | [`1-now.png`](1-now.png) | [`Main.dc.html`](Main.dc.html) | podsumowanie, „Waiting for you” (bramki, pytania, włączenie na PROD, ocena skutku), uwagi (rozjazd FE/BE, prognoza z wątpliwością), oś zdarzeń, rozmowa z Claude |
| Product | [`2-product.png`](2-product.png) | [`Produkt.dc.html`](Produkt.dc.html) | domena → funkcjonalność → części w serwisach z flagami; przełącznik per środowisko; nieaktywny, gdy kod części nie jest wdrożony; na PROD plan przełączenia (BE → FE) i decyzja w pdi |
| Work | [`3-work.png`](3-work.png) | [`Praca.dc.html`](Praca.dc.html) | zmiany jako przebiegi przez osiem faz zamiast tablicy, na kogo czekają, prognoza G3 z „?” przy wątpliwości |
| Releases | [`4-releases.png`](4-releases.png) | [`Wydania.dc.html`](Wydania.dc.html) | część ShipScope: środowiska (wersje, drift, rollback, rozjazd flag) i historia wdrożeń w zakładkach |
| Problems | [`5-problems.png`](5-problems.png) | [`Problemy.dc.html`](Problemy.dc.html) | zgłoszenie „kto, czego nie może, jaki skutek”, pytania od Claude, podpowiedź duplikatu, lista po triażu |
| Consistency | [`6-consistency.png`](6-consistency.png) | [`Spojnosc.dc.html`](Spojnosc.dc.html) | ci_for_sdlc: gotowość zmian w ośmiu wymiarach, kolejka pytań do decyzji, odpowiedzi znalezione w źródłach (A2a), zaakceptowane ryzyka z terminem przeglądu |
| Consistency: zmiana | [`7-consistency-change.png`](7-consistency-change.png) | [`SpojnoscZmiana.dc.html`](SpojnoscZmiana.dc.html) | ustalenia CHG-8 z dowodami ze źródeł obok siebie (Jira, Confluence, Figma, kod z rekonstrukcji tf, JUnit); decyzja: wybór rozwiązania, akceptacja ryzyka z powodem i terminem albo odrzucenie, zapis jako DEC-n w pdi; macierz ścieżka × stan z ramkami z `design.md`; kryteria akceptacji ↔ testy |
| — | — | [`Nawigacja.dc.html`](Nawigacja.dc.html) | wspólne menu (komponent) |
| — | — | [`canvas.json`](canvas.json) | układ ekranów na kanwie |

PNG pokazują stan początkowy ekranów (bez kliknięć; plan przełączenia na ekranie Product otwiera się po kliknięciu
przełącznika PROD w podglądzie). Pliki `.dc.html` to format edytora Design w Claude: wymagają jego środowiska
(`support.js`) i nie otwierają się poprawnie jako zwykłe strony. Źródłem prawdy jest podgląd pod linkiem wyżej; ten
katalog to kopia do historii i przeglądu w PR-ach. Po zmianie makiety PNG trzeba wygenerować ponownie.
