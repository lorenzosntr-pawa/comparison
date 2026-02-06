import { useEffect, useRef } from 'react'
import { useWebSocketScrapeProgress } from '@/hooks/use-websocket-scrape-progress'

export interface ScrapeProgressEvent {
  platform: string | null
  phase: string
  current: number
  total: number
  events_count: number | null
  message: string | null
  timestamp: string
}

export interface PlatformProgress {
  phase: string
  eventsCount: number
  isComplete: boolean
  isFailed: boolean
}

interface UseScrapeProgressOptions {
  /** Run ID to track (only connects when provided and run is active) */
  runId?: number
  /** Whether the run is currently active */
  isRunning: boolean
  /** Callback when scrape completes */
  onComplete?: () => void
}

/**
 * Hook to track scrape progress via WebSocket.
 */
export function useScrapeProgress({ isRunning, onComplete }: UseScrapeProgressOptions) {
  // Create stable reference to onComplete
  const onCompleteRef = useRef(onComplete)
  useEffect(() => {
    onCompleteRef.current = onComplete
  }, [onComplete])

  // Track if we've already fired completion to avoid double-invalidation
  const completedRef = useRef(false)

  // Reset completed flag when run starts
  useEffect(() => {
    if (isRunning) {
      completedRef.current = false
    }
  }, [isRunning])

  // WebSocket transport
  const ws = useWebSocketScrapeProgress({
    enabled: isRunning,
    onComplete: () => {
      if (!completedRef.current) {
        completedRef.current = true
        onCompleteRef.current?.()
      }
    },
  })

  return {
    isConnected: ws.isConnected,
    error: ws.error,
    currentProgress: ws.currentProgress,
    platformProgress: ws.platformProgress,
    overallPhase: ws.overallPhase,
  }
}
