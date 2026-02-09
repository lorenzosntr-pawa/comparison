/**
 * Hook for fetching event statistics for the dashboard.
 *
 * @module use-events-stats
 * @description Provides aggregate event counts for displaying on the dashboard.
 * Makes two parallel API calls to get total event count and matched event count
 * (events with odds from at least 2 bookmakers).
 *
 * @example
 * ```typescript
 * import { useEventsStats } from '@/features/dashboard/hooks/use-events-stats'
 *
 * function DashboardStats() {
 *   const { totalEvents, matchedEvents, isPending } = useEventsStats()
 *
 *   if (isPending) return <Spinner />
 *
 *   return (
 *     <div>
 *       <p>Total Events: {totalEvents}</p>
 *       <p>Comparable Events: {matchedEvents}</p>
 *     </div>
 *   )
 * }
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

/**
 * Fetches event statistics for dashboard display.
 *
 * @description Runs two parallel queries to get:
 * 1. Total number of events in the system
 * 2. Number of "matched" events (available from 2+ bookmakers for comparison)
 *
 * Both queries poll every 60 seconds to keep stats current. Uses page_size=1
 * since we only need the total count, not the actual event data.
 *
 * @returns Object containing totalEvents count, matchedEvents count,
 *          isPending (true if either query loading), and error (first error encountered)
 *
 * @example
 * ```typescript
 * const { totalEvents, matchedEvents, isPending, error } = useEventsStats()
 *
 * const matchRate = matchedEvents / totalEvents * 100
 * console.log(`${matchRate.toFixed(1)}% of events are comparable`)
 * ```
 */
export function useEventsStats() {
  // Get events with at least 2 bookmakers (matched)
  const matchedQuery = useQuery({
    queryKey: ['events', 'stats', 'matched'],
    queryFn: () => api.getEvents({ page_size: 1, min_bookmakers: 2 }),
    refetchInterval: 60000, // Poll every 60s
  })

  // Get all events
  const totalQuery = useQuery({
    queryKey: ['events', 'stats', 'total'],
    queryFn: () => api.getEvents({ page_size: 1 }),
    refetchInterval: 60000,
  })

  return {
    totalEvents: totalQuery.data?.total ?? 0,
    matchedEvents: matchedQuery.data?.total ?? 0,
    isPending: matchedQuery.isPending || totalQuery.isPending,
    error: matchedQuery.error || totalQuery.error,
  }
}
