# Linksifty completion plan

Updated: 2026-10-13. Owner: Codex for coding; Filip for accounts, credentials and live acceptance.

This is the canonical remaining-work plan. It refines the approved [original plan](2026-10-11-linksifty-personal-mvp.md) without changing product scope. The PRD and design remain the product contracts. C1–C8 replace vague “integration later” steps with reviewable deliverables. No additional approval is required for the already-authorized coding scope.

## Evidence-based baseline

- **D1 — Backend foundation: Done.** FastAPI health/configuration; frozen domain models; weighted score and threshold snapshot. Backend tests cover these rules.
- **D2 — UX/API preview: Done (preview scope).** React Inbox/Add/Settings shell builds. Inbox fetches the API and Add posts URLs. Production authentication UI, detail/chat/settings persistence and frontend behavior tests are still missing.
- **D3 — Auth and item persistence slice: Done (mock-verified scope).** Server validates bearer tokens with Supabase; owner-filtered list/detail/submission are wired; repository delete/read methods exist but are not routed. Submission RPC creates item+job together. Demo mode defaults off. SQL has not been applied or tested in PostgreSQL.
- Latest evidence: 37 backend tests, strict mypy, Ruff and frontend build passed. This is not proof of the whole MVP. `agent-toolkit check` was unavailable.

## Constraints and execution

Use `uv` for Python and npm inside `frontend/`. Preserve unrelated changes. Provider credentials remain server-only. Test integrations with mocked transports. Never assess incomplete sources. Store immutable threshold snapshots. No paid worker and no Jev/System One. Complete canonical progress before derived boards.

Order: C1 and independent C2/C3 tests first, then C4 → C5 → C6/C7 → C8. One coding task in progress at a time. External setup does not block writing any adapter or mocked test.

## Detailed tasks

### C1 — Database integrity and retention

**Status:** In progress · **Original reference:** Tasks 3–4 · **Owner:** Codex  
**Dependencies:** None  
**Files:** supabase/migrations/, infrastructure/supabase_repository.py

**Deliverable:** Owner-consistent foreign keys, server-only writes, safe lease bounds, cleanup RPC and complete repository operations.

**Acceptance:** A child record cannot reference another owner's parent. Client roles cannot claim jobs or forge assessments. Expired records cascade-delete. Claiming at the retry limit terminates cleanly. Deletion/read-state operations return 404 outside the owner.

**Verification:** Mock REST contract tests plus runnable SQL two-user RLS/ownership tests and rollback-only lease tests. Local PostgreSQL validation is required; hosted validation is an external gate.

- [ ] Write a failing behavioral test for the stated acceptance path.
- [ ] Implement the smallest complete path and its explicit failures.
- [ ] Run focused tests and strict type/lint checks; record output in evidence.md.
- [ ] Update progress and derived boards after verification.

### C2 — Safe source acquisition

**Status:** Ready · **Original reference:** Task 5 / Phase 4 · **Owner:** Codex  
**Dependencies:** None  
**Files:** infrastructure/http_fetcher.py, domain/content_policy.py, tests/unit/test_http_fetcher.py

**Deliverable:** Fetch public HTML safely and return an explicit manual-content result for every incomplete source.

**Acceptance:** Resolve and validate DNS targets including redirects; prevent DNS rebinding through the actual connection path. Reject credentials/private targets and unsupported media. Bound timeout, redirects and streaming bytes. Exclude scripts/styles/navigation from extracted text. Partial/paywall/login content never reaches assessment.

**Verification:** Mock transport tests for redirects to private IPs, oversized bodies, script-only/paywall pages, malformed URLs, timeout and successful extraction; no real fetches.

- [ ] Write a failing behavioral test for the stated acceptance path.
- [ ] Implement the smallest complete path and its explicit failures.
- [ ] Run focused tests and strict type/lint checks; record output in evidence.md.
- [ ] Update progress and derived boards after verification.

### C3 — Assessment, citations and budget

**Status:** Ready · **Original reference:** Task 6 / Phase 5 · **Owner:** Codex  
**Dependencies:** None for adapter tests; C1 for atomic budget storage  
**Files:** application/assessment_service.py, infrastructure/openrouter_client.py, domain/models.py, supabase/migrations/

**Deliverable:** Strict provider JSON, exact source citations, deterministic verdict and an atomic monthly cost cap.

**Acceptance:** Reject incomplete source text before invoking the provider. Require exactly eight criteria, valid source IDs and excerpt bounds; note claims cite evidence. Reserve worst-case cost before a paid request, reconcile actual cost, and preserve reservations on ambiguous failure. Changing settings never changes historic verdicts.

**Verification:** Mock OpenRouter request/response tests, invalid JSON and fabricated citation tests, concurrent reservation tests and threshold snapshot tests. No paid calls.

- [ ] Write a failing behavioral test for the stated acceptance path.
- [ ] Implement the smallest complete path and its explicit failures.
- [ ] Run focused tests and strict type/lint checks; record output in evidence.md.
- [ ] Update progress and derived boards after verification.

