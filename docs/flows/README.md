# Przepływy użytkownika i przetwarzania

Stan implementacji: 2026-10-22. [Architektura](../architecture/overview.md) ·
[Diagram analizy](../diagrams/processing.html) · [Diagram systemu](../diagrams/system.html).

## 1. Logowanie, próba i zatwierdzenie konta

1. Przeglądarka rozpoczyna Google OAuth przez Supabase i wraca na swój origin.
   Supabase odtwarza sesję; frontend przekazuje access token do API.
2. API weryfikuje token oraz potwierdzony email. Brak/odrzucenie tokenu daje `401`,
   niedostępność usługi uwierzytelniania `503`.
3. `GET /v1/me` zapewnia profil i zwraca status `pending`, `approved` lub `rejected`.
   Nowy użytkownik oczekuje na decyzję i może zgłosić trzy linki próbne.
   Odrzucone konto nie może korzystać z prywatnych funkcji.
4. Zweryfikowany adres zgodny z `LINKSIFTY_ADMIN_EMAIL` daje uprawnienia admina.
   Administrator zatwierdza/odrzuca konta i zmienia limity, bez wglądu w cudzą treść.
5. Po zatwierdzeniu transakcji statusu opcjonalny Resend wysyła powiadomienie.
   Błąd emaila nie cofa zatwierdzenia; osobna akcja pozwala ponowić wysyłkę.
6. Wylogowanie lub wygaśnięcie sesji usuwa prywatny stan UI i przerywa strumień
   poprzedniego użytkownika. Licznik Admin pokazuje oczekujące konta i znika dla zera
   albo niedostępnego wyniku.

Źródła: [AuthProvider](../../frontend/src/auth/AuthProvider.tsx),
[auth](../../backend/src/linksifty/api/auth.py),
[AccountService](../../backend/src/linksifty/application/account_contracts.py),
[admin API](../../backend/src/linksifty/api/admin.py).

## 2. Dodanie linku i pełna analiza

1. Add wysyła 1–5 URL-i do `POST /v1/items`. Opcjonalne `web_search` oznacza zgodę
   na dodatkowy research. `allow_partial_preview` zapisuje dopuszczenie kosztu
   podglądu przy niepełnej treści; starszy klient bez pola domyślnie go nie włącza.
2. Transakcja sprawdza dostęp, próbę i duplikaty w obrębie właściciela, tworzy
   element oraz zadanie. API zwraca `202`, a istniejący lub powtórzony link `409`.
   `202` oznacza przyjęcie pracy, nie gotową ocenę.
3. Runner przejmuje lease zadania. Pobiera publiczną stronę lub tekst z X.
   Każde przekierowanie i adres podlega kontroli; niekompletny lub niedostępny
   materiał przechodzi do ścieżki ręcznego wklejenia opisanej niżej.
4. Kompletny tekst zostaje zapisany. Media są pomijane, a znane typy mediów
   pozostają informacją o ograniczeniu zakresu.
5. Jeśli zgoda i konfiguracja pozwalają, research wykonuje jedno wyszukiwanie
   Brave, osobno rezerwuje Jev do wyboru trafnych kandydatów, a następnie pobiera
   do 20 wybranych stron. Błąd selekcji nie uruchamia pobierania wszystkich
   wyników; analiza może pozostać oparta wyłącznie na źródle głównym.
6. Przed wywołaniem modelu baza atomowo rezerwuje konserwatywny maksymalny koszt
   i utrwala próg oraz rubric. OpenRouter otrzymuje oznaczone fragmenty tekstu.
7. Model zwraca notatkę, temat i ocenę kryteriów, wskazując ID fragmentów.
   Backend odtwarza oryginalny cytat i jego źródło oraz waliduje wynik. Wygenerowany
   tytuł może zostać zachowany również wtedy, gdy walidacja pełnej analizy zawiedzie.
8. Potwierdzony koszt jest rozliczany. Czysta funkcja domenowa liczy wynik i werdykt.
   Zapis oceny, cytatów i zakończenia odbywa się z kontrolą aktualnego lease.
9. Kolejka odbiera snapshoty SSE. Detail pokazuje notatkę, wynik, zakres oceny,
   cytaty, źródła i powód werdyktu; może rozpocząć chat.

[ProcessingService](../../backend/src/linksifty/application/processing_service.py)
i [ProcessingRepository](../../backend/src/linksifty/infrastructure/processing_repository.py)
są główną ścieżką runtime. Wklejony nowy tekst używa `POST /v1/items/paste`
i pomija pobranie URL oraz research źródła.

## 3. Brak treści, podgląd i Retry

Nieudane, zbyt krótkie, zablokowane lub częściowe pobranie prowadzi do
`awaiting_manual_content`. **Nie tworzy oceny ani punktacji** i nie zapisuje
częściowego tekstu jako kompletnego wejścia analizy.

Jeśli wcześniej dopuszczono podgląd, istnieje czytelny fragment i budżet pozwala,
jednorazowo przyjęte wywołanie może wygenerować jednozdaniowy `Partial preview`.
Podgląd zużywa budżet AI, nie odblokowuje analizy i nadal wymaga pełnej treści.
Nieznana opłata pozostaje widoczna jako oczekująca.

Użytkownik ma dwie ścieżki:

- **Paste content:** `PUT /v1/items/{id}/content` uzupełnia ten sam element.
  API wymaga co najmniej 200 znaków czytelnego tekstu i maksymalnie 100 KB UTF-8.
- **Retry:** `POST /v1/items/{id}/resume` ponownie pobiera źródło na tym samym
  elemencie i może rozpocząć analizę. Interfejs ujawnia użycie budżetu oraz
  możliwe osobne opłaty X. Niepewne wywołania/opłaty blokują niebezpieczne ponowienie.

