import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export interface UseMatchesParams {
  page?: number
  pageSize?: number
  minBookmakers?: number
  tournamentId?: number
  kickoffFrom?: string
  kickoffTo?: string
}

export function useMatches(params: UseMatchesParams = {}) {
  const { page = 1, pageSize = 50, minBookmakers, tournamentId, kickoffFrom, kickoffTo } = params

  return useQuery({
    queryKey: ['matches', { page, pageSize, minBookmakers, tournamentId, kickoffFrom, kickoffTo }],
    queryFn: () =>
      api.getEvents({
        page,
        page_size: pageSize,
        min_bookmakers: minBookmakers,
        tournament_id: tournamentId,
        kickoff_from: kickoffFrom,
        kickoff_to: kickoffTo,
      }),
    staleTime: 30000, // 30 seconds
    gcTime: 60000, // 60 seconds (formerly cacheTime)
    refetchInterval: 60000, // Poll every 60 seconds
  })
}
