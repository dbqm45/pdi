# Konsola pdi na tożsamości suity (ADR 17 §3, krok 4) — plan

Stan: 2026-11-25, decyzje 1–5 przyjęte przez właściciela; kroki 1–4 zrobione (ten PR), sprawdzone na żywo. Wcześniej przeszły DI Release Control
(`evdt-shipscope-flags` 0.7.6), DI Definition (`ci_for_sdlc` 0.1.72) i DI Release, krok 1 (`evdt-service-shipscope`
0.2.70). Wszystko lokalnie, bez hostingu (wdrożenie na Hetzner — gdy suita zadziała end-to-end).

## Jak jest dziś

- Konsola (`src/pdi/console.py`, DZ14, DZ18) słucha tylko na `127.0.0.1:8788`; wpuszcza z jednym tokenem sesji w URL
  (`?t=…`, `PDI_CONSOLE_TOKEN`), bez kont.
- Decyzja z przycisku zapisuje `decided_by` = `PDI_DECIDED_BY` albo po prostu `"console"`: nie wiadomo, **kto**
  zdecydował. To główna luka — bramka ma mieć nazwanego zatwierdzającego (kryterium planu budowy suity).
- Realm `suite` ma już klienta `di-decision` z rolami `viewer`, `editor`, `admin` (bez e-maila, DI3).
- Serwer MCP pdi działa przez stdio, bez autoryzacji; zdalny MCP z OAuth to osobny etap (`TODO.md`).

## Decyzje do potwierdzenia (rekomendacja w każdej)

1. **Konsola zostaje lokalnym procesem w Pythonie, z logowaniem OIDC** — nie przepisujemy jej teraz na usługę
   TypeScript (DA4). Rekomendacja: tak. Usługa konsoli powstanie z wdrożeniem; logowanie i role przejdą 1:1.
2. **Z ustawionym wystawcą (`PDI_SUITE_ISSUER`, `PDI_SUITE_CLIENT_SECRET`) konsola wymaga logowania przez suitę**:
   kod z PKCE, sesja w ciasteczku HttpOnly (po stronie serwera, w pamięci procesu), bez tokenu w URL. Bez wystawcy —
   jak dziś (token w URL), żeby konsola działała bez Keycloaka. Rekomendacja: tak.
3. **Role z klienta `di-decision`:** `viewer` — czyta tablicę, ślad i skrzynkę; `editor` i `admin` — także decydują
   przyciskami. Bez roli — odmowa. Organizacja: `PDI_SUITE_ORGANIZATION` (jedna, jak w DI Definition). Rekomendacja: tak.
4. **Kto zdecydował:** `decided_by` = nazwa osoby z tokenu (pole jest tekstem; kontrakt bez zmian). Rekomendacja: tak.
   Stały identyfikator osoby (`sub`) w decyzji wymaga nowego pola w kontrakcie (`decided_by_id`, 0.25.0) — osobna
   decyzja, razem z Admin Console (AC1), gdy będzie wiele osób.
5. **MCP bez zmian w tym kroku.** Rekomendacja: tak; zdalny MCP z OAuth to osobny krok z `TODO.md`.

## Kroki

1. `src/pdi/suite_login.py`: odkrywanie, PKCE, wymiana kodu, ID token RS256 z JWKS wystawcy (`iss`, `aud`, `azp`,
   `exp`, `nonce`) — weryfikacja RS256 przez `cryptography`, która już jest w `uv.lock` (50.0.2, zależność pośrednia
   przez `mcp`; sprawdzone 2026-11-25): wpisana jako bezpośrednia w `pyproject.toml`, bez nowej paczki.
2. Konsola: trasy `/login`, `/callback`, `/logout`; sesje; role na trasach i przyciskach; `decided_by` z sesji.
3. `sdlc up`: zmienne `PDI_SUITE_*` z `~/.sdlc/env` (sekret z `npm run identity -- secrets`), adres przekierowania
   `REDIRECT_DI_DECISION=http://127.0.0.1:8788/*` w `configure`.
4. Testy z fałszywym wystawcą (jak w trzech poprzednich aplikacjach), potem na żywo z lokalnym Keycloakiem.

## Ryzyka

- Sesje w pamięci znikają przy restarcie konsoli: trzeba zalogować się ponownie (akceptowalne lokalnie).
- `cryptography` jako zależność bezpośrednia: wersja z `uv.lock` bez zmian; uzasadnienie w commicie.

## Co wyszło przy wdrożeniu (2026-11-25)

- Widoki konsoli wstawiają `?t=` do każdego linku; w trybie suity dostają stałą, niesekretną wartość (`s`), a dostęp
  daje sesja w ciasteczku (HttpOnly, SameSite=Lax). W adresie nie ma już poświadczenia.
- POST w trybie suity wymaga nagłówka Origin albo Referer z tej konsoli (sesja jedzie w ciasteczku).
- Rola `viewer` widzi strony bez przycisków decyzji, z wyjaśnieniem; serwer i tak odmawia (403).
- `sdlc up` startuje konsolę po konfiguracji suity (sekret klienta `di-decision` powstaje przy pierwszym `up`);
  połowiczne `PDI_SUITE_*` nie trafiają do konsoli.
- Na żywo (Keycloak 26.4.7, di-identity 0.1.3): osoba spoza `acme` — 403 z powodem; `viewer` — tylko odczyt, decyzja 403;
  `editor` — decyzja zapisana z `decided_by: Ola Test`.
