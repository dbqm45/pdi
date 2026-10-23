# Aktualizacja po nowych materiałach (09, 10)

**Krótko:** analiza Zespołu Danych [09] potwierdza najpoważniejszą z alternatyw, które wskazywałem wcześniej (zmiana przewoźnika i nieaktualne statusy). Diagnoza z opisu inicjatywy ("brak informacji w interfejsie jest przyczyną") nie jest prawdziwa dla większości kontaktów. Rekomenduję zatrzymać wydanie panelu w obecnym kształcie i przestawić kolejność prac. Nie rekomenduję porzucenia inicjatywy.

Oznaczenia źródeł jak poprzednio: [01] opis, [02] wywiady, [03] analityka, [04] raport obsługi, [05] team lead, [06] OKR, [07] decyzja, [08] ORD-412, [09] analiza Zespołu Danych, [10] aktualizacja UX.

## Co mówi [09]

- **61%** zgłoszeń o status dotyczyło zamówień, w których status w aplikacji był nieaktualny o ponad 24 godziny [09]. To potwierdza wątek z [02, U7] i [05] ("dlaczego nadal w przygotowaniu", kurier już dzwonił).
- **23%** to pytania o znaczenie statusu lub datę dostawy przy aktualnym statusie [09]. Tylko ta część jest tym, co panel adresuje w pierwotnym założeniu.
- **16%** to inne lub nieustalone [09].
- **Przyczyna jest zlokalizowana:** nowy przewoźnik od tyg. 18, mediana opóźnienia zdarzenia "przekazane przewoźnikowi" 31 h, przy 2 h u pozostałych. Skoki w tyg. 19 i 24 to awarie webhooków, z ok. 3-krotnie wyższą liczbą zgłoszeń [09, zgodnie z [04]].

Odpowiada to wprost na pytanie, które stawiałem w punktach 3 i 4 pierwszej analizy (alternatywa nr 1, brakujące dane o opóźnieniach). Ta część była do ustalenia przed estymacją.

## Co to zmienia w rachunku

Liczby poniżej to moje wyliczenia z [04], [06] i [09]. Zakładam, że 9,8 kontaktu na 100 zamówień z [06] dotyczy porównywalnego okresu.

- Status to ok. 3,7 kontaktu na 100 zamówień (38% × 9,8). KR 1.1 wymaga spadku z 9,8 do 8,0, czyli o 1,8 [06].
- **Gdyby panel całkowicie usunął wszystkie kontakty z grupy 23%**, daje to ok. 0,86 na 100 zamówień, czyli wynik ok. 8,9, nie 8,0. Realnie panel usunie część tej grupy, więc wkład do KR będzie wyraźnie mniejszy.
- **Naprawa opóźnień zdarzeń** adresuje grupę 61%, czyli ok. 2,3 na 100 zamówień. Sama w sobie mogłaby dać ok. 7,5, więc cel KR byłby w zasięgu, przy zastrzeżeniach niżej. To nie jest zakres ORD-412 [08], a zasadnicza część wartości leży właśnie tam.
- Mój wcześniejszy próg decyzyjny ("przynajmniej ok. 50% kontaktów to podtypy, które panel adresuje przy poprawnych danych") **nie jest spełniony**: jest 23%, nie 50%. Wg tego kryterium odpowiedź brzmiałaby "najpierw coś innego".

**Zastrzeżenia do [09], żeby nie przesadzić:**

1. **Próba z Q2 jest zawyżona przez awarie.** Dwa tygodnie miały ok. 3-krotny wolumen [09]. Udział 61% i baza 38% mogą w stanie ustalonym być niższe. To zmniejsza zarówno potencjał naprawy integracji, jak i panelu. Stąd potrzeba danych za Q3.
2. **Nie wiadomo, jaka część z 61% przypada na nowego przewoźnika**, a jaka na pozostałych. Mediana 2 h u pozostałych sugeruje koncentrację na nowym, ale podziału kontaktów brak [09].
3. **Nie wiadomo, czy integracja została już naprawiona** (analiza jest z 20.08). Jeśli tak, część problemu zniknęła niezależnie od panelu i trzeba ją odjąć od bazy.
4. **Próg 24 h jest arbitralny**, a klasyfikacja ręczna [09]. Kierunek wniosku jest jednak mocny: różnica 31 h kontra 2 h i zbieżność z tygodniami skoków trudno wytłumaczyć błędem klasyfikacji.
5. **Nie wiem, czy panel osłabiłby kontakty o nieaktualny status** [założenie]. Może pomóc, jeśli pokaże "ostatnia aktualizacja" i uczciwie wyjaśni brak danych. Może też zaszkodzić, bo pokaże widocznie błędny stan. Tego żaden materiał nie testował.

