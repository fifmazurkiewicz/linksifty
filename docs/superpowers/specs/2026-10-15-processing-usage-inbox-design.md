# Linksifty: przetwarzanie, koszty USD i czytelna kolejka

Data: 2026-10-15. Status: zakres zaakceptowany; dokument do przeglądu właściciela przed planem implementacji.

## 1. Problem i kontekst

Użytkownik nie widzi aktualnych wydatków ani pracy wykonywanej po wysłaniu linku. Administrator nie może zmieniać limitów. Settings pokazuje stały próg bez możliwości zapisania zmiany. Inbox nie wyjaśnia swojej funkcji i wyświetla sprzeczne komunikaty.

Obecny backend zapisuje link i zadanie, ale nie uruchamia przetwarzania. Frontend dla każdego stanu poza `awaiting_manual_content` pokazuje gotową ocenę, a brak werdyktu zastępuje komunikatem „Paste content”. Po wysłaniu nowych linków zastępuje też listę wyłącznie nowo utworzonymi rekordami. Istnieją Google OAuth, reguły dostępu i panel zatwierdzania kont; istnieje czysta reguła punktacji. Dokładne rozliczanie kosztów wymaga rzeczywistych wywołań modelu.

Dokument rozwija etap drugi [wcześniejszej specyfikacji](2026-10-14-multi-user-access-admin-design.md) oraz istniejące M3–M5/M9. Nie oznacza uruchomienia opisanych funkcji na produkcji.

## 2. Cele i granice

Cele: rzeczywiste przetwarzanie bezpiecznie pozyskanej treści, widoczne etapy pracy, dokładny koszt OpenRouter przypisany użytkownikowi, egzekwowane limity admina, zapisywany próg oceny i zrozumiały dostęp do wyników.

Zakres obejmuje zwykłe strony WWW oraz ręczne wklejenie treści. Istniejące ograniczenie do pięciu linków i trzy linki próbne pozostają. X oraz inne nieobsługiwane formaty otrzymują jawne przejście do ręcznego wklejenia; ich dedykowane integracje, chat, poszukiwanie dodatkowych źródeł, płatności i redesign marki są poza tą zmianą. Nie ma osobnego płatnego workera.

## 3. Użytkownicy i przepływy

### Dodanie i analiza

1. Zalogowany użytkownik wysyła do pięciu linków. Dopiero trwały zapis potwierdza przyjęcie. Kolejka zachowuje także starsze linki.
2. Każdy link pokazuje etap i czas ostatniej aktualizacji: oczekiwanie, pobieranie strony, sprawdzanie treści, oczekiwanie na analizę, analiza, zapisywanie wyniku, gotowe.
3. Komunikat podaje domenę rzeczywiście pobieranej strony. „Analizuję informacje” pojawia się dopiero po uruchomieniu analizy. Nie ma symulowanej animacji etapów ani procentu bez pomiaru.
4. Niepełna lub niedostępna treść zatrzymuje proces przed analizą, z powodem i przyciskiem „Wklej treść”. Użytkownik może też wybrać wklejenie od razu. Pusta treść jest odrzucana.
5. Przed płatną analizą system sprawdza dostęp i rezerwuje budżet. Potwierdzeniem kosztowego działania jest świadome wysłanie linku lub treści, z widoczną informacją o wykorzystaniu miesięcznego budżetu; brak automatycznego płatnego ponowienia niepewnego wywołania.
6. Gotowy rekord otwiera zapisane podsumowanie, wynik, werdykt, osiem kryteriów z uzasadnieniem i powiązane fragmenty źródła. Dostępny wynik wymaga skutecznego zapisu całego zestawu.

### Budżet i administrator

Użytkownik widzi swój bieżący miesiąc: faktycznie wydano, zarezerwowano, miesięczny limit, pozostało i datę resetu. Podgląd jest w nawigacji oraz Settings. Administrator widzi te same dane dla kont i może świadomie zapisać nowy nieujemny limit USD, w tym zero. Nie uzyskuje dostępu do ich linków ani treści. Zmiana limitu nie wysyła wiadomości e-mail.

### Settings i kolejka

