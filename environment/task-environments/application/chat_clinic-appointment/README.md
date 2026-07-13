# chat_clinic-appointment task environment

This task expects an **already-running upstream chatbot endpoint** — the real open-source
product under test.

- **Product (open source, from GitHub):** RasaHQ/rasa — https://github.com/RasaHQ/rasa
- Set `CHATBOT_UPSTREAM_CLINIC` (or legacy `CLINIC_CHATBOT_URL`) to the endpoint you want Playground to call.
- No startable local sidecar is vendored here; the chatbot runs upstream and speaks the
  standard `/v1/messages` contract (see the task's `input/chatbot.yaml`).