### C4 — Durable job execution

**Status:** Planned · **Original reference:** Task 4 / Phase 3 · **Owner:** Codex  
**Dependencies:** C1, C2, C3  
**Files:** application/job_runner.py, domain/jobs.py, infrastructure/supabase_repository.py

**Deliverable:** Bounded execution on authenticated requests with atomic claims and lease-fenced writes.

**Acceptance:** Drain at most two jobs per trigger. Require owner and lease token on every final write. Persist completed assessment/citations/item state atomically. Allow one transient retry, reclaim expired leases without duplicate work, and recover safely after process stop. Failed acquisition writes only manual-content status.

**Verification:** Two-claimant tests, stale-lease write rejection, crash/restart tests, paid-call ambiguity tests and no-assessment-on-failed-fetch integration tests.

- [ ] Write a failing behavioral test for the stated acceptance path.
- [ ] Implement the smallest complete path and its explicit failures.
- [ ] Run focused tests and strict type/lint checks; record output in evidence.md.
- [ ] Update progress and derived boards after verification.

### C5 — Complete product API

**Status:** Planned · **Original reference:** Task 7 · **Owner:** Codex  
**Dependencies:** C1, C4  
**Files:** api/schemas.py, api/routes/, application/item_service.py, application/item_contracts.py

**Deliverable:** Authenticated pagination/filtering, paste recovery, duplicate choices, deletion/read-state and persisted settings.

**Acceptance:** Routes remain transport-only. Batch source modes support fetch/paste. Duplicate submissions require an explicit decision. Cross-user IDs return 404. Confirmed delete cascades. Settings label future-only threshold and budget status. Queued and completed results expose truthful typed status.

**Verification:** HTTP contracts for all routes, ownership across every mutation, invalid payloads, partial batch validation, duplicates and deletion confirmation.

- [ ] Write a failing behavioral test for the stated acceptance path.
- [ ] Implement the smallest complete path and its explicit failures.
- [ ] Run focused tests and strict type/lint checks; record output in evidence.md.
- [ ] Update progress and derived boards after verification.

### C6 — Authenticated frontend workflow

**Status:** Planned · **Original reference:** Tasks 8–9 / Phase 7 · **Owner:** Codex  
**Dependencies:** C5 (UI components can be developed against mocked contracts)  
**Files:** frontend/src/lib/, frontend/src/features/, frontend/tests/

**Deliverable:** Login/session restoration, inbox and item detail connected to the API with manual recovery and settings.

**Acceptance:** Attach bearer tokens; keep provider keys server-only. Preserve inbox after submit, show pending/error/empty states, prevent repeated submissions, validate API responses, and provide retry. Include verdict filters, read/unread, delete confirmation, criteria/excerpts and mobile/keyboard access.

**Verification:** Frontend behavior tests with mocked API covering login expiry, failed submission without text loss, complete/manual/queued detail, delete confirmation, mobile layout and keyboard interactions.

- [ ] Write a failing behavioral test for the stated acceptance path.
- [ ] Implement the smallest complete path and its explicit failures.
- [ ] Run focused tests and strict type/lint checks; record output in evidence.md.
- [ ] Update progress and derived boards after verification.

### C7 — Grounded chat and official X

**Status:** In progress (chat/X/source code implemented locally; hosted acceptance remains) · **Original reference:** Tasks 5–6 / Phase 6 · **Owner:** Codex
**Dependencies:** C2, C3, C5  
**Files:** application/chat_service.py, infrastructure/x_adapter.py, api/chat.py, frontend/src/features/queue/AnalysisChat.tsx

**Deliverable:** Item-bound analysis/topic chat using saved evidence and conditional one-search research and a dedicated official X acquisition adapter.

**Acceptance:** Reject other-user and incomplete items. Answers cite saved excerpts or decline unsupported questions; input text cannot override grounding rules. Charge chat through the shared budget. X uses official API only and explains access/tier failures. For each question, search only when necessary and at most once; safely read up to 20 results. Restore exact passage evidence.

**Verification:** Mock X and OpenRouter tests for access errors, unsupported claims, invalid citation IDs, injection attempts, source cap and budget rejection.

- [ ] Write a failing behavioral test for the stated acceptance path.
- [ ] Implement the smallest complete path and its explicit failures.
- [ ] Run focused tests and strict type/lint checks; record output in evidence.md.
- [ ] Update progress and derived boards after verification.

### C8 — Release checks and deployment artifacts

**Status:** Planned · **Original reference:** Task 10 / Phase 8 · **Owner:** Codex  
**Dependencies:** C1–C7  
**Files:** .github/workflows/ci.yml, docs/deployment/, docs/release/, README.md

**Deliverable:** Repeatable CI, safe structured logs, Render/Vercel configuration and a 20-link evaluation template.

