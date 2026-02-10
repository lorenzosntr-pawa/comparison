/**
 * Hook for fetching tournaments with event counts for historical analysis.
 *
 * @module use-tournaments
 * @description Fetches events within a date range and extracts unique tournaments
 * with their event counts. Used in the historical analysis page to show which
 * tournaments have data in the selected period.
 */

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { DateRange } from '../components'

/**
 * Tournament with event count for historical analysis.
 */
export interface TournamentWithCount {
  /** Tournament ID */
  id: number
  /** Tournament name */
  name: string
  /** Country or null for international */
  country: string | null
  /** Number of events in the date range */
  eventCount: number
}

/**
 * Fetches tournaments with event counts for a date range.
 *
 * @param dateRange - The date range to query
 * @returns TanStack Query result with array of TournamentWithCount
 */
export function useTournaments(dateRange: DateRange) {
  const kickoffFrom = dateRange.from?.toISOString()
  const kickoffTo = dateRange.to?.toISOString()

  return useQuery({
    queryKey: ['historical-tournaments', kickoffFrom, kickoffTo],
    queryFn: async () => {
      // Fetch all events in the date range (large page size to get all)
      const response = await api.getEvents({
        page: 1,
        page_size: 1000,
        kickoff_from: kickoffFrom,
        kickoff_to: kickoffTo,
      })

      // Extract unique tournaments with event counts
      const tournamentMap = new Map<number, TournamentWithCount>()

      for (const event of response.events) {
        const existing = tournamentMap.get(event.tournament_id)
        if (existing) {
          existing.eventCount++
        } else {
          tournamentMap.set(event.tournament_id, {
            id: event.tournament_id,
            name: event.tournament_name,
            country: event.tournament_country,
            eventCount: 1,
          })
        }
      }

      // Sort by event count (descending)
      return Array.from(tournamentMap.values()).sort(
        (a, b) => b.eventCount - a.eventCount
      )
    },
    enabled: Boolean(kickoffFrom && kickoffTo),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  })
}
