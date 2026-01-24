import { useNavigate } from 'react-router'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import type { MatchedEvent, BookmakerOdds } from '@/types/api'

// Market IDs we display inline (Betpawa taxonomy from backend)
// 3743 = 1X2 Full Time, 5000 = Over/Under Full Time, 3795 = Both Teams To Score Full Time
const MARKET_CONFIG = {
  '3743': { id: '3743', label: '1X2', outcomes: ['1', 'X', '2'] },
  '5000': { id: '5000', label: 'O/U 2.5', outcomes: ['Over', 'Under'] },
  '3795': { id: '3795', label: 'BTTS', outcomes: ['Yes', 'No'] },
} as const

// Bookmaker display config
const BOOKMAKER_LABELS: Record<string, string> = {
  betpawa: 'BP',
  sportybet: 'SB',
  bet9ja: 'B9',
}

// Static color classes for Tailwind JIT compilation
// Dynamic classes like `bg-green-500/${opacity}` don't work with Tailwind JIT
const COLOR_CLASSES = {
  green: {
    10: 'bg-green-500/10',
    20: 'bg-green-500/20',
    30: 'bg-green-500/30',
    40: 'bg-green-500/40',
    50: 'bg-green-500/50',
  },
  red: {
    10: 'bg-red-500/10',
    20: 'bg-red-500/20',
    30: 'bg-red-500/30',
    40: 'bg-red-500/40',
    50: 'bg-red-500/50',
  },
} as const

type OpacityLevel = 10 | 20 | 30 | 40 | 50

interface MatchTableProps {
  events: MatchedEvent[]
  isLoading?: boolean
  visibleColumns?: string[]
  excludeBetpawa?: boolean
}

/**
 * Get odds value for a specific outcome from inline odds.
 */
function getOutcomeOdds(
  bookmaker: BookmakerOdds,
  marketId: string,
  outcomeName: string
): number | null {
  const market = bookmaker.inline_odds?.find((m) => m.market_id === marketId)
  if (!market) return null

  const outcome = market.outcomes.find((o) =>
    o.name.toLowerCase() === outcomeName.toLowerCase() ||
    o.name === outcomeName
  )
  return outcome?.odds ?? null
}

/**
 * Get comparison data for color coding.
 * Returns betpawa odds and best competitor info.
 */
interface ComparisonData {
  betpawaOdds: number | null
  bestCompetitorOdds: number | null
  bestCompetitorSlug: string | null
}

function getComparisonData(
  bookmakers: BookmakerOdds[],
  marketId: string,
  outcomeName: string
): ComparisonData {
  const betpawa = bookmakers.find((b) => b.bookmaker_slug === 'betpawa')
  const betpawaOdds = betpawa ? getOutcomeOdds(betpawa, marketId, outcomeName) : null

  let bestCompetitorOdds: number | null = null
  let bestCompetitorSlug: string | null = null

  for (const b of bookmakers) {
    if (b.bookmaker_slug === 'betpawa') continue
    const odds = getOutcomeOdds(b, marketId, outcomeName)
    if (odds !== null && (bestCompetitorOdds === null || odds > bestCompetitorOdds)) {
      bestCompetitorOdds = odds
      bestCompetitorSlug = b.bookmaker_slug
    }
  }

  return { betpawaOdds, bestCompetitorOdds, bestCompetitorSlug }
}

/**
 * Render a single odds cell with color coding.
 *
 * Color coding shows competitive position:
 * - Green on Betpawa: Betpawa has best odds
 * - Red on Betpawa: Betpawa is worse than competitor
 * - Green on competitor: This competitor beats Betpawa (has better odds)
 */
