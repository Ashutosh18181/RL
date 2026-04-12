"""
Baseline agents for the Email Triage RL Environment.

Two implementations:
1. BaselineAgent  — uses OpenAI API (gpt-4o-mini)
2. MockAgent      — deterministic rule-based agent (no API key needed)

Both expose the same interface: agent.act(observation) → Action
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from env.models import Action, ActionType, EmailItem, Observation

# ─── Mock / Rule-based Agent ─────────────────────────────────────────────────

class MockAgent:
    """
    Deterministic rule-based agent.
    Uses urgency score, category heuristics, and action priority rules.
    No external API required — perfect for CI / demo mode.
    """

    REPLY_TEMPLATES: dict[str, str] = {
        "complaint": (
            "Dear {name},\n\n"
            "Thank you for reaching out and we sincerely apologize for the experience you've had. "
            "We take complaints very seriously and we are escalating this to our resolution team immediately. "
            "We will resolve this issue and will follow up with you within 24 hours.\n\n"
            "We apologize again for the inconvenience and appreciate your patience.\n\n"
            "Best regards,\nCustomer Support Team"
        ),
        "refund": (
            "Dear {name},\n\n"
            "Thank you for contacting us regarding your refund request. "
            "We understand this is important and we sincerely apologize for any inconvenience. "
            "We are processing your refund immediately and you should see it reflected within 3–5 business days. "
            "Your satisfaction is our top priority.\n\n"
            "Best regards,\nCustomer Support Team"
        ),
        "inquiry": (
            "Dear {name},\n\n"
            "Thank you for your inquiry! We are happy to assist. "
            "Please allow us to look into this and we will provide you with a detailed response within 1 business day. "
            "If you need immediate assistance, please do not hesitate to call us.\n\n"
            "Best regards,\nCustomer Support Team"
        ),
        "urgent": (
            "Dear {name},\n\n"
            "We have received your urgent request and are treating it with the highest priority. "
            "I am escalating this immediately to our senior support team. "
            "A specialist will contact you within the next 15 minutes to resolve this issue. "
            "We sincerely apologize for the impact this is having on your operations.\n\n"
            "Best regards,\nSenior Customer Support Manager"
        ),
        "abuse": (
            "Dear Valued Customer,\n\n"
            "We understand you are frustrated and we take your concerns seriously. "
            "We would like to help resolve the underlying issue. "
            "Please reach out to us directly so we can assist you in a constructive manner.\n\n"
            "Best regards,\nCustomer Relations Team"
        ),
    }

    ESCALATION_CATEGORIES = {"urgent", "abuse"}
    ARCHIVE_CATEGORIES = {"spam"}

    def act(self, observation: Observation) -> Action:
        """
        Decide next action based on current observation.

        Priority order:
        1. Process the highest-urgency email in inbox first
        2. Archive spam
        3. Classify if not yet classified
        4. Escalate urgent/abuse, reply to others
        """
        if not observation.inbox:
            # Fallback — should not happen if episode is active
            return Action(
                type=ActionType.tag,
                email_id="unknown",
                content="no-op",
            )

        # Sort inbox by urgency descending
        sorted_inbox = sorted(
            observation.inbox, key=lambda e: e.urgency_score, reverse=True
        )
        email: EmailItem = sorted_inbox[0]

        already_classified = self._was_classified(observation.history, email.id)

        # Step 1: Classify if not yet done
        if not already_classified:
            return Action(
                type=ActionType.classify,
                email_id=email.id,
                classification=email.category.value,  # mock agent has perfect oracle classification
            )

        # Step 2: Archive spam
        if email.category.value in self.ARCHIVE_CATEGORIES:
            return Action(type=ActionType.archive, email_id=email.id)

        # Step 3: Escalate urgent/abuse
        if email.category.value in self.ESCALATION_CATEGORIES:
            return Action(
                type=ActionType.escalate,
                email_id=email.id,
                content=f"Escalating '{email.subject}' — urgency={email.urgency_score:.2f}",
            )

        # Step 4: Reply with appropriate template
        template = self.REPLY_TEMPLATES.get(email.category.value, self.REPLY_TEMPLATES["inquiry"])
        reply_body = template.format(name=email.sender_name)

        return Action(
            type=ActionType.reply,
            email_id=email.id,
            content=reply_body,
        )

    @staticmethod
    def _was_classified(history: list[dict[str, Any]], email_id: str) -> bool:
        return any(
            h.get("email_id") == email_id and h.get("action_type") == "classify"
            for h in history
        )


# ─── OpenAI-powered Agent ─────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are an intelligent email triage agent. Given an inbox observation, you must decide the SINGLE best next action.

Your available actions are:
- classify: Determine the email's intent. Set "classification" to one of: complaint, refund, inquiry, spam, urgent, abuse.
- reply: Send a professional, empathetic reply. Set "content" to the full reply text (minimum 20 words).
- escalate: Escalate to a senior agent. Use for urgent and abuse emails. Set "content" to escalation notes.
- archive: Archive the email permanently. Use ONLY for spam emails.
- tag: Add an informational tag. Use sparingly.

Rules:
1. Always classify before taking any terminal action on an email.
2. Archive spam immediately after classifying.
3. Escalate urgent/abuse emails.
4. Reply with professional, empathetic language to complaints, refunds, and inquiries.
5. Process highest urgency emails FIRST.
6. Respond with VALID JSON only — no markdown fences, no extra text.

Response format (JSON only):
{
  "type": "classify|reply|escalate|archive|tag",
  "email_id": "email_xxx",
  "classification": "category or null",
  "content": "text or null"
}
"""


