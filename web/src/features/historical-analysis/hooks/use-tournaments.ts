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

/**
 * Tracked markets for historical analysis.
 * Market IDs from use-column-settings.ts
 */
export const TRACKED_MARKETS = [
  { id: '3743', label: '1X2' },
  { id: '5000', label: 'O/U 2.5' },
  { id: '3795', label: 'BTTS' },
  { id: '4693', label: 'DC' },
] as const

/**
 * Margin metrics for a single market type.
 */
export interface MarginMetrics {
  /** Average Betpawa margin for this market, or null if no data */
  avgMargin: number | null
  /** Average best competitor margin (lowest of sportybet/bet9ja), or null if no data */
  competitorAvgMargin: number | null
  /** Margin trend indicator, or null if insufficient data */
  trend: 'up' | 'down' | 'stable' | null
  /** Opening margin (earliest event by kickoff), or null if no data */
  openingMargin: number | null
  /** Closing margin (latest event by kickoff), or null if no data */
  closingMargin: number | null
  /** Delta between closing and opening margin (closing - opening), or null if either is null */
  marginDelta: number | null
}

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
  /** Margin metrics by market ID (e.g., '3743' for 1X2) */
  marginsByMarket: Record<string, MarginMetrics>
  /** Coverage percentage by bookmaker (0-100) */
  coverageByBookmaker: Record<string, number>
}

/**
 * Per-market accumulator data during extraction.
 */
interface MarketAccumulatorData {
  betpawaMargins: number[]
  competitorMargins: number[]
  eventMargins: { kickoff: string; margin: number }[]
}

/**
 * Internal structure for accumulating tournament data during extraction.
 */
interface TournamentAccumulator {
  id: number
  name: string
  country: string | null
  eventCount: number
  /** Per-market margin data keyed by market ID */
  marginData: Record<string, MarketAccumulatorData>
  coverageCounts: Record<string, number>
}

/**
 * Extract the margin for a specific bookmaker and market from an event.
 * @param event - The matched event
 * @param bookmakerSlug - The bookmaker to extract margin from
 * @param marketId - The market ID to extract margin for
 * @returns The margin or null if not available
 */
function extractBookmakerMargin(
  event: MatchedEvent,
  bookmakerSlug: string,
  marketId: string
): number | null {
  const bookmaker = event.bookmakers.find(
    (b) => b.bookmaker_slug === bookmakerSlug && b.has_odds
  )
  if (!bookmaker) return null

  const market = bookmaker.inline_odds.find((odds) => odds.market_id === marketId)
  return market?.margin ?? null
}

/**
 * Get the best (lowest) competitor margin from an event for a specific market.
 * @param event - The matched event
 * @param marketId - The market ID to extract margin for
 * @returns The lowest competitor margin or null if none available
 */
function getBestCompetitorMargin(
  event: MatchedEvent,
  marketId: string
): number | null {
  const margins = COMPETITOR_SLUGS.map((slug) =>
    extractBookmakerMargin(event, slug, marketId)
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
 * Create an empty market accumulator data structure.
 */
function createEmptyMarketData(): MarketAccumulatorData {
  return {
    betpawaMargins: [],
    competitorMargins: [],
    eventMargins: [],
  }
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
          include_started: true, // BUG-013 fix: include completed matches
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
            marginData: {},
            coverageCounts: {},
          }
          // Initialize margin data for all tracked markets
          for (const market of TRACKED_MARKETS) {
            accumulator.marginData[market.id] = createEmptyMarketData()
          }
          // Initialize coverage counts for all bookmakers
          for (const slug of ALL_BOOKMAKER_SLUGS) {
            accumulator.coverageCounts[slug] = 0
          }
          tournamentMap.set(event.tournament_id, accumulator)
        }

        accumulator.eventCount++

        // Extract margins for each tracked market
        for (const market of TRACKED_MARKETS) {
          const marketData = accumulator.marginData[market.id]

          // Extract Betpawa margin for this market
          const betpawaMargin = extractBookmakerMargin(
            event,
            BETPAWA_SLUG,
            market.id
          )
          if (betpawaMargin !== null) {
            marketData.betpawaMargins.push(betpawaMargin)
            marketData.eventMargins.push({
              kickoff: event.kickoff,
              margin: betpawaMargin,
            })
          }

          // Extract best competitor margin for this market
          const competitorMargin = getBestCompetitorMargin(event, market.id)
          if (competitorMargin !== null) {
            marketData.competitorMargins.push(competitorMargin)
          }
        }

        // Track coverage per bookmaker (event-level, not market-level)
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
        // Calculate margin metrics for each market
        const marginsByMarket: Record<string, MarginMetrics> = {}

        for (const market of TRACKED_MARKETS) {
          const marketData = acc.marginData[market.id]

          const avgMargin =
            marketData.betpawaMargins.length > 0
              ? marketData.betpawaMargins.reduce((sum, m) => sum + m, 0) /
                marketData.betpawaMargins.length
              : null

          const competitorAvgMargin =
            marketData.competitorMargins.length > 0
              ? marketData.competitorMargins.reduce((sum, m) => sum + m, 0) /
                marketData.competitorMargins.length
              : null

          const trend = calculateTrend(marketData.eventMargins)

          // Calculate opening/closing margins from kickoff-sorted events
          let openingMargin: number | null = null
          let closingMargin: number | null = null
          let marginDelta: number | null = null

          if (marketData.eventMargins.length > 0) {
            // Sort by kickoff ascending to get chronological order
            const sorted = [...marketData.eventMargins].sort(
              (a, b) => new Date(a.kickoff).getTime() - new Date(b.kickoff).getTime()
            )
            openingMargin = sorted[0].margin
            closingMargin = sorted[sorted.length - 1].margin
            marginDelta = closingMargin - openingMargin
          }

          marginsByMarket[market.id] = {
            avgMargin,
            competitorAvgMargin,
            trend,
            openingMargin,
            closingMargin,
            marginDelta,
          }
        }

        // Calculate coverage percentages
        const coverageByBookmaker: Record<string, number> = {}
        for (const slug of ALL_BOOKMAKER_SLUGS) {
          coverageByBookmaker[slug] =
            acc.eventCount > 0
              ? (acc.coverageCounts[slug] / acc.eventCount) * 100
              : 0
        }

        tournaments.push({
          id: acc.id,
          name: acc.name,
          country: acc.country,
          eventCount: acc.eventCount,
          marginsByMarket,
          coverageByBookmaker,
        })
      }

      // Sort by 1X2 avgMargin ascending (best first), null values last
      const market1X2Id = TRACKED_MARKETS[0].id
      return tournaments.sort((a, b) => {
        const aMargin = a.marginsByMarket[market1X2Id]?.avgMargin
        const bMargin = b.marginsByMarket[market1X2Id]?.avgMargin
        if (aMargin === null && bMargin === null) return 0
        if (aMargin === null) return 1
        if (bMargin === null) return -1
        return aMargin - bMargin
      })
    },
    enabled: Boolean(kickoffFrom && kickoffTo),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  })
}
