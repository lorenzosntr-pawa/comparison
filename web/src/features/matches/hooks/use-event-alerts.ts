/**
 * Hooks for fetching alerts for a specific event.
 *
 * @module use-event-alerts
 * @description TanStack Query hooks for event-specific alert data.
 */

import { useQuery, useQueries } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { RiskAlert, RiskAlertsResponse } from '@/features/risk-monitoring/hooks/use-alerts'

/** Summary of alerts for an event */
export interface EventAlertSummary {
  count: number
  maxSeverity: 'warning' | 'elevated' | 'critical' | null
  hasAlerts: boolean
}

/**
 * Fetch alerts for a specific event.
 *
 * @param eventId - The event ID to fetch alerts for
 * @returns Query result with alerts for the event
 */
export function useEventAlerts(eventId: number | undefined) {
  return useQuery({
    queryKey: ['events', eventId, 'alerts'],
    queryFn: async (): Promise<RiskAlertsResponse> => {
      return api.get<RiskAlertsResponse>(`/events/${eventId}/alerts`)
    },
    enabled: !!eventId,
    staleTime: 1000 * 30, // 30 seconds
  })
}

/**
 * Get alert summary for an event (count, maxSeverity, hasAlerts).
 *
 * @param eventId - The event ID to get summary for
 * @returns Summary with count, maxSeverity, and hasAlerts
 */
export function useEventAlertSummary(eventId: number | undefined): {
  data: EventAlertSummary | undefined
  isPending: boolean
  error: Error | null
} {
  const query = useEventAlerts(eventId)

  const summary = query.data
    ? computeAlertSummary(query.data.alerts)
    : undefined

  return {
    data: summary,
    isPending: query.isPending,
    error: query.error,
  }
}

/**
 * Compute alert summary from alerts array.
 * Severity priority: critical > elevated > warning
 */
function computeAlertSummary(alerts: RiskAlert[]): EventAlertSummary {
  if (alerts.length === 0) {
    return { count: 0, maxSeverity: null, hasAlerts: false }
  }

  const severityPriority = { critical: 3, elevated: 2, warning: 1 }
  let maxSeverity: 'warning' | 'elevated' | 'critical' = 'warning'

  for (const alert of alerts) {
    if (severityPriority[alert.severity] > severityPriority[maxSeverity]) {
      maxSeverity = alert.severity
    }
  }

  return {
    count: alerts.length,
    maxSeverity,
    hasAlerts: true,
  }
}

/** Result type for batch event alert counts */
export interface EventAlertCounts {
  [eventId: number]: EventAlertSummary
}

/**
 * Batch fetch alert summaries for multiple events.
 * Uses useQueries for efficient parallel fetching.
 *
 * @param eventIds - Array of event IDs to fetch alerts for
 * @returns Record mapping eventId to alert summary
 */
export function useEventAlertCounts(eventIds: number[]): {
  data: EventAlertCounts
  isPending: boolean
} {
  const queries = useQueries({
    queries: eventIds.map((eventId) => ({
      queryKey: ['events', eventId, 'alerts'],
      queryFn: async (): Promise<RiskAlertsResponse> => {
        return api.get<RiskAlertsResponse>(`/events/${eventId}/alerts`)
      },
      staleTime: 1000 * 30, // 30 seconds
      enabled: eventIds.length > 0,
    })),
  })

  const isPending = queries.some((q) => q.isPending)

  const data: EventAlertCounts = {}
  queries.forEach((query, index) => {
    const eventId = eventIds[index]
    if (query.data) {
      data[eventId] = computeAlertSummary(query.data.alerts)
    }
  })

  return { data, isPending }
}
