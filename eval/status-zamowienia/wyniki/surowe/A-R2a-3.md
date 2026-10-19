# Odpowiedź na nowe materiały [09] i [10]

**Werdykt.** Dokument [09] w dużej mierze potwierdza hipotezę, którą wskazałem jako alternatywną i najbardziej ryzykowną (pkt 3.1 i 3.2 wcześniejszej oceny), i osłabia założenie A1, od którego zależała decyzja. Dokument [10] nie wnosi nic do tej kwestii. Rekomenduję, by nie kontynuować inicjatywy w obecnym kształcie, tylko przeprowadzić szybkie przeplanowanie: naprawa przepływu zdarzeń od przewoźnika wchodzi na pierwsze miejsce, a zakres panelu zostaje zawężony i uzależniony od świeżości danych.

Oznaczenia źródeł jak poprzednio, [09] to analiza Zespołu Danych, [10] to aktualizacja UX v3. "Wyliczenie własne" oznacza liczby, które policzyłem z podanych danych.

## 1. Co [09] rozstrzyga

- **Dominująca przyczyna to nieaktualny status, nie brak szczegółów.** 61% zgłoszeń dotyczyło zamówień, w których status w aplikacji był nieaktualny o ponad 24 godziny, bo zdarzenie logistyczne nie dotarło do OMS [09]. Tylko 23% to pytania przy aktualnym statusie (znaczenie statusu lub data dostawy) [09]. To jest dokładnie przypadek z pkt 3.2 (nieaktualny status vs brak szczegółu), który w [01] i [07] nie był uwzględniony.
- **Wyjaśnia skok z Q2.** Piki w tygodniach 19 i 24 to awarie integracji webhooków z nowym przewoźnikiem, z ok. 3-krotnie wyższą liczbą zgłoszeń [09]. Mediana opóźnienia zdarzenia "przekazane przewoźnikowi" wynosi 31 godzin dla nowego przewoźnika i 2 godziny dla pozostałych [09]. Pasuje to do informacji z [04] o zmianie przewoźnika od tygodnia 18. Hipoteza z pkt 3.1 się potwierdziła. Wyjaśnia też tygodnia 24, którego wcześniej nie umiałem wytłumaczyć.
- **Dane są mocniejsze niż to, co było wcześniej.** Losowa próba 1 200 zgłoszeń zestawiona z logami OMS i webhooków [09] to dokładnie ten typ sprawdzenia, który proponowałem w sekcji 5 (z większą próbą).

## 2. Co to znaczy dla inicjatywy

**Skala potencjalnego efektu panelu (wyliczenie własne).** Przy założeniu z mojej poprzedniej oceny, że status to ok. 3,7 kontaktu na 100 zamówień (38% z 9,8 **[założenie: ten sam okres]**), a KR 1.1 wymaga spadku o 1,8 pkt [06]:
- Kontakty przy aktualnym statusie (23%) to ok. 0,86 pkt na 100 zamówień. Nawet gdyby panel wyeliminował je wszystkie, nie dowiezie samodzielnie KR (potrzeba 1,8).
- Kontakty związane z nieaktualnym statusem (61%) to ok. 2,3 pkt. Ich usunięcie przekraczałoby wymagany spadek.
- Realistycznie panel nie usunie wszystkich kontaktów z żadnej z grup, więc to górne granice, nie prognozy.

**Panel bez naprawy danych może zaszkodzić.** Panel zasilany tymi samymi opóźnionymi zdarzeniami [07], [08] pokaże dokładniejszy, ale błędny przebieg, na przykład "w kompletacji" przez 31 godzin po faktycznym przekazaniu kuriera. Dla klientów z 61% grupy może to zwiększyć frustrację i zwiększyć liczbę kontaktów, nie zmniejszyć. Kryteria akceptacji w [08] nic o tym nie mówią: wymagają pokazania "wszystkich zdarzeń zapisanych w OMS", czyli panel będzie poprawny względem OMS, a nie względem rzeczywistości.

**Panel nie jest bezwartościowy.** Pozostaje potrzeba informacji o znaczeniu statusów i dacie dostawy (23% w [09], 6 z 8 i 7 z 8 osób w [02]). To przemawia za zawężonym zakresem, nie za zamknięciem pomysłu.

## 3. Zastrzeżenia do [09]

