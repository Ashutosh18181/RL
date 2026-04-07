"""
Email Triage & Customer Support Automation RL Environment
OpenEnv-compatible environment package.
"""

from .environment import EmailTriageEnv
from .models import Observation, Action, ActionType, Reward, StepResult, TaskConfig, EmailItem

__all__ = [
    "EmailTriageEnv",
    "Observation",
    "Action",
    "ActionType",
    "Reward",
    "StepResult",
    "TaskConfig",
    "EmailItem",
]

__version__ = "1.0.0"