**Acceptance:** CI runs strict mypy, tests, Ruff and frontend test/build. Logs omit secrets and source bodies. Deployment instructions cover migrations, CORS, sessions and cold starts. Produce an honest completion audit against the PRD. Real provider/account evaluation remains external.

**Verification:** Full local quality gates, log redaction test, mocked complete submission-to-result test and source fallback path. Record missing agent-toolkit runtime separately.

- [ ] Write a failing behavioral test for the stated acceptance path.
- [ ] Implement the smallest complete path and its explicit failures.
- [ ] Run focused tests and strict type/lint checks; record output in evidence.md.
- [ ] Update progress and derived boards after verification.

## Mniejsze zadania wykonawcze — 2026-10-13

C1–C8 pozostają epikami. Poniższe **40 zadań** jest jednostką pracy na kanbanie; status epiku wynika z jego podzadań. Każde zadanie kończy się działającym fragmentem, testem i wpisem w evidence.md. Orientacyjna wielkość: jedna sesja robocza; bezpieczeństwo DNS, budżet i testy współbieżności mogą wymagać więcej czasu. Nie są to zobowiązania terminowe.

Ścieżki backendu poniżej są względem repo. Wszystkie zadania kodowe mają właściciela Codex. WIP = 1. Istniejące D1–D3 pozostają ukończonymi fragmentami o wcześniej opisanym zakresie.

### C1 — Baza danych i retencja

**Pliki obszaru:** supabase/migrations/; backend/src/linksifty/infrastructure/supabase_repository.py

#### C1.1 — Własność rekordów podrzędnych

**Status:** Blocked · **Zależności:** brak; lokalna weryfikacja wymaga PostgreSQL (brak runtime)

**Opis:** Dodaj złożone klucze obce dla item_id/user_id i assessment_id/user_id, aby treść, zadania, cytaty i czat należały do tego samego użytkownika co rodzic.

**Gotowe, gdy:** Baza odrzuca zapis dziecka z user_id innego właściciela; poprawny zapis i kasowanie kaskadowe działają.

**Sprawdzenie:** Transakcyjny test SQL na dwóch użytkownikach; po teście rollback.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

#### C1.2 — Uprawnienia RLS i RPC

**Status:** Planned · **Zależności:** C1.1

**Opis:** Rozdziel odczyty użytkownika i operacje serwerowe. Zablokuj bezpośrednie tworzenie ocen, przejmowanie zadań i zmiany budżetu przez role klienta.

**Gotowe, gdy:** anon/authenticated nie mogą wykonywać RPC serwerowych ani fałszować wyników; właściciel odczytuje wyłącznie swoje dane.

**Sprawdzenie:** Macierz testów SQL dla anon, authenticated A/B i service_role.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

#### C1.3 — Limit prób i bezpieczny lease

**Status:** Planned · **Zależności:** C1.2

**Opis:** Uzgodnij licznik prób w Pythonie i SQL. Pierwsza próba plus jeden retry; przejęcie zapisuje token i termin ważności.

**Gotowe, gdy:** Zadanie nie przekracza dwóch prób; drugi claimant nie dostaje aktywnego lease, a wyczerpane zadanie kończy się failed.

**Sprawdzenie:** Testy granic prób, dwóch claimantów i wygasłego lease z kontrolowanym czasem.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

#### C1.4 — Usuwanie po 30 dniach

**Status:** Planned · **Zależności:** C1.1, C1.2

**Opis:** Dodaj ograniczony cleanup RPC kasujący wygasłe items i wszystkie zależne dane. Uwzględnij queued, processing, completed, failed i manual-content.

**Gotowe, gdy:** Dokładna granica expires_at jest egzekwowana; niewygasłe rekordy pozostają; cleanup nie zostawia osieroconych danych.

**Sprawdzenie:** Test SQL z rekordami przed, na i po terminie; sprawdzenie wszystkich tabel podrzędnych.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

#### C1.5 — Repozytorium treści i ustawień

**Status:** Planned · **Zależności:** C1.1, C1.2

**Opis:** Rozszerz kontrakty aplikacji i adapter REST o zapis/odczyt treści, ustawień, usuwanie oraz read/unread. Zachowaj user_id w każdym wywołaniu.

**Gotowe, gdy:** Brak dostępu między użytkownikami; błędy i nieprawidłowe odpowiedzi dostawcy nie ujawniają sekretów ani danych.

**Sprawdzenie:** Mock HTTP dla każdej metody, ownership predicates, 404 i awarii dostawcy.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

### C2 — Pobieranie źródeł

**Pliki obszaru:** backend/src/linksifty/infrastructure/http_fetcher.py; backend/src/linksifty/domain/content_policy.py

#### C2.1 — Walidacja URL i DNS

**Status:** Done (mock DNS/transport + rzeczywisty transport z mock socket) · **Zależności:** brak

**Opis:** Akceptuj tylko HTTP/HTTPS bez danych logowania. Weryfikuj wszystkie adresy DNS i zabezpiecz rzeczywiste połączenie przed private IP oraz DNS rebinding.

