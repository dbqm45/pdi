# Propozycja: szybki tor obok fabryki tf

**Data:** 2026-11-27 · **Status:** do decyzji właściciela (pytania DT1–DT4 w §7) · **Dotyczy:** tf, pdi, ShipScope

## 1. Problem

Zadanie „zmień nagłówki na kilku stronach i szerokość pola” zajęło w tf ponad godzinę. To był komponent
z design systemu, z testami, ale jak na pracę z AI to i tak długo. Jeśli Suite ma pomagać w decyzjach i wykonaniu
w wielu miejscach naraz, droga od decyzji do zmiany musi być szybka. Pytanie właściciela: czy fabryka tf jest w Suite
potrzebna, czy wystarczą skille (w stylu Matta Pococka) i prosty workflow, a może zostawić tf i pracować nad jego
szybkością.

Danych z tego przebiegu (oś czasu, koszt, waga zadania) nikt jeszcze nie przejrzał. Wszystko niżej o przyczynach to
hipotezy do sprawdzenia, nie diagnoza.

## 2. Jaką rolę tf pełni w Suite (stan 2026-11-27, sprawdzone w repo tf i pdi)

- **Wykonawca zmiany:** fazy intencja → plan → dostarczenie; po każdej bramka B1–B5, o której decyduje człowiek
  w pdi (od dbqm45/pdi#236 tylko przyciskiem w konsoli). Dziennik zmiany `changes/CHG-n/decisions.md` i ślad
  zgłoszenie → zmiana → zadanie → PR → wydanie.
- **Ochrona niezależna od modelu:** poziomy izolacji i kontener z firewallem (`docs/isolation.md` w tf), blokada
  niebezpiecznych poleceń, ochrona plików z sekretami, skan sekretów, strażnik TDD, ocena ryzyka zmiany (DV2,
  doradcza), pętla PR.
- **Wagi zadania:** `light`, `quick`, `normal`, `full`; `quick` to szybki tor dla małych zadań: jedna porcja pracy,
  bez podwójnej weryfikacji (tf #432). Obszar wrażliwy wymusza `full`.
- **Pomiar:** oś czasu przebiegu i czas czekania na pytania (tf #455), koszt, tokeny i czas zadania (tf #343).

Skill to prośba do modelu; hook, sandbox i bramka to mechanizm. Tej różnicy dotyczyły dbqm45/pdi#235 i #236 — tam
też zamieniliśmy prośbę na mechanizm.

## 3. Hipotezy: gdzie mogła zniknąć godzina

| # | Hipoteza | Jak sprawdzić |
|---|---|---|
| H1 | Za ciężka waga: komponent design systemu uznany za obszar wrażliwy → `full` zamiast `quick` | `weight` i `weight_log` w `task.json` przebiegu |
| H2 | Pełny zestaw testów (z przeglądarką) po każdej porcji pracy zamiast testów dotkniętych zmianą | oś czasu: udział kroków weryfikacji |
| H3 | Sekwencyjność: porcja po porcji, przegląd po przeglądzie, model czeka na model | oś czasu: kroki, które mogły iść równolegle |
| H4 | Czekanie na człowieka (pytania, bramki): wg prawa Little'a czas przejścia to praca w toku / przepustowość, a człowiek jest najwolniejszym ogniwem | oś czasu: czas czekania na pytania (#455) |
| H5 | Zimny start: nowa sesja, odbudowa kontekstu, brak trafień w pamięci podręcznej promptów | koszt i tokeny wejścia na krok (#343) |

## 4. Opcje

| | Opcja | Za | Przeciw |
|---|---|---|---|
| A | **Zostawić tf bez zmian** | nic nie trzeba robić | małe zadania dalej trwają godzinę; ludzie zaczną omijać Suite |
| B | **Zastąpić tf skillami i prostym workflow** | szybko, mało ruchomych części | tracimy mechanizmy (sandbox, TDD, bramki, ślad), z których korzysta reszta Suite; ochrona znów staje się prośbą |
| C | **Dwa tory: szybki (skille) i pełny (tf), wybór z oceny ryzyka** | małe zmiany szybko, ryzykowne dalej pod kontrolą; ochrona zostaje na obu torach | trzeba zbudować wybór toru i pilnować, żeby szybki tor nie stał się furtką |
| D | **Tylko przyspieszyć tf** (bez nowego toru) | jedna droga | sama optymalizacja może nie wystarczyć, jeśli większość czasu to stałe koszty faz i bramek |

## 5. Rekomendacja: C, poprzedzona pomiarem

1. **Najpierw pomiar (H1–H5) na tym przebiegu** i kilku innych. Jeśli większość czasu to testy i weryfikacja —
   wystarczy D. Jeśli to stałe koszty faz i bramek — potrzebny szybki tor (C). Jeśli to czekanie na człowieka —
   żaden szybszy model nie pomoże, pomoże mniej pytań.
2. **Szybki tor:** zwykła sesja ze skillami (krótkie, jednozadaniowe, w duchu Matta Pococka — jego zestawu nie
   sprawdzałem [niezweryfikowane]). Bez faz i bramek B1–B5, ale z ochroną zawsze włączoną: hooki, sandbox, skan
   sekretów, testy dotknięte zmianą przed PR. Zmiana i tak trafia do ShipScope (wdrożenie, rollback) i do śladu
   w pdi (PR z kluczem zmiany).
3. **Pełny tor:** tf jak dziś dla uprawnień, danych, migracji, publicznego API, zmian w wielu serwisach.
4. **Wybór toru z oceny ryzyka (DV2) i z danych:** dziś ocena jest tylko doradcza, a decyzja DV2 mówi, że polityka
   „jaka zmiana, jakie bramki” przyjdzie, gdy będą dane o rozkładzie ryzyka. Ten przypadek jest takim sygnałem.
   Obniżanie toru na podstawie danych, jak licznik akceptacji przy autonomii (95% z 30): typ zmiany, przy którym
   pełny tor niczego nie złapał, schodzi na szybki — decyzją człowieka w pdi.

## 6. Przyspieszenia tf (niezależnie od toru)

- **Testy dotknięte zmianą** z grafu zależności po każdej porcji, pełny zestaw raz przed PR. CI samej fabryki już to
  robi (`workspace.py check --changed-from`); w projektach — do sprawdzenia [niezweryfikowane].
- **Równoległość:** niezależne porcje i weryfikacja (testy, lint, przegląd) jednocześnie.
- **Model dobrany do kroku:** tańszy i szybszy do edycji mechanicznych, mocniejszy do planu i przeglądu.
- **Wspólny kontekst między fazami** zamiast zimnego startu; pilnowanie trafień w pamięć podręczną promptów.
- **Budżet czasu na wagę** (np. `quick` 10 min): przekroczenie to sygnał dla człowieka, nie ciche mielenie.
- **Model decyzyjny wagi:** wybór wagi minimalizuje oczekiwany koszt = czas pracy + P(błąd) × koszt błędu. P(błąd)
  szacujemy z oceny ryzyka i z rollbacków oraz CFR z ShipScope (sekcja „Kolejka a jakość” na „Przepływie”).

## 7. Decyzje do podjęcia

| ID | Pytanie | Rekomendacja |
|---|---|---|
| DT1 | Czy tf zostaje w Suite jako pełny tor i warstwa ochrony? | tak (opcja C) |
| DT2 | Czy budujemy szybki tor na skillach, z ochroną zawsze włączoną? | tak, po pomiarze z DT3 |
| DT3 | Czy najpierw rozkładamy przebieg „nagłówki i szerokość pola” (i kilka innych) na składniki H1–H5? | tak, jako pierwszy krok |
| DT4 | Czy tor wybiera automat z oceny ryzyka, a obniżenie dla typu zmiany zatwierdza człowiek w pdi? | tak; do tego czasu tor wybiera człowiek |

Po decyzji: wpisy w [`decyzje.md`](decyzje.md) i plan kroków (pomiar → szybki tor → wybór toru → przyspieszenia
tf) w `TODO.md`.
