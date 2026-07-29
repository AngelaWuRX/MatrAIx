"""Grounded chatbot sidecar (rule-based smoke implementation) for the four
`chat_*` persona tasks.

One deterministic HTTP product under test that stands in for the real
open-source chatbots named in each task README (LibreChat, a mental-health
bot, a retail-support bot, a clinic booker). The active persona is selected
by the ``SIDECAR_BOT`` env var, so all four task services build the same
image and share this compose file, each pinned to one bot:

    mental_health_bot  -> emotional support + one concrete coping technique
    retail_support_bot -> order #W-2087 wrong-size exchange (US 8 -> US 10)
    clinic_booking_bot -> weekday-morning physical with Dr. Lee
    dev_helper_bot     -> Python KeyError: 'name' safe-lookup fix

The reply shape matches the tasks' `input/chatbot.yaml` protocol
(`POST /v1/messages` -> {sessionId, reply, turn, recommendedItems};
`GET /health`). This is a smoke-run product in the same tier as the Acme
support sidecar: a production chatbot can replace it by pointing the task's
`CHATBOT_UPSTREAM_*` env at a different endpoint.
"""

from __future__ import annotations

import os
import re
import uuid
from typing import Callable

from flask import Flask, jsonify, request

app = Flask(__name__)

BOT = os.environ.get("SIDECAR_BOT", "dev_helper_bot").strip() or "dev_helper_bot"

_sessions: dict[str, dict] = {}


def _has(text: str, *needles: str) -> bool:
    return any(n in text for n in needles)


# --------------------------------------------------------------------------- #
# mental_health_bot
# --------------------------------------------------------------------------- #
_CRISIS_RE = re.compile(
    r"\b(kill myself|end (it|my life)|suicid|hurt myself|self[- ]harm|"
    r"don'?t want to (be here|live)|no reason to live)\b",
    re.IGNORECASE,
)
_MH_RESOURCES = [
    "Box breathing: inhale 4s, hold 4s, exhale 4s, hold 4s",
    "5-4-3-2-1 grounding (name 5 things you see, 4 you feel, ...)",
    "A wind-down routine for the hour before bed",
    "988 Suicide & Crisis Lifeline (call or text, 24/7)",
]


def _mental_health(state: dict, msg: str) -> tuple[str, list[str]]:
    text = msg.lower()
    if _CRISIS_RE.search(msg):
        return (
            "I'm really glad you told me, and I want to make sure you're safe. "
            "If you might act on these thoughts, please reach out right now to "
            "the 988 Suicide & Crisis Lifeline (call or text 988 in the US) or "
            "your local emergency number. You don't have to get through this "
            "alone. Would you like to stay here and talk while you do that?",
            ["988 Suicide & Crisis Lifeline (call or text 988)"],
        )
    if state["turn"] == 0:
        return (
            "Hi, I'm really glad you reached out. It sounds like a heavy week. "
            "Take your time — what's been weighing on you the most tonight?",
            [],
        )
    if not state.get("offered") and _has(
        text, "sleep", "tired", "can't switch", "cant switch", "work", "stress",
        "overwhelm", "anxious", "racing",
    ):
        state["offered"] = True
        return (
            "That sounds exhausting — a racing mind on top of bad sleep is "
            "really draining. Let's try one small thing together right now: "
            "**box breathing**. Breathe in for 4 seconds, hold for 4, out for 4, "
            "hold for 4, and repeat that four times. Want to try it now and tell "
            "me how your body feels afterward?",
            _MH_RESOURCES,
        )
    if _has(text, "better", "calmer", "helped", "grounded", "a bit", "little"):
        return (
            "I'm really glad it took even a little of the edge off. You can come "
            "back to box breathing any time your mind starts to spin. Would a "
            "short wind-down routine for the hour before bed be useful too?",
            _MH_RESOURCES,
        )
    return (
        "Thank you for sharing that. Whenever you're ready, we can try a quick "
        "grounding exercise — or we can just keep talking it through. What "
        "would help most right now?",
        _MH_RESOURCES,
    )


# --------------------------------------------------------------------------- #
# retail_support_bot
# --------------------------------------------------------------------------- #
_RETAIL_ITEMS = [
    "Free size exchange US 8 → US 10 on order #W-2087",
    "Prepaid return label emailed for the US 8 pair",
    "Replacement ships on confirmation, arrives in 3–5 business days",
]


def _retail_support(state: dict, msg: str) -> tuple[str, list[str]]:
    text = msg.lower()
    if "w-2087" in text or re.search(r"\b2087\b", text):
        state["order_known"] = True
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


# --------------------------------------------------------------------------- #
# clinic_booking_bot
# --------------------------------------------------------------------------- #
_CLINIC_SLOTS = [
    "Tue 8:30 AM — Dr. Lee",
    "Wed 9:15 AM — Dr. Lee",
    "Thu 10:00 AM — Dr. Patel (if Dr. Lee is full)",
]


def _clinic_booking(state: dict, msg: str) -> tuple[str, list[str]]:
    text = msg.lower()
    if _has(text, "physical", "check-up", "checkup", "annual", "routine"):
        state["reason_known"] = True
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


# --------------------------------------------------------------------------- #
# dev_helper_bot
# --------------------------------------------------------------------------- #
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


_HANDLERS: dict[str, Callable[[dict, str], tuple[str, list[str]]]] = {
    "mental_health_bot": _mental_health,
    "retail_support_bot": _retail_support,
    "clinic_booking_bot": _clinic_booking,
    "dev_helper_bot": _dev_helper,
}


@app.get("/health")
def health():
    return jsonify({"status": "ok", "bot": BOT})


@app.get("/")
def root():
    return jsonify({"status": "ok", "bot": BOT})


@app.post("/v1/messages")
def post_message():
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", "")).strip()
    if not message:
        return jsonify({"error": "message must not be empty"}), 400

    session_id = str(payload.get("sessionId") or "").strip() or uuid.uuid4().hex
    state = _sessions.setdefault(
        session_id, {"turn": 0, "messages": []}
    )
    state["messages"].append({"role": "user", "content": message})

    handler = _HANDLERS.get(BOT, _dev_helper)
    reply, recommended = handler(state, message)

    state["messages"].append({"role": "assistant", "content": reply})
    state["turn"] += 1
    return jsonify(
        {
            "sessionId": session_id,
            "reply": reply,
            "turn": state["turn"],
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
