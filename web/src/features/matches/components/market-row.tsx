import { cn } from '@/lib/utils'
import type { MarketOddsDetail } from '@/types/api'
import { OddsBadge } from './odds-badge'
import { MarginIndicator } from './margin-indicator'

// Bookmaker slugs in display order
const BOOKMAKER_ORDER = ['betpawa', 'sportybet', 'bet9ja']

interface MarketRowProps {
  marketName: string
  line: number | null
  bookmakerMarkets: Map<string, MarketOddsDetail | null>
  bookmakerOrder?: string[]
  eventId?: number
  onOddsClick?: (bookmakerSlug: string, marketId: string, marketName: string) => void
  onMarginClick?: (bookmakerSlug: string, marketId: string, marketName: string) => void
}

interface OutcomeDisplay {
  name: string
  odds: number | null
  isActive: boolean
}

/**
 * Normalize outcome name for cross-bookmaker matching.
 * Different bookmakers use different separators:
 * - Betpawa: "1X - Under", "12 - Over"
 * - SportyBet/Bet9ja: "1X & Under", "12 & Over"
 */
function normalizeOutcomeName(name: string): string {
  return name
    .replace(/ - /g, ' & ')  // Betpawa uses " - ", others use " & "
    .replace(/\s+/g, ' ')    // Normalize whitespace
    .trim()
}

/**
 * Build a unified list of outcomes across all bookmakers for comparison.
 * Uses Betpawa outcomes as reference, falling back to first available.
 */
function getUnifiedOutcomes(
  bookmakerMarkets: Map<string, MarketOddsDetail | null>
): string[] {
  // Prefer Betpawa's outcome names as reference (only if has outcomes)
  const betpawaMarket = bookmakerMarkets.get('betpawa')
  if (betpawaMarket && betpawaMarket.outcomes.length > 0) {
    return betpawaMarket.outcomes.map((o) => o.name)
  }

  // Fall back to first available bookmaker with outcomes
  for (const slug of BOOKMAKER_ORDER) {
    const market = bookmakerMarkets.get(slug)
    if (market && market.outcomes.length > 0) {
      return market.outcomes.map((o) => o.name)
    }
  }

  return []
}

/**
 * Get outcome data for a specific bookmaker and outcome name.
 * Uses normalized names for matching to handle cross-bookmaker differences.
 */
function getOutcomeForBookmaker(
  market: MarketOddsDetail | null,
  outcomeName: string
): OutcomeDisplay {
  if (!market) {
    return { name: outcomeName, odds: null, isActive: false }
  }

  // Normalize the target name for matching
  const normalizedTarget = normalizeOutcomeName(outcomeName)

  // Find outcome by normalized name match
  const outcome = market.outcomes.find(
    (o) => normalizeOutcomeName(o.name) === normalizedTarget
  )
  if (!outcome) {
    return { name: outcomeName, odds: null, isActive: false }
  }

  return {
    name: outcomeName,
    odds: outcome.odds,
    isActive: outcome.is_active,
  }
}

/**
 * Determine best/worst odds for an outcome across bookmakers.
 * Uses normalized names for matching to handle cross-bookmaker differences.
 */
function getOddsComparison(
  bookmakerMarkets: Map<string, MarketOddsDetail | null>,
  outcomeName: string
): { best: number | null; worst: number | null } {
  const odds: number[] = []
  const normalizedTarget = normalizeOutcomeName(outcomeName)

  for (const slug of BOOKMAKER_ORDER) {
    const market = bookmakerMarkets.get(slug)
    if (market) {
      const outcome = market.outcomes.find(
        (o) => normalizeOutcomeName(o.name) === normalizedTarget
      )
      if (outcome && outcome.is_active && outcome.odds > 0) {
        odds.push(outcome.odds)
      }
    }
  }

  if (odds.length === 0) {
    return { best: null, worst: null }
  }

  return {
    best: Math.max(...odds),
    worst: Math.min(...odds),
  }
}

