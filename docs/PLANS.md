# ExecPlans

This repository uses a distilled ExecPlan contract adapted from OpenAI's Codex
Execution Plans guidance. Follow this file first. The full source wording is
stored for reference in
[references/openai-codex-execplans-reference.md](references/openai-codex-execplans-reference.md).

An ExecPlan is a self-contained, living implementation plan for work that is
too large, risky, or ambiguous to trust to chat context alone. A good ExecPlan
lets a novice resume the work with only the current working tree and the plan
file.

## When to use an ExecPlan

Use an ExecPlan when the work is:

- multi-hour or multi-step
- ambiguous enough that an agent could lose context mid-flight
- likely to touch several files, systems, or failure modes
- important enough that another person or agent may need to resume it later

Harness-level guidance:

- `core`: optional
- `integration`: use one for risky or ambiguous integration work
- `service`: default for non-trivial work
- `critical`: default for non-trivial work and expected for risky changes

## Non-negotiable rules

- The plan must be self-contained. Do not assume the reader remembers prior
  chats, prior plans, or external docs.
- The plan must explain why the change matters in user terms before describing
  the edits.
- The plan must define jargon in plain language. If you use terms like `smoke
  test`, `fixture`, or `rollback`, explain what they mean in this repository.
- The plan must describe observable outcomes, not only code edits. A reader
  should know what to run and what success looks like.
- The plan must be a living document. Update it as decisions change, work
  progresses, and surprises appear.
- The plan must name exact repository-relative files, scripts, commands, and
  validation steps.
- The plan must describe safe retry or recovery steps for risky work.

## Required sections

Every ExecPlan in this repository must include these sections:

- `Purpose / Big Picture`
- `Progress`
- `Surprises & Discoveries`
- `Decision Log`
- `Outcomes & Retrospective`
- `Context and Orientation`
- `Plan of Work`
- `Concrete Steps`
- `Validation and Acceptance`
- `Idempotence and Recovery`
- `Artifacts and Notes`

Include `Interfaces and Dependencies` when the work adds or changes important
APIs, command surfaces, or module boundaries. Use milestones when they improve
clarity or reduce risk, but make each milestone independently verifiable.

## Repository-specific formatting

- Checked-in ExecPlans are normal Markdown files. Do not wrap the whole file in
  one outer code fence.
- Write in prose first. Use checklists only in the `Progress` section.
- The `Progress` section must use checkboxes with timestamps and must reflect
  reality at every stopping point.
- Keep commands and short transcripts concise. Indented examples are usually
  enough.
- Prefer repetition over ambiguity. If a fact matters, restate it in the plan
  instead of sending the reader to another doc and hoping they infer it.

## Working rules

- Start from [exec-plans/template.md](exec-plans/template.md).
- Put active plans under `docs/exec-plans/active/`.
- Move completed plans to `docs/exec-plans/completed/`.
- If the plan changes direction, record the decision in `Decision Log` and
  update the affected sections so the file stays internally consistent.
- If implementation reveals a bug, performance constraint, or library quirk,
  record it in `Surprises & Discoveries` with short evidence.
- At meaningful completion points, update `Outcomes & Retrospective` with what
  shipped, what remains, and what was learned.
