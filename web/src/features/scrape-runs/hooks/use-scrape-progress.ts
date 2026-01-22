import { useEffect, useRef, useReducer, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'

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

interface UseScrapeProgressOptions {
  /** Run ID to track (only connects when provided and run is active) */
  runId?: number
  /** Whether the run is currently active */
  isRunning: boolean
  /** Callback when scrape completes */
  onComplete?: () => void
}

export function useScrapeProgress({ runId, isRunning, onComplete }: UseScrapeProgressOptions) {
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

          // Invalidate queries to refresh data
          queryClient.invalidateQueries({ queryKey: ['scheduler-history'] })
          queryClient.invalidateQueries({ queryKey: ['events'] })
          if (runIdRef.current) {
            queryClient.invalidateQueries({ queryKey: ['scrape-run', runIdRef.current] })
          }

          onCompleteRef.current?.()
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

  // Auto-connect when run becomes active, disconnect when it stops
  useEffect(() => {
    if (isRunning && runId) {
      // Schedule connection for next tick to avoid setState in effect
      const timeoutId = setTimeout(() => {
        if (!eventSourceRef.current) {
          connect()
        }
      }, 0)
      return () => clearTimeout(timeoutId)
    } else if (!isRunning && eventSourceRef.current) {
      disconnect()
    }

    // Cleanup on unmount
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [isRunning, runId, connect, disconnect])

  return {
    isConnected: state.isConnected,
    error: state.error,
    currentProgress: state.currentProgress,
    platformProgress: state.platformProgress,
    overallPhase: state.overallPhase,
  }
}
