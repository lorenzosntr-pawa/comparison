import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export interface Tournament {
  id: number
  name: string
}

/**
 * Fetch tournaments by getting events and extracting unique tournaments.
 * This is a workaround until a dedicated tournaments endpoint is added.
 */
export function useTournaments() {
  return useQuery({
    queryKey: ['tournaments'],
    queryFn: async () => {
      // Fetch a large batch of events to get tournament variety
      const response = await api.getEvents({ page_size: 100 })

      // Extract unique tournaments
      const tournamentsMap = new Map<number, Tournament>()
      for (const event of response.events) {
        if (!tournamentsMap.has(event.tournament_id)) {
          tournamentsMap.set(event.tournament_id, {
            id: event.tournament_id,
            name: event.tournament_name,
          })
        }
      }

      // Return sorted by name
      return Array.from(tournamentsMap.values()).sort((a, b) =>
        a.name.localeCompare(b.name)
      )
    },
    staleTime: 5 * 60 * 1000, // 5 minutes - tournaments don't change often
    gcTime: 10 * 60 * 1000, // 10 minutes
  })
}
