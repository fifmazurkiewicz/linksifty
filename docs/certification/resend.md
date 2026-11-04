# Linksifty — konfiguracja i sprawdzenie Resend

## Co już działa w kodzie

Integracja istnieje w `backend/src/linksifty/infrastructure/resend_client.py`, a aplikacja uruchamia ją, gdy ma jednocześnie `RESEND_API_KEY` i `RESEND_FROM_EMAIL`. Obecnie służy do jednego powiadomienia: zatwierdzenia konta przez administratora. Nie jest mechanizmem logowania Google ani wiadomością wysyłaną po każdej analizie lub rejestracji.

Weryfikacja 4 listopada 2026: testy Resend oraz obsługi zatwierdzania kont przeszły w pełnym zestawie backendu. Sprawdzają żądanie wysyłki, stały klucz idempotencji, bezpieczne błędy, timeout i nieprawidłową odpowiedź. Awaria maila nie cofa zatwierdzenia konta. Administrator może ponowić nieudaną wysyłkę.

Nie sprawdzono panelu Resend, ustawień Render, rekordów DNS ani rzeczywistej dostawy. Stan produkcyjny: **niepotwierdzony**. Nie odczytywano prawdziwych kluczy i nie wysyłano wiadomości.

## Co masz ustawić

1. Otwórz [Resend → Domains](https://resend.com/domains). Dodaj domenę nadawczą. Możesz użyć osobnej subdomeny, np. `mail.fmazurkiewicz.dev`; to propozycja, nie istniejąca konfiguracja.
2. W panelu dostawcy DNS dodaj dokładnie rekordy pokazane przez Resend dla wybranej domeny i regionu. Nie przepisuj przykładowych wartości z internetu. Poczekaj, aż domena uzyska status **Verified**. Nie zmieniaj rekordów obsługujących obecną stronę lub skrzynkę, jeśli panel Resend tego nie wymaga.
3. Otwórz [Resend → API Keys](https://resend.com/api-keys), utwórz klucz np. `linksifty-production`, wybierz **Sending access** i ogranicz go do wybranej domeny. Zapisz go bezpośrednio w ustawieniach serwera; nie wklejaj do chatu ani repozytorium.
4. Na **Render → usługa backendu Linksifty → Environment** ustaw:

| Zmienna | Wartość |
| --- | --- |
| `RESEND_API_KEY` | Nowy klucz z Resend |
| `RESEND_FROM_EMAIL` | Np. `Linksifty <noreply@mail.fmazurkiewicz.dev>`, jeśli zweryfikowałeś właśnie `mail.fmazurkiewicz.dev` |
| `FRONTEND_ORIGIN` | `https://linksifty.fmazurkiewicz.dev` |
| `LINKSIFTY_ADMIN_EMAIL` | Twój zweryfikowany adres Google używany przez administratora |

5. Zapisz zmiany i wykonaj ponowne wdrożenie/restart backendu, żeby odczytał nowe ustawienia. Klucz nie trafia do Vercel ani do zmiennych `VITE_`.

Dokumentacja dostawcy: [weryfikacja domeny](https://resend.com/docs/dashboard/domains/introduction), [uprawnienia kluczy API](https://resend.com/changelog/new-api-key-permissions).

## Jak potwierdzić działanie

1. Zaloguj własne dodatkowe konto testowe, które jeszcze oczekuje na zatwierdzenie. Samo korzystanie z darmowej próby nie wyzwala maila.
2. Z konta administratora zatwierdź to konto. To rzeczywista zmiana uprawnień i wysłanie wiadomości na kontrolowany przez Ciebie adres.
3. Sprawdź status powiadomienia w panelu administratora i wiadomość w Resend → Emails. Odpowiedź aplikacji `sent` oznacza przyjęcie przez API Resend, a nie gwarancję doręczenia do skrzynki.
4. Sprawdź zdarzenie dostarczenia w Resend oraz folder odebrane/spam adresata.
5. Jeśli wcześniejsza próba zakończyła się błędem, po naprawie konfiguracji użyj przycisku ponowienia w panelu administratora. Nie odrzucaj i nie zatwierdzaj ponownie konta tylko po to, by wymusić kolejny mail.

| Objaw | Co sprawdzić |
| --- | --- |
| `not_configured` | Czy obie zmienne Resend są ustawione na backendzie i czy wykonano restart |
| `provider_rejected` | Domenę Verified, zgodność nadawcy, zakres klucza i szczegóły błędu w panelu Resend |
| `timeout` / `unavailable` | Dostępność Resend i sieci; przed ponowieniem sprawdź, czy dostawca przyjął poprzednią wiadomość |
| `sent`, ale brak maila | Status delivered/bounced w Resend, adres odbiorcy i spam |
| Brak maila po rejestracji | Obecny kod wysyła wiadomość po zatwierdzeniu przez administratora, nie po samej rejestracji |

Logowanie Supabase/Google nie wymaga konfigurowania Resend jako SMTP dla tej funkcji. Ewentualne maile uwierzytelniające Supabase to osobna konfiguracja.
