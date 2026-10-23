# Czy Twoje decyzje nadal mają podstawy?

> **Wstrzymane 2026-10-23** — pdi rozwijane jest jako warstwa decyzji we własnym flow SDLC, z pilotem na własnych problemach ([dokument 12](../docs/12-zmiana-kierunku-sdlc.md)). Materiał zostaje na wypadek, gdyby po F5 wróciło pytanie o użycie pdi poza tym flow.

*Zaproszenie do udziału we wczesnej walidacji projektu Product Decision Intelligence*

---

## Problem

Decyzja produktowa opiera się na liczbach i warunkach z chwili jej podjęcia: koszcie, udziale, terminie, dostępności danych, zakresie rynku. Potem zespół ją wdraża — a reszta firmy żyje dalej. Dział zakupów podpisuje aneks, integracje zmieniają API dostawcy, marketing planuje nowy rynek, finanse aktualizują prognozy.

Żaden z tych dokumentów nie wspomina Twojej decyzji. Każdy może ją jednak po cichu unieważnić. Najczęściej dowiadujesz się o tym po wdrożeniu — kiedy wynik odbiega od założeń i trzeba szukać przyczyny.

## Co sprawdzam

Pracuję nad podejściem, które **pamięta, na czym opierają się Twoje decyzje** — jakie liczby, założenia i warunki musiały być spełnione — i **przegląda nowe informacje z firmy pod kątem tego, czy któraś te podstawy podważa**. Gdy tak jest, mówi wprost, co się zmieniło i jaki ma to skutek dla decyzji. Gdy nie — milczy.

Przykład z testu na fikcyjnej firmie:

> **Decyzja (3 tygodnie temu):** obniżamy próg darmowej dostawy do 99 zł. Wynik: ok. +22,6 tys. zł miesięcznie przy koszcie paczki 11,80 zł.
> **Nowy dokument (Dział Zakupów):** aneks do umowy z przewoźnikiem — dopłata paliwowa 9% i nowa stawka za paczki ciężkie. Ani słowa o progu dostawy.
> **Ostrzeżenie:** średni koszt paczki rośnie do ok. 13,28 zł. Przy 18 tys. dodatkowych paczek to +26,6 tys. zł kosztów miesięcznie — więcej niż cały zakładany zysk. **Decyzja przestaje się opłacać (ok. −4 tys. zł/mies.), zanim wejdzie w życie.**
> **Propozycja:** przeliczyć próg przed 1 grudnia albo renegocjować stawkę dla paczek ciężkich.

W tym samym czterotygodniowym teście ogólny asystent AI bez zapamiętanego uzasadnienia decyzji zauważył aneks, ale napisał tylko „sprawdź opłacalność” — bo nie wiedział, na jakich liczbach decyzja się opierała.

## Co dostajesz

- **Prywatne „ubezpieczenie” 1–3 Twoich decyzji** przez 4–6 tygodni wdrażania: co tydzień krótka informacja — zwykle „bez zmian”, czasem jedno konkretne ostrzeżenie z wyliczonym skutkiem.
- **Spisane podstawy Twoich decyzji** — założenia nośne i warunki, przy których decyzja przestaje mieć sens. Wielu PM-om już samo to porządkuje myślenie.
- Ostrzeżenia **nie oceniają Ciebie** i nie trafiają do nikogo poza Tobą. Decyzja, co z nimi zrobić, zostaje Twoja.

## Czego potrzebuję od Ciebie

Łącznie ok. **3–4 godziny w ciągu 6–7 tygodni**:

| Krok | Czas |
|---|---|
| Rozmowa: jak u Was zapadają decyzje i czy zdarzyło się, że decyzja straciła podstawy bez Twojej wiedzy | 45–60 min |
| Wybór 1–3 decyzji **już podjętych** (w trakcie wdrażania) i przekazanie materiałów o nich (po anonimizacji — pomogę) | ok. 30 min |
| Potwierdzenie, że dobrze spisałem podstawy Twoich decyzji | 20 min |
| **Raz w tygodniu, przez 4–6 tygodni:** przekazanie tego, co w tym tygodniu pojawiło się w firmie i co *mogłoby* mieć znaczenie — notatki, tickety, maile z innych działów, zmiany w umowach, raporty (nie musisz oceniać, czy ma znaczenie — od tego jestem ja) + ocena moich uwag: trafne / nietrafne / już wiedziałem / bez znaczenia | 10–15 min tygodniowo |
| Rozmowa na koniec: czy coś zmieniło się dzięki temu w Twoich decyzjach | 20–30 min |

Jeśli w ostatnich miesiącach zdarzyło Ci się, że decyzja straciła podstawy przez coś, co wydarzyło się w innym dziale — **sama rozmowa o takim przypadku jest dla mnie bardzo cenna**, nawet jeśli nie zdecydujesz się na dalszą współpracę.

## Poufność

- Pracuję wyłącznie na materiałach, które sam wybierzesz, po usunięciu nazw firm, klientów, osób i danych liczbowych, które uznasz za wrażliwe (liczby możesz zastąpić proporcjami — rachunek nadal działa).
- Materiały nie są nikomu udostępniane ani publikowane. Wnioski z projektu publikuję tylko w formie zagregowanej, bez możliwości identyfikacji Ciebie lub Twojej organizacji.
- Do analizy używam modelu AI ([dostawca do uzupełnienia]) wyłącznie na warunkach wykluczających trenowanie na przekazanych danych.
- Na Twoje żądanie usuwam wszystkie materiały i notatki.
- Jeśli Twoja organizacja wymaga umowy o poufności — podpiszę ją.

Szczegóły: [zasady poufności](zasady-poufnosci.md).

## Uczciwie o etapie projektu

To **wczesna walidacja, nie gotowy produkt**. Nie ma jeszcze aplikacji ani integracji z Waszymi narzędziami — analizy przygotowuję sam, według opracowanej metody i z pomocą AI. Dwa testy na fikcyjnych przypadkach pokazały, że metoda działa przy informacjach, które zmieniają liczby lub warunki decyzji. Nie wiem jeszcze, **jak często takie sytuacje zdarzają się naprawdę** — i to jest główne pytanie, na które chcę odpowiedzieć z Tobą. Jeśli przez 6 tygodni nic takiego się nie wydarzy, to również jest wynik, który chcę poznać.

## Dla kogo to jest

Jeśli odpowiadasz za decyzje o tym, co i dlaczego budować, masz 1–3 decyzje w trakcie wdrażania, a Twoja praca zależy od innych działów (zakupy, logistyka, integracje, finanse, marketing) — to zaproszenie jest dla Ciebie.

**Jak zacząć:** odpisz lub napisz na [kontakt do uzupełnienia]. Zacznijmy od 20-minutowej rozmowy.

*[Imię i nazwisko] · [kontakt]*