Settings udostępnia edytowalny próg 40–100%, domyślnie 60%, przycisk zapisu, potwierdzenie i błąd. Zmiana nie wpływa na zapisane oceny. Próg jest utrwalany przy rozpoczęciu danej analizy; wznowienie tej samej analizy zachowuje tę wartość.

Inbox staje się kolejką zapisanych linków. Krótki opis wyjaśnia: „Dodaj linki, obserwuj analizę i sprawdź, co warto przeczytać”. Widoki „Wszystkie”, „W trakcie”, „Wymaga działania” i „Gotowe” pokazują liczności. Domyślnie widoczne są wszystkie linki. Karta ma tytuł lub domenę, jednoznaczny stan, adekwatną akcję oraz wynik tylko po ukończeniu. Gotowe wyniki można filtrować po werdykcie. Pusty widok wyjaśnia, czy brakuje linków, czy tylko wyników dla filtra.

## 4. Wymagania funkcjonalne

| ID | Wymaganie |
| --- | --- |
| P01 | Etapy pochodzą z trwałego stanu zadania, są przypisane do właściciela i nie zależą od lokalnego timera UI. |
| P02 | Użytkownik otrzymuje aktualizacje w aktywnym widoku bez ręcznego odświeżania; zerwane połączenie nie kasuje zadania. |
| P03 | Wznowienie pokazuje zapisany etap i jawnie odróżnia aktywną pracę od oczekiwania lub przerwanej sesji. |
| P04 | Niekompletne pobranie nigdy nie uruchamia modelu ani nie tworzy podsumowania lub oceny. |
| P05 | Analiza korzysta wyłącznie z dostępnej treści; cytaty muszą odpowiadać rzeczywistym fragmentom, a punktacja pozostaje deterministyczna. |
| U01 | Każde płatne wywołanie ma jednoznaczne przypisanie użytkownika, rezerwację i rzeczywisty koszt albo jawnie nierozliczoną rezerwację. |
| U02 | Miesiąc rozliczeniowy jest kalendarzowym miesiącem UTC; domyślny limit wynosi 10 USD. |
| U03 | Warunek dopuszczenia wywołania: wydatki + aktywne rezerwacje + nowa rezerwacja nie przekraczają limitu. Sprawdzenie jest atomowe. |
| U04 | Kwoty zachowują dokładność poniżej centa; zaokrąglenie UI nie zmienia rozliczeń. UI nie ukrywa małego dodatniego kosztu jako 0 USD. |
| U05 | Pozostało = max(0, limit − wydatki − rezerwacje). UI rozróżnia potwierdzone zero od braku dostępnych danych. |
| U06 | Rozliczenie jest idempotentne. Koszt wyższy niż rezerwacja jest zapisany w całości i blokuje dalsze wydatki ponad limit. |
| U07 | Nieznany wynik, brak kosztu lub timeout po wysłaniu pozostawia rezerwację. Nie wolno ponownie płatnie wykonać tej samej próby bez rozstrzygnięcia jej wyniku. |
| U08 | Granica miesiąca nie usuwa poprzednich rezerwacji; wynik rozlicza miesiąc pierwotnej rezerwacji. |
| A01 | Tylko zweryfikowany administrator zmienia limit. Użytkownik nie może zmienić go przez API ani bezpośredni zapis w bazie. |
| A02 | Obniżenie limitu poniżej zużycia zachowuje historię i blokuje nowe rezerwacje; nie unieważnia już dopuszczonego wywołania. |
| S01 | Próg jest walidowany i trwale zapisany dla właściciela. Błąd zapisu nie jest prezentowany jako sukces. |
| I01 | Przyjęcie nowych linków nie usuwa starych z widoku. Stan queued/processing nigdy nie deklaruje gotowej oceny. |
| I02 | Formularz wklejenia i szczegóły są dostępne z odpowiedniej karty; niedostępny wynik nie ma pozornego przycisku otwarcia. |

## 5. Błędy i odzyskiwanie

