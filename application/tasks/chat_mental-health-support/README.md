# chat_mental-health-support

- **Product under test:** a local mental-health support chatbot sidecar, modeled on Rogendo/Mental-health-Chatbot (https://github.com/Rogendo/Mental-health-Chatbot)
- **Sidecar:** `application/chatbot-api-sidecar_mental-health-support` — compose service `mental-health-chatbot`, host port 8906
- **applicationId:** `mental_health_bot`, registered in `application/playground/backend/service/chatbot_sidecar_service.py` `_SIDECAR_SPECS`
- **Upstream URL env:** `CHATBOT_UPSTREAM_MENTAL_HEALTH` — point this at a deployed instance to run against the real product instead of the bundled sidecar

Verifier emits `task_outcome` / `conversation_summary` / `user_feedback` per the chatbot contract.
