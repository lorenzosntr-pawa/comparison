import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { DailyMetric, PlatformMetric } from '../components'

export interface ScrapeAnalyticsResponse {
  daily_metrics: DailyMetric[]
  platform_metrics: PlatformMetric[]
  period_start: string
  period_end: string
}

export interface AnalyticsParams {
  days?: number
}

export function useAnalytics(params?: AnalyticsParams) {
  const days = params?.days ?? 14

  return useQuery({
    queryKey: ['scrape-analytics', days],
    queryFn: () =>
      api.get<ScrapeAnalyticsResponse>(`/scrape/analytics?days=${days}`),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}
