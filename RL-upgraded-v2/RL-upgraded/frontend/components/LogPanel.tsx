'use client'

import type { LogEntry } from '@/app/page'

interface Props {
  logs: LogEntry[]
  baselineResult: any
}

const ACTION_ICONS: Record<string, string> = {
  classify: '🏷',
  reply: '✉️',
  escalate: '🚨',
  archive: '🗄',
  tag: '🔖',
}

const ACTION_COLORS: Record<string, string> = {
  classify: 'var(--accent-blue)',
  reply: 'var(--accent-green)',
  escalate: 'var(--accent-orange)',
  archive: 'var(--text-secondary)',
  tag: 'var(--accent-purple)',
}

function formatKey(key: string): string {
  return key.replace(/_/g, ' ')
}

export default function LogPanel({ logs, baselineResult }: Props) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
      <div className="log-timeline">
        {logs.length === 0 && (
          <div className="log-empty">
            <div className="log-empty-icon">📋</div>
            <div>No actions yet.<br />Reset an episode and start taking actions.</div>
          </div>
        )}

        {[...logs].reverse().map((log, i) => {
          const r = log.reward
          const isPos = r > 0
          const isNeg = r < 0
          const color = ACTION_COLORS[log.action_type] ?? 'var(--accent-blue)'

          return (
            <div key={`${log.step}-${i}`} className="log-entry">
              <div className="log-step-num">{log.step}</div>
              <div className="log-entry-content">
                <div className="log-action-type" style={{ color }}>
                  {ACTION_ICONS[log.action_type] ?? ''} {log.action_type}
                </div>
                <div className="log-email-id">
                  {log.email_id}
                  {log.classification && (
                    <span style={{ color: 'var(--accent-blue)', marginLeft: 6 }}>
                      → {log.classification}
                    </span>
                  )}
                </div>

                <div className="log-reward-row">
                  <span className={`log-reward ${isPos ? 'pos' : isNeg ? 'neg' : 'zero'}`}>
                    {isPos ? '+' : ''}{r.toFixed(4)}
                  </span>
                  <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>reward</span>
                </div>

                {/* Breakdown chips */}
                {Object.entries(log.breakdown).length > 0 && (
                  <div className="log-breakdown">
                    {Object.entries(log.breakdown).map(([k, v]) => (
                      <span
                        key={k}
                        className={`log-bd-chip ${v >= 0 ? 'pos' : 'neg'}`}
                      >
                        {v >= 0 ? '+' : ''}{v.toFixed(2)} {formatKey(k)}
                      </span>
                    ))}
                  </div>
                )}

                {log.message && (
                  <div className="log-msg">{log.message.slice(0, 120)}</div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Baseline result summary */}
      {baselineResult && (
        <div className="baseline-result">
          <div className="baseline-result-title">🤖 Mock Agent Results</div>
          <div className="baseline-score-row">
            <span className="baseline-task-name">Task: {baselineResult.task_id}</span>
            <span
              className="baseline-grade"
              style={{ color: baselineResult.grade?.passed ? 'var(--accent-green)' : 'var(--accent-red)' }}
            >
              {baselineResult.grade?.grade_letter} — {baselineResult.grade?.score?.toFixed(4)}
            </span>
          </div>
          <div className="baseline-score-row">
            <span className="baseline-task-name">Steps taken</span>
            <span className="baseline-grade" style={{ color: 'var(--accent-blue)', fontSize: 14 }}>
              {baselineResult.total_steps}
            </span>
          </div>
          <div className="baseline-score-row">
            <span className="baseline-task-name">Total reward</span>
            <span
              className="baseline-grade"
              style={{
                color: baselineResult.total_reward >= 0 ? 'var(--accent-green)' : 'var(--accent-red)',
                fontSize: 14,
              }}
            >
              {baselineResult.total_reward >= 0 ? '+' : ''}{baselineResult.total_reward?.toFixed(4)}
            </span>
          </div>
          <div className="baseline-score-row">
            <span className="baseline-task-name">Passed</span>
            <span
              className="baseline-grade"
              style={{ color: baselineResult.grade?.passed ? 'var(--accent-green)' : 'var(--accent-red)', fontSize: 14 }}
            >
              {baselineResult.grade?.passed ? '✓ YES' : '✗ NO'}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
