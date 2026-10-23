Z siedmiu materiałów trzy wymagają Twojej uwagi: wyniki testu A/B (01 i 05 poniżej), komunikat magazynu o inwentaryzacji i Design System v4. Pozostałe cztery nie dotyczą Twoich inicjatyw.

## 1. Wyniki testu A/B progu dostawy (05) – inicjatywa 1, wymaga decyzji lub dopowiedzenia

Wniosek zespołu Danych brzmi „efekt się potwierdza”. To prawda, ale tylko dla konwersji. Test nie rozstrzyga, czy zmiana opłaca się biznesowo.

- **Konwersja:** +5,8% w koszykach 99–149 zł (CI 95%: +4,1% do +7,5%), co jest solidnym potwierdzeniem pilotażu. Efekt jest nieco niższy niż w pilotażu w 3 miastach, więc zaktualizuj założenia w business case.
- **Przychód:** konwersja ogółem rośnie tylko o 0,9%, a średnia wartość koszyka spada o 3,4%. Z tych dwóch liczb wychodzi mniej więcej −2,5% przychodu na odwiedzającego (1,009 × 0,966 ≈ 0,975). To szacunek własny, który zakłada, że oba wskaźniki dotyczą tej samej populacji [założenie].
- **Koszt dostawy:** więcej zamówień dostaje darmową wysyłkę, więc koszt logistyki na zamówienie rośnie. Materiał nie podaje ani marży, ani kosztu dostawy.
- **Zwroty:** brak istotnych różnic, więc to ryzyko możesz zamknąć.
- **Sezonowość:** test trwał 6 tygodni i skończył się przed 2026-11-13. Prawdopodobnie nie obejmuje szczytu Black Friday ani świąt [niezweryfikowane], a start jest 2026-12-01.

**Co zrobić:** poproś Zespół Danych i Finanse o przeliczenie wyniku na marżę po kosztach dostawy, czyli wartość netto na odwiedzającego, a nie samą konwersję. Potem potwierdź GO na 2026-12-01 na tej podstawie. Rozważ też monitoring średniego koszyka po starcie z progiem wycofania zmiany.

## 2. Magazyn: inwentaryzacja 28–30.12 (06) – inicjatywy 1 i 2

Zamówienia złożone po 2026-12-27 będą wysłane dopiero 2026-12-31. Magazyn prosi zespoły produktowe o informację na stronie od 2026-12-20.

- **Inicjatywa 2 (panel statusu):** release jest 2026-12-10, a opóźnienie wysyłki wypada w okresie świątecznym. Panel to naturalne miejsce na komunikat o opóźnieniu i na poprawne daty „wysłane / w drodze”. Uwzględnij ten przypadek w zawężonym zakresie albo świadomie go wyłącz. Magazyn musi też wiedzieć, że status „oczekuje na wysyłkę” będzie wtedy trwał 3–4 dni.
- **Inicjatywa 1 (próg 99 zł):** po obniżce progu będzie więcej zamówień z darmową dostawą, a część z nich przyjdzie w szczycie świątecznym. Komunikat o terminie wysyłki musi być widoczny od 20.12 także w koszyku i przy kasie. Inaczej wzrośnie liczba kontaktów do obsługi klienta o „gdzie jest zamówienie”.

Termin 2026-12-20 jest po Twoim release'ie 2026-12-10, więc zmiany w panelu i w komunikatach da się jeszcze wprowadzić w jednym cyklu.

## 3. Design System v4 (01) – inicjatywa 2, niski priorytet

- **Komponent „Timeline”:** pasuje do panelu statusu zamówienia (oś etapów). Sprawdź z designem, czy użyć go zamiast własnego rozwiązania, bo skróci to czas realizacji przed 2026-12-10.
- **Wycofanie „Badge v2”:** jeśli panel używa Badge v2 do statusów, zaprojektuj go od razu na nowym komponencie.
- **Migracja tokenów do 2027-01-31:** to termin po Twoim release'ie. Nowy panel powinien od razu używać nowych tokenów, żeby nie trafić na listę długu do migracji.

## Pominięte jako nieistotne

- **Incydent BLIK (02):** to jednorazowa awaria dostawcy, z alertem już dodanym i dostępnością 99,95%. Nie zmienia planu wycofania płatności za pobraniem od 2027-02-01. Wróć do tematu tylko wtedy, gdy incydenty się powtórzą, bo wtedy wpłynęłoby to na argumentację za wycofaniem COD.
- **OKR Marketingu (03)**, **opinie w sklepach z aplikacjami (04)** i **aktualizacja bezpieczeństwa (07):** bez związku z tymi trzema inicjatywami.
