'use client'

import type { EmailItem } from '@/app/page'

interface Props {
  email: EmailItem
  isActive: boolean
  isResolved: boolean
  onClick?: () => void
}

const CAT_LABELS: Record<string, string> = {
  complaint: '⚠️ Complaint',
  refund: '💳 Refund',
  inquiry: '❓ Inquiry',
  spam: '🚫 Spam',
  urgent: '🚨 Urgent',
  abuse: '⛔ Abuse',
}

const SENTIMENT_ICONS: Record<string, string> = {
  positive: '😊',
  neutral: '😐',
  negative: '😤',
}

function getUrgencyClass(score: number): string {
  if (score >= 0.7) return 'urgency-high'
  if (score >= 0.4) return 'urgency-med'
  return 'urgency-low'
}

function getUrgencyColor(score: number): string {
  if (score >= 0.7) return '#ef4444'
  if (score >= 0.4) return '#eab308'
  return '#22c55e'
}

function formatTime(ts: string): string {
  if (!ts) return ''
  try {
    return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch {
    return ts
  }
}

function getInitials(name: string): string {
  return name
    .split(' ')
    .map(w => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

export default function EmailCard({ email, isActive, isResolved, onClick }: Props) {
  if (isResolved && !email.subject && !email.body) {
    return (
      <div className="email-card resolved" style={{ padding: '12px 20px', display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ color: 'var(--accent-green)', fontSize: 14 }}>✓</span>
        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{email.id} — resolved</span>
      </div>
    )
  }

  return (
    <div 
      className={`email-card ${isActive ? 'active-email' : ''} ${isResolved ? 'resolved' : ''}`}
      onClick={onClick}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      {/* Urgency bar on top */}
      <div className="urgency-bar">
        <div
          className="urgency-fill"
          style={{
            width: `${email.urgency_score * 100}%`,
            background: getUrgencyColor(email.urgency_score),
          }}
        />
      </div>

      <div className="email-card-header">
        <div className="email-card-meta">
          <div className="email-subject">{email.subject}</div>
          <div className="email-sender-row">
            <div className="email-avatar" style={{ fontSize: 11 }}>
              {getInitials(email.sender_name || email.sender)}
            </div>
            <div>
              <div className="email-sender">{email.sender_name || email.sender}</div>
              <div className="email-time">{formatTime(email.timestamp)}</div>
            </div>
          </div>
        </div>

        <div className="email-badges">
          {isResolved ? (
            <span className="resolved-badge">✓ Resolved</span>
          ) : email.urgency_score > 0 ? (
            <span className={`urgency-badge ${getUrgencyClass(email.urgency_score)}`}>
              {(email.urgency_score * 10).toFixed(0)}/10
            </span>
          ) : null}
          <span className={`cat-badge cat-${email.category}`}>
            {CAT_LABELS[email.category] ?? email.category}
          </span>
          <span style={{ fontSize: 12 }}>
            {SENTIMENT_ICONS[email.sentiment] ?? ''}
          </span>
        </div>
      </div>

      {email.body && (
        <div className="email-body">
          {email.body.length > 400 ? email.body.slice(0, 400) + '…' : email.body}
        </div>
      )}

      {isActive && !isResolved && (
        <div style={{
          padding: '6px 20px 10px',
          display: 'flex', alignItems: 'center', gap: 6,
          fontSize: 11, color: 'var(--accent-blue)',
          borderTop: '1px solid rgba(59,130,246,0.15)',
          background: 'rgba(59,130,246,0.04)',
        }}>
          <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent-blue)', animation: 'pulse-dot 1.5s infinite' }} />
          Current email — take an action below
        </div>
      )}
    </div>
  )
}
