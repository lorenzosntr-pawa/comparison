/**
 * Real-time risk alert subscription hook.
 *
 * @module use-risk-alert-updates
 * @description Subscribes to real-time alert updates via WebSocket and automatically
 * invalidates TanStack Query caches when new alerts are detected.
 */

import { useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { useWebSocket, type WebSocketMessage } from '@/hooks/use-websocket'

/** Data payload for risk_alert WebSocket messages */
export interface RiskAlertUpdateData {
  alert_count: number
  event_ids: number[]
  severities: string[]
}

export interface UseRiskAlertUpdatesOptions {
  enabled?: boolean
}

export interface UseRiskAlertUpdatesReturn {
  isConnected: boolean
  reconnect: () => void
}

/**
 * Hook for subscribing to real-time risk alert updates via WebSocket.
 *
 * Cache invalidation:
 * - ['alerts'] - refreshes all alert queries (list + stats)
 */
export function useRiskAlertUpdates(
  options: UseRiskAlertUpdatesOptions = {}
): UseRiskAlertUpdatesReturn {
  const { enabled = true } = options

  const queryClient = useQueryClient()

  const handleMessage = useCallback(
    (message: WebSocketMessage<RiskAlertUpdateData>) => {
      if (message.type !== 'risk_alert') return

      console.log('[useRiskAlertUpdates] New alerts:', message.data.alert_count)

      // Invalidate all alert queries (list views and stats)
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
    },
    [queryClient]
  )

  const handleReconnect = useCallback(() => {
    console.log('[useRiskAlertUpdates] Reconnected, invalidating queries')
    queryClient.invalidateQueries({ queryKey: ['alerts'] })
  }, [queryClient])

  const { state, reconnect } = useWebSocket<RiskAlertUpdateData>({
    topics: ['risk_alerts'],
    enabled,
    onMessage: handleMessage,
    onReconnect: handleReconnect,
  })

  return {
    isConnected: state === 'connected',
    reconnect,
  }
}
