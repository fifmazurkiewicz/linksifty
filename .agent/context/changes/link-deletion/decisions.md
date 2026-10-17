# Approved design and implementation decisions

- Reuse the existing queue and cascade relationships; one batch operation serves
  both single-item and selected-item controls. No new dependencies.
- A native browser confirmation lists the count and irreversibility. Backend and
  SQL also require explicit `confirmed: true`.
- Delete at most 50 unique IDs (the queue's current page size), atomically.
  Missing/foreign IDs reject the whole batch with one generic unavailable error.
- Lock account profile, settings, reservations, jobs, then items to follow the
  existing paste, budget and late-result write orders. Reject inconsistently
  owned child rows before cascading (legacy schema lacks composite owner FKs).
  In-flight paid calls may already have been sent; retained orphan reservations
  allow late generation-ID/cost reconciliation without retaining article content.
- Scrub rubric snapshots in retained reservations to static legacy defaults;
  monthly spend and trial usage do not reset when content is deleted.
- Clear selection on filter changes. Select-all applies to visible items only.
  Retain selection on error; show success only after server confirmation.
- Filter successful deletions from later stale in-flight snapshots in the current
  session, so deleted content cannot flash back into the queue.
