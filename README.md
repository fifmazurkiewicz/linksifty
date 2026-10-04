# Linksifty

Linksifty is an agent-toolkit-assisted implementation of a web app that turns saved article and X links into source-grounded notes and a repeatable value verdict.

It is deliberately paired with a separate implementation of the same product that does not use agent-toolkit. The product contract is shared; workflow, evidence, and delivery process are the comparison surface.

## Start here

- [Product vision](docs/product/vision.md)
- [Architecture overview](docs/architecture/overview.md)
- [MVP roadmap](docs/roadmap.md)
- [Agent instructions](AGENTS.md)

## Local checks

```sh
uv run pytest
uv run mypy src
uv run ruff check .
uv run ruff format --check .
```

If the local agent-toolkit checkout is available, also run `agent-toolkit check` for configuration drift.
