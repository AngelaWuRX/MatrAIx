"""Lakeside Family Clinic — appointment booking — chatbot sidecar (rule-based smoke implementation).

Deterministic HTTP product under test for the `chat_clinic-appointment` persona task. Stands in
for the real open-source product the task is modeled on:
RasaHQ/rasa (https://github.com/RasaHQ/rasa)

Scenario: weekday-morning physical with Dr. Lee

One service per compose dir, matching every other chat sidecar: the runtime
resolves a single primary service per `local_compose` dir, so each task gets
its own directory and its own image.

Protocol (see the task's `input/chatbot.yaml`):
  POST /v1/messages -> {sessionId, reply, turn, recommendedItems}
  GET  /health      -> {status, bot}
  GET  /ready       -> {status, bot, capabilities}   (Playground readiness)

A production chatbot can replace this by pointing the task's `CHATBOT_UPSTREAM_CLINIC`
env at a different endpoint.
"""

from __future__ import annotations

import os
import re
import uuid

from flask import Flask, jsonify, request

app = Flask(__name__)

BOT = "clinic_booking_bot"

_sessions: dict[str, dict] = {}


def _has(text: str, *needles: str) -> bool:
    return any(n in text for n in needles)


_CLINIC_SLOTS = [
    "Tue 8:30 AM — Dr. Lee",
    "Wed 9:15 AM — Dr. Lee",
    "Thu 10:00 AM — Dr. Patel (if Dr. Lee is full)",
]


_CLINIC_FOLLOWUPS = [
    "You're booked for **Tue 8:30 AM with Dr. Lee** — a reminder goes out the "
    "day before. Would you like the visit added to your calendar?",
    "Nothing else is needed. If you'd like to move it, weekday mornings stay "
    "open for the next two weeks — just say the word.",
    "All set on my end. Bring your insurance card and arrive about 10 minutes "
    "early; message here if anything changes.",
]


def _clinic_booking(state: dict, msg: str) -> tuple[str, list[str]]:
    text = msg.lower()
    if _has(text, "physical", "check-up", "checkup", "annual", "routine"):
        state["reason_known"] = True
    # Once booked, move the conversation on rather than re-confirming verbatim.
    if state.get("resolved"):
        i = state.get("followup", 0)
        state["followup"] = i + 1
        return (_CLINIC_FOLLOWUPS[min(i, len(_CLINIC_FOLLOWUPS) - 1)], _CLINIC_SLOTS)
    if state.get("offered") and _has(
        text, "tue", "wed", "thu", "8:30", "9:15", "morning", "lee", "yes",
        "confirm", "book", "that works", "first", "sounds good",
    ):
        state["resolved"] = True
        return (
            "You're all set — I've **confirmed your annual physical with "
            "Dr. Lee on Tuesday at 8:30 AM**. You'll get a reminder the day "
            "before. Please arrive 10 minutes early with your insurance card. "
            "Is there anything else I can help you with?",
            _CLINIC_SLOTS,
        )
    if state.get("reason_known"):
        state["offered"] = True
        return (
            "Happy to book your annual physical. Dr. Lee has weekday-morning "
            "openings in the next two weeks: **Tue 8:30 AM** or **Wed 9:15 AM**. "
            "If neither works, Dr. Patel has Thu 10:00 AM. Which would you like?",
            _CLINIC_SLOTS,
        )
    return (
        "Hi! I can help you book an appointment. What's the visit for, and do "
        "you have a preferred day, time, or provider?",
        [],
    )

_handler = _clinic_booking


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
