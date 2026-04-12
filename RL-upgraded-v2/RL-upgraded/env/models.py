"""
Pydantic v2 models for the Email Triage RL Environment.
All types used across env, backend, and baseline.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Email Item
# ---------------------------------------------------------------------------

class EmailCategory(str, Enum):
    complaint = "complaint"
    refund = "refund"
    inquiry = "inquiry"
    spam = "spam"
    urgent = "urgent"
    abuse = "abuse"


class Sentiment(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class EmailItem(BaseModel):
    id: str
    subject: str
    body: str
    sender: str
    sender_name: str
    category: EmailCategory
    urgency_score: float = Field(ge=0.0, le=1.0)
    sentiment: Sentiment
    timestamp: str
    thread_id: Optional[str] = None
    thread_position: int = 1          # 1=first in thread, 2+=follow-up requiring escalation
    sla_deadline_steps: Optional[int] = None  # agent must act within N steps or incur SLA breach penalty
    is_resolved: bool = False


# ---------------------------------------------------------------------------
# Observation
# ---------------------------------------------------------------------------

class Observation(BaseModel):
    current_email: Optional[EmailItem] = None
    inbox: List[EmailItem] = Field(default_factory=list)
    resolved_emails: List[str] = Field(default_factory=list)      # list of email IDs
    history: List[Dict[str, Any]] = Field(default_factory=list)   # action log
    step_count: int = 0
    remaining_steps: int = 20
    task_id: str = "easy"
    task_description: str = ""
    episode_reward: float = 0.0


# ---------------------------------------------------------------------------
# Action
# ---------------------------------------------------------------------------

class ActionType(str, Enum):
    classify = "classify"
    reply = "reply"
    escalate = "escalate"
    archive = "archive"
    tag = "tag"


class Action(BaseModel):
    type: ActionType
    email_id: str
    content: Optional[str] = None   # required for reply / tag
    classification: Optional[str] = None  # for classify actions


# ---------------------------------------------------------------------------
# Reward
# ---------------------------------------------------------------------------

class Reward(BaseModel):
    value: float
    breakdown: Dict[str, float] = Field(default_factory=dict)
    message: str = ""


# ---------------------------------------------------------------------------
# Step Result
# ---------------------------------------------------------------------------

class StepResult(BaseModel):
    observation: Observation
    reward: Reward
    done: bool
    info: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Task Configuration
# ---------------------------------------------------------------------------

class TaskConfig(BaseModel):
    id: str
    name: str
    description: str
    max_steps: int
    difficulty: str
    objective: str
    success_threshold: float = 0.7
    email_ids: List[str] = Field(default_factory=list)
