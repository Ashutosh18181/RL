'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import EmailCard from '@/components/EmailCard'
import ActionPanel from '@/components/ActionPanel'
import LogPanel from '@/components/LogPanel'
import ScoreDisplay from '@/components/ScoreDisplay'

// ─── Types (mirrors backend Pydantic models) ──────────────────────────────────
export interface EmailItem {
  id: string
  subject: string
  body: string
  sender: string
  sender_name: string
  category: string
  urgency_score: number
  sentiment: string
  timestamp: string
  thread_id?: string
  is_resolved: boolean
}

export interface TaskConfig {
  id: string
  name: string
  description: string
  max_steps: number
  difficulty: string
  objective: string
  success_threshold: number
  email_ids: string[]
}

export interface RewardBreakdown { [key: string]: number }

export interface RewardData {
  value: number
  breakdown: RewardBreakdown
  message: string
}

export interface LogEntry {
  step: number
  action_type: string
  email_id: string
  classification?: string
  content?: string
  reward: number
  breakdown: RewardBreakdown
  message: string
}

export interface GradeData {
  task_id: string
  score: number
  total_steps: number
  passed: boolean
  grade_letter: string
}

export interface ObservationData {
  current_email: EmailItem | null
  inbox: EmailItem[]
  resolved_emails: string[]
  history: LogEntry[]
  step_count: number
  remaining_steps: number
  task_id: string
  task_description: string
  episode_reward: number
}

export interface Toast {
  id: string
  type: 'success' | 'error' | 'info'
  message: string
}

// ─── API base ─────────────────────────────────────────────────────────────────
const API = process.env.NEXT_PUBLIC_API_URL || '/api'

async function apiFetch(path: string, opts?: RequestInit) {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'API error')
  }
  return res.json()
}

