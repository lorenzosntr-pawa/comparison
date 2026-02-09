/**
 * Hook for fetching odds history for a single bookmaker.
 *
 * @module use-odds-history
 * @description Provides historical odds data for a specific event/market/bookmaker
 * combination. Shows how odds changed over time, useful for charts displaying
 * price movements and identifying value opportunities.
 *
 * For comparing odds across multiple bookmakers, see use-multi-odds-history.
 *
 * @example
 * ```typescript
 * import { useOddsHistory } from '@/features/matches/hooks/use-odds-history'
 *
 * function OddsChart({ eventId }: { eventId: number }) {
 *   const { data, isPending } = useOddsHistory({
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
 * Parameters for fetching odds history.
 *
 * @description Specifies which event, market, and bookmaker to fetch odds
 * history for, with optional time range filtering.
 */
export interface UseOddsHistoryParams {
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
 * Fetches historical odds data for a single bookmaker.
 *
 * @description Returns timestamped odds snapshots showing how prices changed
 * over time for all outcomes in a market. Useful for single-bookmaker charts
 * showing odds movement leading up to an event.
 *
 * The query is disabled if any required parameter (eventId, marketId, bookmakerSlug)
 * is missing. Uses a 1-minute stale time since historical data changes slowly.
 *
 * @param params - Query parameters including event, market, bookmaker, and time range
 * @returns TanStack Query result with OddsHistoryResponse containing history array
 *
 * @example
 * ```typescript
 * const { data, isPending, error } = useOddsHistory({
 *   eventId: 12345,
 *   marketId: '3743',
 *   bookmakerSlug: 'betpawa',
 *   fromTime: '2024-01-01T00:00:00Z',
 * })
 *
 * // data?.history = [{ timestamp: '...', outcomes: [...] }, ...]
 * ```
 */
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
