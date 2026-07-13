# chat_budget-coach

- **Product under test:** an OpenDialog conversational assistant for regulated personal finance (opendialogai/opendialog, https://github.com/opendialogai/opendialog)
- **Upstream URL env:** `CHATBOT_UPSTREAM_BUDGET` (with default `baseUrl` in `input/chatbot.yaml`)
- **applicationId:** `budget_coach_bot` — register in `application/playground/backend/service/chatbot_sidecar_service.py` `_SIDECAR_SPECS` as an upstream spec (compose_dir=None, primary_env=CHATBOT_UPSTREAM_BUDGET).

Verifier emits `task_outcome` / `conversation_summary` / `user_feedback` per the chatbot contract.
