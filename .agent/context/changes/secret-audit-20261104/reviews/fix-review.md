# SEC-001 fix review — 2026-11-05

Independent read-only reviewer examined the configuration, regression script and
Secrets workflow against Gitleaks v8.28.0 sources.

Configuration correctly combines path and anchored hash line with AND, restricted
to generic-api-key; provider rules remain active. Reviewer found that absolute
scanner paths in the regression would not match the anchored relative allowlist.
REV-001: fixed by Docker working directory /src and scanning `.`.

Outcome: source correction complete; release verification remains incomplete.
Actual scanner unavailable locally; CI not triggered. Toolkit generator still
restores the unsafe exception. SEC-001 remains in progress, not verified.
