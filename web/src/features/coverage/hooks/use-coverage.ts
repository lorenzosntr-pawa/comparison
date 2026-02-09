/**
 * Hooks for fetching palimpsest coverage data.
 *
 * @module use-coverage
 * @description Provides TanStack Query hooks for fetching coverage statistics and
 * palimpsest event lists. Coverage data shows how well betpawa's event catalog
 * overlaps with competitor platforms, helping identify gaps in coverage.
 *
 * @example
 * ```typescript
 * import { useCoverage, usePalimpsestEvents } from '@/features/coverage/hooks/use-coverage'
 *
 * function CoverageOverview() {
 *   const { data: stats } = useCoverage()
 *   const { data: events } = usePalimpsestEvents({ availability: 'competitor-only' })
 *
 *   return (
 *     <div>
 *       <p>Matched: {stats?.matched_count}</p>
 *       <p>Gap events: {events?.events.length}</p>
 *     </div>
 *   )
 * }
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

/**
 * Fetches palimpsest coverage statistics.
 *
 * @description Returns aggregate counts of how many events are matched between
 * betpawa and competitors, vs. only available on one platform. Useful for
 * displaying high-level coverage metrics on dashboards.
 *
 * @param params - Optional configuration
 * @param params.includeStarted - If true, include events that have already kicked off (default: false)
 * @returns TanStack Query result containing CoverageStats with match/gap counts
 *
 * @example
 * ```typescript
 * const { data, isPending, error } = useCoverage({ includeStarted: true })
 * // data?.betpawa_only_count, data?.competitor_only_count, data?.matched_count
 * ```
 */
export function useCoverage(params?: { includeStarted?: boolean }) {
  const includeStarted = params?.includeStarted ?? false
  return useQuery({
    queryKey: ['coverage', { includeStarted }],
    queryFn: () => api.getCoverage({ includeStarted }),
    staleTime: 30000, // 30 seconds
    gcTime: 60000, // 60 seconds
    refetchInterval: 60000, // Poll every 60 seconds
  })
}

/**
 * Parameters for filtering and sorting palimpsest events.
 *
 * @description Configuration object for the usePalimpsestEvents hook to filter
 * the events list by availability status, platform, sport, and search terms.
 */
export interface UsePalimpsestEventsParams {
  /** Filter by coverage status: 'betpawa-only', 'competitor-only', or 'matched' */
  availability?: 'betpawa-only' | 'competitor-only' | 'matched'
  /** Filter to only include events from specific platforms */
  platforms?: string[]
  /** Filter by sport ID */
  sport_id?: number
  /** Search term to filter events by name */
  search?: string
  /** Sort order: 'kickoff' (by start time) or 'tournament' (grouped by competition) */
  sort?: 'kickoff' | 'tournament'
  /** Include events that have already started */
  includeStarted?: boolean
}

/**
 * Fetches filtered list of palimpsest events.
 *
 * @description Returns a paginated list of events from the palimpsest (master event catalog)
 * with detailed coverage information. Use this to browse events and identify coverage gaps
 * between betpawa and competitor platforms.
 *
 * @param params - Filter and sort configuration
 * @returns TanStack Query result with PalimpsestEventsResponse containing events array
 *
 * @example
 * ```typescript
 * // Find events only available on competitors (coverage gaps)
 * const { data } = usePalimpsestEvents({
 *   availability: 'competitor-only',
 *   sort: 'kickoff',
 * })
 *
 * // Search for specific matches
 * const { data } = usePalimpsestEvents({ search: 'Manchester United' })
 * ```
 */
export function usePalimpsestEvents(params: UsePalimpsestEventsParams = {}) {
  const { availability, platforms, sport_id, search, sort, includeStarted } = params

  return useQuery({
    queryKey: ['palimpsest-events', { availability, platforms, sport_id, search, sort, includeStarted }],
    queryFn: () =>
      api.getPalimpsestEvents({
        availability,
        platforms,
        sport_id,
        search,
        sort,
        include_started: includeStarted,
      }),
    staleTime: 30000, // 30 seconds
    gcTime: 60000, // 60 seconds
    refetchInterval: 60000, // Poll every 60 seconds
  })
}