function OddsValue({
  odds,
  bookmakerSlug,
  comparisonData,
}: {
  odds: number | null
  bookmakerSlug: string
  comparisonData: ComparisonData
}) {
  if (odds === null) {
    return <span className="text-muted-foreground text-xs">-</span>
  }

  const isBetpawa = bookmakerSlug === 'betpawa'
  const { betpawaOdds, bestCompetitorOdds } = comparisonData
  const tolerance = 0.02

  let bgClass = ''

  if (isBetpawa && bestCompetitorOdds !== null && betpawaOdds !== null) {
    // Betpawa column: compare to best competitor
    const delta = betpawaOdds - bestCompetitorOdds

    if (Math.abs(delta) > tolerance) {
      const intensity = Math.min(Math.abs(delta) * 25, 1)
      const opacityLevel = Math.min(
        Math.max(Math.ceil(intensity * 5) * 10, 10),
        50
      ) as OpacityLevel
      // Green if Betpawa is better, red if worse
      const color = delta > tolerance ? 'green' : 'red'
      bgClass = COLOR_CLASSES[color][opacityLevel]
    }
  } else if (!isBetpawa && betpawaOdds !== null) {
    // Competitor column: highlight if this competitor beats Betpawa
    const delta = odds - betpawaOdds

    if (delta > tolerance) {
      // This competitor has better odds than Betpawa - highlight in green
      const intensity = Math.min(delta * 25, 1)
      const opacityLevel = Math.min(
        Math.max(Math.ceil(intensity * 5) * 10, 10),
        50
      ) as OpacityLevel
      bgClass = COLOR_CLASSES.green[opacityLevel]
    }
  }

  return (
    <span
      className={cn(
        'inline-block px-1.5 py-0.5 rounded text-xs font-medium min-w-[2.5rem] text-center',
        bgClass,
        isBetpawa && 'font-bold'
      )}
    >
      {odds.toFixed(2)}
    </span>
  )
}

/**
 * Render market odds header (outcome names).
 */
function MarketHeader({ marketId }: { marketId: string }) {
  const config = MARKET_CONFIG[marketId as keyof typeof MARKET_CONFIG]
  if (!config) return null

  return (
    <>
      {config.outcomes.map((outcome) => (
        <th
          key={outcome}
          className="px-2 py-2 text-xs font-medium text-muted-foreground text-center whitespace-nowrap"
        >
          {outcome}
        </th>
      ))}
    </>
  )
}

/**
 * Render market odds cells for a bookmaker.
 */
function MarketCells({
  bookmaker,
  marketId,
  comparisonDataByOutcome,
}: {
  bookmaker: BookmakerOdds | undefined
  marketId: string
  comparisonDataByOutcome: Record<string, ComparisonData>
}) {
  const config = MARKET_CONFIG[marketId as keyof typeof MARKET_CONFIG]
  if (!config) return null

  const bookmakerSlug = bookmaker?.bookmaker_slug ?? ''

  return (
    <>
      {config.outcomes.map((outcome) => {
        const odds = bookmaker ? getOutcomeOdds(bookmaker, marketId, outcome) : null
        const comparisonData = comparisonDataByOutcome[outcome]

        return (
          <td key={outcome} className="px-2 py-2 text-center">
            <OddsValue
              odds={odds}
              bookmakerSlug={bookmakerSlug}
              comparisonData={comparisonData}
            />
          </td>
        )
      })}
    </>
  )
}

/**
 * Format kickoff time for display.
 */
function formatKickoff(kickoff: string): string {
  const date = new Date(kickoff)
  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()
  const isTomorrow =
    date.toDateString() === new Date(now.getTime() + 86400000).toDateString()

  const timeStr = date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })

  if (isToday) {
    return `Today ${timeStr}`
  }
  if (isTomorrow) {
    return `Tomorrow ${timeStr}`
  }

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

