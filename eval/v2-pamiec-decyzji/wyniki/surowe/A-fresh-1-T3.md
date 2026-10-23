Z siedmiu materiałów jeden wymaga Twojej decyzji (INT-233). Dwa kolejne warto mieć z tyłu głowy, ale niczego od Ciebie nie wymagają. Pozostałych czterech nie zgłaszam.

## Wymaga uwagi: INT-233, migracja przewoźnika Y na API v3 (inicjatywa 2, panel statusu)

**Dlaczego to Cię dotyczy.** Panel statusu zamówienia pokazuje klientowi to, co OMS wie o przesyłce. Po migracji dla przesyłek przewoźnika Y OMS będzie wiedział znacznie mniej:

- **Tylko dwa zdarzenia.** W v3 są wyłącznie „nadane” i „doręczone”. Znikają „w doręczeniu” i awizacja, czyli statusy, o które klienci najczęściej pytają. Z perspektywy panelu paczka Y będzie „nadana” aż do „doręczona”.
- **Opóźnienie do ok. 12 h.** Plan Standard odświeża zdarzenia mniej więcej co 12 h, bo nie ma webhooków. Panel może więc pokazywać nieaktualny status.
- **Kolejność dat jest niekorzystna.** Panel wychodzi 2026-12-10. Migracja na v3 jest planowana do 2026-12-12, a v2 wygasa 2026-12-15. Panel wystartuje na pełniejszych danych z v2, a po 2 dniach te dane się pogorszą. Tego zachowania nikt nie zaprojektował.
- **Mapowanie zdarzeń v3 na statusy OMS jest „w toku”.** Zespół Integracji właśnie decyduje, co klient zobaczy. Ty tej decyzji nie widzisz.
- **Kryteria akceptacji tego zadania pokrywają tylko zapis w OMS.** Nie obejmują tego, czy panel pokazuje sensowny status.

**Ryzyko dla celu panelu.** Panel ma m.in. odciążyć kontakty o status zamówienia. Ich udział to teraz 26% (tydzień 47). Przy braku „w doręczeniu” i awizacji oraz przy 12-godzinnym opóźnieniu dla paczek Y ten cel jest zagrożony. Nie wiem, jaki udział przesyłek obsługuje Y [niezweryfikowane], więc nie umiem oszacować skali.

**Co bym zrobił:**

1. Ustal z Integracjami, jaki jest udział przesyłek Y i co dokładnie trafi do OMS po 12-12.
2. Zdecyduj, czy zakres panelu na 12-10 zostaje bez zmian, czy dla Y panel pokazuje tylko „nadane/doręczone” z komunikatem w rodzaju „status aktualizowany kilka razy dziennie”. Tekst trzeba przygotować przed wydaniem.
3. Rozważ plan Premium (odświeżanie co 15 min), który kosztuje szacunkowo +0,30 zł za paczkę i wymaga renegocjacji umowy. Nawet Premium nie przywróci „w doręczeniu” ani awizacji, bo v3 ich nie ma. Premium poprawia więc tylko opóźnienie, a nie brakujące statusy. Policz koszt przy realnej liczbie paczek Y.
4. Poproś o wyrównanie dat: panel 12-10 vs migracja 12-12 vs wygaszenie v2 12-15. Jeśli migracja przesunie się za 12-15, zdarzenia przestaną przychodzić zupełnie.

**Wpływ na inicjatywę 1 (próg 99 zł).** Niższy próg zwiększy udział zamówień z darmową dostawą, więc koszt przesyłki częściej pokryje firma. Jeśli zespół wybierze Premium, +0,30 zł dojdzie do kosztu każdej paczki Y. Nie wiem, ile to będzie w skali miesiąca [niezweryfikowane]. Ta kwota wchodzi do rachunku opłacalności progu.

## Do obserwacji, bez pilnej akcji

- **Tygodnik danych (tydzień 47).** Dane mogą służyć jako punkt odniesienia dla Twoich metryk:
  - **Panel:** udział kontaktów o status to 26%, a NPS po dostawie to 43.
  - **Próg:** średnia wartość koszyka to 158 zł, tuż nad starym progiem 149 zł.
  - **Zastrzeżenie:** to tydzień Black Week (sesje +6,3%, koszyk −4,8% t/t), więc nie traktowałbym go jako bazy do biznescase'u progu 99 zł. Przyczyny spadku koszyka nie znam [założenie: promocje].
- **Sprint 32, kody rabatowe łączone (Q1).** To nie koliduje ze startem 12-01. Warto jednak ustalić, czy próg darmowej dostawy liczy się od wartości koszyka przed czy po rabatach. Przy łączonych kodach wartość po rabacie częściej spadnie poniżej 99 zł.

## Pominięte jako nieistotne dla Twoich inicjatyw

Ankieta pracownicza, koszty infrastruktury, plan treści poradników oraz zmiana etykiet przewoźnika X (bez zmian w procesie i cenniku, a szablony dla magazynu mają być do 25.11).
