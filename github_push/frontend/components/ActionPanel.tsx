'use client'

import { useState, useCallback } from 'react'
import type { EmailItem } from '@/app/page'

interface Props {
  currentEmail: EmailItem | null
  done: boolean
  loading: boolean
  baselineRunning: boolean
  onStep: (action: object) => void
  onReset: () => void
  onBaseline: () => void
}

const CATEGORIES = ['complaint', 'refund', 'inquiry', 'spam', 'urgent', 'abuse']

const ACTION_TEMPLATES: Record<string, string> = {
  complaint: 'Dear {name},\n\nThank you for contacting us. We sincerely apologize for your experience and are escalating this to our resolution team immediately. We will follow up within 24 hours.\n\nBest regards,\nCustomer Support Team',
  refund: 'Dear {name},\n\nThank you for reaching out. We have processed your refund request and you should see it reflected within 3–5 business days. We apologize for any inconvenience.\n\nBest regards,\nCustomer Support Team',
  inquiry: 'Dear {name},\n\nThank you for your inquiry! We are happy to help. Please allow us 1 business day to provide a detailed response to your question.\n\nBest regards,\nCustomer Support Team',
  urgent: 'Dear {name},\n\nWe have received your urgent request and are treating it with the highest priority. A senior specialist will contact you within 15 minutes.\n\nBest regards,\nSenior Support Manager',
  abuse: 'Dear Valued Customer,\n\nWe understand you are frustrated. We would like to help resolve the underlying issue. Please contact us so we can assist in a constructive manner.\n\nBest regards,\nCustomer Relations Team',
}

export default function ActionPanel({
  currentEmail, done, loading, baselineRunning, onStep, onReset, onBaseline,
}: Props) {
  const [actionType, setActionType] = useState<string>('')
  const [classification, setClassification] = useState<string>('inquiry')
  const [content, setContent] = useState<string>('')

  const fillTemplate = useCallback((cat: string) => {
    const template = ACTION_TEMPLATES[cat] ?? ACTION_TEMPLATES.inquiry
    setContent(template.replace('{name}', currentEmail?.sender_name ?? 'Valued Customer'))
  }, [currentEmail])

  const handleActionSelect = (type: string) => {
    setActionType(t => t === type ? '' : type)
    if (type === 'reply' && currentEmail) {
      fillTemplate(currentEmail.category)
    } else if (type !== 'reply') {
      setContent('')
    }
  }

  const handleSubmit = () => {
    if (!currentEmail || !actionType) return
    const action: any = {
      type: actionType,
      email_id: currentEmail.id,
    }
    if (actionType === 'classify') action.classification = classification
    if (actionType === 'reply' || actionType === 'tag' || actionType === 'escalate') {
      action.content = content || undefined
    }
    onStep(action)
    // Reset selection after submit
    setActionType('')
    setContent('')
  }

  const wordCount = content.trim().split(/\s+/).filter(Boolean).length
  const canSubmit = !done && !loading && !!currentEmail && !!actionType

  return (
    <div className="action-panel">
      <div className="action-panel-inner">
        {/* Control row */}
        <div className="control-row">
          <button className="reset-btn" onClick={onReset} disabled={loading}>
            {loading ? <div className="spinner" /> : '↺'} Reset
          </button>
          <button
            className="baseline-btn"
            onClick={onBaseline}
            disabled={baselineRunning || loading}
          >
            {baselineRunning ? <><div className="spinner" /> Running…</> : '🤖 Run Mock Agent'}
          </button>
        </div>

        {!done && currentEmail && (
          <>
            <div className="action-panel-title">
              Action on: <span style={{ color: 'var(--text-primary)' }}>{currentEmail.id}</span>
            </div>

            {/* Action buttons */}
            <div className="action-buttons">
              {[
                { type: 'classify', label: '🏷 Classify', cls: 'btn-classify' },
                { type: 'reply', label: '✉️ Reply', cls: 'btn-reply' },
                { type: 'escalate', label: '🚨 Escalate', cls: 'btn-escalate' },
                { type: 'archive', label: '🗄 Archive', cls: 'btn-archive' },
                { type: 'tag', label: '🔖 Tag', cls: 'btn-tag' },
              ].map(({ type, label, cls }) => (
                <button
                  key={type}
                  className={`action-btn ${cls} ${actionType === type ? 'selected' : ''}`}
                  onClick={() => handleActionSelect(type)}
                  disabled={done || loading}
                >
                  {label}
                </button>
              ))}
            </div>

            {/* Classify input */}
            {actionType === 'classify' && (
              <select
                className="classify-select"
                value={classification}
                onChange={e => setClassification(e.target.value)}
              >
                {CATEGORIES.map(c => (
                  <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
                ))}
              </select>
            )}

            {/* Text input for reply/escalate/tag */}
            {(actionType === 'reply' || actionType === 'escalate' || actionType === 'tag') && (
              <>
                <textarea
                  className="reply-textarea"
                  placeholder={
                    actionType === 'reply' ? 'Write your professional reply here…' :
                    actionType === 'escalate' ? 'Escalation notes (optional)…' :
                    'Tag label or notes…'
                  }
                  value={content}
                  onChange={e => setContent(e.target.value)}
                  rows={actionType === 'reply' ? 5 : 3}
                />
                {actionType === 'reply' && (
                  <div className={`word-count ${wordCount >= 20 ? 'ok' : ''}`}>
                    {wordCount}/20 words {wordCount >= 20 ? '✓' : '(need 20+ for full completeness score)'}
                  </div>
                )}
              </>
            )}

            {/* Submit */}
            {actionType && (
              <button className="submit-btn" onClick={handleSubmit} disabled={!canSubmit}>
                {loading ? <><div className="spinner" /> Processing…</> : `Submit ${actionType.toUpperCase()} action →`}
              </button>
            )}
          </>
        )}

        {done && (
          <div style={{ textAlign: 'center', padding: '12px 0', color: 'var(--text-secondary)', fontSize: 13 }}>
            Episode complete. Click <strong>Reset</strong> to start a new one.
          </div>
        )}

        {!currentEmail && !done && (
          <div style={{ textAlign: 'center', padding: '12px 0', color: 'var(--text-muted)', fontSize: 13 }}>
            Reset an episode to begin working on emails.
          </div>
        )}
      </div>
    </div>
  )
}
