import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export interface ScrapeRun {
  id: number
  status: string
  started_at: string
  completed_at: string | null
  events_scraped: number
  events_failed: number
  trigger: string | null
  platform_timings: Record<
    string,
    { duration_ms: number; events_count: number }
  > | null
}

export interface ScrapeStats {
  total_runs: number
  runs_24h: number
  avg_duration_seconds: number | null
}

export function useScrapeRuns(limit = 20, offset = 0) {
  return useQuery({
    queryKey: ['scrape-runs', limit, offset],
    queryFn: () =>
      api.get<ScrapeRun[]>(`/scrape/runs?limit=${limit}&offset=${offset}`),
    staleTime: 30_000,
  })
}

export function useScrapeStats() {
  return useQuery({
    queryKey: ['scrape-stats'],
    queryFn: () => api.get<ScrapeStats>('/scrape/stats'),
    staleTime: 60_000,
  })
}
