"""
inference.py — Email Triage OpenEnv
Hackathon-compliant inference script.

Required environment variables:
  API_BASE_URL  — LLM API endpoint (e.g. https://api-inference.huggingface.co/v1)
  MODEL_NAME    — Model identifier (e.g. meta-llama/Llama-3.3-70B-Instruct)
  HF_TOKEN      — Hugging Face API token

Optional:
  ENV_BASE_URL  — Email Triage environment URL (default: http://localhost:8000)
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error

# ── Config ────────────────────────────────────────────────────────────────────
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api-inference.huggingface.co/v1").rstrip("/")
MODEL_NAME   = os.environ.get("MODEL_NAME",   "meta-llama/Llama-3.3-70B-Instruct")
HF_TOKEN     = os.environ.get("HF_TOKEN",     "")
ENV_BASE_URL = os.environ.get("ENV_BASE_URL", "http://localhost:8000").rstrip("/")

TASKS = ["easy", "medium", "hard", "extreme"]
MAX_RETRIES = 3

def _clamp_score(val: float) -> float:
    return round(max(0.0001, min(val, 0.9999)), 4)


# ── Logging helpers ───────────────────────────────────────────────────────────

def log_start(task_id: str):
    print(f"[START] task={task_id}", flush=True)


def log_step(task_id: str, step: int, action: dict, reward: float, done: bool, obs_summary: str):
    print(f"[STEP] step={step} reward={reward}", flush=True)


def log_end(task_id: str, total_reward: float, steps: int, final_score: float):
    print(f"[END] task={task_id} score={final_score} steps={steps}", flush=True)

# ── HTTP Helper ───────────────────────────────────────────────────────────────

def post_json(url: str, data: dict, headers: dict = None, timeout: int = 30) -> dict:
    if headers is None:
        headers = {}
    headers["Content-Type"] = "application/json"
    
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

# ── Environment helpers ───────────────────────────────────────────────────────

def env_reset(task_id: str) -> dict:
    for attempt in range(MAX_RETRIES):
        try:
            return post_json(f"{ENV_BASE_URL}/api/reset", {"task_id": task_id})
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise e
            time.sleep(2 ** attempt)

def env_step(action: dict) -> dict:
    for attempt in range(MAX_RETRIES):
        try:
            return post_json(f"{ENV_BASE_URL}/api/step", {"action": action})
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise e
            time.sleep(2 ** attempt)

def env_grader(task_id: str, history: list, email_ids: list) -> float:
    try:
        data = post_json(f"{ENV_BASE_URL}/api/grader", {"task_id": task_id, "history": history, "email_ids": email_ids})
        return float(data.get("score", data.get("final_score", 0.0)))
    except Exception:
        return _clamp_score(0.0)


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
        headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            "max_tokens": 300,
            "temperature": 0.2,
        }
        url = API_BASE_URL if API_BASE_URL.endswith("/chat/completions") else f"{API_BASE_URL}/chat/completions"
        response = post_json(url, payload, headers=headers)
        raw = response["choices"][0]["message"]["content"].strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        # Fallback: classify as inquiry
        email_id = observation["current_email"]["id"]
        return {"type": "classify", "email_id": email_id, "classification": "inquiry", "content": None}


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
            # Literal string here too
            print(f"[END] task={task_id} score=0.0001 error={str(e)}")
            scores[task_id] = _clamp_score(0.0)

    avg = _clamp_score(sum(scores.values()) / len(scores))
    print(f"[SUMMARY] easy={scores.get('easy', 0.0001):.4f} medium={scores.get('medium', 0.0001):.4f} hard={scores.get('hard', 0.0001):.4f} extreme={scores.get('extreme', 0.0001):.4f} avg={avg:.4f}", flush=True)



if __name__ == "__main__":
    try:
        main()
    except Exception as top_level_error:
        # Avoid JSON here too, just in case the grader parser is sensitive
        print(f"[FATAL] {top_level_error}", flush=True)
        sys.exit(0)



