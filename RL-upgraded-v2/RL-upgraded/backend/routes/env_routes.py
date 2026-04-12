"""
Environment routes — the core OpenEnv-compatible API.
Endpoints: /reset, /step, /state, /tasks, /grader, /baseline
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Body, HTTPException, Header
from pydantic import BaseModel

from env.environment import EmailTriageEnv
from env.grader import grade_episode
from env.models import Action
from env.tasks import ALL_TASKS

router = APIRouter()

# ─── Session management ───────────────────────────────────────────────────────
# Each session gets its own isolated env instance to prevent race conditions.
# Sessions keyed by X-Session-ID header; default session for header-less callers.
_sessions: dict[str, EmailTriageEnv] = {}
DEFAULT_SESSION = "default"


def _get_env(session_id: str) -> EmailTriageEnv:
    if session_id not in _sessions:
        _sessions[session_id] = EmailTriageEnv()
    return _sessions[session_id]


# ─── Request / Response schemas ───────────────────────────────────────────────

class ResetRequest(BaseModel):
    task_id: str = "easy"


class ResetRequestOptional(BaseModel):
    task_id: Optional[str] = "easy"


class StepRequest(BaseModel):
    action: Action


class GraderRequest(BaseModel):
    task_id: str
    history: list[dict[str, Any]]
    email_ids: list[str]


class BaselineRequest(BaseModel):
    task_id: str = "easy"
    mock: bool = True   # if True, uses rule-based mock agent instead of OpenAI


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/reset")
async def reset_env(
    req: Optional[ResetRequestOptional] = Body(default=None),
    x_session_id: Optional[str] = Header(default=None),
):
    """
    Reset the environment to start a new episode.
    Accepts an optional JSON body with task_id (defaults to 'easy').
    Optionally pass X-Session-ID header for isolated concurrent sessions.
    Returns the initial Observation.
    """
    session_id = x_session_id or DEFAULT_SESSION
    task_id = (req.task_id if req and req.task_id else None) or "easy"
    try:
        env = _get_env(session_id)
        obs = env.reset(task_id=task_id)
        return {"ok": True, "observation": obs.model_dump(), "session_id": session_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/step")
async def step_env(
    req: StepRequest,
    x_session_id: Optional[str] = Header(default=None),
):
    """
    Execute one action in the current episode.
    Returns (observation, reward, done, info).
    """
    session_id = x_session_id or DEFAULT_SESSION
    try:
        env = _get_env(session_id)
        result = env.step(req.action)
        return result.model_dump()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/state")
async def get_state(x_session_id: Optional[str] = Header(default=None)):
    """Get full current environment state snapshot."""
    session_id = x_session_id or DEFAULT_SESSION
    return _get_env(session_id).state()


@router.get("/tasks")
async def list_tasks():
    """List all available task configurations and action schema."""
    return {
        "tasks": [t.model_dump() for t in ALL_TASKS.values()],
        "action_schema": {
            "fields": {
                "type": "string — one of: classify, reply, escalate, archive, tag",
                "email_id": "string — ID of the target email",
                "classification": "string | null — required for classify action",
                "content": "string | null — required for reply/tag actions",
            }
        },
    }


@router.post("/grader")
async def run_grader(req: GraderRequest):
    """
    Grade a completed or in-progress episode.
    Accepts history and returns a scored report.
    """
    try:
        report = grade_episode(
            task_id=req.task_id,
            history=req.history,
            task_email_ids=req.email_ids,
        )
        return {"ok": True, "grade": report, "score": report["score"]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/baseline")
async def run_baseline(req: BaselineRequest):
    """
    Run the baseline agent on the specified task.
    Returns per-step log and final score.
    Accessible at /baseline and /api/baseline.
    """
    from baseline.agent import BaselineAgent, MockAgent

    agent_cls = MockAgent if req.mock else BaselineAgent
    agent = agent_cls()

    local_env = EmailTriageEnv()
    obs = local_env.reset(task_id=req.task_id)

    steps_log: list[dict[str, Any]] = []
    total_reward = 0.0
    done = False
    max_iterations = 50
    iteration = 0

    while not done and iteration < max_iterations:
        action = await asyncio.to_thread(agent.act, obs)
        result = local_env.step(action)

        steps_log.append({
            "step": result.observation.step_count - 1,
            "action": action.model_dump(),
            "reward": result.reward.model_dump(),
            "done": result.done,
        })

        total_reward += result.reward.value
        done = result.done
        obs = result.observation
        iteration += 1

    final_state = local_env.state()
    grade = grade_episode(
        task_id=req.task_id,
        history=final_state["history"],
        task_email_ids=ALL_TASKS[req.task_id].email_ids,
    )

    return {
        "task_id": req.task_id,
        "total_steps": len(steps_log),
        "total_reward": round(total_reward, 4),
        "grade": grade,
        "score": grade["score"],
        "steps": steps_log,
    }
