# chat_retail-order-support

- **Product under test:** a local order-support chatbot sidecar, modeled on Chatwoot (chatwoot/chatwoot, https://github.com/chatwoot/chatwoot)
- **Sidecar:** `application/chatbot-api-sidecar_grounded-chatbots` — compose service `retail-support-chatbot` (`SIDECAR_BOT=retail_support_bot`), host port 8907
- **applicationId:** `retail_support_bot`, registered in `application/playground/backend/service/chatbot_sidecar_service.py` `_SIDECAR_SPECS`
- **Upstream URL env:** `CHATBOT_UPSTREAM_RETAIL` — point this at a deployed Chatwoot instance to run against the real product instead of the bundled sidecar

Verifier emits `task_outcome` / `conversation_summary` / `user_feedback` per the chatbot contract.
