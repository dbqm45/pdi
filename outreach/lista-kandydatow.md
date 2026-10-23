# Lista kandydatów — jak ją zbudować w 90 minut

> **Wstrzymane 2026-10-23** — pdi rozwijane jest jako warstwa decyzji we własnym flow SDLC, z pilotem na własnych problemach ([dokument 12](../docs/12-zmiana-kierunku-sdlc.md)). Materiał zostaje na wypadek, gdyby po F5 wróciło pytanie o użycie pdi poza tym flow.

Uzupełnienie [profilu design partnera](profil-design-partnera.md). Cel: **15–20 nazwisk**, z których po rozmowach zostanie 3–5 partnerów i co najmniej 10 odpowiedzi na pytanie P8.

**Nazwiska wpisujesz tylko do pliku `outreach/rejestr-kandydatow.csv`** (szablon: [rejestr-kandydatow-szablon.csv](rejestr-kandydatow-szablon.csv)). Ten plik jest w `.gitignore` — nie trafi do repozytorium. W repozytorium zostają tylko zagregowane liczby.

## 1. Gdzie szukać — segmenty z największą szansą na „ciche unieważnienia”

Decyzje tracą podstawy przez inne działy tam, gdzie produkt zależy od dostawców, umów, regulacji, logistyki lub wielu rynków. Takich PM-ów szukaj najpierw.

| Priorytet | Segment | Typowe decyzje PM-a | Kto po cichu zmienia ich podstawy | Przykładowy sygnał |
|---|---|---|---|---|
| **1** | E-commerce, marketplace, retail omnichannel | progi dostawy, metody płatności, zwroty, dostępność „wysyłka dziś” | zakupy, logistyka, magazyn, operator płatności, marketing (nowe rynki) | aneks z przewoźnikiem, zmiana prowizji operatora, wejście na nowy rynek |
| **1** | Fintech, insurtech, płatności | limity, scoring, onboarding, prowizje | compliance, prawo, partnerzy bankowi, ryzyko | nowa interpretacja regulatora, zmiana warunków partnera |
| **1** | B2B SaaS z integracjami | cennik, plany, funkcje zależne od API partnerów | partnerstwa, integracje, finanse (koszt chmury), sprzedaż (umowy enterprise) | partner wygasza API, klient strategiczny negocjuje wyjątek |
| **2** | Travel, mobilność, logistyka (TSL tech) | ceny, dostępność, SLA dla klienta | dostawcy, operacje, zakupy paliwa/energii | zmiana SLA dostawcy, nowe koszty energii |
| **2** | Telco, media, subskrypcje | pakiety, ceny, promocje | licencje treści, sieć, prawo konsumenckie | zmiana kosztu licencji, nowy wymóg informacyjny |
| **2** | Platformy wewnętrzne w dużych firmach | migracje, standardy, harmonogramy | inne zespoły produktowe, bezpieczeństwo, zakupy | zespół zależny zmienia priorytety, nowa polityka bezpieczeństwa |
| **3** | Aplikacje konsumenckie bez łańcucha dostaw, wczesne startupy (< 30 osób) | funkcje, UX | mało działów — mało sygnałów | — (niski priorytet: kryterium O4) |

Zasada różnorodności: **maks. 2–3 osoby z jednej organizacji** i co najmniej 2–3 różne segmenty.

## 2. Przebieg 1 — własna sieć (30–40 min, najważniejszy)

Przejdź po kolei przez poniższe pytania i zapisz każde nazwisko, które przyjdzie Ci do głowy — oceniać będziesz później:

- Z którymi PM-ami / Head of Product pracowałem w ostatnich 5 latach?
- Kto z moich byłych firm awansował na stanowisko produktowe?
- Kogo poznałem na meetupach, konferencjach, szkoleniach produktowych?
- Kto z mojego otoczenia narzekał kiedyś, że „decyzja się posypała przez coś z innego działu”? (to od razu kandydat z D1)
- Którzy znajomi pracują w segmentach priorytetu 1 — nawet jeśli nie są PM-ami? (mogą polecić PM-a — kanał poleceń)
- Kto z kontaktów na LinkedIn (1. stopień) ma w tytule „Product Manager”, „Product Owner”, „Head of Product”, „Group PM”?

Cel przebiegu: 15+ nazwisk, zanim zaczniesz szukać dalej.

## 3. Przebieg 2 — wyszukiwanie na LinkedIn (20–30 min)

Filtry: lokalizacja Polska, kontakty 1. i 2. stopnia (2. stopień = ktoś może Cię polecić — wariant B wiadomości).

Wyszukiwania (pole „Osoby”):

