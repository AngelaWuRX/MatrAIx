# chatbot-api-sidecar_mental-health-support

Local HTTP chatbot product under test for `chat_mental-health-support`.
Persona agent runtime: `application/shared-chat-persona`.

| Field | Value |
|---|---|
| Task | `chat_mental-health-support` |
| `applicationId` | `mental_health_bot` |
| Compose service | `mental-health-chatbot` |
| Host port | 8906 |
| Upstream override env | `CHATBOT_UPSTREAM_MENTAL_HEALTH` |

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
docker compose up --build mental-health-chatbot
curl -s localhost:8000/ready
curl -s -X POST localhost:8000/v1/messages \
  -H 'content-type: application/json' -d '{"message":"hello"}'
```

Deterministic, rule-based **smoke-run** product in the same tier as
`chatbot-api-sidecar_acme-support-api`. Modeled on Rogendo/Mental-health-Chatbot (https://github.com/Rogendo/Mental-health-Chatbot); point `CHATBOT_UPSTREAM_MENTAL_HEALTH`
at a deployed instance to run the task against the real product instead.
