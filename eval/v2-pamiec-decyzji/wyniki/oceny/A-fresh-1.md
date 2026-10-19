# Karta oceny v2 — A-fresh-1

## Metadane

| Pole | Wartość |
|---|---|
| Wariant | A-fresh |
| Powtórzenie | 1 |
| Model generujący | nieznane |
| Oceniający | sędzia LLM (model: claude-opus-5-5) |
| Data | 2026-10-19 |

## Sygnały

| ID | Punkty (0–2) | Tydzień wykrycia | Poziom / sposób oznaczenia | Cytat (dowód) |
|---|---|---|---|---|
| S1 aneks X → rachunek D1 | 1 | T4 (w tygodniu pojawienia się) | Pozycja nr 1, „Najważniejsze”; wymaga uwagi | „Business case dla progu 99 zł zakładał prawdopodobnie stare stawki.” / „Średni koszt przesyłki u X rośnie … z ok. 12,00 zł do ok. 14,29 zł, czyli o ok. 19%.” / „Przeliczyć koszt progu 99 zł na nowych stawkach z aneksu.” — wiąże aneks z D1 i liczy wzrost kosztu paczki, ale nie zestawia go z zakładanym zyskiem decyzji (+22,6 tys. zł/mies.) ani nie wskazuje, że rachunek może stać się ujemny; odpowiada „sprawdź opłacalność” = 1 pkt |
| S2 INT-233 → warunek aktualności D2 | 2 | T3 (w tygodniu pojawienia się) | Jedyna pozycja „Wymaga uwagi” w tygodniu | „Znikają „w doręczeniu” i awizacja” / „Opóźnienie do ok. 12 h. … Panel może więc pokazywać nieaktualny status.” / „Panel ma m.in. odciążyć kontakty o status zamówienia. … ten cel jest zagrożony.” |
| S3 brief CZ → zakres D3 (wspólny checkout) | 2 | T1 (w tygodniu pojawienia się) | Pozycja nr 1, „Wymaga uwagi” | „Wycofanie pobrania ma obowiązywać od 2027-02-01. Start sprzedaży w Czechach jest 2027-03-01” / „płatność przy odbiorze (dobírka) to ok. 30% płatności” / „Ustal z zespołem Ekspansja, czy wycofanie pobrania obejmuje Czechy” — wiąże brief z D3 i nazywa konflikt (inny udział pobrania na rynku CZ, zakres rynkowy decyzji) |
| B1 bonus: aneks + wynik A/B razem (0–1) | 0 | — | — | W T4 brak odwołania do wyniku testu A/B z T2 (+5,8%, −3,4% koszyka); wspomniany jest tylko wynik finansowy października |
| **Suma (max 6 + 1)** | **5 + 0** | | | |

## Szum

| Miara | Wartość | Lista (tydzień / plik / cytat) |
|---|---|---|
| FA — fałszywe alarmy (P1–P4, szum, pogranicze na poziomie 3) | 3 | (1) T1 / 06-dane-tygodniowe (szum): „drugi to kontekst do sprawdzenia” / „Zapisz teraz baseline przed startem 2026-12-01” — przedstawiony jako rzecz do sprawdzenia; (2) T4 / 01-konkurent-prog-dostawy (P4): „uwagi wymagają trzy (03, 01, 02)” / „rozważ próg niższy tylko dla nich” — sugestia modyfikacji D1 na podstawie oferty konkurenta; (3) T4 / 02-swieta-dyzury (szum): oznaczony jako wymagający uwagi, „Warto mieć plan wycofania lub korekty gotowy przed zamrożeniem” |
| DUP — duplikaty ostrzeżeń | 1 | T4 / 06-sprint-review-integracje: osobna sekcja „INT-233 w sprint review Integracji … Do sprawdzenia” z zaleceniami („dodaj sprawdzenie statusów w panelu po 2026-12-12 do planu testów”) — ponowne ostrzeżenie o tej samej sprawie, bez nowej informacji podważającej D2 |
| Obciążenie — wszystkie pozycje „wymaga uwagi” w 4 tygodniach | 10 | T1: 2 (04 brief, 06 dane); T2: 3 (05 A/B, 06 magazyn, 01 Design System); T3: 1 (06 INT-233); T4: 4 (03 aneks, 01 konkurent, 02 dyżury/zamrożenie, 06 sprint review) |

Uwagi do klasyfikacji (bez FA):
- T2 / 05-wyniki-ab-prog-dostawy (P1): oznaczony „wymaga uwagi”, ale „Test potwierdza kierunek decyzji” i wskazuje cieńszy wynik („Oczekiwania wobec efektu trzeba skorygować”, „Raport nie podaje wyniku netto”) — poziom 2 dopuszczalny wg klucza.
- T2 / 06-magazyn-inwentaryzacja i 01-design-system-v4 (pogranicze): oznaczone jako wymagające uwagi, bez sugestii zmiany decyzji — odpowiednik poziomu 2, bez kary.
- T2 / 02-incydent-blik (P2): w „Pominięte”, „Nie zmienia planu wycofania płatności za pobraniem” — poziom 0–1, poprawnie.
- T3 / 03-przewoznik-x-etykiety (P3): w „Pominięte” („bez zmian w procesie i cenniku”) — poprawnie.
- T3 / 04-dane-tygodniowe i 01-notatka-sprint-32: w sekcji „Do obserwacji, bez pilnej akcji” — nie liczone jako „wymaga uwagi”.

Trafne zgłoszenia spoza klucza (np. powiązania, których autor klucza nie przewidział):

| Tydzień / plik | Zgłoszenie | Trafne? | Uzasadnienie |
|---|---|---|---|
| T3 / 06-INT-233-api-przewoznika-y | Koszt planu Premium (+0,30 zł/paczkę Y) „wchodzi do rachunku opłacalności progu” | Częściowo | Trafne powiązanie D2 → D1 (ewentualny koszt naprawy aktualności podnosi koszt paczki przy cienkim wyniku D1); nie było w kluczu, dokument już punktowany jako S2 |
| T2 / 06-magazyn-inwentaryzacja | Przerwa w wysyłkach 28–30.12 a data wysyłki w panelu | Tak (pogranicze) | Zgodne z oczekiwaną reakcją na dokument z pogranicza |

## Opóźnienie

| Sygnał | W tygodniu pojawienia się? |
|---|---|
| S1 | tak (T4) |
| S2 | tak (T3) |
| S3 | tak (T1) |

## Subiektywnie

- Czy PM zauważyłby dzięki temu wynikowi coś, czego inaczej by nie zauważył? tak — konflikt CZ/pobranie (T1) i degradację danych Y dla panelu (T3); przy aneksie (T4) dostałby sygnał, ale bez informacji, że decyzja może przestać się opłacać.
- Ile czasu tygodniowo PM poświęciłby na przeczytanie wyników? ok. 5–8 min (odpowiedzi średnio 600–900 słów).

Wynik: `SYGNALY=5/6 BONUS=0 FA=3 DUP=1 OBCIAZENIE=10`