**Gotowe, gdy:** Nie da się ominąć blokady przez localhost, IPv6, mieszane odpowiedzi DNS lub zmianę adresu między kontrolą i połączeniem.

**Sprawdzenie:** Mock resolver/transport; prywatne IPv4/IPv6, credential URL, rebinding i publiczny sukces.

- [x] Kod i przypadki błędów.
- [x] Testy/quality gates oraz evidence.md.
- [x] Zaktualizowany progress i kanban.

**Evidence 2026-10-13:** 38 testów fetchera; 73 testy backendu, strict mypy i Ruff pass. Wszystkie odpowiedzi DNS są sprawdzane, transport łączy się z przypiętym IP, Host/SNI zachowują nazwę, env proxies są wyłączone. Brak realnych fetch/provider calls; agent-toolkit gate nadal niedostępny.

#### C2.2 — Bezpieczne przekierowania

**Status:** Ready · **Zależności:** C2.1

**Opis:** Obsłuż przekierowania krok po kroku z walidacją każdego celu i skończonym limitem skoków.

**Gotowe, gdy:** Publiczny redirect działa; przekierowanie do private IP, niebezpiecznego schematu lub pętla kończą się kontrolowanym błędem.

**Sprawdzenie:** Mock HTTP: redirect względny, prywatny cel, pętla i przekroczenie limitu.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

#### C2.3 — Limity pobierania

**Status:** Planned · **Zależności:** C2.1

**Opis:** Pobieraj body strumieniowo z limitem bajtów, timeoutem i dozwolonymi typami treści; zakończ pobieranie po przekroczeniu limitu.

**Gotowe, gdy:** Nieograniczona odpowiedź lub PDF/video nie trafia do analizy; timeout ma jawny powód błędu.

**Sprawdzenie:** Mock stream: za duży body bez Content-Length, timeout, zły Content-Type i poprawny HTML.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

#### C2.4 — Ekstrakcja czytelnej treści

**Status:** Planned · **Zależności:** C2.3

**Opis:** Odfiltruj script/style i elementy nawigacji; normalizuj tekst oraz zachowaj stabilne pozycje do cytowania.

**Gotowe, gdy:** Tekst użyty do analizy nie zawiera kodu skryptów; identyczne wejście daje identyczny tekst i indeksy.

**Sprawdzenie:** Fixtures HTML: skrypty, style, encje, whitespace, błędne znaczniki i artykuł.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

#### C2.5 — Wspólny wynik i fallback

**Status:** Planned · **Zależności:** C2.2, C2.4

**Opis:** Ujednolić wynik pobrania z inputem paste i polityką kompletności. Paywall/login/script-only/partial wymagają ręcznego tekstu.

**Gotowe, gdy:** Niekompletne źródło ma awaiting_manual_content z powodem; żaden taki wynik nie wywołuje modelu.

**Sprawdzenie:** Testy kompletności oraz spy potwierdzający zero wywołań analizy przy błędzie.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

### C3 — Analiza i koszty

**Pliki obszaru:** backend/src/linksifty/application/assessment_service.py; backend/src/linksifty/infrastructure/openrouter_client.py; supabase/migrations/

#### C3.1 — Schemat odpowiedzi modelu

**Status:** Ready · **Zależności:** brak

**Opis:** Zdefiniuj ścisłe Pydantic DTO dla notatki, ośmiu kryteriów, źródeł i cytatów. Odrzuć brakujące/powtórzone kryteria i nieznane pola.

**Gotowe, gdy:** Model nie może zwrócić własnego verdict ani nieprawidłowego wyniku 1–5; draft spełnia pełny kontrakt.

**Sprawdzenie:** Przypadki poprawnego JSON, brakujących/powtórzonych kryteriów, złych typów i dodatkowych pól.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

#### C3.2 — Walidacja cytatów i claims

**Status:** Planned · **Zależności:** C3.1

**Opis:** Sprawdź source_id, indeksy start/end, zgodność excerpt z zapisaną treścią i powiązania ważnych claims z cytatami.

**Gotowe, gdy:** Nieistniejące źródło, indeks poza zakresem i zmyślony excerpt blokują zapis oceny.

**Sprawdzenie:** Testy poprawnego cytatu, Unicode/offsetów, fałszywego tekstu i claim bez dowodu.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

#### C3.3 — Adapter OpenRouter

**Status:** Planned · **Zależności:** C3.1

**Opis:** Dodaj serwerowe żądanie structured output z konfigurowanym modelem, limitem tokenów, timeoutem i mapowaniem błędów.

**Gotowe, gdy:** Klucz nie trafia do browsera/logów; zły JSON, odmowa modelu i timeout są jawne; brak realnych paid calls w testach.

**Sprawdzenie:** MockTransport: treść żądania, poprawny output, odmowa, 429/5xx, timeout i redakcja sekretów.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

#### C3.4 — Rezerwacja budżetu 10 USD

**Status:** Planned · **Zależności:** C1.2

