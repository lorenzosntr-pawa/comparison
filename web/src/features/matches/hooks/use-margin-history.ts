import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export interface UseMarginHistoryParams {
  eventId: number
  marketId: string
  bookmakerSlug: string
  fromTime?: string
  toTime?: string
  enabled?: boolean
}

export function useMarginHistory({
  eventId,
  marketId,
  bookmakerSlug,
  fromTime,
  toTime,
  enabled = true,
}: UseMarginHistoryParams) {
  return useQuery({
    queryKey: ['margin-history', eventId, marketId, bookmakerSlug, fromTime, toTime],
    queryFn: () =>
      api.getMarginHistory({
        eventId,
        marketId,
        bookmakerSlug,
        fromTime,
        toTime,
      }),
    enabled: enabled && !!eventId && !!marketId && !!bookmakerSlug,
    staleTime: 60000, // 1 minute
    gcTime: 300000, // 5 minutes
  })
}
