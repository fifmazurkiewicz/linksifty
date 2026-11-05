# Manual QA backlog — Linksifty

Lista zgłoszeń z testów manualnych. Priorytety i realizacja osobno, po zakończeniu zbierania.

Status wpisu: `open` · `prioritized` · `in_progress` · `done` · `wontfix`

**Execution:** branch `fix/manual-qa-backlog-20261105` · change record `.agent/context/changes/manual-qa-backlog-20261105/`

---

## QA-001 — Odrzucone zgłoszenie nadal w panelu admina

| Pole | Wartość |
| --- | --- |
| Status | done (pending MR) |
| Priorytet | do ustalenia |
| Kontekst testu | konto admina, panel Admin |
| Obserwacja | Po odrzuceniu zgłoszenia użytkownika wpis dalej widać; dostępna jest tylko akcja Approve (Reject znika). |

### Oczekiwane zachowanie (właściciel)

1. Po Reject zgłoszenie znika z aktywnej listy admina (archiwizacja w bazie, nie „wiszące” oczekujące).
2. Odrzucony użytkownik może ponownie poprosić o akceptację.
3. Ponowna prośba ustawia konto z powrotem w kolejkę do decyzji i wysyła adminowi nowy mail przez Resend.

### Stan kodu dziś (analiza)

- Statusy profilu: `pending` \| `approved` \| `rejected` (`account_contracts.py`).
- Panel admina listuje wszystkie konta; dla `rejected` ukrywa Reject, ale nadal pokazuje Approve (`AdminPanel.tsx`).
- Odrzucony user widzi ekran „Account unavailable” bez przycisku ponownej prośby (`AccountStatusScreen.tsx`).
- Mail o nowym koncie powstaje przy pierwszym insertcie profilu; przy `rejected` dispatch jest pomijany; akceptacja nie wysyła maila. Brak ścieżki „request again → nowe zdarzenie + Resend”.

### Zakres do doprecyzowania przy priorytetyzacji

- Czy archiwum ma być niewidoczne całkowicie, czy osobna sekcja „Rejected / archived”?
- Czy budżety konta odrzuconego mają znikać z panelu razem ze zgłoszeniem?
- Limit / cooldown ponownych próśb (spam maili Resend)?
- Czy ponowna prośba resetuje trial, czy zachowuje zużyte linki próbne?
- Relacja do QA-002: wspólny model akcji Approve / Reject / Block.

### Kryteria akceptacji (robocze)

- [ ] Po Reject wpis nie pojawia się w aktywnej liście do akceptacji.
- [ ] Rekord pozostaje w bazie jako zarchiwizowany / `rejected` (bez soft-delete treści użytkownika poza regułami produktu).
- [ ] User ma jawną akcję ponownej prośby o dostęp.
- [ ] Ponowna prośba → status wymagający decyzji admina + nowy mail Resend do właściciela.
- [ ] Licznik „pending approvals” nie liczy odrzuconych ani zarchiwizowanych.

---

## QA-002 — Approved: zamiast Reject powinno być Block / zawieszenie

| Pole | Wartość |
| --- | --- |
| Status | done (pending MR) |
| Priorytet | do ustalenia |
| Kontekst testu | konto admina, panel Admin |
| Dowód | screenshot: `pending` → Approve + Reject; `approved` → tylko Reject |
| Obserwacja | Dla zaakceptowanego konta admin widzi wyłącznie „Reject”, co nie mówi o zawieszeniu/blokadzie działającego użytkownika. |

### Oczekiwane zachowanie (właściciel)

Docelowy model akcji w panelu:

| Stan konta | Akcje admina |
| --- | --- |
| `pending` (nowe lub ponowna prośba) | **Approve** / **Reject** |
| `approved` | **Block** (zawieszenie / blokada), nie „Reject” |
| po Reject (zgłoszenie) | znika z aktywnej kolejki; user może zgłosić się ponownie → mail Resend → znowu Approve / Reject |
| po Block (aktywne konto) | konto niedostępne dla usera; (do doprecyzowania: czy Block = ten sam stan co rejected, czy osobny `blocked`) |

Reject dotyczy decyzji o zgłoszeniu. Block dotyczy odebrania dostępu już zaakceptowanemu kontu. Etykieta musi to rozróżniać.

