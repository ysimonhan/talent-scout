# Engineering Learnings

Capture durable lessons here as the project evolves.

## External API Integration

- When integrating with third-party AI APIs, do not rely only on documentation for response shape.
- First capture a real response with a minimal probe script if behavior is unclear.
- Treat structured output requests as best-effort: parse canonical structured fields first, then fall back to message text/content when necessary.
- Log enough of upstream error bodies to diagnose failures, but never log secrets.

## Long-Running Analysis Jobs

- Persist job state, codebook output, failure logs, and generated artifacts incrementally to disk.
- Design batch jobs for partial success: one failed transcript must not discard successful analyses.
- Record failed transcript IDs and error messages in a dedicated failure artifact.
- On startup, recover or mark interrupted jobs explicitly rather than leaving them in an ambiguous running state.

## Deployment and Runtime

- In Railway, use `sh -c` when shell expansion is required in the start command.
- Keep all durable runtime data under the configured data directory (`DATA_DIR`, production mount typically `/data`).
- Distinguish clearly between local app failures and upstream provider outages/timeouts.

## Testing Expectations

- For integration fixes, add tests that reflect real captured upstream payloads.
- Mock external network calls at the boundary function.
- Cover retries, partial success, failure logging, and artifact generation in tests.
