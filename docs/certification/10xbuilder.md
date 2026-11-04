# Linksifty — dokumentacja do zgłoszenia 10xBuilder

Stan sprawdzony 4 listopada 2026 na podstawie kodu, dokumentacji i lokalnych testów. Opis nie jest potwierdzeniem zastosowania wszystkich migracji na produkcji.

Repozytorium: https://github.com/fifmazurkiewicz/linksifty

Aplikacja: https://linksifty.fmazurkiewicz.dev

## Użytkownik i problem

Linksifty jest dla osoby, która zbiera artykuły i posty, ale potrzebuje pomocy w wyborze materiałów wartych przeczytania. Zamiast kolejnej listy zakładek dostaje notatkę, cytaty, ocenę ośmiu kryteriów i wyjaśniony werdykt. Analiza dotyczy tekstu; aplikacja nie deklaruje analizy obrazów, audio ani wideo.

## Kontrola dostępu i darmowe konto

Logowanie obsługuje Supabase Auth. Backend ustala tożsamość użytkownika i ogranicza operacje na treści do właściciela. Administrator zarządza kontami, ale nie otrzymuje dostępu do cudzych artykułów i analiz.

Oceniający korzystają z własnego darmowego konta. W implementacji konto oczekujące ma pulę trzech dodanych źródeł; zatwierdzenie przez administratora nie jest wymagane do samego rozpoczęcia próby. Analiza nadal podlega dostępnemu budżetowi usług. Usunięcie wpisu nie zwraca wykorzystanej próby ani kosztu. To opis reguł kodu — ich aktywację na wdrożeniu należy potwierdzić świeżym kontem.

## CRUD w domenie aplikacji

| Operacja | Działanie użytkownika | Znaczenie i zabezpieczenia |
| --- | --- | --- |
| Create | Dodanie linku lub tekstu do analizy | Powstaje wpis i zadanie przetwarzania. Aplikacja waliduje wejście, wykrywa duplikaty i sprawdza uprawnienia oraz limity. |
| Read | Przeglądanie kolejki i szczegółów analizy | Użytkownik widzi swoje źródła, stan przetwarzania, notatkę, cytaty, oceny, wynik i uzasadnienie. |
| Update | Wklejenie pełnej treści do istniejącego wpisu wymagającego uzupełnienia | Aktualizacja materiału źródłowego pozwala kontynuować analizę tego samego wpisu. Dodatkowo można zmieniać własne opisy kryteriów, wagi i próg dla przyszłych analiz. Nie jest to obietnica dowolnej edycji już gotowego wyniku AI. |
| Delete | Usunięcie jednego lub grupy własnych wpisów | Operacja wymaga potwierdzenia i usuwa powiązaną treść, analizę, cytaty, rozmowę i zadania. Zapisy rozliczeniowe pozostają na potrzeby rozliczenia kosztów. |

## Logika biznesowa

### Od źródła do analizy

Użytkownik dodaje źródło. Backend próbuje pobrać kompletny tekst, a następnie przekazuje materiał do modelu. Brak pełnej treści kieruje wpis do ręcznego uzupełnienia. Czytelny fragment może dostać oznaczony podgląd, ale nie pełną ocenę ani wynik procentowy.

Model przygotowuje notatkę i ocenę kryteriów, a aplikacja waliduje strukturę oraz powiązanie cytatów ze źródłami. Ostateczny tekst cytatu pochodzi z zapisanych fragmentów źródła. Brave może dostarczyć dodatkowe materiały porównawcze, ale sama obecność innej strony nie stanowi dowodu niezależnego potwierdzenia.

### Ocena i werdykt

Osiem kryteriów obejmuje wartość poznawczą, poparcie twierdzeń, użyteczność, wiarygodność źródła, odtwarzalność, niezależne potwierdzenie, uczciwe przedstawienie interesów i konkretność. Każde ocenione kryterium ma punkty 1–5 oraz wagę 1–10. Kryteria niezweryfikowane lub niemające zastosowania nie otrzymują sztucznego zera.

Wynik oblicza kod domenowy, niezależnie od dostawcy LLM:

`wynik = 100 × suma(punkty × waga) / (5 × suma wag ocenionych kryteriów)`

Wynik jest zaokrąglany do dwóch miejsc. Brak ocenionych kryteriów oznacza brak wyniku. Dla bieżących reguł wersji 2:

