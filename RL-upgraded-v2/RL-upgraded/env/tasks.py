"""
Task definitions for the Email Triage RL Environment.
Three difficulty levels: easy, medium, hard.
"""

from .models import TaskConfig

# ─── EASY TASK ───────────────────────────────────────────────────────────────
# Single inbox email. Goal: classify correctly and apply the right tag.
TASK_EASY = TaskConfig(
    id="easy",
    name="Single Email Triage",
    description=(
        "You have a single incoming email in your inbox. "
        "Correctly classify its intent (complaint / refund / inquiry / spam / urgent / abuse) "
        "and apply the appropriate tag. A reply is optional but helps your score."
    ),
    max_steps=5,
    difficulty="easy",
    objective="Classify the email correctly and tag it. Spam emails should be archived.",
    success_threshold=0.7,
    email_ids=["email_003"],       # defective product complaint
)

# ─── MEDIUM TASK ─────────────────────────────────────────────────────────────
# Three emails of different types. Goal: classify each, generate a reply for
# non-spam emails, and archive spam.
TASK_MEDIUM = TaskConfig(
    id="medium",
    name="Multi-Email Resolution",
    description=(
        "You have a mixed inbox of 3 emails. For each email you must: "
        "(1) classify the intent, (2) reply with an appropriate, professional message "
        "OR archive if spam. The reply content is evaluated for tone and completeness."
    ),
    max_steps=10,
    difficulty="medium",
    objective=(
        "Process all 3 emails: classify intent, write appropriate replies for "
        "actionable emails, and archive spam."
    ),
    success_threshold=0.65,
    email_ids=["email_007", "email_015", "email_011"],  # urgent refund, spam, warranty inquiry
)

# ─── HARD TASK ───────────────────────────────────────────────────────────────
# Five emails including a multi-turn thread, an urgent escalation, refund,
# spam, and a complaint. Requires prioritization and escalation decisions.
TASK_HARD = TaskConfig(
    id="hard",
    name="Multi-Turn Escalation & Prioritization",
    description=(
        "You have a complex inbox of 5 emails including urgent issues, a multi-turn "
        "complaint thread, a refund, and spam. You must: "
        "(1) Prioritize by urgency, "
        "(2) Track context across thread emails, "
        "(3) Escalate when appropriate, "
        "(4) Reply professionally to each actionable email, "
        "(5) Archive spam."
    ),
    max_steps=20,
    difficulty="hard",
    objective=(
        "Handle all 5 emails with correct prioritization: address urgent emails first, "
        "escalate the ongoing complaint thread, process refund, and archive spam."
    ),
    success_threshold=0.6,
    email_ids=[
        "email_018",   # CRITICAL: payment system down (urgent, score=1.0)
        "email_028",   # complaint thread part 1
        "email_029",   # complaint thread part 2 — requires escalation
        "email_025",   # medical emergency refund (high urgency)
        "email_030",   # spam — archive
    ],
)

# All tasks indexed for lookup
ALL_TASKS: dict[str, TaskConfig] = {
    "easy": TASK_EASY,
    "medium": TASK_MEDIUM,
    "hard": TASK_HARD,
    # extreme is added below after its definition
}


def get_task(task_id: str) -> TaskConfig:
    task = ALL_TASKS.get(task_id)
    if task is None:
        raise ValueError(f"Unknown task_id '{task_id}'. Valid options: {list(ALL_TASKS.keys())}")
    return task


# ─── EXTREME TASK ─────────────────────────────────────────────────────────────
# Ten emails: multiple urgent crises, two complaint threads, abuse, mixed refunds,
# spam. Rate-limiting is simulated by penalizing redundant actions more steeply.
TASK_EXTREME = TaskConfig(
    id="extreme",
    name="Full Inbox Blitz — Executive Triage",
    description=(
        "You are the on-call senior support lead. Ten emails have arrived overnight. "
        "They include a system-down alert, two ongoing complaint threads requiring "
        "escalation, a medical emergency refund, multiple standard inquiries, spam, "
        "and an abuse report. You must ruthlessly prioritize, escalate threads, "
        "archive noise, and resolve everything within 35 steps."
    ),
    max_steps=35,
    difficulty="extreme",
    objective=(
        "Process all 10 emails with correct prioritization: critical urgency first, "
        "escalate all thread follow-ups, archive spam/abuse-if-resolved, "
        "write professional replies for all actionable emails."
    ),
    success_threshold=0.50,
    email_ids=[
        "email_018",   # CRITICAL: payment system down (urgency=1.0)
        "email_025",   # medical emergency refund (urgency=0.95)
        "email_028",   # complaint thread part 1
        "email_029",   # complaint thread part 2 — requires escalation
        "email_007",   # urgent refund
        "email_001",   # standard complaint
        "email_011",   # warranty inquiry
        "email_015",   # spam
        "email_030",   # spam
        "email_004",   # billing complaint
    ],
)

ALL_TASKS["extreme"] = TASK_EXTREME
