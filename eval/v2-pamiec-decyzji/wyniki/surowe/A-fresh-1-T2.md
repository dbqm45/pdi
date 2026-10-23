Z siedmiu materiałów trzy wymagają Twojej uwagi. Przy dwóch z nich (01 i 06) jest też rzecz do sprawdzenia, której materiał nie rozstrzyga.

## 1. Wyniki testu A/B progu dostawy (05) - inicjatywa 1, próg 99 zł od 2026-12-01

Test potwierdza kierunek decyzji. Zespół Danych pisze, że efekt z pilotażu w 3 miastach utrzymuje się w skali kraju, ale jest nieco niższy.

- Konwersja w koszykach 99-149 zł rośnie o 5,8% (95% CI: +4,1% do +7,5%). Dolna granica przedziału jest wyraźnie dodatnia.
- Konwersja ogółem rośnie tylko o 0,9%.
- Średnia wartość koszyka spada o 3,4%, bo część klientów przestaje dobierać produkty do 149 zł.
- Udział zwrotów się nie zmienia.

Dlaczego to wymaga uwagi:
- Oczekiwania wobec efektu trzeba skorygować do liczb z testu krajowego, a nie z pilota. Jeśli w uzasadnieniu biznesowym są liczby z pilota, popraw je przed startem.
- Raport nie podaje wyniku netto, czyli przychodu ani marży po uwzględnieniu kosztu dostawy. Przy jednoczesnym wzroście konwersji i spadku wartości koszyka to jest brakujące ogniwo. Zapytaj Zespół Danych, czy mają przeliczenie, i jeśli nie, poproś o nie przed 2026-12-01. Nie wiem, czy ono już istnieje.
- Spadek wartości koszyka o 3,4% warto uwzględnić w komunikacji i w sposobie mierzenia sukcesu po starcie. Mierz konwersję w segmencie 99-149 zł razem z wartością koszyka, bo sama konwersja ogółem (+0,9%) wypada słabo.

## 2. Magazyn - inwentaryzacja (06) - inicjatywy 1 i 2

Inwentaryzacja trwa od 2026-12-28 do 2026-12-30. Zamówienia złożone po 2026-12-27 zostaną wysłane dopiero 2026-12-31. Magazyn prosi zespoły produktowe o informację na stronie od 2026-12-20.

- Panel statusu zamówienia (release 2026-12-10) wejdzie na produkcję przed tą przerwą. Panel będzie pokazywał status i termin wysyłki, więc klienci zamawiający w okolicach świąt zobaczą w nim opóźnienie. Ustal z zespołem, skąd panel bierze datę wysyłki. Jeśli to jest wyliczana obietnica, a nie ręczny komunikat, trzeba uwzględnić tę przerwę. To zależy od zakresu panelu, którego nie znam.
- Próg 99 zł obowiązuje od 2026-12-01, więc przerwa wypada w okresie z darmową dostawą dla tańszych koszyków. Klienci kupujący w tym czasie dostaną dostawę z kilkudniowym opóźnieniem. Tego nie da się zmienić, ale informacja o terminie przy zamówieniu powinna być spójna z komunikatem magazynu. Warto też ustalić z obsługą klienta, czy spodziewają się wzrostu pytań o status.
- Termin 2026-12-20 na informację na stronie wypada 10 dni po release panelu. Ustal z magazynem i swoim zespołem, kto za nią odpowiada i czy panel jest właściwym miejscem na ten komunikat.

## 3. Design System v4 (01) - inicjatywa 2, panel statusu

Dla panelu statusu istotne są dwie pozycje.

- Komponent Timeline (oś czasu, wariant pionowy i poziomy) pasuje do wizualizacji statusu zamówienia. Sprawdź z projektantem, czy panel ma go użyć. Zakres jest zawężony, więc to może być oszczędność pracy, ale może też zmienić zakres. Zdecyduj to przed końcem projektu UI, bo release jest 2026-12-10.
- Wycofany Badge v2: jeśli projekt panelu używa Badge v2 do oznaczania statusów, trzeba go zastąpić, zanim panel trafi na produkcję. Nie wiem, czy panel go używa, więc to do sprawdzenia.

Migracja tokenów kolorów do 2027-01-31 wypada po release panelu. Panel powinien od razu powstać na nowych tokenach, żeby nie wymagał poprawek tuż po wdrożeniu.

## Pominięte, bo nie dotyczą Twoich inicjatyw

- 02 (incydent BLIK): jednorazowa awaria u dostawcy, naprawiona, z dodanym alertem. Nie zmienia planu wycofania płatności za pobraniem od 2027-02-01. Jedyna uwaga: wycofanie COD zwiększy zależność od płatności online, więc jeśli takie incydenty się powtórzą, wróć do tematu. Na razie to pierwszy incydent w 2026 r., więc nie traktuję tego jako sprawy do działania.
- 03 (OKR marketingu), 04 (opinie w sklepach z aplikacjami), 07 (aktualizacja biblioteki logowania w backendzie): brak związku z progiem dostawy, panelem statusu ani płatnością za pobraniem. Przy 07 nie wiem, czy usługi Twoich inicjatyw są na liście zespołu Platforma. To dotyczy zespołu technicznego, nie Ciebie.