- `hype` wymaga konkretnego sygnału przesady powiązanego z cytatem; sam niski wynik nie wystarcza;
- brak oceny lub słabe/niezweryfikowane kryterium kluczowe oznacza `to_review`;
- po spełnieniu warunków kryteriów kluczowych wynik na poziomie ustawionego progu lub wyższym oznacza `valuable`;
- pozostałe przypadki otrzymują `to_review`.

Kryteria kluczowe to poparcie twierdzeń, wiarygodność, użyteczność i konkretność; punktacja do 2 lub brak oceny wymaga przeglądu. Każda analiza zachowuje użyty zestaw reguł i próg, więc zmiana ustawień nie przepisuje historii. Starsze analizy zachowują wcześniejsze zasady.

### Kontrola kosztów

Przed płatną operacją aplikacja rezerwuje budżet użytkownika. Znany koszt rozlicza po odpowiedzi dostawcy. Nieznany koszt pozostaje zarezerwowany; timeout nie jest traktowany jako darmowe wywołanie. Niepewnych płatnych operacji aplikacja nie ponawia automatycznie. Wyszukiwanie i odpowiedzi modeli korzystają ze wspólnego limitu użytkownika.

## Komentarz do formularza — propozycja do zatwierdzenia przez autora

Linksifty to mój autorski projekt pomagający wybierać wartościowe materiały z internetu. Zapisany link lub wklejony tekst zamienia w notatkę z cytatami, ocenę ośmiu kryteriów i wyjaśniony werdykt. Chciałem stworzyć narzędzie, które pomaga zdecydować, czemu poświęcić uwagę.

Jedną z kluczowych decyzji było oddzielenie pracy modelu językowego od deterministycznego obliczania wyniku. Równie ważne było uczciwe sygnalizowanie braków: gdy nie da się pobrać pełnej treści, aplikacja prosi o jej uzupełnienie, zamiast przedstawiać fragment jako kompletną analizę. Istotnymi wyzwaniami projektu były pobieranie różnych źródeł, poprawne cytowania, izolacja danych użytkowników i kontrola kosztów zewnętrznych usług.

W trakcie pracy rozwijaliśmy również agent-toolkit — zestaw wspólnych zasad i umiejętności dla agentów pomagających tworzyć oprogramowanie. Równoległy rozwój obejmował między innymi dokumentację kontekstową, planowanie i przegląd zmian, testowanie oparte na ryzyku, standardy CI oraz bezpieczne monitorowanie błędów. Linksifty było praktycznym miejscem stosowania tych narzędzi i zbierania doświadczeń do ich dalszego rozwoju. Repozytorium toolkit: https://github.com/fifmazurkiewicz/agent-toolkit

Projekt pokazuje moje zastosowanie praktyk 10xWorkflow: pracę z kontekstem produktu, rozbijanie zmian na weryfikowalne kroki i sprawdzanie rezultatów testami. Praca nad nim pozwoliła mi przełożyć materiał kursu na działającą aplikację oraz własny warsztat pracy z AI.

Uwaga dla autora przed wklejeniem: akapity o osobistym celu i doświadczeniu są propozycją wypowiedzi w pierwszej osobie. Potwierdź, że oddają Twoje wrażenia. Nie dopisano nieznanych opinii o ulubionej lekcji ani satysfakcji z kursu. Historia repozytorium toolkit potwierdza rozwój wymienionych obszarów, lecz nie przypisuje każdej zmiany wyłącznie pracom nad Linksifty.

## Materiały i dowody

- [Repozytorium aplikacji](https://github.com/fifmazurkiewicz/linksifty)
- [Agent-toolkit](https://github.com/fifmazurkiewicz/agent-toolkit)
- [Testy behawioralne w toolkit](https://github.com/fifmazurkiewicz/agent-toolkit/commit/6372fd6)
- [Strategia testów w toolkit](https://github.com/fifmazurkiewicz/agent-toolkit/commit/831bd88)
- [Standard monitorowania Sentry w toolkit](https://github.com/fifmazurkiewicz/agent-toolkit/commit/f72e1b7)
- Plan najważniejszych testów: `docs/test-plan.md`.
- Wyniki lokalne: 607 testów backendu, 93 testy interfejsu i 5 testów Sentry — wszystkie przeszły 4 listopada 2026.
- Screenshoty do formularza przygotowuje autor.