### Stan kodu dziś (analiza)

- Jedyna mutacja statusu w API admina: `approved` \| `rejected` — brak osobnego `blocked` / suspend.
- UI: `status !== 'approved'` → Approve; `status !== 'rejected'` → Reject. Dla approved zostaje więc tylko Reject (`AdminPanel.tsx`).
- Skutek `rejected` już odcina dostęp (`can_access`, ekran „Account unavailable”), więc semantycznie Reject na approved działa jak blokada, ale nazwa i UX tego nie komunikują.

### Zakres do doprecyzowania przy priorytetyzacji

- Czy **Block** to nowy status `blocked`, czy tylko etykieta UI na przejście `approved → rejected`?
- Czy zablokowany user może sam poprosić o odblokowanie (jak po Reject), czy tylko admin odblokowuje przez Approve?
- Czy po Block konto znika z listy aktywnych, zostaje z etykietą Blocked, czy osobna sekcja?
- Potwierdzenie odblokowania: samo Approve wystarczy?

### Kryteria akceptacji (robocze)

- [ ] Dla `pending`: widoczne Approve i Reject.
- [ ] Dla `approved`: widoczne Block (nie Reject); akcja zawiesza dostęp.
- [ ] Semantyka Reject vs Block jest jasna w UI (i najlepiej w statusie / API).
- [ ] Spójność z QA-001: po Reject / Block user może (lub nie — wg decyzji) ponownie wejść w kolejkę z mailem do admina.
- [ ] Licznik pending liczy tylko oczekujące zgłoszenia, nie zablokowanych.

---

## Model docelowy (QA-001 + QA-002, roboczy)

```text
[nowe konto] → pending → Approve → approved
                      ↘ Reject  → archived/rejected
                                      ↘ user: request again → pending + mail Resend
[approved] → Block → blocked/suspended (nazwa TBD)
                ↘ (?) odblokowanie przez Approve lub ponowna prośba usera
```

QA-001 i QA-002 warto realizować razem albo w tej kolejności: najpierw model stanów, potem UI etykiet.

---

## QA-003 — Publiczny repo GitHub kończy jako „requires sign-in”

| Pole | Wartość |
| --- | --- |
| Status | done (pending MR) |
| Priorytet | do ustalenia |
| Kontekst testu | Inbox → Needs action |
| URL | `https://github.com/higgsfield-ai/skills`; także `https://github.com/Panniantong/Agent-Reach` |
| Dowód | screenshot (higgsfield): „Paste readable content… The page requires sign-in.” + Partial preview; drugi publiczny URL zgłoszony z tym samym objawem |
| Obserwacja | Publiczne repo GitHub nie daje pełnej analizy; system żąda paste / Retry i raportuje `login_required`. Wzorzec powtarza się na ≥2 publicznych repo. |

### Dlaczego tak się dzieje (analiza kodu)

To niemal na pewno **fałszywy positive heurystyki logowania**, nie prawdziwy paywall GitHuba.

1. Fetcher pobiera HTML i wyciąga tekst. Ignoruje m.in. `nav` / `footer` / `aside`, ale **nie** `header` — chrome GitHuba z „Sign in” / „Sign up” często wpada do tekstu.
2. Po udanym 200: jeśli w tekście jest `"sign in"` lub `"log in"`, wynik od razu to `FetchFailure.LOGIN_REQUIRED` (`http_fetcher.py`), bez oceny czy to ściana logowania, czy link w UI.
3. Ta sama heurystyka jest w `evaluate_content` (`content_policy.py`) dla fetched text.
4. Partial preview powstał z fragmentu — treść repo była częściowo czytelna; ocena i tak nie ruszyła, bo failure = login wall.

Repo jest publiczne; Linksifty nie loguje się do GitHuba. Komunikat myli użytkownika: wygląda jak „strona wymaga konta”, a chodzi o wykrycie frazy w HTML.

### Oczekiwane zachowanie (robocze)

- Publiczne strony GitHub (repo / README / issues publiczne) nie powinny wpadać w `login_required` tylko przez chrome „Sign in”.
- Albo: osobna ścieżka dla `github.com` (np. raw README / API), albo ostrzejsza detekcja login wall (nie sam substring w całej stronie).
- Jeśli treść jest wystarczająca (≥200 znaków, kompletny dokument), powinna iść do assessment; paste tylko gdy naprawdę brak treści.

