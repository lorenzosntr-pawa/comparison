import { useQueries } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { OddsHistoryResponse } from '@/types/api'

export interface UseMultiOddsHistoryParams {
  eventId: number
  marketId: string
  bookmakerSlugs: string[]
  fromTime?: string
  toTime?: string
  enabled?: boolean
}

export interface MultiOddsHistoryData {
  [bookmakerSlug: string]: {
    history: OddsHistoryResponse['history']
    bookmakerName: string
  }
}

export function useMultiOddsHistory({
  eventId,
  marketId,
  bookmakerSlugs,
  fromTime,
  toTime,
  enabled = true,
}: UseMultiOddsHistoryParams) {
  const queries = useQueries({
    queries: bookmakerSlugs.map((bookmakerSlug) => ({
      queryKey: ['odds-history', eventId, marketId, bookmakerSlug, fromTime, toTime],
      queryFn: () =>
        api.getOddsHistory({
          eventId,
          marketId,
          bookmakerSlug,
          fromTime,
          toTime,
        }),
      enabled: enabled && !!eventId && !!marketId && bookmakerSlugs.length > 0,
      staleTime: 60000, // 1 minute
      gcTime: 300000, // 5 minutes
    })),
  })

  const isLoading = queries.some((q) => q.isLoading)
  const isError = queries.some((q) => q.isError)
  const error = queries.find((q) => q.error)?.error

  // Merge all results into a single object keyed by bookmaker
  const data: MultiOddsHistoryData | undefined = queries.every((q) => q.data)
    ? queries.reduce((acc, q, index) => {
        const bookmakerSlug = bookmakerSlugs[index]
        if (q.data) {
          acc[bookmakerSlug] = {
            history: q.data.history,
            bookmakerName: q.data.bookmaker_name,
          }
        }
        return acc
      }, {} as MultiOddsHistoryData)
    : undefined

  const refetch = () => {
    queries.forEach((q) => q.refetch())
  }

  return {
    data,
    isLoading,
    isError,
    error,
    refetch,
  }
}
