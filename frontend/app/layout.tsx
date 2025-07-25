import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AI Therapist - Voice Chat',
  description: 'Compassionate AI therapy through voice interaction',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}