### Zakres do doprecyzowania przy priorytetyzacji

- Czy cel to ogólna poprawa heurystyki (mniej FP na wielu serwisach), czy specjalnie GitHub?
- Czy wspierać `raw.githubusercontent.com` / API GitHuba (osobny adapter jak X)?
- Jak traktować prywatne repo (prawdziwy 404/login)?

### Kryteria akceptacji (robocze)

- [ ] Publiczne `github.com/...` (przynajmniej README / landing repo) nie kończy się `login_required` wyłącznie przez UI „Sign in”.
- [ ] Komunikat dla prawdziwej ściany logowania nadal jest jasny.
- [ ] Partial preview / paste pozostają dla faktycznie nieczytelnych źródeł.
- [ ] Regresja: strony z realnym „Please sign in to continue” nadal wymagają paste.

---

## QA-004 — X Article: `x_article_incomplete` / `article_code_invalid` mimo pełnego payloadu

| Pole | Wartość |
| --- | --- |
| Status | done (pending MR) |
| Priorytet | do ustalenia |
| Kontekst | post/Article z X; Retry → Needs action; Langfuse: `stage=x_article_incomplete`, `status=awaiting_manual_content` |
| Dowód | logi `x_api_debug` (request_id `1ec7c9fdf0074b03…`, części 6/7 i 7/7, `truncated=false`) + `x_fetch_failed reason=x_article_incomplete check=article_code_invalid`; job `865557a8-bb77-4922-9da6-efc6bd1edf1b` |
| Obserwacja | X zwrócił długi tekst Article (tytuł o Jev/Claude bill), a Linksifty i tak nie uruchomił assessmentu — UI prosi o paste / Retry. |

### Co oznacza „incomplete” tutaj

**Nie** znaczy „X uciął odpowiedź” ani „brak body w API”.

Oznacza: adapter dostał Article (HTTP 200, payload złożony), ale **strict parser** uznał strukturę za niekompletną/niezaufaną do oceny i fail-closed → `awaiting_manual_content`. Stage w trace (`x_article_incomplete`) to zapisana przyczyna odmowy, nie „brak fetcha”.

Konkretnie `check=article_code_invalid`: w `entities.code` jest snippet, który nie przechodzi walidacji w `parse_article` (`x_content.py`), np.:

- `code` nie jest niepustym stringiem,
- `content` nie jest stringiem albo zawiera `\0`,
- `language` nie pasuje do `[A-Za-z0-9_+.#-]{0,40}`,
- albo **`code` nie występuje jako substring w `content`** (wymagane przez parser).

Wtedy cały Article jest odrzucany — nawet jeśli `plain_text` / title wyglądają kompletnie w logach.

### Stan kodu dziś

- Celowa polityka: „previews never stand in for Article bodies”; niepewne entity → brak assessmentu.
- UI mapuje `x_article_incomplete` na prośbę o wklejenie całego artykułu wraz z kodem.
- Wcześniejsze podobne FP/kompatybilność: `article_entities_invalid`, `article_media_invalid`, `article_body_*` (historia w `x-rich-sources`).

### Oczekiwane zachowanie (robocze)

- Gdy body Article jest kompletne, a tylko metadata code jest „dziwna”, nie blokować całej analizy bez jasnego powodu — albo naprawić kompatybilność ze realnym shape X `entities.code`, albo degradować: body + ujawnione pominięcie code blocks.
- Komunikat użytkownika powinien odróżniać „X nie oddał treści” od „odrzucone przez walidację code/entities”.

### Zakres do doprecyzowania

- Zachować fail-closed na code, czy allowlist / soft-omit z etykietą „code blocks omitted”?
- Czy zbierać zanonimizowany fixture shape (bez treści użytkownika) z kolejnego live failure?

### Kryteria akceptacji (robocze)

