# Decisions

- Keep the eight canonical criterion IDs/names. Edit description and relative
  integer weight 1–10 only, with one atomic Save for the entire settings form.
- Store rubric per account, not in frontend local storage or Render variables.
  Existing authentication supplies owner ID; payload cannot select an owner.
- Domain default catalog owns Python descriptions and default weights; transport
  validation converts to pure domain types. SQL needs a matching default for
  backfill; pin its equivalence with a runnable test rather than maintain a third
  frontend default catalog.
- Use `rubric: {criteria: [{name, description, weight}, ...]}` in settings and
  `rubric_snapshot` with the same shape in job/reservation/assessment records.
  Order the API/UI by CriterionName, not arbitrary submitted list order.
- Snapshot at first model reservation, aligned with the current threshold
  transaction. Search reservation is a separate provider operation and does not
  select analysis rules. Recovery reuses the original snapshot.
- Legacy completed/reserved records receive the original default rubric. Fresh,
  unreserved jobs read current settings; explicit reset clears the snapshot in
  the same guarded transaction as threshold/reservation reset.
- Descriptions guide model interpretation but cannot disable citation/schema,
  budget or independent-corroboration safeguards. Weights affect deterministic
  scoring; model output must not supply the authoritative weights.
- Keep legacy threshold-only PUT working by preserving the stored rubric when
  omitted. Reject unknown settings keys rather than silently accept fake edits.
  New UI requires a complete rubric from GET and cannot save against an older API.
- Keep all providers mocked for verification. Coordinate migration/backend/UI
  deployment; custom editing stays unavailable until matching API is deployed.
