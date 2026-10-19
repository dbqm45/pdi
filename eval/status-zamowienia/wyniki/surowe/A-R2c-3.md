Tak, z materiału 09 wynika coś istotnego dla inicjatywy. Materiał 10 nie zmienia nic poza drobnym punktem do sprawdzenia.

## 1. Analiza Zespołu Danych (09): główny wniosek

Panel pokazuje status, a według analizy większość zgłoszeń o status wynika z tego, że status jest nieaktualny. Panel sam tego nie naprawi.

- 61% zgłoszeń z próby (n = 1 200, Q2 2026) dotyczyło zamówień ze statusem nieaktualnym o ponad 24 h. Zdarzenie logistyczne już zaszło, ale nie trafiło do OMS.
- Źródłem jest integracja z nowym przewoźnikiem, działającym od tygodnia 18. Mediana opóźnienia zdarzenia „przekazane przewoźnikowi" to 31 h, przy 2 h u pozostałych.
- Skoki zgłoszeń w tygodniach 19 i 24 zbiegły się z awariami webhooków. W tych tygodniach zgłoszeń było około 3 razy więcej niż średnio.
- 23% zgłoszeń dotyczyło zamówień z aktualnym statusem. Klient pytał o znaczenie statusu lub przewidywaną datę dostawy.

### Co to znaczy dla panelu

- **Panel może pogorszyć sytuację, jeśli dane zostaną takie jak są.** Klient dostanie czytelny, ładny panel, który pokazuje stary status. Zobaczy wprost, że „nic się nie dzieje", i może częściej pisać do obsługi, a nie rzadziej. Nie mam danych, które by to potwierdzały ani wykluczały. [założenie]
- **Panel adresuje bezpośrednio głównie te 23%.** Dotyczą one znaczenia statusów i daty dostawy, czyli tego, co panel może wyjaśnić.
- **Przy 61% panel pomoże tylko pośrednio.** Pomogłoby to, że klient widzi aktualność danych (np. „ostatnia aktualizacja: …"), albo komunikat przy podejrzanym opóźnieniu. Realną naprawą jest jednak integracja z przewoźnikiem i opóźnienie zdarzenia w OMS.
- **Cel i metryka sukcesu inicjatywy wymagają przeglądu.** Jeśli cel brzmi „mniej zgłoszeń o status", a naprawa integracji nie jest częścią planu, cel może być nieosiągalny samym panelem. Nie znam celu ani metryk inicjatywy, więc to jest do sprawdzenia po Waszej stronie. [niezweryfikowane]

### Rekomendacje

1. Potraktować naprawę opóźnień OMS i webhooków nowego przewoźnika jako zależność lub równoległy element inicjatywy, z właścicielem i terminem. Bez tego ryzykujemy wdrożenie panelu, który nie spełni celu.
2. Rozważyć niewielkie rozszerzenie zakresu panelu: widoczna data ostatniej aktualizacji i komunikat, gdy od ostatniego zdarzenia minęło zbyt dużo czasu. Opóźnienie jest wtedy jawne, a nie ukryte. To zmiana zakresu, więc wymaga decyzji właściciela produktu.
3. Zaplanować pomiar przed i po osobno dla zamówień od nowego przewoźnika i od pozostałych. Inaczej efekt panelu zmiesza się z efektem naprawy integracji.
4. Do celu i do raportu użyć rozbicia z analizy (61% / 23% / 16%) zamiast jednej liczby „zgłoszenia o status".

### Ograniczenia analizy

- To korelacja w próbie z jednego kwartału. Analiza nie dowodzi, że bez opóźnień zgłoszeń byłoby o 61% mniej. Część tych klientów mogłaby pisać także przy aktualnym statusie.
- Kategoryzacja była ręczna, więc możliwe są błędy klasyfikacji. Autorzy sami to zaznaczają.
- 61% dotyczy kategorii „Status zamówienia", nie wszystkich zgłoszeń.
- Analiza jest z 20 sierpnia, czyli sprzed decyzji o budowie panelu (według Ciebie sprzed około miesiąca). Nie wiem, czy decyzja uwzględniała te dane. Jeśli nie, warto zapytać Kierownika Obsługi Klienta, który ją zlecił, oraz Zespół Danych o aktualny stan integracji. Po awariach w tygodniach 19 i 24 mogło się coś zmienić. [niezweryfikowane]

## 2. Aktualizacja UX v3 (10)

Wprost nic z niej nie wynika. Dokument deklaruje brak zmian funkcjonalnych, a zmiany dotyczą ikon, koloru, długości opisów i stanu pustego. Są dwa punkty do sprawdzenia:

- **Opisy etapów skrócone do 90 znaków.** Dane pokazują, że 23% pytań dotyczy znaczenia statusu. Warto sprawdzić, czy skrócone opisy dalej wyjaśniają, co status oznacza i co będzie dalej. Przydałby się krótki test z użytkownikami albo przegląd na realnych pytaniach ze zgłoszeń.
- **Stan pusty „Szczegółowa historia jest dostępna dla zamówień od [data wdrożenia]".** To jest w porządku, ale ten komunikat nie obsługuje przypadku z analizy, czyli zamówienia z zaległym zdarzeniem. Dla tego przypadku potrzebny jest osobny stan, o którym mowa w rekomendacji 2.

Kontrast koloru akcentu został według autora sprawdzony na poziomie WCAG AA. Nie weryfikowałem tego.

## Podsumowanie

Inicjatywa nie jest podważona, ale jej skuteczność zależy od czegoś spoza panelu. Najpierw ustalcie, kto i kiedy naprawia opóźnienia danych od nowego przewoźnika. Potem zdecydujcie, czy zakres panelu obejmuje jawne pokazanie aktualności danych.
