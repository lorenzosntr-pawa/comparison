import { useEffect, useRef, useReducer, useCallback, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
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

interface ProgressState {
  isConnected: boolean
  error: string | null
  currentProgress: ScrapeProgressEvent | null
  platformProgress: Map<string, PlatformProgress>
  overallPhase: string
}

type ProgressAction =
  | { type: 'RESET' }
  | { type: 'CONNECTING' }
  | { type: 'CONNECTED' }
  | { type: 'DISCONNECTED' }
  | { type: 'ERROR'; error: string }
  | { type: 'PROGRESS'; event: ScrapeProgressEvent }

function progressReducer(state: ProgressState, action: ProgressAction): ProgressState {
  switch (action.type) {
    case 'RESET':
      return {
        isConnected: false,
        error: null,
        currentProgress: null,
        platformProgress: new Map(),
        overallPhase: 'idle',
      }
    case 'CONNECTING':
      return {
        ...state,
        error: null,
        currentProgress: null,
        platformProgress: new Map(),
        overallPhase: 'connecting',
      }
    case 'CONNECTED':
      return { ...state, isConnected: true, overallPhase: 'starting' }
    case 'DISCONNECTED':
      return { ...state, isConnected: false }
    case 'ERROR':
      return { ...state, isConnected: false, error: action.error, overallPhase: 'error' }
    case 'PROGRESS': {
      const { event } = action
      const newPlatformProgress = new Map(state.platformProgress)

      if (event.platform) {
        newPlatformProgress.set(event.platform, {
          phase: event.phase,
          eventsCount: event.events_count ?? 0,
          isComplete: event.phase === 'completed' || event.phase === 'storing_complete',
          isFailed: event.phase === 'failed',
        })
      }

      return {
        ...state,
        currentProgress: event,
        overallPhase: event.phase,
        platformProgress: newPlatformProgress,
      }
    }
    default:
      return state
  }
}

const initialState: ProgressState = {
  isConnected: false,
  error: null,
  currentProgress: null,
  platformProgress: new Map(),
  overallPhase: 'idle',
}

/** Maximum WebSocket failures before falling back to SSE */
const WS_FAIL_THRESHOLD = 3

interface UseScrapeProgressOptions {
  /** Run ID to track (only connects when provided and run is active) */
  runId?: number
  /** Whether the run is currently active */
  isRunning: boolean
  /** Callback when scrape completes */
  onComplete?: () => void
}

/**
 * Internal SSE-based progress hook used as fallback.
 * Connects to run-specific SSE endpoint when enabled.
 */
function useSseProgress({
  runId,
  enabled,
  onComplete,
}: {
  runId?: number
  enabled: boolean
  onComplete?: () => void
}) {
  const queryClient = useQueryClient()
  const eventSourceRef = useRef<EventSource | null>(null)
  const [state, dispatch] = useReducer(progressReducer, initialState)

  // Create stable reference to onComplete
  const onCompleteRef = useRef(onComplete)
  useEffect(() => {
    onCompleteRef.current = onComplete
  }, [onComplete])

  // Create stable reference to runId for closure
  const runIdRef = useRef(runId)
  useEffect(() => {
    runIdRef.current = runId
  }, [runId])

  // Track if we've already fired completion to avoid double-invalidation
  const completedRef = useRef(false)

  // Connect to SSE stream for observing existing scrape
  const connect = useCallback(() => {
    // Prevent duplicate connections
    if (eventSourceRef.current) {
      return
    }

    // Must have runId to observe
    const currentRunId = runIdRef.current
    if (!currentRunId) {
      return
    }

    completedRef.current = false
    dispatch({ type: 'CONNECTING' })

    // Use run-specific observe endpoint (NOT /api/scrape/stream which creates new scrapes)
    const eventSource = new EventSource(`/api/scrape/runs/${currentRunId}/progress`)
    eventSourceRef.current = eventSource

    eventSource.onopen = () => {
      dispatch({ type: 'CONNECTED' })
    }

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as ScrapeProgressEvent
        dispatch({ type: 'PROGRESS', event: data })

        // Handle completion
        if (data.phase === 'completed' || data.phase === 'failed') {
          eventSource.close()
          eventSourceRef.current = null
          dispatch({ type: 'DISCONNECTED' })

          // Avoid double-invalidation if already completed
          if (!completedRef.current) {
            completedRef.current = true

            // Invalidate queries to refresh data
            queryClient.invalidateQueries({ queryKey: ['scheduler-history'] })
            queryClient.invalidateQueries({ queryKey: ['events'] })
            if (runIdRef.current) {
              queryClient.invalidateQueries({ queryKey: ['scrape-run', runIdRef.current] })
            }

            onCompleteRef.current?.()
          }
        }
      } catch (e) {
        console.error('Failed to parse SSE event:', e)
      }
    }

    eventSource.onerror = () => {
      eventSource.close()
      eventSourceRef.current = null
      // 410 Gone means scrape already completed - not a real error
      // Just disconnect silently; the UI will show completed status from API data
      dispatch({ type: 'DISCONNECTED' })
    }
  }, [queryClient])

  // Disconnect from SSE stream
  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
      dispatch({ type: 'DISCONNECTED' })
    }
  }, [])

  // Auto-connect when enabled and runId is available
  useEffect(() => {
    if (enabled && runId) {
      // Schedule connection for next tick to avoid setState in effect
      const timeoutId = setTimeout(() => {
        if (!eventSourceRef.current) {
          connect()
        }
      }, 0)
      return () => clearTimeout(timeoutId)
    } else if (!enabled && eventSourceRef.current) {
      disconnect()
    }

    // Cleanup on unmount
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [enabled, runId, connect, disconnect])

  return {
    isConnected: state.isConnected,
    error: state.error,
    currentProgress: state.currentProgress,
    platformProgress: state.platformProgress,
    overallPhase: state.overallPhase,
  }
}

