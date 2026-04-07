"""
Core RL Environment — EmailTriageEnv

Implements the OpenEnv interface:
  - reset(task_id) → Observation
  - step(action)   → (Observation, Reward, done, info)
  - state()        → full state dict
"""

from __future__ import annotations

import copy
from typing import Any

from .email_data import get_email
from .grader import grade_episode
from .models import Action, ActionType, EmailItem, Observation, Reward, StepResult
from .reward import compute_reward
from .tasks import get_task, TaskConfig


class EmailTriageEnv:
    """
    Email Triage & Customer Support Automation RL Environment.

    An episode processes a queue of emails defined by the selected task.
    The agent must classify, reply, escalate, tag, or archive each email
    to maximize cumulative reward.
    """

    def __init__(self) -> None:
        self._task: TaskConfig | None = None
        self._inbox: list[EmailItem] = []
        self._resolved_ids: list[str] = []
        self._history: list[dict[str, Any]] = []
        self._step_count: int = 0
        self._episode_reward: float = 0.0
        self._done: bool = False
        self._current_email: EmailItem | None = None

    # ─── Public API ──────────────────────────────────────────────────────────

    def reset(self, task_id: str = "easy") -> Observation:
        """
        Start a new episode for the given task.
        Returns the initial Observation.
        """
        self._task = get_task(task_id)
        self._inbox = [
            e for eid in self._task.email_ids
            if (e := get_email(eid)) is not None
        ]
        self._resolved_ids = []
        self._history = []
        self._step_count = 0
        self._episode_reward = 0.0
        self._done = False
        self._current_email = self._inbox[0] if self._inbox else None

        return self._build_observation()

    def step(self, action: Action) -> StepResult:
        """
        Execute one action and advance the environment.

        Returns StepResult(observation, reward, done, info).
        Raises RuntimeError if episode is already done.
        """
        if self._done:
            raise RuntimeError("Episode is done. Call reset() to start a new one.")
        if self._task is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")

        # Find the email the action targets
        email = self._get_email_from_inbox(action.email_id)
        if email is None:
            # Action on non-existent / already resolved email
            penalty = Reward(
                value=-0.1,
                breakdown={"invalid_email_id": -0.1},
                message=f"Email '{action.email_id}' not found in active inbox.",
            )
            self._step_count += 1
            self._episode_reward += penalty.value
            self._done = self._check_done()
            return StepResult(
                observation=self._build_observation(),
                reward=penalty,
                done=self._done,
                info={"warning": "invalid_email_id"},
            )

        # Previous actions on this email
        prior_actions = [
            h for h in self._history if h.get("email_id") == action.email_id
        ]

        # Compute reward
        reward = compute_reward(action, email, prior_actions)

        # Record action in history
        history_entry: dict[str, Any] = {
            "step": self._step_count,
            "action_type": action.type.value,
            "email_id": action.email_id,
            "classification": action.classification,
            "content": action.content,
            "reward": reward.value,
            "breakdown": reward.breakdown,
            "resolved": False,
        }

        # Resolve email if terminal action
        if action.type in (ActionType.archive, ActionType.reply, ActionType.escalate):
            email.is_resolved = True
            self._resolved_ids.append(action.email_id)
            history_entry["resolved"] = True
            # Remove from inbox
            self._inbox = [e for e in self._inbox if e.id != action.email_id]
            # Advance current email pointer
            self._current_email = self._inbox[0] if self._inbox else None

        self._history.append(history_entry)
        self._step_count += 1
        self._episode_reward = round(self._episode_reward + reward.value, 4)
        self._done = self._check_done()

        info: dict[str, Any] = {
            "step": self._step_count - 1,
            "resolved": history_entry["resolved"],
            "remaining_emails": len(self._inbox),
            "episode_reward": self._episode_reward,
        }

        if self._done:
            grade = grade_episode(
                task_id=self._task.id,
                history=self._history,
                task_email_ids=self._task.email_ids,
            )
            info["final_grade"] = grade

        return StepResult(
            observation=self._build_observation(),
            reward=reward,
            done=self._done,
            info=info,
        )

    def state(self) -> dict[str, Any]:
        """
        Return a complete snapshot of the environment state.
        Safe to serialize to JSON.
        """
        return {
            "task": self._task.model_dump() if self._task else None,
            "inbox": [e.model_dump() for e in self._inbox],
            "current_email": self._current_email.model_dump() if self._current_email else None,
            "resolved_ids": list(self._resolved_ids),
            "history": list(self._history),
            "step_count": self._step_count,
            "episode_reward": self._episode_reward,
            "done": self._done,
            "remaining_steps": (
                (self._task.max_steps - self._step_count) if self._task else 0
            ),
        }

    # ─── Private helpers ──────────────────────────────────────────────────────

    def _get_email_from_inbox(self, email_id: str) -> EmailItem | None:
        for e in self._inbox:
            if e.id == email_id:
                return e
        return None

    def _check_done(self) -> bool:
        if self._task is None:
            return True
        if self._step_count >= self._task.max_steps:
            return True
        if not self._inbox:
            return True
        return False

    def _build_observation(self) -> Observation:
        return Observation(
            current_email=copy.deepcopy(self._current_email),
            inbox=copy.deepcopy(self._inbox),
            resolved_emails=list(self._resolved_ids),
            history=list(self._history),
            step_count=self._step_count,
            remaining_steps=(
                (self._task.max_steps - self._step_count) if self._task else 0
            ),
            task_id=self._task.id if self._task else "",
            task_description=self._task.description if self._task else "",
            episode_reward=self._episode_reward,
        )