```
("Product Manager" OR "Head of Product" OR "Product Owner" OR "Group Product Manager") AND (e-commerce OR marketplace OR checkout OR logistyka OR dostawa OR fulfillment)
```

```
("Product Manager" OR "Head of Product") AND (fintech OR płatności OR payments OR insurtech OR ubezpieczenia)
```

```
("Product Manager" OR "Head of Product") AND (integracje OR integrations OR API OR partnerships OR platforma) AND (SaaS OR B2B)
```

```
("Product Manager" OR "Product Owner") AND (pricing OR cennik OR monetyzacja OR monetization)
```

Słowo „pricing / cennik / monetyzacja” w profilu to dobry sygnał kryterium D3 (decyzje z policzalnym uzasadnieniem).

Nie używaj automatycznych narzędzi do pobierania profili ani masowych zaproszeń — ryzyko blokady konta i sprzeczne z [zasadami kontaktu](wiadomosc-kontaktowa.md#zasady).

## 4. Przebieg 3 — społeczności (10–20 min, przygotowanie na później)

| Społeczność | Co wiadomo (stan na 2026-10-19) | Jak użyć |
|---|---|---|
| ProductTank Kraków (Mind the Product) | Regularne meetupy: #43 (2025-11-26), #44 (2026-02-24), #45 (2026-05-26, 10-lecie) — [Crossweb](https://crossweb.pl/wydarzenia/producttank-krakow-44/), [#45](https://crossweb.pl/en/events/producttank-krakow-45/); kolejnych terminów nie znaleziono | Śledzić następny termin; po wystąpieniach — rozmowy z prelegentami i organizatorami (mogą polecać) |
| ProductTank Warszawa | Brak informacji o wydarzeniach w 2026 (tylko wzmianki historyczne) | Sprawdzić u organizatorów; nie planować na tym kanale |
| Product Shapers (Polska) | Cykl spotkań i warsztatów dla liderów produktu (min. 3 lata doświadczenia w przywództwie); wydarzenie w Warszawie w serwisie [Luma](https://luma.com/iv5imlci) — rok niepotwierdzony | Dobry kanał do Head of Product (decydenci, mogą polecić PM-ów) — sprawdzić aktualne terminy |
| Mind the Product (globalnie) | Społeczność ze Slackiem i meetupami w wielu miastach ([przegląd społeczności PM](https://clickup.com/pl/blog/444043/spolecznosc-menedzerow-produktu)) | Post w kanale regionalnym — wariant C wiadomości |

Społeczności dają zasięg, ale słabsze zaufanie — traktuj je jako źródło kontaktów na drugą falę, nie pierwszą.

## 5. Punktacja przed kontaktem

Dla każdego nazwiska z przebiegów 1–3 przyznaj 0–2 pkt (kolumny w szablonie rejestru):

| Kolumna | 0 | 1 | 2 |
|---|---|---|---|
| `pkt_rola` (O1) | wykonuje roadmapę innych | współdecyduje | sam decyduje o kierunku |
| `pkt_zaleznosc` (O4, segment) | priorytet 3 | priorytet 2 | priorytet 1 |
| `pkt_liczby` (D3) | brak sygnału | prawdopodobnie | wiem, że decyduje o cenach/kosztach/SLA |
| `pkt_relacja` | zimny kontakt | 2. stopień / letni | znamy się dobrze |
| `pkt_przypadek` (D1) | nie wiem | możliwe | wiem, że miał taką sytuację |

**Suma 0–10.** Do pierwszej fali wybierz **5 osób z najwyższą sumą**, ale z co najmniej 2 organizacji i bez bliskich przyjaciół w większości (ryzyko ocen z grzeczności). Kolejne 5 — po tygodniu, z uwzględnieniem poleceń.

## 6. Kolejność kontaktu

| Fala | Kto | Wiadomość | Kiedy |
|---|---|---|---|
| 1 | 5 osób z najwyższą sumą, kontakty ciepłe | [wariant A](wiadomosc-kontaktowa.md#wariant-a--osoba-znana-sieć-kontaktów) | Dzień 5 planu |
| 2 | 5 kolejnych + polecenia z fali 1 | wariant A lub [B](wiadomosc-kontaktowa.md#wariant-b--osoba-z-polecenia) | tydzień później |
| 3 | pozostali + społeczności | wariant B lub [C](wiadomosc-kontaktowa.md#wariant-c--post-w-społeczności) | gdy fale 1–2 dadzą < 3 partnerów |

## 7. Ile to powinno dać (szacunek do weryfikacji)

Przy 15–20 kontaktach: ok. 8–12 rozmów (odpowiedzi na P8) → 3–5 partnerów. *[założenie — odsetki odpowiedzi nieznane; zapisuj je od pierwszej fali, to pierwsze dane rynkowe]*
