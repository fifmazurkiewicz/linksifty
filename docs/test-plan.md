# Linksifty — plan najważniejszych testów

Data weryfikacji: 4 listopada 2026. Zakres: główny przepływ od dodania artykułu do oceny oraz najważniejsze integracje. Plan opisuje istniejące testy, nie deklaruje utworzenia nowych.

## Cel i granice

Użytkownik dodaje własny link lub tekst, otrzymuje analizę opartą na dostępnej treści i może nią zarządzać. Błąd pobrania nie może zamienić się w pozornie kompletną analizę, a wywołania zewnętrzne nie mogą omijać limitu kosztów ani ujawniać cudzych danych.

Testy automatyczne zastępują zewnętrzne API kontrolowanymi odpowiedziami. Sprawdzają działanie adapterów i przepływów, ale nie potwierdzają aktualności kluczy, konfiguracji produkcji, jakości wszystkich odpowiedzi modelu ani rzeczywistego doręczenia poczty. Testy SQL/RLS na prawdziwej bazie i pełne E2E wdrożenia są osobnymi bramkami; nie zostały wykonane w tej weryfikacji.

## Priorytetowe scenariusze i ryzyka

Oceny prawdopodobieństwa są konserwatywnymi założeniami planu, nie statystyką awarii. Nie służą obniżaniu głębokości istniejących testów. Ścieżki poniżej są względne wobec repozytorium.

| Obszar | Oczekiwane zachowanie i ryzyko regresji | Wpływ / prawdopodobieństwo | Istniejące testy |
| --- | --- | --- | --- |
| Dodanie artykułu | Zalogowany użytkownik zapisuje źródło i zadanie przed otrzymaniem potwierdzenia. Nieudany zapis nie może wyglądać na sukces. | Wysoki / średnie | `backend/tests/unit/test_production_items_api.py`: `test_authenticated_submission_persists_job_transaction_before_returning`, `test_failed_persistence_never_acknowledges_submission` |
| Duplikaty i limit wejścia | Powtórne dodanie nie uruchamia kolejnej analizy; zbyt duża paczka jest odrzucana. | Wysoki (koszty) / średnie | `test_duplicate_links.py`, `test_processing_api.py::test_duplicate_submission_returns_conflict_without_waking_worker`, `test_items_api.py::test_submit_rejects_more_than_five_sources` w `backend/tests/unit/` |
| Pobranie strony WWW | Pobieracz usuwa skrypty i nawigację. Strona logowania, odpowiedź częściowa lub binarna wymaga ręcznego uzupełnienia. Niepełny materiał nie otrzymuje pełnej oceny. | Wysoki / średnie | `backend/tests/unit/test_http_fetcher.py`, `test_partial_previews.py`, `test_processing_failures.py` |
| Złośliwy URL | Prywatny adres, niebezpieczne odpowiedzi DNS i przekierowanie do sieci prywatnej nie mogą doprowadzić do odczytu zasobów serwera. | Wysoki / średnie | `test_http_fetcher.py`: `test_unsafe_urls_never_reach_transport`, `test_all_dns_answers_must_be_public`, `test_redirect_to_private_ip_never_connects` |
| Brave Search i dodatkowe źródła | Klucz jest przekazywany nagłówkiem. Liczba kandydatów i pobranych stron jest ograniczona; niepewne płatne wyszukiwanie nie jest automatycznie ponawiane. Repost i błędne pobranie nie są dowodem potwierdzenia. | Wysoki (koszty i błędna ocena) / średnie | `backend/tests/unit/test_research.py`: `test_brave_uses_header_auth_and_bounds_candidates`, `test_research_checks_at_most_twenty_pages_and_never_repeats_uncertain_search`, `test_research_does_not_count_reposts_or_failed_fetches` |
| Funkcje LLM i cytowania | Odpowiedź modelu musi spełnić kontrakt i odwoływać się do właściwego źródła. Cytat z zewnętrznej strony nie może zostać przypisany artykułowi głównemu. | Wysoki / średnie | `backend/tests/unit/test_openrouter.py`, `test_calibrated_provider.py`, `test_passage_selection.py`, `test_research.py::test_external_excerpt_cannot_be_attributed_to_primary_source` |
| Koszty LLM | Timeout i brak informacji o zużyciu nie oznaczają darmowego wywołania. Niezatwierdzony model nie rozpoczyna płatnej operacji. | Wysoki / średnie | `test_openrouter.py`: `test_missing_usage_and_timeout_are_never_treated_as_free`, `test_an_unverified_model_cannot_start_a_paid_request` |
| Wynik i werdykt | Niski wynik sam w sobie nie oznacza hype. Brak wiedzy nie jest zerową oceną. Brak mocnych kryteriów kluczowych blokuje valuable. | Średni / średnie | `backend/tests/unit/test_scoring.py`, `test_calibrated_scoring.py`, w tym `test_hype_requires_explicit_cited_signal`, `test_unknown_critical_evidence_cannot_become_valuable`, `test_all_unknown_has_no_percentage` |
| Aktualizacja i odczyt | Użytkownik może uzupełnić treść swojego wpisu i zapisać własne kryteria; widok odróżnia wynik od oczekiwania na analizę. Próba aktualizacji cudzego wpisu nie ujawnia danych. | Wysoki / średnie | `backend/tests/unit/test_processing_api.py`, `frontend/tests/queue.test.tsx`, `frontend/tests/assessment.test.tsx` |
| Usunięcie i izolacja | Usuwanie wymaga potwierdzenia; anonimowy użytkownik i właściciel innego konta nie mogą usuwać ani odczytywać wpisu. | Wysoki / średnie | `backend/tests/unit/test_item_deletion.py`, `test_production_items_api.py::test_other_users_item_remains_not_found_after_authentication`, `frontend/tests/queue-delete.test.tsx` |
| Resend | Zatwierdzenie konta pozostaje skuteczne mimo awarii maila. Ponowienie korzysta z tego samego zdarzenia; błąd dostawcy nie ujawnia danych. | Średni / średnie | `backend/tests/unit/test_resend_client.py`, `test_account_service.py` |

