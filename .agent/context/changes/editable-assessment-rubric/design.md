# Editable assessment descriptions and weights

## User intent and scope

The user wants the eight assessment criteria visible in Settings, with editable
descriptions and weights. The chosen scope keeps the eight existing criterion
IDs and names. Adding, removing or renaming criteria is outside this change.

The existing English interface will use English labels and default descriptions.
Users may write descriptions in their preferred language.

## Settings experience

Below the valuable-threshold field, show eight named entries, each with a short
editable description and a numeric weight. Explain that each criterion receives
1–5 points and that higher weights increase its contribution. Show the general
formula: sum(score × weight) / (5 × sum(weights)) × 100%.

Use one explicit Save settings action for the threshold and all eight entries.
Keep edits on save failure, show field validation and a clear save confirmation,
and prevent duplicate submissions. Preserve keyboard access, visible focus,
existing light/dark tokens and a narrow-screen layout without horizontal scroll.
Successful loading must precede editing; a load failure cannot overwrite stored
values with defaults. Do not trigger analysis, purchases or provider requests on
save. Settings belong only to the authenticated account, including admins.

Proposed validation: each description is 1–1000 nonblank characters, with no NUL;
each weight is an integer from 1 to 10. Zero does not disable criteria. Require
exactly one entry for every fixed ID, rejecting unknown or duplicate IDs.
Default weights remain 2 for evidence, credibility, replicability and absence of
conflict of interest, and 1 for the other four criteria.

## Meaning of descriptions

Descriptions guide what the model evaluates for each criterion. They are bounded
rubric data, separated from article text and from the non-editable grounding
instructions. They cannot override the requirements for eight scores, real
source excerpts, cost controls or the existing independent-corroboration guard.
Do not add automatic model retries or change the configured model.

## Persistence and analysis snapshots

Extend the owner-scoped settings API/storage with the complete rubric, using
existing routes, application services and repository adapters. Persist updates
atomically so threshold, descriptions and weights cannot be partially saved.
Validate in the API and database; restrict database functions under established
service-only RPC conventions and preserve owner checks and lock ordering.

Snapshot threshold and rubric together at the first model-budget reservation,
before inference. Pass that exact rubric to the provider and to deterministic
scoring. Store the snapshot with the completed assessment and expose it in the
detail response so the original weights and descriptions remain inspectable.
Recovering an interrupted attempt must reuse its stored snapshot, including
after the user's settings change. Different accounts must never share settings.

Legacy assessments and already-reserved jobs use the original fixed rubric;
they must never acquire today's edited settings. Jobs without a model reservation
take current settings at their first reservation. Explicit user-requested fresh
analysis follows existing resume/reset semantics; recovery must not silently
start another paid attempt. Historical scores and verdicts are not recalculated.

Use a forward migration, defaults/backfill for existing records and deployment
instructions. Preserve the existing pure domain scoring boundary; no FastAPI,
database or provider imports belong in scoring. Existing default scoring remains
identical. Do not deploy the migration or hosted services without authorization.

## Verification and delivery

Cover custom weighted totals, invalid rubrics, atomic owner-scoped updates,
snapshot consistency across settings edits/recovery, default legacy behavior,
model rubric delivery and preserved citation/corroboration guards. Frontend tests
cover all eight fields, save/load errors, validation and submitted values. Paid
and remote providers are mocked. Run backend tests, strict mypy, Ruff lint/format,
frontend tests/lint/build, toolkit check and a proportionate responsive UI check.

Update product/deployment documentation and the editable architecture data-flow
diagram with Archify during implementation. No new runtime dependency is needed.
Review the implementation and record any findings and dispositions before
completion. Push/deployment remain separate from local implementation.