Nie wynika z nich odrzucenie wniosków, tylko dokładniejsze sformułowanie, co wiemy.
- **Brak punktu odniesienia.** Wiemy, że 61% zgłoszeń dotyczyło zamówień z nieaktualnym statusem. Nie wiemy, jaki odsetek wszystkich zamówień miał nieaktualny status (i ilu klientów z takim statusem nie napisało). To mierzy związek, nie siłę przyczynowości. Mimo to zbieżność trzech faktów (mediana 31 godzin vs 2 godziny, piki w czasie awarii, 61% w próbie) jest mocna.
- **Kategoryzacja ręczna** (autorzy sami to zaznaczają [09]) i **jeden kwartał**. Q2 zawierał awarie, więc baza Q2 jest prawdopodobnie zawyżona. Nie wiadomo, jak wygląda sytuacja w Q3.
- **Nie wiemy, czy awaria integracji została naprawiona.** [09] opisuje stan z Q2. Jeśli naprawa nastąpiła, efekt powinien być już widoczny w danych Q3 (kontakty na 100 zamówień, osobno dla nowego przewoźnika). Jeśli nie, to zasadniczy problem trwa.
- **16% "inne lub nie do ustalenia"** pozostaje nieobjaśnione.

## 4. Dokument [10] (UX v3)

Zmiany to ikony, kolor akcentu, skrócone opisy etapów do 90 znaków i stan pusty dla zamówień sprzed wdrożenia [10]. Wszystkie są kosmetyczne i nie zmieniają zakresu funkcjonalnego ("Brak zmian w zakresie funkcjonalnym" [10]). Nie wpływają na ocenę. Dwie drobne uwagi:
- Skrócenie opisów do 90 znaków mieści się w limicie 120 z [08].
- Projekt nie ma stanu dla przypadku "dane nieaktualne lub brakujące". To ten przypadek jest dziś główną przyczyną kontaktów, więc warto go dodać.

## 5. Rekomendacja i następne kroki

**Rekomendacja: zatrzymać dalszą rozbudowę panelu w obecnym zakresie do czasu ustalenia stanu integracji i przeplanować.** Koszt dotychczas poniesiony (miesiąc pracy) jest kosztem utopionym i nie powinien decydować o dalszym kierunku. Liczy się to, co zostało do zrobienia i jaki efekt da.

1. **Od razu (godziny):** poinformować sponsora (Head of Product, właściciel KR 1.1) o [09]. Uzgodnić, czy zespoły kontynuują, czy przechodzą do przeplanowania. Sprawdzić, kto odpowiada za integrację z nowym przewoźnikiem i czy awaria jest już naprawiona.
2. **Tanio (1–2 dni):** sprawdzić dane za Q3. Kontakty statusowe na 100 zamówień per przewoźnik i tydzień oraz aktualne opóźnienie webhooków (mediana i p95). To rozstrzyga, czy problem trwa.
3. **Przeplanować zakres w kolejności wartości:**
   - naprawa i monitoring integracji (alert na opóźnienie zdarzeń, np. powyżej progu ustalonego z tech leadem),
   - zawężony panel lub lekki wariant (czytelne nazwy, data dostawy), tylko jeśli dane są świeże,
   - do panelu dodać kryterium akceptacji dla świeżości (np. "ostatnia aktualizacja" i zachowanie, gdy zdarzenia brakują), nie tylko zgodność z OMS.
4. **Metryka rezultatu** (nadal brakująca, wymagana w [06]): baza, cel, termin, pomiar osobno dla kontaktów przy statusie aktualnym i nieaktualnym. Pozwoli to ocenić, czy panel w ogóle działa, gdy dane są dobre.
5. **Wnioski procesowe:** hipotezy dotyczące przyczyny należało zweryfikować przed przekazaniem do estymacji. Analiza w [09] zajęła Zespołowi Danych niewiele czasu, a zmieniła obraz problemu. Warto to uwzględnić przy podobnych decyzjach.

**Czego nie wiem:** nie mam informacji o postępie prac, o koszcie wykonanej części ani o tym, czy integracja została już poprawiona. Przy braku tych informacji rekomenduję przeplanowanie, nie zamknięcie projektu. Jeśli okaże się, że większość pracy jest już wykonana, a integracja naprawiona, rozsądnym wariantem jest dokończenie zawężonego panelu z kryterium świeżości.
