/**
 * Hook for fetching detailed market statistics for a specific tournament.
 *
 * @module use-tournament-markets
 * @description Fetches events for a tournament and computes per-market statistics
 * including average, min, max margin and margin history timeline for charts.
 */

import { useQuery } from '@tanstack/react-query'
import { subDays } from 'date-fns'
import { api } from '@/lib/api'
import type { DateRange } from '../components'
import type { MatchedEvent } from '@/types/api'

const BETPAWA_SLUG = 'betpawa'

/**
 * Single margin data point for timeline charts.
 */
export interface MarginHistoryPoint {
  capturedAt: string
  margin: number
}

/**
 * Market statistics for a tournament.
 */
export interface TournamentMarket {
  /** Market ID (e.g., "3743" for 1X2) */
  id: string
  /** Market name (e.g., "1X2", "Over/Under") */
  name: string
  /** Line value for handicap/total markets, or null */
  line: number | null
  /** Average Betpawa margin across all events */
  avgMargin: number
  /** Minimum margin observed */
  minMargin: number
  /** Maximum margin observed */
  maxMargin: number
  /** Number of events with this market */
  eventCount: number
  /** Chronological margin history for timeline chart */
  marginHistory: MarginHistoryPoint[]
}

/**
 * Tournament metadata.
 */
export interface TournamentInfo {
  id: number
  name: string
  country: string | null
  eventCount: number
}

/**
 * Per-market accumulator during data extraction.
 */
interface MarketAccumulator {
  id: string
  name: string
  line: number | null
  margins: number[]
  marginHistory: MarginHistoryPoint[]
}

/**
 * Generate a unique key for a market (id + line combination).
 */
function getMarketKey(marketId: string, line: number | null): string {
  return line !== null ? `${marketId}:${line}` : marketId
}

/**
 * Hook to fetch and compute market statistics for a specific tournament.
 *
 * @param tournamentId - The tournament ID to fetch data for
 * @param dateRange - Optional date range filter (defaults to last 30 days)
 * @returns Query result with markets data and tournament info
 */
export function useTournamentMarkets(
  tournamentId: number,
  dateRange?: DateRange
) {
  // Default to last 30 days if no range provided
  const effectiveRange = dateRange ?? {
    from: (() => {
      const d = subDays(new Date(), 30)
      d.setHours(0, 0, 0, 0)
      return d
    })(),
    to: (() => {
      const d = new Date()
      d.setHours(23, 59, 59, 999)
      return d
    })(),
  }

  const kickoffFrom = effectiveRange.from?.toISOString()
  const kickoffTo = effectiveRange.to?.toISOString()

  return useQuery({
    queryKey: ['tournament-markets', tournamentId, kickoffFrom, kickoffTo],
    queryFn: async () => {
      // Fetch all events using pagination
      const pageSize = 100
      let allEvents: MatchedEvent[] = []
      let page = 1

      while (true) {
        const response = await api.getEvents({
          page,
          page_size: pageSize,
          kickoff_from: kickoffFrom,
          kickoff_to: kickoffTo,
          include_started: true,
        })

        allEvents = allEvents.concat(response.events)

        if (response.events.length < pageSize) break
        page++
      }

      // Filter events for this specific tournament
      const tournamentEvents = allEvents.filter(
        (e) => e.tournament_id === tournamentId
      )

      if (tournamentEvents.length === 0) {
        return {
          markets: [] as TournamentMarket[],
          tournament: null as TournamentInfo | null,
        }
      }

      // Extract tournament info from first event
      const firstEvent = tournamentEvents[0]
      const tournament: TournamentInfo = {
        id: tournamentId,
        name: firstEvent.tournament_name,
        country: firstEvent.tournament_country,
        eventCount: tournamentEvents.length,
      }

      // Accumulate market data
      const marketMap = new Map<string, MarketAccumulator>()

      for (const event of tournamentEvents) {
        // Find Betpawa bookmaker data
        const betpawa = event.bookmakers.find(
          (b) => b.bookmaker_slug === BETPAWA_SLUG && b.has_odds
        )
        if (!betpawa) continue

        // Extract all markets from Betpawa's inline_odds
        for (const market of betpawa.inline_odds) {
          if (market.margin === null || market.margin < 0) continue

          const key = getMarketKey(market.market_id, market.line)
          let acc = marketMap.get(key)

          if (!acc) {
            acc = {
              id: market.market_id,
              name: market.market_name,
              line: market.line,
              margins: [],
              marginHistory: [],
            }
            marketMap.set(key, acc)
          }

          acc.margins.push(market.margin)
          acc.marginHistory.push({
            capturedAt: betpawa.snapshot_time || event.kickoff,
            margin: market.margin,
          })
        }
      }

      // Convert accumulators to TournamentMarket objects
      const markets: TournamentMarket[] = []

      for (const acc of marketMap.values()) {
        if (acc.margins.length === 0) continue

        const avgMargin =
          acc.margins.reduce((sum, m) => sum + m, 0) / acc.margins.length
        const minMargin = Math.min(...acc.margins)
        const maxMargin = Math.max(...acc.margins)

        // Sort margin history by time
        const sortedHistory = [...acc.marginHistory].sort(
          (a, b) =>
            new Date(a.capturedAt).getTime() - new Date(b.capturedAt).getTime()
        )

        markets.push({
          id: acc.id,
          name: acc.name,
          line: acc.line,
          avgMargin,
          minMargin,
          maxMargin,
          eventCount: acc.margins.length,
          marginHistory: sortedHistory,
        })
      }

      // Sort by eventCount descending (most common markets first)
      markets.sort((a, b) => b.eventCount - a.eventCount)

      return { markets, tournament }
    },
    enabled: Boolean(tournamentId && kickoffFrom && kickoffTo),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  })
}
