# LLM Observability

Use this note only for projects that ship LLM or agent behavior in environments
where traceability, prompt changes, evaluation quality, or user feedback matter.

## When to care

Consider adopting an LLM observability stack when the project has one or more of
these properties:

- production traffic or real users
- prompts or tool orchestration that will change over time
- non-trivial failure analysis needs
- evaluation, regression detection, or human feedback loops
- cost, latency, or reliability requirements that need measurement

## What to decide

Document the answers to these questions before wiring in a vendor:

- Which environments need tracing: local, staging, production, or all three?
- Which objects must be observable: requests, traces, spans, prompts, scores,
  sessions, or datasets?
- Which data must be redacted or excluded?
- Which workflows need evaluation: offline evals, online monitoring, or both?
- Who will use the system: engineers only, or also product and ops?

## Vendor note

Langfuse is a strong option for agent and LLM production use cases because it
covers tracing, prompt management, evals, and feedback loops in one system.
Use it when that stack matches the project needs. Do not treat it as mandatory
for every repository or every harness level.

## Template guidance

- `core`: usually unnecessary
- `integration`: optional if the project already depends on an external LLM API
- `service`: reasonable to adopt when LLM behavior is part of the product
- `critical`: observability is required, but the exact vendor should still be a
  conscious choice
