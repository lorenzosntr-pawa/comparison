import { useEffect, useRef } from 'react'
import { cn } from '@/lib/utils'
import { format } from 'date-fns'

export interface LogMessage {
  time: string
  platform: string | null
  phase: string
  message: string | null
  level: 'info' | 'warning' | 'error'
}

// Platform colors for log entries
const PLATFORM_COLORS: Record<string, string> = {
  betpawa: 'text-green-400',
  sportybet: 'text-blue-400',
  bet9ja: 'text-orange-400',
}

interface LiveLogProps {
  messages: LogMessage[]
  className?: string
  maxHeight?: string
}

export function LiveLog({ messages, className, maxHeight = 'h-48' }: LiveLogProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [messages])

  if (messages.length === 0) {
    return (
      <div
        className={cn(
          maxHeight,
          'overflow-y-auto bg-zinc-900 text-zinc-400 font-mono text-xs p-3 rounded-md flex items-center justify-center',
          className,
        )}
      >
        Waiting for log messages...
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className={cn(
        maxHeight,
        'overflow-y-auto bg-zinc-900 text-zinc-100 font-mono text-xs p-3 rounded-md',
        className,
      )}
    >
      {messages.map((msg, i) => (
        <div
          key={i}
          className={cn(
            'py-0.5 leading-relaxed',
            msg.level === 'error' && 'text-red-400',
            msg.level === 'warning' && 'text-yellow-400',
          )}
        >
          <span className="text-zinc-500">[{msg.time}]</span>
          {msg.platform && (
            <span className={cn('ml-1', PLATFORM_COLORS[msg.platform] || 'text-zinc-300')}>
              [{msg.platform}]
            </span>
          )}
          <span className="ml-1 text-zinc-400">{msg.phase}:</span>
          <span className="ml-1">{msg.message || '...'}</span>
        </div>
      ))}
    </div>
  )
}

// Helper to convert SSE progress event to log message
export function progressToLogMessage(event: {
  platform: string | null
  phase: string
  message: string | null
  timestamp?: string
}): LogMessage {
  const time = event.timestamp
    ? format(new Date(event.timestamp), 'HH:mm:ss')
    : format(new Date(), 'HH:mm:ss')

  const isFailed = event.phase === 'failed'
  const isWarning = event.phase.includes('timeout') || event.phase.includes('retry')

  return {
    time,
    platform: event.platform,
    phase: event.phase,
    message: event.message,
    level: isFailed ? 'error' : isWarning ? 'warning' : 'info',
  }
}
