# chatbot-api-sidecar_grounded-chatbots

Local HTTP chatbot product under test for the five grounded `chat_*` persona
tasks. Persona agent runtime: `application/shared-chat-persona`.

One image (`./grounded-chatbot`) serves all five bots; the active persona is
selected per service by the `SIDECAR_BOT` environment variable. Each task pins
one bot via the `applicationId` in its `input/chatbot.yaml`, registered in
`application/playground/backend/service/chatbot_sidecar_service.py`.

| Task | `applicationId` (`SIDECAR_BOT`) | compose service | host port | upstream env |
|---|---|---|---|---|
| `chat_mental-health-support` | `mental_health_bot` | `mental-health-support-chatbot` | 8906 | `CHATBOT_UPSTREAM_MENTAL_HEALTH` |
| `chat_retail-order-support` | `retail_support_bot` | `retail-support-chatbot` | 8907 | `CHATBOT_UPSTREAM_RETAIL` |
| `chat_clinic-appointment` | `clinic_booking_bot` | `clinic-booking-chatbot` | 8908 | `CHATBOT_UPSTREAM_CLINIC` |
| `chat_budget-coach` | `budget_coach_bot` | `budget-coaching-chatbot` | 8909 | `CHATBOT_UPSTREAM_BUDGET` |
| `chat_dev-helper` | `dev_helper_bot` | `dev-help-chatbot` | 8910 | `CHATBOT_UPSTREAM_DEV` |

## Protocol

Matches each task's `input/chatbot.yaml`:

- `POST /v1/messages` — body `{sessionId, message, ...}` → `{sessionId, reply, turn, recommendedItems}`
- `GET /health` — `{status: "ok", bot: <SIDECAR_BOT>}`

## Run one bot locally

```bash
docker compose up --build dev-help-chatbot
# then, from the container network:
curl -s localhost:8000/health
curl -s -X POST localhost:8000/v1/messages \
  -H 'content-type: application/json' \
  -d '{"message":"KeyError: name on data[\"user\"][\"name\"] in Python"}'
```

This is a deterministic, rule-based **smoke-run** product in the same tier as
`chatbot-api-sidecar_acme-support-api`. The task READMEs name the real
open-source products each scenario is modeled on (LibreChat, Rasa, Chatwoot,
OpenDialog, Rogendo/Mental-health-Chatbot); an operator can swap in one of
those by pointing the task's `CHATBOT_UPSTREAM_*` env at its endpoint.
