# Linksifty — powiadomienie o pierwszym logowaniu

## Zachowanie

Po pierwszym logowaniu nowego użytkownika aplikacja zapisuje profil i jedno trwałe zdarzenie `account_requested`, a następnie próbuje wysłać przypomnienie do **fifmazurkiewicz@gmail.com**. Wiadomość zawiera adres nowego użytkownika i link do aplikacji. Nigdy nie jest wysyłana do nowego użytkownika. Konto właściciela nie generuje powiadomienia.

Odświeżanie strony i kolejne logowania nie tworzą kolejnych zdarzeń. Zatwierdzenie konta nadaje dostęp poza pulą trzech źródeł próbnych; nadal obowiązują miesięczne limity kosztów. Zatwierdzenie nie wyzwala maila. Błąd wysyłki nie blokuje logowania. Istniejące przed migracją profile nie są objęte wysyłką wsteczną.

## Konfiguracja na Render

Domena `fmazurkiewicz.dev` jest zweryfikowana według informacji właściciela.

```dotenv
RESEND_API_KEY=TU_WSTAW_KLUCZ_RESEND
RESEND_FROM_EMAIL=Linksifty <noreply@fmazurkiewicz.dev>
RESEND_ADMIN_EMAIL=fifmazurkiewicz@gmail.com
```

Klucz pozostaje wyłącznie na backendzie. `LINKSIFTY_ADMIN_EMAIL` nadal określa konto administratora; odbiorca maila nie nadaje uprawnień. Po zmianie ustawień wykonaj ponowne wdrożenie API.

Kolejność rollout: migracja `supabase/migrations/20261104_000023_first_login_notification.sql` → pasujący backend → frontend z etykietą **New account email**. Stary backend nie wysyła nowego rodzaju zdarzeń. Zachowano historyczne nazwy pól `approval_email_*` i adres endpointu retry dla kompatybilności API; w aktualnym backendzie dotyczą powiadomienia o nowym koncie. Starsze zdarzenia `account_approved` pozostają historyczne i nie są wysyłane przez nowy backend.

## Sprawdzenie po wdrożeniu

1. Zaloguj nowe dodatkowe konto Google, którego profil nie istnieje w aplikacji. Nie usuwaj działających kont w celu testu.
2. Sprawdź w skrzynce właściciela i Resend → Emails wiadomość **Linksifty: new account awaiting approval**.
3. Odśwież stronę i zaloguj się ponownie: liczba wiadomości nie powinna wzrosnąć.
4. Zatwierdź konto w Admin: użytkownik uzyskuje dostęp bez limitu prób, lecz z limitem budżetu; kolejny mail nie powstaje.

Status `sent` oznacza przyjęcie przez API, nie gwarantuje doręczenia. Sprawdź zdarzenie delivered/bounced w Resend i spam w Gmailu.

## Błędy i odzyskiwanie

| Status | Działanie |
| --- | --- |
| `failed (not_configured)` | Ustaw obie zmienne nadawcy/klucza, sprawdź odbiorcę i zrestartuj API |
| `failed (provider_rejected)` | Sprawdź zakres klucza, domenę i nadawcę w Resend |
| `failed (timeout)` / `failed (unavailable)` | Najpierw sprawdź w Resend, czy wiadomość została przyjęta; nie ponawiaj jej w ciemno |
| `sent`, brak w skrzynce | Sprawdź status dostarczenia, spam i adres odbiorcy |
| Brak zdarzenia dla dawnego konta | To oczekiwane: brak wysyłki wstecznej. Testuj świeże konto |

**Retry email** w panelu administratora jest jawną akcją operatora dla nieudanych zdarzeń. Ponowienia używają tego samego klucza idempotencji (UUID zdarzenia). Logowanie nigdy nie ponawia stanów `failed` ani `sending`.

Jeżeli proces przerwie się po przejęciu zdarzenia, status może pozostać `sending`. Panel nie ponawia go automatycznie. Operator powinien sprawdzić w Resend klucz zdarzenia oraz odbiorcę. Jeśli dostawca przyjął wiadomość, należy uzgodnić rekord `account_notifications` z jej identyfikatorem i stanem `sent` przez istniejący serwerowy RPC `finish_account_notification`; nie generować nowego maila. Jeśli wiadomości nie ma, trzeba najpierw potwierdzić, że poprzednie żądanie nie jest nadal w toku. Ręczne odzyskanie wymaga uprawnionego dostępu serwerowego do bazy, nie klucza w przeglądarce.

Klucze idempotencji Resend mają ograniczony czas przechowywania (24 godziny). Po tym czasie nie ponawiaj niepewnego wywołania bez uzgodnienia z dostawcą: mogłoby utworzyć drugi mail. Brak automatycznej powtórki jest celowy; przy awarii przypomnienie może wymagać ręcznego uzgodnienia. Ta zmiana nie obiecuje matematycznej gwarancji pojedynczej dostawy na granicy dwóch systemów.

Nie zmieniano środowiska produkcyjnego ani nie wysyłano prawdziwych wiadomości podczas implementacji. Testy używają kontrolowanej odpowiedzi HTTP.

Dokumentacja: [domeny Resend](https://resend.com/docs/dashboard/domains/introduction), [idempotencja](https://resend.com/docs/dashboard/emails/idempotency-keys).
