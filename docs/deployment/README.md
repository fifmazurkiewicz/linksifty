# Runbook deploymentu

Stan repozytorium: 2026-10-22. To procedura operatora, a nie potwierdzenie
wdrożenia. [CI/CD](ci-cd.md) · [Szczegółowy setup](setup.md) ·
[Supabase](supabase.md) · [Diagram](../diagrams/delivery.html).

## Topologia

| Usługa | Artefakt / odpowiedzialność | Konfiguracja projektu |
| --- | --- | --- |
| Supabase | Auth, PostgreSQL, PostgREST/RPC, retencja | Migracje SQL i osobny `retention.sql` |
| Render | API i oportunistyczny runner w jednym kontenerze | Root context `.`, `Dockerfile`, health `/health` |
| Vercel | Statyczny frontend | Root `frontend`, `npm ci`, `npm run build`, output `dist` |
| Dostawcy | OpenRouter; opcjonalnie Brave, X, Resend, Langfuse | Wyłącznie konfiguracja serwera |

Kolejność nowego środowiska: **Supabase → API → frontend → finalne CORS/Auth URLs
→ testy akceptacyjne**. Używaj osobnych danych i kluczy stagingowych. Preview
frontendu powinien wskazywać staging API; API konfiguruje jeden produkcyjny origin.
Nie zakładaj, że przypadkowy adres preview zostanie dopuszczony.

## Konfiguracja

Nazwy i domyślne wartości: [config.py](../../backend/src/linksifty/config.py)
i [`.env.example`](../../.env.example). Pliki z rzeczywistymi wartościami są
nieśledzone. API korzysta z environment; samo nie ładuje `.env`.

