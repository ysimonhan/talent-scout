# Docs Index

Use this as the repository table of contents.

## Core records

- [architecture.md](architecture.md): current system shape, boundaries, and key
  decisions
- [reliability.md](reliability.md): rollout, failure-mode, and containment
  defaults
- [quality-score.md](quality-score.md): current quality bar and maturity gaps
- [golden-principles.md](golden-principles.md): stable engineering defaults that
  should survive across features
- [bootstrap-checklist.md](bootstrap-checklist.md): what every new project
  should set up on day 1

## Planning

- [PLANS.md](PLANS.md): when ExecPlans are required and how to keep them useful
- [exec-plans/template.md](exec-plans/template.md): self-contained plan template
- [exec-plans/active/README.md](exec-plans/active/README.md): active work area
- [exec-plans/completed/README.md](exec-plans/completed/README.md): completed
  work archive
- [references/openai-codex-execplans-reference.md](references/openai-codex-execplans-reference.md):
  full OpenAI reference text that informed the local ExecPlan rules

## Operational guidance

- [agent-responsibly.md](agent-responsibly.md): human judgment expectations for
  agent-assisted changes
- [integration-guardrails.md](integration-guardrails.md): rules for third-party
  APIs and async assumptions
- [external-apis-railway-deploy-longjobs.md](external-apis-railway-deploy-longjobs.md):
  accumulated integration and runtime learnings

## References and generated outputs

- [references/README.md](references/README.md): durable source notes and
  integration references
- [references/integration-status.md](references/integration-status.md): explicit
  record of whether the project has external integrations yet
- [references/provider-routing.md](references/provider-routing.md): routing
  policy for Azure OpenAI, Langdock, and other LLM execution backends
- [references/azure-openai.md](references/azure-openai.md): Azure OpenAI
  endpoint, Responses, Chat Completions, and Batch notes
- [references/langdock.md](references/langdock.md): Langdock Chat and Agents
  API notes
- [references/llm-observability.md](references/llm-observability.md): optional
  guidance for LLM and agent observability decisions
- [generated/README.md](generated/README.md): generated outputs location

## Change evidence

- [change-reviews/README.md](change-reviews/README.md): preflight review output
  location
