# Privacy And Sanitization

This repository is a sanitized public case study.

## Public Data Rules

- Use synthetic supplier, buyer, and workflow data only.
- Do not include client names, private URLs, real contact details, real company data, or private process screenshots.
- Do not preserve private repository history.
- Do not commit `.env`, logs, generated reports, or local artifacts.

## Review Checklist

Before publishing:

- Run a targeted scan for old client names, employer names, private URLs, credentials, and phone-number patterns.
- Run `uv run pytest`.
- Run `uv run ruff check .`.

Any sensitive match must be reviewed before publication.
