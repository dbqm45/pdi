Tak, z materiałów coś wynika, i to głównie z analizy Zespołu Danych (09). Aktualizacja UX (10) nie zmienia zakresu funkcjonalnego, więc dla inicjatywy jest neutralna.

## Co wynika z analizy danych (09)

**1. Panel statusu nie rozwiąże głównej przyczyny zgłoszeń.**
- 61% zgłoszeń o status dotyczyło zamówień, w których status w aplikacji był nieaktualny o ponad 24 godziny. Zdarzenie logistyczne już nastąpiło, ale nie trafiło do OMS.
- Panel pokaże klientowi to, co jest w OMS. Gdy dane są spóźnione, panel pokaże spóźniony status, a klient dalej będzie pisał do obsługi.
- Przyczyna leży w integracji z nowym przewoźnikiem, nie w sposobie prezentacji statusu.

**2. Analiza wskazuje konkretną przyczynę.**
- Awarie webhooków nowego przewoźnika wypadły w tygodniach 19 i 24. To skoki z raportu Q2, a liczba zgłoszeń była wtedy ok. 3 razy wyższa niż średnio.
- Mediana opóźnienia zdarzenia „przekazane przewoźnikowi” wynosi 31 godzin dla nowego przewoźnika i 2 godziny dla pozostałych.
- Wzrost zgłoszeń w Q2, który zlecił Kierownik Obsługi Klienta, najprawdopodobniej wiąże się z tym przewoźnikiem.

**3. Panel pomoże w mniejszej części przypadków.**
- 23% zgłoszeń dotyczyło zamówień z aktualnym statusem. Klient pytał o znaczenie statusu lub przewidywaną datę dostawy.
- Tu czytelny panel z opisami etapów i datą dostawy może realnie odciążyć obsługę.
- Pozostałe 16% to „inne lub nie do ustalenia”. Nie wiadomo, ile z tego panel by objął.

## Co bym zmienił lub dodał do inicjatywy

- **Cel i miara sukcesu.** Jeśli panel miał obniżyć liczbę zgłoszeń o status, to bez naprawy opóźnień danych efekt będzie ograniczony. Zakładam, że uzasadnienie decyzji sprzed miesiąca zawierało takie założenie [niezweryfikowane: nie widziałem tego uzasadnienia]. Warto je zestawić z tymi liczbami i ustalić realistyczny cel, np. odciążenie głównie w tych 23%.
- **Naprawa integracji z przewoźnikiem jako zależność lub równoległy wątek.** Potrzebny jest właściciel, termin i monitoring opóźnień webhooków. Bez tego panel działa na złych danych.
- **Uczciwa prezentacja świeżości danych w panelu.** Panel powinien pokazywać znacznik „ostatnia aktualizacja” i komunikat, gdy status jest podejrzanie stary. Dzięki temu klient nie traktuje starego statusu jako aktualnego.
- **Treści pod 23% zgłoszeń.** Wyjaśnienie statusów i widoczna przewidywana data dostawy. UX Writer już skracał opisy etapów, więc warto sprawdzić, czy skrócenie do 90 znaków nie wycina informacji potrzebnych do odpowiedzi na te pytania.
- **Raport dla zlecającego.** Kierownik Obsługi Klienta zlecił analizę w związku ze wzrostem w Q2. Warto mu przekazać wniosek: źródłem jest opóźnienie danych od przewoźnika, nie brak panelu.

## Zastrzeżenia do danych

- Analiza pokazuje związek, nie dowodzi przyczynowości. Mocniejsze argumenty to skoki w tygodniach awarii i różnica 31 h kontra 2 h.
- Nie mamy punktu odniesienia. Nie wiemy, jaki odsetek wszystkich zamówień miał nieaktualny status, więc 61% nie mówi, jak bardzo nieaktualność zwiększa szansę na zgłoszenie.
- Autorzy sami wskazują ograniczenia: kategoryzacja ręczna (możliwe błędy) i próba z jednego kwartału (Q2 2026). Nowy przewoźnik działa od tygodnia 18, więc dane obejmują tylko jego pierwsze tygodnie, które mogły być nietypowe.
- Dane mają kilka miesięcy. Przed decyzją warto sprawdzić, czy sytuacja z przewoźnikiem nie zmieniła się od Q2 [niezweryfikowane].

## Co wynika z aktualizacji UX (10)

- Zmiany to ikony z nowej biblioteki, kolor akcentu (kontrast WCAG AA, zgodnie z deklaracją autora, nie sprawdzałem), skrócone opisy i stan pusty dla zamówień sprzed wdrożenia.
- Autor zaznacza „brak zmian w zakresie funkcjonalnym”, więc nie ma wpływu na zakres, harmonogram ani architekturę.
- Jedyne powiązanie z analizą to uwaga o opisach etapów, opisana wyżej. Stan pusty dla starych zamówień nie dotyka problemu nieaktualnych statusów.

## Podsumowanie

Nie ma powodu, żeby przerywać budowę panelu. Warto jednak zmienić oczekiwania co do jego efektu i dodać do inicjatywy wątek naprawy opóźnień z nowym przewoźnikiem oraz oznaczanie świeżości danych w panelu. Bez tego główna przyczyna zgłoszeń (61%) pozostanie.
