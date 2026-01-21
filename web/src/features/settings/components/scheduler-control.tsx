import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Pause, Play } from 'lucide-react'
import { useSchedulerStatus } from '@/features/dashboard/hooks/use-scheduler'
import { usePauseScheduler, useResumeScheduler } from '../hooks'

export function SchedulerControl() {
  const { data: status, isLoading } = useSchedulerStatus()
  const { mutate: pause, isPending: isPausing } = usePauseScheduler()
  const { mutate: resume, isPending: isResuming } = useResumeScheduler()

  const isRunning = status?.running ?? false
  const isPaused = status?.paused ?? false
  const scrapeJob = status?.jobs?.find((j) => j.id === 'scrape_odds')
  const nextRun = scrapeJob?.next_run

  const formatNextRun = (dateStr: string | null | undefined) => {
    if (!dateStr) return 'Not scheduled'
    const date = new Date(dateStr)
    return date.toLocaleString()
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-between">
        <div className="space-y-0.5">
          <div className="text-sm font-medium">Status</div>
          <div className="text-sm text-muted-foreground">Loading...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="space-y-0.5">
          <div className="text-sm font-medium">Scheduler Status</div>
          <div className="text-sm text-muted-foreground">
            Control the automatic scraping scheduler
          </div>
        </div>
        <Badge variant={isPaused ? 'secondary' : isRunning ? 'default' : 'destructive'}>
          {isPaused ? 'Paused' : isRunning ? 'Running' : 'Stopped'}
        </Badge>
      </div>

      {!isPaused && nextRun && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-muted-foreground">Next scrape:</div>
          <div className="text-sm">{formatNextRun(nextRun)}</div>
        </div>
      )}

      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => pause()}
          disabled={isPaused || isPausing || isResuming}
        >
          <Pause className="mr-2 h-4 w-4" />
          {isPausing ? 'Pausing...' : 'Pause'}
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => resume()}
          disabled={!isPaused || isPausing || isResuming}
        >
          <Play className="mr-2 h-4 w-4" />
          {isResuming ? 'Resuming...' : 'Resume'}
        </Button>
      </div>
    </div>
  )
}
