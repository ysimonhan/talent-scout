# Integration Guardrails

## Core Rule
Do not infer an external API shape from product naming, runtime needs, or partial familiarity.
Verify the exact API family and request/response format from official docs or the official SDK first.

## Required checks before implementation
1. Identify the exact API family and endpoint.
2. Confirm the canonical request shape from official docs.
3. Confirm the canonical response shape from official docs, the official SDK, or a live fixture.
4. Check whether async behavior is provider-side or app-side.
5. Prefer existing repo fixtures and parsers over inventing a new shape.

## Anti-patterns
- Do not assume "long-running" means the provider exposes async submit/poll endpoints.
- Do not mix API families from the same vendor.
- Do not translate a broker/job architecture into a vendor job architecture unless docs explicitly show that model.
- Do not switch between chat `messages` and top-level `input` formats without verifying the endpoint family.

## Architecture rule
If the product needs async UX, prefer an app-side queue/worker plus a local status endpoint before assuming the vendor provides an async polling API.

## Evidence rule
Before finalizing an integration, keep at least one of the following in the repo or artifacts:
- an official SDK example
- an official doc reference
- a captured live fixture

Use `uv run python scripts/capture_fixture.py ...` to store fixtures under `tests/fixtures/`
with a short metadata note.

## Perplexity-specific example
- Agent API uses `POST /v1/agent` or `/v1/responses`.
- Agent API requests use `input` plus `preset` and/or `model`.
- Sonar/chat-style `messages` belong to a different API surface and should not be mixed into Agent API integrations.
