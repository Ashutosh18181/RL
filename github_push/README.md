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

> **OpenEnv-compatible** reinforcement learning environment where an AI agent learns to read, classify, reply to, escalate, and archive real-world customer support emails.

---

## 🎯 Problem Motivation

Every customer support team handles hundreds of emails daily. Manual triage is slow, error-prone, and inconsistent. An RL agent trained in this environment learns to:

- **Prioritize** urgent issues before routine inquiries
- **Classify** intent correctly (complaint, refund, inquiry, spam, urgent, abuse)
- **Respond** with professional, empathetic tone
- **Escalate** issues that require senior intervention
- **Archive** spam without wasting response time

This directly maps to real business value: reducing mean time to resolution (MTTR), improving CSAT scores, and freeing human agents for complex cases.

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────┐
│                     Web Browser                            │
│   ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐  │
│   │ Task Selector│ │ Email Viewer │ │   Action Log     │  │
│   │ + Score Ring │ │ + Action     │ │   + Baseline     │  │
│   └──────────────┘ └──────────────┘ └──────────────────┘  │
└────────────────────────────┬───────────────────────────────┘
                             │ HTTP / REST
┌────────────────────────────▼───────────────────────────────┐
│                  FastAPI Backend  :8000                     │
│   POST /reset   POST /step   GET /state   GET /tasks       │
│   POST /grader  POST /baseline                             │
└──────────────┬─────────────────────────────────────────────┘
               │ Python calls
┌──────────────▼─────────────────────────────────────────────┐
│                   RL Environment Core                       │
│   EmailTriageEnv  ─  reset() / step() / state()           │
│   ├── email_data.py  (35 synthetic emails)                 │
│   ├── tasks.py       (easy / medium / hard)                │
│   ├── reward.py      (dense reward, 7 components)          │
│   └── grader.py      (deterministic graders)               │
└────────────────────────────────────────────────────────────┘
```

---

## 📐 Observation & Action Schema

### Observation
| Field | Type | Description |
|---|---|---|
| `current_email` | `EmailItem \| null` | Next email to process |
| `inbox` | `EmailItem[]` | All pending emails |
| `resolved_emails` | `str[]` | IDs of handled emails |
| `history` | `dict[]` | Full action log with rewards |
| `step_count` | `int` | Steps taken this episode |
| `remaining_steps` | `int` | Steps remaining |
| `episode_reward` | `float` | Cumulative reward so far |

### EmailItem
| Field | Type |
|---|---|
| `id` | `str` |
| `subject` | `str` |
| `body` | `str` |
| `sender` | `str` |
| `category` | `complaint\|refund\|inquiry\|spam\|urgent\|abuse` |
| `urgency_score` | `float [0,1]` |
| `sentiment` | `positive\|neutral\|negative` |

### Action
| Field | Type | Description |
|---|---|---|
| `type` | `classify\|reply\|escalate\|archive\|tag` | Action type |
| `email_id` | `str` | Target email ID |
| `classification` | `str \| null` | Category (for `classify` action) |
| `content` | `str \| null` | Reply text / tag label |

---

## 🎮 Tasks

### 🟢 Easy — Single Email Triage
- **Inbox**: 1 email (product complaint)
- **Goal**: Classify correctly + apply appropriate tag
- **Max steps**: 5
- **Success threshold**: 0.70
- **Grading**: 50% classification, 30% action, 20% reply tone

### 🟡 Medium — Multi-Email Resolution
- **Inbox**: 3 emails (urgent refund, spam, warranty inquiry)
- **Goal**: Classify all, reply professionally, archive spam
- **Max steps**: 10
- **Success threshold**: 0.65
- **Grading**: Per-email score averaging classification + action + reply quality

### 🔴 Hard — Multi-Turn Escalation & Prioritization
- **Inbox**: 5 emails including a critical system outage, 2-email complaint thread, medical refund, spam
- **Goal**: Prioritize by urgency, escalate the thread, process all correctly
- **Max steps**: 20
- **Success threshold**: 0.60
- **Grading**: 40% per-email + 20% urgency ordering + 20% thread escalation + 20% coverage

---

## 🎯 Reward Function

| Component | Value | Condition |
|---|---|---|
| `correct_classification` | **+0.30** | Classification matches ground truth |
| `correct_action` | **+0.20** | Appropriate action for email type |
| `reply_tone` | **+0.20** | Professional/empathetic language (heuristic) |
| `reply_completeness` | **+0.10** | Reply ≥ 20 words |
| `urgency_prioritization` | **+0.20** | Urgent email replied/escalated |
| `wrong_classification` | **−0.30** | Incorrect classification |
| `ignored_urgent` | **−0.20** | Urgent email archived |
| `redundant_action` | **−0.10** | Same action type repeated on same email |

---

## 🚀 Setup

### Prerequisites
- Python 3.12+
- Node.js 20+
- pip

### 1. Clone & install backend
```bash
git clone <repo>
cd email-triage-env
pip install -r requirements.txt
```

### 2. Start backend
```bash
uvicorn backend.main:app --reload --port 8000
```

Open API docs: http://localhost:8000/api/docs

### 3. Start frontend
```bash
cd frontend
npm install
npm run dev
```

Open dashboard: http://localhost:3000

---

## 🤖 Running the Baseline Agent

### Mock agent (no API key needed)
```bash
python -m baseline.run --mock
```

### Run a specific task only
```bash
python -m baseline.run --mock --task easy
python -m baseline.run --mock --task medium
python -m baseline.run --mock --task hard
```

### OpenAI-powered agent
```bash
export OPENAI_API_KEY=sk-...
python -m baseline.run
```

### Save results to JSON
```bash
python -m baseline.run --mock --output scores.json
```

---

## 📊 Expected Scores (Mock Agent)

| Task | Score | Grade | Notes |
|---|---|---|---|
| Easy | ~0.85–0.95 | A/A+ | Oracle classification = near-perfect |
| Medium | ~0.75–0.87 | B/A | 3-email coverage with templates |
| Hard | ~0.65–0.78 | C/B | Urgency ordering + thread escalation logic |

> The mock agent uses oracle classification (it knows the ground truth category), so scores are intentionally high and represent an upper bound. The OpenAI agent will score lower due to classification uncertainty.

---

## 🛠️ API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/reset` | Start new episode. Body: `{ task_id: "easy"\|"medium"\|"hard" }` |
| `POST` | `/api/step` | Take action. Body: `{ action: Action }` |
| `GET` | `/api/state` | Get full environment state |
| `GET` | `/api/tasks` | List all task configs |
| `POST` | `/api/grader` | Grade a history. Body: `{ task_id, history, email_ids }` |
| `POST` | `/api/baseline` | Run mock/OpenAI agent. Body: `{ task_id, mock: true }` |
| `GET` | `/api/emails` | Browse full email corpus |
| `GET` | `/api/emails/{id}` | Get single email detail |

