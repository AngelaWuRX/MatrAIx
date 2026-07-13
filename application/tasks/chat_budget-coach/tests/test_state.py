"""Generic verifier for the persona-bot chatbot task family.

Validates the platform-written transcript.json (+ optional user_feedback.json), then emits
verifier/structured_output.json with the shared chatbot contexts (task_outcome,
conversation_summary, user_feedback) per application/task-spec/chatbot. Self-configures the
task-goal label from the transcript's botType, so one identical verifier serves every task.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

OUTPUT_DIR = Path(os.environ.get("PERSONABENCH_OUTPUT_DIR") or os.environ.get("MATRIX_OUTPUT_DIR") or "/app/output")
TRANSCRIPT_PATH = OUTPUT_DIR / "transcript.json"
FEEDBACK_PATH = OUTPUT_DIR / "user_feedback.json"

GOAL_BY_BOT = {
    "mental_health": "Get supportive, safe emotional-support guidance",
    "retail_support": "Resolve an order or customer-support issue",
    "clinic_booking": "Book a clinic appointment with safe triage",
    "budget_coach": "Get budgeting guidance within the assistant's scope",
    "dev_helper": "Get a working solution to a coding question",
}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail(f"{path} is missing")
    try:
        val = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path} is not valid JSON: {exc}")
    if not isinstance(val, dict):
        fail(f"{path} must contain a JSON object")
    return val


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{label} must be a non-empty string")
    return value


def validate_messages(messages: Any) -> None:
    if not isinstance(messages, list) or not messages:
        fail("transcript.messages must be a non-empty list")
    for i, m in enumerate(messages):
        if not isinstance(m, dict):
            fail(f"transcript.messages[{i}] must be an object")
        if m.get("role") not in {"user", "assistant"}:
            fail(f"message role must be user or assistant, got {m.get('role')!r}")
        require_string(m.get("content"), "message content")


def validate_feedback(fb: dict[str, Any]) -> None:
    for k in ("needConstraintSatisfaction", "personalPreferenceSatisfaction"):
        v = fb.get(k)
        if v is None or (isinstance(v, str) and not v.strip()):
            fail(f"user_feedback.{k} must be present")
    require_string(fb.get("reason"), "user_feedback.reason")
    r = fb.get("overallExperienceRating")
    if not isinstance(r, int) or not (1 <= r <= 10):
        fail("user_feedback.overallExperienceRating must be an integer 1-10")
    if not isinstance(fb.get("askedUsefulClarificationQuestions"), bool):
        fail("user_feedback.askedUsefulClarificationQuestions must be boolean")


def bucket(value: Any) -> str:
    t = str(value).strip().lower()
    if t in {"true", "1"}:
        return "yes"
    if t in {"false", "0"}:
        return "no"
    return t if t in {"yes", "partially", "no"} else "no"


def derive_outcome(need: str | None, pref: str | None, has_fb: bool) -> str:
    if has_fb and need == "yes" and pref == "yes":
        return "resolved"
    if has_fb and (need in {"yes", "partially"} or pref in {"yes", "partially"}):
        return "partially_resolved"
    return "unresolved" if has_fb else "partially_resolved"


def derive_path(qcount: int, outcome: str) -> str:
    if outcome == "resolved":
        return "clarify_then_resolve" if qcount > 0 else "direct_resolution"
    return "clarify_then_partial" if qcount > 0 else "stalled"


def verifier_dir() -> Path:
    base = os.environ.get("HARBOR_VERIFIER_DIR") or os.environ.get("PERSONABENCH_VERIFIER_DIR") or "/logs/verifier"
    p = Path(base)
    try:
        p.mkdir(parents=True, exist_ok=True)
    except OSError:
        p = Path(__file__).resolve().parent.parent / "verifier"
        p.mkdir(parents=True, exist_ok=True)
    return p


def facet(key, label, role, kind, value):
    return {"key": key, "label": label, "role": role, "kind": kind, "value": value}


def main() -> int:
    tr = load_json(TRANSCRIPT_PATH)
    require_string(tr.get("sessionId"), "transcript.sessionId")
    messages = tr.get("messages")
    validate_messages(messages)
    bot_type = str(tr.get("botType") or tr.get("domain") or "").strip()
    goal = GOAL_BY_BOT.get(bot_type, "Complete the persona's conversational goal")

    fb = None
    if FEEDBACK_PATH.exists():
        fb = load_json(FEEDBACK_PATH)
        validate_feedback(fb)

    user_turns = sum(1 for m in messages if m["role"] == "user")
    asst_turns = sum(1 for m in messages if m["role"] == "assistant")
    qcount = sum(1 for m in messages if m["role"] == "assistant" and "?" in m.get("content", ""))

    need = bucket(fb.get("needConstraintSatisfaction")) if fb else None
    pref = bucket(fb.get("personalPreferenceSatisfaction")) if fb else None
    outcome = derive_outcome(need, pref, fb is not None)
    path = derive_path(qcount, outcome)
    reason = (fb.get("reason") if fb else None) or "No self-report provided."

    contexts = [
        {"key": "task_outcome.primary", "label": "Task outcome", "contextType": "task_outcome", "facets": [
            facet("outcome_status", "Outcome status", "primary", "categorical", outcome),
            facet("resolution_basis", "Resolution basis", "primary", "categorical",
                  "user_feedback" if fb else "conversation_commitment"),
            facet("outcome_reason", "Outcome reason", "explanation", "textual", reason),
            facet("next_step_owner", "Next step owner", "evidence", "categorical",
                  "none" if outcome == "resolved" else "agent"),
            facet("task_goal_label", "Task goal", "evidence", "textual", goal),
        ]},
        {"key": "conversation_summary.primary", "label": "Conversation summary",
         "contextType": "conversation_summary", "facets": [
            facet("conversation_path", "Conversation path", "primary", "categorical", path),
            facet("user_turn_count", "User turn count", "score", "numerical", user_turns),
            facet("assistant_turn_count", "Assistant turn count", "score", "numerical", asst_turns),
            facet("message_count", "Message count", "score", "numerical", len(messages)),
            facet("clarification_question_count", "Clarification question count", "score", "numerical", qcount),
            facet("process_notes", "Process notes", "explanation", "textual",
                  f"{user_turns} user / {asst_turns} assistant turns; {qcount} clarification question(s)."),
        ]},
    ]
    if fb is not None:
        contexts.append({"key": "user_feedback.primary", "label": "User feedback",
                         "contextType": "user_feedback", "facets": [
            facet("overall_experience_rating", "Overall experience rating", "score", "numerical",
                  int(fb["overallExperienceRating"])),
            facet("feedback_reason", "Feedback reason", "explanation", "textual", reason),
            facet("need_constraint_satisfaction", "Need or constraint satisfaction", "evidence", "categorical", need),
            facet("personal_preference_satisfaction", "Personal preference satisfaction", "evidence", "categorical", pref),
            facet("clarification_questions_useful", "Clarification questions useful", "primary", "categorical",
                  "true" if fb.get("askedUsefulClarificationQuestions") else "false"),
        ]})

    (verifier_dir() / "structured_output.json").write_text(json.dumps({
        "schemaVersion": "1.0", "artifactType": "personabench.trial_evaluation", "taskType": "chatbot",
        "presenceCheck": {"passed": True, "requiredArtifacts": ["transcript.json"], "missingArtifacts": []},
        "sourceArtifacts": {"transcript": str(TRANSCRIPT_PATH),
                            **({"userFeedback": str(FEEDBACK_PATH)} if fb else {})},
        "contexts": contexts,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
