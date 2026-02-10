/**
 * Hook for fetching tournaments with event counts for historical analysis.
 *
 * @module use-tournaments
 * @description Fetches events within a date range and extracts unique tournaments
 * with their event counts and metrics. Used in the historical analysis page to show
 * which tournaments have data in the selected period along with margin and coverage stats.
 */

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { DateRange } from '../components'
import type { MatchedEvent } from '@/types/api'

/** Bookmaker slugs for analysis */
const BETPAWA_SLUG = 'betpawa'
const COMPETITOR_SLUGS = ['sportybet', 'bet9ja']
const ALL_BOOKMAKER_SLUGS = [BETPAWA_SLUG, ...COMPETITOR_SLUGS]

/** Market ID for 1X2 (match result) */
const MARKET_1X2_ID = '3743'

/**
 * Tournament with event count and metrics for historical analysis.
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
  /** Average Betpawa 1X2 margin for the tournament, or null if no data */
  avgMargin: number | null
  /** Average best competitor 1X2 margin (lowest of sportybet/bet9ja), or null if no data */
  competitorAvgMargin: number | null
  /** Coverage percentage by bookmaker (0-100) */
  coverageByBookmaker: Record<string, number>
  /** Margin trend indicator, or null if insufficient data */
  trend: 'up' | 'down' | 'stable' | null
}

/**
 * Internal structure for accumulating tournament data during extraction.
 */
interface TournamentAccumulator {
  id: number
  name: string
  country: string | null
  eventCount: number
  betpawaMargins: number[]
  competitorMargins: number[]
  coverageCounts: Record<string, number>
  /** Events with kickoff and margin for trend calculation */
  eventMargins: { kickoff: string; margin: number }[]
}

/**
 * Extract the 1X2 margin for a specific bookmaker from an event.
 * @param event - The matched event
 * @param bookmakerSlug - The bookmaker to extract margin from
 * @returns The 1X2 margin or null if not available
 */
function extractBookmaker1X2Margin(
  event: MatchedEvent,
  bookmakerSlug: string
): number | null {
  const bookmaker = event.bookmakers.find(
    (b) => b.bookmaker_slug === bookmakerSlug && b.has_odds
  )
  if (!bookmaker) return null

  const market1X2 = bookmaker.inline_odds.find(
    (odds) => odds.market_id === MARKET_1X2_ID
  )
  return market1X2?.margin ?? null
}

/**
 * Get the best (lowest) competitor margin from an event.
 * @param event - The matched event
 * @returns The lowest competitor margin or null if none available
 */
function getBestCompetitorMargin(event: MatchedEvent): number | null {
  const margins = COMPETITOR_SLUGS.map((slug) =>
    extractBookmaker1X2Margin(event, slug)
  ).filter((m): m is number => m !== null)

  if (margins.length === 0) return null
  return Math.min(...margins)
}

/**
 * Calculate trend based on first-half vs second-half margin comparison.
 * @param eventMargins - Array of events with kickoff and margin, sorted by kickoff
 * @returns 'up' (worsening), 'down' (improving), 'stable', or null if insufficient data
 */
function calculateTrend(
  eventMargins: { kickoff: string; margin: number }[]
): 'up' | 'down' | 'stable' | null {
  // Need at least 4 events for trend calculation
  if (eventMargins.length < 4) return null

  // Sort by kickoff ascending
  const sorted = [...eventMargins].sort(
    (a, b) => new Date(a.kickoff).getTime() - new Date(b.kickoff).getTime()
  )

  // Split into first and second halves
  const midpoint = Math.floor(sorted.length / 2)
  const firstHalf = sorted.slice(0, midpoint)
  const secondHalf = sorted.slice(midpoint)

  // Calculate averages
  const firstHalfAvg =
    firstHalf.reduce((sum, e) => sum + e.margin, 0) / firstHalf.length
  const secondHalfAvg =
    secondHalf.reduce((sum, e) => sum + e.margin, 0) / secondHalf.length

  const diff = secondHalfAvg - firstHalfAvg

  // Threshold is 0.5%
  if (diff < -0.5) return 'down' // Improving (margin going down)
  if (diff > 0.5) return 'up' // Worsening (margin going up)
  return 'stable'
}

