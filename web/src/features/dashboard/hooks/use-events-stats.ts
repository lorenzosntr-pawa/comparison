import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function useEventsStats() {
  // Get events with at least 2 bookmakers (matched)
  const matchedQuery = useQuery({
    queryKey: ['events', 'stats', 'matched'],
    queryFn: () => api.getEvents({ page_size: 1, min_bookmakers: 2 }),
    refetchInterval: 60000, // Poll every 60s
  })

  // Get all events
  const totalQuery = useQuery({
    queryKey: ['events', 'stats', 'total'],
    queryFn: () => api.getEvents({ page_size: 1 }),
    refetchInterval: 60000,
  })

  return {
    totalEvents: totalQuery.data?.total ?? 0,
    matchedEvents: matchedQuery.data?.total ?? 0,
    isPending: matchedQuery.isPending || totalQuery.isPending,
    error: matchedQuery.error || totalQuery.error,
  }
}
