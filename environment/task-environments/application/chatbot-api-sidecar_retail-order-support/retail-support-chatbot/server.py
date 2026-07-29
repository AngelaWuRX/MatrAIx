"""Summit Outfitters — order support — chatbot sidecar (rule-based smoke implementation).

Deterministic HTTP product under test for the `chat_retail-order-support` persona task. Stands in
for the real open-source product the task is modeled on:
chatwoot/chatwoot (https://github.com/chatwoot/chatwoot)

Scenario: order #W-2087 wrong-size exchange (US 8 -> US 10)

One service per compose dir, matching every other chat sidecar: the runtime
resolves a single primary service per `local_compose` dir, so each task gets
its own directory and its own image.

Protocol (see the task's `input/chatbot.yaml`):
  POST /v1/messages -> {sessionId, reply, turn, recommendedItems}
  GET  /health      -> {status, bot}
  GET  /ready       -> {status, bot, capabilities}   (Playground readiness)

A production chatbot can replace this by pointing the task's `CHATBOT_UPSTREAM_RETAIL`
env at a different endpoint.
"""

from __future__ import annotations

import os
import re
import uuid

from flask import Flask, jsonify, request

app = Flask(__name__)

BOT = "retail_support_bot"

_sessions: dict[str, dict] = {}


def _has(text: str, *needles: str) -> bool:
    return any(n in text for n in needles)


_RETAIL_ITEMS = [
    "Free size exchange US 8 → US 10 on order #W-2087",
    "Prepaid return label emailed for the US 8 pair",
    "Replacement ships on confirmation, arrives in 3–5 business days",
]


_RETAIL_FOLLOWUPS = [
    "You're all set: the **US 10 replacement for #W-2087** is confirmed and the "
    "prepaid label is in your inbox. Is there anything else I can look at?",
    "Nothing further is needed from you — just drop the US 8 pair off whenever "
    "it suits. Would you like the tracking number sent by text as well?",
    "Happy to help. I'll leave the exchange open in case anything looks off when "
    "the new pair lands — reply here any time.",
    "One last thing worth knowing: the size chart on that model runs about half "
    "a size small, so the US 10 should sit right. Anything else before I close "
    "this out?",
    "Thanks for your patience with the mix-up — I've noted it on the order so "
    "the warehouse sees it.",
    "No rush on the return: the label doesn't expire for 30 days, and you keep "
    "the replacement either way.",
    "If the US 10 also runs short, reply on this same thread and I'll send a "
    "10.5 without another return.",
    "That's everything handled on my side. Your confirmation email should have "
    "landed by now.",
    "Glad we got it sorted. Enjoy the shoes once they arrive.",
]


def _retail_support(state: dict, msg: str) -> tuple[str, list[str]]:
    text = msg.lower()
    if "w-2087" in text or re.search(r"\b2087\b", text):
        state["order_known"] = True
    # Once the exchange is arranged, keep the conversation moving instead of
    # repeating the confirmation verbatim on every later turn.
    if state.get("resolved"):
        i = state.get("followup", 0)
        state["followup"] = i + 1
        return (_RETAIL_FOLLOWUPS[min(i, len(_RETAIL_FOLLOWUPS) - 1)], _RETAIL_ITEMS)
    if _has(text, "refund", "money back", "store credit") and not _has(
        text, "not a refund", "no refund", "instead of a refund", "replacement"
    ):
        return (
            "I can absolutely help — and since the size was our error, I'd "
            "recommend a free exchange rather than a refund so you still get the "
            "shoes you wanted. Shall I set up a replacement in US 10 for order "
            "#W-2087?",
            _RETAIL_ITEMS,
        )
    if state.get("order_known") and _has(
        text, "us 10", "size 10", "replace", "replacement", "exchange", "correct size",
        "right size", "yes", "please",
    ):
        state["resolved"] = True
        return (
            "Done — I've arranged a **replacement in US 10 for order "
            "#W-2087** at no charge. A prepaid label for the US 8 pair is on its "
            "way to your email; you can drop it off any time. Your US 10 ships as "
            "soon as that scans and arrives in **3–5 business days**. Anything "
            "else I can help with?",
            _RETAIL_ITEMS,
        )
    if state["turn"] == 0 or not state.get("order_known"):
        return (
            "I'm sorry your order arrived in the wrong size — let's fix that. "
            "Could you share your order number so I can pull it up?",
            [],
        )
    return (
        "Thanks. Just to confirm: you'd like a **replacement in US 10** for order "
        "#W-2087, not a refund — is that right? I can arrange the exchange "
        "right now, or connect you to a human agent if you'd prefer.",
        _RETAIL_ITEMS,
    )

_handler = _retail_support


@app.get("/health")
def health():
    return jsonify({"status": "ok", "bot": BOT})


@app.get("/")
def root():
    return jsonify({"status": "ok", "bot": BOT})


@app.get("/ready")
@app.get("/v1/ready")
def ready():
    # Exercise the reply path so "Service up" means this bot can actually
    # answer, not merely that the process is listening.
    reply, _ = _handler({"turn": 0, "messages": []}, "hello")
    if not str(reply).strip():
        return jsonify({"status": "error", "detail": "empty bot reply"}), 503
    return jsonify(
        {
            "status": "ready",
            "bot": BOT,
            "capabilities": ["text_chat", "structured_exposure"],
        }
    )


@app.post("/v1/messages")
def post_message():
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", "")).strip()
    if not message:
        return jsonify({"error": "message must not be empty"}), 400

    session_id = str(payload.get("sessionId") or "").strip() or uuid.uuid4().hex
    state = _sessions.setdefault(session_id, {"turn": 0, "messages": []})
    state["messages"].append({"role": "user", "content": message})

    reply, recommended = _handler(state, message)

    state["messages"].append({"role": "assistant", "content": reply})
    state["turn"] += 1
    # `turn` is an OBJECT, not the turn counter: the eval harness does
    # `dict(response[turnField])` and merges it over the response before
    # resolving structuredExposure selectors. Returning a bare int raises
    # "'int' object is not iterable" and fails every trial. Mirrors the
    # openbb finance-chatbot payload.
    return jsonify(
        {
            "sessionId": session_id,
            "reply": reply,
            "turn": {
                "conversationId": session_id,
                "assistantMessage": reply,
                "turnIndex": state["turn"],
                "recommendedItems": recommended,
            },
            "recommendedItems": recommended,
        }
    )


@app.get("/v1/conversation")
def get_conversation():
    session_id = str(request.args.get("sessionId") or "").strip()
    state = _sessions.get(session_id, {"messages": []})
    return jsonify({"sessionId": session_id, "messages": state["messages"]})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
