"""
Dense reward function for the Email Triage RL Environment.

Reward is computed per action based on:
  - Correctness of classification
  - Appropriateness of action
  - Quality / tone of reply
  - Urgency prioritization
  - Redundancy penalty

Returns a Reward object with both total value and per-component breakdown.
"""

from __future__ import annotations

from typing import Any

from .models import Action, ActionType, EmailItem, Reward

# ─── Threshold constants ──────────────────────────────────────────────────────
URGENT_URGENCY_THRESHOLD = 0.7   # emails above this are considered urgent
SPAM_CATEGORIES = {"spam"}
ESCALATION_CATEGORIES = {"urgent", "abuse"}

# ─── Professional / empathetic language markers ───────────────────────────────
PROFESSIONAL_KEYWORDS = [
    "we apologize", "i apologize", "sorry", "sincerely", "thank you",
    "understand", "resolve", "assistance", "help", "support",
    "please", "we will", "we are", "escalate", "priority",
]
POSITIVE_RESOLUTION_KEYWORDS = [
    "refund", "replacement", "credit", "resolved", "fixed", "expedite",
    "immediately", "right away", "urgently", "senior", "manager",
]
COMPLETENESS_MIN_WORDS = 20     # minimum reply length to be considered complete


def compute_tone_score(reply_text: str, email_sentiment: str = "neutral") -> float:
    """
    Heuristic: score reply tone on a 0–1 scale.
    Checks for professional language, empathy, and resolution-oriented words.
    Applies a sentiment continuity penalty if the email is negative but
    the reply lacks any empathy keywords.
    """
    if not reply_text:
        return 0.0
    lower = reply_text.lower()
    word_count = len(lower.split())

    professional_hits = sum(1 for kw in PROFESSIONAL_KEYWORDS if kw in lower)
    resolution_hits = sum(1 for kw in POSITIVE_RESOLUTION_KEYWORDS if kw in lower)

    # Normalize: max 5 professional + 3 resolution hits expected for a perfect response
    tone = min(professional_hits / 5, 1.0) * 0.6 + min(resolution_hits / 3, 1.0) * 0.4

    # Sentiment continuity penalty: negative emails require empathy
    EMPATHY_KEYWORDS = ["apologize", "sorry", "understand", "sincerely", "apologies"]
    empathy_hits = sum(1 for kw in EMPATHY_KEYWORDS if kw in lower)
    if email_sentiment == "negative" and empathy_hits == 0:
        tone *= 0.5  # cold reply to a frustrated customer is penalized

    # Penalize very short replies
    if word_count < COMPLETENESS_MIN_WORDS:
        tone *= word_count / COMPLETENESS_MIN_WORDS

    return round(min(tone, 1.0), 4)


