# chat_dev-helper

- **Product under test:** LibreChat, an open-source AI assistant used for coding help (danny-avila/LibreChat, https://github.com/danny-avila/LibreChat)
- **Upstream URL env:** `CHATBOT_UPSTREAM_DEV` (with default `baseUrl` in `input/chatbot.yaml`)
- **applicationId:** `dev_helper_bot` — register in `application/playground/backend/service/chatbot_sidecar_service.py` `_SIDECAR_SPECS` as an upstream spec (compose_dir=None, primary_env=CHATBOT_UPSTREAM_DEV).

Verifier emits `task_outcome` / `conversation_summary` / `user_feedback` per the chatbot contract.
