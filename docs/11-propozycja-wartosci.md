# 11. Decyzja: zawężenie propozycji wartości

**Data:** 2026-10-19 · **Decydujący:** właściciel projektu · **Status:** przyjęta, do weryfikacji w rozmowach z design partnerami

## Decyzja

Główną wartością PDI przestaje być **krytyczna analiza decyzji przed jej podjęciem** (Decision Risk Radar). Staje się nią:

> **Strażnik podstaw decyzji** — system pamięta, na jakich liczbach, założeniach i warunkach oparto decyzję PM-a, przegląda nowe informacje z całej firmy i ostrzega, gdy któraś z nich te podstawy unieważnia — z wyliczonym skutkiem dla decyzji. Poza tym milczy.

Jedno zdanie dla PM-a: *„Przypilnuję, żeby Twoja decyzja nie straciła podstaw bez Twojej wiedzy.”*

## Dlaczego

| Ustalenie | Źródło |
|---|---|
| Jednorazową krytykę decyzji ogólny asystent AI z dobrym promptem robi równie dobrze jak prototyp PDI (16/16 vs 16/16) | [Test v1](../eval/status-zamowienia/wyniki/raport.md) |
| Reakcję na nowy dokument w tej samej rozmowie — też | Test v1, runda 2 |
| Gdy informacja zmienia **liczby lub warunki** decyzji i jej nie wspomina, tylko wariant z zapamiętanym uzasadnieniem wylicza skutek (3/3 vs 0/3) | [Test v2](../eval/v2-pamiec-decyzji/wyniki/raport.md), sygnał S1 |
| Szum (fałszywe alarmy, duplikaty) ogranicza metoda — poziomy reakcji i zasada „zbędne powiadomienie to błąd” — nie pamięć | Test v2, wariant A+ |
| Jednorazowa analiza jest powszechnie dostępna; luka rynkowa leży w trwałym modelu decyzji i ochronie uwagi | [Analiza konkurencji](10-analiza-konkurencji.md), U2–U3 |

Szeroka obietnica („lepiej przemyśl decyzję”) prowadziłaby do walidacji czegoś, co nie jest wyróżnikiem: PM oceniłby analizę jako przydatną, a i tak zrobiłby ją później sam w ChatGPT.

## Co się zmienia

| Obszar | Było | Jest |
|---|---|---|
| Główna wartość | A. Decision Risk Radar | **Strażnik podstaw decyzji** (połączenie C — model decyzji, Continuous Guardian i Attention Intelligence) |
| Rola radaru (A) | Główny argument | Pierwszy krok: spisanie podstaw decyzji (założenia nośne, warunki unieważnienia) |
| Moment użycia | Przed decyzją | Po decyzji, przez cały okres wdrażania |
| Wejście | Materiały jednej inicjatywy | Podstawy 1–3 podjętych decyzji + cotygodniowy strumień informacji z firmy |
| Wyjście | Decision Readiness Brief | Cotygodniowa informacja: zwykle „bez zmian”, czasem jedno ostrzeżenie z wyliczonym skutkiem |
| Design partner | Inicjatywa przed decyzją, jednorazowa analiza | 1–3 decyzje we wdrażaniu, obserwacja 4–6 tygodni |
| Główne pytanie walidacyjne | Czy analiza wykrywa coś, czego PM nie widzi? | **Jak często decyzje tracą podstawy przez informacje z innych działów — i czy wyłapujemy to na czas?** |

Zaktualizowane materiały: [propozycja dla PM-ów](../outreach/propozycja-dla-pm.md), [profil partnera](../outreach/profil-design-partnera.md), [szablony kontaktu](../outreach/wiadomosc-kontaktowa.md), [zasady poufności](../outreach/zasady-poufnosci.md) (materiały cotygodniowe), [plan, Etap 0](08-plan-projektu.md#etap-0-design-partnerzy-i-przypadki-k1-k3).

## Czego ta decyzja nie zmienia

- Model decyzji ([02](02-living-decision-model.md)), katalog wzorców ([03](03-decision-risk-radar.md)), pętla zamykania luk ([04](04-knowledge-gap-closure.md)) i poziomy uwagi ([05](05-attention-intelligence.md)) zostają — to z nich składa się mechanizm, który zadziałał w teście v2.
- Nie rozstrzyga, czy PDI ma być produktem komercyjnym, czy narzędziem wewnętrznym. Wynik testu v2 (przewaga z prostego mechanizmu: zapisany model + prompt) przesuwa rekomendację w stronę narzędzia wewnętrznego / skilla; ostatecznie rozstrzygną to rozmowy z partnerami.

## Ryzyka decyzji

| Ryzyko | Jak je wykryjemy |
|---|---|
| Takie sytuacje są rzadkie — wartość za mała, by ktoś z niej korzystał | Pytanie P8 w każdej rozmowie ([profil](../outreach/profil-design-partnera.md#6-pytania-kwalifikacyjne-rozmowa-2030-min)): odsetek PM-ów z konkretnym przypadkiem w ostatnich 6–12 miesiącach |
| PM nie widzi informacji, które mają znaczenie, więc nie może ich przekazać | Porównanie: czy ostrzeżenia dotyczą tego, co PM przekazał, czy przypadki z P8 pochodziły z miejsc, do których PM nie ma dostępu |
| Uzasadnienia decyzji rzadko są spisane z liczbami | Pytanie P4 w rozmowach; trafność spisania podstaw potwierdzana przez partnera |
| Trudniej o partnerów (więcej czasu i dostępu niż przy jednorazowej analizie) | Odsetek rozmów kończących się zgodą; limit 6 tygodni z Etapu 0 |
| Nadwrażliwość przy decyzjach z cienkim marginesem (obserwowana w teście v2) | Oceny partnerów: odsetek „nietrafne / bez znaczenia” |

## Kiedy wrócić do tej decyzji

- Jeśli mniej niż ok. 1/3 rozmówców poda na P8 konkretny przypadek → problem jest za rzadki; wrócić do pytania o propozycję wartości przed budową czegokolwiek. *[próg wstępny — potwierdzić przed pierwszymi rozmowami]*
- Jeśli przypadki z P8 pochodzą głównie z miejsc, do których PM nie ma wglądu → wartość wymaga integracji ze źródłami firmy (wyższy koszt, inna architektura).
- Jeśli w pilotażu ponad połowa ostrzeżeń jest oceniana jako „już wiedziałem” → PM-owie sami pilnują podstaw lepiej, niż zakładamy.
