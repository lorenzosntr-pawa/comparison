import type { BookmakerMarketData, MarketOddsDetail } from '@/types/api'
import { MarketRow } from './market-row'

// Bookmaker slugs in display order
const BOOKMAKER_ORDER = ['betpawa', 'sportybet', 'bet9ja']
const BOOKMAKER_NAMES: Record<string, string> = {
  betpawa: 'Betpawa',
  sportybet: 'SportyBet',
  bet9ja: 'Bet9ja',
}

// Market groups for visual organization (for future use)
// const MARKET_GROUPS: Record<string, string[]> = {
//   Main: ['1X2', 'Double Chance', 'Draw No Bet'],
//   Goals: ['Over/Under', 'Both Teams to Score', 'Total Goals', 'Team Goals'],
//   Handicaps: ['Asian Handicap', 'European Handicap', 'Handicap'],
// }

interface MarketGridProps {
  marketsByBookmaker: BookmakerMarketData[]
}

interface UnifiedMarket {
  id: string
  name: string
  line: number | null
  bookmakerMarkets: Map<string, MarketOddsDetail | null>
}

/**
 * Build a unified list of markets from all bookmakers.
 * Uses Betpawa as the reference taxonomy.
 */
/**
 * Merge outcomes from multiple market records with the same key.
 * Some bookmakers (like Betpawa) split outcomes across multiple records.
 */
function mergeMarketOutcomes(
  existing: MarketOddsDetail,
  incoming: MarketOddsDetail
): MarketOddsDetail {
  // Merge outcomes, avoiding duplicates by name
  const existingNames = new Set(existing.outcomes.map((o) => o.name))
  const mergedOutcomes = [
    ...existing.outcomes,
    ...incoming.outcomes.filter((o) => !existingNames.has(o.name)),
  ]

  // Recalculate margin with all outcomes
  let margin = 0
  try {
    const totalImpliedProb = mergedOutcomes.reduce((sum, o) => {
      if (o.odds > 0 && o.is_active) {
        return sum + 1 / o.odds
      }
      return sum
    }, 0)
    if (totalImpliedProb > 0) {
      margin = Math.round((totalImpliedProb - 1) * 100 * 100) / 100
    }
  } catch {
    margin = existing.margin
  }

  return {
    ...existing,
    outcomes: mergedOutcomes,
    margin,
  }
}

function buildUnifiedMarkets(
  marketsByBookmaker: BookmakerMarketData[]
): UnifiedMarket[] {
  // Create a map of bookmaker slug -> markets by market key
  // Markets with the same key have their outcomes merged
  const bookmakerMaps = new Map<string, Map<string, MarketOddsDetail>>()

  for (const bookmakerData of marketsByBookmaker) {
    const marketMap = new Map<string, MarketOddsDetail>()
    for (const market of bookmakerData.markets) {
      // Create a unique key for each market (id + line)
      const key =
        market.line !== null
          ? `${market.betpawa_market_id}_${market.line}`
          : market.betpawa_market_id

      // Merge outcomes if market already exists (same id+line)
      const existing = marketMap.get(key)
      if (existing) {
        marketMap.set(key, mergeMarketOutcomes(existing, market))
      } else {
        marketMap.set(key, market)
      }
    }
    bookmakerMaps.set(bookmakerData.bookmaker_slug, marketMap)
  }

  // Collect all unique market keys across all bookmakers
  const allMarketKeys = new Set<string>()
  for (const [, marketMap] of bookmakerMaps) {
    for (const key of marketMap.keys()) {
      allMarketKeys.add(key)
    }
  }

  const unifiedMarkets: UnifiedMarket[] = []

  // First add Betpawa markets (they define the reference)
  // Use the deduplicated map instead of raw markets to avoid duplicate rows
  const betpawaMap = bookmakerMaps.get('betpawa')
  if (betpawaMap) {
    for (const [key, market] of betpawaMap) {
      const bookmakerMarkets = new Map<string, MarketOddsDetail | null>()
      for (const slug of BOOKMAKER_ORDER) {
        const bMap = bookmakerMaps.get(slug)
        bookmakerMarkets.set(slug, bMap?.get(key) ?? null)
      }

      unifiedMarkets.push({
        id: market.betpawa_market_id,
        name: market.betpawa_market_name,
        line: market.line,
        bookmakerMarkets,
      })
      allMarketKeys.delete(key)
    }
  }

  // Add remaining markets from other bookmakers that Betpawa doesn't have
  for (const key of allMarketKeys) {
    // Find first bookmaker that has this market
    let referenceMarket: MarketOddsDetail | undefined
    for (const slug of BOOKMAKER_ORDER) {
      const bMap = bookmakerMaps.get(slug)
      referenceMarket = bMap?.get(key)
      if (referenceMarket) break
    }

    if (referenceMarket) {
      const bookmakerMarkets = new Map<string, MarketOddsDetail | null>()
      for (const slug of BOOKMAKER_ORDER) {
        const bMap = bookmakerMaps.get(slug)
        bookmakerMarkets.set(slug, bMap?.get(key) ?? null)
      }

      unifiedMarkets.push({
        id: referenceMarket.betpawa_market_id,
        name: referenceMarket.betpawa_market_name,
        line: referenceMarket.line,
        bookmakerMarkets,
      })
    }
  }

  return unifiedMarkets
}

export function MarketGrid({ marketsByBookmaker }: MarketGridProps) {
  const unifiedMarkets = buildUnifiedMarkets(marketsByBookmaker)

  if (unifiedMarkets.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No market data available for this match.
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b bg-muted/50">
            <th className="py-3 px-4 text-left font-semibold">Market</th>
            <th className="py-3 px-2 text-center font-semibold">Selection</th>
            {BOOKMAKER_ORDER.map((slug) => (
              <th key={slug} className="py-3 px-2 text-center font-semibold">
                {BOOKMAKER_NAMES[slug]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {unifiedMarkets.map((market, index) => (
            <MarketRow
              key={`${market.id}_${market.line ?? 'null'}_${index}`}
              marketName={market.name}
              line={market.line}
              bookmakerMarkets={market.bookmakerMarkets}
            />
          ))}
        </tbody>
      </table>
    </div>
  )
}
