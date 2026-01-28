import { useEffect, useRef, useState, useCallback } from 'react'
import { Link } from 'react-router'
import { useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Progress } from '@/components/ui/progress'
import { useSchedulerHistory, useActiveScrapesObserver, useSchedulerStatus } from '../hooks'
import { cn } from '@/lib/utils'
import { formatDistanceToNow } from 'date-fns'
import { ArrowRight, Loader2, Play, CheckCircle2, XCircle, Radio, Circle, Clock } from 'lucide-react'

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
  connection_failed: 'destructive',
  running: 'outline',
  pending: 'outline',
}

function formatStatus(status: string): string {
  if (status === 'connection_failed') return 'Connection Lost'
  return status
}

// Platform-specific colors for progress bars
const PLATFORM_PROGRESS_COLORS: Record<string, string> = {
  betpawa: '[&>div]:bg-green-500',
  sportybet: '[&>div]:bg-blue-500',
  bet9ja: '[&>div]:bg-orange-500',
}

// Platform-specific colors for icons
const PLATFORM_ICON_COLORS: Record<string, string> = {
  betpawa: 'text-green-500',
  sportybet: 'text-blue-500',
  bet9ja: 'text-orange-500',
}

// Status icons for per-platform display
const PLATFORM_STATUS_ICONS: Record<string, { icon: typeof Circle; color: string }> = {
  pending: { icon: Circle, color: 'text-muted-foreground' },
  active: { icon: Loader2, color: 'text-blue-500' },
  completed: { icon: CheckCircle2, color: 'text-green-500' },
  failed: { icon: XCircle, color: 'text-destructive' },
}

// Platform abbreviations for display
const PLATFORM_ABBREV: Record<string, string> = {
  betpawa: 'BP',
  sportybet: 'SB',
  bet9ja: 'B9',
}

function PlatformStatusIcon({ platform, status }: { platform: string; status: string }) {
  const { icon: Icon, color } = PLATFORM_STATUS_ICONS[status] || PLATFORM_STATUS_ICONS.pending
  const abbrev = PLATFORM_ABBREV[platform] || platform.slice(0, 3).toUpperCase()
  return (
    <div className="flex items-center gap-0.5" title={`${platform}: ${status}`}>
      <Icon className={cn('h-3 w-3', color, status === 'active' && 'animate-spin')} />
      <span className="text-xs">{abbrev}</span>
    </div>
  )
}

// All platforms we track
const ALL_PLATFORMS = ['betpawa', 'sportybet', 'bet9ja']

// Determine per-platform status from run data
function getPlatformStatuses(
  run: { status: string; platform_timings: Record<string, unknown> | null },
  isCurrentlyRunning: boolean,
  activeProgress: ScrapeProgressEvent | null
): Record<string, string> {
  const statuses: Record<string, string> = {}

  for (const platform of ALL_PLATFORMS) {
    if (run.platform_timings?.[platform]) {
      // Platform exists in timings = completed
      statuses[platform] = 'completed'
    } else if (isCurrentlyRunning) {
      // Run is active - check if this platform is being scraped now
      if (activeProgress?.platform?.toLowerCase() === platform) {
        statuses[platform] = 'active'
      } else {
        statuses[platform] = 'pending'
      }
    } else if (run.status === 'failed' || run.status === 'partial' || run.status === 'connection_failed') {
      // Run finished with failures - platforms not in timings failed
      statuses[platform] = 'failed'
    } else {
      statuses[platform] = 'pending'
    }
  }

  return statuses
}

