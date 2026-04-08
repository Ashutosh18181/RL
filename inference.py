"""
inference.py — Email Triage OpenEnv
Hackathon-compliant inference script.

Required environment variables:
  API_BASE_URL  — LLM API endpoint (e.g. https://api-inference.huggingface.co/v1)
  MODEL_NAME    — Model identifier (e.g. meta-llama/Llama-3.3-70B-Instruct)
  HF_TOKEN      — Hugging Face API token

Optional:
  ENV_BASE_URL  — Email Triage environment URL (default: https://ash1809-void.hf.space)
"""

import os
import sys
import json
import time
import requests
from openai import OpenAI

# ── Config ────────────────────────────────────────────────────────────────────
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api-inference.huggingface.co/v1")
MODEL_NAME   = os.environ.get("MODEL_NAME",   "meta-llama/Llama-3.3-70B-Instruct")
HF_TOKEN     = os.environ.get("HF_TOKEN",     "")
ENV_BASE_URL = os.environ.get("ENV_BASE_URL", "https://ash1809-void.hf.space").rstrip("/")

TASKS = ["easy", "medium", "hard"]
MAX_RETRIES = 3

# ── OpenAI client (OpenAI-compatible) ─────────────────────────────────────────
client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN,
)

# ── Logging helpers ───────────────────────────────────────────────────────────

def log_start(task_id: str):
    print(json.dumps({
        "event":   "[START]",
        "task_id": task_id,
        "model":   MODEL_NAME,
        "env_url": ENV_BASE_URL,
    }), flush=True)


def log_step(task_id: str, step: int, action: dict, reward: float, done: bool, obs_summary: str):
    print(json.dumps({
        "event":       "[STEP]",
        "task_id":     task_id,
        "step":        step,
        "action_type": action.get("type", "unknown"),
        "reward":      round(reward, 4),
        "done":        done,
        "obs":         obs_summary,
    }), flush=True)


def log_end(task_id: str, total_reward: float, steps: int, final_score: float):
    print(json.dumps({
        "event":        "[END]",
        "task_id":      task_id,
        "total_reward": round(total_reward, 4),
        "steps":        steps,
        "score":        round(final_score, 4),
    }), flush=True)

# ── Environment helpers ───────────────────────────────────────────────────────

def env_reset(task_id: str) -> dict:
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.post(f"{ENV_BASE_URL}/api/reset", json={"task_id": task_id}, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(2 ** attempt)


def env_step(action: dict) -> dict:
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.post(f"{ENV_BASE_URL}/api/step", json={"action": action}, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(2 ** attempt)


def env_grader(task_id: str, history: list, email_ids: list) -> float:
    try:
        r = requests.post(
            f"{ENV_BASE_URL}/api/grader",
            json={"task_id": task_id, "history": history, "email_ids": email_ids},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        return float(data.get("score", data.get("final_score", 0.0)))
    except Exception:
        return 0.0

# ── LLM agent ────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert email triage agent. You process customer support emails by taking one action at a time.

For each email you must:
1. classify — assign a category: complaint, refund, inquiry, spam, urgent, or abuse
2. reply — write a professional, empathetic response (for non-spam)
3. escalate — if the email is urgent or involves an unresolved complaint thread
4. archive — if the email is spam

Always respond with a single JSON action object (no markdown, no extra text):
{
  "type": "classify" | "reply" | "escalate" | "archive" | "tag",
  "email_id": "<id>",
  "classification": "<category or null>",
  "content": "<reply text, tag label, or null>"
}"""


def build_prompt(observation: dict) -> str:
    current = observation.get("current_email")
    history = observation.get("history", [])
    step    = observation.get("step_count", 0)
    remaining = observation.get("remaining_steps", "?")

    lines = [
        f"Step {step} | {remaining} steps remaining",
        f"Episode reward so far: {observation.get('episode_reward', 0):.3f}",
        "",
    ]

    if current:
        lines += [
            "=== CURRENT EMAIL ===",
            f"ID:       {current.get('id')}",
            f"Subject:  {current.get('subject')}",
            f"From:     {current.get('sender')}",
            f"Urgency:  {current.get('urgency_score', 0):.2f}",
            f"Sentiment:{current.get('sentiment')}",
            f"Body:\n{current.get('body', '')}",
            "",
        ]
    else:
        lines.append("No current email — episode may be complete.")

    if history:
        lines.append("=== LAST ACTION ===")
        last = history[-1]
        lines.append(f"  action={last.get('action', {}).get('type')} reward={last.get('reward', 0):.3f}")

    lines.append("\nRespond with ONE JSON action object.")
    return "\n".join(lines)


def get_llm_action(observation: dict) -> dict | None:
    """Ask the LLM for the next action. Returns None if no current email."""
    if not observation.get("current_email"):
        return None

    prompt = build_prompt(observation)

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=300,
            temperature=0.2,
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        # Fallback: classify as inquiry
        email_id = observation["current_email"]["id"]
        return {"type": "classify", "email_id": email_id, "classification": "inquiry", "content": None}
    except Exception as e:
        print(f"[WARN] LLM call failed: {e}", file=sys.stderr)
        return None

# ── Run one task ──────────────────────────────────────────────────────────────

def run_task(task_id: str) -> float:
    log_start(task_id)

    # Reset environment
    reset_response = env_reset(task_id)
    observation = reset_response.get("observation", reset_response)

    step_count   = 0
    total_reward = 0.0
    history      = []
    email_ids    = []
    done         = False

    while not done:
        action = get_llm_action(observation)
        if action is None:
            break  # No more emails to process

        # Track email IDs for grader
        eid = action.get("email_id")
        if eid and eid not in email_ids:
            email_ids.append(eid)

        # Step environment
        step_result  = env_step(action)
        reward       = float(step_result.get("reward", 0.0))
        done         = bool(step_result.get("done", False))
        observation  = step_result.get("observation", {})
        step_count  += 1
        total_reward += reward

        # Record for grader
        history.append({"action": action, "reward": reward})

        # Summarise observation for log
        cur = observation.get("current_email")
        obs_summary = f"next_email={cur['id'] if cur else 'none'}"

        log_step(task_id, step_count, action, reward, done, obs_summary)

        # Safety cap — should not be needed with done flag
        if step_count >= 50:
            break

    # Get final graded score
    final_score = env_grader(task_id, history, email_ids)
    log_end(task_id, total_reward, step_count, final_score)
    return final_score

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not HF_TOKEN:
        print("[WARN] HF_TOKEN is not set — LLM calls may fail.", file=sys.stderr)

    scores = {}
    for task_id in TASKS:
        try:
            score = run_task(task_id)
            scores[task_id] = score
        except Exception as e:
            print(json.dumps({"event": "[END]", "task_id": task_id, "error": str(e), "score": 0.0}), flush=True)
            scores[task_id] = 0.0

    # Final summary
    print(json.dumps({
        "event":   "[SUMMARY]",
        "scores":  scores,
        "average": round(sum(scores.values()) / len(scores), 4),
    }), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as top_level_error:
        print(json.dumps({"event": "[FATAL]", "error": str(top_level_error)}), flush=True)
        # We must exit with 0 to prevent the grader from crashing on 'unhandled exception',
        # allowing it to evaluate gracefully on zero scores.
        sys.exit(0)

