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

// Bookmaker display names and order
const BOOKMAKER_ORDER = ['betpawa', 'sportybet', 'bet9ja'] as const
const BOOKMAKER_DISPLAY_NAMES: Record<string, string> = {
  betpawa: 'Betpawa',
  sportybet: 'SportyBet',
  bet9ja: 'Bet9ja',
}

interface MarketCoverage {
  slug: string
  name: string
  count: number
  percentage: number
}

interface MappingStats {
  sportybet: number
  bet9ja: number
  total: number
}

// Market categories based on betpawa_market_name keywords
type MarketCategory = 'main' | 'goals' | 'handicaps' | 'other'

interface CategoryStats {
  category: MarketCategory
  label: string
  bestOddsCount: number
  totalOutcomes: number
  percentage: number
}

/**
 * Determine market category based on betpawa_market_name keywords
 */
function getMarketCategory(marketName: string): MarketCategory {
  const name = marketName.toLowerCase()

  // Main markets
  if (name.includes('1x2') || name.includes('double chance') || name.includes('draw no bet')) {
    return 'main'
  }

  // Goals markets
  if (name.includes('over') || name.includes('under') || name.includes('goals') || name.includes('score')) {
    return 'goals'
  }

  // Handicap markets
  if (name.includes('handicap')) {
    return 'handicaps'
  }

  return 'other'
}

const CATEGORY_LABELS: Record<MarketCategory, string> = {
  main: 'Main',
  goals: 'Goals',
  handicaps: 'Handicaps',
  other: 'Other',
}

interface SummarySectionProps {
  marketsByBookmaker: BookmakerMarketData[]
}

interface CompetitiveStats {
  bestOddsCount: number
  totalOutcomes: number
  percentage: number
  avgMarginDiff: number
  byCategory: CategoryStats[]
}

/**
 * Calculate market coverage per bookmaker.
 * Returns array of coverage data with Betpawa as the reference (100%).
 */
function calculateMarketCoverage(
  marketsByBookmaker: BookmakerMarketData[]
): MarketCoverage[] {
  const betpawaData = marketsByBookmaker.find(
    (b) => b.bookmaker_slug === 'betpawa'
  )
  const betpawaCount = betpawaData?.markets.length ?? 0

  return BOOKMAKER_ORDER.map((slug) => {
    const bookmaker = marketsByBookmaker.find((b) => b.bookmaker_slug === slug)
    const count = bookmaker?.markets.length ?? 0
    const percentage = betpawaCount > 0 ? (count / betpawaCount) * 100 : 0

    return {
      slug,
      name: BOOKMAKER_DISPLAY_NAMES[slug] ?? slug,
      count,
      percentage: slug === 'betpawa' ? 100 : percentage,
    }
  })
}

/**
 * Calculate mapping stats for competitor markets.
 * Shows how many competitor markets are matched to Betpawa taxonomy.
 */
