import { useEffect, useRef, useState, useCallback } from 'react'
import { Link } from 'react-router'
import { useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Progress } from '@/components/ui/progress'
import { useSchedulerHistory, useActiveScrapesObserver } from '../hooks'
import { cn } from '@/lib/utils'
import { formatDistanceToNow } from 'date-fns'
import { ArrowRight, Loader2, Play, CheckCircle2, XCircle, Radio } from 'lucide-react'

interface ScrapeProgressEvent {
  platform: string | null
  phase: string
  current: number
  total: number
  events_count: number | null
  message: string | null
  timestamp: string
}

function formatDuration(
  startedAt: string,
  completedAt: string | null
): string | null {
  if (!completedAt) return null
  const start = new Date(startedAt).getTime()
  const end = new Date(completedAt).getTime()
  const seconds = Math.round((end - start) / 1000)
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes}m ${secs}s`
}

const statusVariants: Record<
  string,
  'default' | 'destructive' | 'secondary' | 'outline'
> = {
  completed: 'default',
  partial: 'secondary',
  failed: 'destructive',
  running: 'outline',
  pending: 'outline',
}

export function RecentRuns() {
  const queryClient = useQueryClient()
  const { data, isPending, error, refetch } = useSchedulerHistory(5)
  const eventSourceRef = useRef<EventSource | null>(null)

  // State for manual scrapes triggered from this component
  const [isManualStreaming, setIsManualStreaming] = useState(false)
  const [manualProgress, setManualProgress] = useState<ScrapeProgressEvent | null>(null)
  const [scrapeError, setScrapeError] = useState<string | null>(null)
  const [completedPlatforms, setCompletedPlatforms] = useState(0)

  // Observer for scheduled scrapes running in the background
  const {
    activeScrapeId,
    isObserving: isObservingScheduled,
    progress: scheduledProgress,
    stopChecking,
  } = useActiveScrapesObserver()

  // Use either manual progress or observed scheduled progress
  const activeProgress = isManualStreaming ? manualProgress : scheduledProgress
  const isStreaming = isManualStreaming || isObservingScheduled
  const isScheduledScrape = !isManualStreaming && isObservingScheduled

  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    setIsManualStreaming(false)
  }, [])

  const startScrape = useCallback(() => {
    // Stop checking for scheduled scrapes when starting manual
    stopChecking()
    cleanup()
    setScrapeError(null)
    setManualProgress(null)
    setCompletedPlatforms(0)
    setIsManualStreaming(true)

    const eventSource = new EventSource('/api/scrape/stream')
    eventSourceRef.current = eventSource

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as ScrapeProgressEvent
        setManualProgress(data)

        // Track completed platforms
        if (data.phase === 'storing_complete' ||
            (data.phase === 'completed' && data.platform)) {
          setCompletedPlatforms((prev) => Math.min(prev + 1, 3))
        }

        if (data.phase === 'completed' || data.phase === 'failed') {
          eventSource.close()
          setIsManualStreaming(false)
          // Invalidate and refetch queries
          queryClient.invalidateQueries({ queryKey: ['scheduler-history'] })
          queryClient.invalidateQueries({ queryKey: ['events'] })
          refetch()
        }
      } catch (e) {
        console.error('Failed to parse SSE event:', e)
      }
    }

    eventSource.onerror = () => {
      eventSource.close()
      setIsManualStreaming(false)
      setScrapeError('Connection lost')
    }
  }, [cleanup, queryClient, refetch, stopChecking])

  // Cleanup on unmount
  useEffect(() => {
    return cleanup
  }, [cleanup])

  // Calculate progress percentage for manual scrapes
  const manualProgressPercent =
    manualProgress?.phase === 'completed' ? 100 :
    manualProgress?.phase === 'failed' ? 0 :
    Math.round((completedPlatforms / 3) * 100 + (isManualStreaming && completedPlatforms < 3 ? 15 : 0))

  // Calculate progress percentage for observed scheduled scrapes
  const scheduledProgressPercent = scheduledProgress
    ? scheduledProgress.phase === 'completed'
      ? 100
      : scheduledProgress.phase === 'failed'
      ? 0
      : Math.round((scheduledProgress.current / scheduledProgress.total) * 100)
    : 0

  const progressPercent = isManualStreaming ? manualProgressPercent : scheduledProgressPercent

  if (isPending) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">
            Recent Scrape Runs
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">
            Recent Scrape Runs
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">Failed to load run history</p>
        </CardContent>
      </Card>
    )
  }

  const showProgressSection = isStreaming ||
    activeProgress?.phase === 'completed' ||
    activeProgress?.phase === 'failed'

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">Recent Scrape Runs</CardTitle>
        <Button variant="ghost" size="sm" asChild>
          <Link to="/scrape-runs">
            View All <ArrowRight className="ml-1 h-4 w-4" />
          </Link>
        </Button>
      </CardHeader>
      <CardContent>
        {/* Live Progress Section */}
        {showProgressSection && (
          <div className="mb-4 pb-4 border-b">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  {isStreaming && (
                    <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
                  )}
                  {activeProgress?.phase === 'completed' && (
                    <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
                  )}
                  {activeProgress?.phase === 'failed' && (
                    <XCircle className="h-3.5 w-3.5 text-destructive" />
                  )}
                  <span className={cn(
                    'font-medium',
                    activeProgress?.phase === 'completed' && 'text-green-500',
                    activeProgress?.phase === 'failed' && 'text-destructive'
                  )}>
                    {activeProgress?.phase === 'completed' ? 'Scrape Complete' :
                     activeProgress?.phase === 'failed' ? 'Scrape Failed' :
                     activeProgress?.phase === 'scraping' && activeProgress.platform ?
                       `Scraping ${capitalizeFirst(activeProgress.platform)}...` :
                     activeProgress?.phase === 'storing' && activeProgress.platform ?
                       `Storing ${capitalizeFirst(activeProgress.platform)}...` :
                     'Starting scrape...'}
                  </span>
                  {/* Show indicator for scheduled vs manual */}
                  {isScheduledScrape && (
                    <Badge variant="outline" className="ml-1 text-xs py-0 h-5">
                      <Radio className="h-2.5 w-2.5 mr-1 text-blue-500" />
                      Scheduled
                    </Badge>
                  )}
                </div>
                <span className="text-muted-foreground">
                  {activeProgress?.events_count ?? 0} events
                </span>
              </div>
              <Progress
                value={progressPercent}
                className={cn(
                  'h-1.5',
                  activeProgress?.phase === 'completed' && '[&>div]:bg-green-500',
                  activeProgress?.phase === 'failed' && '[&>div]:bg-destructive'
                )}
              />
            </div>
            {scrapeError && (
              <p className="mt-2 text-xs text-destructive">{scrapeError}</p>
            )}
          </div>
        )}

        {/* Trigger Scrape Button (when not streaming) */}
        {!isStreaming && activeProgress?.phase !== 'completed' && activeProgress?.phase !== 'failed' && (
          <div className="mb-4 pb-4 border-b">
            <Button
              variant="outline"
              size="sm"
              className="w-full"
              onClick={startScrape}
            >
              <Play className="mr-1.5 h-3.5 w-3.5" />
              Start New Scrape
            </Button>
          </div>
        )}

        {/* Reset button after completion */}
        {!isStreaming && (activeProgress?.phase === 'completed' || activeProgress?.phase === 'failed') && (
          <div className="mb-4">
            <Button
              variant="ghost"
              size="sm"
              className="w-full text-xs"
              onClick={() => {
                setManualProgress(null)
                setCompletedPlatforms(0)
              }}
            >
              Dismiss
            </Button>
          </div>
        )}

        {data?.runs.length === 0 ? (
          <p className="text-sm text-muted-foreground">No scrape runs yet</p>
        ) : (
          <div className="space-y-3">
            {data?.runs.map((run) => {
              const duration = formatDuration(run.started_at, run.completed_at)
              const isCurrentlyRunning = run.status === 'running' && activeScrapeId === run.id
              return (
                <div
                  key={run.id}
                  className={cn(
                    "flex items-center justify-between py-2 border-b last:border-0",
                    isCurrentlyRunning && "bg-primary/5 -mx-2 px-2 rounded"
                  )}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={statusVariants[run.status]}
                        className={cn(
                          run.status === 'completed' &&
                            'bg-green-500 hover:bg-green-600',
                          run.status === 'running' &&
                            'animate-pulse'
                        )}
                      >
                        {run.status}
                      </Badge>
                      {run.trigger === 'scheduled' && (
                        <Radio className="h-3 w-3 text-blue-500" />
                      )}
                      {duration && (
                        <span className="text-xs text-muted-foreground">
                          {duration}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {formatDistanceToNow(new Date(run.started_at), {
                        addSuffix: true,
                      })}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">
                      {run.events_scraped} events
                    </p>
                    {run.events_failed > 0 && (
                      <p className="text-xs text-destructive">
                        {run.events_failed} failed
                      </p>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function capitalizeFirst(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1)
}
