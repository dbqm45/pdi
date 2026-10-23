Tak, wynika z nich jedna istotna rzecz. Dotyczy ona głównie pliku 09 (analiza Zespołu Danych). Plik 10 (UX v3) nie zmienia zakresu funkcjonalnego, więc wpływa na inicjatywę tylko marginalnie.

## Co wynika z analizy danych (plik 09)

**1. Panel sam nie usunie głównej przyczyny zgłoszeń.**
- 61% zgłoszeń o status dotyczyło zamówień, w których status w aplikacji był nieaktualny o ponad 24 godziny. Zdarzenie logistyczne już zaszło, ale nie dotarło do OMS.
- Panel pokaże ten sam nieaktualny status, tylko w lepszej formie. Klient dalej będzie widział, że "nic się nie dzieje", i dalej napisze do obsługi.
- Ładniejszy panel z nieaktualnymi danymi może nawet pogorszyć sytuację, bo wygląda wiarygodnie, a pokazuje nieprawdę.

**2. Główna przyczyna leży w integracji z nowym przewoźnikiem, a nie w interfejsie.**
- Mediana opóźnienia zdarzenia "przekazane przewoźnikowi" wynosi 31 godzin dla nowego przewoźnika (od tygodnia 18). Dla pozostałych przewoźników wynosi 2 godziny.
- W tygodniach 19 i 24 były awarie webhooków i zgłoszeń było ok. 3 razy więcej niż zwykle. To tłumaczy skoki w raporcie Q2, które były powodem zlecenia analizy.

**3. Panel może pomóc w mniejszej części problemu.**
- 23% zgłoszeń dotyczyło zamówień z aktualnym statusem, gdzie klient pytał o znaczenie statusu lub przewidywaną datę dostawy. Tu dobre opisy etapów i data dostawy w panelu mogą realnie zmniejszyć liczbę zgłoszeń.
- Pozostałe 16% to "inne lub nie do ustalenia".

## Co bym zrobił

Nie sugeruję zatrzymywania prac. Decyzja zapadła, a panel ma wartość dla tych 23%. Zmieniłbym jednak następujące rzeczy.

1. **Dodać zależność od naprawy integracji z nowym przewoźnikiem.** Bez tego inicjatywa nie osiągnie efektu, jeśli jej celem jest redukcja zgłoszeń o status. Trzeba ustalić, kto jest właścicielem naprawy i w jakim terminie.
2. **Uwzględnić w panelu nieaktualne dane.** Proponuję pokazywać "ostatnia aktualizacja: [data i godzina]". Dla zamówień bez nowego zdarzenia przez dłuższy czas proponuję komunikat w rodzaju "czekamy na informację od przewoźnika". To zmiana funkcjonalna, więc wymaga decyzji, ale jest tania i trafia w główny problem. Plik 10 (UX v3) tego nie przewiduje. Zawiera tylko stan pusty dla zamówień sprzed wdrożenia.
3. **Ustalić miarę sukcesu osobno dla każdego segmentu.** Przykład: liczba zgłoszeń dla zamówień z aktualnym statusem (panel) i liczba zgłoszeń dla zamówień z opóźnionym statusem (integracja). Inaczej poprawa lub brak poprawy będzie trudna do zinterpretowania.
4. **Sprawdzić, na jakich założeniach opierała się decyzja o budowie panelu.** Jeśli zakładała, że panel zmniejszy liczbę zgłoszeń o status, ta analiza osłabia to założenie. Nie znam dokumentu decyzji, więc tylko wskazuję, że warto to porównać.

## Zastrzeżenia do samej analizy

- To jest korelacja z jednej próby (1 200 zgłoszeń, jeden kwartał), a kategoryzacja była ręczna. Autorzy sami to zaznaczają.
- 61% to udział wśród zgłoszeń. Analiza nie mówi, jaka część wszystkich zamówień miała nieaktualny status, ani ilu klientów z nieaktualnym statusem w ogóle nie napisało. Nie da się więc z niej policzyć, o ile spadłaby liczba zgłoszeń po naprawie integracji. Takie liczby byłyby szacunkiem.
- Kierunek wniosku jest jednak spójny: skoki zgłoszeń zbiegają się z awariami webhooków, a opóźnienie dotyczy konkretnego przewoźnika. Nie wygląda to na artefakt klasyfikacji.

## Plik 10 (UX v3)

- Zmiany są kosmetyczne: nowe ikony, kolor akcentu (kontrast sprawdzony, WCAG AA), skrócone opisy do 90 znaków i stan pusty dla starszych zamówień.
- Nie zmienia to zakresu ani harmonogramu.
- Skrócone opisy etapów warto jeszcze przejrzeć pod kątem tych 23% zgłoszeń o znaczenie statusu. Opisy mają wyjaśniać, co status oznacza i co będzie dalej, a 90 znaków to mało miejsca.
