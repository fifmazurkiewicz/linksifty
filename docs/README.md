# Dokumentacja Linksifty

Zaktualizowana 2026-10-22 na podstawie kodu i konfiguracji repozytorium.
Opisy bieżącej implementacji nie potwierdzają stanu środowisk zewnętrznych.

| Temat | Dokument |
| --- | --- |
| Start, wymagania i polecenia | [README projektu](../README.md), [frontend](../frontend/README.md) |
| Komponenty, dane, integracje i bezpieczeństwo | [Architektura](architecture/overview.md) |
| Logowanie, analiza, recovery, chat i usuwanie | [Przepływy](flows/README.md) |
| Interaktywne diagramy i ich edycja | [Diagramy](diagrams/README.md) |
| GitHub Actions, testy i granice automatyzacji | [CI/CD](deployment/ci-cd.md) |
| Kolejność wdrożenia, środowiska, rollback | [Runbook](deployment/README.md) |
| Szczegółowa konfiguracja i rollout poszczególnych funkcji | [Setup](deployment/setup.md), [Supabase](deployment/supabase.md) |
| Cel produktu i dalsze prace | [Wizja](product/vision.md), [roadmapa](roadmap.md) |
| Wcześniejsze decyzje i opis zmian | [Historia architektury](architecture/implementation-history.md), [referencja funkcji](product/feature-reference.md) |

Źródłem prawdy dla działania jest kod, dla schematu migracje, a dla CI
`.github/workflows/ci.yml`. Ustawienia Render/Vercel, zastosowane migracje,
sekrety i aktywność retencji wymagają sprawdzenia w konkretnym środowisku.
Starsze specyfikacje i plany w `superpowers/` oraz materiały w `.agent/context/`
zachowują kontekst decyzji, lecz nie zastępują aktualnej dokumentacji.
