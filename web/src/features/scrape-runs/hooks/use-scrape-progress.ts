/**
 * Hook for tracking real-time scrape progress via WebSocket.
 *
 * @module use-scrape-progress
 * @description Provides real-time progress updates for an active scrape run
 * using WebSocket transport. This is the primary hook for showing live
 * progress bars and status updates in the scrape detail view.
 *
 * Wraps the shared use-websocket-scrape-progress hook with run-specific
 * logic including completion detection and callback management.
 *
 * @example
 * ```typescript
 * import { useScrapeProgress } from '@/features/scrape-runs/hooks/use-scrape-progress'
 *
 * function ScrapeProgressBar({ runId, isRunning }) {
 *   const {
 *     currentProgress,
 *     platformProgress,
 *     overallPhase,
 *   } = useScrapeProgress({
 *     runId,
 *     isRunning,
 *     onComplete: () => queryClient.invalidateQueries(['scrape-run', runId]),
 *   })
 *
 *   return (
 *     <div>
 *       <p>Phase: {overallPhase}</p>
 *       <p>Progress: {currentProgress?.current}/{currentProgress?.total}</p>
 *     </div>
 *   )
 * }
 * ```
 */

import { useEffect, useRef } from 'react'
import { useWebSocketScrapeProgress } from '@/hooks/use-websocket-scrape-progress'

/**
 * Configuration options for useScrapeProgress.
 */
interface UseScrapeProgressOptions {
  /** Run ID to track (only connects when provided and run is active) */
  runId?: number
  /** Whether the run is currently active - controls WebSocket connection */
  isRunning: boolean
  /** Callback fired once when scrape completes (protected against double-firing) */
  onComplete?: () => void
}

/**
 * Tracks scrape progress via WebSocket connection.
 *
 * @description Connects to the scrape progress WebSocket when isRunning is true,
 * providing real-time updates about scrape phases and item counts. Includes
 * completion detection that fires the onComplete callback exactly once.
 *
 * ## Behavior
 * - WebSocket connection enabled only when `isRunning: true`
 * - Completion callback fires exactly once per run (ref-tracked)
 * - Completion flag resets when a new run starts
 * - Uses stable refs to prevent callback identity issues
 *
 * @param options - Configuration including runId, isRunning flag, and onComplete callback
 * @returns Object with connection state and progress data
 *
 * @example
 * ```typescript
 * const { isConnected, currentProgress, platformProgress, overallPhase } = useScrapeProgress({
 *   runId: activeRunId,
 *   isRunning: status === 'running',
 *   onComplete: () => {
 *     // Refresh the run detail to get final state
 *     queryClient.invalidateQueries(['scrape-run', activeRunId])
 *   },
 * })
 * ```
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