def compute_reward(
    action: Action,
    email: EmailItem,
    previous_actions_on_email: list[dict[str, Any]],
    current_step: int = 0,
) -> Reward:
    """
    Compute dense reward for a single action on an email.

    Args:
        action: The action the agent took.
        email: The email the action was applied to.
        previous_actions_on_email: History of prior actions on this same email.
        current_step: Current episode step count (used for SLA breach detection).

    Returns:
        Reward(value, breakdown, message)
    """
    breakdown: dict[str, float] = {}
    messages: list[str] = []

    is_spam = email.category.value in SPAM_CATEGORIES
    is_urgent = email.urgency_score >= URGENT_URGENCY_THRESHOLD
    needs_escalation = email.category.value in ESCALATION_CATEGORIES

    prior_action_types = [a["action_type"] for a in previous_actions_on_email]
    is_redundant = action.type.value in prior_action_types

    # ── Redundancy penalty ────────────────────────────────────────────────────
    if is_redundant:
        breakdown["redundant_action"] = -0.1
        messages.append(f"Redundant action '{action.type.value}' already applied.")

    # ── Action type correctness ───────────────────────────────────────────────
    if action.type == ActionType.archive:
        if is_spam:
            breakdown["correct_action"] = +0.2
            messages.append("Correctly archived spam email.")
        else:
            breakdown["correct_action"] = -0.15
            messages.append("Archived a non-spam email — loss of information.")

    elif action.type == ActionType.classify:
        if action.classification == email.category.value:
            breakdown["correct_classification"] = +0.3
            messages.append(f"Correctly classified as '{email.category.value}'.")
        elif action.classification is None:
            breakdown["correct_classification"] = -0.1
            messages.append("Classification action missing classification field.")
        else:
            breakdown["correct_classification"] = -0.3
            messages.append(
                f"Wrong classification '{action.classification}' "
                f"(correct: '{email.category.value}')."
            )

    elif action.type == ActionType.reply:
        if is_spam:
            # Replying to spam is wasted effort
            breakdown["correct_action"] = -0.1
            messages.append("Replied to spam — wasted effort.")
        else:
            breakdown["correct_action"] = +0.2
            messages.append("Reply action on valid email.")

            # Tone evaluation (with sentiment continuity)
            reply_text = action.content or ""
            tone_score = compute_tone_score(reply_text, email.sentiment.value)
            tone_reward = round(0.2 * tone_score, 4)
            breakdown["reply_tone"] = tone_reward
            messages.append(f"Reply tone score: {tone_score:.2f}.")

            # Completeness
            word_count = len(reply_text.split()) if reply_text else 0
            if word_count >= COMPLETENESS_MIN_WORDS:
                breakdown["reply_completeness"] = +0.1
                messages.append("Reply is complete and detailed.")
            else:
                breakdown["reply_completeness"] = 0.0
                messages.append(f"Reply too short ({word_count} words, need {COMPLETENESS_MIN_WORDS}+).")

    elif action.type == ActionType.escalate:
        if needs_escalation:
            breakdown["correct_action"] = +0.2
            messages.append("Correctly escalated urgent/abuse email.")
        else:
            breakdown["correct_action"] = -0.05
            messages.append("Escalated a non-urgent email — minor misuse of escalation.")

    elif action.type == ActionType.tag:
        # Tags are only rewarded if classification was already done first
        already_classified = any(
            a.get("action_type") == "classify" and a.get("email_id") == action.email_id
            for a in previous_actions_on_email
        )
        if is_spam:
            breakdown["correct_action"] = -0.05
            messages.append("Tagged spam — should archive instead.")
        elif already_classified:
            breakdown["correct_action"] = +0.1
            messages.append("Tagged email after classification — good workflow.")
        else:
            breakdown["correct_action"] = 0.0
            messages.append("Tag without prior classify — no reward (classify first).")

    # ── Urgency prioritization ────────────────────────────────────────────────
    if is_urgent and action.type in (ActionType.reply, ActionType.escalate):
        breakdown["urgency_prioritization"] = +0.2
        messages.append("Properly handled urgent email with reply/escalation.")
    elif is_urgent and action.type == ActionType.archive:
        breakdown["urgency_prioritization"] = -0.2
        messages.append("CRITICAL: Archived an urgent email! Severe penalty.")
    elif is_urgent and action.type == ActionType.tag:
        breakdown["urgency_prioritization"] = -0.05
        messages.append("Tagged urgent email instead of acting — partial credit only.")

    # ── SLA breach detection ──────────────────────────────────────────────────
    if email.sla_deadline_steps is not None:
        first_action_step = previous_actions_on_email[0].get("step", current_step) if previous_actions_on_email else current_step
        if first_action_step > email.sla_deadline_steps:
            steps_overdue = first_action_step - email.sla_deadline_steps
            breach_penalty = round(-0.1 * min(steps_overdue, 3), 4)  # max -0.30
            breakdown["sla_breach"] = breach_penalty
            messages.append(
                f"SLA BREACH: Acted {steps_overdue} step(s) past deadline "
                f"(deadline={email.sla_deadline_steps}). Penalty={breach_penalty}."
            )
        elif not previous_actions_on_email:
            # First action within SLA window — bonus
            breakdown["sla_met"] = +0.05
            messages.append(f"SLA met: acted within {email.sla_deadline_steps}-step deadline.")

    # ── Thread escalation bonus ───────────────────────────────────────────────
    if getattr(email, "thread_position", 1) > 1 and action.type == ActionType.escalate:
        breakdown["thread_escalation_bonus"] = +0.1
        messages.append("Correctly escalated a follow-up thread email — bonus awarded.")

    # ── Sum breakdown ─────────────────────────────────────────────────────────
    total = round(sum(breakdown.values()), 4)
    # Clamp to [-1.0, +1.0]
    total = max(-1.0, min(1.0, total))

    return Reward(
        value=total,
        breakdown=breakdown,
        message=" | ".join(messages),
    )