## Uwaga do [10]

Aktualizacja UX [10] to kosmetyka (ikony, kolor, długość opisów, stan pusty dla starych zamówień) i słusznie deklaruje brak zmian funkcjonalnych. Nic w niej nie jest błędne. Problem jest przez pominięcie: projekt **nie ma stanu "dane nieaktualne lub brakujące"**, a właśnie z takimi przypadkami wiąże się większość kontaktów [09]. Opis do 90 znaków [10] jest zgodny z limitem 120 [08], więc to nie sprzeczność.

## Co bym teraz zrobił

Inicjatywa jest już w realizacji, więc część nakładu mogła zostać poniesiona. Nie znam jej stanu ani kosztów [niezweryfikowane]. Decyzję traktowałbym według przyszłych kosztów, nie dotychczasowych.

1. **Natychmiast: właściciel i termin naprawy integracji z nowym przewoźnikiem** (opóźnienie 31 h do poziomu zbliżonego do pozostałych, monitoring i alert na opóźnienie zdarzeń). To najtańsza i największa dźwignia wg [09]. Dziś brak właściciela, jak w [05] ("Działania: brak").
2. **Panel: nie wydawać go przed naprawą opóźnień.** Prace frontowe mogą trwać, ale wydanie bramkować metryką aktualności zdarzeń (np. p95 opóźnienia na przewoźnika poniżej uzgodnionego progu). Inaczej panel pokaże widoczną, błędną oś czasu, co zagraża KR 1.2 (NPS po dostawie ≥ 42) [06].
3. **Zmienić zakres ORD-412 [08]:**
   - dodać stan "dane nieaktualne lub brakujące" i znacznik czasu ostatniej aktualizacji;
   - zastąpić kryterium "100% zamówień wyświetla się poprawnie" kryteriami aktualności;
   - dodać datę dostawy jako wymaganie, nie opcję "jeśli dostępna", bo to czego klienci chcą najbardziej [02];
   - zdefiniować metrykę efektu: kontakty o status na 100 zamówień, z bazą i celem, zgodnie z regułą [06].
4. **Tanie działania, które nie wymagają panelu:** uproszczenie nazw statusów i data dostawy w obecnym ekranie [02, rekomendacje 1-2]. Adresują część z grupy 23% za ułamek kosztu.
5. **Dane do uzupełnienia (1-2 dni):** udział kontaktów per przewoźnik w próbie, status naprawy integracji, tygodniowy przebieg kontaktów o status za Q3 oraz wersja bazowa "stan ustalony" bez tygodni awarii.

## Rekomendacja

**Kontynuować inicjatywę, ale ją przesekwencjonować:** najpierw integracja z przewoźnikiem, panel jako drugi krok z poprawionym zakresem i warunkiem wydania. Jeśli po naprawie integracji i danych za Q3 grupa "znaczenie statusu i data dostawy" okaże się nadal duża, panel ma uzasadnienie. Jeśli nie, to oszczędność dwóch sprintów dwóch zespołów jest wyraźna. Uczciwie zaznaczam, że ten wniosek zmieniłby się, gdyby dane Q3 pokazały, że 23% jest w stanie ustalonym znacznie większe.

Warto też zapisać na najbliższym spotkaniu, że założenie z [01] i [07] ("brak informacji w interfejsie jest przyczyną") zostało zweryfikowane negatywnie dla większości kontaktów. Zapis tej zmiany w decyzji jest ważniejszy niż samo przesunięcie terminów.
