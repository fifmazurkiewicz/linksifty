# Frontend Linksifty

React 19 + TypeScript + Vite. Aplikacja zawiera logowanie Google przez Supabase,
Add, kolejkę z postępem SSE, szczegóły ocen, chat, ustawienia i panel administratora.
[README projektu](../README.md) · [Flow](../docs/flows/README.md) ·
[Deployment](../docs/deployment/README.md).

## Uruchomienie

Node 22.23.2 odpowiada CI. Wszystkie poniższe polecenia wykonuj w `frontend/`:

```sh
npm ci
npm run dev
```

Najpierw skonfiguruj nieśledzony `.env.local`:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_SUPABASE_URL=https://<project-ref>.supabase.co
VITE_SUPABASE_ANON_KEY=<public-publishable-or-anon-key>
```

Uruchom API zgodnie z głównym README. Supabase i API muszą dopuszczać dokładny
origin UI, domyślnie `http://localhost:5173`. Brak publicznej konfiguracji Supabase
oznacza niedostępne logowanie. Zmiana `.env.local` wymaga restartu Vite.
Wartości `VITE_` są publiczne: nie umieszczaj tu service-role ani kluczy dostawców.

## Mapa kodu

| Plik/katalog | Odpowiedzialność |
| --- | --- |
| [App.tsx](src/App.tsx) | Nawigacja i kompozycja ekranów |
| [auth](src/auth) | Klient Supabase, sesja, OAuth i wylogowanie |
| [lib/api.ts](src/lib/api.ts) | Typy, wywołania API z bearer tokenem, SSE |
| [features/queue](src/features/queue) | Kolejka, szczegóły, chat, komentarze |
| [features/settings](src/features/settings) | Rubric, próg, zużycie |
| [features/admin](src/features/admin) | Decyzje kont i limity |
| [ThemeToggle.tsx](src/ThemeToggle.tsx) | Motyw jasny/ciemny |
| [tests](tests) | Testy zachowania z mockami integracji |

## Weryfikacja i build

```sh
npm run lint
npm test -- --run
npm run build
npm run preview
```

Build uruchamia `tsc -b && vite build`, a wynik trafia do `dist/`.
`preview` służy sprawdzeniu lokalnego buildu; nie zastępuje API.
Vercel używa root directory `frontend`, install `npm ci`, build `npm run build`
i output `dist`. Zmiana publicznych zmiennych wymaga nowego buildu.
Frontend nie uruchamia migracji i nie zawiera serwerowych integracji.
