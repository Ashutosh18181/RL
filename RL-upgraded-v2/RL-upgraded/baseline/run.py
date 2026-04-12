"""
Baseline runner — executes all 3 tasks and reports scores.

Usage:
  python -m baseline.run                  # requires OPENAI_API_KEY
  python -m baseline.run --mock           # rule-based oracle agent, no key needed
  python -m baseline.run --task easy      # single task
  python -m baseline.run --output scores.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from typing import Any

# ── ensure project root is on the path ────────────────────────────────────────
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.environment import EmailTriageEnv
from env.grader import grade_episode
from env.tasks import ALL_TASKS
from baseline.agent import BaselineAgent, MockAgent


# ─── ANSI colours ─────────────────────────────────────────────────────────────
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def colour_reward(r: float) -> str:
    c = GREEN if r > 0 else (RED if r < 0 else YELLOW)
    return f"{c}{r:+.4f}{RESET}"


def run_task(
    task_id: str,
    agent: BaselineAgent | MockAgent,
    verbose: bool = True,
) -> dict[str, Any]:
    """Run a single task episode and return full result."""
    env = EmailTriageEnv()
    obs = env.reset(task_id=task_id)
    task = ALL_TASKS[task_id]

    if verbose:
        print(f"\n{BOLD}{CYAN}{'═' * 60}{RESET}")
        print(f"{BOLD}  TASK: {task.name} [{task.difficulty.upper()}]{RESET}")
        print(f"  {task.description}")
        print(f"  Max steps: {task.max_steps} | Emails: {len(task.email_ids)}")
        print(f"{BOLD}{CYAN}{'═' * 60}{RESET}\n")

    steps_log: list[dict[str, Any]] = []
    total_reward = 0.0
    done = False
    step_num = 0

    while not done:
        action = agent.act(obs)

        if verbose:
            print(f"  {BOLD}Step {step_num:02d}{RESET} → [{action.type.value.upper()}] "
                  f"email={action.email_id}", end="")
            if action.classification:
                print(f" | class={action.classification}", end="")
            if action.content:
                preview = action.content[:60].replace("\n", " ")
                print(f" | \"{preview}...\"", end="")
            print()

        result = env.step(action)
        r = result.reward

        if verbose:
            bd_str = ", ".join(f"{k}={v:+.3f}" for k, v in r.breakdown.items())
            print(f"           {colour_reward(r.value)} [{bd_str}]")
            if r.message:
                print(f"           → {r.message[:100]}")

        steps_log.append({
            "step": step_num,
            "action": action.model_dump(),
            "reward": r.model_dump(),
            "done": result.done,
        })

        total_reward += r.value
        done = result.done
        obs = result.observation
        step_num += 1

    # Grade episode
    final_state = env.state()
    grade = grade_episode(
        task_id=task_id,
        history=final_state["history"],
        task_email_ids=task.email_ids,
    )

    if verbose:
        grade_colour = GREEN if grade["passed"] else RED
        print(f"\n  {BOLD}── Episode Summary ──{RESET}")
        print(f"  Total steps    : {step_num}")
        print(f"  Cumulative rew : {colour_reward(round(total_reward, 4))}")
        print(f"  Score (grader) : {grade_colour}{grade['score']:.4f}{RESET}")
        print(f"  Grade letter   : {grade_colour}{grade['grade_letter']}{RESET}")
        print(f"  Passed         : {grade_colour}{'✓ YES' if grade['passed'] else '✗ NO'}{RESET}")

    return {
        "task_id": task_id,
        "task_name": task.name,
        "difficulty": task.difficulty,
        "total_steps": step_num,
        "cumulative_reward": round(total_reward, 4),
        "score": grade["score"],
        "grade_letter": grade["grade_letter"],
        "passed": grade["passed"],
        "steps": steps_log,
    }


def run_all(
    tasks: list[str],
    mock: bool,
    verbose: bool,
    output: str | None,
) -> None:
    agent_cls = MockAgent if mock else BaselineAgent
    agent_name = "MockAgent (Rule-Based Oracle)" if mock else "BaselineAgent (gpt-4o-mini)"

    print(f"\n{BOLD}{'━' * 60}{RESET}")
    print(f"{BOLD}  Email Triage RL Environment — Baseline Runner{RESET}")
    print(f"  Agent      : {agent_name}")
    print(f"  Tasks      : {', '.join(tasks)}")
    print(f"  Timestamp  : {datetime.utcnow().isoformat()}Z")
    print(f"{BOLD}{'━' * 60}{RESET}")

    agent = agent_cls()
    results: list[dict[str, Any]] = []
    t_start = time.perf_counter()

    for task_id in tasks:
        result = run_task(task_id, agent, verbose=verbose)
        results.append(result)

    elapsed = time.perf_counter() - t_start
    avg_score = sum(r["score"] for r in results) / len(results)
    all_passed = all(r["passed"] for r in results)

    print(f"\n{BOLD}{'━' * 60}{RESET}")
    print(f"{BOLD}  OVERALL RESULTS{RESET}")
    print(f"{'━' * 60}")
    print(f"  {'Task':<35} {'Score':>7} {'Grade':>6} {'Passed':>8}")
    print(f"  {'─' * 57}")
    for r in results:
        c = GREEN if r["passed"] else RED
        print(
            f"  {r['task_name']:<35} "
            f"{c}{r['score']:>7.4f}{RESET} "
            f"{c}{r['grade_letter']:>6}{RESET} "
            f"{c}{'YES':>8}{RESET}" if r["passed"] else
            f"  {r['task_name']:<35} "
            f"{RED}{r['score']:>7.4f}{RESET} "
            f"{RED}{r['grade_letter']:>6}{RESET} "
            f"{RED}{'NO':>8}{RESET}"
        )
    print(f"  {'─' * 57}")
    avg_c = GREEN if avg_score >= 0.65 else RED
    print(f"  {'AVERAGE':<35} {avg_c}{avg_score:>7.4f}{RESET}")
    print(f"  {'ALL PASSED':<35} {GREEN if all_passed else RED}{'YES' if all_passed else 'NO':>7}{RESET}")
    print(f"  Runtime: {elapsed:.2f}s")
    print(f"{BOLD}{'━' * 60}{RESET}\n")

    summary = {
        "agent": agent_name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "runtime_seconds": round(elapsed, 2),
        "average_score": round(avg_score, 4),
        "all_passed": all_passed,
        "results": results,
    }

    if output:
        with open(output, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"  Results saved to: {output}")

    # Print clean JSON to stdout as well
    print(json.dumps({"average_score": avg_score, "all_passed": all_passed,
                      "per_task": [{
                          "task": r["task_id"], "score": r["score"],
                          "grade": r["grade_letter"], "passed": r["passed"]
                      } for r in results]}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Email Triage RL baseline agent across all tasks."
    )
    parser.add_argument(
        "--mock", action="store_true",
        help="Use rule-based mock agent (no OpenAI API key required)"
    )
    parser.add_argument(
        "--task", choices=["easy", "medium", "hard", "extreme", "all"], default="all",
        help="Which task(s) to run (default: all)"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Optional path to save JSON results (e.g. scores.json)"
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress per-step output"
    )
    args = parser.parse_args()

    tasks = ["easy", "medium", "hard", "extreme"] if args.task == "all" else [args.task]
    run_all(tasks=tasks, mock=args.mock, verbose=not args.quiet, output=args.output)


if __name__ == "__main__":
    main()
