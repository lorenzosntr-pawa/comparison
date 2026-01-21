import { useEffect, useRef, useState, useCallback } from 'react'
import { Link } from 'react-router'
import { useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Progress } from '@/components/ui/progress'
import { useSchedulerHistory } from '../hooks'
import { cn } from '@/lib/utils'
import { formatDistanceToNow } from 'date-fns'
import { ArrowRight, Loader2, Play, CheckCircle2, XCircle } from 'lucide-react'

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

  const [isStreaming, setIsStreaming] = useState(false)
  const [progress, setProgress] = useState<ScrapeProgressEvent | null>(null)
  const [scrapeError, setScrapeError] = useState<string | null>(null)
  const [completedPlatforms, setCompletedPlatforms] = useState(0)

  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    setIsStreaming(false)
  }, [])

  const startScrape = useCallback(() => {
    cleanup()
    setScrapeError(null)
    setProgress(null)
    setCompletedPlatforms(0)
    setIsStreaming(true)

    const eventSource = new EventSource('/api/scrape/stream')
    eventSourceRef.current = eventSource

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as ScrapeProgressEvent
        setProgress(data)

        // Track completed platforms
        if (data.phase === 'storing_complete' ||
            (data.phase === 'completed' && data.platform)) {
          setCompletedPlatforms((prev) => Math.min(prev + 1, 3))
        }

        if (data.phase === 'completed' || data.phase === 'failed') {
          eventSource.close()
          setIsStreaming(false)
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
      setIsStreaming(false)
      setScrapeError('Connection lost')
    }
  }, [cleanup, queryClient, refetch])

  // Cleanup on unmount
  useEffect(() => {
    return cleanup
  }, [cleanup])

  // Calculate progress percentage (based on platforms: 0-33-66-100)
  const progressPercent =
    progress?.phase === 'completed' ? 100 :
    progress?.phase === 'failed' ? 0 :
    Math.round((completedPlatforms / 3) * 100 + (isStreaming && completedPlatforms < 3 ? 15 : 0))

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
        {(isStreaming || progress?.phase === 'completed' || progress?.phase === 'failed') && (
          <div className="mb-4 pb-4 border-b">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  {isStreaming && (
                    <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
                  )}
                  {progress?.phase === 'completed' && (
                    <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
                  )}
                  {progress?.phase === 'failed' && (
                    <XCircle className="h-3.5 w-3.5 text-destructive" />
                  )}
                  <span className={cn(
                    'font-medium',
                    progress?.phase === 'completed' && 'text-green-500',
                    progress?.phase === 'failed' && 'text-destructive'
                  )}>
                    {progress?.phase === 'completed' ? 'Scrape Complete' :
                     progress?.phase === 'failed' ? 'Scrape Failed' :
                     progress?.phase === 'scraping' && progress.platform ?
                       `Scraping ${capitalizeFirst(progress.platform)}...` :
                     progress?.phase === 'storing' && progress.platform ?
                       `Storing ${capitalizeFirst(progress.platform)}...` :
                     'Starting scrape...'}
                  </span>
                </div>
                <span className="text-muted-foreground">
                  {progress?.events_count ?? 0} events
                </span>
              </div>
              <Progress
                value={progressPercent}
                className={cn(
                  'h-1.5',
                  progress?.phase === 'completed' && '[&>div]:bg-green-500',
                  progress?.phase === 'failed' && '[&>div]:bg-destructive'
                )}
              />
            </div>
            {scrapeError && (
              <p className="mt-2 text-xs text-destructive">{scrapeError}</p>
            )}
          </div>
        )}

        {/* Trigger Scrape Button (when not streaming) */}
        {!isStreaming && progress?.phase !== 'completed' && progress?.phase !== 'failed' && (
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
        {!isStreaming && (progress?.phase === 'completed' || progress?.phase === 'failed') && (
          <div className="mb-4">
            <Button
              variant="ghost"
              size="sm"
              className="w-full text-xs"
              onClick={() => {
                setProgress(null)
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
              return (
                <div
                  key={run.id}
                  className="flex items-center justify-between py-2 border-b last:border-0"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={statusVariants[run.status]}
                        className={cn(
                          run.status === 'completed' &&
                            'bg-green-500 hover:bg-green-600'
                        )}
                      >
                        {run.status}
                      </Badge>
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
