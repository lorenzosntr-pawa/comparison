/**
 * Hook for observing active scrape runs in real-time.
 *
 * @module use-observe-scrape
 * @description Provides real-time observation of active scrape runs via WebSocket.
 * This hook handles the complexity of checking for active scrapes via REST API
 * and then switching to WebSocket observation for live progress updates.
 *
 * ## State Machine
 *
 * The hook operates in these states:
 * 1. **Checking** - Polling REST API to find active scrapes (every 5s)
 * 2. **Observing** - WebSocket connected, receiving live progress updates
 * 3. **Idle** - No active scrapes, still polling to detect new ones
 *
 * ## Data Flow
 *
 * 1. On mount, polls `/scrape/runs/active` to find active scrape IDs
 * 2. If active scrape found, WebSocket receives progress messages
 * 3. Progress is tracked per-platform with phase transitions
 * 4. On scrape completion, resets to idle and resumes polling
 *
 * @example
 * ```typescript
 * import { useActiveScrapesObserver } from '@/features/dashboard/hooks/use-observe-scrape'
 *
 * function ScrapeProgressCard() {
 *   const {
 *     activeScrapeId,
 *     isObserving,
 *     progress,
 *     platformProgress,
 *     overallPhase,
 *   } = useActiveScrapesObserver()
 *
 *   if (!activeScrapeId) return <p>No active scrapes</p>
 *
 *   return (
 *     <div>
 *       <p>Scrape #{activeScrapeId}: {overallPhase}</p>
 *       {Array.from(platformProgress.entries()).map(([platform, p]) => (
 *         <div key={platform}>
 *           {platform}: {p.phase} ({p.current}/{p.total})
 *         </div>
 *       ))}
 *     </div>
 *   )
 * }
 * ```
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import {
  useWebSocketScrapeProgress,
  type PlatformProgress,
} from '@/hooks/use-websocket-scrape-progress'
import { api } from '@/lib/api'

/**
 * Scrape progress snapshot for a single update.
 *
 * @description Represents progress at a specific point in time, including
 * the current phase, item counts, and any status messages.
 */
export interface ScrapeProgress {
  /** Platform being scraped (e.g., 'betpawa', 'sportybet'), null for overall progress */
  platform: string | null
  /** Current scrape phase (e.g., 'fetching_events', 'scraping_odds', 'matching') */
  phase: string
  /** Current item number being processed */
  current: number
  /** Total items to process in this phase */
  total: number
  /** Number of events processed (populated in later phases) */
  events_count: number | null
  /** Human-readable status message */
  message: string | null
  /** ISO timestamp of this progress update */
  timestamp: string
}

/**
 * Observes active scrape runs via polling and WebSocket.
 *
 * @description This hook combines REST API polling with WebSocket observation
 * to provide real-time scrape progress. It automatically detects when a scrape
 * starts and connects to the WebSocket for live updates.
 *
 * ## Lifecycle
 *
 * 1. Polls `/scrape/runs/active` every 5 seconds to detect active scrapes
 * 2. When active scrape found, stores its ID and WebSocket receives updates
 * 3. On scrape completion (via onComplete callback), clears active ID
 * 4. Continues polling to detect the next scrape
 *
 * ## Return Values
 *
 * - `activeScrapeId`: ID of the currently running scrape, or null
 * - `isChecking`: True during initial check before first poll completes
 * - `isObserving`: True when actively receiving WebSocket updates
 * - `progress`: Latest progress message (overall)
 * - `platformProgress`: Map of platform -> progress for multi-platform scrapes
 * - `overallPhase`: Current phase name (e.g., 'scraping', 'matching')
 * - `stopChecking`: Function to stop the polling interval
 *
 * @returns Object with scrape observation state and controls
 *
 * @example
 * ```typescript
 * const {
 *   activeScrapeId,
 *   isObserving,
 *   platformProgress,
 *   overallPhase,
 *   error,
 *   reconnect,
 * } = useActiveScrapesObserver()
 *
 * // Show connection status
 * if (error) {
 *   return <Button onClick={reconnect}>Reconnect</Button>
 * }
 * ```
 */
export function useActiveScrapesObserver() {
  const [activeScrapeId, setActiveScrapeId] = useState<number | null>(null)
  const [isChecking, setIsChecking] = useState(true)
  const checkIntervalRef = useRef<number | null>(null)

  const checkForActiveScrapes = useCallback(async () => {
    try {
      const activeIds = await api.get<number[]>('/scrape/runs/active')
      if (activeIds.length > 0) {
        setActiveScrapeId(activeIds[0])
      } else {
        setActiveScrapeId(null)
      }
    } catch {
      console.debug('No active scrapes or endpoint not available')
      setActiveScrapeId(null)
    } finally {
      setIsChecking(false)
    }
  }, [])

  // Check initially and then every 5 seconds
  useEffect(() => {
    checkForActiveScrapes()

    checkIntervalRef.current = window.setInterval(checkForActiveScrapes, 5000)

    return () => {
      if (checkIntervalRef.current) {
        window.clearInterval(checkIntervalRef.current)
      }
    }
  }, [checkForActiveScrapes])

  // WebSocket transport for progress observation
  const ws = useWebSocketScrapeProgress({
    enabled: true,
    onComplete: () => {
      setActiveScrapeId(null)
    },
  })

  return {
    activeScrapeId,
    isChecking,
    isObserving: activeScrapeId !== null && ws.isConnected,
    progress: ws.currentProgress,
    platformProgress: ws.platformProgress as Map<string, PlatformProgress>,
    overallPhase: ws.overallPhase,
    error: ws.error,
    connectionState: ws.connectionState,
    reconnect: ws.reconnect,
    stopChecking: () => {
      if (checkIntervalRef.current) {
        window.clearInterval(checkIntervalRef.current)
        checkIntervalRef.current = null
      }
    },
  }
}