**Opis:** Dodaj atomowe rezerwacje kosztu per użytkownik/miesiąc przed wywołaniem modelu, rozliczenie kosztu i identyfikator operacji.

**Gotowe, gdy:** Dwa równoległe żądania nie przekraczają limitu; timeout o nieznanym koszcie nie zwalnia automatycznie rezerwacji.

**Sprawdzenie:** Testy współbieżności w SQL oraz miesiąca/granicy limitu, idempotencji i niepewnej odpowiedzi.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

#### C3.5 — Pełny use case oceny

**Status:** Planned · **Zależności:** C2.5, C3.2, C3.3, C3.4

**Opis:** Połącz completeness → rezerwację → provider draft → walidację dowodów → czysty scorer. Snapshot progu pochodzi z bieżących ustawień.

**Gotowe, gdy:** Błąd przed modelem nic nie kosztuje; niepoprawny draft nie tworzy wyniku; późniejsze zmiany progu nie zmieniają historycznej oceny.

**Sprawdzenie:** Mock pełnej ścieżki, zero-call guard dla partial content i test niezmienności threshold_snapshot.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

### C4 — Wykonywanie zadań

**Pliki obszaru:** backend/src/linksifty/application/job_runner.py; backend/src/linksifty/domain/jobs.py; supabase/migrations/

#### C4.1 — Claim i zwolnienie zadania

**Status:** Planned · **Zależności:** C1.3

**Opis:** Dodaj adapter RPC do pobierania claimable jobs i kontrakt runnera z user_id, item_id, tokenem i zegarem.

**Gotowe, gdy:** Runner otrzymuje jedno własne zadanie; pusty wynik nie jest błędem; próby i lease są spójne.

**Sprawdzenie:** Mock REST i kontrakty pustej kolejki, innego user_id oraz wygasłego zadania.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

#### C4.2 — Zapisy chronione tokenem lease

**Status:** Planned · **Zależności:** C4.1

**Opis:** W każdym update/finalizacji wymagaj właściciela i aktualnego lease_token, aby stary proces nie zapisał wyniku.

**Gotowe, gdy:** Przeterminowany runner nie może nadpisać stanu nowego właściciela lease.

**Sprawdzenie:** SQL/mocked-contract test dwóch tokenów i stale worker write.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

#### C4.3 — Pipeline i atomowy wynik

**Status:** Planned · **Zależności:** C4.2, C3.5

**Opis:** Runner wykonuje acquisition i ocenę; wynik, cytaty i status zapisuje jedną transakcją.

**Gotowe, gdy:** Nie ma completed bez pełnej oceny i cytatów; failed fetch tworzy tylko prośbę o treść.

**Sprawdzenie:** Integracja na fake adapters oraz test rollbacku przy nieudanym zapisie cytatu.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

#### C4.4 — Retry i wznowienie po przerwaniu

**Status:** Planned · **Zależności:** C4.3

**Opis:** Obsłuż chwilowy błąd, restart, utratę lease i niejednoznaczny wynik płatnego wywołania.

**Gotowe, gdy:** Wznowienie nie wykonuje ślepo drugiego płatnego żądania; po wyczerpaniu prób stan failed ma czytelny powód.

**Sprawdzenie:** Symulacje crash przed/po provider call, timeout, wygasły lease i drugie niepowodzenie.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

#### C4.5 — Ograniczony trigger w API

**Status:** Planned · **Zależności:** C4.4, C1.4

**Opis:** Po uwierzytelnionym wejściu uruchom kontrolowany drain maksymalnie dwóch jobs i ograniczone cleanup.

**Gotowe, gdy:** Response nie czeka na cały pipeline; brak mnożenia runnerów dla jednego procesu; status pochodzi z bazy.

**Sprawdzenie:** Testy wielu requestów, limitu dwóch jobs, anulowania procesu i prawdziwego statusu.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

### C5 — Endpointy produktu

**Pliki obszaru:** backend/src/linksifty/api/routes/; backend/src/linksifty/api/schemas.py; backend/src/linksifty/application/item_service.py

#### C5.1 — Kontrakty i batch fetch/paste

**Status:** Planned · **Zależności:** C1.5

**Opis:** Wyodrębnij schemas/routes z main.py; rozszerz submission do fetch lub pasted text per źródło i jasnych błędów wejścia.

**Gotowe, gdy:** 1–5 źródeł, wymagane dane dla każdego trybu i udokumentowany wynik częściowo poprawnej paczki.

**Sprawdzenie:** HTTP contract tests: puste wejście, szóste źródło, brak treści i mieszana paczka.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

#### C5.2 — Decyzja dla duplikatu

**Status:** Planned · **Zależności:** C5.1

**Opis:** Normalizuj URL i zapytaj użytkownika o akcję przy już istniejącym linku; zapisz wybraną decyzję jawnie.

**Gotowe, gdy:** Duplikat nie uruchamia po cichu nowej analizy ani nie nadpisuje istniejącego wyniku.