- Paywall, logowanie, niedozwolony adres, przekroczony rozmiar, brak czytelnej treści i nieobsługiwany format pokazują bezpieczny powód oraz ręczne wklejenie. Nie są automatycznie ponawiane szerzej.
- Wyczerpany budżet oznacza „Wymaga działania”, z dostępną kwotą i datą resetu; po podniesieniu limitu lub resecie użytkownik może jawnie wznowić analizę. Nie trzeba ponownie pobierać już zapisanej kompletnej treści.
- Utrata dzierżawy blokuje zapis starego wykonawcy. Przejęcie zadania nie dubluje modelu ani rozliczenia. Rozstrzygnięcie niepewnego wywołania poprzedza jego wznowienie.
- Brak konfiguracji modelu i awaria infrastruktury są widoczne jako brak możliwości analizy, nigdy jako gotowy wynik. Ręczne wklejenie nie naprawia awarii dostawcy.
- Utrata połączenia z aktualizacjami pokazuje ostatni potwierdzony etap i komunikat o ponownym łączeniu. Odświeżenie odtwarza stan z serwera.
- Błędna odpowiedź modelu nie tworzy oceny. Jej rzeczywisty koszt jest nadal rozliczony; ewentualne ponowienie wymaga jawnej akcji i nowej rezerwacji.
- Wygaśnięcie sesji i wylogowanie zatrzymują odbiór prywatnych aktualizacji i czyszczą dane. Odrzucone konto nie ma dostępu do prywatnych operacji.

## 6. Ograniczenia i kierunek architektury

Zachowane są React/TypeScript/Vite, FastAPI/Pydantic v2, Supabase i istniejące granice domeny. Przetwarzanie jest ograniczonym wykonawcą w API; PostgreSQL zapewnia trwałość, dzierżawy i atomowość budżetu. Przeglądarka otrzymuje uwierzytelnione zdarzenia postępu oraz może odtworzyć stan po rozłączeniu. Preferowany jest strumień SSE przez autoryzowane żądanie, z odzyskiwaniem stanu; nie dokładamy brokera ani infrastruktury WebSocket. Konkretne kontrakty ustali plan po zweryfikowaniu zachowania hostingu.

Bezpieczeństwo pobierania obejmuje publiczny adres docelowy, walidację DNS i przekierowań, przypięte połączenie oraz ograniczenia czasu i rozmiaru. Istniejące samo sprawdzanie adresu nie wystarcza. Treści źródeł i modelu są niezaufane. Klucze pozostają na serwerze. Wszelkie rekordy, zdarzenia i cytaty są izolowane per właściciel, także dla admina.

Istniejąca polityka `settings owner` zezwala na zapis całego wiersza z limitem: wymaga ograniczenia uprawnień przed udostępnieniem egzekwowanych limitów. Użytkownik edytuje wyłącznie próg; budżet jest kontrolowany przez serwer/admina.

Zachowane są komponenty, kolory i typografia. UI ma semantyczne przyciski, etykiety, widoczny fokus, obsługę klawiatury, statusy live bez nadmiernych komunikatów i układ mobilny bez poziomego przewijania. Nie wprowadza się niepotrzebnego ruchu. Język produktu pozostaje spójny z istniejącym angielskim UI; polskie etykiety w tym dokumencie opisują znaczenie, nie nową lokalizację.

Treści zachowują obecny termin 30 dni; postęp nie zawiera treści i wygasa razem z linkiem. Proponowany okres przechowywania beztreściowego rejestru kosztów to 90 dni, obejmujący rozliczenie poprzednich miesięcy. Niepewne rezerwacje nie są kasowane przed wyjaśnieniem. Jest to jawna decyzja do zatwierdzenia z tym dokumentem.

## 7. Kryteria odbioru