Źródła oczekiwań: `context/foundation/prd.md`, `docs/product/vision.md`, `docs/product/feature-reference.md`, `docs/deployment/setup.md`, projektowe reguły w `AGENTS.md`. Scenariusze opisują ryzyka produktu; istniejące testy mają różną głębokość i nie wszystkie są pełnymi testami integracyjnymi.

## Uruchomienie i wynik

Z katalogu głównego:

```sh
uv run --locked --package linksifty pytest backend/tests -q
```

W katalogu `frontend/`:

```sh
npm ci
npm test -- --run
npm run test:sentry
npm run lint
npm run build
```

Wynik 4 listopada 2026: **607 testów backendu, 93 testy interfejsu i 5 dodatkowych testów Sentry — wszystkie przeszły**. Backend zgłosił jedno ostrzeżenie o wycofywaniu integracji Starlette TestClient z httpx. Mypy, Ruff, kontrola formatowania, frontend lint, produkcyjny build i `agent-toolkit check` również przeszły.

Przed odtworzeniem lokalnych zależności frontendowy build i test Sentry nie startowały z powodu brakujących pakietów Sentry. Po `npm ci` przeszły bez zmiany kodu lub pliku zależności. Audyt npm wykazał osobno 5 podatnych pakietów: 4 moderate i 1 high. Zielone testy nie oznaczają czystego audytu zależności.

## Krótka akceptacja na wdrożeniu — do wykonania osobno

1. Zalogować świeże darmowe konto i sprawdzić dostępną pulę trzech źródeł.
2. Dodać czytelny artykuł i otworzyć analizę z cytatami i werdyktem.
3. W oddzielnym źródle włączyć Brave i sprawdzić źródła porównawcze oraz zużycie budżetu.
4. Dodać niedostępny artykuł, uzupełnić treść ręcznie i sprawdzić analizę tego samego wpisu.
5. Usunąć własny wpis po potwierdzeniu. Drugie konto nie może odczytać jego szczegółów.
6. Po konfiguracji Resend zatwierdzić własne konto testowe, sprawdzić status dostawcy i odbiór wiadomości.

Te kroki mogą zużywać limity usług. Nie były wykonywane w automatycznych zestawach opisanych powyżej.
