/**
 * Hook for fetching scrape analytics and metrics.
 *
 * @module use-analytics
 * @description Provides aggregated scraping metrics over a configurable time period.
 * Returns daily trends and per-platform performance data, useful for monitoring
 * scraper health and identifying performance patterns.
 *
 * @example
 * ```typescript
 * import { useAnalytics } from '@/features/scrape-runs/hooks/use-analytics'
 *
 * function AnalyticsDashboard() {
 *   const { data, isPending } = useAnalytics({ days: 14 })
 *
 *   if (isPending) return <Spinner />
 *
 *   return (
 *     <div>
 *       <DailyChart data={data.daily_metrics} />
 *       <PlatformTable data={data.platform_metrics} />
 *     </div>
 *   )
 * }
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { DailyMetric, PlatformMetric } from '../components'

/**
 * Response from the scrape analytics endpoint.
 *
 * @description Contains daily trends and platform-level metrics for the requested period.
 */
export interface ScrapeAnalyticsResponse {
  /** Array of daily aggregated metrics (success rate, event counts, etc.) */
  daily_metrics: DailyMetric[]
  /** Array of per-platform metrics (timing, success rate by platform) */
  platform_metrics: PlatformMetric[]
  /** ISO timestamp for start of analysis period */
  period_start: string
  /** ISO timestamp for end of analysis period */
  period_end: string
}

/**
 * Parameters for configuring the analytics query.
 */
export interface AnalyticsParams {
  /** Number of days to analyze (default: 14) */
  days?: number
}

/**
 * Fetches scrape analytics for the specified period.
 *
 * @description Returns aggregated metrics showing scraper performance over time.
 * Includes daily trends (useful for charts) and platform-level breakdowns
 * (useful for identifying platform-specific issues).
 *
 * Uses a 5-minute stale time since analytics data changes slowly.
 *
 * @param params - Optional configuration with days parameter
 * @returns TanStack Query result with ScrapeAnalyticsResponse
 *
 * @example
 * ```typescript
 * // Get last 7 days of metrics
 * const { data } = useAnalytics({ days: 7 })
 *
 * // Calculate overall success rate
 * const totalSuccess = data?.daily_metrics.reduce((sum, d) => sum + d.success_count, 0)
 * const totalRuns = data?.daily_metrics.reduce((sum, d) => sum + d.total_runs, 0)
 * const successRate = totalSuccess / totalRuns * 100
 * ```
 */
export function useAnalytics(params?: AnalyticsParams) {
  const days = params?.days ?? 14

  return useQuery({
    queryKey: ['scrape-analytics', days],
    queryFn: () =>
      api.get<ScrapeAnalyticsResponse>(`/scrape/analytics?days=${days}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}
