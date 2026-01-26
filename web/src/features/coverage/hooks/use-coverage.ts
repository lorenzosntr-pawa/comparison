import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function useCoverage(params?: { includeStarted?: boolean }) {
  const includeStarted = params?.includeStarted ?? false
  return useQuery({
    queryKey: ['coverage', { includeStarted }],
    queryFn: () => api.getCoverage({ includeStarted }),
    staleTime: 30000, // 30 seconds
    gcTime: 60000, // 60 seconds
    refetchInterval: 60000, // Poll every 60 seconds
  })
}

export interface UsePalimpsestEventsParams {
  availability?: 'betpawa-only' | 'competitor-only' | 'matched'
  platforms?: string[]
  sport_id?: number
  search?: string
  sort?: 'kickoff' | 'tournament'
  includeStarted?: boolean
}

export function usePalimpsestEvents(params: UsePalimpsestEventsParams = {}) {
  const { availability, platforms, sport_id, search, sort, includeStarted } = params

  return useQuery({
    queryKey: ['palimpsest-events', { availability, platforms, sport_id, search, sort, includeStarted }],
    queryFn: () =>
      api.getPalimpsestEvents({
        availability,
        platforms,
        sport_id,
        search,
        sort,
        include_started: includeStarted,
      }),
    staleTime: 30000, // 30 seconds
    gcTime: 60000, // 60 seconds
    refetchInterval: 60000, // Poll every 60 seconds
  })
}