Brak kompletnego tekstu nie jest dowodem niskiej wartości materiału.
Źródła: [processing API](../../backend/src/linksifty/api/processing.py),
[migracja podglądów](../../supabase/migrations/20261019_000021_partial_previews.sql),
[migracja Retry](../../supabase/migrations/20261018_000014_retry_fetch.sql).

## 4. Wynik i werdykt

Dla ocenionych kryteriów wynik to `100 × Σ(score × weight) / (5 × Σ(weight))`,
zaokrąglony do dwóch miejsc. Kryteria `not_applicable` i `not_verified` nie
udają wyniku zero. Brak ocenianych kryteriów daje `score = null`.

W aktualnym rubric v2 udokumentowane fragmentami sygnały przesady dają `hype`.
Brak lub słaba ocena kluczowych kryteriów (dowody, wiarygodność, praktyczność,
konkretność; wynik ≤2) wymaga `to_review`. `valuable` wymaga spełnienia progu
oraz wystarczająco ocenionych kluczowych kryteriów. Niski wynik sam nie dowodzi hype.

Ustawienia zmieniają przyszłe analizy: próg 40–100, opisy ośmiu kryteriów i wagi
całkowite 1–10. Zapisane oraz przerwane analizy zachowują snapshot zasad.
Historyczny rubric v1 ma inne reguły i nie jest automatycznie przeliczany.
Źródła: [scoring](../../backend/src/linksifty/domain/scoring.py),
[rubric](../../backend/src/linksifty/domain/rubric.py).

## 5. Chat o analizie i temacie

1. Detail odczytuje zapisaną rozmowę. Pytanie wysyła unikalny request ID,
   treść i limit researchu. Powtórzenie tego samego ID zwraca zapisany stan,
   bez uruchamiania kolejnego płatnego wykonania.
2. Pierwsze wywołanie OpenRouter to klasyfikator Jev. Pytania poza tematem
   lub niebezpieczne kończą się odmową bez researchu i modelu odpowiedzi.
   Niepewna klasyfikacja zatrzymuje flow; błędna odpowiedź klasyfikatora daje błąd.
3. Dla trafnego pytania model korzysta z analizy, oryginalnego tekstu, zapisanych
   źródeł i ostatniej rozmowy. Odpowiada w języku pytania (polski/angielski),
   a niejednoznaczny temat powinien doprecyzować.
4. Brak dowodów może uruchomić Brave i bezpieczne pobranie stron, jeśli usługa
   jest dostępna i wystarcza budżetu. Aktualny klient dopuszcza do dwóch różnych
   wyszukiwań na pytanie; brak pola w starszym kliencie oznacza limit jednego.
5. Drugie, doprecyzowane wyszukiwanie wymaga rozliczenia pierwszego. Cały flow
   obejmuje do trzech wywołań modelu odpowiedzi oraz klasyfikację. Każde płatne
   miejsce ma własną jednorazową rezerwację. Niepewne wyniki nie są ponawiane.
6. Zapisana odpowiedź zawiera cytowania do dostępnych fragmentów albo uczciwą
   informację o brakujących dowodach. Brak Brave pozwala korzystać z zapisanej treści.

Źródła: [ChatService](../../backend/src/linksifty/application/chat_service.py),
[chat API](../../backend/src/linksifty/api/chat.py),
[migracja 000022](../../supabase/migrations/20261020_000022_chat_research.sql).

## 6. Komentarze czytelników i usuwanie

Komentarze z X są pobierane na jawne żądanie, z osobnym przyjęciem operacji.
Nie są dowodami oceny i nie zmieniają score. Reddit może zostać rozpoznany,
ale odczyt jego komentarzy ma status `unsupported`.
Zobacz [DiscussionService](../../backend/src/linksifty/application/discussions.py).

Delete / Delete selected wymaga potwierdzenia i obsługuje do 50 unikalnych ID.
`POST /v1/items/delete` sprawdza własność całego zestawu, usuwa treść, analizy,
cytaty, rozmowy i zadania oraz blokuje spóźnione zapisy workerów. Zachowuje
rozliczenia, rezerwacje i zużytą próbę; usunięcie nie zwraca kosztu.
Źródła: [items API](../../backend/src/linksifty/api/items.py),
[migracja usuwania](../../supabase/migrations/20261017_000011_delete_items.sql).

## 7. Przerwanie i odzyskanie pracy

| Sytuacja | Działanie i widoczny skutek |
| --- | --- |
| Restart przed wywołaniem modelu | Po wygaśnięciu lease kolejna wizyta może przejąć zadanie |
| Zapisany wynik, przerwany końcowy zapis | Odzyskanie wyniku bez drugiego wywołania |
| Nieznany koszt, znane generation ID | Uzgodnienie przez lookup dostawcy i rozliczenie pierwotnej rezerwacji |
| Nieznany koszt bez ID | Rezerwacja pozostaje; wymagane sprawdzenie przez operatora |
| Przerwany SSE | Ponowne połączenie i świeży snapshot; status nie jest tracony |
| Nieprawidłowa struktura/cytaty | Jawny błąd analizy, bez wymyślonego wyniku; rzeczywisty koszt nadal podlega rozliczeniu |
| Brak budżetu | Brak nowego wywołania w danym płatnym kroku; zwiększenie limitu nie uzgadnia starych nieznanych opłat |

[Runbook](../deployment/README.md) opisuje diagnostykę i retencję. Nie należy
obchodzić blokady kosztów przez skasowanie rezerwacji lub zgłoszenie kopii linku.
