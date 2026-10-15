# Progress — processing, USD usage and inbox

**Status: lokalna implementacja ukończona; bramki wydania otwarte (2026-10-15).**
Właściciel wznowił prace poleceniem „dokończ zadania które zapisaliśmy”.
Kanoniczny zapis wykonania: ten plik. Zakres: `plan.md`; lista pozostałych prac:
`tasks.md`; widok pochodny: `plan-kanban.html`.

## Uzgodnienia

- Zaakceptowany zakres: aktualne USD, prawdziwy postęp, limity admina, Settings i zrozumiała kolejka.
- Szczegóły kosztów przechowywane 30 dni; bieżące sumy miesiąca UTC oraz nierozliczone rezerwacje przetrwają cleanup.
- Natywne wykonanie w tej sesji, bez subagentów i nowych zależności.
- Nie wykonywano płatnych wywołań modelu, wdrożeń, wiadomości ani push.

## Stan planu

| ID | Wynik | Stan |
| --- | --- | --- |
| T1 | Ustawienia, rejestr USD, transakcje, migracja i testy bazy | Done lokalnie: sześć migracji, 63 asercji pgTAP, rzeczywiste równoległe rezerwacje i wykrywanie regresji PASS. |
| T2 | Bezpieczne pobieranie i wykonawca OpenRouter | Done lokalnie: pełny bound modelu, recovery, limity, utrata dzierżawy, osierocone rezerwacje; testy green. |
| T3 | API i postęp SSE | Done lokalnie: scope, reconnect, wygaśnięcie konta, heartbeat i paused UI; hosted cold start pozostaje E1. |
| T4 | Kolejka, wyniki, Settings, limity admina | Done lokalnie: testy rzeczywistych komponentów, lint/build; nowa inspekcja wizualna niedostępna. |
| T5 | Kontrole, dokumentacja, review i lokalny commit | Blocked: dostępne kontrole i dokumentacja ukończone; wymagany agent-toolkit niedostępny, review pozostaje revise. |
| E1 | Aktywacja i odbiór docelowego środowiska | Planned: poza lokalnym wykonaniem, wymaga wskazanego środowiska i zgody na koszty/zmiany zewnętrzne. |

## Dostarczona implementacja

- Migracja `000005`: ustawienia, budżet admina, atomowe rezerwacje i rozliczenia do pierwotnego miesiąca, właścicielski scope, server-only mutacje, dzierżawy i retencja.
- Wykonawca: maksymalnie trzech właścicieli równolegle, pięć zadań na przebudzenie; zapis wyniku przed settlement, brak ponownego inference dla niepewnej próby. Znany zapisany koszt ma pierwszeństwo przed lookupem generacji.
- OpenRouter: strict schema, osiem kryteriów i dokładne fragmenty źródła, Decimal koszt; rezerwacja pełnego zweryfikowanego kontekstu modelu przy wymuszonych cenach. Nieznany model blokowany przed requestem.
- Fetcher: publiczne DNS/IP dla każdego przekierowania, izolacja cookies/proxy, ograniczony czas i rozmiar, identity encoding, wykrywanie niepełnego/binarniego źródła. Nieudany fetch wymaga wklejenia, bez oceny.
- Postęp: heartbeat co 15 s, lease 60 s, świeżość 45 s; trwały etap nie udaje aktywnej pracy po zatrzymaniu wykonawcy.
- API i UI: authenticated SSE, faktyczne/reserved/remaining USD, kolejka z filtrami i bezpiecznym wznowieniem, wklejenie, zapisany wynik z cytatami, zapisywalny próg, limity admina, czyszczenie starej sesji.
- Dokumentacja konfiguracji, odzyskiwania i retencji; edytowalny diagram, roadmapa, review i dispositions.

## Końcowa weryfikacja bieżącego kodu

- Backend: **124 passed**; strict mypy: **29 plików PASS**.
- Ruff check PASS; format check PASS (**77 plików**).
- Frontend: **19 passed**; lint PASS; production build PASS.
- `git diff --check`: PASS.
- `agent-toolkit check`: exit 127, brak polecenia — otwarta REV-005.
- Gate PostgreSQL: **PASS, exit 0** na PostgreSQL 17.11 / pgTAP 1.3.4. Sześć migracji zastosowanych; 63 asercji i równoległe rezerwacje przeszły. REV-004 zamknięta dla lokalnych semantyk bazy; hosted auth pozostaje E1.
- Archify validate/deliver/check PASS; browser-check skipped (Chrome unavailable). Najnowszy receipt: `lifecycle.review-2/`.
- Próba aktualnego browser QA została odrzucona przez politykę URL narzędzia. Nie obchodzono ograniczenia. Aktualne testy komponentów potwierdzają szczegóły, wklejenie, wznowienie i edycję ustawień; dawne screenshots są historycznym dowodem mockowanego QA.

## Otwarte zależności i przekazanie

Właściciel zatwierdził przygotowanie lokalnego runtime. Zainstalowano PostgreSQL 17 przez Homebrew i pgTAP 1.3.4 z oficjalnego PGXN (checksum zweryfikowana). Jednorazowy klaster `/private/tmp/linksifty-processing-pg17` i baza `linksifty_processing_test` zawierają wyłącznie fikcyjne dane. Serwer testowy zatrzymany po testach; bez usługi startowej. Minimalny fixture auth nie zastępuje hosted Supabase/GoTrue/JWT. Agent-toolkit i Graft pozostają niedostępne.
Nie zastosowano migracji ani harmonogramu w Supabase i nie aktywowano hostingu. Brak dowodu rzeczywistego kosztu/SSE na hostingu. Nie archiwizować ani nie uznawać za gotowe do wydania przed zamknięciem bramek. Implementacja zapisana w lokalnym commicie `b82959b`; dodatkowe testy/runtime docs przygotowane w kolejnym commicie. Nic nie jest wypychane.

Szczegóły dowodów: `evidence.md`; ustalenia review: `reviews/review-decisions.md`.

## Corrective follow-up

User reports hosted 000005 applied and Settings working. Supplied stuck checking-content and interruption warning prompted a matching-schema regression test: pgcrypto in extensions makes old source-write digest calls fail (42883). Added 000006 using built-in SHA256, preserving all guards; fresh six-migration gate and 63 assertions PASS. Correction is local; user must apply 000006, then refresh for safe lease recovery. Hosted exception inferred from matching reproduction, not directly inspected. Both local clusters stopped. REV-007 verified locally; agent-toolkit and hosted acceptance remain open.

## Retrieval coverage audit — 2026-10-15

Owner requested checking all retrieval/source-search points and supplied two unusable-result records. Audit confirms single-source acquisition/analysis implemented, but external discovery/corroboration, max-five source checks and official X/chat remain planned M6/C7 capabilities. Hosted success is unproven; model rejection lacks diagnostic categories. See reviews/information-retrieval-audit.md and open REV-008/009. Read-only review; no product behavior changed. Focused 62 tests passed with mocks.

## Approved Brave / Langfuse execution — 2026-10-16

Owner approved integration scope and authorized code/docs/diagram updates and push to main. See brave-langfuse-plan.md. Implemented informed opt-in Brave discovery plus up to five source fetches, source identities and exact citations, atomic shared-budget search reservations, uncertain-request no-repeat handling, categorized model rejection and optional metadata-only Langfuse spans. Migration 000007 required for activation. Local tests pass; final verification/diagram/commit underway. Keys absent and no real provider traffic. REV-008/009 locally addressed; real hosted rejection reason still unconfirmed until tracing enabled by operator.
