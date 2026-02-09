/**
 * Hook for fetching detailed information about a single match.
 *
 * @module use-match-detail
 * @description Provides comprehensive event data including team names, kickoff time,
 * tournament info, and all available odds from all bookmakers. Used on the match
 * detail page to show full comparison data.
 *
 * @example
 * ```typescript
 * import { useMatchDetail } from '@/features/matches/hooks/use-match-detail'
 *
 * function MatchDetailPage({ eventId }: { eventId: number }) {
 *   const { data: event, isPending, error } = useMatchDetail(eventId)
 *
 *   if (isPending) return <Spinner />
 *   if (error) return <ErrorMessage error={error} />
 *
 *   return (
 *     <div>
 *       <h1>{event.home_team} vs {event.away_team}</h1>
 *       <p>Kickoff: {event.kickoff_time}</p>
 *       <OddsComparisonTable markets={event.markets} />
 *     </div>
 *   )
 * }
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

/**
 * Fetches detailed event data for a single match.
 *
 * @description Returns full event data including all markets and odds from
 * all bookmakers. Polls every 60 seconds to keep odds current. The query
 * is disabled if eventId is undefined or NaN.
 *
 * @param eventId - The event ID to fetch, or undefined to disable the query
 * @returns TanStack Query result with EventDetailResponse containing full event data
 *
 * @example
 * ```typescript
 * // In a route component
 * const params = useParams()
 * const eventId = params.id ? parseInt(params.id) : undefined
 * const { data, isPending } = useMatchDetail(eventId)
 * ```
 */
export function useMatchDetail(eventId: number | undefined) {
  return useQuery({
    queryKey: ['match-detail', eventId],
    queryFn: () => api.getEventDetail(eventId!),
    enabled: eventId !== undefined && !isNaN(eventId),
    staleTime: 30000, // 30 seconds
    gcTime: 60000, // 60 seconds
    refetchInterval: 60000, // Poll every 60 seconds
  })
}
