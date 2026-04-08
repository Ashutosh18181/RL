"""
Deterministic graders for all three task difficulty levels.

Graders are PURE FUNCTIONS — no randomness, no side effects.
Each returns a float in [0.0, 1.0].

History format (list of dicts):
  {
    "step": int,
    "action_type": str,
    "email_id": str,
    "classification": str | None,
    "content": str | None,
    "reward": float,
    "resolved": bool,
  }
"""

from __future__ import annotations

from typing import Any

from .email_data import get_email
from .reward import compute_tone_score


# ─── Helper ───────────────────────────────────────────────────────────────────

def _actions_for_email(history: list[dict[str, Any]], email_id: str) -> list[dict[str, Any]]:
    return [h for h in history if h.get("email_id") == email_id]


def _has_action(history: list[dict[str, Any]], email_id: str, action_type: str) -> bool:
    return any(
        h.get("email_id") == email_id and h.get("action_type") == action_type
        for h in history
    )


def _get_classification(history: list[dict[str, Any]], email_id: str) -> str | None:
    for h in history:
        if h.get("email_id") == email_id and h.get("action_type") == "classify":
            return h.get("classification")
    return None


def _get_reply(history: list[dict[str, Any]], email_id: str) -> str | None:
    for h in history:
        if h.get("email_id") == email_id and h.get("action_type") == "reply":
            return h.get("content")
    return None


# ─── EASY GRADER ─────────────────────────────────────────────────────────────

def grade_easy(history: list[dict[str, Any]], task_email_ids: list[str]) -> float:
    """
    Easy task grader.

    Rubric (total 1.0):
    - Correct classification: 0.5
    - Appropriate action (tag non-spam / archive spam): 0.3
    - Optional reply quality bonus: 0.2
    """
    if not task_email_ids:
        return 0.0

    email_id = task_email_ids[0]
    email = get_email(email_id)
    if email is None:
        return 0.0

    score = 0.0

    # Classification correctness (0.5)
    classification = _get_classification(history, email_id)
    if classification == email.category.value:
        score += 0.5
    elif classification is not None:
        # Partial credit for attempting any classification
        score += 0.05

    # Action correctness (0.3)
    if email.category.value == "spam":
        if _has_action(history, email_id, "archive"):
            score += 0.3
        elif _has_action(history, email_id, "tag"):
            score += 0.1  # partial — tagging spam is acceptable but not ideal
    else:
        # Non-spam: should tag or reply
        if _has_action(history, email_id, "tag") or _has_action(history, email_id, "reply"):
            score += 0.3
        elif _has_action(history, email_id, "escalate"):
            score += 0.2  # escalation is fine for complaints/urgent

    # Reply tone bonus (0.2)
    reply = _get_reply(history, email_id)
    if reply:
        tone = compute_tone_score(reply)
        score += 0.2 * tone

    final_score = min(score, 1.0)
    # Clamp to strictly (0, 1) as required by hackathon grader
    final_score = max(0.0001, min(final_score, 0.9999))
    return round(final_score, 4)



# ─── MEDIUM GRADER ───────────────────────────────────────────────────────────

def grade_medium(history: list[dict[str, Any]], task_email_ids: list[str]) -> float:
    """
    Medium task grader (3 emails).

    Rubric per email (each worth 1/3 of total):
    - Correct classification: 0.4
    - Correct action (reply / archive spam): 0.35
    - Reply tone & completeness: 0.25
    """
    if not task_email_ids:
        return 0.0

    per_email_score = 1.0 / len(task_email_ids)
    total = 0.0

    for email_id in task_email_ids:
        email = get_email(email_id)
        if email is None:
            continue

        email_score = 0.0
        is_spam = email.category.value == "spam"
        is_urgent = email.urgency_score >= 0.7

        # Classification (0.4)
        classification = _get_classification(history, email_id)
        if classification == email.category.value:
            email_score += 0.4
        elif classification is not None:
            email_score += 0.05

        # Action correctness (0.35)
        if is_spam:
            if _has_action(history, email_id, "archive"):
                email_score += 0.35
            elif _has_action(history, email_id, "tag"):
                email_score += 0.1
        else:
            replied = _has_action(history, email_id, "reply")
            escalated = _has_action(history, email_id, "escalate")
            if replied:
                email_score += 0.35
            elif escalated and is_urgent:
                email_score += 0.3  # escalation acceptable for urgent
            elif escalated:
                email_score += 0.1

        # Reply quality (0.25)
        reply = _get_reply(history, email_id)
        if reply and not is_spam:
            tone = compute_tone_score(reply)
            word_count = len(reply.split())
            completeness = min(word_count / 30, 1.0)  # 30 words = full completeness score
            quality_score = 0.6 * tone + 0.4 * completeness
            email_score += 0.25 * quality_score

        total += email_score * per_email_score

    final_score = min(total, 1.0)
    # Clamp to strictly (0, 1) as required by hackathon grader
    final_score = max(0.0001, min(final_score, 0.9999))
    return round(final_score, 4)



