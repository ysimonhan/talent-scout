# Bootstrap Checklist

Complete these steps when creating a new project from the template.

1. Rename the project in `pyproject.toml`, `README.md`, and `main.py`.
2. Choose the initial `[tool.repo_harness].level`.
3. Replace the starter notes in [architecture.md](architecture.md) with the real
   system boundaries and decisions.
4. Create the first ExecPlan if the initial work is multi-step or ambiguous.
5. Keep at least one smoke scenario under `evals/smoke/`.
6. Run `uv run python scripts/check_repo.py` and fix any missing contract files.
7. Record the first durable integration note or explicitly keep
   [references/integration-status.md](references/integration-status.md) as
   `no external integrations yet`.
8. Use `scripts/preflight.py` before shipping the first risky change.
9. If the project ships LLM or agent workflows, choose an observability/evals
   approach early and capture that decision in
   [references/llm-observability.md](references/llm-observability.md).
