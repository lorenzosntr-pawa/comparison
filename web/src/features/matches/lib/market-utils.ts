/**
 * Utility functions for market data processing and display.
 *
 * @module market-utils
 * @description Provides helper functions for working with betting market data,
 * including time formatting, market deduplication, outcome merging, and
 * margin recalculation. Used primarily by the event detail and odds comparison views.
 *
 * Key functionality:
 * - Relative time formatting for snapshot timestamps
 * - Market outcome merging (handles split outcome records)
 * - Deduplicated market maps for cross-bookmaker comparison
 * - Market odds availability checking
 */

import type { BookmakerMarketData, MarketOddsDetail, InlineOdds } from '@/types/api'

/**
 * Formats an ISO timestamp as human-readable relative time.
 *
 * @description Converts timestamps to user-friendly strings like "2m ago" or "3h ago".
 * Handles API timestamps that may lack the 'Z' UTC suffix.
 *
 * @param isoString - ISO timestamp string, or null
 * @returns Formatted relative time string, or empty string if input is null
 *
 * @example
 * ```typescript
 * formatRelativeTime('2024-01-15T10:30:00Z') // "5m ago" (if 5 minutes have passed)
 * formatRelativeTime(null) // ""
 * ```
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
 * Merges outcomes from multiple market records with the same key.
 *
 * @description Some bookmakers (like Betpawa) split outcomes across multiple records.
 * This function combines them into a single market with all outcomes and recalculates
 * the margin based on the merged outcome set.
 *
 * @param existing - The existing market record to merge into
 * @param incoming - The new market record with additional outcomes
 * @returns A new MarketOddsDetail with merged outcomes and recalculated margin
 *
 * @example
 * ```typescript
 * // Market split across two records:
 * // Record 1: { outcomes: [{ name: "Home", odds: 2.0 }] }
 * // Record 2: { outcomes: [{ name: "Away", odds: 2.0 }] }
 * const merged = mergeMarketOutcomes(record1, record2)
 * // Result: { outcomes: [{ name: "Home", odds: 2.0 }, { name: "Away", odds: 2.0 }], margin: 0 }
 * ```
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
 * Builds deduplicated market maps for all bookmakers.
 *
 * @description Creates a nested map structure organizing markets by bookmaker and market key.
 * Markets with the same ID+line combination are merged (outcomes combined). This enables
 * efficient cross-bookmaker market comparison in the UI.
 *
 * @param marketsByBookmaker - Array of bookmaker market data from API
 * @returns Nested Map: bookmaker_slug -> market_key -> MarketOddsDetail
 *
 * @example
 * ```typescript
 * const deduped = buildDeduplicatedMarkets(eventDetail.markets_by_bookmaker)
 *
 * // Access betpawa's 1x2 market
 * const betpawaMarkets = deduped.get('betpawa')
 * const match1x2 = betpawaMarkets?.get('1x2')
 *
 * // Access over/under 2.5 market (with line)
 * const ouMarket = betpawaMarkets?.get('over_under_2.5')
 * ```
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
 * Checks if a market has actual odds available.
 *
 * @description Determines if a market should be displayed by checking for at least
 * one active outcome with valid odds. Markets without active outcomes or with
 * zero odds are considered unavailable.
 *
 * @param market - The market to check
 * @returns True if market has at least one active outcome with odds > 0
 *
 * @example
 * ```typescript
 * const market = bookmakerMarkets.get('1x2')
 * if (market && marketHasOdds(market)) {
 *   // Safe to render odds
 * }
 * ```
 */
export function marketHasOdds(market: MarketOddsDetail): boolean {
  return (
    market.outcomes &&
    market.outcomes.length > 0 &&
    market.outcomes.some((o) => o.is_active && o.odds > 0)
  )
}

/**
 * Formats an ISO timestamp as human-readable "Unavailable since" text.
 *
 * @description Converts timestamps to concise format for tooltip display,
 * e.g., "Unavailable since Jan 15, 10:30 AM"
 *
 * @param isoTimestamp - ISO timestamp string when market became unavailable
 * @returns Formatted string for tooltip display
 *
 * @example
 * ```typescript
 * formatUnavailableSince('2024-01-15T10:30:00Z') // "Unavailable since Jan 15, 10:30 AM"
 * ```
 */
export function formatUnavailableSince(isoTimestamp: string): string {
  // Ensure timestamp is parsed as UTC
  const normalized = isoTimestamp.endsWith('Z') ? isoTimestamp : isoTimestamp + 'Z'
  const date = new Date(normalized)

  // Use locale-aware formatting for concise tooltip display
  const formatted = new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(date)

  return `Unavailable since ${formatted}`
}

/**
 * Market availability state for UI rendering.
 *
 * - 'available': Market is currently offered with odds
 * - 'unavailable': Market was previously offered but became unavailable
 * - 'never_offered': Market was never offered by this bookmaker
 */
export type MarketAvailabilityState = 'available' | 'unavailable' | 'never_offered'

/**
 * Determines the availability state of a market.
 *
 * @description Centralizes the three-state logic for market availability,
 * enabling consistent rendering across UI components.
 *
 * @param market - InlineOdds object, or null/undefined if market not in response
 * @returns The availability state for UI rendering
 *
 * @example
 * ```typescript
 * getMarketAvailabilityState(null)                           // 'never_offered'
 * getMarketAvailabilityState(undefined)                      // 'never_offered'
 * getMarketAvailabilityState({ available: false, ... })      // 'unavailable'
 * getMarketAvailabilityState({ available: true, ... })       // 'available'
 * getMarketAvailabilityState({ ... })                        // 'available' (default)
 * ```
 */
export function getMarketAvailabilityState(
  market: InlineOdds | null | undefined
): MarketAvailabilityState {
  // Market not in response at all = never offered
  if (market === null || market === undefined) {
    return 'never_offered'
  }

  // Market explicitly marked as unavailable
  if (market.available === false) {
    return 'unavailable'
  }

  // Available (explicit true or undefined defaults to available)
  return 'available'
}