function calculateMappingStats(
  marketsByBookmaker: BookmakerMarketData[]
): MappingStats {
  const sportybet = marketsByBookmaker.find((b) => b.bookmaker_slug === 'sportybet')
  const bet9ja = marketsByBookmaker.find((b) => b.bookmaker_slug === 'bet9ja')

  const sportyCount = sportybet?.markets.length ?? 0
  const bet9jaCount = bet9ja?.markets.length ?? 0

  return {
    sportybet: sportyCount,
    bet9ja: bet9jaCount,
    total: sportyCount + bet9jaCount,
  }
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

  const emptyByCategory: CategoryStats[] = [
    { category: 'main', label: CATEGORY_LABELS.main, bestOddsCount: 0, totalOutcomes: 0, percentage: 0 },
    { category: 'goals', label: CATEGORY_LABELS.goals, bestOddsCount: 0, totalOutcomes: 0, percentage: 0 },
    { category: 'handicaps', label: CATEGORY_LABELS.handicaps, bestOddsCount: 0, totalOutcomes: 0, percentage: 0 },
    { category: 'other', label: CATEGORY_LABELS.other, bestOddsCount: 0, totalOutcomes: 0, percentage: 0 },
  ]

  if (!betpawaData) {
    return { bestOddsCount: 0, totalOutcomes: 0, percentage: 0, avgMarginDiff: 0, byCategory: emptyByCategory }
  }

  let bestOddsCount = 0
  let totalOutcomes = 0
  let marginDiffSum = 0
  let marginComparisons = 0

  // Track stats by category
  const categoryStats: Record<MarketCategory, { best: number; total: number }> = {
    main: { best: 0, total: 0 },
    goals: { best: 0, total: 0 },
    handicaps: { best: 0, total: 0 },
    other: { best: 0, total: 0 },
  }

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
    const category = getMarketCategory(betpawaMarket.betpawa_market_name)

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
      categoryStats[category].total++

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
        categoryStats[category].best++
      }
    }
  }

  const percentage =
    totalOutcomes > 0 ? (bestOddsCount / totalOutcomes) * 100 : 0
  const avgMarginDiff =
    marginComparisons > 0 ? marginDiffSum / marginComparisons : 0

  // Build category breakdown
  const byCategory: CategoryStats[] = (['main', 'goals', 'handicaps', 'other'] as const).map((cat) => ({
    category: cat,
    label: CATEGORY_LABELS[cat],
    bestOddsCount: categoryStats[cat].best,
    totalOutcomes: categoryStats[cat].total,
    percentage: categoryStats[cat].total > 0
      ? (categoryStats[cat].best / categoryStats[cat].total) * 100
      : 0,
  }))

  return { bestOddsCount, totalOutcomes, percentage, avgMarginDiff, byCategory }
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

  const marketCoverage = useMemo(
    () => calculateMarketCoverage(marketsByBookmaker),
    [marketsByBookmaker]
  )

  const mappingStats = useMemo(
    () => calculateMappingStats(marketsByBookmaker),
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Market Coverage */}
          <div>
            <h4 className="text-sm font-medium mb-2">Market Coverage</h4>
            <div className="space-y-2">
              {marketCoverage.map((coverage) => {
                const isBetpawa = coverage.slug === 'betpawa'
                return (
                  <div key={coverage.slug} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className={isBetpawa ? 'font-medium' : ''}>
                        {coverage.name}
                      </span>
                      <span className="text-muted-foreground">
                        {coverage.count} markets
                        {!isBetpawa && ` (${coverage.percentage.toFixed(0)}%)`}
                      </span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className={cn(
                          'h-full rounded-full transition-all',
                          isBetpawa
                            ? 'bg-primary'
                            : coverage.percentage >= 80
                              ? 'bg-green-500'
                              : coverage.percentage >= 50
                                ? 'bg-yellow-500'
                                : 'bg-red-500'
                        )}
                        style={{ width: `${Math.min(coverage.percentage, 100)}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Mapping Quality */}
          <div>
            <h4 className="text-sm font-medium mb-2">Mapping Quality</h4>
            <div className="p-3 rounded-lg bg-green-100 dark:bg-green-900/30">
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                {mappingStats.total}
              </div>
              <div className="text-sm text-muted-foreground">
                matched markets
              </div>
            </div>
            <div className="mt-2 space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">SportyBet</span>
                <span>{mappingStats.sportybet} markets</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Bet9ja</span>
                <span>{mappingStats.bet9ja} markets</span>
              </div>
            </div>
          </div>

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
            {/* Category Breakdown */}
            <div className="mt-3 pt-2 border-t text-xs">
              <div className="flex flex-wrap gap-x-3 gap-y-1">
                {stats.byCategory
                  .filter((cat) => cat.totalOutcomes > 0)
                  .map((cat) => {
                    const catColor =
                      cat.percentage >= 60
                        ? 'text-green-600 dark:text-green-400'
                        : cat.percentage < 40
                          ? 'text-red-600 dark:text-red-400'
                          : 'text-yellow-600 dark:text-yellow-400'
                    return (
                      <span key={cat.category}>
                        <span className="text-muted-foreground">{cat.label}: </span>
                        <span className={catColor}>
                          {cat.bestOddsCount}/{cat.totalOutcomes} ({cat.percentage.toFixed(0)}%)
                        </span>
                      </span>
                    )
                  })}
              </div>
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
