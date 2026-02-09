import type { BookmakerMarketData, MarketOddsDetail } from '@/types/api'

/**
 * Format an ISO timestamp as relative time (e.g., "2m ago").
 */
export function formatRelativeTime(isoString: string | null): string {
  if (!isoString) return ''
  // API sends UTC timestamps without 'Z' suffix - ensure correct parsing
  const normalized = isoString.endsWith('Z') ? isoString : isoString + 'Z'
  const date = new Date(normalized)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  return date.toLocaleDateString()
}

/**
 * Merge outcomes from multiple market records with the same key.
 * Some bookmakers (like Betpawa) split outcomes across multiple records.
 */
export function mergeMarketOutcomes(
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

/**
 * Build deduplicated market maps for all bookmakers.
 * Markets with the same ID+line are merged (outcomes combined).
 * Returns Map<bookmaker_slug, Map<market_key, MarketOddsDetail>>
 */
export function buildDeduplicatedMarkets(
  marketsByBookmaker: BookmakerMarketData[]
): Map<string, Map<string, MarketOddsDetail>> {
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

  return bookmakerMaps
}

/**
 * Check if a market has actual odds available.
 * A market has odds if it has at least one active outcome with odds > 0.
 */
export function marketHasOdds(market: MarketOddsDetail): boolean {
  return (
    market.outcomes &&
    market.outcomes.length > 0 &&
    market.outcomes.some((o) => o.is_active && o.odds > 0)
  )
}
