# chat_clinic-appointment

- **Product under test:** a Rasa-based medical / appointment-booking assistant (RasaHQ/rasa, https://github.com/RasaHQ/rasa)
- **Upstream URL env:** `CHATBOT_UPSTREAM_CLINIC` (with default `baseUrl` in `input/chatbot.yaml`)
- **applicationId:** `clinic_booking_bot` — register in `application/playground/backend/service/chatbot_sidecar_service.py` `_SIDECAR_SPECS` as an upstream spec (compose_dir=None, primary_env=CHATBOT_UPSTREAM_CLINIC).

Verifier emits `task_outcome` / `conversation_summary` / `user_feedback` per the chatbot contract.