1. Dwa wysłane linki pojawiają się obok istniejących; mockowany proces pokazuje kolejne rzeczywiste etapy, a przeładowanie zachowuje postęp. Każdy link ma niezależny stan.
2. Zablokowana i częściowa strona przechodzą do wklejenia bez wywołania modelu. Wklejona kompletna treść prowadzi do wyniku i poprawnych cytatów.
3. Użytkownik widzi koszt mniejszy niż cent, rezerwacje, limit, saldo i reset. Brak rozliczenia nie jest przedstawiany jako darmowe wywołanie.
4. Przy limicie 1 USD i dwóch równoczesnych rezerwacjach po 0,60 USD dopuszczona jest najwyżej jedna. Powtórne rozliczenie nie powiększa kosztu.
5. Admin zapisuje limit 0 USD; nowe wywołanie jest blokowane przed dostawcą. Zwykły użytkownik nie może zwiększyć limitu ani przez API, ani przez bezpośredni zapis w Supabase.
6. Próg 75% przetrwa przeładowanie; nowe analizy stosują 75%, istniejące zachowują zapisany próg i werdykt. Wartości poza 40–100 są odrzucane.
7. Filtry kolejki działają; gotowy wynik pokazuje notatkę, kryteria i fragmenty. Oczekujący link nie pokazuje „assessment is ready” ani przypadkowego „Paste content”.
8. Testy obejmują izolację właściciela dla zdarzeń, wyników, wklejenia i settings, odmowę uprawnień, zerwany strumień, utratę dzierżawy, timeout dostawcy, zmianę miesiąca i limit obniżony podczas pracy.
9. Wszystkie integracje w testach są mockowane. Wymagane bramki: backend tests, strict mypy, Ruff check/format, frontend tests/lint/build i `agent-toolkit check`. Brak runtime jest jawnym ograniczeniem, nie zaliczonym testem.
10. Oddzielna aktywacja na hostingu potwierdza migracje/RLS, rzeczywisty koszt i strumień postępu. Lokalne mocki nie są dowodem działania produkcji.

## 8. Zależności i decyzje wymagane przed implementacją

| Obszar | Odpowiedzialność / warunek |
| --- | --- |
| Kontrakt OpenRouter | Wykonawca: zweryfikować oficjalny kontrakt kosztu, identyfikatora wywołania, rozliczenia niepewnego wyniku i konserwatywnej rezerwacji dla skonfigurowanego modelu. |
| Model i ceny | Wykonawca: model konfigurowany na serwerze, ograniczony output i zweryfikowany maksymalny koszt przed wykonaniem. Brak bezpiecznej granicy kosztowej blokuje płatne wywołanie. |
| Streaming / Render | Wykonawca: zweryfikować przerwanie strumienia, cold start i wznowienie bez wymagania stale aktywnej karty. |
| Migracje i RLS | Wykonawca: ochrona ustawień i własności oraz testy rzeczywistego PostgreSQL przed wdrożeniem. |
| Retencja kosztów | Filip: akceptacja proponowanych 90 dni z wyjątkiem nierozliczonych rezerwacji w ramach przeglądu dokumentu. |
| Aktywacja i koszty zewnętrzne | Filip: migracje i konfiguracja usług po gotowym kodzie; prawdziwe płatne próby wymagają osobnej zgody. |

## 9. Rozważone podejścia i decyzja

Sama poprawa UI usunęłaby sprzeczne teksty, ale nie dostarczyłaby kosztów ani rzeczywistych etapów. Pełny worker z brokerem zwiększyłby liczbę usług i naruszył obecny model hostingu. Wybrano rozwinięcie istniejącego wykonawcy API i trwałego stanu Supabase, z uwierzytelnionym strumieniem postępu. Efektem ma być kompletny przepływ w zatwierdzonym zakresie, nie kolejna makieta.

## 10. Materiały i stan zatwierdzenia

- Zakres zaakceptowany w rozmowie 2026-10-15; akceptacja dotyczyła przygotowania tej specyfikacji.
- Dowody obecnego działania: `frontend/src/App.tsx`, `frontend/src/features/admin/AdminPanel.tsx`, `backend/src/linksifty/main.py`, `backend/src/linksifty/application/item_service.py`, `backend/src/linksifty/application/assessment_service.py`, `backend/src/linksifty/domain/scoring.py`, `supabase/migrations/20261012_000001_personal_mvp.sql`.
- [Docelowy cykl życia](../../../.agent/context/changes/processing-usage-inbox/lifecycle.html) i [edytowalny JSON](../../../.agent/context/changes/processing-usage-inbox/lifecycle.json). Diagram opisuje projekt, nie aktualnie wdrożony kod; stałe kontrolki przeglądarki diagramu pozostają po angielsku.
- Następny etap: przegląd i zatwierdzenie tego dokumentu, następnie techniczny plan implementacji. Nie zmieniono kodu produktu.
