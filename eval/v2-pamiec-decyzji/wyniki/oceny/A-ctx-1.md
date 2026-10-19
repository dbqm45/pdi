# Karta oceny v2 — A-ctx-1

## Metadane

| Pole | Wartość |
|---|---|
| Wariant | A-ctx |
| Powtórzenie | 1 |
| Model generujący | nieznane |
| Oceniający | sędzia LLM (model: claude-opus-5-5) |
| Data | 2026-10-19 |

## Sygnały

| ID | Punkty (0–2) | Tydzień wykrycia | Poziom / sposób oznaczenia | Cytat (dowód) |
|---|---|---|---|---|
| S1 aneks X → rachunek D1 | 2 | T4 (na czas) | „wymaga pilnej uwagi”, pozycja 1; pełny rachunek | „Przy niezmienionej marży 235 000 zł wynik spada z +22 600 zł do ok. −4 000 zł miesięcznie” |
| S2 INT-233 → warunek aktualności D2 | 2 | T3 (na czas) | „wymaga pilnej uwagi”, pozycja 1; nazywa podważony warunek decyzji | „Uzasadnienie z 2026-10-27 brzmi: «Panel ma sens, bo dane o zdarzeniach od przewoźników są teraz aktualne»” / „Status «w doręczeniu» nie będzie dostępny” |
| S3 brief CZ → zakres D3 (wspólny checkout) | 2 | T1 (na czas) | „wymaga Twojej uwagi”, jedyna pozycja tygodnia | „checkout jest wspólny dla całej platformy. Wyłączenie z 2027-02-01 obejmie więc automatycznie także Czechy” |
| B1 bonus: aneks + wynik A/B razem (0–1) | 1 | T4 | w sekcji aneksu | „Nałożone na wcześniejsze korekty (test A/B z tygodnia 2: +5,8% zamiast +6,1% i spadek koszyka −3,4% …) wynik prawdopodobnie schodzi poniżej zera” |
| **Suma (max 6 + 1)** | **6 + 1** | | | |

## Szum

| Miara | Wartość | Lista (tydzień / plik / cytat) |
|---|---|---|
| FA — fałszywe alarmy (P1–P4, szum, pogranicze na poziomie 3) | 1 | T4 / `02-swieta-dyzury.md` (dokument z listy szumu) — „## 2. Zamrożenie wdrożeń 2026-12-20 – 2027-01-04 (wymaga uwagi)”. Oba terminy decyzji (12-01, 12-10) wypadają przed zamrożeniem, a dokument nie podważa żadnego założenia; obserwacja o krótkim oknie na poprawki jest rozsądna, ale według definicji z klucza to FA. |
| DUP — duplikaty ostrzeżeń | 1 | T4 / `06-sprint-review-integracje.md` — „## 3. Sprint review Integracji: INT-233 (wymaga uwagi, kontynuacja z tygodnia 3)”. Pełne ostrzeżenie (osobna sekcja „wymaga uwagi”, powtórzone skutki i opcje); jedyna nowa informacja to „mapowanie gotowe”, co nie zmienia oceny sprawy. |
| Obciążenie — wszystkie pozycje „wymaga uwagi” w 4 tygodniach | 7 | T1: brief CZ (S3). T2: wyniki A/B (P1), inwentaryzacja magazynu (pogranicze). T3: INT-233 (S2). T4: aneks X (S1), zamrożenie wdrożeń (FA), INT-233 sprint review (DUP). |

Pozycje sprawdzone i niezaliczone jako FA:
- T2 / `05-wyniki-ab-prog-dostawy.md` (P1) — oznaczony „wymaga uwagi”, ale wskazuje cieńszy wynik D1 i wprost: „Decyzji nie trzeba z tego powodu odwoływać: wniosek zespołu Danych jest taki, że efekt się potwierdza, tylko słabiej”. Według klucza poziom 2 jest tu dopuszczalny.
- T2 / `06-magazyn-inwentaryzacja.md` (pogranicze) — „wymaga uwagi” (nie „pilnej”), trafnie wiąże z datą dostawy w panelu D2. Traktuję jako poziom 2, czyli poprawny. Jest to jednak propozycja zmiany zakresu, więc ocena jest na granicy poziomu 3.
- T2 / `02-incydent-blik.md` (P2) — „Do wiadomości”, „nie zmienia decyzji”; brak zalecenia ponownej oceny D3. Poprawnie.
- T2 / `01-design-system-v4.md` (pogranicze) — „Do wiadomości”. Poprawnie.
- T3 / `03-przewoznik-x-etykiety.md` (P3) — pominięty („brak zmian w procesie nadawania i w cenniku”). Poprawnie.
- T4 / `01-konkurent-prog-dostawy.md` (P4) — „Do wiadomości”, „nie zmienia Twojej decyzji”. Poprawnie.
- T3 tygodnik danych i sprint 32 — „Do wiadomości”. Nie FA.

Trafne zgłoszenia spoza klucza (np. powiązania, których autor klucza nie przewidział):

| Tydzień / plik | Zgłoszenie | Trafne? | Uzasadnienie |
|---|---|---|---|
| T3 / `06-INT-233-api-przewoznika-y.md` | Opcja Premium (+0,30 zł/paczkę Y) uderzyłaby też w rachunek D1 | tak (częściowo) | Poprawne powiązanie krzyżowe D2→D1; opisane jako warunkowe („Jeśli wybierzesz Premium”), w ramach już liczonej pozycji, więc bez wpływu na obciążenie |
| T4 / `02-swieta-dyzury.md` | Krótkie okno na poprawki panelu przed zamrożeniem | częściowo | Użyteczne dla planowania, ale nie podważa założenia żadnej decyzji, więc według klucza liczone jako FA (wyżej) |

## Subiektywnie

- Czy PM zauważyłby dzięki temu wynikowi coś, czego inaczej by nie zauważył? **tak** — wszystkie trzy ukryte powiązania wykryto w tygodniu pojawienia się dokumentu, a S1 z rachunkiem zgodnym z kluczem (13,28 zł, +26,6 tys. zł, ok. −4 tys. zł/mies.).
- Ile czasu tygodniowo PM poświęciłby na przeczytanie wyników? ok. 3–5 min (odpowiedzi mają 3–6 tys. znaków)