**Sprawdzenie:** HTTP test konfliktu 409 i ponowienia z poprawną/niepoprawną decyzją.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

#### C5.3 — Ręczne wklejenie treści

**Status:** Planned · **Zależności:** C5.1, C4.2

**Opis:** Dodaj endpoint content replacement dla awaiting_manual_content i bezpieczne ponowne kolejkowanie własnego item.

**Gotowe, gdy:** Własna poprawna treść wraca do queued; obcy item 404; zbyt krótki tekst nie uruchamia analizy.

**Sprawdzenie:** Testy ownership, walidacji treści i atomowej zmiany content/job/item.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

#### C5.4 — Inbox, read/unread i delete

**Status:** Planned · **Zależności:** C1.5

**Opis:** Dodaj paginację, verdict filter, sort unread/score, zmianę przeczytania i potwierdzane kasowanie.

**Gotowe, gdy:** Po submit stare items pozostają; sortowanie/filter działa; niepotwierdzone i obce kasowanie nie usuwa danych.

**Sprawdzenie:** Testy kolejności, granic strony, filtrowania, read/unread, 404 i delete confirmation.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

#### C5.5 — Settings i status budżetu

**Status:** Planned · **Zależności:** C1.5, C3.4

**Opis:** Dodaj zapis progu dla przyszłych ocen i odczyt wydatków/rezerwacji miesięcznych; expose detail ocen/cytatów.

**Gotowe, gdy:** Próg ma dopuszczalny zakres, historyczne verdicts pozostają; queued item nie udaje gotowej oceny.

**Sprawdzenie:** HTTP test progu/ownership, budget DTO oraz complete/manual/queued detail.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

### C6 — Pełny frontend

**Pliki obszaru:** frontend/src/lib/; frontend/src/features/; frontend/tests/

#### C6.1 — Testy UI i klient API

**Status:** Ready · **Zależności:** brak; użyj mock contracts

**Opis:** Dodaj runner testów UI i typowany klient HTTP z walidacją odpowiedzi; uporządkuj App.tsx w małe ekrany.

**Gotowe, gdy:** Niepoprawna odpowiedź API ma kontrolowany błąd; nawigacja Inbox/Add/Settings pozostaje działająca.

**Sprawdzenie:** Test renderowania, mocked fetch sukces/błąd oraz production build.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

#### C6.2 — Login i sesja użytkownika

**Status:** Planned · **Zależności:** C6.1

**Opis:** Dodaj logowanie Google OAuth przez Supabase (wybór użytkownika 2026-10-14), przywrócenie sesji, token w API requestach, wylogowanie i obsługę wygaśnięcia. Konfiguracja: docs/deployment/setup.md, sekcja 3.4. Zachowaj wyłączony public signup i dostęp wyłącznie dla wcześniej utworzonego użytkownika.

**Gotowe, gdy:** Bez sesji nie pobieramy prywatnych danych; 401 wraca do loginu; dane poprzedniej sesji są czyszczone.

**Sprawdzenie:** Mock auth: restore, refresh, expiry, logout i brak prywatnych danych po wylogowaniu.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

#### C6.3 — Add i odzyskanie submission

**Status:** Planned · **Zależności:** C6.2, C5.1, C5.2

**Opis:** Wprowadź fetch/paste per źródło, walidację i wybór dla duplikatu. Zablokuj powtórny submit i zachowaj input przy błędzie.

**Gotowe, gdy:** Nie znika wpisany tekst po 503; jedna akcja wysyła jeden request; sukces odświeża cały Inbox.

**Sprawdzenie:** Testy szóstej pozycji, błędu, pending/double-click, duplikatu i pełnej listy po sukcesie.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

#### C6.4 — Inbox/detail i zarządzanie

**Status:** Planned · **Zależności:** C6.2, C5.3, C5.4, C5.5

**Opis:** Zbuduj filtry, item detail z kryteriami/cytatami, recovery paste oraz read/delete actions.

**Gotowe, gdy:** Oddziel complete/manual/queued; tekst plus kolor; delete ma potwierdzenie; recovery uruchamia poprawny flow.

**Sprawdzenie:** Mock UI test stanów, filtra, cytatów, read/unread, odmowy delete i wklejenia treści.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

#### C6.5 — Settings i dostępność

**Status:** Planned · **Zależności:** C6.2, C5.5

**Opis:** Podłącz persisted settings/budget, dodaj loading/error/empty/retry oraz mobile, focus i accessible names dla ekranów.

**Gotowe, gdy:** Próg opisany jako przyszły; klawiatura obsługuje cały flow; mobilny układ nie obcina formularzy/statusów.

**Sprawdzenie:** Test focus/nazw/disabled, save failure/retry i ręczny viewport/keyboard check.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

### C7 — Chat, X i dodatkowe źródła

**Pliki obszaru:** backend/src/linksifty/application/chat_service.py; backend/src/linksifty/infrastructure/x_adapter.py; frontend/src/features/chat/

