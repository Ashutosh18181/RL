import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Email Triage RL Environment',
  description:
    'OpenEnv-compatible RL environment for email triage and customer support automation. Watch an AI agent classify, reply, escalate, and archive emails in real-time.',
  keywords: ['RL environment', 'email triage', 'AI agent', 'OpenEnv', 'reinforcement learning'],
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  )
}
