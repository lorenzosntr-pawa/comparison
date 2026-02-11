/**
 * Hook for fetching detailed market statistics for a specific tournament.
 *
 * @module use-tournament-markets
 * @description Fetches events for a tournament and computes per-market statistics
 * including average, min, max margin and margin history timeline for charts.
 * Fetches full event details to get ALL markets (not just inline summary).
 */

import { useQuery } from '@tanstack/react-query'
import { subDays } from 'date-fns'
import { api } from '@/lib/api'
import type { DateRange } from '../components'
import type { MatchedEvent, EventDetailResponse } from '@/types/api'

const BETPAWA_SLUG = 'betpawa'

/** Concurrency limit for fetching event details */
const CONCURRENT_FETCHES = 5

/**
 * Single margin data point for timeline charts.
 */
export interface MarginHistoryPoint {
  capturedAt: string
  margin: number
}

/**
 * Margin data point with time-to-kickoff calculation for normalized X-axis.
 */
export interface TimeToKickoffPoint {
  /** Hours until kickoff (negative values: -72, -24, -1, etc.) */
  hoursToKickoff: number
  /** Margin value */
  margin: number
  /** Event ID for drill-down capability */
  eventId: number
}

/**
 * Time bucket labels for grouping margin data.
 */
export type TimeBucket = '7d+' | '3-7d' | '24-72h' | '<24h'

/**
 * Statistics for a specific time bucket.
 */
export interface BucketStats {
  bucket: TimeBucket
  avgMargin: number
  pointCount: number
}

/**
 * Margin statistics for a bookmaker (used for competitor data).
 */
export interface MarketMarginStats {
  /** Average margin across all events */
  avgMargin: number
  /** Minimum margin observed */
  minMargin: number
  /** Maximum margin observed */
  maxMargin: number
  /** Number of events with data */
  eventCount: number
  /** First recorded margin (earliest snapshot) */
  openingMargin?: number
  /** Last recorded margin (closest to kickoff) */
  closingMargin?: number
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
  /** First margin data point (earliest captured_at) */
  openingMargin: number
  /** Last margin data point (closest to kickoff) */
  closingMargin: number
  /** Change from opening to closing margin */
  marginDelta: number
  /** Margin history with normalized time-to-kickoff X-axis */
  timeToKickoffHistory: TimeToKickoffPoint[]
  /** Statistics per time bucket */
  bucketStats: BucketStats[]
  /** Competitor margin stats keyed by bookmaker slug (e.g., sportybet, bet9ja) */
  competitorMargins: Record<string, MarketMarginStats | null>
  /** Competitor time-to-kickoff data keyed by bookmaker slug for overlay charts */
  competitorTimelineData: Record<string, TimeToKickoffPoint[]>
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
  timeToKickoffHistory: TimeToKickoffPoint[]
  /** Competitor margins keyed by bookmaker slug */
  competitorMargins: Record<string, number[]>
  /** Competitor time-to-kickoff data keyed by bookmaker slug */
  competitorTimelineData: Record<string, TimeToKickoffPoint[]>
}

/** Competitor bookmaker slugs to track */
const COMPETITOR_SLUGS = ['sportybet', 'bet9ja']

/**
 * Determine which time bucket a hoursToKickoff value falls into.
 */
