# Linksifty

Linksifty zamienia zapisane linki i wklejony tekst w notatki z cytatami, ocenę
ośmiu kryteriów i powtarzalny werdykt: `valuable`, `to_review` albo `hype`.
Użytkownik może porozmawiać z AI o analizie i jej temacie, sprawdzić dodatkowe
źródła oraz śledzić wykorzystanie miesięcznego budżetu.

Aktualny zakres to **analiza tekstu** stron WWW, postów, wątków i Articles z X.
Obrazy, wideo i audio są pomijane z widoczną informacją w wyniku. Niepełne
pobranie wymaga wklejenia treści; krótki częściowy podgląd nie stanowi analizy.

## Dokumentacja

| Potrzebuję… | Dokument |
| --- | --- |
| Zorientować się w projekcie | [Indeks dokumentacji](docs/README.md) |
| Poznać komponenty i odpowiedzialności | [Architektura](docs/architecture/overview.md) |
| Prześledzić działanie aplikacji | [Przepływy](docs/flows/README.md) |
| Obejrzeć diagramy | [Diagramy HTML i edytowalne JSON](docs/diagrams/README.md) |
| Zrozumieć testy i proces wydania | [CI/CD](docs/deployment/ci-cd.md) |
| Wdrożyć lub wycofać wersję | [Runbook deploymentu](docs/deployment/README.md) |
| Skonfigurować usługi i migracje | [Szczegółowy setup](docs/deployment/setup.md), [Supabase](docs/deployment/supabase.md) |
| Poznać założenia i dalsze prace | [Wizja](docs/product/vision.md), [roadmapa](docs/roadmap.md) |

## Stack i układ repozytorium

```text
backend/src/linksifty/
  api/             HTTP, uwierzytelnianie, walidacja transportu
  application/     przypadki użycia, przetwarzanie, chat
  domain/          czyste reguły oceny i walidacji treści
  infrastructure/  Supabase, OpenRouter, X, Brave, Resend, Langfuse
  main.py          składanie aplikacji i adapterów
frontend/          React 19, TypeScript, Vite; npm
supabase/          migracje PostgreSQL, testy SQL, harmonogram retencji
docs/              dokumentacja i diagramy
.github/workflows/ testy backendu, frontendu i kontenera
```

Backend używa Python 3.11+, FastAPI, Pydantic v2 i `uv`. Dane oraz sesje
obsługuje Supabase. Frontend jest statycznym buildem na Vercel, API osobnym
kontenerem na Render. Zadania są trwałe w bazie, a wykonuje je ograniczony
runner wewnątrz API. Nie ma osobnego stale działającego workera ani brokera.

## Start lokalny

Wymagania zgodne z CI: Python 3.11, uv 0.12.17, Node 22.23.2 oraz npm.
Polecenia backendu uruchamiaj z katalogu głównego, npm wyłącznie z `frontend/`.

```sh
uv sync --locked --package linksifty --group dev
uv run --package linksifty uvicorn linksifty.main:app --reload
```

[Health](http://127.0.0.1:8000/health) działa bez kluczy i zwraca
`{"status":"ok"}`. [OpenAPI UI](http://127.0.0.1:8000/docs) opisuje kontrakt HTTP.
Bez konfiguracji Supabase prywatne funkcje nie będą działać.

Dla rzeczywistych danych przygotuj lokalny, nieśledzony `.env` na podstawie
[`.env.example`](.env.example), nie nadpisując istniejącego pliku. Skonfiguruj
Supabase, migracje i Google OAuth według [setupu](docs/deployment/setup.md#9-local-development-environment).
API samo nie wczytuje `.env`; uruchom je przez:

```sh
uv run --env-file .env --package linksifty uvicorn linksifty.main:app --reload
```

W `frontend/.env.local` ustaw **tylko publiczne wartości**:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_SUPABASE_URL=https://<project-ref>.supabase.co
VITE_SUPABASE_ANON_KEY=<public-publishable-or-anon-key>
```

W osobnym terminalu:

```sh
cd frontend
npm ci
npm run dev
```

Otwórz `http://localhost:5173` i ustaw tę samą wartość w `FRONTEND_ORIGIN` API
oraz dozwolonych przekierowaniach Supabase. Backendowe `LINKSIFTY_DEMO_MODE=true`
udostępnia przykładowe odpowiedzi API bez trwałego zapisu; nie jest pełnym
obejściem logowania w UI. Na hostingu pozostaw `false`.

## Weryfikacja

```sh
uv run --package linksifty pytest backend/tests
uv run --package linksifty mypy --strict backend/src
uv run --package linksifty ruff check .
uv run --package linksifty ruff format --check .
agent-toolkit check
```

W `frontend/`: `npm run lint`, `npm test -- --run`, `npm run build`.
Integracje w testach są mockowane. Testy bazy, współbieżności i akceptacja na
hostingu są osobnymi bramkami opisanymi w [CI/CD](docs/deployment/ci-cd.md).

## Deployment i ważne zasady

[Runbook](docs/deployment/README.md) opisuje kolejność **migracje → API → frontend**,
zmienne, smoke testy, retencję i rollback. GitHub Actions wykonuje CI; repozytorium
nie zawiera automatycznego CD ani aplikowania migracji. Ustawienia integracji Git
w panelach hostingu wymagają osobnego sprawdzenia.

Każda operacja na treści jest ograniczona do właściciela, również dla administratora.
Płatne wywołania najpierw rezerwują budżet; nieznany koszt pozostaje zarezerwowany.
Klucze service-role, OpenRouter, X, Brave i Resend pozostają na serwerze.
Szczegóły funkcji, języka wyników i zmian wdrożeniowych zawiera
[referencja funkcji](docs/product/feature-reference.md). Przełącznik motywu obsługuje
jasny i ciemny interfejs, preferencję systemową i zapamiętanie wyboru w przeglądarce.

The Admin tab shows the number of accounts awaiting approval, refreshed on
navigation and after account decisions. The count is hidden when zero or unavailable.

Projekt korzysta z agent-toolkit; reguły współpracy zawiera [AGENTS.md](AGENTS.md).
Osobna implementacja tego samego produktu służy porównaniu procesu pracy z agent-toolkit.
