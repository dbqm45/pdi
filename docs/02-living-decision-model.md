# 2. Living Decision Model (fundament: Decision Integrity Graph)

Living Decision Model (LDM) to wewnętrzna reprezentacja tego, co organizacja **wie**, w co **wierzy**, co **postanowiła** i co może **wpłynąć** na te ustalenia. Jest grafem: węzły to elementy wiedzy, krawędzie to relacje logiczne między nimi.

Schemat formalny: [`model/living-decision-model.schema.json`](../model/living-decision-model.schema.json).

## 2.1. Zasada epistemiczna — najważniejsza reguła modelu

Każdy węzeł ma **status epistemiczny**. System nie może mieszać tych kategorii, a zwłaszcza nie może traktować własnych wniosków jako ustaleń organizacji.

| Status | Znaczenie | Przykład |
|---|---|---|
| `observation` | Bezpośrednia obserwacja / dana | „38% zgłoszeń do supportu dotyczy statusu zamówienia (Q3, n=12 400)” |
| `interpretation` | Wniosek wyciągnięty z obserwacji przez człowieka | „Użytkownicy nie rozumieją statusu zamówienia” |
| `hypothesis` | Przyjęte, niepotwierdzone wyjaśnienie lub założenie | „Przyczyną jest brak informacji w interfejsie” |
| `decision` | Zatwierdzone ustalenie z właścicielem i datą | „Budujemy panel statusu zamówienia” |
| `ai_inference` | Wniosek systemu, niezatwierdzony przez człowieka | „Uzasadnienie wydaje się pomijać opóźnienia aktualizacji statusu” |

Dodatkowo każdy węzeł ma **pochodzenie rekonstrukcji**:

- `stated` — zapisane wprost w źródle,
- `reconstructed` — odtworzone przez system z pośrednich przesłanek (np. hipoteza nigdzie nienazwana, ale implikowana przez wybór rozwiązania),
- `confirmed` — rekonstrukcja potwierdzona przez człowieka.

> Dlaczego to krytyczne: w praktyce uzasadnienia decyzji rzadko są spisane. System **musi** je rekonstruować — i musi uczciwie oznaczać, że to rekonstrukcja. Ostrzeżenie oparte na niepotwierdzonej rekonstrukcji ma niższą pewność i inną formę komunikatu („Wygląda na to, że decyzja zakłada X — czy to prawda?”).

## 2.2. Typy węzłów

| Typ | Opis | Kluczowe atrybuty |
|---|---|---|
| `Initiative` | Kontener: inicjatywa produktowa | etap, właściciel, **następna decyzja** (`next_decision`) |
| `Problem` | Co próbujemy rozwiązać i dla kogo | segment, skala |
| `Goal` | Oczekiwany rezultat | metryka, wartość docelowa, horyzont |
| `Evidence` | Informacja o stanie świata | typ źródła, siła, aktualność, zakres (n, okres) |
| `Hypothesis` | Wyjaśnienie / założenie | krytyczność, stan weryfikacji |
| `Option` | Rozważane rozwiązanie (wybrane lub odrzucone) | koszt, odwracalność |
| `Decision` | Ustalenie z uzasadnieniem | właściciel, data, odwracalność, koszt błędu, status |
| `Constraint` | Warunek, który musi być spełniony | źródło (biznes/tech/prawo) |
| `Requirement` | Wymaganie | odniesienie do systemu źródłowego |
| `DesignArtifact` | Element designu | odniesienie do systemu źródłowego |
| `SuccessCriterion` | Po czym poznamy, że zadziałało | metryka, sposób pomiaru |
| `Unknown` | Nazwana luka w wiedzy | pytanie, wpływ na decyzję, właściciel, stan |
| `Signal` | Nowa informacja z monitoringu (tryb Guardian) | źródło, data, dotknięte węzły |

## 2.3. Typy krawędzi

Krawędzie są ważniejsze niż węzły — to one niosą logikę decyzji.

| Krawędź | Od → Do | Znaczenie |
|---|---|---|
| `supports` | Evidence → Problem/Hypothesis/Option | Dowód wspiera |
| `contradicts` | Evidence → Problem/Hypothesis/Option | Dowód podważa |
| `interprets` | Interpretation → Evidence | Wniosek wyciągnięty z danych |
| `explains` | Hypothesis → Problem | Hipoteza jako przyczyna problemu |
| `competes_with` | Hypothesis ↔ Hypothesis | Konkurencyjne wyjaśnienia |
| `addresses` | Option → Problem/Hypothesis | Rozwiązanie celuje w przyczynę |
| `assumes` | Decision/Option/Requirement → Hypothesis | Zależność od założenia |
| `chooses` / `rejects` | Decision → Option | Wybór / odrzucenie alternatywy |
| `serves` | Decision/Option → Goal | Służy celowi |
| `derives_from` | Requirement/DesignArtifact → Decision | Wynika z decyzji |
| `verifies` | SuccessCriterion → Goal | Pozwala zweryfikować cel |
| `violates` | Requirement/DesignArtifact → Constraint | Narusza warunek |
| `blocks` | Unknown → Decision | Niewiadoma, od której zależy decyzja |
| `resolves` | Evidence → Unknown | Dowód zamyka lukę |
| `affects` | Signal → dowolny węzeł | Nowa informacja dotyka elementu |
| `same_concept` / `diverging_concept` | węzeł ↔ węzeł | Ten sam / rozbieżnie rozumiany termin w różnych zespołach |

Każda krawędź ma: `confidence` (0–1), `rationale` (dlaczego istnieje), `provenance` (`stated` / `reconstructed` / `confirmed`).

## 2.4. Łańcuch uzasadnienia

Szkielet każdej inicjatywy to ścieżka:

```
Evidence ──supports──► Problem ◄──explains── Hypothesis ◄──addresses── Option ◄──chooses── Decision
                                                                                              │
                                Goal ◄──serves────────────────────────────────────────────────┤
                                 ▲                                                            │
                     SuccessCriterion ──verifies                    Requirement ──derives_from┘
```

**Integralność decyzji** = każde ogniwo tego łańcucha istnieje i jest wystarczająco silne **w stosunku do wagi decyzji**. Decision Risk Radar sprawdza właśnie to (patrz [03](03-decision-risk-radar.md)).

## 2.5. Atrybuty wspólne wszystkich węzłów

- `id`, `type`, `statement` (treść w jednym zdaniu),
- `epistemic_status`, `provenance`,
- `sources[]` — odniesienia do dokumentu/fragmentu/systemu (z datą),
- `updated_at`, `valid_until` (opcjonalnie — dane mają termin przydatności),
- `confidence` (0–1) — pewność systemu co do poprawności ekstrakcji, **nie** prawdziwości twierdzenia,
- `owner` (opcjonalnie).

Rozróżnienie w ostatnim punkcie jest istotne: system może być w 95% pewny, że dokument zawiera hipotezę X, i jednocześnie ta hipoteza może mieć słabe wsparcie dowodowe. To dwie różne osie.

## 2.6. Model żyje

- Nowe źródła tworzą `Signal`, który jest dopasowywany do istniejących węzłów (`affects`).
- Węzły mają historię wersji — można odtworzyć stan wiedzy **w chwili podjęcia decyzji**. To warunek uczciwej oceny („czy decyzja była rozsądna na podstawie tego, co wtedy wiedzieliśmy?”) i ochrony przed hindsight bias.
- Decyzje nie są nadpisywane — są zastępowane (`superseded_by`) z uzasadnieniem.
