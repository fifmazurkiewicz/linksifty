# Trailing citation omission markers — 2026-10-16

Implemented the user's approved bounded fix for the observed model quote ending
in `...`. Match the original quote first, then permit removing one trailing `...`
or `…` only when the entire remaining quote matches its attributed source.
Preserve whitespace re-anchoring and the minimum 10-character quote length;
reject changed words/case, internal omissions and cross-source substitution.

Strengthened the existing model prompt and added a distinct trace repair flag.
No dependencies, migrations, model changes or automatic paid retries. Existing
failed results remain unchanged. Graft is unavailable; focused searches located
the matcher, its adapter caller and processing offset checks.

Verification is recorded in [evidence](evidence.md). Hosted deployment and paid
verification have not been performed for this fix.
