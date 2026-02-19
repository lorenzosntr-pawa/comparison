/**
 * Hooks for fetching and managing risk alerts.
 *
 * @module use-alerts
 * @description TanStack Query hooks for risk alert APIs.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

/** Single risk alert record */
export interface RiskAlert {
  id: number
  eventId: number
  eventName: string | null
  homeTeam: string | null
  awayTeam: string | null
  bookmakerSlug: string
  marketId: string
  marketName: string
  line: number | null
  outcomeName: string | null
  alertType: 'price_change' | 'direction_disagreement' | 'availability'
  severity: 'warning' | 'elevated' | 'critical'
  changePercent: number
  oldValue: number | null
  newValue: number | null
  competitorDirection: string | null
  detectedAt: string
  acknowledgedAt: string | null
  status: 'new' | 'acknowledged' | 'past'
  eventKickoff: string
}

/** Paginated alerts response with status counts */
export interface RiskAlertsResponse {
  alerts: RiskAlert[]
  total: number
  newCount: number
  acknowledgedCount: number
  pastCount: number
}

/** Alert statistics grouped by status, severity, and type */
export interface AlertStats {
  total: number
  byStatus: Record<string, number>
  bySeverity: Record<string, number>
  byType: Record<string, number>
}

/** Filters for alert queries */
export interface AlertFilters {
  status?: 'new' | 'acknowledged' | 'past' | null
  severity?: 'warning' | 'elevated' | 'critical' | null
  alertType?: 'price_change' | 'direction_disagreement' | 'availability' | null
  limit?: number
  offset?: number
}

/**
 * Fetch paginated risk alerts with filters.
 */
export function useAlerts(filters: AlertFilters = {}) {
  return useQuery({
    queryKey: ['alerts', filters],
    queryFn: async (): Promise<RiskAlertsResponse> => {
      const params = new URLSearchParams()
      if (filters.status) params.set('status', filters.status)
      if (filters.severity) params.set('severity', filters.severity)
      if (filters.alertType) params.set('alert_type', filters.alertType)
      if (filters.limit) params.set('limit', filters.limit.toString())
      if (filters.offset) params.set('offset', filters.offset.toString())
      const query = params.toString()
      return api.get<RiskAlertsResponse>(`/alerts${query ? `?${query}` : ''}`)
    },
    staleTime: 1000 * 30, // 30 seconds
  })
}

/**
 * Fetch alert statistics grouped by status, severity, and type.
 */
export function useAlertStats() {
  return useQuery({
    queryKey: ['alerts', 'stats'],
    queryFn: async (): Promise<AlertStats> => {
      return api.get<AlertStats>('/alerts/stats')
    },
    staleTime: 1000 * 60, // 1 minute
  })
}

/** Acknowledge request body */
interface AcknowledgeRequest {
  acknowledged: boolean
}

/**
 * Mutation to acknowledge or unacknowledge an alert.
 */
export function useAcknowledgeAlert() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      alertId,
      acknowledged,
    }: {
      alertId: number
      acknowledged: boolean
    }): Promise<RiskAlert> => {
      return api.patch<RiskAlert>(`/alerts/${alertId}`, {
        acknowledged,
      } as AcknowledgeRequest)
    },
    onSuccess: () => {
      // Invalidate alerts queries to refresh list and counts
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
    },
  })
}