// ─── Main App ─────────────────────────────────────────────────────────────────
export default function Home() {
  const [tasks, setTasks] = useState<TaskConfig[]>([])
  const [selectedTask, setSelectedTask] = useState<string>('easy')
  const [observation, setObservation] = useState<ObservationData | null>(null)
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [episodeReward, setEpisodeReward] = useState(0)
  const [grade, setGrade] = useState<GradeData | null>(null)
  const [done, setDone] = useState(false)
  const [loading, setLoading] = useState(false)
  const [baselineRunning, setBaselineRunning] = useState(false)
  const [baselineResult, setBaselineResult] = useState<any>(null)
  const [toasts, setToasts] = useState<Toast[]>([])
  const toastId = useRef(0)

  // ─── Toast helpers ────────────────────────────────────────────────────────
  const toast = useCallback((type: Toast['type'], message: string) => {
    const id = String(++toastId.current)
    setToasts(t => [...t, { id, type, message }])
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 3500)
  }, [])

  // ─── Load tasks on mount ──────────────────────────────────────────────────
  useEffect(() => {
    apiFetch('/tasks')
      .then(data => setTasks(data.tasks))
      .catch(() => toast('error', 'Cannot connect to backend. Make sure it is running.'))
  }, []) // eslint-disable-line

  // ─── Reset episode ────────────────────────────────────────────────────────
  const handleReset = useCallback(async () => {
    setLoading(true)
    setGrade(null)
    setDone(false)
    setLogs([])
    setEpisodeReward(0)
    setBaselineResult(null)
    try {
      const data = await apiFetch('/reset', {
        method: 'POST',
        body: JSON.stringify({ task_id: selectedTask }),
      })
      setObservation(data.observation)
      setSelectedEmailId(data.observation.current_email?.id || null)
      toast('success', `Episode started — Task: ${selectedTask.toUpperCase()}`)
    } catch (e: any) {
      toast('error', e.message)
    } finally {
      setLoading(false)
    }
  }, [selectedTask, toast])

  // Auto-reset when task changes
  useEffect(() => {
    handleReset()
  }, [selectedTask]) // eslint-disable-line

  // ─── Step (take action) ───────────────────────────────────────────────────
  const handleStep = useCallback(async (action: object) => {
    if (done || !observation) return
    setLoading(true)
    try {
      const data = await apiFetch('/step', {
        method: 'POST',
        body: JSON.stringify({ action }),
      })
      const newObs: ObservationData = data.observation
      const reward: RewardData = data.reward

      setObservation(newObs)
      setEpisodeReward(newObs.episode_reward)

      // Build log entry
      const entry: LogEntry = {
        step: newObs.step_count - 1,
        action_type: (action as any).type,
        email_id: (action as any).email_id,
        classification: (action as any).classification,
        content: (action as any).content,
        reward: reward.value,
        breakdown: reward.breakdown,
        message: reward.message,
      }
      setLogs(l => [...l, entry])

      if (data.done) {
        setDone(true)
        if (data.info?.final_grade) setGrade(data.info.final_grade)
        toast('info', `Episode complete! Score: ${data.info?.final_grade?.score?.toFixed(3) ?? '...'}`)
      } else {
        const r = reward.value
        if (r > 0) toast('success', `+${r.toFixed(3)} reward`)
        else if (r < 0) toast('error', `${r.toFixed(3)} penalty`)
      }
    } catch (e: any) {
      toast('error', e.message)
    } finally {
      setLoading(false)
    }
  }, [done, observation, toast])

  // ─── Run baseline ─────────────────────────────────────────────────────────
  const handleBaseline = useCallback(async () => {
    setBaselineRunning(true)
    setBaselineResult(null)
    try {
      const data = await apiFetch('/baseline', {
        method: 'POST',
        body: JSON.stringify({ task_id: selectedTask, mock: true }),
      })
      setBaselineResult(data)
      // Reload state from baseline run
      setLogs(data.steps.map((s: any) => ({
        step: s.step,
        action_type: s.action.type,
        email_id: s.action.email_id,
        classification: s.action.classification,
        reward: s.reward.value,
        breakdown: s.reward.breakdown,
        message: s.reward.message,
      })))
      setGrade(data.grade)
      setDone(true)
      setEpisodeReward(data.total_reward)
      toast('success', `Baseline complete! Score: ${data.grade.score.toFixed(3)}`)
    } catch (e: any) {
      toast('error', `Baseline failed: ${e.message}`)
    } finally {
      setBaselineRunning(false)
    }
  }, [selectedTask, toast])

  const currentTask = tasks.find(t => t.id === selectedTask)
  const activeEmail = observation?.inbox.find(e => e.id === selectedEmailId) || observation?.current_email || null

  return (
    <div className="app-layout">
      {/* ── Header ──────────────────────────────────────────────────── */}
      <header className="header">
        <div className="header-brand">
          <div className="header-logo">📧</div>
          <div>
            <div className="header-title">Email Triage RL Environment</div>
            <div className="header-subtitle">OpenEnv-Compatible AI Training System</div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          {observation && (
            <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
              Step{' '}
              <span style={{ color: 'var(--text-primary)', fontWeight: 700 }}>
                {observation.step_count}
              </span>
              /{(observation.step_count + observation.remaining_steps)}
            </div>
          )}
          <div className="header-badge">
            <div className="header-badge-dot" />
            API Connected
          </div>
        </div>
      </header>

      {/* ── 3-column grid ──────────────────────────────────────────── */}
      <main className="main-grid">
        {/* LEFT — Task Selector + Score */}
        <aside className="panel">
          <div className="panel-header">
            <span className="panel-title">Tasks</span>
            <span className="panel-count">{tasks.length}</span>
          </div>

          <div className="task-selector">
            {tasks.length === 0 && (
              <div style={{ color: 'var(--text-muted)', fontSize: 12, padding: 8 }}>
                Loading tasks…
              </div>
            )}
            {tasks.map(task => (
              <div
                key={task.id}
                className={`task-card ${selectedTask === task.id ? 'active' : ''}`}
                onClick={() => setSelectedTask(task.id)}
              >
                <div className="task-card-header">
                  <div className="task-card-name">{task.name}</div>
                  <span className={`difficulty-badge difficulty-${task.difficulty}`}>
                    {task.difficulty}
                  </span>
                </div>
                <div className="task-card-desc">{task.objective}</div>
                <div className="task-meta">
                  <div className="task-meta-item">⚡ {task.max_steps} steps</div>
                  <div className="task-meta-item">📬 {task.email_ids.length} emails</div>
                  <div className="task-meta-item">🎯 {(task.success_threshold * 100).toFixed(0)}% threshold</div>
                </div>
              </div>
            ))}
          </div>

          <div className="panel-header" style={{ marginTop: 8 }}>
            <span className="panel-title">Episode Score</span>
          </div>
          <ScoreDisplay
            episodeReward={episodeReward}
            grade={grade}
            done={done}
            totalSteps={logs.length}
            maxSteps={currentTask?.max_steps ?? 20}
            lastBreakdown={logs[logs.length - 1]?.breakdown ?? null}
          />
        </aside>

        {/* CENTER — Email Workspace + Action Panel */}
        <section className="center-panel">
          <div className="email-workspace">
            {!observation || observation.inbox.length === 0 && !done ? (
              <div className="empty-inbox">
                <div className="empty-inbox-icon">📭</div>
                <div className="empty-inbox-text">
                  Select a task and click <strong>Reset</strong> to start an episode.
                  <br />The inbox will appear here.
                </div>
              </div>
            ) : (
              <>
                {done && (
                  <div className="episode-done-banner">
                    <div className="episode-done-title">
                      {grade?.passed ? '🎉 Episode Complete — Passed!' : '⚠️ Episode Complete'}
                    </div>
                    <div className="episode-done-sub">
                      Score: {grade?.score?.toFixed(4)} | Grade: {grade?.grade_letter} | Steps: {logs.length}
                    </div>
                  </div>
                )}
                {observation.inbox.map(email => (
                  <EmailCard
                    key={email.id}
                    email={email}
                    isActive={email.id === activeEmail?.id}
                    isResolved={false}
                    onClick={() => setSelectedEmailId(email.id)}
                  />
                ))}
                {observation.resolved_emails.map(id => (
                  <EmailCard
                    key={`resolved-${id}`}
                    email={{ id, subject: id, body: '', sender: '', sender_name: '', category: 'inquiry', urgency_score: 0, sentiment: 'neutral', timestamp: '', is_resolved: true }}
                    isActive={false}
                    isResolved={true}
                  />
                ))}
              </>
            )}
          </div>

          {/* Action Panel */}
          <ActionPanel
            currentEmail={activeEmail}
            done={done}
            loading={loading}
            baselineRunning={baselineRunning}
            onStep={handleStep}
            onReset={handleReset}
            onBaseline={handleBaseline}
          />
        </section>

        {/* RIGHT — Logs + Baseline */}
        <aside className="panel logs-panel">
          <div className="panel-header">
            <span className="panel-title">Action Log</span>
            <span className="panel-count">{logs.length} steps</span>
          </div>
          <LogPanel logs={logs} baselineResult={baselineResult} />
        </aside>
      </main>

      {/* Toasts */}
      <div className="toast-container">
        {toasts.map(t => (
          <div key={t.id} className={`toast toast-${t.type}`}>{t.message}</div>
        ))}
      </div>
    </div>
  )
}
