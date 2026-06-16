# Quality Score

Use this file to score the current state of the project and make gaps explicit.

## Current target

- Harness level: `core`
- Desired next level: `integration` only when the project adds external systems

## Scoring rubric

- 0: prototype works once, but behavior is mostly implicit
- 1: code, tests, and docs exist, but failure handling is thin
- 2: repo checks, smoke coverage, and durable notes are in place
- 3: rollout, rollback, and integration evidence are explicit
- 4: critical-path behavior is observable, rehearsed, and hard to regress

## Minimum bar by level

- `core`: score 1 or better
- `integration`: score 2 or better
- `service`: score 3 or better
- `critical`: score 4 or a documented gap plan

## Review prompts

- What part of the behavior still lives only in chat history?
- Which risky path lacks a smoke scenario, fixture, or rollback note?
- Which docs would a new agent need in order to resume work cold?
