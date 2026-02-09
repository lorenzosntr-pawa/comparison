/**
 * Real-time odds update subscription hook.
 *
 * @module use-odds-updates
 * @description Subscribes to real-time odds updates via WebSocket and automatically
 * invalidates TanStack Query caches when new odds data is received. This enables
 * instant UI updates when bookmaker odds change, without waiting for polling intervals.
 *
 * Integration with TanStack Query:
 * - When an odds_update message is received, invalidates ['events'] for list views
 * - Also invalidates ['event', event_id] for the specific event's detail view
 * - On reconnection, invalidates queries to ensure data consistency
 *
 * @example
 * ```typescript
 * import { useOddsUpdates } from '@/hooks/use-odds-updates'
 *
 * function OddsComparisonPage() {
 *   // Enable real-time odds updates - cache invalidation is automatic
 *   const { isConnected, reconnect } = useOddsUpdates()
 *
 *   // Use standard TanStack Query for data fetching
 *   const { data: events } = useQuery({
 *     queryKey: ['events'],
 *     queryFn: () => api.getEvents(),
 *   })
 *
 *   return (
 *     <div>
 *       {!isConnected && <span>Reconnecting...</span>}
 *       {events?.map(event => <EventCard key={event.id} event={event} />)}
 *     </div>
 *   )
 * }
 * ```
 */

import { useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { useWebSocket, type WebSocketMessage } from './use-websocket'

/**
 * Data payload for odds_update WebSocket messages.
 *
 * @description Identifies which event and bookmaker have updated odds.
 */
export interface OddsUpdateData {
  /** Event ID that has new odds */
  event_id: number
  /** Bookmaker slug that provided the update */
  bookmaker: string
  /** ID of the new odds snapshot */
  snapshot_id: number
  /** ISO timestamp of the snapshot */
  snapshot_time: string
}

/**
 * Configuration options for the odds updates hook.
 */
export interface UseOddsUpdatesOptions {
  /** Whether to connect (default: true). Set to false to disable real-time updates. */
  enabled?: boolean
}

/**
 * Return value from the odds updates hook.
 */
export interface UseOddsUpdatesReturn {
  /** Whether WebSocket is connected */
  isConnected: boolean
  /** Manually trigger WebSocket reconnection */
  reconnect: () => void
}

/**
 * Hook for subscribing to real-time odds updates via WebSocket.
 *
 * @description Connects to the 'odds_updates' WebSocket topic and automatically
 * invalidates TanStack Query caches when new odds are received, ensuring the UI
 * always displays the latest odds data.
 *
 * Cache invalidation:
 * - ['events'] - refreshes list views (Odds Comparison page)
 * - ['event', event_id] - refreshes specific event detail view
 *
 * @param options - Configuration options
 * @returns Connection state and reconnection control
 */
export function useOddsUpdates(
  options: UseOddsUpdatesOptions = {}
): UseOddsUpdatesReturn {
  const { enabled = true } = options

  const queryClient = useQueryClient()

  // Handle incoming odds_update messages
  const handleMessage = useCallback(
    (message: WebSocketMessage<OddsUpdateData>) => {
      if (message.type !== 'odds_update') return

      const { event_id } = message.data

      // Invalidate the events list (for Odds Comparison page)
      queryClient.invalidateQueries({ queryKey: ['events'] })

      // Invalidate the specific event (for Event Details page)
      queryClient.invalidateQueries({ queryKey: ['event', event_id] })
    },
    [queryClient]
  )

  // Handle reconnection - invalidate queries to sync state
  const handleReconnect = useCallback(() => {
    console.log('[useOddsUpdates] Reconnected, invalidating queries')
    queryClient.invalidateQueries({ queryKey: ['events'] })
  }, [queryClient])

  // Connect to WebSocket with odds_updates topic
  const { state, reconnect } = useWebSocket<OddsUpdateData>({
    topics: ['odds_updates'],
    enabled,
    onMessage: handleMessage,
    onReconnect: handleReconnect,
  })

  return {
    isConnected: state === 'connected',
    reconnect,
  }
}
