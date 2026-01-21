import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function useMatchDetail(eventId: number | undefined) {
  return useQuery({
    queryKey: ['match-detail', eventId],
    queryFn: () => api.getEventDetail(eventId!),
    enabled: eventId !== undefined && !isNaN(eventId),
    staleTime: 30000, // 30 seconds
    gcTime: 60000, // 60 seconds
    refetchInterval: 60000, // Poll every 60 seconds
  })
}
