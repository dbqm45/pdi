# 9. Weryfikacja planu projektu

> **Zastąpione 2026-10-23** przez [plan jednego flow SDLC](plan-jeden-flow-sdlc.md). Co z tego dokumentu przechodzi do nowego kierunku: [dokument 12](12-zmiana-kierunku-sdlc.md).

Przegląd wstępnego planu ([08-plan-projektu.md](08-plan-projektu.md)) w świetle dwóch nowych ustaleń:

- **Pierwszym użytkownikiem jest PM jako właściciel decyzji.**
- **Nie mamy jeszcze dostępu do żadnych inicjatyw** — ani zakończonych, ani realizowanych.

Plan w [08](08-plan-projektu.md) zawiera już poprawki opisane poniżej. Ten dokument wyjaśnia, co zmieniono i dlaczego.

## 9.1. Ocena ogólna

Plan jest dobry kierunkowo: zaczyna od dowodów zamiast od kodu, ogranicza zakres MVP, porównuje rozwiązanie z ogólnym asystentem AI i stawia twarde pytanie na koniec każdego etapu. Jest spójny z dokumentami 01–07, z drobnymi różnicami w nazewnictwie (patrz 9.5).

Ma jednak jedno **założenie nośne, które obecnie jest fałszywe**: że mamy organizację, w której można przeprowadzić discovery, zebrać 5–10 inicjatyw, rozmawiać z interesariuszami i uruchomić pilotaż. Od tego zależą etapy 1, 2, 5 i plan pierwszych pięciu dni. Bez naprawy tego punktu plan nie może wystartować.

## 9.2. Problemy krytyczne

### K1. Brak źródła przypadków i użytkowników → dodany Etap 0

Etapy 1.2, 1.3, 2.3, 5 i dni 1–3 zakładają dostęp do rzeczywistych inicjatyw i osób. Nie mamy go.

**Poprawka:** nowy **Etap 0 — Design partnerzy i przypadki** (tygodnie 0–3), który poprzedza discovery i ma twardy warunek przejścia:

- ≥ 3 PM-ów z co najmniej 2 różnych organizacji zgadza się być design partnerami (wywiady + udostępnienie materiałów + udział w teście),
- ≥ 6 przypadków z materiałami **z chwili podjęcia decyzji** (nie odtworzonymi później),
- ustalone zasady poufności (patrz K3).

Źródła przypadków, w kolejności wartości dowodowej:

| Źródło | Do czego się nadaje | Ograniczenie |
|---|---|---|
| Bieżące inicjatywy design partnerów | Test wartości i pilotaż prospektywny | Brak znanego rezultatu |
| Zakończone inicjatywy design partnerów | Test retrospektywny z oceną ex post | Trudno odtworzyć stan wiedzy z chwili decyzji |
| Własne doświadczenie autora projektu | Dzień 2–3, kalibracja katalogu wzorców | Pamięć + hindsight bias; nie walidują wartości |
| Publiczne studia przypadków / post-mortemy | Inspiracja wzorców ryzyka | Brak materiałów źródłowych z chwili decyzji |
| Przypadki syntetyczne z celowo wprowadzonymi błędami | Testy regresyjne detektorów (jak `examples/status-zamowienia.yaml`) | **Nie dowodzą wartości** — system znajduje to, co do nich włożyliśmy |

Zasada: przypadki syntetyczne służą do testowania, czy system działa poprawnie, **nigdy** do wykazania, że ma wartość.

### K2. Bramki go/no-go bez progów → progi ustalane przed testem, nie po

Plan słusznie unika arbitralnych progów przed zebraniem danych bazowych. Ale pytania „Czy warto budować MVP?” i „Czy rozwiązanie poprawia proces?” bez progu ustalonego **przed** zobaczeniem wyników zamieniają się w ocenę subiektywną. Przy pracy nad własnym pomysłem to realne ryzyko (przesuwanie poprzeczki).

