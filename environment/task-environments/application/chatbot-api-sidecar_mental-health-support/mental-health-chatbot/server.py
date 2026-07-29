"""Haven — mental-health support — chatbot sidecar (rule-based smoke implementation).

Deterministic HTTP product under test for the `chat_mental-health-support` persona task. Stands in
for the real open-source product the task is modeled on:
Rogendo/Mental-health-Chatbot (https://github.com/Rogendo/Mental-health-Chatbot)

Scenario: emotional support + one concrete coping technique

One service per compose dir, matching every other chat sidecar: the runtime
resolves a single primary service per `local_compose` dir, so each task gets
its own directory and its own image.

Protocol (see the task's `input/chatbot.yaml`):
  POST /v1/messages -> {sessionId, reply, turn, recommendedItems}
  GET  /health      -> {status, bot}
  GET  /ready       -> {status, bot, capabilities}   (Playground readiness)

A production chatbot can replace this by pointing the task's `CHATBOT_UPSTREAM_MENTAL_HEALTH`
env at a different endpoint.
"""

from __future__ import annotations

import os
import re
import uuid

from flask import Flask, jsonify, request

app = Flask(__name__)

BOT = "mental_health_bot"

_sessions: dict[str, dict] = {}


def _has(text: str, *needles: str) -> bool:
    return any(n in text for n in needles)


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


_MH_EASED = [
    "I'm really glad it took even a little of the edge off. You can come back "
    "to box breathing any time your mind starts to spin. Would a short "
    "wind-down routine for the hour before bed be useful too?",
    "That's worth noticing — your body responded. Keeping screens out of the "
    "last hour before bed tends to compound that effect. Want to try pairing "
    "the two tonight?",
    "You've got two things that work now: the breathing when your mind races, "
    "and a calmer hour before sleep. How are you feeling about tonight?",
    "If it helps, the 5-4-3-2-1 exercise works the same way when you're away "
    "from home — name five things you can see, then four you can feel.",
    "None of this has to fix the work situation to be worth doing. Getting "
    "your body out of alarm first usually makes the rest easier to face.",
    "If the sleep doesn't ease up over a couple of weeks, it's worth mentioning "
    "to a GP or counsellor — that's a practical step, not a big one.",
    "You handled a hard week by reaching out, which isn't nothing.",
    "I'm glad you checked in tonight. Be gentle with yourself.",
]

_MH_CONTINUE = [
    "Thank you for sharing that. Whenever you're ready, we can try a quick "
    "grounding exercise — or we can just keep talking it through. What would "
    "help most right now?",
    "That makes sense, and it's a lot to hold. If naming it out loud helps "
    "more than an exercise right now, I'm here for that too — what's been "
    "hardest?",
    "I hear you. We don't have to fix all of it tonight. Is there one piece "
    "that feels the most urgent to set down?",
    "Being behind at work has a way of following you home. What would 'enough "
    "for today' look like, if you got to define it?",
    "You've been carrying this a while by the sound of it. Has anything helped "
    "even slightly before — sleep, movement, talking to someone?",
    "It's okay if the answer is 'nothing much'. Sometimes naming that is the "
    "honest starting point.",
    "Whatever you decide to try, one small thing repeated beats a big plan you "
    "can't sustain this week.",
    "I'm still here. Take whatever time you need.",
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
    # Vary later turns so a long conversation doesn't repeat one reply verbatim.
    i = state.get("followup", 0)
    state["followup"] = i + 1
    if _has(text, "better", "calmer", "helped", "grounded", "a bit", "little"):
        pool = _MH_EASED
    else:
        pool = _MH_CONTINUE
    return (pool[min(i, len(pool) - 1)], _MH_RESOURCES)

_handler = _mental_health


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
