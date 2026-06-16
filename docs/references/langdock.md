# Langdock

Use Langdock when a project benefits from the enterprise platform layer:
workspace governance, managed agents, shared tools, knowledge folders, and
OpenAI-compatible chat behind Langdock authentication.

## Base URLs

Cloud:

```text
https://api.langdock.com
```

Dedicated deployment:

```text
https://<deployment-url>/api/public
```

For dedicated deployments, include `/api/public` in the base URL. Missing this
path is a common source of authentication errors.

Prefer the `eu` region unless the project has an explicit reason to use another
region.

## Authentication

Langdock API calls use a Bearer token:

```text
Authorization: Bearer <LANGDOCK_API_KEY>
Content-Type: application/json
```

Do not call Langdock directly from browser/client-side code. Route requests
through a backend so the API key stays server-side.

## OpenAI Chat Completion API

Endpoint:

```text
POST /openai/{region}/v1/chat/completions
```

Example base URL for the OpenAI Python SDK:

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.langdock.com/openai/eu/v1",
    api_key="<LANGDOCK_API_KEY>",
)

completion = client.chat.completions.create(
    model="gpt-5-mini",
    messages=[
        {"role": "user", "content": "Write a concise project summary."}
    ],
)
print(completion.choices[0].message.content)
```

Use this API for simple OpenAI-compatible chat requests where Langdock routing,
workspace controls, and EU governance matter more than direct Azure throughput.

Important differences from raw OpenAI:

- Available models are workspace-dependent. Query
  `GET /openai/{region}/v1/models`.
- `reasoning_effort` supports `none`, `minimal`, `low`, `medium`, `high`, and
  `xhigh` where supported by the selected model.
- `n`, `service_tier`, `parallel_tool_calls`, and `stream_options` are not
  supported.
- Rate limits are documented at workspace/model level, not per API key.

## Agents API

Endpoint:

```text
POST /agent/v1/chat/completions
```

The Agents API chats with a pre-configured Langdock agent or with an inline
temporary agent configuration. It uses the Vercel AI SDK `UIMessage` format, not
classic OpenAI `messages`.

Minimal request:

```json
{
  "agentId": "agent_123",
  "messages": [
    {
      "id": "msg_1",
      "role": "user",
      "parts": [
        { "type": "text", "text": "Hello, how can you help me?" }
      ]
    }
  ],
  "stream": false
}
```

Common request fields:

| Field | Notes |
| --- | --- |
| `agentId` | ID of an existing shared agent. Use either `agentId` or `agent`. |
| `agent` | Inline temporary agent configuration. Use either `agent` or `agentId`. |
| `messages` | Required array of Vercel AI SDK `UIMessage` objects. |
| `stream` | Optional streaming flag. |
| `output` | Optional structured output specification. |
| `maxSteps` | Optional max tool steps, documented range 1-20. |
| `imageResponseFormat` | `url` or `b64_json` for image-generating agents. |

User message shape:

```json
{
  "id": "msg_1",
  "role": "user",
  "parts": [
    { "type": "text", "text": "Please analyze this document." }
  ],
  "metadata": {
    "attachments": ["<uploaded-attachment-uuid>"]
  }
}
```

The docs describe `UIMessage.parts` for conversation history and tool/source
state. The standard completion response is documented as a `messages` array with
assistant `content`, plus an `output` field when structured output is requested.
When building multi-turn chat, preserve the provider's returned message shape
instead of converting it too early.

## Attachments And Tools

- Upload files through the Upload Attachment API and reference returned UUIDs in
  `metadata.attachments`.
- Do not use `type: "file"` parts for uploaded attachments; that form is for
  inline file references.
- Langdock UI tools are called Actions. API tool use requires a preselected
  shared connection.
- Tools that require human confirmation do not work through the API because they
  require manual approval in the Langdock UI.

## When To Use Langdock

Prefer Langdock for:

- smaller interactive consultant workflows
- internal assistants whose behavior should be managed in the Langdock UI
- workflows needing shared agents, Actions, knowledge folders, or attachments
- governance-first routes where workspace-level controls matter

Prefer direct Azure OpenAI for:

- high-token interview or transcript analysis
- high-throughput backfills
- batchable offline jobs
- cases that need direct Azure deployment control

## Error And Limit Handling

Common API statuses:

- `400`: invalid request, malformed message format, inaccessible agent, or agent
  not shared with the API key
- `401`: invalid or missing API key
- `429`: rate limit exceeded
- `500`: server error

Operational rules:

- Log `provider=langdock`, endpoint family, model or agent ID, HTTP status,
  retry count, and request/response IDs when available.
- Treat `400` and `401` as non-retryable until the request or credentials are
  fixed.
- Retry `429` and transient `5xx` responses with bounded backoff.
- Keep browser clients away from the API key; call Langdock from backend code.

## Sources

- Langdock OpenAI Chat completion docs:
  <https://docs.langdock.com/api-endpoints/completion/openai>
- Langdock Agents Completions API docs:
  <https://docs.langdock.com/api-endpoints/agent/agent>
- Context Hub document used: `langdock/langdock`, fetched with
  `chub get langdock/langdock --lang py` on 2026-04-24.
