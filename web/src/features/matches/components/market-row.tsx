import type { MarketOddsDetail } from '@/types/api'

// Bookmaker slugs in display order
const BOOKMAKER_ORDER = ['betpawa', 'sportybet', 'bet9ja']

interface MarketRowProps {
  marketName: string
  line: number | null
  bookmakerMarkets: Map<string, MarketOddsDetail | null>
}

interface OutcomeDisplay {
  name: string
  odds: number | null
  isActive: boolean
}

/**
 * Build a unified list of outcomes across all bookmakers for comparison.
 * Uses Betpawa outcomes as reference, falling back to first available.
 */
function getUnifiedOutcomes(
  bookmakerMarkets: Map<string, MarketOddsDetail | null>
): string[] {
  // Prefer Betpawa's outcome names as reference
  const betpawaMarket = bookmakerMarkets.get('betpawa')
  if (betpawaMarket) {
    return betpawaMarket.outcomes.map((o) => o.name)
  }

  // Fall back to first available bookmaker
  for (const slug of BOOKMAKER_ORDER) {
    const market = bookmakerMarkets.get(slug)
    if (market) {
      return market.outcomes.map((o) => o.name)
    }
  }

  return []
}

/**
 * Get outcome data for a specific bookmaker and outcome name.
 */
function getOutcomeForBookmaker(
  market: MarketOddsDetail | null,
  outcomeName: string
): OutcomeDisplay {
  if (!market) {
    return { name: outcomeName, odds: null, isActive: false }
  }

  const outcome = market.outcomes.find((o) => o.name === outcomeName)
  if (!outcome) {
    return { name: outcomeName, odds: null, isActive: false }
  }

  return {
    name: outcomeName,
    odds: outcome.odds,
    isActive: outcome.is_active,
  }
}

export function MarketRow({
  marketName,
  line,
  bookmakerMarkets,
}: MarketRowProps) {
  const outcomeNames = getUnifiedOutcomes(bookmakerMarkets)

  // Format market display name with line if present
  const displayName =
    line !== null ? `${marketName} ${line}` : marketName

  return (
    <tr className="border-b hover:bg-muted/50">
      {/* Market name column */}
      <td className="py-3 px-4 font-medium">{displayName}</td>

      {/* Outcome names column */}
      <td className="py-3 px-2 text-center">
        <div className="flex flex-col gap-1">
          {outcomeNames.map((name) => (
            <span key={name} className="text-sm text-muted-foreground">
              {name}
            </span>
          ))}
        </div>
      </td>

      {/* Bookmaker columns */}
      {BOOKMAKER_ORDER.map((slug) => {
        const market = bookmakerMarkets.get(slug) ?? null
        const margin = market?.margin

        return (
          <td key={slug} className="py-3 px-2 text-center">
            <div className="flex flex-col gap-1">
              {outcomeNames.map((outcomeName) => {
                const outcome = getOutcomeForBookmaker(market, outcomeName)
                return (
                  <span
                    key={outcomeName}
                    className={`text-sm ${
                      outcome.odds === null
                        ? 'text-muted-foreground'
                        : outcome.isActive
                        ? ''
                        : 'text-muted-foreground line-through'
                    }`}
                  >
                    {outcome.odds !== null ? outcome.odds.toFixed(2) : '-'}
                  </span>
                )
              })}
              {/* Margin display */}
              {margin !== undefined && (
                <span className="text-xs text-muted-foreground mt-1">
                  {margin.toFixed(1)}%
                </span>
              )}
            </div>
          </td>
        )
      })}
    </tr>
  )
}
