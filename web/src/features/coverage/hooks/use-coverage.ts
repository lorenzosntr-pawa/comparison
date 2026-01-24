import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function useCoverage() {
  return useQuery({
    queryKey: ['coverage'],
    queryFn: () => api.getCoverage(),
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
}

export function usePalimpsestEvents(params: UsePalimpsestEventsParams = {}) {
  const { availability, platforms, sport_id, search, sort } = params

  return useQuery({
    queryKey: ['palimpsest-events', { availability, platforms, sport_id, search, sort }],
    queryFn: () =>
      api.getPalimpsestEvents({
        availability,
        platforms,
        sport_id,
        search,
        sort,
      }),
    staleTime: 30000, // 30 seconds
    gcTime: 60000, // 60 seconds
    refetchInterval: 60000, // Poll every 60 seconds
  })
}
