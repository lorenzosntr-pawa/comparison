import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export interface UseMatchesParams {
  page?: number
  pageSize?: number
  minBookmakers?: number
  tournamentIds?: number[]
  kickoffFrom?: string
  kickoffTo?: string
  search?: string
  availability?: 'betpawa' | 'competitor'
}

export function useMatches(params: UseMatchesParams = {}) {
  const { page = 1, pageSize = 50, minBookmakers, tournamentIds, kickoffFrom, kickoffTo, search, availability } = params

  return useQuery({
    queryKey: ['matches', { page, pageSize, minBookmakers, tournamentIds, kickoffFrom, kickoffTo, search, availability }],
    queryFn: () =>
      api.getEvents({
        page,
        page_size: pageSize,
        min_bookmakers: minBookmakers,
        tournament_ids: tournamentIds,
        kickoff_from: kickoffFrom,
        kickoff_to: kickoffTo,
        search,
        availability,
      }),
    staleTime: 30000, // 30 seconds
    gcTime: 60000, // 60 seconds (formerly cacheTime)
    refetchInterval: 60000, // Poll every 60 seconds
  })
}
