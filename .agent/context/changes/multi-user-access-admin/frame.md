# Frame: Multi-user access, approval and spend controls

## Observed problem

The deployed Vite UI is still a prototype: it has no sign-in/session flow, displays a stale `frontend` browser title and `LOCAL API PREVIEW` label, and calls authenticated API routes without a bearer token. Linksifty's current personal MVP contract excludes public signup, account approval, administration and multi-user spend controls. Filip now wants the earlier multi-user product rules restored so other users can request access and process links under per-user cost limits.

## Intended outcome

Google OAuth through Supabase is the sole sign-in method. A new user starts pending, can try up to three links, and cannot submit more until an admin approves the account. Admins can approve or reject accounts and administer each user's monthly USD budget and usage, but cannot view another user's links or assessment content. The owner's verified Google identity is the initial administrator. Resend sends the user an email after approval. The deployed app title identifies Linksifty and no longer claims it is a local API preview.

## Affected users and systems

- Signed-out visitors, pending users, approved users and the initial admin.
- React/Vite frontend on Vercel; FastAPI API on Render; Supabase Auth and Postgres; OpenRouter for paid model calls; Resend for approval email.
- Current item submission, per-user settings, account access checks, and the future assessment/cost pipeline.

## Constraints

- Every item, note, assessment and chat operation remains scoped to its owner, including requests made by admins.
- Authorization data must not rely on user-editable Supabase `user_metadata`.
- Supabase service/secret keys, Resend key and OpenRouter key remain server-only.
- Pending trial allowance and paid monthly spend limits must be enforced transactionally on the server/database, including concurrent submissions or model calls.
- Approval state changes must not depend on email delivery succeeding.
- Backend rules remain outside FastAPI routes; provider adapters remain at the edge. Remote integrations are mocked in tests.
- Use the existing `settings.monthly_budget_cents` default of $10 as the initial budget unless a product decision changes it.

## Success criteria

- A visitor can authenticate with Google and receives a restored Supabase session in the Vercel app.
- Pending users see their approval status and trial balance; after three trial links they cannot submit more until approved.
- The initial admin can approve or reject accounts through the app; admin routes deny normal users and never expose user content.
- The approved user receives an email through Resend; a provider failure is visible to the admin and does not undo approval.
- Admins can see per-user month-to-date OpenRouter usage and set a monthly USD cap; parallel requests cannot exceed the cap.
- API requests carry a valid session, expired/invalid sessions return the user to sign-in, and signed-out UI shows no private data.
- Browser title says `Linksifty`; the stale local-preview label is removed or replaced by truthful account status.

## Assumptions and open questions

- “3 trial links” counts accepted submitted links for the account lifetime, including links that later require manual content; this avoids unlimited fetch work under retry.
- Monthly USD usage is the sum of actual provider-reported costs for that user's requests, including future assessment/chat calls, with conservative reservations before paid requests.
- The initial default budget remains $10 per calendar month; admins may set each account's cap, including zero.
- Resend sends only an approval confirmation to the user; no new-signup admin notice or rejection email is requested.
- The app currently has no completed paid processing pipeline, so a spend dashboard is meaningful only when usage capture and budget enforcement are integrated with each paid call.

## Competing explanations

- The `LOCAL API PREVIEW` label may be mistaken for a live environment indicator; code shows it is hard-coded in the UI.
- The browser title `frontend` comes from the Vite starter document, not Vercel or the custom domain.
- The user may expect the admin usage panel to show values immediately, but current code has no provider call ledger; actual usage should not be fabricated as zero spend when calls cannot yet be measured.
