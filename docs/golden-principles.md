# Golden Principles

- Keep `AGENTS.md` short and route to durable docs instead of copying prose.
- Prefer a script or test over a reminder in chat when a rule matters twice.
- Scale the harness by risk and lifespan, not by repo existence.
- Capture real fixtures before you harden parsers or error handling.
- Treat green tests as necessary but not sufficient for risky changes.
- Leave behind rollout, detection, and rollback thinking for work with blast
  radius.
- Keep generated artifacts out of the system of record.
- If a rule becomes important for every change, move it into the repo contract.
