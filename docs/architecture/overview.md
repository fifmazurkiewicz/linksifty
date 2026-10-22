# Architektura Linksifty

Stan kodu sprawdzony 2026-10-22. Dokument opisuje implementację w repozytorium,
nie potwierdza konfiguracji ani aktywacji usług na hostingu.
[Diagram systemu](../diagrams/system.html) · [Przepływy](../flows/README.md) ·
[Deployment](../deployment/README.md).

## Komponenty i odpowiedzialności

| Komponent | Odpowiedzialność | Źródło |
| --- | --- | --- |
| React / TypeScript / Vite | Logowanie, Add, kolejka, szczegóły, chat, ustawienia, administracja | [frontend/src](../../frontend/src) |
| FastAPI | HTTP, CORS, weryfikacja tożsamości, odpowiedzi i SSE | [main.py](../../backend/src/linksifty/main.py), [api](../../backend/src/linksifty/api) |
| Usługi aplikacyjne | Przypadki użycia, pobieranie, budżet, koordynacja analizy i chatu | [application](../../backend/src/linksifty/application) |
| Domena | Ocena gotowości treści, kryteria, punktacja i werdykt bez I/O | [domain](../../backend/src/linksifty/domain) |
| Adaptery | HTTP do Supabase i dostawców, pobieranie WWW, telemetryka | [infrastructure](../../backend/src/linksifty/infrastructure) |
| Supabase Auth | Google OAuth, sesja, zweryfikowana tożsamość | [supabase_auth.py](../../backend/src/linksifty/infrastructure/supabase_auth.py) |
| Supabase Postgres / PostgREST | Trwałe dane, RPC, blokady, RLS, rezerwacje, leasing zadań | [migracje](../../supabase/migrations) |

Kierunek zależności to transport → usługa aplikacyjna → kontrakty i domena.
`main.py` tworzy konkretne adaptery; część prostych tras jest nadal zdefiniowana
w tym pliku. Reguły punktacji pozostają w `domain/scoring.py`.
Runtime korzysta z `ProcessingService`; starszy `AssessmentService` nie jest
głównym koordynatorem wywołań dostawców.

## Topologia i granice zaufania

Vercel dostarcza statyczny frontend. Przeglądarka łączy się z Supabase Auth
w celu logowania i z API na Render, wysyłając token w nagłówku `Authorization`.
API weryfikuje token przez `/auth/v1/user`, a następnie przekazuje zweryfikowany
UUID do usług. Nie ufa identyfikatorowi właściciela przesłanemu przez klienta.

Backend używa PostgREST/RPC przez HTTP, a nie bezpośredniego połączenia SQL.
Service-role ma szerokie uprawnienia, dlatego filtry właściciela i sprawdzanie
własności w RPC są konieczne niezależnie od RLS. Administrator zarządza kontami
i limitami; nie dostaje dostępu do cudzych linków, analiz ani rozmów.

`VITE_` zawiera wyłącznie publiczny URL API, URL Supabase i publiczny klucz.
Sekrety dostawców pozostają na API. `FRONTEND_ORIGIN` konfiguruje jeden origin
produkcyjny; bez niego kod dopuszcza lokalne originy na porcie 5173.
CORS nie zastępuje autoryzacji.

## Przetwarzanie i trwałość

Zgłoszenie tworzy link oraz zadanie w jednej transakcji, zanim API zwróci `202`.
Runner działa jako zadanie asyncio w procesie API: maksymalnie trzech właścicieli
jednocześnie na instancję i pięć zadań na jedno wybudzenie. Zgłoszenie, wznowienie
lub odczyt kolejki wybudza pracę; osobny broker i stale działający worker nie istnieją.

