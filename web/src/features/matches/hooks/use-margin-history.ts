/**
 * Hook for fetching margin history for a single bookmaker.
 *
 * @module use-margin-history
 * @description Provides historical margin data for a specific event/market/bookmaker
 * combination. Margins show the bookmaker's profit percentage built into the odds,
 * useful for identifying value and comparing bookmaker competitiveness.
 *
 * For comparing margins across multiple bookmakers, see use-multi-margin-history.
 *
 * @example
 * ```typescript
 * import { useMarginHistory } from '@/features/matches/hooks/use-margin-history'
 *
 * function MarginChart({ eventId }: { eventId: number }) {
 *   const { data, isPending } = useMarginHistory({
 *     eventId,
 *     marketId: '3743', // 1X2
 *     bookmakerSlug: 'betpawa',
 *   })
 *
 *   if (isPending) return <Spinner />
 *
 *   return <LineChart data={data.history} />
 * }
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

/**
 * Parameters for fetching margin history.
 *
 * @description Specifies which event, market, and bookmaker to fetch margin
 * history for, with optional time range filtering.
 */
export interface UseMarginHistoryParams {
  /** Event ID to fetch history for */
  eventId: number
  /** Market ID (e.g., '3743' for 1X2) */
  marketId: string
  /** Bookmaker identifier (e.g., 'betpawa', 'sportybet') */
  bookmakerSlug: string
  /** ISO timestamp for start of time range (optional) */
  fromTime?: string
  /** ISO timestamp for end of time range (optional) */
  toTime?: string
  /** Set to false to disable the query (default: true) */
  enabled?: boolean
}

/**
 * Fetches historical margin data for a single bookmaker.
 *
 * @description Returns timestamped margin values showing how the bookmaker's
 * profit percentage changed over time for a specific market. Useful for
 * charts showing margin trends leading up to an event.
 *
 * The query is disabled if any required parameter (eventId, marketId, bookmakerSlug)
 * is missing. Uses a 1-minute stale time since historical data changes slowly.
 *
 * @param params - Query parameters including event, market, bookmaker, and time range
 * @returns TanStack Query result with MarginHistoryResponse containing history array
 *
 * @example
 * ```typescript
 * const { data, isPending, error } = useMarginHistory({
 *   eventId: 12345,
 *   marketId: '3743',
 *   bookmakerSlug: 'betpawa',
 *   fromTime: '2024-01-01T00:00:00Z',
 * })
 *
 * // data?.history = [{ timestamp: '...', margin: 5.2 }, ...]
 * ```
 */
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
