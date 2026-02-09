import { useState, useCallback, useRef, useEffect, useMemo } from 'react'
import { useQueryClient, type QueryClient } from '@tanstack/react-query'

import { useWebSocket, type WebSocketMessage } from './use-websocket'

/**
 * Scrape progress event data shape (matches SSE hook interface)
 */
export interface ScrapeProgressEvent {
  platform: string | null
  phase: string
  current: number
  total: number
  events_count: number | null
  message: string | null
  timestamp: string
}

/**
 * Per-platform progress tracking
 */
export interface PlatformProgress {
  phase: string
  eventsCount: number
  isComplete: boolean
  isFailed: boolean
}

/**
 * Options for useWebSocketScrapeProgress hook
 */
export interface UseWebSocketScrapeProgressOptions {
  /** Whether to connect (default: true) */
  enabled?: boolean
  /** Query client for invalidation (uses hook's client if not provided) */
  queryClient?: QueryClient
  /** Callback when scrape completes */
  onComplete?: () => void
}

/**
 * Return type matching existing SSE hook interface
 */
export interface UseWebSocketScrapeProgressReturn {
  /** Whether WebSocket is connected */
  isConnected: boolean
  /** Latest progress event */
  currentProgress: ScrapeProgressEvent | null
  /** Per-platform progress map */
  platformProgress: Map<string, PlatformProgress>
  /** Overall phase (idle, connecting, scraping, completed, failed, etc.) */
  overallPhase: string
  /** Error message if any */
  error: string | null
  /** Manually trigger reconnection */
  reconnect: () => void
}

/**
 * WebSocket-based scrape progress hook.
 *
 * Drop-in replacement for the SSE-based useScrapeProgress hook.
 * Subscribes to the scrape_progress topic and provides the same
 * interface for easy migration.
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
    currentProgress,
    platformProgress,
    overallPhase,
    error,
    reconnect,
  }
}