Leasing i zapis w PostgreSQL zabezpieczają własność pracy także po restarcie.
Runtime używa heartbeat co 15 sekund i lease 60 sekund. UI odróżnia trwały etap
od aktywności workera; heartbeat starszy niż 45 sekund oznacza pauzę. SSE
`/v1/activity` kończy połączenie po około 50 sekundach, a klient łączy się ponownie.
To przepływ snapshotów, nie trwały dziennik zdarzeń.

Uśpiony lub zrestartowany serwer może wznowić pracę przy następnej wizycie.
Ponowne przejęcie zadania z rezerwacją uruchamia uzgodnienie kosztu lub odzyskanie
zapisanego wyniku, a nie automatyczne ponowienie płatnego wywołania.

## Dane i naliczanie kosztów

| Grupa | Zawartość i cykl życia |
| --- | --- |
| `account_profiles`, `account_notifications`, `settings` | Dostęp, próba, status powiadomienia, próg i rubric, miesięczny limit |
| `items`, `source_contents`, `jobs` | Link, kompletny tekst, etapy, lease i dane potrzebne do wznowienia |
| `assessments`, `citations` | Wynik oraz cytaty powiązane z rzeczywistymi fragmentami źródła |
| Chat i research | Rozmowy, tury i zebrane źródła ograniczone do właściciela i elementu |
| `usage_months`, `usage_reservations` | Dokładne kwoty USD, rozliczenia i nierozstrzygnięte rezerwacje |

Schemat i nazwy pomocniczych tabel/RPC definiują [migracje](../../supabase/migrations).
Rezerwacja blokuje ustawienia właściciela i sprawdza bieżący miesiąc UTC wraz
z nierozliczonymi kwotami. Po odpowiedzi dostawcy następuje idempotentne
rozliczenie w miesiącu pierwotnej rezerwacji. Brak potwierdzonego kosztu nie
oznacza kosztu zerowego. Czytanie X jest rozliczane poza wspólnym limitem
OpenRouter/Brave.

Usunięcie elementu kasuje jego treść i powiązane wyniki, lecz zachowuje dane
niezbędne do rozliczenia opłat. Czyszczenie przeterminowanych treści i szczegółów
kosztów wymaga aktywnego [harmonogramu retencji](../../supabase/retention.sql),
jeśli ma działać bez wizyt. Nierozliczone rezerwacje i sumy bieżącego miesiąca
są zachowywane; szczegóły kosztów mają 30-dniową retencję.

## Dostawcy i ograniczenia

- OpenRouter generuje treść analizy, tytuły, podglądy i odpowiedzi chatu.
  Wynik liczbowy oraz werdykt oblicza backend. Wspierane modele i ograniczenia
  kosztów określa adapter; dowolny identyfikator modelu nie gwarantuje działania.
- Publiczne WWW jest pobierane z walidacją adresów, przekierowań, DNS i limitów.
  X korzysta z opcjonalnego oficjalnego adaptera po włączeniu odczytów.
- Brave i selektor Jev są opcjonalne. Analiza wymaga osobnej zgody na research;
  wynik wyszukiwarki sam nie jest dowodem. Dopiero pobrane fragmenty mogą być cytowane.
- Czytane są teksty. Moduły historycznego odczytu obrazów pozostają w repozytorium,
  ale nie są podłączone do bieżącego przetwarzania nowych analiz.
- Resend wysyła powiadomienie po zatwierdzeniu konta. Langfuse jest opcjonalny;
  jego awaria nie zatrzymuje pracy, a włączone ślady mogą zawierać ograniczoną,
  zredagowaną treść artykułów i modeli. Retencja śladów jest osobną konfiguracją.

## Historia i utrzymanie

[Historia implementacji](implementation-history.md) zachowuje wcześniejsze
diagramy i opisy etapów wdrażania. [Referencja funkcji](../product/feature-reference.md)
zawiera szczegółowe uwagi przeniesione z README. Przy zmianie zachowania aktualizuj
ten dokument, odpowiedni flow i źródła diagramów; historyczny plan nie jest
dowodem aktualnej gotowości wdrożenia.
