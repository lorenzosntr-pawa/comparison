import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export interface ScrapeError {
  id: number
  error_type: string
  error_message: string
  occurred_at: string
  platform: string | null
}

export interface ScrapeRunDetail {
  scrape_run_id: number
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
  errors: ScrapeError[] | null
}

interface UseScrapeRunDetailOptions {
  /** Enable polling when scrape is running (default: false) */
  pollWhileRunning?: boolean
}

export function useScrapeRunDetail(id: number, options?: UseScrapeRunDetailOptions) {
  const { pollWhileRunning = false } = options ?? {}

  return useQuery({
    queryKey: ['scrape-run', id],
    queryFn: () => api.get<ScrapeRunDetail>(`/scrape/${id}`),
    staleTime: 60_000,
    enabled: !isNaN(id),
    // Poll every 5 seconds when running (if enabled)
    refetchInterval: (query) => {
      if (!pollWhileRunning) return false
      const data = query.state.data
      return data?.status === 'running' ? 5000 : false
    },
  })
}
