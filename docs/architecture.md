# Architecture

## Current shape

This template is a small Python project managed by `uv`. It ships a progressive
harness that can grow from `core` to `critical` without replacing the template.

## Boundaries

- Application entry point: `main.py`
- Repository contract and hygiene checks: `scripts/check_repo.py`
- Smoke harness: `scripts/run_harness.py` and `evals/smoke/`
- Change evidence: `scripts/preflight.py` and `docs/change-reviews/`
- Integration evidence: `scripts/capture_fixture.py` and `tests/fixtures/`

## Design choices

- `AGENTS.md` is a router, not a handbook.
- `docs/` is the system of record for durable knowledge.
- Harness expectations scale by `[tool.repo_harness].level`.
- The `service` level is the first level that expects the full harness.
- LLM and agent projects should use provider routing instead of hardcoding one
  model backend throughout the codebase. See
  [references/provider-routing.md](references/provider-routing.md).

## Provider routing pattern

Agent code should choose an execution backend through a small routing policy:

```text
task profile -> routing policy -> provider adapter -> model/API call
```

Use this pattern when the project may need different backends for throughput,
governance, cost, or tool availability.

- Use direct Azure OpenAI for high-token, high-throughput, batchable, or
  long-context workloads.
- Use Langdock Chat or Agents APIs for smaller interactive workflows, internal
  assistants, and flows where Langdock governance, shared agents, or knowledge
  folders matter more than raw throughput.
- Keep direct provider-specific parameters at the adapter boundary.

## Current assumptions

- No external integrations are present yet.
- The starter smoke scenario validates the default entry point only.
- Real projects derived from this template should replace placeholders with
  project-specific architecture notes early.
- Provider references are templates. Replace placeholder endpoint values with
  project-local environment variables, never committed secrets.

## Open questions

- Which harness level does the new project need right now?
- Which project-specific constraints should move from chat into `docs/` first?
