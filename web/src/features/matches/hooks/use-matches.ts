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
  /** ISO timestamp - only show matches kicking off after this time */
  kickoffFrom?: string
  /** ISO timestamp - only show matches kicking off before this time */
  kickoffTo?: string
  /** Free-text search (matches team names, tournament) */
  search?: string
  /** Filter by platform availability: 'betpawa' or 'competitor' */
  availability?: 'betpawa' | 'competitor'
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
  const { page = 1, pageSize = 50, minBookmakers, tournamentIds, kickoffFrom, kickoffTo, search, availability } = params

  return useQuery({
    queryKey: ['matches', { page, pageSize, minBookmakers, tournamentIds, kickoffFrom, kickoffTo, search, availability }],
    queryFn: () =>
      api.getEvents({
        page,
        page_size: pageSize,
        min_bookmakers: minBookmakers,
        tournament_ids: tournamentIds,
        kickoff_from: kickoffFrom,
        kickoff_to: kickoffTo,
        search,
        availability,
      }),
    staleTime: 30000, // 30 seconds
    gcTime: 60000, // 60 seconds (formerly cacheTime)
    refetchInterval: 60000, // Poll every 60 seconds
  })
}
