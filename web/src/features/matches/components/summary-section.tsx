import { useMemo } from 'react'
import { cn } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { BookmakerMarketData, MarketOddsDetail } from '@/types/api'
import { buildDeduplicatedMarkets, formatRelativeTime, marketHasOdds } from '../lib/market-utils'

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
  snapshotTime: string | null
}

interface MappingStats {
  sportybet: number
  bet9ja: number
  total: number
}

// Tab names matching market-grid.tsx for consistent display
const TAB_NAMES: Record<string, string> = {
  popular: 'Popular',
  goals: 'Goals',
  handicaps: 'Handicaps',
  combos: 'Combos',
  halves: 'Halves',
  corners: 'Corners',
  cards: 'Cards',
  specials: 'Specials',
  other: 'Other',
}

// Display order for category breakdown (subset of full tab order)
const CATEGORY_DISPLAY_ORDER = ['popular', 'goals', 'handicaps', 'combos', 'halves', 'corners', 'cards', 'specials', 'other']

interface CategoryStats {
  category: string
  label: string
  bestOddsCount: number
  totalOutcomes: number
  percentage: number
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
 * Only counts DEDUPLICATED markets that have actual odds available.
 */
function calculateMarketCoverage(
  bookmakerMaps: Map<string, Map<string, MarketOddsDetail>>,
  marketsByBookmaker: BookmakerMarketData[]
): MarketCoverage[] {
  // Count deduplicated Betpawa markets with odds
  const betpawaMap = bookmakerMaps.get('betpawa')
  let betpawaCount = 0
  if (betpawaMap) {
    for (const market of betpawaMap.values()) {
      if (marketHasOdds(market)) {
        betpawaCount++
      }
    }
  }

  // Build a map of slug -> snapshot_time from raw data
  const snapshotTimes = new Map<string, string | null>()
  for (const bm of marketsByBookmaker) {
    snapshotTimes.set(bm.bookmaker_slug, bm.snapshot_time)
  }

  return BOOKMAKER_ORDER.map((slug) => {
    const marketMap = bookmakerMaps.get(slug)
    let count = 0
    if (marketMap) {
      for (const market of marketMap.values()) {
        if (marketHasOdds(market)) {
          count++
        }
      }
    }
    const percentage = betpawaCount > 0 ? (count / betpawaCount) * 100 : 0

    return {
      slug,
      name: BOOKMAKER_DISPLAY_NAMES[slug] ?? slug,
      count,
      percentage: slug === 'betpawa' ? 100 : percentage,
      snapshotTime: snapshotTimes.get(slug) ?? null,
    }
  })
}

/**
 * Calculate mapping stats for competitor markets.
 * Shows how many DEDUPLICATED competitor markets are matched to Betpawa taxonomy.
 */
function calculateMappingStats(
  bookmakerMaps: Map<string, Map<string, MarketOddsDetail>>
): MappingStats {
  const sportyCount = bookmakerMaps.get('sportybet')?.size ?? 0
  const bet9jaCount = bookmakerMaps.get('bet9ja')?.size ?? 0

  return {
    sportybet: sportyCount,
    bet9ja: bet9jaCount,
    total: sportyCount + bet9jaCount,
  }
}

/**
 * Calculate competitive stats for Betpawa vs competitors.
 * Uses pre-deduplicated market maps for accurate counting.
 * Categories are based on actual market_groups from data (not keyword heuristics).
 */
function calculateCompetitiveStats(
  bookmakerMaps: Map<string, Map<string, MarketOddsDetail>>
): CompetitiveStats {
  const betpawaMarketMap = bookmakerMaps.get('betpawa')
  if (!betpawaMarketMap || betpawaMarketMap.size === 0) {
    return { bestOddsCount: 0, totalOutcomes: 0, percentage: 0, avgMarginDiff: 0, byCategory: [] }
  }

  let bestOddsCount = 0
  let totalOutcomes = 0
  let marginDiffSum = 0
  let marginComparisons = 0

  // Track stats by actual market_groups from data
  const categoryStats = new Map<string, { best: number; total: number }>()

  // Iterate through Betpawa's deduplicated markets
  for (const [key, betpawaMarket] of betpawaMarketMap) {
    // Get market groups from data, default to 'other' if not present
    const marketGroups = betpawaMarket.market_groups ?? ['other']

    // Compare margins
    let competitorMarginSum = 0
    let competitorCount = 0
    for (const slug of ['sportybet', 'bet9ja']) {
      const competitorMap = bookmakerMaps.get(slug)
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

      // Add to each category the market belongs to
      for (const group of marketGroups) {
        const stats = categoryStats.get(group) ?? { best: 0, total: 0 }
        stats.total++
        categoryStats.set(group, stats)
      }

      // Find best odds across all bookmakers
      let bestOdds = betpawaOutcome.odds
      let betpawaHasBest = true

      for (const slug of ['sportybet', 'bet9ja']) {
        const competitorMap = bookmakerMaps.get(slug)
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
        // Add best count to each category the market belongs to
        for (const group of marketGroups) {
          const stats = categoryStats.get(group)
          if (stats) {
            stats.best++
          }
        }
      }
    }
  }

  const percentage =
    totalOutcomes > 0 ? (bestOddsCount / totalOutcomes) * 100 : 0
  const avgMarginDiff =
    marginComparisons > 0 ? marginDiffSum / marginComparisons : 0

  // Build category breakdown using display order, only including groups with outcomes
  const byCategory: CategoryStats[] = CATEGORY_DISPLAY_ORDER
    .filter((cat) => categoryStats.has(cat))
    .map((cat) => {
      const stats = categoryStats.get(cat)!
      return {
        category: cat,
        label: TAB_NAMES[cat] ?? cat,
        bestOddsCount: stats.best,
        totalOutcomes: stats.total,
        percentage: stats.total > 0 ? (stats.best / stats.total) * 100 : 0,
      }
    })

  // Add any unknown groups not in the display order
  const unknownGroups = [...categoryStats.keys()]
    .filter((cat) => !CATEGORY_DISPLAY_ORDER.includes(cat))
    .sort()

  for (const cat of unknownGroups) {
    const stats = categoryStats.get(cat)!
    byCategory.push({
      category: cat,
      label: TAB_NAMES[cat] ?? cat,
      bestOddsCount: stats.best,
      totalOutcomes: stats.total,
      percentage: stats.total > 0 ? (stats.best / stats.total) * 100 : 0,
    })
  }

  return { bestOddsCount, totalOutcomes, percentage, avgMarginDiff, byCategory }
}

export function SummarySection({ marketsByBookmaker }: SummarySectionProps) {
  // Build deduplicated market maps once for all calculations
  // This ensures consistent counts across all summary cards
  const bookmakerMaps = useMemo(
    () => buildDeduplicatedMarkets(marketsByBookmaker),
    [marketsByBookmaker]
  )

  const stats = useMemo(
    () => calculateCompetitiveStats(bookmakerMaps),
    [bookmakerMaps]
  )

  const marketCoverage = useMemo(
    () => calculateMarketCoverage(bookmakerMaps, marketsByBookmaker),
    [bookmakerMaps, marketsByBookmaker]
  )

  const mappingStats = useMemo(
    () => calculateMappingStats(bookmakerMaps),
    [bookmakerMaps]
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
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Market Coverage */}
          <div>
            <h4 className="text-sm font-medium mb-2">Market Coverage</h4>
            <div className="space-y-2">
              {marketCoverage.map((coverage) => {
                const isBetpawa = coverage.slug === 'betpawa'
                const relativeTime = formatRelativeTime(coverage.snapshotTime)
                return (
                  <div key={coverage.slug} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className={isBetpawa ? 'font-medium' : ''}>
                        {coverage.name}
                        {relativeTime && (
                          <span className="text-xs text-muted-foreground/70 ml-1">
                            ({relativeTime})
                          </span>
                        )}
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
              <div className="text-xs text-muted-foreground">
                matched competitor markets
              </div>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              <Badge variant="secondary" className="text-sm font-normal">
                <span className="text-muted-foreground mr-1">SportyBet:</span>
                <span className="font-medium">{mappingStats.sportybet}</span>
              </Badge>
              <Badge variant="secondary" className="text-sm font-normal">
                <span className="text-muted-foreground mr-1">Bet9ja:</span>
                <span className="font-medium">{mappingStats.bet9ja}</span>
              </Badge>
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
            <div className="mt-3 pt-2 border-t">
              <div className="grid grid-cols-2 gap-2 text-sm">
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
                      <div key={cat.category} className="flex justify-between">
                        <span className="text-muted-foreground">{cat.label}</span>
                        <span className={cn('font-medium', catColor)}>
                          {cat.percentage.toFixed(0)}%
                        </span>
                      </div>
                    )
                  })}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
