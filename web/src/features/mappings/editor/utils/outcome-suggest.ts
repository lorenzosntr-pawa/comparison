/**
 * Auto-suggest algorithm for outcome mappings.
 *
 * Analyzes sample_outcomes from source market data and suggests canonical
 * outcome mappings with platform-specific field population.
 */

export type SourcePlatform = 'sportybet' | 'bet9ja'

export interface SuggestedOutcome {
  /** Suggested canonical ID (e.g., 'home', 'draw', 'over') */
  canonicalId: string
  /** Betpawa outcome name */
  betpawaName: string | null
  /** SportyBet outcome description */
  sportybetDesc: string | null
  /** Bet9ja outcome suffix */
  bet9jaSuffix: string | null
  /** Position in outcome list (0-indexed) */
  position: number
  /** Confidence level of the suggestion */
  confidence: 'high' | 'medium' | 'low'
  /** Original value that triggered this suggestion */
  source: string
}

/**
 * Known canonical patterns for outcome matching.
 * Each pattern maps display values to canonical IDs.
 */
const CANONICAL_PATTERNS: Record<string, string[]> = {
  // 1X2 / Match Result
  home: ['home', '1', 'h', 'home win', 'home team', 'w1'],
  draw: ['draw', 'x', 'd', 'tie'],
  away: ['away', '2', 'a', 'away win', 'away team', 'w2'],

  // Over/Under
  over: ['over', 'o', '+', 'more'],
  under: ['under', 'u', '-', 'less'],

  // Yes/No (e.g., Both Teams to Score)
  yes: ['yes', 'y', 'gg', 'btts yes'],
  no: ['no', 'n', 'ng', 'btts no'],

  // Double Chance
  '1x': ['1x', 'home or draw', 'home/draw'],
  '12': ['12', 'home or away', 'home/away', 'no draw'],
  x2: ['x2', '2x', 'draw or away', 'away/draw', 'away or draw'],

  // Odd/Even
  odd: ['odd', 'odd goals'],
  even: ['even', 'even goals'],
}

/**
 * Normalizes a string for pattern matching.
 * Converts to lowercase, trims whitespace, removes extra spaces.
 */
function normalize(value: string): string {
  return value.toLowerCase().trim().replace(/\s+/g, ' ')
}

/**
 * Extracts a displayable name/description from a sample outcome object.
 * Handles different platform-specific structures.
 */
function extractOutcomeValue(
  outcome: Record<string, unknown>,
  platform: SourcePlatform
): string | null {
  // SportyBet typically uses 'desc' or 'name' fields
  if (platform === 'sportybet') {
    if (typeof outcome.desc === 'string' && outcome.desc) {
      return outcome.desc
    }
    if (typeof outcome.name === 'string' && outcome.name) {
      return outcome.name
    }
  }

  // Bet9ja typically uses 'name', 'suffix', or 'key' fields
  if (platform === 'bet9ja') {
    if (typeof outcome.name === 'string' && outcome.name) {
      return outcome.name
    }
    if (typeof outcome.suffix === 'string' && outcome.suffix) {
      return outcome.suffix
    }
    if (typeof outcome.key === 'string' && outcome.key) {
      // Extract suffix from key like "S_1X2_1" -> "1"
      const parts = outcome.key.split('_')
      if (parts.length > 0) {
        return parts[parts.length - 1]
      }
    }
  }

  // Fallback: try common field names
  for (const field of ['desc', 'name', 'value', 'label', 'suffix']) {
    if (typeof outcome[field] === 'string' && outcome[field]) {
      return outcome[field] as string
    }
  }

  return null
}

/**
 * Matches an outcome value against canonical patterns.
 * Returns the canonical ID and confidence level.
 */
function matchCanonicalPattern(value: string): {
  canonicalId: string
  confidence: 'high' | 'medium' | 'low'
} {
  const normalizedValue = normalize(value)

  // First pass: exact match (high confidence)
  for (const [canonicalId, patterns] of Object.entries(CANONICAL_PATTERNS)) {
    for (const pattern of patterns) {
      if (normalizedValue === pattern) {
        return { canonicalId, confidence: 'high' }
      }
    }
  }

  // Second pass: contains match (medium confidence)
  for (const [canonicalId, patterns] of Object.entries(CANONICAL_PATTERNS)) {
    for (const pattern of patterns) {
      if (
        normalizedValue.includes(pattern) ||
        pattern.includes(normalizedValue)
      ) {
        return { canonicalId, confidence: 'medium' }
      }
    }
  }

  // No match: use sanitized original value as canonical ID (low confidence)
  const sanitizedId = normalizedValue
    .replace(/[^a-z0-9]/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_|_$/g, '')

  return {
    canonicalId: sanitizedId || `outcome_${Date.now()}`,
    confidence: 'low',
  }
}

/**
 * Suggests outcome mappings from sample outcome data.
 *
 * @param sampleOutcomes - Array of raw sample outcome objects from scraping
 * @param sourcePlatform - The source platform ('sportybet' or 'bet9ja')
 * @returns Array of suggested outcome mappings
 */
export function suggestOutcomes(
  sampleOutcomes: Array<Record<string, unknown>> | null,
  sourcePlatform: SourcePlatform
): SuggestedOutcome[] {
  // Handle null/empty input
  if (!sampleOutcomes || sampleOutcomes.length === 0) {
    return []
  }

  const suggestions: SuggestedOutcome[] = []
  const seenCanonicalIds = new Set<string>()

  for (let i = 0; i < sampleOutcomes.length; i++) {
    const outcome = sampleOutcomes[i]
    const value = extractOutcomeValue(outcome, sourcePlatform)

    if (!value) {
      // Skip outcomes we can't extract a value from
      continue
    }

    const { canonicalId: rawCanonicalId, confidence } =
      matchCanonicalPattern(value)

    // Handle duplicate canonical IDs by appending position suffix
    let canonicalId = rawCanonicalId
    if (seenCanonicalIds.has(canonicalId)) {
      canonicalId = `${rawCanonicalId}_${i}`
    }
    seenCanonicalIds.add(canonicalId)

    // Build the suggestion with platform-specific field populated
    const suggestion: SuggestedOutcome = {
      canonicalId,
      betpawaName: null,
      sportybetDesc: sourcePlatform === 'sportybet' ? value : null,
      bet9jaSuffix: sourcePlatform === 'bet9ja' ? value : null,
      position: i,
      confidence,
      source: value,
    }

    suggestions.push(suggestion)
  }

  return suggestions
}

/**
 * Converts suggested outcomes to form items format.
 * Strips the 'confidence' and 'source' fields used for UI hints.
 */
export interface OutcomeFormItem {
  canonicalId: string
  betpawaName: string | null
  sportybetDesc: string | null
  bet9jaSuffix: string | null
  position: number
}

export function suggestionsToFormItems(
  suggestions: SuggestedOutcome[]
): OutcomeFormItem[] {
  return suggestions.map((s) => ({
    canonicalId: s.canonicalId,
    betpawaName: s.betpawaName,
    sportybetDesc: s.sportybetDesc,
    bet9jaSuffix: s.bet9jaSuffix,
    position: s.position,
  }))
}

/**
 * Creates a new empty outcome form item at a given position.
 */
export function createEmptyOutcomeItem(position: number): OutcomeFormItem {
  return {
    canonicalId: '',
    betpawaName: null,
    sportybetDesc: null,
    bet9jaSuffix: null,
    position,
  }
}
