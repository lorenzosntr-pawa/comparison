/**
 * Hook for fetching margin history across multiple bookmakers simultaneously.
 *
 * @module use-multi-margin-history
 * @description Fetches historical margin data for a market from multiple bookmakers
 * in parallel. This enables side-by-side comparison charts showing how margins
 * differ between platforms over time.
 *
 * Uses TanStack Query's useQueries to run parallel requests, then merges
 * results into a single object keyed by bookmaker slug.
 *
 * @example
 * ```typescript
 * import { useMultiMarginHistory } from '@/features/matches/hooks/use-multi-margin-history'
 *
 * function MarginComparisonChart({ eventId }: { eventId: number }) {
 *   const { data, isLoading } = useMultiMarginHistory({
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
import type { MarginHistoryResponse } from '@/types/api'

/**
 * Parameters for fetching margin history from multiple bookmakers.
 *
 * @description Similar to UseMarginHistoryParams but accepts an array of
 * bookmaker slugs to fetch in parallel.
 */
export interface UseMultiMarginHistoryParams {
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
  /** Set to false to disable all queries (default: true) */
  enabled?: boolean
}

/**
 * Merged margin history data from multiple bookmakers.
 *
 * @description Object keyed by bookmaker slug, containing each bookmaker's
 * history array and display name.
 */
export interface MultiMarginHistoryData {
  [bookmakerSlug: string]: {
    /** Array of timestamped margin values */
    history: MarginHistoryResponse['history']
    /** Human-readable bookmaker name */
    bookmakerName: string
  }
}

/**
 * Fetches margin history from multiple bookmakers in parallel.
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
 * @param params - Query parameters including event, market, and bookmaker array
 * @returns Object with data, isLoading, isError, error, and refetch
 *
 * @example
 * ```typescript
 * const { data, isLoading, refetch } = useMultiMarginHistory({
 *   eventId: 12345,
 *   marketId: '3743',
 *   bookmakerSlugs: ['betpawa', 'sportybet'],
 * })
 *
 * // Access individual bookmaker data
 * const betpawaMargins = data?.betpawa.history
 * ```
 */
export function useMultiMarginHistory({
  eventId,
  marketId,
  bookmakerSlugs,
  fromTime,
  toTime,
  enabled = true,
}: UseMultiMarginHistoryParams) {
  const queries = useQueries({
    queries: bookmakerSlugs.map((bookmakerSlug) => ({
      queryKey: ['margin-history', eventId, marketId, bookmakerSlug, fromTime, toTime],
      queryFn: () =>
        api.getMarginHistory({
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
  const data: MultiMarginHistoryData | undefined = queries.every((q) => q.data)
    ? queries.reduce((acc, q, index) => {
        const bookmakerSlug = bookmakerSlugs[index]
        if (q.data) {
          acc[bookmakerSlug] = {
            history: q.data.history,
            bookmakerName: q.data.bookmaker_name,
          }
        }
        return acc
      }, {} as MultiMarginHistoryData)
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
