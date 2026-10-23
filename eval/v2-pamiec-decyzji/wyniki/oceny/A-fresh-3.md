# Karta oceny v2 — A-fresh-3

## Metadane

| Pole | Wartość |
|---|---|
| Wariant | A-fresh |
| Powtórzenie | 3 |
| Model generujący | nieznane |
| Oceniający | sędzia LLM (model: claude-opus-5-5) |
| Data | 2026-10-19 |

## Sygnały

| ID | Punkty (0–2) | Tydzień wykrycia | Poziom / sposób oznaczenia | Cytat (dowód) |
|---|---|---|---|---|
| S1 aneks X → rachunek D1 | 1 | T4 (w tygodniu pojawienia) | „Wymaga uwagi”, punkt 1 | „Przeliczyć uzasadnienie biznesowe progu 99 zł z nowymi stawkami przed 2026-12-01.”; „średni koszt przesyłki u przewoźnika X rośnie z 12,00 zł do ok. 14,29 zł, czyli o ok. 19%” — wiąże aneks z progiem i liczy wzrost kosztu, ale nie porównuje go z zakładanym zyskiem decyzji (ok. 22,6 tys. zł/mies.) ani nie mówi, że rachunek może stać się ujemny. To ogólne „sprawdź opłacalność”, więc 1 pkt. |
| S2 INT-233 → warunek aktualności D2 | 2 | T3 (w tygodniu pojawienia) | „Wymaga działania”, punkt 1 | „Status «nadane» może być nieaktualny nawet o pół doby.”; „Znikają «w doręczeniu» i awizacja.”; „Taki panel prawdopodobnie nie ograniczy kontaktów «gdzie jest moja paczka».” |
| S3 brief CZ → zakres D3 (wspólny checkout) | 2 | T1 (w tygodniu pojawienia) | „Wymaga uwagi”, punkt 1 | „Wycofanie płatności za pobraniem startuje 2027-02-01, czyli miesiąc wcześniej.”; „dobírka to ok. 30% płatności”; „Jeśli obejmuje, powstaje konflikt między Twoją inicjatywą a celami Ekspansji.” Wspólny checkout nie jest nazwany wprost, ale jest konflikt zakresu i inny udział pobrania na rynku CZ. |
| B1 bonus: aneks + wynik A/B razem (0–1) | 0 | — | — | W T4 nie ma odwołania do wyniku testu A/B z T2. Jako tło przywołano tylko marżę z dokumentu 07. |
| **Suma (max 6 + 1)** | **5 + 0** | | | |

## Szum

| Miara | Wartość | Lista (tydzień / plik / cytat) |
|---|---|---|
| FA — fałszywe alarmy (P1–P4, szum, pogranicze na poziomie 3) | 2 | (1) T3 / 01-notatka-sprint-32-checkout (szum): sekcja „Do sprawdzenia, niski priorytet” — „Warto sprawdzić, jaką część klientów COD stanowią goście”, „ustal z Checkout, czy próg darmowej dostawy liczy się od wartości przed rabatem”. (2) T4 / 02-swieta-dyzury (szum): w sekcji „Wymaga uwagi”, choć release panelu 10.12 i start progu 1.12 nie kolidują z zamrożeniem — „Panel statusu (release 2026-12-10) ma 10 dni zapasu przed zamrożeniem.” |
| DUP — duplikaty ostrzeżeń | 1 | T4 / 06-sprint-review-integracje: ponowne ostrzeżenie o INT-233 w sekcji „Wymaga uwagi” bez nowej informacji („zależność do potwierdzenia”). Jest też słabsze niż w T3, bo przebieg nie pamięta wcześniejszego ustalenia. |
| Obciążenie — wszystkie pozycje „wymaga uwagi” w 4 tygodniach | 9 | T1: 04. T2: 05, 06, 01 („trzy wymagają Twojej uwagi”). T3: 06 (INT-233), 01 (sprint 32). T4: 03, 06, 02. |

Uwagi do pozycji niezaliczonych jako FA:
- T2 / 05 (P1): oznaczone jako wymagające uwagi („wymaga decyzji lub dopowiedzenia”), ale z wnioskiem, że efekt się potwierdza i jest nieco niższy („zaktualizuj założenia w business case”, „Potem potwierdź GO”). Odpowiada to poziomowi 2 ze wskazaniem cieńszego wyniku D1, który klucz dopuszcza. Przypadek graniczny: szacunek „−2,5% przychodu na odwiedzającego” zbliża się do twierdzenia, że test sam podważa decyzję, ale odpowiedź tego nie stwierdza.
- T2 / 06 i T2 / 01 (pogranicze): poziom 2 bez sugestii zmiany decyzji, więc bez kary. Wliczone do obciążenia.
- T2 / 02 (P2): „Nie zmienia planu wycofania” — poziom 0–1, w porządku.
- T3 / 03 (P3): pominięte — w porządku.
- T4 / 01 (P4): „Do wiadomości, bez pilnego działania” — w porządku.
- T1 / 06 i T3 / 04 (tygodniki danych): podane jako kontekst lub punkt odniesienia pomiaru („To nie jest alarm”, „ważny kontekst”), a nie jako ostrzeżenie. Nie liczę ich jako FA ani do obciążenia (pogranicze interpretacji).

Trafne zgłoszenia spoza klucza:

| Tydzień / plik | Zgłoszenie | Trafne? | Uzasadnienie |
|---|---|---|---|
| T3 / 01-notatka-sprint-32-checkout | Łączone kody rabatowe a podstawa liczenia progu 99 zł | Częściowo (nie zmienia oceny FA) | To realne pytanie implementacyjne, ale nie podważa założeń nośnych D1, więc pozostaje FA. |

## Opóźnienie

| Sygnał | W tygodniu pojawienia? |
|---|---|
| S1 | tak (T4) |
| S2 | tak (T3) |
| S3 | tak (T1) |

## Subiektywnie

- Czy PM zauważyłby dzięki temu wynikowi coś, czego inaczej by nie zauważył? Tak: konflikt CZ z D3 i wpływ INT-233 na panel są dobrze uzasadnione. Przy S1 brakuje wniosku, że decyzja może przestać się opłacać.
- Ile czasu tygodniowo PM poświęciłby na przeczytanie wyników? Ok. 5–8 min.

SYGNALY=5/6 BONUS=0 FA=2 DUP=1 OBCIAZENIE=9
