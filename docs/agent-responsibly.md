# Agent-Responsible Workflow

This template is for learning fast without blindly shipping whatever an agent generated.

The rule is simple: use agents for speed, but make the human own the mental model, the risks,
and the ship decision.

## When to stop and think harder

Run a preflight before shipping any change that touches:

- external APIs
- retries, caching, queues, or background jobs
- auth, billing, or user data
- deployment config, infra, or database access
- feature flags or rollout behavior

Command:

```powershell
uv run python scripts/preflight.py
```

This writes a review artifact under `docs/change-reviews/` so the reasoning is durable instead
of living only in chat history. The review should capture rollout behavior, detection signals,
commands run, rollback, and the evidence or fixtures that justify the change.

## What good leverage looks like

Before you merge or deploy, you should be able to answer:

- What does this change do?
- How does it behave once rolled out?
- What can break, and who feels it first?
- How is blast radius limited?
- How do I detect a bad rollout quickly?
- How do I turn it off, rollback, or contain it?

If you cannot explain those from memory, you are still relying on the agent.

## Template defaults to prefer

For new prototypes, bias toward these defaults:

- add timeouts to network calls
- keep retries explicit and bounded
- capture real API fixtures before locking parser logic
- gate risky behavior behind an env var or feature flag
- log enough context to debug failures without leaking secrets
- test failure paths, not only happy paths
- document production assumptions in `docs/`

## Learning loop

After an incident, surprise, or integration mismatch:

1. Save the lesson in `docs/`.
2. Add or tighten a test.
3. Move the new rule into `AGENTS.md` if it should apply every time.
4. Prefer a script or check over a reminder in prose when possible.
