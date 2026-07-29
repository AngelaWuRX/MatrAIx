# Chat task environments

## Persona agent (shared)

`shared-chat-persona/` — Harbor main image for all chatbot tasks.

## Local endpoint hosts (per SUT)

Pick the sidecar **by the persona-facing protocol** (`input/chatbot.yaml`
`transport`), not by every internal dependency of the product.

| Directory | Task | Persona-facing protocol |
|-----------|------|-------------------------|
| `chatbot-api-sidecar_recai/` | `chat_recai` | HTTP |
| `chatbot-api-sidecar_openbb/` | `chat_openbb` | HTTP adapter (`finance-chatbot`) over OpenBB MCP (`openbb-mcp`) |
| `chatbot-api-sidecar_acme-support-api/` | `example-chat-api_support_chatbot` | HTTP |
| `chatbot-mcp-sidecar_acme-support/` | `example-chat-mcp_support_chatbot` | MCP |
| `chatbot-api-sidecar_multi-agent-medical-assistant/` | `chat_multi-agent-medical-assistant` | HTTP adapter over product upstream |
| `chatbot-api-sidecar_meal-plan-api/` | `chat_meal-planning-nutrition` | HTTP |
| `chatbot-api-sidecar_mental-health-support/` | `chat_mental-health-support` | HTTP |
| `chatbot-api-sidecar_retail-order-support/` | `chat_retail-order-support` | HTTP |
| `chatbot-api-sidecar_clinic-appointment/` | `chat_clinic-appointment` | HTTP |
| `chatbot-api-sidecar_dev-helper/` | `chat_dev-helper` | HTTP |

One directory per task, with a **single** service each. The runtime resolves
one primary service per `local_compose` dir
(`pick_primary_sidecar_service` → `services[0]`) and has no per-task awareness,
so several co-equal bots sharing one compose file would all resolve to the same
service. Multi-service dirs above (`openbb`, `multi-agent-medical-assistant`)
are one primary plus a backing dependency, not co-equal bots.

```toml
[environment]
definition = "application/shared-chat-persona"
local_compose = "application/chatbot-api-sidecar_recai"  # omit for external URLs
```

`chatbot-api-sidecar_openbb` is an API sidecar because the eval talks
`/v1/messages`; OpenBB itself is the MCP data layer behind the adapter, not a
`chatbot-mcp-sidecar_*` (those are for MCP surfaces the persona calls directly).
