/**
 * Hook for fetching a paginated list of matches.
 *
 * @module use-matches
 * @description Provides the main data source for the matches list view.
 * Supports filtering by bookmaker count, tournament, kickoff time, search
 * term, and availability status.
 *
 * @example
 * ```typescript
 * import { useMatches } from '@/features/matches/hooks/use-matches'
 *
 * function MatchesList() {
 *   const { data, isPending, error } = useMatches({
 *     page: 1,
 *     pageSize: 50,
 *     minBookmakers: 2, // Only show comparable matches
 *     search: 'Manchester',
 *   })
 *
 *   if (isPending) return <Spinner />
 *
 *   return (
 *     <div>
 *       <p>Found {data.total} matches</p>
 *       {data.items.map(match => <MatchRow key={match.id} match={match} />)}
 *     </div>
 *   )
 * }
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

/**
 * Parameters for filtering and paginating the matches list.
 *
 * @description Configuration object for the useMatches hook to control
 * pagination and filtering of the events list.
 */
export interface UseMatchesParams {
  /** Page number for pagination (1-indexed, default: 1) */
  page?: number
  /** Number of items per page (default: 50) */
  pageSize?: number
  /** Minimum number of bookmakers required (2+ for comparison) */
  minBookmakers?: number
  /** Filter by specific tournament IDs */
  tournamentIds?: number[]
  /** Filter by country/region names */
  countries?: string[]
  /** ISO timestamp - only show matches kicking off after this time */
  kickoffFrom?: string
  /** ISO timestamp - only show matches kicking off before this time */
  kickoffTo?: string
  /** Free-text search (matches team names, tournament) */
  search?: string
  /** Filter by platform availability: 'betpawa', 'competitor', or 'alerts' */
  availability?: 'betpawa' | 'competitor' | 'alerts'
}

/**
 * Fetches a paginated list of matches with filtering.
 *
 * @description The primary hook for the matches list view. Returns paginated
 * event data with inline odds from all bookmakers. Polls every 60 seconds
 * to keep odds current.
 *
 * ## Filtering
 * - `minBookmakers: 2` returns only "comparable" matches (available on 2+ platforms)
 * - `tournamentIds` filters to specific competitions
 * - `kickoffFrom/To` creates a time window
 * - `search` performs fuzzy matching on team/tournament names
 *
 * @param params - Filter and pagination options
 * @returns TanStack Query result with MatchedEventList containing items array and total count
 *
 * @example
 * ```typescript
 * // Fetch today's comparable Premier League matches
 * const { data } = useMatches({
 *   minBookmakers: 2,
 *   tournamentIds: [17], // Premier League
 *   kickoffFrom: new Date().toISOString(),
 *   kickoffTo: endOfDay(new Date()).toISOString(),
 * })
 * ```
 */
export function useMatches(params: UseMatchesParams = {}) {
  const { page = 1, pageSize = 50, minBookmakers, tournamentIds, countries, kickoffFrom, kickoffTo, search, availability } = params

  // Use availability as a top-level key part to ensure different modes have different cache entries
  const queryKey = ['matches', availability ?? 'betpawa', page, pageSize, minBookmakers, search ?? ''] as const
  console.log('[DEBUG] useMatches - availability:', availability, '- full queryKey:', queryKey)

  const query = useQuery({
    queryKey,
    queryFn: async () => {
      console.log('[DEBUG] >>> queryFn STARTING for availability:', availability)
      try {
        const result = await api.getEvents({
          page,
          page_size: pageSize,
          min_bookmakers: minBookmakers,
          tournament_ids: tournamentIds,
          countries,
          kickoff_from: kickoffFrom,
          kickoff_to: kickoffTo,
          search,
          availability,
        })
        console.log('[DEBUG] >>> queryFn SUCCESS, got', result?.events?.length ?? 0, 'events')
        return result
      } catch (err) {
        console.error('[DEBUG] >>> queryFn ERROR:', err)
        throw err
      }
    },
    staleTime: 30000, // 30 seconds
    gcTime: 60000, // 60 seconds (formerly cacheTime)
    refetchInterval: 60000, // Poll every 60 seconds
  })

  // Log query state on every call
  console.log('[DEBUG] useMatches - query state:', {
    isPending: query.isPending,
    isFetching: query.isFetching,
    isStale: query.isStale,
    status: query.status,
    fetchStatus: query.fetchStatus,
  })

  return query
}

/**
 * Fetches the count of events with availability alerts.
 *
 * @description Returns the number of events that have at least one market
 * with unavailable_at set (indicating the market was previously available
 * but is now unavailable).
 *
 * @returns TanStack Query result with count of events with alerts
 */
export function useAlertsCount() {
  return useQuery({
    queryKey: ['alertsCount'],
    queryFn: () => api.getAlertsCount(),
    staleTime: 30000, // 30 seconds
    gcTime: 60000, // 60 seconds
    refetchInterval: 60000, // Poll every 60 seconds
  })
}