export function RecentRuns() {
  const queryClient = useQueryClient()
  const { data, isPending, error, refetch } = useSchedulerHistory(6)
  const { data: scheduler } = useSchedulerStatus()
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

        // Overall completion (platform is null) means whole scrape is done
        if (!data.platform && (data.phase === 'completed' || data.phase === 'failed')) {
          eventSource.close()
          setIsManualStreaming(false)

          // Optimistic update: immediately show correct status in list
          const newStatus = data.phase === 'completed' ? 'completed' : 'failed'
          queryClient.setQueryData(['scheduler-history'], (old: { runs: Array<{ id: number; status: string }> } | undefined) => {
            if (!old?.runs?.[0]) return old
            return {
              ...old,
              runs: old.runs.map((run, i) =>
                i === 0 ? { ...run, status: newStatus } : run
              ),
            }
          })

          // Then refetch for accurate data (events count, etc.)
          void queryClient.refetchQueries({ queryKey: ['scheduler-history'] })
          void queryClient.refetchQueries({ queryKey: ['events'] })
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

  // Auto-rescrape: if latest run has connection_failed status, auto-trigger new scrape
  const autoRescrapeTriggered = useRef(false)
  useEffect(() => {
    if (
      data?.runs?.[0]?.status === 'connection_failed' &&
      !autoRescrapeTriggered.current &&
      !isStreaming
    ) {
      autoRescrapeTriggered.current = true
      startScrape()
    }
  }, [data?.runs, isStreaming, startScrape])

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
          {[1, 2, 3, 4, 5, 6].map((i) => (
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
        <div className="flex items-center gap-2">
          {/* Interval badge */}
          {(() => {
            const scrapeJob = scheduler?.jobs?.find((j) => j.id === 'scrape_all_platforms')
            return (
              <>
                {scrapeJob?.interval_minutes && (
                  <Badge variant="outline" className="gap-1 text-xs">
                    <Clock className="h-3 w-3" />
                    {scrapeJob.interval_minutes}m
                  </Badge>
                )}

                {/* Next run time */}
                {scrapeJob?.next_run && !scheduler?.paused && (
                  <Badge variant="outline" className="gap-1 text-xs text-muted-foreground">
                    Next: {formatDistanceToNow(new Date(scrapeJob.next_run), { addSuffix: true })}
                  </Badge>
                )}
              </>
            )
          })()}

          {/* Scheduler status */}
          <Badge
            variant={scheduler?.paused ? 'secondary' : scheduler?.running ? 'default' : 'outline'}
            className={cn(
              'gap-1 text-xs',
              scheduler?.running && !scheduler?.paused && 'bg-green-500 hover:bg-green-600'
            )}
          >
            <span
              className={cn(
                'h-1.5 w-1.5 rounded-full',
                scheduler?.paused ? 'bg-yellow-500' :
                scheduler?.running ? 'bg-green-100' : 'bg-gray-500'
              )}
            />
            {scheduler?.paused ? 'Paused' : scheduler?.running ? 'Running' : 'Stopped'}
          </Badge>

          <Button variant="ghost" size="sm" asChild>
            <Link to="/scrape-runs">
              View All <ArrowRight className="ml-1 h-4 w-4" />
            </Link>
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {/* Live Progress Section */}
        {showProgressSection && (
          <div className="mb-4 pb-4 border-b">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  {isStreaming && activeProgress?.platform ? (
                    <Loader2 className={cn(
                      'h-3.5 w-3.5 animate-spin',
                      PLATFORM_ICON_COLORS[activeProgress.platform.toLowerCase()] || 'text-primary'
                    )} />
                  ) : isStreaming ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
                  ) : null}
                  {activeProgress?.phase === 'completed' && (
                    <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
                  )}
                  {activeProgress?.phase === 'failed' && (
                    <XCircle className="h-3.5 w-3.5 text-destructive" />
                  )}
                  <span className={cn(
                    'font-medium',
                    activeProgress?.phase === 'completed' && 'text-green-500',
                    activeProgress?.phase === 'failed' && 'text-destructive',
                    isStreaming && activeProgress?.platform && PLATFORM_ICON_COLORS[activeProgress.platform.toLowerCase()]
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
                  // Overall completion (platform is null) gets green/red
                  !activeProgress?.platform && activeProgress?.phase === 'completed' && '[&>div]:bg-green-500',
                  !activeProgress?.platform && activeProgress?.phase === 'failed' && '[&>div]:bg-destructive',
                  // Platform-specific colors during active scraping (including per-platform completion)
                  isStreaming && activeProgress?.platform &&
                    PLATFORM_PROGRESS_COLORS[activeProgress.platform.toLowerCase()]
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
              const platformStatuses = getPlatformStatuses(run, isCurrentlyRunning, activeProgress)
              return (
                <Link
                  key={run.id}
                  to={`/scrape-runs/${run.id}`}
                  className={cn(
                    "flex items-center justify-between py-2 border-b last:border-0 hover:bg-muted/50 transition-colors -mx-2 px-2 rounded cursor-pointer",
                    isCurrentlyRunning && "bg-primary/5"
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
                        {formatStatus(run.status)}
                      </Badge>
                      {run.trigger === 'scheduled' && (
                        <Radio className="h-3 w-3 text-blue-500" />
                      )}
                      {run.events_failed > 0 && (
                        <Badge variant="destructive" className="text-xs py-0 h-5">
                          {run.events_failed} err
                        </Badge>
                      )}
                      {duration && (
                        <span className="text-xs text-muted-foreground">
                          {duration}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <p className="text-xs text-muted-foreground">
                        {formatDistanceToNow(new Date(run.started_at), {
                          addSuffix: true,
                        })}
                      </p>
                      <div className="flex items-center gap-1.5">
                        {ALL_PLATFORMS.map((platform) => (
                          <PlatformStatusIcon
                            key={platform}
                            platform={platform}
                            status={platformStatuses[platform]}
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">
                      {run.events_scraped} events
                    </p>
                  </div>
                </Link>
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
