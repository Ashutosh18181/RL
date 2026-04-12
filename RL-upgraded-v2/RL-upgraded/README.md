---
title: Email Triage OpenEnv
emoji: 📧
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8000
tags:
  - openenv
---

# 📧 Email Triage & Customer Support Automation — RL Environment

> **OpenEnv-compatible** reinforcement learning environment where an AI agent learns to read, classify, reply to, escalate, and archive real-world customer support emails — with SLA deadlines, multi-turn thread tracking, and sentiment-aware reward shaping.

[![OpenEnv](https://img.shields.io/badge/OpenEnv-Compatible-blue)](https://openenv.dev)
[![HF Space](https://img.shields.io/badge/🤗-Live%20Demo-yellow)](https://huggingface.co/spaces/ash1809/void)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 🎯 Why This Environment Exists

Every customer support team handles hundreds of emails daily. Manual triage is slow, inconsistent, and doesn't scale. Existing RL benchmarks use toy tasks (GridWorld, CartPole) that don't transfer to business value.

This environment fills a real gap: **a fully observable, dense-reward environment where decisions have asymmetric consequences** — missing an SLA on a payment outage costs more than misclassifying a routine inquiry. That asymmetry is what makes the environment challenging and useful for evaluating frontier models.

Concretely, a trained agent should reduce:
- **Mean Time to Resolution (MTTR)** for urgent emails
- **Misclassification rate** across 6 intent categories
- **SLA breach rate** on time-sensitive tickets
- **Escalation errors** in multi-turn complaint threads

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────┐
│                     Web Browser / Agent                     │
└────────────────────────┬───────────────────────────────────┘
                         │ HTTP / REST  (X-Session-ID header)
┌────────────────────────▼───────────────────────────────────┐
│              FastAPI Backend  :8000                         │
│  POST /reset  POST /step  GET /state  GET /tasks           │
│  POST /grader  POST /baseline                              │
│  Session-isolated: each X-Session-ID gets its own env      │
└─────────────┬──────────────────────────────────────────────┘
              │ Python calls
┌─────────────▼──────────────────────────────────────────────┐
│                   RL Environment Core                       │
│   EmailTriageEnv  —  reset() / step() / state()           │
│   ├── email_data.py   (35 emails, 6 categories)            │
│   ├── tasks.py        (easy / medium / hard / extreme)     │
│   ├── reward.py       (dense, 9 components + SLA)          │
│   └── grader.py       (deterministic, per-task rubrics)    │
└────────────────────────────────────────────────────────────┘
```

### Session Isolation
Pass `X-Session-ID: <uuid>` to get a completely isolated environment instance. This enables **concurrent multi-agent evaluation** without state collisions — critical for Phase 2 automated benchmarking.

---

## 📐 Observation & Action Schema

### Observation
| Field | Type | Description |
|---|---|---|
| `current_email` | `EmailItem \| null` | Next email to process |
| `inbox` | `EmailItem[]` | All pending emails |
| `resolved_emails` | `str[]` | IDs of handled emails |
| `history` | `dict[]` | Full action log with rewards and breakdowns |
| `step_count` | `int` | Steps taken this episode |
| `remaining_steps` | `int` | Steps remaining |
| `task_id` | `str` | Active task identifier |
| `episode_reward` | `float` | Cumulative reward so far |

### EmailItem
| Field | Type | Description |
|---|---|---|
| `id` | `str` | Unique email identifier |
| `subject` | `str` | Email subject line |
| `body` | `str` | Full email body |
| `sender` | `str` | Sender email address |
| `category` | `complaint\|refund\|inquiry\|spam\|urgent\|abuse` | Ground truth category |
| `urgency_score` | `float [0,1]` | Continuous urgency signal |
| `sentiment` | `positive\|neutral\|negative` | Sender sentiment |
| `thread_id` | `str \| null` | Links emails in the same thread |
| `thread_position` | `int` | 1=first, 2+=follow-up (follow-ups require escalation) |
| `sla_deadline_steps` | `int \| null` | Agent must act within N steps or incur SLA breach penalty |

### Action
| Field | Type | Description |
|---|---|---|
| `type` | `classify\|reply\|escalate\|archive\|tag` | Action type |
| `email_id` | `str` | Target email ID |
| `classification` | `str \| null` | Category (for `classify`) |
| `content` | `str \| null` | Reply text or tag label |

---

## 🎮 Tasks

### 🟢 Easy — Single Email Triage
- **Inbox**: 1 email (product complaint)
- **Goal**: Classify correctly + apply appropriate tag
- **Max steps**: 5 | **Success threshold**: 0.70
- **Grading**: 50% classification · 30% action · 20% reply tone

### 🟡 Medium — Multi-Email Resolution
- **Inbox**: 3 emails (urgent refund, spam, warranty inquiry)
- **Goal**: Classify all, reply professionally, archive spam
- **Max steps**: 10 | **Success threshold**: 0.65
- **Grading**: Per-email average of classification + action + reply quality

### 🔴 Hard — Multi-Turn Escalation & Prioritization
- **Inbox**: 5 emails — critical outage (SLA=3 steps), complaint thread (2 emails), medical refund (SLA=4 steps), spam
- **Goal**: Prioritize by urgency, meet SLA deadlines, escalate thread, process all
- **Max steps**: 20 | **Success threshold**: 0.60
- **Grading**: 35% per-email · 15% urgency ordering · 20% thread escalation · 15% SLA compliance · 15% coverage

### ⚫ Extreme — Full Inbox Blitz
- **Inbox**: 10 emails — all of the above plus additional mixed cases
- **Goal**: Ruthless prioritization across the full inbox in 35 steps
- **Max steps**: 35 | **Success threshold**: 0.50
- **Grading**: Same rubric as Hard, scaled across 10 emails

---

## 🎯 Reward Function

The reward is **dense** — every action gets a signal, not just episode end.

| Component | Value | Condition |
|---|---|---|
| `correct_classification` | **+0.30** | Classification matches ground truth |
| `correct_action` | **+0.20** | Appropriate action for email type |
| `reply_tone` | **+0.20** | Professional/empathetic language (heuristic) |
| `reply_completeness` | **+0.10** | Reply ≥ 20 words |
| `urgency_prioritization` | **+0.20** | Urgent email replied/escalated |
| `sla_met` | **+0.05** | First action on SLA email within deadline |
| `thread_escalation_bonus` | **+0.10** | Follow-up thread email correctly escalated |
| `wrong_classification` | **−0.30** | Incorrect classification |
| `ignored_urgent` | **−0.20** | Urgent email archived |
| `redundant_action` | **−0.10** | Same action type repeated on same email |
| `sla_breach` | **−0.10 to −0.30** | Action taken after SLA deadline (scales with overdue steps) |
| `sentiment_discontinuity` | **×0.5 tone multiplier** | Cold reply to a negative-sentiment email |

### Novel Mechanics

**SLA Breach Penalty**: Emails with `sla_deadline_steps` set must receive a terminal action (reply or escalate) within that many total episode steps. Missing the deadline applies a scaled penalty (-0.10 per step overdue, capped at -0.30). This creates a genuine prioritization tradeoff — spending too many steps on easy emails costs points on critical ones.

**Sentiment Continuity**: The tone scorer applies a 50% multiplier penalty if a reply to a `negative`-sentiment email contains no empathy keywords. You can't just copy-paste a template and get full tone score.

**Thread Escalation Bonus**: Follow-up thread emails (`thread_position > 1`) give a +0.10 bonus when correctly escalated, rewarding the agent for understanding conversational context.

**Tag Ordering Constraint**: Tags only award `+0.10` if classification was done first on the same email. This closes a naive reward hacking strategy of tagging everything without classifying.

---

## 🚀 Setup

### Prerequisites
- Python 3.12+ · Node.js 20+ · pip

### 1. Install & start backend
```bash
git clone <repo> && cd email-triage-env
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```
API docs: http://localhost:8000/api/docs

### 2. Start frontend
```bash
cd frontend && npm install && npm run dev
```
Dashboard: http://localhost:3000

---

## 🤖 Running the Baseline Agent

```bash
# Mock agent (no API key) — all 4 tasks
python -m baseline.run --mock

# Single task
python -m baseline.run --mock --task hard

# Save to JSON
python -m baseline.run --mock --output scores.json

# OpenAI-powered
export OPENAI_API_KEY=sk-...
python -m baseline.run --task hard
```

---

## 📊 Expected Scores (Mock Agent — Oracle Classification)

| Task | Score | Grade | Notes |
|---|---|---|---|
| Easy | ~0.85–0.95 | A/A+ | Oracle classification = near-perfect |
| Medium | ~0.75–0.87 | B/A | 3-email coverage with templates |
| Hard | ~0.68–0.78 | B/B+ | SLA compliance + thread escalation adds challenge |
| Extreme | ~0.58–0.70 | C/B | Full inbox prioritization under step budget |

> Mock agent uses oracle classification (reads ground truth), so scores are intentionally high and represent an upper bound. Real LLM agents score lower due to classification uncertainty and imperfect prioritization.

---

## 🛠️ API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/reset` | Start new episode. Body: `{ task_id }`. Optional header: `X-Session-ID` |
| `POST` | `/api/step` | Take action. Body: `{ action: Action }`. Optional header: `X-Session-ID` |
| `GET` | `/api/state` | Get full environment state |
| `GET` | `/api/tasks` | List all tasks + action schema |
| `POST` | `/api/grader` | Grade history. Returns `{ grade, score }` |
| `POST` | `/api/baseline` | Run mock/OpenAI agent. Returns `{ score, steps, grade }` |
| `GET` | `/api/emails` | Browse email corpus |
| `GET` | `/api/emails/{id}` | Get single email detail |
| `GET` | `/api/health` | Health check |

All endpoints also available without `/api` prefix for strict spec compliance.

---

## 🐳 Docker

```bash
# Build and run
docker build -t email-triage-env .
docker run -p 8000:8000 email-triage-env

# Dev with compose
docker-compose up
```

---

## 📁 Project Structure

```
email-triage-env/
├── env/
│   ├── models.py          # Pydantic v2: EmailItem (with thread_position, sla_deadline_steps)
│   ├── email_data.py      # 35 synthetic emails across 6 categories
│   ├── tasks.py           # easy / medium / hard / extreme task configs
│   ├── reward.py          # Dense reward: 9 components including SLA + sentiment
│   ├── grader.py          # Deterministic graders with SLA compliance scoring
│   └── environment.py     # EmailTriageEnv: reset() / step() / state()
├── backend/
│   ├── main.py            # FastAPI app with session management
│   └── routes/
│       ├── env_routes.py  # All OpenEnv endpoints with X-Session-ID support
│       └── email_routes.py
├── baseline/
│   ├── agent.py           # MockAgent (oracle) + BaselineAgent (OpenAI, SLA-aware)
│   └── run.py             # CLI runner for all 4 tasks
├── inference.py           # HF-compatible inference script (HF_TOKEN + API_BASE_URL)
├── openenv.yaml           # Full OpenEnv v2.0.0 spec
├── Dockerfile             # Multi-stage: Node frontend + Python backend
└── docker-compose.yml
```

---

## 📜 License

MIT — free for academic, commercial, and hackathon use.