/**
 * Hook to track scrape progress with WebSocket primary and SSE fallback.
 *
 * Prefers WebSocket transport, automatically falls back to SSE after
 * repeated WebSocket failures.
 */
export function useScrapeProgress({ runId, isRunning, onComplete }: UseScrapeProgressOptions) {
  // Track WebSocket failures for fallback logic
  const [wsFailCount, setWsFailCount] = useState(0)
  const wsEnabled = wsFailCount < WS_FAIL_THRESHOLD && isRunning

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

  // Primary: WebSocket transport
  const ws = useWebSocketScrapeProgress({
    enabled: wsEnabled,
    onComplete: () => {
      // Avoid double-firing if SSE also completes
      if (!completedRef.current) {
        completedRef.current = true
        onCompleteRef.current?.()
      }
    },
  })

  // Track WebSocket errors to trigger fallback
  const prevWsPhase = useRef<string | null>(null)
  useEffect(() => {
    if (ws.overallPhase === 'error' && prevWsPhase.current !== 'error') {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- WebSocket state is external system
      setWsFailCount((prev) => {
        const newCount = prev + 1
        if (newCount >= WS_FAIL_THRESHOLD) {
          console.warn(
            `[useScrapeProgress] WebSocket failed ${newCount} times, falling back to SSE`
          )
        }
        return newCount
      })
    }
    prevWsPhase.current = ws.overallPhase
  }, [ws.overallPhase])

  // Fallback: SSE transport (enabled when WebSocket is disabled and run is active)
  const sseEnabled = !wsEnabled && isRunning
  const sse = useSseProgress({
    runId,
    enabled: sseEnabled,
    onComplete: () => {
      // Avoid double-firing if WebSocket also completes
      if (!completedRef.current) {
        completedRef.current = true
        onCompleteRef.current?.()
      }
    },
  })

  // Combine states: prefer WebSocket when connected, SSE when not
  const isConnected = wsEnabled ? ws.isConnected : sse.isConnected
  const error = wsEnabled ? ws.error : sse.error

  // Use the active transport's state
  const currentProgress = wsEnabled ? ws.currentProgress : sse.currentProgress
  const platformProgress = wsEnabled ? ws.platformProgress : sse.platformProgress
  const overallPhase = wsEnabled ? ws.overallPhase : sse.overallPhase

  return {
    isConnected,
    error,
    currentProgress,
    platformProgress,
    overallPhase,
    // Expose transport info for debugging
    transport: wsEnabled ? 'websocket' : sseEnabled ? 'sse' : 'none',
  }
}