#### C7.1 — Oficjalny adapter X

**Status:** Done (local implementation; hosted X access remains external) · **Zależności:** C2.5

**Opis:** Obsłuż URL post/thread przez oficjalne X API i wspólny SourceResult, bez generycznego scrapingu X.

**Gotowe, gdy:** Brak uprawnień/planu ma jawny manual fallback; testy używają mocka bez klucza.

**Sprawdzenie:** Mock odpowiedzi X: sukces, usunięty post, 401/403/429 i niepełna treść.

- [x] Kod i przypadki błędów.
- [x] Mock/SQL/UI tests and evidence.md; unavailable toolkit/browser gates documented.
- [x] Updated progress and derived boards.

Local implementation and boundaries: [canonical progress](../../../.agent/context/changes/x-ingestion/progress.md). Migration 000012 and explicit operator enablement required.

#### C7.2 — Sprawdzenie do pięciu źródeł

**Status:** Planned · **Zależności:** C2.5, C3.2

**Opis:** Pobierz najwyżej pięć cytowanych źródeł, deduplikuj reposty i zachowaj excerpt/pozycję/source_id.

**Gotowe, gdy:** Szóste źródło nie jest pobierane; niedostępne źródło nie jest liczone jako potwierdzenie.

**Sprawdzenie:** Test limitu, duplikatów, zablokowanego źródła i zgodności cytatów.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

#### C7.3 — Use case grounded chat

**Status:** Done (local implementation; hosted quality acceptance remains) · **Zależności:** C3.3, C3.4, C3.2

**Opis:** Answer analysis/topic questions using saved evidence; search only for missing evidence, once per question. Cite exact supplied passages, decline unsupported claims and ignore source instructions.

**Gotowe, gdy:** Nie ma odpowiedzi o obcym/niedokończonym item; każda claim ma prawidłowy citation_id; chat używa wspólnego cap.

**Sprawdzenie:** Mock provider: unsupported pytanie, injection w source, fabricated IDs i budget rejection.

- [x] Kod i przypadki błędów.
- [x] Testy/quality gates oraz evidence.md.
- [x] Zaktualizowany progress i kanban.

**Evidence 2026-10-18:** [Chat progress](../../../.agent/context/changes/analysis-chat/progress.md); 283 backend / 57 frontend tests, chat SQL/RLS and concurrency gates. Migration 000013; unavailable toolkit/browser and hosted acceptance remain separate.

#### C7.4 — API i historia rozmowy

**Status:** Done (local implementation; hosted quality acceptance remains) · **Zależności:** C7.3, C5.5

**Opis:** Dodaj item-scoped chat endpoints, zapis wiadomości i walidację błędów; wiadomości wygasają z item.

**Gotowe, gdy:** Każdy read/write wymaga właściciela; niepowodzenie providera nie zapisuje zmyślonej odpowiedzi.

**Sprawdzenie:** HTTP test owner, incomplete item, historia i rollback/awaria.

- [x] Kod i przypadki błędów.
- [x] Testy/quality gates oraz evidence.md.
- [x] Zaktualizowany progress i kanban.

**Evidence 2026-10-18:** [Chat progress](../../../.agent/context/changes/analysis-chat/progress.md); 283 backend / 57 frontend tests, chat SQL/RLS and concurrency gates. Migration 000013; unavailable toolkit/browser and hosted acceptance remain separate.

#### C7.5 — UI czatu z cytatami

**Status:** Done (local implementation; hosted quality acceptance remains) · **Zależności:** C7.4, C6.4

**Opis:** Dodaj chat na detail, pending message, retry błędu oraz linki do cytowanych excerptów.

**Gotowe, gdy:** Nie gubimy pytania przy błędzie; brak double-send; unsupported answer ma zrozumiałą odmowę.

**Sprawdzenie:** Frontend mocked chat: pending/success/refusal/error, keyboard i cytaty.

- [x] Kod i przypadki błędów.
- [x] Testy/quality gates oraz evidence.md.
- [x] Zaktualizowany progress i kanban.

**Evidence 2026-10-18:** [Chat progress](../../../.agent/context/changes/analysis-chat/progress.md); 283 backend / 57 frontend tests, chat SQL/RLS and concurrency gates. Migration 000013; unavailable toolkit/browser and hosted acceptance remain separate.

### C8 — Jakość i wydanie

**Pliki obszaru:**  .github/workflows/ci.yml; docs/deployment/; docs/release/

#### C8.1 — CI dla obu pakietów

**Status:** Done (lokalnie i GitHub CI zweryfikowane 2026-10-14) · **Zależności:** istniejące lokalne komendy; test UI dołącz po C6.1

**Opis:** Dodaj jobs Python tests/strict mypy/Ruff oraz frontend test/build z lockfiles; sprawdzaj tylko właściwe foldery produktu.

**Gotowe, gdy:** Pipeline odtwarza komendy lokalne i nie ignoruje failed gates; brak wymagania realnych paid integrations.