/**
 * Fetches tournaments with event counts and metrics for a date range.
 *
 * @param dateRange - The date range to query
 * @returns TanStack Query result with array of TournamentWithCount including metrics
 */
export function useTournaments(dateRange: DateRange) {
  const kickoffFrom = dateRange.from?.toISOString()
  const kickoffTo = dateRange.to?.toISOString()

  return useQuery({
    queryKey: ['historical-tournaments', kickoffFrom, kickoffTo],
    queryFn: async () => {
      // Fetch all events in the date range using pagination (API max is 100)
      const pageSize = 100
      let allEvents: MatchedEvent[] = []
      let page = 1

      while (true) {
        const response = await api.getEvents({
          page,
          page_size: pageSize,
          kickoff_from: kickoffFrom,
          kickoff_to: kickoffTo,
        })

        allEvents = allEvents.concat(response.events)

        // If we got fewer events than requested, we've reached the end
        if (response.events.length < pageSize) break

        page++
      }

      // Extract unique tournaments with event counts and accumulate metrics data
      const tournamentMap = new Map<number, TournamentAccumulator>()

      for (const event of allEvents) {
        let accumulator = tournamentMap.get(event.tournament_id)

        if (!accumulator) {
          accumulator = {
            id: event.tournament_id,
            name: event.tournament_name,
            country: event.tournament_country,
            eventCount: 0,
            betpawaMargins: [],
            competitorMargins: [],
            coverageCounts: {},
            eventMargins: [],
          }
          // Initialize coverage counts for all bookmakers
          for (const slug of ALL_BOOKMAKER_SLUGS) {
            accumulator.coverageCounts[slug] = 0
          }
          tournamentMap.set(event.tournament_id, accumulator)
        }

        accumulator.eventCount++

        // Extract Betpawa 1X2 margin
        const betpawaMargin = extractBookmaker1X2Margin(event, BETPAWA_SLUG)
        if (betpawaMargin !== null) {
          accumulator.betpawaMargins.push(betpawaMargin)
          accumulator.eventMargins.push({
            kickoff: event.kickoff,
            margin: betpawaMargin,
          })
        }

        // Extract best competitor margin
        const competitorMargin = getBestCompetitorMargin(event)
        if (competitorMargin !== null) {
          accumulator.competitorMargins.push(competitorMargin)
        }

        // Track coverage per bookmaker
        for (const bookmaker of event.bookmakers) {
          if (
            ALL_BOOKMAKER_SLUGS.includes(bookmaker.bookmaker_slug) &&
            bookmaker.has_odds
          ) {
            accumulator.coverageCounts[bookmaker.bookmaker_slug]++
          }
        }
      }

      // Convert accumulators to final TournamentWithCount objects
      const tournaments: TournamentWithCount[] = []

      for (const acc of tournamentMap.values()) {
        // Calculate average margins
        const avgMargin =
          acc.betpawaMargins.length > 0
            ? acc.betpawaMargins.reduce((sum, m) => sum + m, 0) /
              acc.betpawaMargins.length
            : null

        const competitorAvgMargin =
          acc.competitorMargins.length > 0
            ? acc.competitorMargins.reduce((sum, m) => sum + m, 0) /
              acc.competitorMargins.length
            : null

        // Calculate coverage percentages
        const coverageByBookmaker: Record<string, number> = {}
        for (const slug of ALL_BOOKMAKER_SLUGS) {
          coverageByBookmaker[slug] =
            acc.eventCount > 0
              ? (acc.coverageCounts[slug] / acc.eventCount) * 100
              : 0
        }

        // Calculate trend
        const trend = calculateTrend(acc.eventMargins)

        tournaments.push({
          id: acc.id,
          name: acc.name,
          country: acc.country,
          eventCount: acc.eventCount,
          avgMargin,
          competitorAvgMargin,
          coverageByBookmaker,
          trend,
        })
      }

      // Sort by Betpawa avgMargin ascending (best first), null values last
      return tournaments.sort((a, b) => {
        if (a.avgMargin === null && b.avgMargin === null) return 0
        if (a.avgMargin === null) return 1
        if (b.avgMargin === null) return -1
        return a.avgMargin - b.avgMargin
      })
    },
    enabled: Boolean(kickoffFrom && kickoffTo),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  })
}
