# chat_clinic-appointment

- **Product under test:** a local appointment-booking chatbot sidecar, modeled on a Rasa-based clinic assistant (RasaHQ/rasa, https://github.com/RasaHQ/rasa)
- **Sidecar:** `application/chatbot-api-sidecar_clinic-appointment` — compose service `clinic-booking-chatbot`, host port 8908
- **applicationId:** `clinic_booking_bot`, registered in `application/playground/backend/service/chatbot_sidecar_service.py` `_SIDECAR_SPECS`
- **Upstream URL env:** `CHATBOT_UPSTREAM_CLINIC` — point this at a deployed Rasa assistant to run against the real product instead of the bundled sidecar

Verifier emits `task_outcome` / `conversation_summary` / `user_feedback` per the chatbot contract.
