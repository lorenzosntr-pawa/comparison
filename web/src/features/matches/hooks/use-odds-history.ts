import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export interface UseOddsHistoryParams {
  eventId: number
  marketId: string
  bookmakerSlug: string
  fromTime?: string
  toTime?: string
  enabled?: boolean
}

export function useOddsHistory({
  eventId,
  marketId,
  bookmakerSlug,
  fromTime,
  toTime,
  enabled = true,
}: UseOddsHistoryParams) {
  return useQuery({
    queryKey: ['odds-history', eventId, marketId, bookmakerSlug, fromTime, toTime],
    queryFn: () =>
      api.getOddsHistory({
        eventId,
        marketId,
        bookmakerSlug,
        fromTime,
        toTime,
      }),
    enabled: enabled && !!eventId && !!marketId && !!bookmakerSlug,
    staleTime: 60000, // 1 minute - historical data changes slowly
    gcTime: 300000, // 5 minutes
  })
}
