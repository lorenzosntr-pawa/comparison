/**
 * Hook for fetching the list of available tournaments.
 *
 * @module use-tournaments
 * @description Provides the list of tournaments (competitions/leagues) that have
 * events in the system. Used for populating tournament filter dropdowns in the
 * matches list view.
 *
 * @example
 * ```typescript
 * import { useTournaments } from '@/features/matches/hooks/use-tournaments'
 *
 * function TournamentFilter({ value, onChange }) {
 *   const { data: tournaments, isPending } = useTournaments()
 *
 *   if (isPending) return <Select disabled placeholder="Loading..." />
 *
 *   return (
 *     <Select value={value} onValueChange={onChange}>
 *       {tournaments?.map(t => (
 *         <SelectItem key={t.id} value={t.id.toString()}>
 *           {t.name} ({t.country})
 *         </SelectItem>
 *       ))}
 *     </Select>
 *   )
 * }
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

/**
 * Tournament (competition/league) data.
 *
 * @description Represents a tournament that can be used to filter events.
 */
export interface Tournament {
  /** Unique tournament ID */
  id: number
  /** Tournament name (e.g., "Premier League", "La Liga") */
  name: string
  /** Country code or name, null for international tournaments */
  country: string | null
}

/**
 * Fetches the list of available tournaments.
 *
 * @description Returns all tournaments that have events in the database.
 * Uses a 5-minute stale time since tournament lists rarely change.
 * Commonly used to populate filter dropdowns.
 *
 * @returns TanStack Query result with array of Tournament objects
 *
 * @example
 * ```typescript
 * const { data: tournaments, isPending, error } = useTournaments()
 *
 * // Group by country for nested display
 * const byCountry = tournaments?.reduce((acc, t) => {
 *   const country = t.country || 'International'
 *   if (!acc[country]) acc[country] = []
 *   acc[country].push(t)
 *   return acc
 * }, {})
 * ```
 */
export function useTournaments() {
  return useQuery({
    queryKey: ['tournaments'],
    queryFn: () => api.getTournaments(),
    staleTime: 5 * 60 * 1000, // 5 minutes - tournaments don't change often
    gcTime: 10 * 60 * 1000, // 10 minutes
  })
}