**Poprawka:** progi są wstępne (patrz [06](06-mvp-i-pilotaz.md#64-metryki)) i mogą zostać skorygowane po Etapie 1, ale **muszą zostać zapisane w repozytorium przed rozpoczęciem testu, którego dotyczą**. Dodano też jawne kryteria zatrzymania projektu (kill criteria) — sekcja 4 planu.

### K3. Poufność materiałów → wymóg w Etapie 0

Design partnerzy będą udostępniać materiały strategiczne cudzej organizacji, a te trafią do modelu AI. Bez rozwiązania tego na początku nikt nie udostępni prawdziwych inicjatyw — a bez nich test wartości jest niemożliwy.

**Poprawka:** w Etapie 0 — prosta umowa poufności, zasady anonimizacji, jawna informacja, który dostawca modelu przetwarza dane i na jakich warunkach (brak trenowania na danych), możliwość usunięcia materiałów.

## 9.3. Konsekwencje wyboru „PM jako właściciel decyzji”

Plan był pisany neutralnie wobec użytkownika. Wybór PM-a zmienia kilka rzeczy:

1. **PM jest jednocześnie użytkownikiem i autorem decyzji, którą system kwestionuje.** To najważniejsze napięcie produktu. System musi działać jak sparingpartner PM-a, a nie jak audytor jego pracy.
2. **Brief jest domyślnie prywatny dla PM-a.** PM decyduje, co i komu udostępnia. Bez tego PM nie będzie wrzucał do systemu słabych, wczesnych materiałów, a właśnie tam system ma największą wartość.
3. **Ostrzeżenia trybu Guardian trafiają do PM-a, nie do jego przełożonych.** Poziom portfolio (Etap 6) wymaga osobnej decyzji o widoczności, opartej na danych zagregowanych, nie na ocenie poszczególnych PM-ów.
4. **Miara wartości dla PM-a:** czy PM zmienił, zawęził lub opóźnił decyzję, czy zamknął lukę, czy wrócił do systemu przy kolejnej inicjatywie bez zachęty. Odpowiedź „to było trafne” jest za mało — liczy się, czy PM coś z tym zrobił.
5. **PM rzadko jest właścicielem źródeł** (analityka, support, badania). Szczebel 2 drabiny KGC („analiza istniejących danych”) oznacza zwykle prośbę do kogoś innego. System powinien przygotować tę prośbę tak, żeby PM mógł ją po prostu wysłać.
6. **Ryzyko efektu potwierdzenia:** PM może korzystać z systemu, żeby uzasadnić już podjętą decyzję. Stress test i obowiązkowe pokazywanie dowodów przeciwnych to tu podstawowe zabezpieczenie.

## 9.4. Problemy mniejsze

| # | Miejsce w planie | Problem | Poprawka |
|---|---|---|---|
| M1 | Etap 1, rezultat „Wybór jednego procesu do pilotażu” | Proces jest już wybrany: od pojawienia się inicjatywy do decyzji o dalszym postępowaniu | Zmienione na „potwierdzenie lub korekta wybranego procesu” |
| M2 | Etap 2.3, test trzech wariantów | Bez zaślepienia oceniający faworyzują „nowe narzędzie”; ogólny asystent AI musi dostać te same materiały i dobry prompt, inaczej porównanie jest nieuczciwe | Dodane: zaślepienie źródła, te same materiały, sensowny prompt bazowy |
| M3 | Etap 2.3 „prototyp PDI” przed Etapem 4 | Niejasne, co to jest przed budową MVP | Doprecyzowane: ręczna analiza według modelu PDI (Wizard of Oz) + prompt ustrukturyzowany według schematu |
| M4 | Etap 3.3, siedem warstw | Dla MVP z ręcznym importem plików warstwy 2, 5 i 7 mogą być minimalne | Dodana adnotacja, co z każdej warstwy jest potrzebne w MVP |
| M5 | Etap 4, Funkcja 5 Change Impact Monitor | Monitoring „wybranego źródła” wymaga integracji, której MVP nie przewiduje | W MVP: ponowne wgranie zmienionego / nowego materiału; integracja z jednym źródłem dopiero w Etapie 6 |
| M6 | Etapy 1 i 2 | Nakładają się w tygodniu 2 przy jednej osobie w zespole | Harmonogram przesunięty o Etap 0; analiza konkurencji (2.1) może iść równolegle z Etapem 0, bo nie wymaga partnerów |
| M7 | Sekcja 6, zespół | Plan zakłada 4–6 ról; obecnie nie wiemy, kto realnie pracuje nad projektem | Dodany wariant minimalny (1–2 osoby + design partnerzy jako eksperci domenowi) |
| M8 | Cel, punkt 4 | Literówka „Ocenią” | Poprawione na „Ocenia” |
| M9 | Harmonogram 12–16 tygodni | Nierealny bez partnerów i bez zespołu | Harmonogram liczony od zamknięcia Etapu 0, z adnotacją |

## 9.5. Spójność z dokumentami 01–07

| Plan | Dokumenty 01–07 | Uwagi |
|---|---|---|
| Evidence Fusion | Rekonstrukcja Living Decision Model ([02](02-living-decision-model.md)) | Ta sama zdolność |
| Decision Risk Radar | [03](03-decision-risk-radar.md), wzorce R1–R12 | Zgodne |
| Active Copilot | Tryb Copilot w KGC ([04](04-knowledge-gap-closure.md)) | Zgodne |
| Readiness Assessment | Decision Readiness Brief ([03 §3.3](03-decision-risk-radar.md#33-wynik-radaru-decision-readiness-brief)) | W specyfikacji to wynik radaru, nie osobna funkcja — warto tak zostawić, żeby nie powstał osobny „wynik gotowości” |
| Change Impact Monitor | Zadanie 4 MVP ([06](06-mvp-i-pilotaz.md)) | Zgodne po poprawce M5 |
| Mierniki bez progów | Progi wstępne w [06 §6.4](06-mvp-i-pilotaz.md#64-metryki) | Pogodzone w K2 |
| „Nie zakładajmy bazy grafowej” | Schemat JSON + reguły na grafie w pamięci | Zgodne — graf jest modelem pojęciowym, nie wyborem bazy danych |

## 9.6. Rozstrzygnięcia i pytania otwarte

| Pytanie | Stan | Gdzie w planie |
|---|---|---|
| Kto pracuje nad projektem | **Rozstrzygnięte:** jedna osoba | [Plan §6](08-plan-projektu.md#6-zespół) — harmonogram ok. 16–22 tygodni po Etapie 0 |
| Charakter projektu | **Warunkowo:** komercyjny przy potencjale rynkowym i luce, wewnętrzny przy silnej konkurencji | [Plan, Etap 2.1](08-plan-projektu.md#etap-2-walidacja-koncepcji-i-przewagi) — reguła decyzyjna oparta na pokryciu scenariuszy |
| Źródło design partnerów | **Otwarte** | [Profil partnera §8](../outreach/profil-design-partnera.md#8-kanały-pozyskiwania) — kanały do przetestowania |

**Nowe pytanie wynikające z odpowiedzi o charakterze projektu:** „narzędzie wewnętrzne” zakłada organizację, w której będzie używane. Skoro obecnie nie ma dostępu do żadnej organizacji — dla kogo byłoby to narzędzie wewnętrzne? Możliwe odpowiedzi: organizacja, w której autor pracuje lub będzie pracował; organizacja jednego z design partnerów; własne narzędzie autora do pracy doradczej. Każda z nich zmienia dalszy kierunek, więc warto ją ustalić najpóźniej na koniec Etapu 2.
