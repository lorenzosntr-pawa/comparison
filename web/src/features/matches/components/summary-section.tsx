import { useMemo } from 'react'
import { cn } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { BookmakerMarketData, MarketOddsDetail } from '@/types/api'

// Key market IDs (Betpawa taxonomy)
const KEY_MARKETS = {
  '1': '1X2',
  '18': 'Over/Under 2.5',
  '29': 'Both Teams to Score',
}

interface SummarySectionProps {
  marketsByBookmaker: BookmakerMarketData[]
}

interface CompetitiveStats {
  bestOddsCount: number
  totalOutcomes: number
  percentage: number
  avgMarginDiff: number
}

/**
 * Calculate competitive stats for Betpawa vs competitors.
 */
function calculateCompetitiveStats(
  marketsByBookmaker: BookmakerMarketData[]
): CompetitiveStats {
  const betpawaData = marketsByBookmaker.find(
    (b) => b.bookmaker_slug === 'betpawa'
  )

  if (!betpawaData) {
    return { bestOddsCount: 0, totalOutcomes: 0, percentage: 0, avgMarginDiff: 0 }
  }

  let bestOddsCount = 0
  let totalOutcomes = 0
  let marginDiffSum = 0
  let marginComparisons = 0

  // Build market maps for quick lookup
  const marketMaps = new Map<string, Map<string, MarketOddsDetail>>()
  for (const bookmakerData of marketsByBookmaker) {
    const marketMap = new Map<string, MarketOddsDetail>()
    for (const market of bookmakerData.markets) {
      const key =
        market.line !== null
          ? `${market.betpawa_market_id}_${market.line}`
          : market.betpawa_market_id
      marketMap.set(key, market)
    }
    marketMaps.set(bookmakerData.bookmaker_slug, marketMap)
  }

  // Iterate through Betpawa's markets
  const betpawaMarketMap = marketMaps.get('betpawa')!
  for (const [key, betpawaMarket] of betpawaMarketMap) {
    // Compare margins
    let competitorMarginSum = 0
    let competitorCount = 0
    for (const slug of ['sportybet', 'bet9ja']) {
      const competitorMap = marketMaps.get(slug)
      const competitorMarket = competitorMap?.get(key)
      if (competitorMarket) {
        competitorMarginSum += competitorMarket.margin
        competitorCount++
      }
    }
    if (competitorCount > 0) {
      const avgCompetitorMargin = competitorMarginSum / competitorCount
      marginDiffSum += betpawaMarket.margin - avgCompetitorMargin
      marginComparisons++
    }

    // Compare odds for each outcome
    for (const betpawaOutcome of betpawaMarket.outcomes) {
      if (!betpawaOutcome.is_active) continue

      totalOutcomes++

      // Find best odds across all bookmakers
      let bestOdds = betpawaOutcome.odds
      let betpawaHasBest = true

      for (const slug of ['sportybet', 'bet9ja']) {
        const competitorMap = marketMaps.get(slug)
        const competitorMarket = competitorMap?.get(key)
        if (competitorMarket) {
          const competitorOutcome = competitorMarket.outcomes.find(
            (o) => o.name === betpawaOutcome.name
          )
          if (competitorOutcome && competitorOutcome.is_active) {
            if (competitorOutcome.odds > bestOdds) {
              bestOdds = competitorOutcome.odds
              betpawaHasBest = false
            } else if (competitorOutcome.odds === bestOdds) {
              // Tie - Betpawa still counts as having best
            }
          }
        }
      }

      if (betpawaHasBest) {
        bestOddsCount++
      }
    }
  }

  const percentage =
    totalOutcomes > 0 ? (bestOddsCount / totalOutcomes) * 100 : 0
  const avgMarginDiff =
    marginComparisons > 0 ? marginDiffSum / marginComparisons : 0

  return { bestOddsCount, totalOutcomes, percentage, avgMarginDiff }
}

/**
 * Get key market data for quick summary display.
 */
function getKeyMarkets(
  marketsByBookmaker: BookmakerMarketData[]
): Map<string, Map<string, MarketOddsDetail | null>> {
  const result = new Map<string, Map<string, MarketOddsDetail | null>>()

  for (const marketId of Object.keys(KEY_MARKETS)) {
    const bookmakerOdds = new Map<string, MarketOddsDetail | null>()

    for (const bookmakerData of marketsByBookmaker) {
      const market = bookmakerData.markets.find(
        (m) => m.betpawa_market_id === marketId
      )
      bookmakerOdds.set(bookmakerData.bookmaker_slug, market ?? null)
    }

    result.set(marketId, bookmakerOdds)
  }

  return result
}

export function SummarySection({ marketsByBookmaker }: SummarySectionProps) {
  const stats = useMemo(
    () => calculateCompetitiveStats(marketsByBookmaker),
    [marketsByBookmaker]
  )

  const keyMarkets = useMemo(
    () => getKeyMarkets(marketsByBookmaker),
    [marketsByBookmaker]
  )

  // Determine competitive position color
  let positionColor = 'text-yellow-600 dark:text-yellow-400'
  let positionBg = 'bg-yellow-100 dark:bg-yellow-900/30'
  if (stats.percentage >= 60) {
    positionColor = 'text-green-600 dark:text-green-400'
    positionBg = 'bg-green-100 dark:bg-green-900/30'
  } else if (stats.percentage < 40) {
    positionColor = 'text-red-600 dark:text-red-400'
    positionBg = 'bg-red-100 dark:bg-red-900/30'
  }

  // Determine margin comparison color
  let marginColor = 'text-muted-foreground'
  if (stats.avgMarginDiff < -0.5) {
    marginColor = 'text-green-600 dark:text-green-400'
  } else if (stats.avgMarginDiff > 0.5) {
    marginColor = 'text-red-600 dark:text-red-400'
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Quick Summary</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Competitive Position */}
          <div>
            <h4 className="text-sm font-medium mb-2">Competitive Position</h4>
            <div className={cn('p-3 rounded-lg', positionBg)}>
              <div className={cn('text-2xl font-bold', positionColor)}>
                {stats.percentage.toFixed(0)}%
              </div>
              <div className="text-sm text-muted-foreground">
                {stats.bestOddsCount} / {stats.totalOutcomes} best odds
              </div>
            </div>
            <div className="mt-2 text-sm">
              <span className="text-muted-foreground">Avg margin vs competitors: </span>
              <span className={marginColor}>
                {stats.avgMarginDiff > 0 ? '+' : ''}
                {stats.avgMarginDiff.toFixed(2)}%
              </span>
            </div>
          </div>

          {/* Key Markets */}
          <div>
            <h4 className="text-sm font-medium mb-2">Key Markets</h4>
            <div className="space-y-2">
              {Object.entries(KEY_MARKETS).map(([marketId, marketName]) => {
                const bookmakerOdds = keyMarkets.get(marketId)
                const betpawaMarket = bookmakerOdds?.get('betpawa')

                if (!betpawaMarket) {
                  return (
                    <div
                      key={marketId}
                      className="flex items-center justify-between py-1 text-sm"
                    >
                      <span className="text-muted-foreground">{marketName}</span>
                      <span className="text-muted-foreground">-</span>
                    </div>
                  )
                }

                return (
                  <div
                    key={marketId}
                    className="flex items-center justify-between py-1 text-sm"
                  >
                    <span>{marketName}</span>
                    <div className="flex gap-2">
                      {betpawaMarket.outcomes.slice(0, 3).map((outcome) => (
                        <Badge
                          key={outcome.name}
                          variant="outline"
                          className="font-mono"
                        >
                          {outcome.name}: {outcome.odds.toFixed(2)}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
