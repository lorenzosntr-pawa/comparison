import { useState, useEffect, useRef } from 'react'
import { Link, useParams } from 'react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useScrapeRunDetail, useScrapeProgress, usePhaseHistory } from './hooks'
import {
  PlatformBreakdown,
  ErrorList,
  RetryDialog,
  Timeline,
  LiveLog,
  PlatformProgressCard,
  progressToLogMessage,
} from './components'
import type { LogMessage } from './components'
import { cn } from '@/lib/utils'
import { formatDistanceToNow, format } from 'date-fns'
import { ArrowLeft, Clock, Calendar, Zap, AlertCircle, Loader2, RotateCcw, Wifi, WifiOff } from 'lucide-react'

// All platforms for determining which ones failed
const ALL_PLATFORMS = ['betpawa', 'sportybet', 'bet9ja'] as const

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

export function ScrapeRunDetailPage() {
  const { id } = useParams<{ id: string }>()
  const runId = Number(id)
  const { data, isPending, error } = useScrapeRunDetail(runId, {
    pollWhileRunning: true, // Auto-refresh when scrape is running
  })

  const [retryDialogOpen, setRetryDialogOpen] = useState(false)

  const isRunning = data?.status === 'running'
  const canRetry = data?.status === 'partial' || data?.status === 'failed' || data?.status === 'connection_failed'

  // SSE streaming for real-time phase updates
  const {
    isConnected,
    currentProgress,
    platformProgress,
    overallPhase,
  } = useScrapeProgress({
    runId,
    isRunning,
  })

  // Phase history for timeline (completed runs)
  const { data: phaseHistory } = usePhaseHistory(runId)

  // Log messages for live log (accumulate from SSE)
  const [logMessages, setLogMessages] = useState<LogMessage[]>([])
  const prevProgressRef = useRef<typeof currentProgress>(null)

  // Accumulate SSE progress into log messages
  useEffect(() => {
    if (currentProgress && currentProgress !== prevProgressRef.current) {
      prevProgressRef.current = currentProgress
      const logMsg = progressToLogMessage(currentProgress)
      setLogMessages((prev) => [...prev.slice(-99), logMsg]) // Keep last 100 messages
    }
  }, [currentProgress])

  // Reset log messages when run changes
  useEffect(() => {
    setLogMessages([])
  }, [runId])

  // Determine failed platforms for retry dialog
  const failedPlatforms = (() => {
    if (!data) return []

    const failed: Array<{ name: string; errorCount: number }> = []

    // Get platforms that are missing from successful timings
    const successfulPlatforms = new Set(
      Object.keys(data.platform_timings || {})
    )

    // Count errors per platform
    const errorCounts: Record<string, number> = {}
    if (data.errors) {
      for (const err of data.errors) {
        if (err.platform) {
          errorCounts[err.platform.toLowerCase()] =
            (errorCounts[err.platform.toLowerCase()] || 0) + 1
        }
      }
    }

    // Platforms with errors or missing from timings
    for (const platform of ALL_PLATFORMS) {
      const hasErrors = errorCounts[platform] > 0
      const notInTimings = !successfulPlatforms.has(platform)

      if (hasErrors || notInTimings) {
        failed.push({
          name: platform,
          errorCount: errorCounts[platform] || 0,
        })
      }
    }

    return failed
  })()

  if (isPending) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-20" />
          <Skeleton className="h-8 w-48" />
        </div>
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-60 w-full" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/scrape-runs">
              <ArrowLeft className="mr-1 h-4 w-4" /> Back
            </Link>
          </Button>
        </div>
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">
              {error?.message || 'Failed to load scrape run details'}
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const duration = formatDuration(data.started_at, data.completed_at)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/scrape-runs">
              <ArrowLeft className="mr-1 h-4 w-4" /> Back
            </Link>
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Scrape Run #{id}</h1>
            <p className="text-muted-foreground">
              {formatDistanceToNow(new Date(data.started_at), { addSuffix: true })}
            </p>
          </div>
        </div>

        {/* Retry Button */}
        {canRetry && failedPlatforms.length > 0 && (
          <Button
            variant="outline"
            onClick={() => setRetryDialogOpen(true)}
            className="gap-2"
          >
            <RotateCcw className="h-4 w-4" />
            Retry Failed
          </Button>
        )}
      </div>

      {/* Live Progress Panel (shown when run is active) */}
      {isRunning && (
        <div className="animate-in fade-in slide-in-from-top-2 duration-300 space-y-4">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin text-primary" />
              <span className="font-medium">Scraping in Progress</span>
            </div>
            <div className="flex items-center gap-1 text-sm text-muted-foreground">
              {isConnected ? (
                <>
                  <Wifi className="h-4 w-4 text-green-500" />
                  <span>Connected</span>
                </>
              ) : (
                <>
                  <WifiOff className="h-4 w-4" />
                  <span>Connecting...</span>
                </>
              )}
            </div>
          </div>

          {/* Live Log */}
          <LiveLog messages={logMessages} maxHeight="h-40" />

          {/* Per-Platform Progress Cards */}
          <div className="grid gap-4 md:grid-cols-3">
            {ALL_PLATFORMS.map((platform) => {
              const timing = data.platform_timings?.[platform]
              const progress = platformProgress.get(platform)
              const isCurrentPlatform = currentProgress?.platform === platform
              const isComplete = progress?.isComplete || !!timing
              const isFailed = progress?.isFailed
              const isActive = isCurrentPlatform && !isComplete && !isFailed

              return (
                <PlatformProgressCard
                  key={platform}
                  platform={platform}
                  progress={progress}
                  timing={timing}
                  isActive={isActive}
                />
              )
            })}
          </div>

          {/* Current phase indicator */}
          {currentProgress && overallPhase !== 'completed' && overallPhase !== 'failed' && (
            <div className="text-sm text-muted-foreground">
              {currentProgress.message || `${capitalizeFirst(overallPhase)} ${currentProgress.platform ? capitalizeFirst(currentProgress.platform) : ''}...`}
            </div>
          )}
        </div>
      )}

      {/* Timeline (shown for completed runs) */}
      {!isRunning && phaseHistory && phaseHistory.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Phase Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            <Timeline phases={phaseHistory} />
          </CardContent>
        </Card>
      )}

      {/* Summary Card */}
      <Card className={cn(isRunning && 'opacity-75')}>
        <CardHeader>
          <CardTitle>Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-secondary">
                <Zap className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Status</p>
                <Badge
                  variant={statusVariants[data.status]}
                  className={cn(
                    data.status === 'completed' &&
                      'bg-green-500 hover:bg-green-600'
                  )}
                >
                  {formatStatus(data.status)}
                </Badge>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-secondary">
                <Clock className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Duration</p>
                <p className="font-medium">{duration || 'In progress'}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-secondary">
                <Calendar className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Started</p>
                <p className="font-medium">
                  {format(new Date(data.started_at), 'MMM d, HH:mm:ss')}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-secondary">
                <AlertCircle className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Events</p>
                <p className="font-medium">
                  {data.events_scraped} scraped
                  {data.events_failed > 0 && (
                    <span className="text-destructive">
                      {' '}
                      · {data.events_failed} failed
                    </span>
                  )}
                </p>
              </div>
            </div>
          </div>

          {data.trigger && (
            <div className="mt-4 border-t pt-4">
              <p className="text-sm text-muted-foreground">
                Trigger: <span className="font-medium">{data.trigger}</span>
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Platform Breakdown */}
      <div className={cn(isRunning && 'opacity-50')}>
        <PlatformBreakdown timings={data.platform_timings} />
      </div>

      {/* Errors (if any) */}
      {data.errors && data.errors.length > 0 && (
        <ErrorList errors={data.errors} />
      )}

      {/* Retry Dialog */}
      <RetryDialog
        open={retryDialogOpen}
        onOpenChange={setRetryDialogOpen}
        runId={runId}
        failedPlatforms={failedPlatforms}
      />
    </div>
  )
}

function capitalizeFirst(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1)
}