- [ ] Artykuły X z pełnym body nie padają wyłącznie na zbyt wąskiej walidacji `entities.code`, o ile shape jest zgodny z realnym API.
- [ ] Prawdziwie uszkodzony/niekompletny Article nadal → paste, bez cichego assessmentu.
- [ ] Log/`failure_reason` pozostaje precyzyjne (`article_code_invalid` vs brak body).
- [ ] UI nie sugeruje „incomplete fetch”, gdy fetch się udał, a padł parser.

---

## QA-005 — Po 2.–3. Retry: zaproponować Vision LLM (obrazy / media)

| Pole | Wartość |
| --- | --- |
| Status | done (pending MR) |
| Priorytet | do ustalenia |
| Typ | propozycja produktowa (enhancement), powiązana z QA-004 i ogólnym `awaiting_manual_content` |
| Obserwacja właściciela | Gdy tekstowy fetch / parse X Article pada (np. incomplete), Retry powtarza tę samą ścieżkę. Po 2–3 próbach warto zaproponować Vision LLM — na źródle mogą być zdjęcia lub filmiki z treścią. |

### Kontekst względem obecnego produktu

- Przy **udanym** bogatym źródle X już jest jedna paczka vision (`OpenRouterImageReader`) dla statycznych PNG/JPEG/WebP z `pbs.twimg.com`, z budżetem i etykietami model-extracted.
- Video / GIF / animacje dziś → `non_static_image` / unsupported; fail-closed, bez vision na klatkach.
- UI Retry wprost: „Media is not analyzed.” — kolejny Retry nie włącza vision.
- Przy `x_article_incomplete` (np. `article_code_invalid`) parser pada **zanim** dojdzie do image reading — vision w ogóle nie startuje, nawet jeśli media są w payloadzie.

### Oczekiwany kierunek (roboczy, od właściciela)

1. N-ty Retry (np. 2. lub 3.) albo osobny CTA: „Spróbuj z Vision / odczytaj obrazy” — **jawna zgoda**, ujawniony koszt budżetu.
2. Vision ma pomóc odzyskać treść ze zdjęć (i ewentualnie filmów), gdy zwykły tekst jest incomplete.
3. Nie zastępować paste w ciemno: nadal ujawniać ograniczenia (to interpretacja modelu, nie pełny assessment source contract bez complete text — do decyzji).

### Zakres do doprecyzowania przy priorytetyzacji

- Próg: po 2. vs 3. Retry, czy od razu osobny przycisk przy `x_article_incomplete` / `x_media_*` / `image_reading_*`?
- Tylko X, czy też zwykły HTTP z `omitted_media` (image/video w HTML)?
- Filmy: klatki / transcript — duży skok scope vs tylko static images już wspierane.
- Czy Vision po nieudanym parse Article może działać na samych media bez zaakceptowanego body (dziś polityka: incomplete Article → paste)?
- Relacja do QA-004: najpierw naprawić `article_code_invalid`, potem Vision jako fallback — czy odwrotnie?

### Kryteria akceptacji (robocze)

- [ ] Po N nieudanych Retry user dostaje jasną, opcjonalną ścieżkę Vision z kosztem i zgodą.
- [ ] Bez zgody nie ma automatycznego Vision na zwykłym Retry.
- [ ] Wynik Vision jest oznaczony jako model-extracted; nie udaje kompletnego źródła, jeśli contract tego zabrania.
- [ ] Budżet / rezerwacje jak przy istniejącej image-reading ścieżce; brak cichych retry paid calls.
- [ ] Video: albo świadomie out of scope v1, albo osobna decyzja z limitem klatek/kosztu.

---

## QA-006 — Błędy fetch / incomplete nie pojawiają się w Sentry

| Pole | Wartość |
| --- | --- |
| Status | done (pending MR) |
| Priorytet | do ustalenia |
| Typ | obserwacja monitoringu (może być by-design + luka widoczności operacyjnej) |
| Kontekst | QA-003 (GitHub `login_required`), QA-004 (`x_article_incomplete` / `article_code_invalid`) — w UI i logach/Langfuse widać failure, w Sentry nic |
| Obserwacja właściciela | Przy tych problemach Sentry nie pokazał żadnego eventu. |

### Dlaczego (analiza kodu / kontraktu)

To **oczekiwane** przy obecnym kontrakcie Sentry, nie dowód że SDK „nie działa”:

1. `x_fetch_failed` / `source_fetch_failed` idą jako `_logger.warning(...)`, nie jako nieobsłużony wyjątek.
2. Wynik to normalny stan produktu: `awaiting_manual_content` + `failure_reason` — użytkownik ma paste/Retry.
3. Kontrakt (`docs/technical/sentry.md`): deniale / walidacja / limity **nie** są application failures; do Sentry idą terminalne/nieoczekiwane wyjątki (`capture_error` w processing) + unhandled.
4. `LoggingIntegration(event_level=ERROR)` — warningi z fetcha nie tworzą eventów Sentry.
5. Frontend: `ApiError` ze statusem &lt; 500 też nie jest reportowany.

Langfuse / logi Render są dziś miejscem na te ścieżki (jak w QA-004), nie Issues w Sentry.

### Co to oznacza produktowo

| Pytanie | Odpowiedź robocza |
| --- | --- |
| Czy Sentry „przegapił crash”? | Nie — to nie crash. |
| Czy admin widzi te problemy w Sentry? | Nie, by design. |
| Czy właściciel chce widoczność w Sentry? | Do decyzji — osobna ścieżka (np. rzadkie `capture_message` z samym `reason`/`check`, bez treści źródła), albo dashboard poza Sentry (Langfuse, metryki fail reasons). |

### Zakres do doprecyzowania

- Zostawić by-design i polegać na Langfuse/logach?
- Dodać **agregowaną** widoczność acquisition failures (tylko `reason`/`check`/`provider`, zero URL/body)?
- Osobno zweryfikować SENTRY-06: czy hosted `SENTRY_ENABLED=true` i synthetic error w ogóle dochodzi (niezależnie od tych fetchy)?

### Kryteria akceptacji (robocze) — zależą od decyzji

**Jeśli by-design:**  
- [ ] Dokumentacja / UI admina jasno: incomplete fetch ≠ Sentry issue; gdzie szukać (Langfuse, log `x_fetch_failed`).

**Jeśli chcesz Sentry visibility:**  
- [ ] Tylko allowlistowane tagi techniczne (`reason`, `check`, `provider`); zero content/URL/PII.  
- [ ] Bez spamu (dedupe / sampling / tylko N-ty Retry).  
- [ ] Regresja privacy envelope nadal przechodzi.

---

## QA-007 — X quote zagnieżdżony: `partial_content` / `missing_referenced_post`

| Pole | Wartość |
| --- | --- |
| Status | done (pending MR) |
| Priorytet | do ustalenia |
| Item / job | item `84ab48f0-…`, job `be911b7b-…`, resume → 202; post `2114001885413716163` |
| Dowód | Render: `x_fetch_failed reason=partial_content check=missing_referenced_post`; Langfuse: failure `partial_content`; Sentry: cisza (jak QA-006) |
| Obserwacja | X oddaje pełny `note_tweet` (lista repo finance+AI) + quote `2111428512142020815` w `includes`; i tak Needs action / partial. |

### Dlaczego

1. Główny post cytuje `2111428512142020815` — jest w `includes.tweets` (1 poziom ekspansji X).
2. Ten cytowany post **też** cytuje `2060693851598107006` — **nie** ma go w `includes` (API nie rozwija quote w głąb w jednym lookupu).
3. W `_source_posts` dodatkowy `_lookup` jest tylko dla `ref.type == "embedded"` (Article embeds). Dla `quoted` / `retweeted` brakuje body → od razu `missing_referenced_post`.
4. Fail-closed: mimo kompletnego tekstu głównego posta cała akwizycja pada → `awaiting_manual_content`.

To nie jest ucięty HTTP (`part=1/3…3/3`, status 200). To świadoma polityka „wszystkie referenced posts muszą być w mapie”, bez follow-up lookup dla zagnieżdżonych quote’ów.

### Oczekiwane zachowanie (robocze)

- Albo: bounded follow-up lookup dla brakujących `quoted`/`retweeted` (jak dla Article `embedded`), z limitem głębokości/requestów.
- Albo: degradacja — oceniać dostępny tekst + jawna etykieta „nested quote omitted”, zamiast blokować cały post.
- Sentry: bez zmian vs QA-006, chyba że osobna decyzja o widoczności `reason`/`check`.

