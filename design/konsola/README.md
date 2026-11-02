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

PDF-y powstały ze stanu plików `.dc.html` z 2026-11-02 (wersja z trzema pasami). Po zmianie makiety trzeba je wygenerować ponownie.

Pliki `.dc.html` to format edytora Design w Claude: wymagają jego środowiska (`support.js`) i nie otwierają się
poprawnie jako zwykłe strony. Źródłem prawdy jest podgląd pod linkiem wyżej; ten katalog to kopia do historii
i przeglądu w PR-ach.

## Wersje klikalne (do otwarcia w przeglądarce)

- [`v2-klikalna/`](v2-klikalna/index.html): **aktualna**, z trzema pasami (stan z 2026-11-02, po akceptacji propozycji niżej).
- [`v1-klikalna/`](v1-klikalna/index.html): wersja sprzed pasów, zachowana do porównania.

Oba katalogi to te same cztery ekrany jako zwykłe strony HTML.
Otwierasz `v1-klikalna/index.html` (albo `Main.html`) w przeglądarce, bez edytora i bez internetu poza czcionkami
Google. Nawigacja między ekranami działa jak w podglądzie (Tablica, Ślad zmiany, Decyzje, Autonomia). Pliki powstały
przez wyrenderowanie `.dc.html` i zapisanie gotowego HTML bez skryptów; makieta nie ma innej logiki niż linki, więc
nic nie ginie.

## Trzy pasy (wprowadzone 2026-11-02)

Z7a planu [zespół jednoosobowy](../../docs/plan-zespol-jednoosobowy.md). Pasy są w makiecie powyżej i w `v2-klikalna/`:
tablica grupuje kolumny faz w pasy, ślad zmiany pokazuje pasy nad etapami i „Pas N z 3 · teraz · dalej” w nagłówku,
rejestr decyzji i autonomia mają etykietę pasa przy każdej decyzji i typie decyzji. W [`pasy-propozycja/`](pasy-propozycja/)
zostało porównanie przed i po.

| Plik | Co pokazuje |
|---|---|
| [`porownanie-tablica.png`](pasy-propozycja/porownanie-tablica.png) | tablica przed i po: kolumny faz pogrupowane w pasy „Zaprojektuj i zbuduj”, „Oceń i wydaj”, „Wdróż, obserwuj, ulepszaj”, z pętlą do pasa 1 |
| [`porownanie-slad.png`](pasy-propozycja/porownanie-slad.png) | ślad zmiany przed i po: pasy nad etapami, „teraz” na bieżącym pasie, w nagłówku „Pas 3 z 3 · teraz: … · dalej: …” |
| `Main.dc.html`, `Slad.dc.html` | źródła wersji z pasami (format edytora Design) |

Przypisanie faz do pasów: **1. Zaprojektuj i zbuduj** — zgłoszenie, wywiad, intencja, wymagania, architektura, design,
gotowość, budowa; **2. Oceń i wydaj** — review, cele zmiany (Z7b-1), B4/B5, wdrożenie na PROD ukryte za flagą;
**3. Wdróż, obserwuj, ulepszaj** — udostępnianie etapami, wydanie R1, ocena skutku, pętla do pasa 1 (Z7b-2).

