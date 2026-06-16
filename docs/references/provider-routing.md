# Provider Routing

Use provider routing when an agent system may need more than one model backend.
Do not bake Azure OpenAI, Langdock, Anthropic, or any other provider into core
agent logic.

## Core Pattern

```text
task profile -> routing policy -> provider adapter -> model/API call
```

The routing policy owns the decision. Provider adapters own request formatting,
authentication, retries, response normalization, and provider-specific logging.

## Default Routing Policy

| Task profile | Preferred backend | Why |
| --- | --- | --- |
| High-token interview analysis, transcript synthesis, document extraction, batch evals | Azure OpenAI | Higher token throughput, direct control over deployments, and Batch support for offline jobs. |
| Small interactive assistant, consultant-facing chat, internal workflow with managed agent config | Langdock Agents API | Langdock manages the agent, tools, knowledge folders, and workspace governance. |
| Simple OpenAI-compatible chat call through enterprise platform | Langdock OpenAI Chat Completion API | OpenAI-compatible request shape with Langdock auth, workspace controls, and EU routing. |
| Experimental capability not exposed by Langdock or Azure | Direct provider adapter | Keep experiments isolated until the capability becomes part of the standard routing policy. |

## Routing Inputs

Classify each model call before selecting a backend:

- token volume and expected context size
- interactivity: synchronous user flow vs offline job
- tool and knowledge requirements
- data residency and governance requirements
- cost sensitivity
- retry and failure tolerance
- need for structured output
- model capability requirements

## Adapter Contract

Every provider adapter should normalize:

- request ID or response ID
- model or deployment name
- status or finish reason
- output text
- structured output when requested
- token usage when available
- retryable vs non-retryable errors
- content filtering or policy blocks

Keep raw provider responses available in logs or traces when safe, but do not
make downstream business logic depend on provider-specific response shapes.

## Anti-Patterns

- Calling providers directly from business logic.
- Mixing Langdock UI agents and direct Azure model calls in the same function.
- Falling back from one provider to another without recording the tradeoff.
- Treating Batch as an interactive agent runtime.
- Storing real API keys, deployment URLs, or internal IDs in committed docs.

## Project Setup Checklist

1. Pick the first backend explicitly in `docs/architecture.md`.
2. Record provider-specific request quirks under `docs/references/`.
3. Add environment variables to `.env.example`, not real `.env` values.
4. Add one smoke scenario per routed workflow.
5. Log enough metadata to tell provider failures apart from prompt/model issues.