| Miejsce | Zmienne / warunek |
| --- | --- |
| API: baza i tożsamość | `SUPABASE_URL`, `SUPABASE_ANON_KEY`, server-only `SUPABASE_SERVICE_ROLE_KEY` |
| API: środowisko | `LINKSIFTY_DEMO_MODE=false`, `FRONTEND_ORIGIN`, `LINKSIFTY_ADMIN_EMAIL` |
| API: AI | `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` (domyślnie `openai/gpt-4o-mini`), `OPENROUTER_CHAT_MODEL` (domyślnie `anthropic/claude-sonnet-5.5`) |
| API: dodatkowy research | `BRAVE_SEARCH_API_KEY` i dodatnia, zweryfikowana dla planu `BRAVE_SEARCH_PRICE_PER_REQUEST_USD` |
| API: X | `X_API_BEARER_TOKEN` oraz jawne `X_API_READS_ENABLED=true`; odczyty mogą kosztować poza limitem AI/Brave |
| API: powiadomienia | `RESEND_API_KEY`, `RESEND_FROM_EMAIL` z potwierdzoną domeną nadawcy |
| API: diagnostyka | `LANGFUSE_ENABLED`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`; opcjonalny `LANGFUSE_TRACING_ENVIRONMENT` obsługiwany przez SDK |
| API: port | `PORT` dostarczany przez Render, domyślnie 8000 w obrazie |
| Frontend: publiczny build | `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` |

Nazwy modeli opisują konfigurację kodu, nie niezależnie potwierdzoną dostępność
lub aktualną cenę w katalogu dostawcy. Adapter dopuszcza tylko zweryfikowane
kontrakty kosztu. `OPENROUTER_IMAGE_MODEL` jest historycznym ustawieniem i nie
włącza odczytu obrazów w obecnym trybie tekstowym.

`VITE_API_BASE_URL` to origin API bez `/v1` i końcowego slash. Nie przenoś do
frontendu service-role ani kluczy dostawców. Zmienne `VITE_` trafiają do bundla;
ich zmiana wymaga nowego buildu. [Dokumentacja Vite](https://vite.dev/guide/env-and-mode).

## Wydanie istniejącego środowiska

1. Wybierz konkretny commit i zapisz rewizję obecnego API/UI oraz listę już
   zastosowanych migracji. Sprawdź zielone CI dla nowego commitu i dodatkowe
   bramki właściwe dla zmiany. Zachowaj plan odtworzenia danych przed migracją.
2. Sprawdź auto-deploy w Render i Vercel. Dla migracji wymagającej skoordynowanego
   wdrożenia kontroluj publikację, aby kod nie wystartował ze starym schematem.
   Sama obecność CI nie jest bramką publikacji hostingu.
3. Zastosuj **tylko brakujące** migracje z `supabase/migrations/`, w kolejności
   leksykograficznej nazw. Bieżący zestaw zawiera 000001–000022; ostatnia to
   `20261020_000022_chat_research.sql`. Na nowej bazie zastosuj cały zestaw.
   Nie pomijaj historycznych migracji obrazów: kolejne migracje zależą od schematu.
4. Sprawdź wynik każdej migracji, przeładowanie schematu PostgREST, uprawnienia
   RPC i testy własności. Skrypty nie są wszystkie idempotentne — nie odtwarzaj
   ich w ciemno po błędzie ani nie usuwaj tabel, aby pozbyć się błędu.
5. Wdróż API na Render z wybranego commitu. Dockerfile i context są w root,
   Docker Command pozostaje pusty. Poczekaj na pozytywny health i sprawdź `401`
   dla anonimowego `GET /v1/items`.
6. Wdróż odpowiadający frontend na Vercel: preset Vite, root `frontend`,
   install `npm ci`, build `npm run build`, output `dist`, Node 22.x.
   Ustaw publiczne zmienne dla właściwego środowiska przed buildem.
7. Sprawdź `FRONTEND_ORIGIN`, Supabase Site URL i redirect allowlist oraz callback
   Google wskazany przez Supabase. UI wraca na swój origin; nie ma osobnej trasy
   `/auth/callback` w tej aplikacji.
8. Przeprowadź poniższy smoke/acceptance, sprawdź retencję i zapisz dowody:
   rewizje API/UI, migracje, czas, wynik testów i pozostałe ograniczenia.

Render buduje obraz z repozytorium; nie pobiera artefaktu z obecnego CI.
[Docker na Render](https://render.com/docs/docker).
Vercel publikuje build statyczny; API pozostaje osobnym serwisem.
[Vite na Vercel](https://vercel.com/docs/frameworks/frontend/vite).

## Kontener lokalnie

Z katalogu głównego, przy dostępnym Dockerze:

```sh
docker build -t linksifty-api .
docker run --rm -p 8000:8000 --env-file .env linksifty-api
```

Obraz zawiera Python 3.11.16, uv 0.12.17 i produkcyjne zależności z `uv.lock`.
Działa jako UID 10001. [`.dockerignore`](../../.dockerignore) ogranicza context
budowania; sekrety przekazuj w runtime. Kontener nie zawiera frontendu, migracji
ani bazy i nie wykonuje migracji przy starcie.

## Smoke testy i akceptacja

| Sprawdzenie | Oczekiwany wynik |
| --- | --- |
| `GET /health` | `200`, `{"status":"ok"}`; tylko liveness, nie gotowość dostawców |
| Anonimowe `GET /v1/items` | `401` przy `LINKSIFTY_DEMO_MODE=false` |
| Google OAuth i `/v1/me` | Powrót na właściwy origin, poprawny profil/status |
| Dwa konta | Brak dostępu do cudzych linków, analiz, chatu i operacji zapisu |
| Nowy link | `202`, postęp w kolejce, źródłowe cytaty i rozliczony koszt |
| Niedostępne źródło | Wymagana pełna treść; ewentualny podgląd bez score |
| Restart/przerwanie streamu | Snapshot wraca; zadanie odzyskuje się bez powielenia płatnego wywołania |
| Chat | Zapisana rozmowa, cytaty, respektowanie researchu i budżetu |
| Retencja | Cron rzeczywiście działa, zachowując nierozstrzygnięte opłaty |

Pełne próby analizy, chatu, wyszukiwania, X i emaili wykonuj dopiero po
zatwierdzeniu ich kosztu/komunikacji. Mocki i health nie zastępują tej akceptacji.
Nie używaj prywatnych treści innych osób do diagnostyki.

## Rollback i awarie

- **Błąd API/UI:** przywróć ostatni znany dobry commit/build i jego konfigurację,
  po sprawdzeniu zgodności z aktualnym schematem. Zmiany współzależne wycofuj
  razem. Nie zakładaj, że dowolna starsza wersja odczyta nowy schemat.
- **Błąd migracji:** zatrzymaj dalsze wydanie i ustal, co zostało zastosowane.
  Repozytorium nie dostarcza automatycznych down-migrations. Dobierz poprawkę
  naprzód albo zatwierdzoną procedurę odtworzenia; nie kasuj danych rozliczeniowych.
- **Nieznana opłata:** pozostaw rezerwację. Znane generation ID pozwala na
  uzgodnienie z dostawcą; bez ID wymagane jest sprawdzenie operatora.
  Instrukcja utrzymaniowa: [recovery](setup.md#13-processing-usage-retention-and-recovery).
- **Zatrzymane przetwarzanie:** sprawdź dostępność API, konfigurację modelu,
  migracje, etap i świeżość heartbeat. Kolejna wizyta może przejąć wygasły lease.
  Nie usuwaj rezerwacji i nie powielaj elementu w celu wymuszenia analizy.
- **`401` / `403` / `503`:** odpowiednio sesja, polityka konta lub niedostępna/
  nieskonfigurowana integracja. Sprawdź bezpieczne logi i właściwy origin.

Retencję uruchamia osobno [supabase/retention.sql](../../supabase/retention.sql).
Cleanup wykonywany przy wizytach nie gwarantuje retencji dla nieaktywnych kont.
Langfuse oraz `X_API_DEBUG` mogą zawierać ograniczoną zredagowaną treść;
nie włączaj ich bez rozważenia dostępu i retencji. Wyłącz debug po diagnostyce.
