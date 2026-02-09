import { useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { useWebSocket, type WebSocketMessage } from './use-websocket'

/**
 * Data shape for odds_update WebSocket messages
 * (matches backend broadcast format)
 */
export interface OddsUpdateData {
  event_id: number
  bookmaker: string
  snapshot_id: number
  snapshot_time: string
}

/**
 * Options for useOddsUpdates hook
 */
export interface UseOddsUpdatesOptions {
  /** Whether to connect (default: true) */
  enabled?: boolean
}

/**
 * Return type for useOddsUpdates hook
 */
export interface UseOddsUpdatesReturn {
  /** Whether WebSocket is connected */
  isConnected: boolean
}

/**
 * Hook that subscribes to real-time odds updates via WebSocket.
 *
 * Automatically invalidates TanStack Query caches when odds change,
 * ensuring the UI shows fresh data immediately without waiting for
 * the polling interval.
 *
 * Invalidates:
 * - ['events'] - for list views (Odds Comparison page)
 * - ['event', event_id] - for detail view (Event Details page)
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

  // Connect to WebSocket with odds_updates topic
  const { state } = useWebSocket<OddsUpdateData>({
    topics: ['odds_updates'],
    enabled,
    onMessage: handleMessage,
  })

  return {
    isConnected: state === 'connected',
  }
}
