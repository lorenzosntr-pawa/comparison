/**
 * Hook for fetching odds history across multiple bookmakers simultaneously.
 *
 * @module use-multi-odds-history
 * @description Fetches historical odds data for a market from multiple bookmakers
 * in parallel. This powers comparison charts showing how odds movements differ
 * between platforms over time - essential for identifying value bets.
 *
 * Uses TanStack Query's useQueries to run parallel requests, then merges
 * results into a single object keyed by bookmaker slug.
 *
 * @example
 * ```typescript
 * import { useMultiOddsHistory } from '@/features/matches/hooks/use-multi-odds-history'
 *
 * function OddsComparisonChart({ eventId }: { eventId: number }) {
 *   const { data, isLoading } = useMultiOddsHistory({
 *     eventId,
 *     marketId: '3743',
 *     bookmakerSlugs: ['betpawa', 'sportybet', 'betway'],
 *   })
 *
 *   if (isLoading) return <Spinner />
 *
 *   // data = { betpawa: { history, bookmakerName }, sportybet: { ... }, ... }
 *   return <MultiLineChart data={data} />
 * }
 * ```
 */

import { useQueries } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { OddsHistoryResponse } from '@/types/api'

/**
 * Parameters for fetching odds history from multiple bookmakers.
 *
 * @description Similar to UseOddsHistoryParams but accepts an array of
 * bookmaker slugs to fetch in parallel.
 */
export interface UseMultiOddsHistoryParams {
  /** Event ID to fetch history for */
  eventId: number
  /** Market ID (e.g., '3743' for 1X2) */
  marketId: string
  /** Array of bookmaker identifiers to compare */
  bookmakerSlugs: string[]
  /** ISO timestamp for start of time range (optional) */
  fromTime?: string
  /** ISO timestamp for end of time range (optional) */
  toTime?: string
  /** Line value for specifier markets (e.g., 2.5 for Over/Under) */
  line?: number | null
  /** Set to false to disable all queries (default: true) */
  enabled?: boolean
}

/**
 * Merged odds history data from multiple bookmakers.
 *
 * @description Object keyed by bookmaker slug, containing each bookmaker's
 * history array and display name.
 */
export interface MultiOddsHistoryData {
  [bookmakerSlug: string]: {
    /** Array of timestamped odds snapshots for all outcomes */
    history: OddsHistoryResponse['history']
    /** Human-readable bookmaker name */
    bookmakerName: string
  }
}

/**
 * Fetches odds history from multiple bookmakers in parallel.
 *
 * @description Uses TanStack Query's useQueries to fire parallel requests
 * for each bookmaker, then merges results into a single data object.
 * Returns combined loading/error state across all queries.
 *
 * ## Query Behavior
 * - Runs one query per bookmaker in bookmakerSlugs array
 * - Query disabled if eventId, marketId, or bookmakerSlugs is empty
 * - Returns data only when ALL queries complete successfully
 * - Uses 1-minute stale time (historical data changes slowly)
 *
 * ## Use Cases
 * - Multi-line charts comparing odds across bookmakers
 * - Identifying which bookmaker moved odds first
 * - Spotting arbitrage opportunities from odds divergence
 *
 * @param params - Query parameters including event, market, and bookmaker array
 * @returns Object with data, isLoading, isError, error, and refetch
 *
 * @example
 * ```typescript
 * const { data, isLoading, refetch } = useMultiOddsHistory({
 *   eventId: 12345,
 *   marketId: '3743',
 *   bookmakerSlugs: ['betpawa', 'sportybet'],
 * })
 *
 * // Access individual bookmaker odds
 * const betpawaOdds = data?.betpawa.history
 * ```
 */
export function useMultiOddsHistory({
  eventId,
  marketId,
  bookmakerSlugs,
  fromTime,
  toTime,
  line,
  enabled = true,
}: UseMultiOddsHistoryParams) {
  const queries = useQueries({
    queries: bookmakerSlugs.map((bookmakerSlug) => ({
      queryKey: ['odds-history', eventId, marketId, bookmakerSlug, fromTime, toTime, line],
      queryFn: () =>
        api.getOddsHistory({
          eventId,
          marketId,
          bookmakerSlug,
          fromTime,
          toTime,
          line,
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
