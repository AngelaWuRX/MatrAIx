# chat_mental-health-support

- **Product under test:** an open-source mental-health support chatbot (Rogendo/Mental-health-Chatbot, https://github.com/Rogendo/Mental-health-Chatbot)
- **Upstream URL env:** `CHATBOT_UPSTREAM_MENTAL_HEALTH` (with default `baseUrl` in `input/chatbot.yaml`)
- **applicationId:** `mental_health_bot` — register in `application/playground/backend/service/chatbot_sidecar_service.py` `_SIDECAR_SPECS` as an upstream spec (compose_dir=None, primary_env=CHATBOT_UPSTREAM_MENTAL_HEALTH).

Verifier emits `task_outcome` / `conversation_summary` / `user_feedback` per the chatbot contract.