function getTimeBucket(hoursToKickoff: number): TimeBucket {
  // hoursToKickoff is negative (e.g., -72 means 72 hours before kickoff)
  if (hoursToKickoff <= -168) return '7d+' // 7 * 24 = 168 hours
  if (hoursToKickoff <= -72) return '3-7d'
  if (hoursToKickoff <= -24) return '24-72h'
  return '<24h'
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

      // Fetch full event details in batches to get ALL markets
      // (inline_odds only contains summary markets, markets_by_bookmaker has all)
      const eventDetails: EventDetailResponse[] = []

      for (let i = 0; i < tournamentEvents.length; i += CONCURRENT_FETCHES) {
        const batch = tournamentEvents.slice(i, i + CONCURRENT_FETCHES)
        const results = await Promise.all(
          batch.map((event) =>
            api.getEventDetail(event.id).catch(() => null)
          )
        )
        eventDetails.push(
          ...results.filter((r): r is EventDetailResponse => r !== null)
        )
      }

      // Accumulate market data from full event details
      const marketMap = new Map<string, MarketAccumulator>()

      for (const eventDetail of eventDetails) {
        // Find Betpawa in markets_by_bookmaker
        const betpawaData = eventDetail.markets_by_bookmaker.find(
          (b) => b.bookmaker_slug === BETPAWA_SLUG
        )
        if (!betpawaData) continue

        // Parse event kickoff time for time-to-kickoff calculation
        const kickoffTime = new Date(eventDetail.kickoff).getTime()
        const capturedAtRaw = betpawaData.snapshot_time || eventDetail.kickoff
        const capturedAtTime = new Date(capturedAtRaw).getTime()

        // Calculate hours to kickoff (negative: before kickoff)
        const hoursToKickoff = (capturedAtTime - kickoffTime) / (1000 * 60 * 60)

        // Extract ALL markets from Betpawa's full market list
        for (const market of betpawaData.markets) {
          if (market.margin === null || market.margin < 0) continue

          const key = getMarketKey(market.betpawa_market_id, market.line)
          let acc = marketMap.get(key)

          if (!acc) {
            acc = {
              id: market.betpawa_market_id,
              name: market.betpawa_market_name,
              line: market.line,
              margins: [],
              marginHistory: [],
              timeToKickoffHistory: [],
              competitorMargins: {},
              competitorTimelineData: {},
            }
            marketMap.set(key, acc)
          }

          acc.margins.push(market.margin)
          acc.marginHistory.push({
            capturedAt: capturedAtRaw,
            margin: market.margin,
          })
          acc.timeToKickoffHistory.push({
            hoursToKickoff,
            margin: market.margin,
            eventId: eventDetail.id,
          })
        }

        // Extract competitor margin data for matching markets
        for (const competitorSlug of COMPETITOR_SLUGS) {
          const competitorBookmaker = eventDetail.markets_by_bookmaker.find(
            (b) => b.bookmaker_slug === competitorSlug
          )
          if (!competitorBookmaker) continue

          // Calculate hours to kickoff for this competitor's snapshot
          const compCapturedAtRaw = competitorBookmaker.snapshot_time || eventDetail.kickoff
          const compCapturedAtTime = new Date(compCapturedAtRaw).getTime()
          const compHoursToKickoff = (compCapturedAtTime - kickoffTime) / (1000 * 60 * 60)

          // For each competitor market, find matching Betpawa market by market_id + line
          for (const compMarket of competitorBookmaker.markets) {
            if (compMarket.margin === null || compMarket.margin < 0) continue

            const key = getMarketKey(compMarket.betpawa_market_id, compMarket.line)
            const acc = marketMap.get(key)

            // Only add competitor data for markets we're already tracking (from Betpawa)
            if (acc) {
              // Aggregate margin stats
              if (!acc.competitorMargins[competitorSlug]) {
                acc.competitorMargins[competitorSlug] = []
              }
              acc.competitorMargins[competitorSlug].push(compMarket.margin)

              // Time-to-kickoff timeline data
              if (!acc.competitorTimelineData[competitorSlug]) {
                acc.competitorTimelineData[competitorSlug] = []
              }
              acc.competitorTimelineData[competitorSlug].push({
                hoursToKickoff: compHoursToKickoff,
                margin: compMarket.margin,
                eventId: eventDetail.id,
              })
            }
          }
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

        // Sort time-to-kickoff history (most negative = earliest first)
        const sortedTimeToKickoff = [...acc.timeToKickoffHistory].sort(
          (a, b) => a.hoursToKickoff - b.hoursToKickoff
        )

        // Compute opening/closing margins from sorted time-to-kickoff history
        const openingMargin =
          sortedTimeToKickoff.length > 0 ? sortedTimeToKickoff[0].margin : avgMargin
        const closingMargin =
          sortedTimeToKickoff.length > 0
            ? sortedTimeToKickoff[sortedTimeToKickoff.length - 1].margin
            : avgMargin
        const marginDelta = closingMargin - openingMargin

        // Compute bucket statistics
        const bucketData: Record<TimeBucket, number[]> = {
          '7d+': [],
          '3-7d': [],
          '24-72h': [],
          '<24h': [],
        }

        for (const point of sortedTimeToKickoff) {
          const bucket = getTimeBucket(point.hoursToKickoff)
          bucketData[bucket].push(point.margin)
        }

        const bucketStats: BucketStats[] = (
          ['7d+', '3-7d', '24-72h', '<24h'] as TimeBucket[]
        )
          .map((bucket) => {
            const margins = bucketData[bucket]
            return {
              bucket,
              avgMargin:
                margins.length > 0
                  ? margins.reduce((s, m) => s + m, 0) / margins.length
                  : 0,
              pointCount: margins.length,
            }
          })
          .filter((s) => s.pointCount > 0) // Only include buckets with data

        // Compute competitor margin stats with opening/closing
        const competitorMargins: Record<string, MarketMarginStats | null> = {}
        for (const slug of COMPETITOR_SLUGS) {
          const margins = acc.competitorMargins[slug] || []
          const timeline = acc.competitorTimelineData[slug] || []
          if (margins.length > 0) {
            // Sort competitor timeline to get opening/closing
            const sortedTimeline = [...timeline].sort(
              (a, b) => a.hoursToKickoff - b.hoursToKickoff
            )
            const openingMargin = sortedTimeline.length > 0 ? sortedTimeline[0].margin : undefined
            const closingMargin = sortedTimeline.length > 0 ? sortedTimeline[sortedTimeline.length - 1].margin : undefined

            competitorMargins[slug] = {
              avgMargin: margins.reduce((s, m) => s + m, 0) / margins.length,
              minMargin: Math.min(...margins),
              maxMargin: Math.max(...margins),
              eventCount: margins.length,
              openingMargin,
              closingMargin,
            }
          } else {
            competitorMargins[slug] = null
          }
        }

        // Sort competitor timeline data by hoursToKickoff
        const competitorTimelineData: Record<string, TimeToKickoffPoint[]> = {}
        for (const slug of COMPETITOR_SLUGS) {
          const timeline = acc.competitorTimelineData[slug] || []
          if (timeline.length > 0) {
            competitorTimelineData[slug] = [...timeline].sort(
              (a, b) => a.hoursToKickoff - b.hoursToKickoff
            )
          }
        }

        markets.push({
          id: acc.id,
          name: acc.name,
          line: acc.line,
          avgMargin,
          minMargin,
          maxMargin,
          eventCount: acc.margins.length,
          marginHistory: sortedHistory,
          openingMargin,
          closingMargin,
          marginDelta,
          timeToKickoffHistory: sortedTimeToKickoff,
          bucketStats,
          competitorMargins,
          competitorTimelineData,
        })
      }

      // Sort by eventCount descending (most common markets first)
      markets.sort((a, b) => b.eventCount - a.eventCount)

      return { markets, tournament }
    },
    enabled: Boolean(tournamentId && kickoffFrom && kickoffTo),
    staleTime: 10 * 60 * 1000, // 10 minutes (longer since we fetch many event details)
    gcTime: 15 * 60 * 1000, // 15 minutes
  })
}
