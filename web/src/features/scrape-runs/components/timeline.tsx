import { cn } from '@/lib/utils'
import { formatDistanceToNow, format } from 'date-fns'
import { Loader2, CheckCircle2, XCircle, Circle } from 'lucide-react'
import type { ScrapePhaseLog } from '../hooks/use-phase-history'

// Platform colors for visual consistency
const PLATFORM_COLORS: Record<string, string> = {
  betpawa: 'text-green-500',
  sportybet: 'text-blue-500',
  bet9ja: 'text-orange-500',
}

// Phase display names for better readability
const PHASE_LABELS: Record<string, string> = {
  initializing: 'Initializing',
  discovering: 'Discovering',
  scraping: 'Scraping',
  mapping: 'Mapping',
  storing: 'Storing',
  completed: 'Completed',
  failed: 'Failed',
}

interface TimelineProps {
  phases: ScrapePhaseLog[]
  className?: string
}

function formatDuration(startedAt: string, endedAt: string | null): string | null {
  if (!endedAt) return null
  const start = new Date(startedAt).getTime()
  const end = new Date(endedAt).getTime()
  const ms = end - start
  if (ms < 1000) return `${ms}ms`
  const seconds = Math.round(ms / 1000)
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes}m ${secs}s`
}

function formatTimestamp(timestamp: string): { time: string; relative: string } {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))

  return {
    time: format(date, 'HH:mm:ss'),
    relative: diffMinutes < 60
      ? formatDistanceToNow(date, { addSuffix: true })
      : format(date, 'MMM d, HH:mm'),
  }
}

export function Timeline({ phases, className }: TimelineProps) {
  if (!phases.length) {
    return (
      <div className={cn('text-sm text-muted-foreground', className)}>
        No phase history available
      </div>
    )
  }

  return (
    <div className={cn('space-y-0', className)}>
      {phases.map((phase, index) => {
        const isLast = index === phases.length - 1
        const isFailed = phase.phase === 'failed'
        const isActive = !phase.ended_at
        const isCompleted = phase.phase === 'completed' || (phase.ended_at && !isFailed)
        const { time } = formatTimestamp(phase.started_at)
        const duration = formatDuration(phase.started_at, phase.ended_at)
        const phaseLabel = PHASE_LABELS[phase.phase] || phase.phase

        return (
          <div key={phase.id} className="flex">
            {/* Timeline connector */}
            <div className="flex flex-col items-center mr-3">
              {/* Node */}
              <div className={cn(
                'flex items-center justify-center w-6 h-6 rounded-full border-2',
                isFailed && 'border-red-500 bg-red-50 dark:bg-red-950',
                isActive && 'border-primary bg-primary/10',
                isCompleted && !isFailed && 'border-green-500 bg-green-50 dark:bg-green-950',
                !isActive && !isFailed && !isCompleted && 'border-muted-foreground/30 bg-muted',
              )}>
                {isFailed && <XCircle className="w-3.5 h-3.5 text-red-500" />}
                {isActive && <Loader2 className="w-3.5 h-3.5 text-primary animate-spin" />}
                {isCompleted && !isFailed && <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />}
                {!isActive && !isFailed && !isCompleted && <Circle className="w-2.5 h-2.5 text-muted-foreground/50" />}
              </div>
              {/* Vertical line */}
              {!isLast && (
                <div className={cn(
                  'w-0.5 flex-1 min-h-[24px]',
                  isFailed ? 'bg-red-200 dark:bg-red-900' : 'bg-border',
                )} />
              )}
            </div>

            {/* Content */}
            <div className={cn(
              'flex-1 pb-4',
              isLast && 'pb-0',
            )}>
              <div className="flex items-center gap-2 text-sm">
                <span className="text-muted-foreground font-mono text-xs">
                  {time}
                </span>
                {phase.platform && (
                  <span className={cn(
                    'font-medium capitalize',
                    PLATFORM_COLORS[phase.platform] || 'text-foreground',
                  )}>
                    {phase.platform}
                  </span>
                )}
                <span className={cn(
                  'font-medium',
                  isFailed && 'text-red-500',
                  isActive && 'text-primary',
                )}>
                  {phaseLabel}
                </span>
                {duration && (
                  <span className="text-muted-foreground text-xs">
                    ({duration})
                  </span>
                )}
              </div>

              {/* Message / events count */}
              {(phase.message || phase.events_processed) && (
                <div className="mt-0.5 text-xs text-muted-foreground pl-0.5">
                  {phase.message && <span>{phase.message}</span>}
                  {phase.events_processed !== null && phase.events_processed > 0 && (
                    <span className="ml-1">
                      · {phase.events_processed} events
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
