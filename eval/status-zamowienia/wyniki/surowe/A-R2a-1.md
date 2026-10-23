# Aktualizacja po nowych materiałach [09] i [10]

**Krótko:** [09] potwierdza alternatywną przyczynę, o której pisałem poprzednio (status nieaktualny zamiast braku informacji w UI). Skala jest większa, niż zakładałem. Nie sugeruję wstrzymania całej inicjatywy. Sugeruję **natychmiastową zmianę zakresu i kolejności prac**, bo obecny plan w [01]/[08]/[10] adresuje mniejszą część problemu, a największą pomija. [10] niczego z [09] nie uwzględnia.

Oznaczenia jak wcześniej: [01]–[08] to poprzednie materiały, [09] analiza Zespołu Danych, [10] aktualizacja UX v3.

## 1. Co [09] zmienia

- **Przyczyna dominująca jest operacyjna.** 61% zgłoszeń o status dotyczyło zamówień, w których status w aplikacji był nieaktualny o ponad 24 godziny [09]. Zespół Danych sprawdził to w logach OMS i webhooków, a nie na podstawie deklaracji klientów, więc to dowód mocniejszy niż wywiady [02] czy notatka [05]. Zgadza się z U7 [02], z notatką team leada [05] i z uwagą tech leada [07].
- **To, co panel faktycznie adresuje, to 23%.** Tyle zgłoszeń dotyczyło aktualnego statusu, gdy pytanie było o znaczenie statusu lub datę dostawy [09]. Reszta to 16% inne/nieustalone.
- **Źródło problemu jest wskazane.** Nowy przewoźnik od tygodnia 18: mediana opóźnienia zdarzenia „przekazane przewoźnikowi” w OMS wynosi 31 godzin, dla pozostałych 2 godziny. W tygodniach 19 i 24 były awarie webhooków, a zgłoszeń było ok. 3 razy więcej niż średnio [09]. To wyjaśnia skoki z [04], które wskazywałem jako niewyjaśnione.
- **Mój próg się spełnił.** Poprzednio zaproponowałem: jeśli (c) status nieaktualny i (d) realne opóźnienie dominują nad (a) niezrozumiałym statusem i (b) datą dostawy, najpierw trzeba naprawiać dane i operacje, a nie UI. [09] pokazuje 61% do 23%. Uwaga: to przybliżone dopasowanie moich kategorii do kategorii Zespołu Danych [założenie].

## 2. Co to oznacza dla efektu inicjatywy

Rachunek na liczbach z [04], [06] i [09] (moje przeliczenie, [założenie] że udziały z próby dotyczą całego kwartału):

- Kontakty o status to ok. 3,7 na 100 zamówień (0,38 × 9,8). KR 1.1 wymaga redukcji o ok. 1,8 na 100 [06].
- 23% z 3,7 to ok. **0,85 na 100**. To maksimum, jeśli panel całkowicie wyeliminuje kontakty z tej grupy, a to jest nierealne. Realnie będzie to ułamek tej wartości.
- Panel zbudowany na zdarzeniach z OMS **nie usuwa** 61%. Nieaktualna oś czasu to ten sam problem w nowej formie, a może gorszy: klient zobaczy szczegółowy przebieg, który jest sprzeczny z tym, co mówi kurier. Tego zagrożenia wcześniej nie było w opisie ryzyk [08].
- Wniosek: sam panel nie osiągnie KR 1.1 i nie powinien być przedstawiany jako główne narzędzie tego KR. Największa dźwignia leży w naprawie integracji z nowym przewoźnikiem. Czy jest tańsza niż panel, nie wiem, bo materiały nie zawierają jej kosztu.

## 3. Zastrzeżenia do [09] (żeby nie przesadzić w drugą stronę)

