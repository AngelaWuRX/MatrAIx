# chat_mental-health-support task environment

This task expects an **already-running upstream chatbot endpoint** — the real open-source
product under test.

- **Product (open source, from GitHub):** Rogendo/Mental-health-Chatbot — https://github.com/Rogendo/Mental-health-Chatbot
- Set `CHATBOT_UPSTREAM_MENTAL_HEALTH` (or legacy `MENTAL_HEALTH_CHATBOT_URL`) to the endpoint you want Playground to call.
- No startable local sidecar is vendored here; the chatbot runs upstream and speaks the
  standard `/v1/messages` contract (see the task's `input/chatbot.yaml`).
