import { useEffect, useRef, useState, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import { Loader2, CheckCircle2, XCircle, Wifi, WifiOff } from 'lucide-react'

export interface ScrapeProgressEvent {
  platform: string | null
  phase: string
  current: number
  total: number
  events_count: number | null
  duration_ms: number | null
  elapsed_ms: number | null
  message: string | null
  timestamp: string
}

interface PlatformProgress {
  phase: string
  eventsCount: number
  isComplete: boolean
  isFailed: boolean
  durationMs: number | null
  startedAt: number | null
}

interface LiveProgressPanelProps {
  onComplete?: () => void
  showOnlyWhenActive?: boolean
}

const PLATFORM_ORDER = ['betpawa', 'sportybet', 'bet9ja'] as const
const PLATFORM_COLORS: Record<string, string> = {
  betpawa: 'bg-green-500',
  sportybet: 'bg-blue-500',
  bet9ja: 'bg-orange-500',
}
const PLATFORM_TEXT_COLORS: Record<string, string> = {
  betpawa: 'text-green-500',
  sportybet: 'text-blue-500',
  bet9ja: 'text-orange-500',
}

export function LiveProgressPanel({
  onComplete,
  showOnlyWhenActive = false,
}: LiveProgressPanelProps) {
  const queryClient = useQueryClient()
  const eventSourceRef = useRef<EventSource | null>(null)

  const [isConnected, setIsConnected] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentProgress, setCurrentProgress] = useState<ScrapeProgressEvent | null>(null)
  const [platformProgress, setPlatformProgress] = useState<Map<string, PlatformProgress>>(new Map())
  const [overallPhase, setOverallPhase] = useState<string>('idle')

  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    setIsConnected(false)
    setIsStreaming(false)
  }, [])

  const startScrape = useCallback(() => {
    cleanup()
    setError(null)
    setCurrentProgress(null)
    setPlatformProgress(new Map())
    setOverallPhase('connecting')
    setIsStreaming(true)

    const eventSource = new EventSource('/api/scrape/stream')
    eventSourceRef.current = eventSource

    eventSource.onopen = () => {
      setIsConnected(true)
      setOverallPhase('starting')
    }

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as ScrapeProgressEvent
        setCurrentProgress(data)
        setOverallPhase(data.phase)

        // Update per-platform progress
        if (data.platform) {
          setPlatformProgress((prev) => {
            const updated = new Map(prev)
            const existing = prev.get(data.platform!)
            updated.set(data.platform!, {
              phase: data.phase,
              eventsCount: data.events_count ?? existing?.eventsCount ?? 0,
              isComplete: data.phase === 'completed' || data.phase === 'storing_complete',
              isFailed: data.phase === 'failed',
              durationMs: data.duration_ms ?? existing?.durationMs ?? null,
              startedAt: existing?.startedAt ?? (data.phase === 'scraping' ? Date.now() : null),
            })
            return updated
          })
        }

        // Handle completion
        if (data.phase === 'completed' || data.phase === 'failed') {
          eventSource.close()
          setIsConnected(false)
          setIsStreaming(false)

          // Invalidate queries to refresh data
          queryClient.invalidateQueries({ queryKey: ['scheduler-history'] })
          queryClient.invalidateQueries({ queryKey: ['events'] })
          queryClient.invalidateQueries({ queryKey: ['scrape-run'] })

          onComplete?.()
        }
      } catch (e) {
        console.error('Failed to parse SSE event:', e)
      }
    }

    eventSource.onerror = () => {
      eventSource.close()
      setIsConnected(false)
      setIsStreaming(false)
      setError('Connection lost')
      setOverallPhase('error')
    }
  }, [cleanup, queryClient, onComplete])

  // Cleanup on unmount
  useEffect(() => {
    return cleanup
  }, [cleanup])

  // Calculate overall progress percentage
  const calculateOverallProgress = (): number => {
    if (overallPhase === 'idle' || overallPhase === 'connecting') return 0
    if (overallPhase === 'completed') return 100
    if (overallPhase === 'failed' || overallPhase === 'error') return 0

    // Count completed platforms
    const completedPlatforms = Array.from(platformProgress.values()).filter(
      (p) => p.isComplete
    ).length
    const totalPlatforms = PLATFORM_ORDER.length

    // Base progress on completed platforms + current progress within active platform
    const baseProgress = (completedPlatforms / totalPlatforms) * 100

    // Add partial progress for current platform (assume 50% for scraping, 100% for storing)
    if (currentProgress?.platform && !platformProgress.get(currentProgress.platform)?.isComplete) {
      const phaseBonus = currentProgress.phase === 'storing' ? 0.5 : 0.25
      return Math.min(99, baseProgress + (phaseBonus / totalPlatforms) * 100)
    }

    return Math.min(99, baseProgress)
  }

  const getPhaseDisplay = (): string => {
    if (!currentProgress) {
      if (overallPhase === 'connecting') return 'Connecting...'
      if (overallPhase === 'starting') return 'Starting scrape...'
      return 'Ready to start'
    }

    if (currentProgress.phase === 'completed') return 'Scrape completed!'
    if (currentProgress.phase === 'failed') return 'Scrape failed'
    if (currentProgress.phase === 'scraping' && currentProgress.platform) {
      return `Scraping ${capitalizeFirst(currentProgress.platform)}...`
    }
    if (currentProgress.phase === 'storing' && currentProgress.platform) {
      return `Storing ${capitalizeFirst(currentProgress.platform)} events...`
    }
    return currentProgress.message ?? currentProgress.phase
  }

  // Hide if showOnlyWhenActive and not streaming
  if (showOnlyWhenActive && !isStreaming && overallPhase === 'idle') {
    return null
  }

  const overallProgress = calculateOverallProgress()
  const isComplete = overallPhase === 'completed'
  const isFailed = overallPhase === 'failed' || overallPhase === 'error'

  return (
    <Card className={cn(
      'transition-all',
      isStreaming && 'ring-2 ring-primary/20'
    )}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Live Scrape Progress</CardTitle>
          <div className="flex items-center gap-2">
            {isConnected ? (
              <Wifi className="h-4 w-4 text-green-500" />
            ) : (
              <WifiOff className="h-4 w-4 text-muted-foreground" />
            )}
            {isStreaming && (
              <Loader2 className="h-4 w-4 animate-spin text-primary" />
            )}
            {isComplete && (
              <CheckCircle2 className="h-4 w-4 text-green-500" />
            )}
            {isFailed && (
              <XCircle className="h-4 w-4 text-destructive" />
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Overall Progress */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className={cn(
              'font-medium',
              isComplete && 'text-green-500',
              isFailed && 'text-destructive'
            )}>
              {getPhaseDisplay()}
            </span>
            <span className="text-muted-foreground">{Math.round(overallProgress)}%</span>
          </div>
          <Progress
            value={overallProgress}
            className={cn(
              'h-2',
              isComplete && '[&>div]:bg-green-500',
              isFailed && '[&>div]:bg-destructive'
            )}
          />
        </div>

        {/* Per-Platform Progress */}
        {(isStreaming || platformProgress.size > 0) && (
          <div className="space-y-3 pt-2 border-t">
            {PLATFORM_ORDER.map((platform) => {
              const progress = platformProgress.get(platform)
              const isCurrentPlatform = currentProgress?.platform === platform
              const isActive = isCurrentPlatform && !progress?.isComplete

              return (
                <div key={platform} className="space-y-1.5">
                  <div className="flex items-center justify-between text-sm">
                    <span className={cn(
                      'font-medium capitalize',
                      isActive && PLATFORM_TEXT_COLORS[platform]
                    )}>
                      {platform}
                      {isActive && (
                        <Loader2 className="ml-1.5 inline h-3 w-3 animate-spin" />
                      )}
                    </span>
                    <span className="text-muted-foreground">
                      {progress?.isComplete ? (
                        <>
                          {progress.eventsCount} events
                          {progress.durationMs != null && (
                            <span className="ml-1 text-xs">({(progress.durationMs / 1000).toFixed(1)}s)</span>
                          )}
                        </>
                      ) : isActive ? (
                        'scraping...'
                      ) : progress?.isFailed ? (
                        'failed'
                      ) : (
                        'pending'
                      )}
                      {progress && (
                        <span className="ml-2">
                          {progress.isComplete && (
                            <CheckCircle2 className="inline h-3.5 w-3.5 text-green-500" />
                          )}
                          {progress.isFailed && (
                            <XCircle className="inline h-3.5 w-3.5 text-destructive" />
                          )}
                        </span>
                      )}
                    </span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-secondary">
                    <div
                      className={cn(
                        'h-1.5 rounded-full transition-all duration-300',
                        progress?.isComplete ? PLATFORM_COLORS[platform] :
                        progress?.isFailed ? 'bg-destructive' :
                        isActive ? PLATFORM_COLORS[platform] + ' animate-pulse' :
                        'bg-muted-foreground/30'
                      )}
                      style={{
                        width: progress?.isComplete ? '100%' :
                               isActive ? '60%' :
                               '0%'
                      }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </div>
        )}

        {/* Start Button (only when not streaming) */}
        {!isStreaming && overallPhase !== 'completed' && (
          <button
            onClick={startScrape}
            className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            {isFailed ? 'Retry Scrape' : 'Start Scrape'}
          </button>
        )}
      </CardContent>
    </Card>
  )
}

function capitalizeFirst(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1)
}
