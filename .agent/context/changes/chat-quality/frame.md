# Chat quality — 2026-10-19

Observed in the owner-provided transcript: safe comparison questions receive a
near-identical article summary; Polish questions receive English answers. Earlier
English attempts failed with classifier uncertainty (diagnosed separately).
The owner requests a better chat model and explicitly selected Claude Sonnet 5.5
over the budget alternative.

Success: chat uses the selected model independently of assessments; the latest
question and its language drive the answer, short follow-ups get focused replies,
and ambiguous comparison names are clarified without invented facts. Existing
evidence validation, owner scope, classifier, one-search cap, exact budget and
no-retry rules remain intact. Tests must mock providers. No paid quality trial,
hosted setting change or new push is authorized by the model preference alone.

Competing explanations: model capability, over-dominant English saved summaries,
implicit language inference, question/history serialization and prompt weakness.
Code reads show frontend sends the actual latest question and renders saved answer
text; no UI summary fallback was found. The model is shared with assessments and
is currently pinned to gpt-4o-mini. The classifier language is used for refusals
but not explicitly carried into relevant answer generation. These findings do
not prove that a model swap alone fixes response quality.

Bounded change to the existing adapter and composition; no new infrastructure,
agent framework, provider credential, database schema or user workflow.
