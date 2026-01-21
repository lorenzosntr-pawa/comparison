import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export interface Tournament {
  id: number
  name: string
  country: string | null
}

/**
 * Fetch tournaments from the dedicated tournaments endpoint.
 */
export function useTournaments() {
  return useQuery({
    queryKey: ['tournaments'],
    queryFn: () => api.getTournaments(),
    staleTime: 5 * 60 * 1000, // 5 minutes - tournaments don't change often
    gcTime: 10 * 60 * 1000, // 10 minutes
  })
}
