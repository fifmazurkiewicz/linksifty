# CI/CD

Stan konfiguracji repozytorium: 2026-10-22.
Źródło prawdy: [ci.yml](../../.github/workflows/ci.yml).
[Diagram](../diagrams/delivery.html) · [Runbook wydania](README.md).

## Co działa automatycznie

GitHub Actions uruchamia workflow `CI` na `push`, `pull_request` oraz ręczne
`workflow_dispatch`. Nie ma filtra ścieżek ani gałęzi. Uprawnienia workflow to
`contents: read`; checkout nie zachowuje credentials. Nowe uruchomienie dla
tej samej referencji anuluje wcześniejsze (`cancel-in-progress: true`).

Trzy niezależne joby na `ubuntu-latest`, każdy z limitem 15 minut:

| Job | Środowisko i instalacja | Sprawdzany wynik |
| --- | --- | --- |
| Backend checks | Python 3.11, uv 0.12.17; `uv sync --locked --package linksifty --group dev` | pytest backendu, mypy strict, Ruff lint i format |
| Frontend checks | Node 22.23.2; `npm ci` wewnątrz `frontend/` | Oxlint, Vitest w trybie jednorazowym, TypeScript i produkcyjny build Vite |
| Backend container smoke | `docker build --tag linksifty-smoke .` | Faktyczny start obrazu, runtime `PORT`, health, anonimowe `401`, UID 10001 i brak `/app/.env` |

Backend i frontend korzystają z lockfile oraz cache zależności. Testy mockują
integracje i nie potrzebują sekretów dostawców. Kontener startuje z `PORT=8123`,
a health musi zwrócić dokładnie `{"status":"ok"}`. Krok `always()` zbiera logi
i usuwa kontener testowy. Obraz nie jest publikowany do rejestru.

## Granica między CI i CD

**W repozytorium nie ma joba wdrażającego, publikacji obrazu ani automatycznych
migracji.** Nie ma też konfiguracji Render Blueprint, Vercel deployment workflow
ani deklaracji środowisk z bramkami akceptacji. Oba hostingi mogą mieć integrację
Git skonfigurowaną w panelach; jej bieżącego stanu nie potwierdza kod.

Wydanie wymaga wskazania rewizji, weryfikacji zgodności schematu, uruchomienia
migracji i wdrożenia dopasowanych wersji API/UI. Zielone CI samo nie gwarantuje,
że host nie wdroży wcześniej. Render oferuje `After CI Checks Pass` oraz `Off`;
przy skoordynowanej migracji operator powinien świadomie kontrolować moment
wdrożenia. To dostępne opcje platformy, nie potwierdzone ustawienia projektu.
[Dokumentacja Render](https://render.com/docs/deploys).

Zasady ochrony gałęzi, wymagane checks oraz zasady publikacji Vercel trzeba
sprawdzić osobno. Opis manualnej ścieżki znajduje się w [runbooku](README.md).

## Lokalne odpowiedniki i dodatkowe bramki

Z katalogu głównego:

```sh
uv run --package linksifty pytest backend/tests
uv run --package linksifty mypy --strict backend/src
uv run --package linksifty ruff check .
uv run --package linksifty ruff format --check .
agent-toolkit check
```

Z `frontend/`:

```sh
npm run lint
npm test -- --run
npm run build
```

`agent-toolkit check` jest wymaganym sprawdzeniem lokalnym i nie jest instalowany
ani wykonywany przez obecny workflow. Niedostępny runtime należy zgłosić jako lukę.

Testy PostgreSQL/RLS/współbieżności wymagają istniejącej, zmigrowanej,
jednorazowej bazy na loopback z nazwą kończącą się `_test`, pgTAP i `psql`.
Po prywatnym ustawieniu `LINKSIFTY_TEST_DATABASE_URL` uruchom:

```sh
uv run --package linksifty python backend/tests/integration/check_processing_database.py
```

Gate nie instaluje ani nie uruchamia bazy i nie aplikuje migracji. Kod `77`
oznacza brak dostępnego środowiska, nie zaliczenie. Wykonuje listę testów SQL
oraz wyścigi zapisów określone w [skrypcie](../../backend/tests/integration/check_processing_database.py).
Nie należy zastępować jego ograniczeń połączeniem do produkcyjnej bazy.

## Co pozostaje poza obecnym CI

- Egzekwowanie RLS, ograniczeń własności i blokad SQL na prawdziwej bazie.
- OAuth, poprawne originy, sekrety, pg_cron i migracje na docelowym hostingu.
- Dostępność/model quality i rzeczywiste rozliczenie OpenRouter, Brave, X, Resend.
- SSE, cold start, restart i odzyskiwanie pracy na wybranym planie hostingu.
- Akceptacja UI w przeglądarce i kompletna ewaluacja produktu.

Takie sprawdzenia zapisuje się jako osobne dowody wydania. Płatne testy i działania
na środowiskach zewnętrznych wymagają świadomej zgody właściciela; ta aktualizacja
dokumentacji ich nie wykonuje.