class BaselineAgent:
    """
    OpenAI gpt-4o-mini powered baseline agent.
    Reads OPENAI_API_KEY from environment.
    """

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as e:
            raise ImportError("openai package not installed. Run: pip install openai") from e

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set. "
                "Use --mock flag to run without an API key."
            )
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def act(self, observation: Observation) -> Action:
        """Call OpenAI and parse structured action from response."""
        prompt = self._build_prompt(observation)

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,   # deterministic
            max_tokens=512,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content or "{}"
        return self._parse_action(raw, observation)

    @staticmethod
    def _build_prompt(obs: Observation) -> str:
        lines = [
            f"Task: {obs.task_id} | Step: {obs.step_count}/{obs.step_count + obs.remaining_steps}",
            f"Episode reward so far: {obs.episode_reward:.3f}",
            "",
            "=== INBOX ===",
        ]
        for email in obs.inbox:
            lines.append(
                f"[{email.id}] Subject: {email.subject}\n"
                f"  From: {email.sender_name} <{email.sender}>\n"
                f"  Urgency: {email.urgency_score:.2f} | Sentiment: {email.sentiment.value}\n"
                f"  Body: {email.body[:300]}{'...' if len(email.body) > 300 else ''}"
            )

        if obs.history:
            lines.append("\n=== ACTION HISTORY ===")
            for h in obs.history[-5:]:   # last 5 actions for context
                lines.append(
                    f"  Step {h['step']}: {h['action_type']} on {h['email_id']} "
                    f"(reward={h['reward']:+.3f})"
                )

        lines.append("\nWhat is your next action? Respond with JSON only.")
        return "\n".join(lines)

    @staticmethod
    def _parse_action(raw: str, obs: Observation) -> Action:
        """Parse LLM JSON response into an Action, with fallback."""
        try:
            raw_stripped = re.sub(r"```(?:json)?|```", "", raw).strip()
            data = json.loads(raw_stripped)
            return Action(
                type=ActionType(data["type"]),
                email_id=data.get("email_id", obs.inbox[0].id if obs.inbox else ""),
                classification=data.get("classification"),
                content=data.get("content"),
            )
        except Exception:
            # Fallback: classify first email
            fallback_id = obs.inbox[0].id if obs.inbox else "unknown"
            return Action(
                type=ActionType.classify,
                email_id=fallback_id,
                classification="inquiry",
            )