export function MarketRow({
  marketName,
  line,
  bookmakerMarkets,
  bookmakerOrder = BOOKMAKER_ORDER,
  eventId,
  onOddsClick,
  onMarginClick,
}: MarketRowProps) {
  const outcomeNames = getUnifiedOutcomes(bookmakerMarkets)

  // Get Betpawa margin for comparison
  const betpawaMarket = bookmakerMarkets.get('betpawa')
  const betpawaMargin = betpawaMarket?.margin ?? null

  // Check if Betpawa has significantly worse margin (>2% higher)
  let hasBadMargin = false
  if (betpawaMargin !== null) {
    for (const slug of ['sportybet', 'bet9ja']) {
      const competitorMarket = bookmakerMarkets.get(slug)
      if (competitorMarket && competitorMarket.margin < betpawaMargin - 2) {
        hasBadMargin = true
        break
      }
    }
  }

  // Format market display name with line if present
  const displayName =
    line !== null ? `${marketName} ${line}` : marketName

  // Get market ID from any bookmaker (prefer Betpawa)
  const marketId = betpawaMarket?.betpawa_market_id ??
    bookmakerMarkets.get('sportybet')?.betpawa_market_id ??
    bookmakerMarkets.get('bet9ja')?.betpawa_market_id ??
    ''

  return (
    <tr
      className={cn(
        'border-b hover:bg-muted/50',
        hasBadMargin && 'bg-red-50 dark:bg-red-900/10'
      )}
    >
      {/* Market name column */}
      <td className="py-3 px-4 font-medium">{displayName}</td>

      {/* Outcome names column */}
      <td className="py-3 px-2 text-center">
        <div className="flex flex-col gap-1">
          {outcomeNames.map((name) => (
            <span key={name} className="text-sm text-muted-foreground h-6 flex items-center justify-center">
              {name}
            </span>
          ))}
        </div>
      </td>

      {/* Bookmaker columns */}
      {bookmakerOrder.map((slug) => {
        const market = bookmakerMarkets.get(slug) ?? null
        const margin = market?.margin

        return (
          <td key={slug} className="py-3 px-2 text-center">
            <div className="flex flex-col gap-1">
              {outcomeNames.map((outcomeName) => {
                const outcome = getOutcomeForBookmaker(market, outcomeName)
                const comparison = getOddsComparison(bookmakerMarkets, outcomeName)
                const betpawaOutcome = getOutcomeForBookmaker(betpawaMarket ?? null, outcomeName)

                const isBest =
                  outcome.odds !== null &&
                  comparison.best !== null &&
                  outcome.odds === comparison.best &&
                  outcome.isActive

                const isWorst =
                  outcome.odds !== null &&
                  comparison.worst !== null &&
                  outcome.odds === comparison.worst &&
                  outcome.isActive &&
                  comparison.best !== comparison.worst

                // Determine if this odds cell should be clickable
                const oddsClickable = onOddsClick && eventId && market && outcome.odds !== null

                return (
                  <div key={outcomeName} className="h-6 flex items-center justify-center">
                    <OddsBadge
                      odds={outcome.odds}
                      isBest={isBest}
                      isWorst={isWorst}
                      isSuspended={!outcome.isActive && outcome.odds !== null}
                      betpawaOdds={slug !== 'betpawa' ? betpawaOutcome.odds : undefined}
                      onClick={oddsClickable ? (e) => {
                        e.stopPropagation()
                        onOddsClick(slug, marketId, displayName)
                      } : undefined}
                    />
                  </div>
                )
              })}
              {/* Margin display - only show if outcomes exist */}
              {margin !== undefined && outcomeNames.length > 0 && (
                <div className="mt-1">
                  <MarginIndicator
                    margin={margin}
                    betpawaMargin={slug !== 'betpawa' ? betpawaMargin : null}
                    onClick={onMarginClick && eventId && market ? (e) => {
                      e.stopPropagation()
                      onMarginClick(slug, marketId, displayName)
                    } : undefined}
                  />
                </div>
              )}
            </div>
          </td>
        )
      })}
    </tr>
  )
}
