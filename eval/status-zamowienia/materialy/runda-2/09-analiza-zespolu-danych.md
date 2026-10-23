# Analiza: zgłoszenia o status zamówienia a aktualizacje statusu

**Autor:** Zespół Danych · **Data:** 2026-08-20 · **Zlecił:** Kierownik Obsługi Klienta (w związku ze wzrostem w Q2)

## Pytanie

Czy zgłoszenia dotyczące statusu zamówienia są związane z opóźnieniami w aktualizacji statusu?

## Dane

Losowa próba 1 200 zgłoszeń z kategorii „Status zamówienia” z Q2 2026, zestawiona z logiem zdarzeń OMS i logiem webhooków przewoźników.

## Wyniki

- **61%** zgłoszeń dotyczyło zamówień, w których status w aplikacji był nieaktualny o ponad 24 godziny w chwili kontaktu (zdarzenie logistyczne już nastąpiło, ale nie trafiło do OMS).
- 23% zgłoszeń dotyczyło zamówień z aktualnym statusem, a pytanie dotyczyło znaczenia statusu lub przewidywanej daty dostawy.
- 16% — inne lub nie do ustalenia.
- W tygodniach 19 i 24 (skoki w raporcie Q2) wystąpiły awarie integracji webhooków z nowym przewoźnikiem; liczba zgłoszeń o status w tych tygodniach była ok. 3 razy wyższa niż średnio.
- Dla nowego przewoźnika (od tygodnia 18) mediana opóźnienia zdarzenia „przekazane przewoźnikowi” w OMS wynosi 31 godzin; dla pozostałych przewoźników — 2 godziny.

## Ograniczenia

- Kategoryzacja zgłoszeń ręczna (możliwe błędy klasyfikacji).
- Próba z jednego kwartału.
