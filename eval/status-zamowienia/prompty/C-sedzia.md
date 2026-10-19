# Sędzia LLM (opcjonalny drugi oceniający)

Główną ocenę wykonujesz sam według `karta-oceny.md`. Sędzia LLM to drugi oceniający: pozwala policzyć zgodność ocen i wyłapać Twoje nieświadome faworyzowanie wariantu B.

Zasady (skill `ai-evals`):
- **inny model** niż ten, który generował odpowiedzi;
- **jedna pozycja klucza na wywołanie** (jeden wymiar na sędziego);
- dozwolona odpowiedź „nieznane”;
- odpowiedź testowanego wariantu bez nagłówków zdradzających wariant (usuń JSON modelu i tytuły typu „Decision Readiness Brief” — wklej tylko treść wniosków).

## Prompt

```
Oceniasz jedną odpowiedź analityczną względem jednego kryterium. Nie oceniaj niczego innego.

KRYTERIUM:
[wklej jeden wiersz z klucza: ID, opis „co jest zaszyte”, „pełne wykrycie”, „częściowe”]

ODPOWIEDŹ DO OCENY:
[wklej odpowiedź]

Zwróć dokładnie jedną linię w formacie:
WERDYKT: 2 | 1 | 0 | nieznane — UZASADNIENIE: [cytat z odpowiedzi, na którym opierasz ocenę, max 2 zdania]

2 = pełne wykrycie wg kryterium, 1 = częściowe, 0 = brak, nieznane = odpowiedź jest niejednoznaczna i nie da się rozstrzygnąć.
```

Dla fałszywych alarmów (F1–F6) użyj tego samego promptu z kryterium: „Czy odpowiedź zgłasza [opis F] jako problem krytyczny lub ważny? 2 = tak, 0 = nie, nieznane”.

## Kalibracja

Porównaj werdykty sędziego ze swoimi. Zgodność = odsetek identycznych werdyktów. Przy zgodności poniżej ok. 80% [założenie — próg do potwierdzenia] przeczytaj rozbieżności: albo kryterium w kluczu jest niejasne (popraw klucz), albo Twoja ocena była stronnicza (popraw ocenę). Zapisz zgodność w raporcie.