# ─── HARD GRADER ─────────────────────────────────────────────────────────────

def grade_hard(history: list[dict[str, Any]], task_email_ids: list[str]) -> float:
    """
    Hard task grader (5 emails with context, thread tracking, prioritization).

    Additional criteria beyond medium:
    - Urgency prioritization: extremely urgent emails handled before lower-urgency ones
    - Thread context: subsequent thread emails recognized and escalated
    - Correct escalation of thread continuation

    Rubric:
    - Per-email correctness: 40% (same as medium, per email)
    - Urgency ordering bonus: 20%
    - Thread escalation: 20%
    - Overall coverage (all emails addressed): 20%
    """
    if not task_email_ids:
        return 0.0

    # ─── Per-email correctness (40% weight) ───────────────────────────────────
    per_email_correctness = grade_medium(history, task_email_ids)

    # ─── Urgency ordering (20%) ───────────────────────────────────────────────
    # Check if urgent emails (score>=0.9) were handled BEFORE low-urgency emails
    urgency_score = 0.0
    high_urgency_ids = []
    low_urgency_ids = []

    for email_id in task_email_ids:
        email = get_email(email_id)
        if email is None:
            continue
        if email.urgency_score >= 0.9:
            high_urgency_ids.append(email_id)
        elif email.urgency_score < 0.5:
            low_urgency_ids.append(email_id)

    if high_urgency_ids and low_urgency_ids:
        # Find first step index for each group
        def first_step(email_ids: list[str]) -> int:
            steps = []
            for h in history:
                if h.get("email_id") in email_ids:
                    steps.append(h.get("step", 999))
            return min(steps) if steps else 999

        high_first = first_step(high_urgency_ids)
        low_first = first_step(low_urgency_ids)

        if high_first < low_first:
            urgency_score = 1.0      # perfect ordering
        elif high_first == low_first:
            urgency_score = 0.5      # interleaved
        else:
            urgency_score = 0.0      # wrong order — urgent handled last
    else:
        urgency_score = 1.0  # no ordering constraint possible

    # ─── Thread escalation (20%) ──────────────────────────────────────────────
    thread_score = 0.0
    # email_028 and email_029 form a thread; email_029 must be escalated
    thread_escalation_email = "email_029"
    if thread_escalation_email in task_email_ids:
        if _has_action(history, thread_escalation_email, "escalate"):
            thread_score = 1.0
        elif _has_action(history, thread_escalation_email, "reply"):
            thread_score = 0.5  # replied but didn't escalate — partial credit
        else:
            thread_score = 0.0
    else:
        thread_score = 1.0  # thread not part of this run

    # ─── Coverage (20%) ───────────────────────────────────────────────────────
    addressed_emails = {h.get("email_id") for h in history}
    coverage = len([e for e in task_email_ids if e in addressed_emails]) / len(task_email_ids)

    # ─── Combined score ───────────────────────────────────────────────────────
    final_score = (
        0.40 * per_email_correctness
        + 0.20 * urgency_score
        + 0.20 * thread_score
        + 0.20 * coverage
    )

    final_score = min(final_score, 1.0)
    # Clamp to strictly (0, 1) as required by hackathon grader
    final_score = max(0.0001, min(final_score, 0.9999))
    return round(final_score, 4)



# ─── Unified grader dispatch ──────────────────────────────────────────────────

def grade_episode(
    task_id: str,
    history: list[dict[str, Any]],
    task_email_ids: list[str],
) -> dict[str, Any]:
    """
    Grade a completed episode and return a structured report.
    """
    graders = {
        "easy": grade_easy,
        "medium": grade_medium,
        "hard": grade_hard,
    }
    grader = graders.get(task_id)
    if grader is None:
        raise ValueError(f"Unknown task_id '{task_id}'")

    score = grader(history, task_email_ids)

    return {
        "task_id": task_id,
        "score": score,
        "total_steps": len(history),
        "passed": score >= _task_thresholds().get(task_id, 0.7),
        "grade_letter": _to_letter_grade(score),
    }


def _task_thresholds() -> dict[str, float]:
    from .tasks import ALL_TASKS
    return {tid: t.success_threshold for tid, t in ALL_TASKS.items()}


def _to_letter_grade(score: float) -> str:
    if score >= 0.9:
        return "A+"
    if score >= 0.8:
        return "A"
    if score >= 0.7:
        return "B"
    if score >= 0.6:
        return "C"
    if score >= 0.5:
        return "D"
    return "F"
