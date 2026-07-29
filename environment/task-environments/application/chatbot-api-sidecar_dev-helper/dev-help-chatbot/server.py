"""DevMate — coding help — chatbot sidecar (rule-based smoke implementation).

Deterministic HTTP product under test for the `chat_dev-helper` persona task. Stands in
for the real open-source product the task is modeled on:
danny-avila/LibreChat (https://github.com/danny-avila/LibreChat)

Scenario: Python KeyError: 'name' safe-lookup fix

One service per compose dir, matching every other chat sidecar: the runtime
resolves a single primary service per `local_compose` dir, so each task gets
its own directory and its own image.

Protocol (see the task's `input/chatbot.yaml`):
  POST /v1/messages -> {sessionId, reply, turn, recommendedItems}
  GET  /health      -> {status, bot}
  GET  /ready       -> {status, bot, capabilities}   (Playground readiness)

A production chatbot can replace this by pointing the task's `CHATBOT_UPSTREAM_DEV`
env at a different endpoint.
"""

from __future__ import annotations

import os
import re
import uuid

from flask import Flask, jsonify, request

app = Flask(__name__)

BOT = "dev_helper_bot"

_sessions: dict[str, dict] = {}


def _has(text: str, *needles: str) -> bool:
    return any(n in text for n in needles)


_DEV_ITEMS = [
    "data['user'].get('name') returns None instead of raising",
    "data.get('user', {}).get('name', 'unknown') to default the whole path",
    "Guard first: if 'name' in data['user']: ...",
]


def _dev_helper(state: dict, msg: str) -> tuple[str, list[str]]:
    text = msg.lower()
    if _has(text, "keyerror", "'name'", "data['user']", "python", "crash",
            "missing", "nested"):
        state["problem_known"] = True
    if state.get("problem_known"):
        state["resolved"] = True
        return (
            "That's a classic one. `data['user']['name']` raises `KeyError` the "
            "moment a `user` record has no `name` key — subscripting a dict "
            "with a missing key always raises. Use a safe lookup instead:\n\n"
            "```python\n"
            "name = data['user'].get('name')            # -> None if absent\n"
            "# or default it and guard the whole path:\n"
            "name = data.get('user', {}).get('name', 'unknown')\n"
            "```\n\n"
            "`.get()` returns `None` (or your default) instead of throwing, so "
            "the incomplete records flow through without crashing. Want the "
            "version that logs the records that are missing the field?",
            _DEV_ITEMS,
        )
    return (
        "Happy to help debug. What language are you in, what's the exact error, "
        "and which line does it crash on?",
        [],
    )

_handler = _dev_helper


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
