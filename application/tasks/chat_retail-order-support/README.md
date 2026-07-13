# chat_retail-order-support

- **Product under test:** Chatwoot, an open-source customer-support / live-chat platform (chatwoot/chatwoot, https://github.com/chatwoot/chatwoot)
- **Upstream URL env:** `CHATBOT_UPSTREAM_RETAIL` (with default `baseUrl` in `input/chatbot.yaml`)
- **applicationId:** `retail_support_bot` — register in `application/playground/backend/service/chatbot_sidecar_service.py` `_SIDECAR_SPECS` as an upstream spec (compose_dir=None, primary_env=CHATBOT_UPSTREAM_RETAIL).

Verifier emits `task_outcome` / `conversation_summary` / `user_feedback` per the chatbot contract.
