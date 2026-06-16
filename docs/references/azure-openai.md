# Azure OpenAI

Use this file for Azure OpenAI provider notes in projects derived from this
template. Replace placeholders with project-local values and keep real secrets in
`.env`, Azure Key Vault, or the deployment platform secret store.

## Endpoint And Auth

Recommended environment variables:

```text
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_KEY=<secret>
```

Azure OpenAI REST calls use the `api-key` header:

```text
api-key: <AZURE_OPENAI_KEY>
Content-Type: application/json
```

Do not use `Authorization: Bearer` unless the project is explicitly using an
Azure AD token flow.

## API Surfaces

### Chat Completions

Use Chat Completions for compatibility with older code or simple chat adapters:

```text
POST {AZURE_OPENAI_ENDPOINT}openai/deployments/{deployment}/chat/completions?api-version=2024-10-21
```

PowerShell shape:

```powershell
$body = @{
  messages = @(
    @{ role = "user"; content = "Say hello." }
  )
  max_completion_tokens = 512
} | ConvertTo-Json -Depth 20

curl.exe -X POST "$($env:AZURE_OPENAI_ENDPOINT)openai/deployments/gpt-5.4/chat/completions?api-version=2024-10-21" `
  -H "api-key: $($env:AZURE_OPENAI_KEY)" `
  -H "Content-Type: application/json" `
  -d $body
```

Observed compatibility rule:

- Some non-reasoning deployments accept classic `max_tokens`.
- Reasoning deployments can reject `max_tokens` and require
  `max_completion_tokens`.
- The parameter is singular: `max_completion_tokens`, not
  `max_completions_tokens`.

### Responses API

Prefer Responses for new direct Azure OpenAI agents:

```text
POST {AZURE_OPENAI_ENDPOINT}openai/responses?api-version=2025-04-01-preview
```

Responses uses `input`, not Chat Completions `messages`, and uses
`max_output_tokens`, not `max_tokens` or `max_completion_tokens`.

PowerShell shape:

```powershell
$body = @{
  model = "gpt-5.4"
  input = "Say hello."
  max_output_tokens = 512
} | ConvertTo-Json -Depth 20

curl.exe -X POST "$($env:AZURE_OPENAI_ENDPOINT)openai/responses?api-version=2025-04-01-preview" `
  -H "api-key: $($env:AZURE_OPENAI_KEY)" `
  -H "Content-Type: application/json" `
  -d $body
```

## Reasoning Token Budget Finding

Reasoning models can spend part or all of the completion/output budget on
internal reasoning before producing visible text.

Observed failure shape:

```json
{
  "finish_reason": "length",
  "message": { "content": "" },
  "usage": {
    "completion_tokens_details": {
      "reasoning_tokens": 20
    }
  }
}
```

Interpretation:

- Empty content with `finish_reason = "length"` and reasoning tokens equal to the
  budget is a token budget/configuration issue.
- Start short reasoning tasks at `max_completion_tokens` or `max_output_tokens`
  of at least 512.
- Use larger budgets, often 1000+ tokens, for planning, synthesis, long-context
  analysis, or tool-heavy steps.

## Batch API

Use Batch for offline workloads, not interactive agents.

Good fits:

- interview analysis backfills
- transcript or document extraction
- eval suites
- bulk classification
- synthetic data generation

Poor fits:

- live chat
- tool loops that need immediate follow-up
- user-facing workflows waiting on each step

Azure Batch requires a deployment configured for `GlobalBatch` or
`DataZoneBatch`. A standard high-limit deployment is not automatically a batch
deployment.

### JSONL Request Shape

Each line in the input `.jsonl` file is one request:

```jsonl
{"custom_id":"case-001","method":"POST","url":"/v1/chat/completions","body":{"model":"<batch-deployment>","messages":[{"role":"user","content":"Summarize this transcript."}],"max_completion_tokens":1200}}
{"custom_id":"case-002","method":"POST","url":"/v1/responses","body":{"model":"<batch-deployment>","input":"Extract risks from this note.","max_output_tokens":1200}}
```

Join results by `custom_id`, not output order.

### Batch Flow

1. Upload a JSONL file with purpose `batch`.
2. Create a batch with `input_file_id`, `endpoint`, and
   `completion_window: "24h"`.
3. Poll the batch status.
4. Download the output file.
5. Inspect the error file if present.

Common v1 endpoint shapes:

```text
POST /openai/v1/files
POST /openai/v1/batches
GET  /openai/v1/batches/{batch_id}
GET  /openai/v1/files/{output_file_id}/content
POST /openai/v1/batches/{batch_id}/cancel
```

Documented design constraints to check before implementation:

- `completion_window` is `24h`
- input file limit is 200 MB without Bring Your Own Storage
- maximum requests per file is 100,000
- batch quota is separate and based on enqueued tokens
- batch pricing and availability depend on the Azure deployment type and region

## Adapter Rules

- Keep Azure-specific parameters inside the Azure adapter.
- Log deployment, served model when returned, request ID, finish/status reason,
  token usage, and reasoning-token usage when present.
- Classify length-limited empty output separately from safety filtering,
  transport failure, and model-quality failure.
- Never commit real endpoint hostnames, keys, or deployment IDs unless the
  repository is explicitly private and approved for internal infrastructure
  metadata.

## Sources

- Azure OpenAI Responses API guide:
  <https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/responses>
- Azure OpenAI Batch guide:
  <https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/batch>
- Azure OpenAI preview REST reference:
  <https://learn.microsoft.com/en-us/azure/foundry/openai/reference-preview>
