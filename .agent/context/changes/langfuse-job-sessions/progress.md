# Langfuse job sessions — 2026-10-16

Implemented the approved bounded design: group analysis execution/resume traces
by stable `linksifty:job:<job_id>` session IDs. Use the existing Langfuse SDK
attribute propagation in the processing scope; nested events, fetch spans and
model generations inherit it. No account identifiers, new dependencies,
migrations, provider calls or model changes.

An ExitStack closes propagation and the observation in order, including partial
setup failure; telemetry errors remain isolated from processing. Standalone
orphan reconciliation has no job session. No topology or product-flow change.
Graft is unavailable; focused searches identified the existing scope boundary.

Verification: [evidence](evidence.md). Implementation is complete; the user
authorized pushing this change and the preceding citation fix to main.
Hosted deployment and paid verification have not been performed in this work.
