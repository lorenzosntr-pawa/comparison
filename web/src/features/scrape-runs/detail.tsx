import { useState } from 'react'
import { Link, useParams } from 'react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useScrapeRunDetail, useScrapeProgress } from './hooks'
import { PlatformBreakdown, ErrorList, RetryDialog } from './components'
import { cn } from '@/lib/utils'
import { formatDistanceToNow, format } from 'date-fns'
import { ArrowLeft, Clock, Calendar, Zap, AlertCircle, Loader2, RotateCcw, CheckCircle2, XCircle, Wifi, WifiOff } from 'lucide-react'

// All platforms for determining which ones failed
const ALL_PLATFORMS = ['betpawa', 'sportybet', 'bet9ja'] as const

// Platform-specific colors for progress visualization
const PLATFORM_COLORS: Record<string, { bg: string; text: string }> = {
  betpawa: { bg: 'bg-green-500', text: 'text-green-500' },
  sportybet: { bg: 'bg-blue-500', text: 'text-blue-500' },
  bet9ja: { bg: 'bg-orange-500', text: 'text-orange-500' },
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
  const canRetry = data?.status === 'partial' || data?.status === 'failed'

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
        <div className="animate-in fade-in slide-in-from-top-2 duration-300">
          <Card className="border-primary/50 bg-primary/5">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin text-primary" />
                  <CardTitle className="text-base">Scraping in Progress</CardTitle>
                </div>
                <div className="flex items-center gap-1">
                  {isConnected ? (
                    <Wifi className="h-4 w-4 text-green-500" />
                  ) : (
                    <WifiOff className="h-4 w-4 text-muted-foreground" />
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {ALL_PLATFORMS.map((platform) => {
                const timing = data.platform_timings?.[platform]
                const sseProgress = platformProgress.get(platform)
                const colors = PLATFORM_COLORS[platform]

                // Use SSE data for real-time phase, fall back to timing completion
                const isComplete = sseProgress?.isComplete || !!timing
                const isFailed = sseProgress?.isFailed
                const isCurrentPlatform = currentProgress?.platform === platform
                const isActive = isCurrentPlatform && !isComplete && !isFailed

                // Get phase display text from SSE
                const getPhaseText = () => {
                  if (isComplete) {
                    const count = sseProgress?.eventsCount ?? timing?.events_count ?? 0
                    return `${count} events`
                  }
                  if (isFailed) return 'Failed'
                  if (sseProgress?.phase === 'storing') return 'Storing...'
                  if (sseProgress?.phase === 'scraping') return 'Scraping...'
                  if (isActive) return 'Scraping...'
                  return 'Pending'
                }

                // Calculate progress width based on actual phase
                const getProgressWidth = () => {
                  if (isComplete) return '100%'
                  if (isFailed) return '100%'
                  if (sseProgress?.phase === 'storing') return '80%'
                  if (sseProgress?.phase === 'scraping' || isActive) return '50%'
                  return '0%'
                }

                return (
                  <div key={platform} className="space-y-1.5">
                    <div className="flex items-center justify-between text-sm">
                      <span className={cn(
                        'font-medium capitalize',
                        isActive && colors.text
                      )}>
                        {platform}
                        {isActive && (
                          <Loader2 className="ml-1.5 inline h-3 w-3 animate-spin" />
                        )}
                      </span>
                      <span className="text-muted-foreground">
                        {getPhaseText()}
                        {isComplete && (
                          <CheckCircle2 className="ml-1.5 inline h-3.5 w-3.5 text-green-500" />
                        )}
                        {isFailed && (
                          <XCircle className="ml-1.5 inline h-3.5 w-3.5 text-destructive" />
                        )}
                      </span>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-secondary">
                      <div
                        className={cn(
                          'h-1.5 rounded-full transition-all duration-500',
                          isComplete ? colors.bg :
                          isFailed ? 'bg-destructive' :
                          isActive ? `${colors.bg} animate-pulse` :
                          'bg-muted-foreground/30'
                        )}
                        style={{ width: getProgressWidth() }}
                      />
                    </div>
                  </div>
                )
              })}

              {/* Current phase indicator */}
              {currentProgress && overallPhase !== 'completed' && overallPhase !== 'failed' && (
                <div className="pt-2 border-t text-sm text-muted-foreground">
                  {currentProgress.message || `${capitalizeFirst(overallPhase)} ${currentProgress.platform ? capitalizeFirst(currentProgress.platform) : ''}...`}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
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
                  {data.status}
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
