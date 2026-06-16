# Reliability

## Defaults

- Add timeouts to network calls.
- Keep retries explicit, bounded, and testable.
- Gate risky behavior behind a feature flag or environment variable.
- Log enough context to debug failures without leaking secrets.
- Prefer failure containment over silent retries or hidden background work.

## Rollout expectations

- Document rollout behavior before shipping risky changes.
- Keep at least one smoke scenario that proves the happy path still works.
- Use `scripts/preflight.py` for changes that can affect users, money, data, or
  operations.

## Failure handling

- Distinguish local failures from upstream failures.
- Record real integration fixtures before hardening parsers.
- Prefer partial success and explicit recovery paths for long-running jobs.
- For LLM calls, log provider, model or deployment, request ID when available,
  token usage, finish/status reason, retry count, and whether the returned text
  was empty.
- Treat empty output from a reasoning model with a length/status limit and high
  reasoning-token usage as a token budget/configuration failure before treating
  it as a model quality issue.
- Retry transport failures, rate limits, and transient server errors with bounded
  backoff. Do not blindly retry schema errors, auth errors, content-filtered
  outputs, or malformed requests.
- Fallback between providers only when the task can tolerate the quality,
  governance, latency, and cost differences.

## Rollback

- Every risky change should have a credible rollback or disable path.
- If the rollback depends on config, document the exact switch in the preflight.

## Drift control

- Use `scripts/check_repo.py` to catch missing evidence and broken doc links.
- Use `scripts/cleanup_generated.py` to clear generated artifacts that should
  not become durable records.
