# Stan zadań po wznowieniu — 2026-10-15

Lista pochodna z `plan.md` i kanonicznego `progress.md`.

## Ukończone lokalnie

- [x] T1: implementacja migracji, precyzyjnych rozliczeń, ustawień i budżetów; testy adaptera/API i przygotowany pgTAP oraz runner równoległych rezerwacji.
- [x] T2: testy i poprawki recovery, późnego wyniku, osieroconych rezerwacji, utraty dzierżawy, zapisanej ceny i jawnego wznowienia bez powtarzania niepewnego płatnego requestu.
- [x] T2: zweryfikowany pełny bound kosztu dla modelu; nieznany model blokuje inference. Bez heurystyki bajt/token.
- [x] T2: bezpieczne pobieranie, także odrzucenie niespodziewanej kompresji i binarnej treści przed analizą.
- [x] T3: heartbeat i świeżość postępu, paused UI, SSE reconnect, owner scope, odrzucenie sesji/konta i czyszczenie danych poprzedniej sesji.
- [x] T4: szczegóły z ośmioma kryteriami/cytatami, wklejenie i wznowienie w testach komponentów; zapis progu i budżetu, zachowanie wcześniejszych linków po wysłaniu.
- [x] T5: 124 testy backendu, mypy, Ruff check/format, 19 testów frontendu, lint, build i diff check.
- [x] T5: README, setup/Supabase, architektura, retencja/recovery, diagram i roadmapa zaktualizowane.
- [x] T5: review implementacji i kanoniczne dispositions; cztery ustalenia poprawione, bramka bazy zamknięta, agent-toolkit pozostaje otwarty. Boardy zsynchronizowane.
- [x] T5: implementacja zapisana w `b82959b`; runtime/testy w kolejnym lokalnym commicie, bez push.

## Otwarte bramki lokalne — wymagane przed wydaniem

- [x] **T1 / REV-004:** lokalny PostgreSQL 17.11 + pgTAP 1.3.4 przygotowany za zgodą właściciela. Wszystkie pięć migracji, 57 asercji pgTAP (RLS na zasianych obcych danych, fencing, rollover, retencja, późne i osierocone wyniki) i rzeczywiste równoległe rezerwacje PASS. Wyłączenie guardu/RLS celowo powodowało FAIL; po przywróceniu PASS. Serwer zatrzymany. Hosted auth i konfiguracja nadal E1.
- [ ] **T5 / REV-005:** uruchomić wymagane `agent-toolkit check`, gdy istniejący runtime będzie dostępny. Obecnie command not found (127), nie PASS.
- [ ] **QA wizualne:** inspekcja bieżącego UI desktop/mobile i diagramu po przywróceniu dozwolonego browser/runtime. Narzędzie odrzuciło URL localhost; nie obchodzić blokady. Aktualne testy komponentów przeszły; historyczne screenshots nie zastępują nowego odbioru wizualnego.

## Nierozpoczęte — aktywacja docelowego środowiska (E1)

- [ ] Zastosować i zweryfikować migrację/RLS oraz włączyć `supabase/retention.sql` w uzgodnionym Supabase.
- [ ] Skonfigurować server-only model/klucz, wdrożyć backend/frontend i sprawdzić SSE/reconnect/cold start na docelowym hostingu.
- [ ] Przeprowadzić autoryzowany odbiór na rzeczywistych linkach: faktyczne USD, limit 0, wklejenie, recovery i retencja. Wymaga odrębnej zgody na płatne próby i wskazanego środowiska.

Nie archiwizować ani nie oznaczać wydania jako gotowego przy otwartych bramkach. Testy providerów pozostają mockowane; żadnych instalacji/aktywacji zewnętrznych nie wykonano.