export function MatchTable({ events, isLoading, visibleColumns = ['3743', '5000', '3795'], excludeBetpawa = false }: MatchTableProps) {
  const navigate = useNavigate()

  // Get ordered list of bookmakers from first event
  // Exclude betpawa when showing competitor-only events
  const bookmakerOrder = excludeBetpawa
    ? ['sportybet', 'bet9ja']
    : ['betpawa', 'sportybet', 'bet9ja']

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3, 4, 5].map((i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    )
  }

  if (events.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No matches found. Try adjusting your filters.
      </div>
    )
  }

  // Filter visible markets
  const visibleMarkets = visibleColumns.filter(
    (id) => id in MARKET_CONFIG
  ) as (keyof typeof MARKET_CONFIG)[]

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b">
            <th className="px-3 py-3 text-left font-medium">Match</th>
            <th className="px-3 py-3 text-left font-medium whitespace-nowrap">Kickoff</th>
            <th className="px-3 py-3 text-left font-medium">Tournament</th>
            <th className="px-3 py-3 text-left font-medium">Region</th>
            {/* Market columns grouped by bookmaker */}
            {visibleMarkets.map((marketId) => (
              <th
                key={marketId}
                colSpan={MARKET_CONFIG[marketId].outcomes.length * bookmakerOrder.length}
                className="px-2 py-2 text-center font-medium border-l"
              >
                {MARKET_CONFIG[marketId].label}
              </th>
            ))}
          </tr>
          {/* Sub-header with bookmaker labels and outcomes */}
          <tr className="border-b bg-muted/30">
            <th colSpan={4}></th>
            {visibleMarkets.map((marketId) =>
              bookmakerOrder.map((slug) => (
                <th
                  key={`${marketId}-${slug}-header`}
                  colSpan={MARKET_CONFIG[marketId].outcomes.length}
                  className="px-2 py-1 text-xs font-medium text-center border-l first:border-l-0"
                >
                  {BOOKMAKER_LABELS[slug] || slug}
                </th>
              ))
            )}
          </tr>
          {/* Outcome headers */}
          <tr className="border-b bg-muted/10">
            <th colSpan={4}></th>
            {visibleMarkets.map((marketId) =>
              bookmakerOrder.map((slug) => (
                <MarketHeader key={`${marketId}-${slug}-outcomes`} marketId={marketId} />
              ))
            )}
          </tr>
        </thead>
        <tbody>
          {events.map((event) => {
            // Check if this is a competitor-only event (negative ID)
            const isCompetitorOnly = event.id < 0

            // Pre-compute comparison data for color coding
            const comparisonDataByMarket: Record<string, Record<string, ComparisonData>> = {}
            visibleMarkets.forEach((marketId) => {
              comparisonDataByMarket[marketId] = {}
              MARKET_CONFIG[marketId].outcomes.forEach((outcome) => {
                comparisonDataByMarket[marketId][outcome] = getComparisonData(
                  event.bookmakers,
                  marketId,
                  outcome
                )
              })
            })

            return (
              <tr
                key={event.id}
                className={cn(
                  'border-b hover:bg-muted/50 transition-colors',
                  isCompetitorOnly
                    ? 'border-l-2 border-l-orange-500/30'
                    : 'cursor-pointer'
                )}
                onClick={() => {
                  // Don't navigate for competitor-only events (no detail view)
                  if (!isCompetitorOnly) {
                    navigate(`/matches/${event.id}`)
                  }
                }}
                title={
                  isCompetitorOnly
                    ? 'Competitor-only event - no detail view'
                    : undefined
                }
              >
                <td className="px-3 py-3">
                  <div className="font-medium">{event.home_team}</div>
                  <div className="text-muted-foreground text-xs">vs {event.away_team}</div>
                </td>
                <td className="px-3 py-3 whitespace-nowrap text-sm">
                  {formatKickoff(event.kickoff)}
                </td>
                <td className="px-3 py-3 text-sm text-muted-foreground">
                  {event.tournament_name}
                </td>
                <td className="px-3 py-3 text-sm text-muted-foreground">
                  {event.tournament_country ?? '-'}
                </td>
                {/* Market cells */}
                {visibleMarkets.map((marketId) =>
                  bookmakerOrder.map((slug) => {
                    const bookmaker = event.bookmakers.find(
                      (b) => b.bookmaker_slug === slug
                    )
                    return (
                      <MarketCells
                        key={`${event.id}-${marketId}-${slug}`}
                        bookmaker={bookmaker}
                        marketId={marketId}
                        comparisonDataByOutcome={comparisonDataByMarket[marketId]}
                      />
                    )
                  })
                )}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
