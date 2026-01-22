import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export interface ScrapePhaseLog {
  id: number
  platform: string | null
  phase: string
  started_at: string
  ended_at: string | null
  events_processed: number | null
  message: string | null
}

export function usePhaseHistory(runId: number) {
  return useQuery({
    queryKey: ['scrape-run-phases', runId],
    queryFn: () => api.get<ScrapePhaseLog[]>(`/scrape/runs/${runId}/phases`),
    staleTime: 30_000, // Refresh every 30s
    enabled: !isNaN(runId),
  })
}
