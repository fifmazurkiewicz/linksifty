# Plan review — 2026-10-18

Outcome: approve local implementation. The owner's approved three-part scope is
represented in T1–T3. Interfaces stay within acquisition/provider/application
boundaries, scoring stays pure, and no credentials move into the browser.

Acceptance tests cover body-versus-preview, nested dependencies, safe complete
media, all-image extraction, lease/owner/expiry/budget admission and recovery.
Unknown schema, unsupported media and uncertain cost fail closed. Manual/external
work is explicit: deploy migration before backend, no live paid calls, verify
real Article payload and extraction quality after deployment. Browser/toolkit
unavailability must be reported rather than normalized into a pass.


## Captured compatibility amendment review

Outcome: approve the owner-approved bounded maintenance amendment T4.
The observed response supports code-entity handling and quoted media hydration;
model and twelve-image changes are explicit owner-approved scope. Tests must
protect exact code, malformed entities, missing expansions after one lookup,
conflicting versions, twelve-request and twelve-image ceilings, all-image vision
coverage, budgets and frontend wording. No new ledger shape or application
orchestration; preserve one generation and uncertain-result exclusion. Automated
checks and manual hosted acceptance are separate. Graft unavailable. No material
plan gaps or non-informational findings remain before test-first implementation.