**Sprawdzenie:** Walidacja workflow i lokalne wykonanie tych samych komend.

- [x] Kod i przypadki błędów.
- [x] Testy/quality gates oraz evidence.md.
- [x] Zaktualizowany progress i kanban.

**Evidence 2026-10-13:** `.github/workflows/ci.yml`, locked installs, 37 backend tests, strict mypy/Ruff, frontend lint/build, walidacja YAML i propagacja błędu testu. Frontend behavior tests czekają na C6.1; `agent-toolkit check` nie działa bez runtime. GitHub CI run 38480767728 pass na commicie 397a769; container build/smoke również pass.

#### C8.2 — Logi i redakcja danych

**Status:** Planned · **Zależności:** C4.5

**Opis:** Dodaj request/item/job correlation, statusy i koszty; usuń tokeny, sekrety i source bodies z logów.

**Gotowe, gdy:** Błędy auth/provider nie ujawniają credentials ani treści; da się prześledzić job po ID.

**Sprawdzenie:** Test captured logs z kontrolowanymi znacznikami sekretów/source i sprawdzeniem ich braku.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

#### C8.3 — Artefakty wdrożeniowe

**Status:** Planned · **Zależności:** C6.2, C4.5

**Opis:** Opisz i skonfiguruj build/start, frontend API URL, backend CORS/env, migrations, cleanup i free-tier wake.

**Gotowe, gdy:** Repo ma kompletne instrukcje dla Vercel/Render/Supabase bez prawdziwych sekretów; demo domyślnie off.

**Sprawdzenie:** Sprawdzenie configów i smoke local health; hosted deploy pozostaje zadaniem Filip.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

**Docker slice — user-authorized 2026-10-14:** Replace native-Python hosting instructions with a root Dockerfile for the existing Render backend. Use Python 3.11 + uv 0.12.17, install only locked production dependencies, run non-root, honor PORT and keep secrets outside the build context. Add a CI image build and health/auth smoke check. Vercel remains frontend-only. C8.3 stays Planned as an epic subtask until its remaining runner/login/deployment acceptance is met; this slice does not claim live readiness.

**Slice checks:** Docker build + non-default PORT /health + anonymous 401 + UID 10001; standard backend gates; updated editable deployment diagram/HTML. Local Docker runtime unavailable, so use GitHub Actions after the already-authorized repository push. Record any unavailable gate honestly.

#### C8.4 — Regresja pełnego flow

**Status:** Planned · **Zależności:** C4.5, C6.5, C7.5

**Opis:** Sprawdź mock workflow login → submit → job → result/manual → detail/chat → delete/expiry.

**Gotowe, gdy:** Utrata procesu i provider error nie łamią prywatności, kosztów ani prawdziwego statusu.

**Sprawdzenie:** Integracyjne testy restart/fallback, frontend behavior, quality gates; zapisz ograniczenia środowiska.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

#### C8.5 — Audit i ocena 20 linków

**Status:** Planned · **Zależności:** C8.4

**Opis:** Zmapuj PRD na evidence, popraw statusy i przygotuj arkusz 20-link evaluation; sprawdź brak niezrealizowanych wymagań.

**Gotowe, gdy:** Kod można uznać za gotowy dopiero przy pełnych testach; live release wymaga minimum 12/20 akceptowanych ocen i wszystkich 20 zakończonych wyników/fallback.

**Sprawdzenie:** Checklist evidence dla PRD + szablon oceny; realne linki i produkcyjne RLS w E1.

- [ ] Kod i przypadki błędów.
- [ ] Testy/quality gates oraz evidence.md.
- [ ] Zaktualizowany progress i kanban.

### Podział E1 — konfiguracja zewnętrzna (właściciel: Filip)

- **E1.1 Supabase:** utworzenie projektu/Auth, zastosowanie gotowych migracji, konfiguracja backend env oraz test dwóch użytkowników/RLS. Zależy od C1 i C8.3.
- **E1.2 X/OpenRouter:** dostęp do oficjalnego X API, wybór modelu, klucze serwerowe i próba na kontrolowanym budżecie. Zależy od C3 i C7.
- **E1.3 Hosting i live acceptance:** Vercel/Render, frontend origin/session config, smoke po cold start, cleanup i 20-link evaluation. Zależy od C8 oraz E1.1/E1.2.

E1.1–E1.3 są oczekującą aktywacją, a nie blokadą implementacji na mockach. Brak lokalnego PostgreSQL lub agent-toolkit może zablokować konkretny gate weryfikacji; należy go zapisać zamiast oznaczać test jako zaliczony.

## E1 — External activation gate (Blocked; owner: Filip)

Configure Supabase/Auth and apply migrations; supply X API access and an OpenRouter model/key; deploy Vercel/Render and run two-user RLS plus 20-link acceptance checks. The 10 USD cap, 30-day retention and free-tier wake behavior must be verified in the deployed flow. This blocks live release verification, not C1–C8 coding.

