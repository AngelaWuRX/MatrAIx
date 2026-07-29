# chatbot-api-sidecar_retail-order-support

Local HTTP chatbot product under test for `chat_retail-order-support`.
Persona agent runtime: `application/shared-chat-persona`.

| Field | Value |
|---|---|
| Task | `chat_retail-order-support` |
| `applicationId` | `retail_support_bot` |
| Compose service | `retail-support-chatbot` |
| Host port | 8907 |
| Upstream override env | `CHATBOT_UPSTREAM_RETAIL` |

Registered in `application/playground/backend/service/chatbot_sidecar_service.py`
`_SIDECAR_SPECS`, so the Playground can start it directly.

**One service per directory.** The runtime resolves a single primary service
per `local_compose` dir, so each grounded chat task ships its own sidecar
directory rather than sharing one multi-service compose file.

## Protocol

- `POST /v1/messages` — `{sessionId, message, ...}` -> `{sessionId, reply, turn, recommendedItems}`.
  `turn` is an **object** (`conversationId` / `assistantMessage` / `turnIndex` /
  `recommendedItems`) because the eval harness merges it over the response to
  resolve `structuredExposure` selectors.
- `GET /health` — `{status, bot}`
- `GET /ready`, `GET /v1/ready` — `{status, bot, capabilities}`; exercises the
  reply path, which is what Playground probes for "Service up".

## Run locally

```bash
docker compose up --build retail-support-chatbot
curl -s localhost:8000/ready
curl -s -X POST localhost:8000/v1/messages \
  -H 'content-type: application/json' -d '{"message":"hello"}'
```

Deterministic, rule-based **smoke-run** product in the same tier as
`chatbot-api-sidecar_acme-support-api`. Modeled on chatwoot/chatwoot (https://github.com/chatwoot/chatwoot); point `CHATBOT_UPSTREAM_RETAIL`
at a deployed instance to run the task against the real product instead.
