/**
 * WebSocket-based scrape progress tracking hook.
 *
 * @module use-websocket-scrape-progress
 * @description Provides real-time scrape progress updates via WebSocket subscription.
 * Tracks overall scrape status and per-platform progress, automatically invalidating
 * TanStack Query caches when scrapes complete.
 *
 * This hook is a drop-in replacement for the SSE-based useScrapeProgress hook,
 * providing the same interface for easy migration.
 *
 * @example
 * ```typescript
 * import { useWebSocketScrapeProgress } from '@/hooks/use-websocket-scrape-progress'
 *
 * function ScrapeMonitor() {
 *   const {
 *     isConnected,
 *     currentProgress,
 *     platformProgress,
 *     overallPhase,
 *   } = useWebSocketScrapeProgress({
 *     onComplete: () => console.log('Scrape finished!'),
 *   })
 *
 *   return (
 *     <div>
 *       <p>Phase: {overallPhase}</p>
 *       {currentProgress && (
 *         <p>Progress: {currentProgress.current}/{currentProgress.total}</p>
 *       )}
 *     </div>
 *   )
 * }
 * ```
 */

import { useState, useCallback, useRef, useEffect, useMemo } from 'react'
import { useQueryClient, type QueryClient } from '@tanstack/react-query'

import { useWebSocket, type WebSocketMessage } from './use-websocket'

/**
 * Scrape progress event data from the backend.
 *
 * @description Represents a single progress update during a scrape run,
 * providing phase information, counts, and optional messages.
 */
export interface ScrapeProgressEvent {
  /** Platform slug (null for overall progress) */
  platform: string | null
  /** Current phase (e.g., 'fetching', 'scraping', 'storing', 'completed', 'failed') */
  phase: string
  /** Current progress count */
  current: number
  /** Total items to process */
  total: number
  /** Number of events processed (null during early phases) */
  events_count: number | null
  /** Optional status message */
  message: string | null
  /** ISO timestamp of this progress update */
  timestamp: string
}

/**
 * Progress tracking for a single platform.
 *
 * @description Aggregated progress state for one bookmaker platform.
 */
export interface PlatformProgress {
  /** Current phase for this platform */
  phase: string
  /** Number of events scraped from this platform */
  eventsCount: number
  /** Whether scraping for this platform is complete */
  isComplete: boolean
  /** Whether scraping for this platform failed */
  isFailed: boolean
}

/**
 * Configuration options for the scrape progress hook.
 */
export interface UseWebSocketScrapeProgressOptions {
  /** Whether to connect (default: true). Set to false to disable progress tracking. */
  enabled?: boolean
  /** Optional query client for cache invalidation (uses hook's client if not provided) */
  queryClient?: QueryClient
  /** Callback invoked when scrape completes (success or failure) */
  onComplete?: () => void
}

/**
 * Return value from the scrape progress hook.
 *
 * @description Provides comprehensive scrape progress state for UI rendering.
 */
export interface UseWebSocketScrapeProgressReturn {
  /** Whether WebSocket is connected */
  isConnected: boolean
  /** WebSocket connection state (for status indicator) */
  connectionState: 'connecting' | 'connected' | 'disconnected' | 'error'
  /** Latest progress event received, or null if none */
  currentProgress: ScrapeProgressEvent | null
  /** Per-platform progress map (keyed by platform slug) */
  platformProgress: Map<string, PlatformProgress>
  /** Overall phase (idle, connecting, scraping, completed, failed, etc.) */
  overallPhase: string
  /** Error message if connection failed, or null */
  error: string | null
  /** Manually trigger WebSocket reconnection */
  reconnect: () => void
}

/**
 * Hook for tracking real-time scrape progress via WebSocket.
 *
 * @description Subscribes to the 'scrape_progress' WebSocket topic and maintains
 * progress state for both overall scrape and per-platform progress. Automatically
 * invalidates relevant TanStack Query caches when scrapes complete.
 *
 * @param options - Configuration options
 * @returns Scrape progress state and control methods
 */
export function useWebSocketScrapeProgress(
  options: UseWebSocketScrapeProgressOptions = {}
): UseWebSocketScrapeProgressReturn {
  const { enabled = true, queryClient: providedClient, onComplete } = options

  const defaultClient = useQueryClient()
  const queryClient = providedClient ?? defaultClient

  // State matching SSE hook interface
  const [currentProgress, setCurrentProgress] = useState<ScrapeProgressEvent | null>(null)
  const [platformProgress, setPlatformProgress] = useState<Map<string, PlatformProgress>>(
    () => new Map()
  )
  // Track the phase from last received message (null if no message yet)
  const [messagePhase, setMessagePhase] = useState<string | null>(null)
  const [wsError, setWsError] = useState<string | null>(null)

  // Stable ref for onComplete callback
  const onCompleteRef = useRef(onComplete)
  useEffect(() => {
    onCompleteRef.current = onComplete
  }, [onComplete])

  // Handle incoming scrape_progress messages
  const handleMessage = useCallback(
    (message: WebSocketMessage<ScrapeProgressEvent>) => {
      if (message.type !== 'scrape_progress') return

      const event = message.data
      setCurrentProgress(event)
      setMessagePhase(event.phase)

      // Update platform-specific progress
      if (event.platform) {
        setPlatformProgress((prev) => {
          const next = new Map(prev)
          next.set(event.platform!, {
            phase: event.phase,
            eventsCount: event.events_count ?? 0,
            isComplete: event.phase === 'completed' || event.phase === 'storing_complete',
            isFailed: event.phase === 'failed',
          })
          return next
        })
      }

      // Handle completion/failure
      if (event.phase === 'completed' || event.phase === 'failed') {
        // Invalidate queries to refresh data
        queryClient.invalidateQueries({ queryKey: ['scheduler-history'] })
        queryClient.invalidateQueries({ queryKey: ['events'] })
        queryClient.invalidateQueries({ queryKey: ['scrape-run'] })

        onCompleteRef.current?.()
      }
    },
    [queryClient]
  )

  // Handle WebSocket errors
  const handleError = useCallback((code: string, detail: string) => {
    setWsError(`${code}: ${detail}`)
  }, [])

  // Handle reconnection - invalidate queries to sync state
  const handleReconnect = useCallback(() => {
    console.log('[useWebSocketScrapeProgress] Reconnected, invalidating queries')
    queryClient.invalidateQueries({ queryKey: ['scheduler-history'] })
    queryClient.invalidateQueries({ queryKey: ['events'] })
    queryClient.invalidateQueries({ queryKey: ['scrape-run'] })
  }, [queryClient])

  // Connect to WebSocket with scrape_progress topic
  const { state, error: connectionError, reconnect } = useWebSocket<ScrapeProgressEvent>({
    topics: ['scrape_progress'],
    enabled,
    onMessage: handleMessage,
    onError: handleError,
    onReconnect: handleReconnect,
  })

  // Derive isConnected from state
  const isConnected = state === 'connected'

  // Combine errors
  const error = wsError ?? connectionError

  // Derive overall phase from WebSocket state and message phase
  // Priority: message phase (if received) > connection state > idle
  const overallPhase = useMemo(() => {
    // If we have a message phase, use it
    if (messagePhase !== null) {
      return messagePhase
    }
    // Otherwise derive from connection state
    if (state === 'connecting') {
      return 'connecting'
    }
    if (state === 'error') {
      return 'error'
    }
    return 'idle'
  }, [messagePhase, state])

  return {
    isConnected,
    connectionState: state,
    currentProgress,
    platformProgress,
    overallPhase,
    error,
    reconnect,
  }
}