- **Próba losowa z całego Q2, nie warstwowana.** Tygodnie 19 i 24 miały ok. 3 razy więcej zgłoszeń, więc mogą zawyżać udział 61%. W „zwykłych” tygodniach udział może być niższy. Tego [09] nie rozdziela [niezweryfikowane].
- **Ręczna kategoryzacja** i **jeden kwartał** [09]. Zespół sam to zaznacza.
- **Nieaktualność oznacza przyczynę tylko częściowo.** Fakt, że status był stary, nie dowodzi, że klient nie napisałby przy aktualnym statusie. Zależność przyczynowa jest wysoce prawdopodobna, ale to wnioskowanie.
- **Brak rozbicia na przewoźników.** Nie wiem, jaka część z 61% przypada na nowego przewoźnika, a jaka na pozostałych. Mediana 2 godzin dla pozostałych sugeruje, że głównie nowy, ale ogon rozkładu może być długi [założenie].
- **Nie wiem, czy integracja jest już naprawiona.** [09] opisuje Q2. Potrzebne są dane z Q3, bo od tego zależy, czy 61% to stan obecny, czy historia.
- Nie podważa to uwag z poprzedniej analizy o 23%: ta część (nazwy statusów i data dostawy) jest nadal dobrze poparta [02][05].

## 4. [10] Aktualizacja UX v3

- Zmiany są sensowne i niewinne: ikony, kolor akcentu z kontrolą WCAG AA, opisy skrócone do 90 znaków (w [08] limit to 120, więc mieści się), stan pusty dla zamówień sprzed wdrożenia. Nie widzę tu problemu.
- **Ale „Brak zmian w zakresie funkcjonalnym”** to dokładnie ten problem. Projekt nadal nie ma stanu „dane nieaktualne lub opóźnione” ani „brak zdarzenia od przewoźnika”, a dotyczy to większości przypadków wg [09]. Stan pusty dotyczy tylko zamówień sprzed wdrożenia.
- Nadal nie ma też mapowania nowych etapów na obecne nazwy statusów ani decyzji o nazwach, co było tanią rekomendacją badaczki [02].

## 5. Rekomendacja

Inicjatywa jest w realizacji, więc koszt już częściowo poniesiony nie powinien decydować o dalszych krokach. Decyzja dotyczy tego, co jeszcze zmienić.

1. **Zrobić to teraz (tanie, kilka dni):**
   - Zapytać zespół integracji, czy problem z nowym przewoźnikiem został naprawiony po Q2, i pobrać dane Q3: opóźnienie zdarzeń per przewoźnik, liczba zgłoszeń o status na 100 zamówień per tydzień.
   - Poprosić Zespół Danych o rozbicie 61% według przewoźnika i według tygodni (z wyłączeniem tygodni awarii 19 i 24), żeby ocenić stan „zwykły”.
2. **Zmienić zakres panelu:**
   - Dodać do wymagań w [08] zachowanie przy nieaktualnych lub brakujących zdarzeniach (np. „ostatnia aktualizacja: …”, brak twierdzeń o etapie, którego nie potwierdzono) oraz pomiar tego stanu.
   - Nie sprzedawać panelu jako dźwigni całego KR 1.1. Zapisać oczekiwany efekt jako zakres (rząd wielkości: poniżej 0,85 na 100 zamówień) i metrykę rezultatu z wartością wyjściową, której nadal brakuje [06].
3. **Zmienić kolejność:** naprawa integracji z nowym przewoźnikiem (właściciel: zespół integracji) powinna być traktowana jako osobna inicjatywa o wyższym priorytecie i zdefiniowana z własną metryką (opóźnienie zdarzenia, odsetek zamówień ze statusem starszym niż 24 godziny). Panel bez niej dostarczy mniej, niż obiecuje [01].
4. **Rozważyć rozdzielenie dostaw:** nazwy statusów plus widoczna data dostawy (część 23% z [09], poparta w [02]) mogą wyjść wcześniej niż pełna oś czasu, jeśli zespoły mają taką możliwość [założenie, bo kosztów nie znam].

**Czego nie robiłbym:** nie zatrzymywałbym całej pracy na podstawie jednej analizy z zastrzeżeniami z pkt 3. Wystarczy, że kroki z pkt 1 potwierdzą stan obecny. Jeśli integracja jest już naprawiona, a udział nieaktualnych statusów w Q3 jest niski, uzasadnienie panelu wraca (23% to nadal duży problem), ale z mniejszym i uczciwszym oczekiwanym efektem.
