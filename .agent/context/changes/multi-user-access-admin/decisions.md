# Decisions: multi-user access, approval and spend controls

- Supabase Google OAuth is the only login method; request identity scopes only. Approved in conversation and recorded in the owner-approved design spec.
- New accounts are pending, with three accepted trial links total; batches that exceed the remaining allowance fail atomically. Approved in conversation and design spec.
- The owner's verified Google identity is the initial admin, configured privately through `LINKSIFTY_ADMIN_EMAIL`; never commit the actual address or server secrets.
- Resend sends a user-facing message only after account approval. Send failure leaves approval in place and is visible/retryable by an admin.
- Delivery is staged: account access/approval first; real per-user OpenRouter USD accounting second.
- Cost policy: OpenRouter inference only, UTC calendar month, $10.00 default, zero is valid, admin adjusts per-user cap; shared hosting, database and email bills are excluded.
- User-level cap precision: integer cents; per-call usage and reservations preserve sub-cent USD precision.
- Admin features manage account state and budgets/usage but never provide access to another user's content.
- Approved spec leaves long-term usage retention and exact verified Resend sender identity as pre-deployment operational decisions; implementation shows current UTC month only and does not prune ledger rows.