### Kryteria akceptacji (robocze)

- [ ] Post z pełnym `note_tweet` i 1-poziomowym quote w includes nie pada tylko przez brak **zagnieżdżonego** quote poza includes.
- [ ] Brakujący referenced post ma albo bounded lookup, albo ujawnione pominięcie — nie cichy partial bez treści użytkownikowi.
- [ ] Limity requestów X / 60s / `_MAX_POSTS` nadal trzymane.
- [ ] Prawdziwie niedostępny referenced post nadal → jasny failure + paste.

---

## QA-008 — Chat: „stopped by the relevance check” — co to znaczy / UX

| Pole | Wartość |
| --- | --- |
| Status | done (pending MR) |
| Priorytet | do ustalenia |
| Kontekst | Analysis chat przy zapisanym assessmentcie |
| Dowód | screenshot: EN ×2 „Is it something like grokbot?” → czerwony komunikat; PL „czy to jest coś podobnego do grok bota?” → pełna odpowiedź o Harness² |
| Obserwacja właściciela | Niejasne, co oznacza zatrzymanie przez relevance check. |

### Co to znaczy (produkt / kod)

Przed odpowiedzią i Brave search chat odpala **klasyfikator zakresu (Jev)**: czy ostatnie pytanie dotyczy zapisanej analizy / jej tematu (`relevant` / `off_topic` / `unsafe`).

Czerwony tekst w UI mapuje wyłącznie `turn.error === 'classification_uncertain'`:

> This question was stopped by the relevance check before an answer or search could run. Your question is saved.

Znaczy: **brama nie wpuściła pytania do answer/search** — pytanie jest zapisane, ale nie było generacji odpowiedzi ani researchu. To **nie** jest crash ani „Sentry error”; to routing / niepewność klasyfikacji.

Różnice ścieżek:

| Wynik | Zachowanie |
| --- | --- |
| `relevant` (pewność/prawdopodobieństwo OK) | idzie decyzja → ewentualnie search → odpowiedź |
| `off_topic` / `unsafe` | completed turn z **stałą** odmową PL/EN (bez search) |
| `uncertain` (niska pewność wyboru) | completed turn z prośbą o doprecyzowanie związku z analizą |
| `classification_uncertain` (failed turn) | czerwony komunikat; historycznie: confidence &lt; 0.8; w obecnym kodzie źródłowym ten string już nie jest ustawiany — UI nadal go tłumaczy dla starych/hosted wierszy |

Na screenshocie EN padło jako failed + ten komunikat; to samo pytanie po polsku przeszło jako relevant i dostało odpowiedź. To wskazuje na **niestabilność / wrażliwość bramki** (język, kontekst „grokbot”, próg), nie na to, że temat jest z zasady zakazany.

### Problemy UX / produktu do rozważenia

- Komunikat nie mówi: *dlaczego* (niepewność vs off-topic), *co zrobić* (powiąż z analizą, przeformułuj).
- To samo pytanie EN fail / PL OK — niespójne UX, wygląda jak bug.
- „Your question is saved” nie wyjaśnia, czy poszła opłata za classification (zwykle tak, mała) i że nie było answer/search charge.

### Oczekiwane (robocze)

- Jasniejszy copy: np. „Nie udało się pewnie uznać pytania za związane z tą analizą — doprecyzuj związek…” zamiast technicznego „relevance check”.
- Spójne traktowanie borderline: soft clarification zamiast failed turn, jeśli hosted jeszcze emituje `classification_uncertain`.
- Ewentualnie: mniej fałszywych stopów na krótkich porównaniach („is it like X?”) gdy temat analizy to framework/agent.

### Kryteria akceptacji (robocze)

- [ ] User rozumie z komunikatu, że pytanie nie dotyczyło pewnie tematu analizy / trzeba doprecyzować.
- [ ] To samo merytoryczne pytanie EN/PL nie daje diametralnie innego wyniku bez wyjaśnienia.
- [ ] Off-topic vs uncertain vs failed classification są rozróżnialne w UI.
- [ ] Nadal: unsafe/off-topic nie odpala answer/search.

---

## Kolejne zgłoszenia

_(dopisywane w trakcie testów manualnych)_
