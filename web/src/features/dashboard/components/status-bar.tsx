import { Badge } from '@/components/ui/badge'
import { useHealth, useSchedulerStatus } from '../hooks'
import { cn } from '@/lib/utils'
import { Database, Clock, Loader2 } from 'lucide-react'

// Platform abbreviations
const PLATFORM_ABBREV: Record<string, string> = {
  betpawa: 'BP',
  sportybet: 'SB',
  bet9ja: 'B9',
}

// Platform colors
const PLATFORM_COLORS: Record<string, string> = {
  betpawa: 'bg-green-500',
  sportybet: 'bg-blue-500',
  bet9ja: 'bg-orange-500',
}

export function StatusBar() {
  const { data: health, isPending: healthLoading } = useHealth()
  const { data: scheduler, isPending: schedulerLoading } = useSchedulerStatus()

  const isLoading = healthLoading || schedulerLoading

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-2 px-4 bg-muted/50 rounded-lg">
        <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
      </div>
    )
  }

  const schedulerStatus = scheduler?.paused ? 'paused' : scheduler?.running ? 'running' : 'stopped'

  return (
    <div className="flex items-center gap-4 py-2 px-4 bg-muted/50 rounded-lg text-sm">
      {/* Database status */}
      <div className="flex items-center gap-1.5">
        <Database className="h-3.5 w-3.5 text-muted-foreground" />
        <span
          className={cn(
            'h-2 w-2 rounded-full',
            health?.database === 'connected' ? 'bg-green-500' : 'bg-red-500'
          )}
        />
        <span className="text-muted-foreground">DB</span>
      </div>

      {/* Scheduler status */}
      <div className="flex items-center gap-1.5">
        <Clock className="h-3.5 w-3.5 text-muted-foreground" />
        <span
          className={cn(
            'h-2 w-2 rounded-full',
            schedulerStatus === 'running' ? 'bg-green-500' :
            schedulerStatus === 'paused' ? 'bg-yellow-500' : 'bg-gray-500'
          )}
        />
        <span className="text-muted-foreground">Scheduler</span>
      </div>

      {/* Separator */}
      <div className="h-4 w-px bg-border" />

      {/* Platform statuses */}
      {health?.platforms.map((platform) => (
        <div key={platform.platform} className="flex items-center gap-1.5">
          <span
            className={cn(
              'h-2 w-2 rounded-full',
              platform.status === 'healthy'
                ? PLATFORM_COLORS[platform.platform] || 'bg-green-500'
                : 'bg-red-500'
            )}
          />
          <span className="text-muted-foreground">
            {PLATFORM_ABBREV[platform.platform] || platform.platform.slice(0, 2).toUpperCase()}
          </span>
        </div>
      ))}
    </div>
  )
}