---

## 🐳 Docker

### Build and run (single container)
```bash
docker build -t email-triage-env .
docker run -p 8000:8000 email-triage-env
```

Access: http://localhost:8000

### Development with Docker Compose
```bash
docker-compose up
```

- Backend API: http://localhost:8000/api/docs
- Frontend dev: http://localhost:3000

### Hugging Face Spaces deployment
1. Push to a Hugging Face Space with `Dockerfile`
2. Set `OPENAI_API_KEY` as a Space secret (optional)
3. Port 8000 is exposed automatically

---

## 📁 Project Structure

```
email-triage-env/
├── env/
│   ├── __init__.py        # Package exports
│   ├── models.py          # Pydantic v2 models
│   ├── email_data.py      # 35 synthetic emails
│   ├── tasks.py           # Task configurations
│   ├── reward.py          # Dense reward function
│   ├── grader.py          # Deterministic graders
│   └── environment.py     # EmailTriageEnv class
├── backend/
│   ├── main.py            # FastAPI app
│   └── routes/
│       ├── env_routes.py  # /reset /step /state /tasks /grader /baseline
│       └── email_routes.py# /emails /emails/{id}
├── baseline/
│   ├── agent.py           # MockAgent + BaselineAgent (OpenAI)
│   └── run.py             # CLI runner
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx       # Main dashboard
│   │   └── globals.css
│   └── components/
│       ├── EmailCard.tsx
│       ├── ActionPanel.tsx
│       ├── LogPanel.tsx
│       └── ScoreDisplay.tsx
├── openenv.yaml           # OpenEnv spec
├── Dockerfile             # Multi-stage build
├── docker-compose.yml
└── requirements.txt
```

---

## 📜 License

MIT — Free for academic, commercial, and hackathon use.
