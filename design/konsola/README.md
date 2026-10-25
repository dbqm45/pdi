# Konsola pdi — makieta

Data: 2026-10-25 · Status: **makieta** (dane przykładowe, nic nie jest podłączone) · Podgląd:
https://claude.ai/artifact/4hM83CXFHEBwFpisV3qw2U

Makieta interfejsu z [planu automatyzacji i konsoli](../../docs/plan-automatyzacja-i-konsola.md) (§5). Dane
przykładowe: sprintdeck budowany przez cały ekosystem (dogfooding). Pola w nawiasach kwadratowych, np.
`[PRÓG AKTYWACJI]`, to wartości do ustalenia, nie dane.

| Plik | Ekran | Co pokazuje |
|---|---|---|
| [`Main.dc.html`](Main.dc.html) | Tablica | podsumowanie (czeka na Ciebie, zablokowane, agenci, u użytkowników, koszt), tablica zmian według faz z czterema stanami kart, oś zdarzeń „Teraz”, skrzynka decyzji, rozmowa z Claude ze szkicem decyzji |
| [`Slad.dc.html`](Slad.dc.html) | Ślad zmiany (CHG-7) | etapy od zgłoszenia do skutku, przebieg z podziałem na człowieka, AI i aplikacje, cięcia i PR-y, udostępnianie flagi, decyzje w zmianie, skutek |
| [`Decyzje.dc.html`](Decyzje.dc.html) | Rejestr decyzji | lista decyzji z filtrami, szczegóły decyzji: powód, opcje, dowody ze statusem epistemicznym, założenie nośne podważone przez nowy sygnał |
| [`Autonomia.dc.html`](Autonomia.dc.html) | Autonomia | poziomy 0–3, typy decyzji z odsetkiem szkiców AI zatwierdzonych bez zmian i progiem 95%, propozycje obniżenia i powrotu poziomu, typy zawsze u człowieka, działania automatu |
| [`canvas.json`](canvas.json) | — | układ ekranów na kanwie |

## PDF do podglądu

Ekrany wyrenderowane do PDF (szerokość 1440 px, jedna strona na ekran), do otwarcia bez edytora:

| Plik | Ekran |
|---|---|
| [`pdf/konsola-pdi.pdf`](pdf/konsola-pdi.pdf) | wszystkie cztery ekrany w jednym pliku |
| [`pdf/1-tablica.pdf`](pdf/1-tablica.pdf) | Tablica |
| [`pdf/2-slad-zmiany.pdf`](pdf/2-slad-zmiany.pdf) | Ślad zmiany (CHG-7) |
| [`pdf/3-decyzje.pdf`](pdf/3-decyzje.pdf) | Rejestr decyzji |
| [`pdf/4-autonomia.pdf`](pdf/4-autonomia.pdf) | Autonomia |

PDF-y powstały ze stanu plików `.dc.html` z 2026-10-25. Po zmianie makiety trzeba je wygenerować ponownie.

Pliki `.dc.html` to format edytora Design w Claude: wymagają jego środowiska (`support.js`) i nie otwierają się
poprawnie jako zwykłe strony. Źródłem prawdy jest podgląd pod linkiem wyżej; ten katalog to kopia do historii
i przeglądu w PR-ach.
