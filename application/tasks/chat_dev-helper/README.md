# chat_dev-helper

- **Product under test:** a local coding-help chatbot sidecar, modeled on LibreChat (danny-avila/LibreChat, https://github.com/danny-avila/LibreChat)
- **Sidecar:** `application/chatbot-api-sidecar_dev-helper` — compose service `dev-help-chatbot`, host port 8909
- **applicationId:** `dev_helper_bot`, registered in `application/playground/backend/service/chatbot_sidecar_service.py` `_SIDECAR_SPECS`
- **Upstream URL env:** `CHATBOT_UPSTREAM_DEV` — point this at a deployed LibreChat instance to run against the real product instead of the bundled sidecar

Verifier emits `task_outcome` / `conversation_summary` / `user_feedback` per the chatbot contract.
