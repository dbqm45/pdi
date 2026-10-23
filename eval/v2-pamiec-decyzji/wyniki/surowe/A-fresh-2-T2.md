Z 7 materiałów uwagi wymagają cztery. Poniżej w kolejności ważności.

## 1. Wyniki A/B progu dostawy (05) — inicjatywa 1, do rozstrzygnięcia przed 2026-12-01

Test potwierdza efekt pilotażu, ale trochę słabszy. Konwersja w koszykach 99–149 zł rośnie o 5,8% (95% CI: +4,1% do +7,5%), bez różnic w zwrotach.

Wynik ma jednak drugą stronę. Konwersja ogółem rośnie tylko o 0,9%, a średnia wartość koszyka spada o 3,4%, bo część klientów przestaje dobierać produkty do 149 zł. Szybki rachunek: 1,009 × 0,966 ≈ 0,975, czyli przychód na sesję może spaść o ok. 2,5%. To moje przybliżenie [założenie: średnia wartość koszyka liczona dla wszystkich zamówień]. Do tego dochodzi koszt dostawy, który firma pokryje przy większej liczbie zamówień w przedziale 99–149 zł.

Test mierzył konwersję, a o sensie progu 99 zł decyduje marża. Zanim start 12-01 stanie się ostateczny, poproś Zespół Danych o przychód i marżę na sesję (po koszcie dostawy). Jeśli wyjdą dodatnie, wniosek zespołu się broni. Jeśli nie, potrzebujesz decyzji z jawnym uzasadnieniem, na przykład że płacisz marżą za wzrost konwersji.

## 2. Inwentaryzacja w magazynie (06) — inicjatywy 1 i 2

Inwentaryzacja trwa 2026-12-28 do 12-30, a zamówienia złożone po 12-27 wyjdą dopiero 12-31. Zespoły produktowe mają poinformować o tym klientów na stronie od 12-20.

- **Inicjatywa 1.** Nowy próg działa od 12-01, czyli w szczycie świątecznym. Obietnica darmowej dostawy nie może sugerować terminów, których magazyn w tych dniach nie dotrzyma. Sprawdź treści promocji i komunikaty o czasie dostawy.
- **Inicjatywa 2.** Panel statusu zamówienia wchodzi 12-10, więc będzie działał w czasie inwentaryzacji. Klient, który zamówi 12-28, zobaczy status „przyjęte” przez kilka dni. Panel powinien pokazywać prawdziwą datę wysyłki albo przynajmniej nie wywoływać pytań do obsługi klienta. Zdecyduj, czy komunikat o przesunięciu wysyłki mieści się w zawężonym zakresie panelu, czy to osobna sprawa dla strony. Tę decyzję trzeba podjąć przed 12-10, bo później dojdzie jej koszt zmiany po wydaniu.

Termin informacji na stronie (12-20) wypada po wydaniu panelu, więc oba terminy da się pogodzić.

## 3. Incydent BLIK (02) — inicjatywa 3, ryzyko do obserwacji (bez pilnej akcji)

Awaria u dostawcy trwała 2 h 40 min (11-12, 18:05–20:45), skutkowała ok. 1 900 nieudanymi płatnościami i szacowaną utratą ok. 240 zamówień. Dostawca deklaruje 99,95% dostępności, a to pierwszy incydent w 2026 r. Wycofanie płatności za pobraniem od 2027-02-01 zwiększy zależność od płatności online. Klient, który dziś w razie problemu z płatnością wybrałby pobranie, nie będzie miał tej opcji.

Nie wnioskuję z jednego incydentu, że plan jest zły. Warto jednak:
- ocenić, czy przy awarii jednej metody klient widzi czytelną alternatywę (karta, przelew),
- wziąć nowy alert (błędy BLIK > 5% w 10 min) pod uwagę w planie wdrożenia 02-01,
- dopisać niedostępność płatności online do rejestru ryzyk inicjatywy.

## 4. Design System v4 (01) — inicjatywa 2, sprawdzenie zależności

Dwie zmiany mogą dotyczyć panelu statusu:
- **Komponent „Timeline”** (oś czasu, wariant pionowy i poziomy) pasuje do wizualizacji statusu zamówienia. Pokusa jest oczywista, ale zakres panelu jest zawężony i termin to 12-10. Zdecyduj świadomie, czy używasz go teraz, czy zostawiasz na później.
- **Wycofany „Badge v2”.** Jeśli panel pokazuje statusy w tym komponencie, zbuduj go od razu na jego następcy. Migracja tokenów (tryb ciemny) trwa do 2027-01-31, czyli po Twoim wydaniu. Zapytaj zespół frontendu, czy panel jest od początku zgodny z nowymi tokenami, żeby nie robić poprawek zaraz po release.

Nie wiem, z jakich komponentów budowany jest panel, więc to pytania do zespołu, a nie potwierdzone problemy.

## Czego nie zgłaszam

Pozostałe materiały (OKR marketingu, opinie ze sklepów z aplikacjami, aktualizacja bibliotek bezpieczeństwa) nie mają w treści żadnego powiązania z Twoimi trzema inicjatywami.
