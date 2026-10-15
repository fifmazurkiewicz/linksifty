# Dark mode — 2026-10-16

Completed the bounded request for a top-right dark-mode control.

- Use one application-level button, shared CSS color variables and native browser
  color-scheme support. No dependency or server setting is needed.
- Initialize from the saved browser choice, otherwise the system preference.
  A manual choice takes priority; blocked storage must not prevent switching.
- Cover account and authenticated screens. Reserve room above desktop content
  and beside the mobile wordmark; keep keyboard focus and pressed state visible.
- Browser-local persistence is deliberate; cross-device synchronization is outside
  this request. No architecture or integration topology changes.
- Verification: [evidence](evidence.md). Toolkit check is clean; upstream and local
  source both report 1.2.0, with no published GitHub releases. No toolkit update
  was performed.
