# Diagramy Linksifty

Diagramy są po angielsku zgodnie z `AGENTS.md`. HTML jest samodzielnym
interaktywnym artefaktem Archify; otwórz lokalny plik w przeglądarce.
Podgląd pliku na GitHub nie wykonuje osadzonego interfejsu.

| Widok | Artefakt | Edytowalne źródło | Walidacja |
| --- | --- | --- | --- |
| System, hosting i granice zaufania (`architecture`) | [system.html](system.html) | [system.json](system.json) | [raport](system.finalize-summary.json) |
| Analiza tekstu i ścieżka niepełnej treści (`workflow`) | [processing.html](processing.html) | [processing.json](processing.json) | [raport](processing-review-2/processing.finalize-summary.json) |
| CI i kontrolowane przez operatora wydanie (`workflow`) | [delivery.html](delivery.html) | [delivery.json](delivery.json) | [raport](delivery.finalize-summary.json) |

Każdy diagram zawiera referencje do plików i zakresów linii w rewizji
`763e0824ae20d089de1103e1d5fa746a4f4859bd`. Linki źródłowe działają w trybie
`local-only`. Nie poświadczają późniejszych niezacommitowanych zmian ani
rzeczywistego stanu hostingu. Flow pomija część szczegółów transportu; pełny opis
warunków, kosztów i recovery znajduje się w [przepływach](../flows/README.md).
Diagram wydania odróżnia istniejące joby CI od manualnej procedury operatora.

## Wynik sprawdzeń — 2026-10-22

Dla wszystkich trzech artefaktów przeszły `validate`, `deliver` i ścisłe `check`
w profilu `showcase`, z weryfikacją źródeł repozytorium. HTML został wygenerowany.
`browser-check` jest **skipped**: lokalny runtime Archify nie znajduje Chrome/
Chromium. `finalize` kończy się kodem 2; nie jest to pełne zaliczenie wszystkich
bramek. Nie wykonano oceny wizualnej ani eksportu zrzutów.

Pełne raporty: `*.finalize.json`, metadane/provenance: `*.delivery.json`,
status przeglądarki: `*.browser-check.json`. Końcowy raport flow analizy jest
w `processing-review-2/`; wcześniejsze raporty w katalogu głównym dokumentują
poprzednią próbę i konflikt ścieżki dowodów po zmianie HTML. Brak renderowania w przeglądarce
nie jest ukrywany jako pozytywny wynik.

## Aktualizacja diagramów

Edytuj JSON i odnośniki do sprawdzonych źródeł, następnie z root repozytorium:

```sh
node .agents/skills/archify/bin/archify.mjs finalize architecture docs/diagrams/system.json docs/diagrams/system.html --repo-root . --quality showcase --json
node .agents/skills/archify/bin/archify.mjs finalize workflow docs/diagrams/processing.json docs/diagrams/processing.html --repo-root . --quality showcase --json
node .agents/skills/archify/bin/archify.mjs finalize workflow docs/diagrams/delivery.json docs/diagrams/delivery.html --repo-root . --quality showcase --json
```

Przy zmianie kodu zaktualizuj `meta.repository.revision` i wszystkie właściwe
referencje na istniejący commit. Nie przypisuj niezacommitowanych plików do HEAD.
Jeśli jest dostępny istniejący Chrome/Chromium, ustaw `ARCHIFY_CHROME` na jego
plik wykonywalny i ponów walidację zamrożonego JSON. Przy zmianie kandydata z
wcześniejszymi dowodami przeglądarkowymi użyj nowego katalogu `--out-dir`, zgodnie
z kontraktem Archify. Nie edytuj ręcznie wygenerowanego HTML.
