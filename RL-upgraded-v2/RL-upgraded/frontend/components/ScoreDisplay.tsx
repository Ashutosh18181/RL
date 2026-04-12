'use client'

import type { GradeData, RewardBreakdown } from '@/app/page'

interface Props {
  episodeReward: number
  grade: GradeData | null
  done: boolean
  totalSteps: number
  maxSteps: number
  lastBreakdown: RewardBreakdown | null
}

const CIRCUMFERENCE = 2 * Math.PI * 54  // r=54

function gradeColor(score: number): string {
  if (score >= 0.8) return '#22c55e'
  if (score >= 0.6) return '#eab308'
  if (score >= 0.4) return '#f97316'
  return '#ef4444'
}

function rewardColor(v: number): string {
  return v >= 0 ? 'var(--accent-green)' : 'var(--accent-red)'
}

function formatKey(key: string): string {
  return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

export default function ScoreDisplay({
  episodeReward, grade, done, totalSteps, maxSteps, lastBreakdown,
}: Props) {
  const score = grade?.score ?? 0
  const offset = CIRCUMFERENCE - (score * CIRCUMFERENCE)
  const color = gradeColor(score)
  const stepPct = maxSteps > 0 ? Math.min(totalSteps / maxSteps, 1) : 0

  return (
    <div className="score-panel">
      {/* Score ring */}
      <div className="score-ring-wrap">
        <div className="score-ring">
          <svg width="140" height="140" viewBox="0 0 140 140">
            <circle className="score-ring-bg" cx="70" cy="70" r="54" />
            <circle
              className="score-ring-fill"
              cx="70" cy="70" r="54"
              stroke={done ? color : '#3b82f6'}
              strokeDasharray={CIRCUMFERENCE}
              strokeDashoffset={done ? offset : CIRCUMFERENCE * 0.85}
            />
          </svg>
          <div className="score-center">
            <div className="score-value" style={{ color: done ? color : 'var(--text-secondary)' }}>
              {done ? (score * 100).toFixed(1) : (episodeReward >= 0 ? '+' : '') + episodeReward.toFixed(2)}
            </div>
            <div className="score-label">{done ? 'score' : 'reward'}</div>
          </div>
        </div>

        {done && grade && (
          <div className="score-grade" style={{ color }}>
            {grade.grade_letter}
          </div>
        )}
      </div>

      {/* Stats grid */}
      <div className="score-stats">
        <div className="score-stat-card">
          <div className="score-stat-value" style={{ color: 'var(--accent-blue)' }}>
            {totalSteps}
          </div>
          <div className="score-stat-label">Steps Taken</div>
        </div>
        <div className="score-stat-card">
          <div
            className="score-stat-value"
            style={{ color: episodeReward >= 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}
          >
            {episodeReward >= 0 ? '+' : ''}{episodeReward.toFixed(3)}
          </div>
          <div className="score-stat-label">Cum. Reward</div>
        </div>
        <div className="score-stat-card">
          <div
            className="score-stat-value"
            style={{ color: done && grade?.passed ? 'var(--accent-green)' : done ? 'var(--accent-red)' : 'var(--text-secondary)' }}
          >
            {done ? (grade?.passed ? '✓' : '✗') : '—'}
          </div>
          <div className="score-stat-label">Passed</div>
        </div>
        <div className="score-stat-card">
          <div className="score-stat-value" style={{ color: 'var(--accent-cyan)' }}>
            {maxSteps - totalSteps}
          </div>
          <div className="score-stat-label">Steps Left</div>
        </div>
      </div>

      {/* Progress bar */}
      <div style={{ marginTop: 14, padding: '0 2px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-muted)', marginBottom: 5 }}>
          <span>Step progress</span>
          <span>{totalSteps}/{maxSteps}</span>
        </div>
        <div style={{ height: 4, background: 'rgba(255,255,255,0.05)', borderRadius: 2, overflow: 'hidden' }}>
          <div
            style={{
              height: '100%', borderRadius: 2,
              width: `${stepPct * 100}%`,
              background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)',
              transition: 'width 0.5s ease',
            }}
          />
        </div>
      </div>

      {/* Last reward breakdown */}
      {lastBreakdown && Object.keys(lastBreakdown).length > 0 && (
        <div className="reward-bar-wrap">
          <div className="reward-bar-label">Last Action Breakdown</div>
          {Object.entries(lastBreakdown).map(([key, val]) => {
            const isPos = val >= 0
            const maxAbsVal = 0.3
            const pct = Math.min(Math.abs(val) / maxAbsVal * 100, 100)
            return (
              <div key={key} className="reward-bar-item">
                <div className="reward-bar-row">
                  <span className="reward-bar-key">{formatKey(key)}</span>
                  <span className={`reward-bar-val ${isPos ? 'pos' : 'neg'}`}>
                    {isPos ? '+' : ''}{val.toFixed(3)}
                  </span>
                </div>
                <div className="reward-bar-track">
                  <div
                    className={`reward-bar-fill ${isPos ? 'pos' : 'neg'}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
