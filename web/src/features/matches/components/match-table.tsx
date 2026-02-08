import { useState, Fragment } from 'react'
import { useNavigate } from 'react-router'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import type { MatchedEvent, BookmakerOdds } from '@/types/api'
import { formatRelativeTime } from '../lib/market-utils'
import { HistoryDialog, type BookmakerInfo } from './history-dialog'

// Market IDs we display inline (Betpawa taxonomy from backend)
// 3743 = 1X2 Full Time, 5000 = Over/Under Full Time, 3795 = Both Teams To Score Full Time, 4693 = Double Chance Full Time
const MARKET_CONFIG = {
  '3743': { id: '3743', label: '1X2', outcomes: ['1', 'X', '2'] },
  '5000': { id: '5000', label: 'O/U 2.5', outcomes: ['Over', 'Under'] },
  '3795': { id: '3795', label: 'BTTS', outcomes: ['Yes', 'No'] },
  '4693': { id: '4693', label: 'DC', outcomes: ['1X', 'X2', '12'] },
} as const

type MarketId = keyof typeof MARKET_CONFIG

// Bookmaker display config
const BOOKMAKER_LABELS: Record<string, string> = {
  betpawa: 'BP',
  sportybet: 'SB',
  bet9ja: 'B9',
}

// Full bookmaker names for dialog titles
const BOOKMAKER_NAMES: Record<string, string> = {
  betpawa: 'BetPawa',
  sportybet: 'SportyBet',
  bet9ja: 'Bet9ja',
}

// State type for history dialog
interface HistoryDialogState {
  eventId: number
  marketId: string
  bookmakerSlug: string
  marketName: string
  bookmakerName: string
  allBookmakers: BookmakerInfo[]
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

// Text color classes for margin display
const TEXT_COLOR_CLASSES = {
  green: 'text-green-600 dark:text-green-400',
  red: 'text-red-600 dark:text-red-400',
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
 * Get margin for a specific market from inline odds.
 */
function getMargin(bookmaker: BookmakerOdds, marketId: string): number | null {
  const market = bookmaker.inline_odds?.find((m) => m.market_id === marketId)
  return market?.margin ?? null
}

/**
 * Compute best (lowest) margin per market across all bookmakers.
 */
function computeBestMargins(
  bookmakers: BookmakerOdds[],
  marketIds: string[]
): Record<string, number | null> {
  const bestMargins: Record<string, number | null> = {}

  for (const marketId of marketIds) {
    let best: number | null = null
    for (const bookmaker of bookmakers) {
      const margin = getMargin(bookmaker, marketId)
      if (margin !== null && (best === null || margin < best)) {
        best = margin
      }
    }
    bestMargins[marketId] = best
  }

  return bestMargins
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
  onClick,
}: {
  odds: number | null
  bookmakerSlug: string
  comparisonData: ComparisonData
  onClick?: (e: React.MouseEvent) => void
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
        isBetpawa && 'font-bold',
        onClick && 'cursor-pointer hover:ring-1 hover:ring-primary/50'
      )}
      onClick={(e) => onClick?.(e)}
    >
      {odds.toFixed(2)}
    </span>
  )
}

/**
 * Get margin comparison data for color coding.
 * Returns betpawa margin and best (lowest) competitor margin.
 */
interface MarginComparisonData {
  betpawaMargin: number | null
  bestCompetitorMargin: number | null
}

function getMarginComparisonData(
  bookmakers: BookmakerOdds[],
  marketId: string
): MarginComparisonData {
  const betpawa = bookmakers.find((b) => b.bookmaker_slug === 'betpawa')
  const betpawaMargin = betpawa ? getMargin(betpawa, marketId) : null

  let bestCompetitorMargin: number | null = null

  for (const b of bookmakers) {
    if (b.bookmaker_slug === 'betpawa') continue
    const margin = getMargin(b, marketId)
    if (margin !== null && (bestCompetitorMargin === null || margin < bestCompetitorMargin)) {
      bestCompetitorMargin = margin
    }
  }

  return { betpawaMargin, bestCompetitorMargin }
}

/**
 * Render margin cell with color coding.
 *
 * Color coding shows competitive position (like odds):
 * - Green on Betpawa: Betpawa has lower margin than competitors
 * - Red on Betpawa: Betpawa has higher margin than competitors
 * - Green on competitor: This competitor has lower margin than Betpawa
 *
 * Best margin per market gets highlighted.
 */
function MarginValue({
  margin,
  bookmakerSlug,
  comparisonData,
  isBestMargin,
  onClick,
}: {
  margin: number | null
  bookmakerSlug: string
  comparisonData: MarginComparisonData
  isBestMargin: boolean
  onClick?: (e: React.MouseEvent) => void
}) {
  if (margin === null) {
    return <span className="text-muted-foreground text-xs">-</span>
  }

  const isBetpawa = bookmakerSlug === 'betpawa'
  const { betpawaMargin, bestCompetitorMargin } = comparisonData
  const tolerance = 0.1 // 0.1% tolerance for margin comparison

  let textClass = ''

  if (isBetpawa && bestCompetitorMargin !== null && betpawaMargin !== null) {
    // Betpawa column: compare to best competitor margin
    const delta = betpawaMargin - bestCompetitorMargin

    if (delta < -tolerance) {
      // Betpawa has lower margin (good) - green
      textClass = TEXT_COLOR_CLASSES.green
    } else if (delta > tolerance) {
      // Betpawa has higher margin (bad) - red
      textClass = TEXT_COLOR_CLASSES.red
    }
  } else if (!isBetpawa && betpawaMargin !== null) {
    // Competitor column: highlight if this competitor has lower margin than Betpawa
    const delta = margin - betpawaMargin

    if (delta < -tolerance) {
      // This competitor has lower margin than Betpawa - green
      textClass = TEXT_COLOR_CLASSES.green
    }
  }

  return (
    <span
      className={cn(
        'inline-block px-1.5 py-0.5 text-xs min-w-[2.5rem] text-center',
        textClass,
        isBestMargin && 'font-bold underline',
        onClick && 'cursor-pointer hover:ring-1 hover:ring-primary/50'
      )}
      onClick={(e) => onClick?.(e)}
    >
      {margin.toFixed(1)}%
    </span>
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
  const [historyDialog, setHistoryDialog] = useState<HistoryDialogState | null>(null)

  // Get ordered list of bookmakers
  // Exclude betpawa when showing competitor-only events
  const bookmakerOrder = excludeBetpawa
    ? ['sportybet', 'bet9ja']
    : ['betpawa', 'sportybet', 'bet9ja']

  const rowsPerMatch = bookmakerOrder.length

  // Filter visible markets
  const visibleMarkets = visibleColumns.filter(
    (id) => id in MARKET_CONFIG
  ) as MarketId[]

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

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          {/* Main header row */}
          <tr className="border-b bg-muted/30">
            <th className="px-3 py-3 text-left font-medium">Region</th>
            <th className="px-3 py-3 text-left font-medium">Tournament</th>
            <th className="px-3 py-3 text-left font-medium whitespace-nowrap">Kickoff</th>
            <th className="px-3 py-3 text-left font-medium">Match</th>
            <th className="px-3 py-3 text-center font-medium w-12">Book</th>
            {/* Market group headers (outcomes + margin column) */}
            {visibleMarkets.map((marketId, index) => (
              <th
                key={marketId}
                colSpan={MARKET_CONFIG[marketId].outcomes.length + 1}
                className={cn(
                  'px-2 py-3 text-center font-medium border-l',
                  index < visibleMarkets.length - 1 && 'border-r border-r-border/50'
                )}
              >
                {MARKET_CONFIG[marketId].label}
              </th>
            ))}
          </tr>
          {/* Outcome sub-headers (with margin column per market) */}
          <tr className="border-b bg-muted/10">
            <th colSpan={5}></th>
            {visibleMarkets.map((marketId) => (
              <Fragment key={marketId}>
                {MARKET_CONFIG[marketId].outcomes.map((outcome) => (
                  <th
                    key={`${marketId}-${outcome}`}
                    className="px-2 py-2 text-xs font-medium text-muted-foreground text-center whitespace-nowrap border-l first:border-l-0"
                  >
                    {outcome}
                  </th>
                ))}
                <th
                  key={`${marketId}-margin`}
                  className="px-2 py-2 text-xs font-medium text-muted-foreground text-center whitespace-nowrap border-r border-r-border/50"
                >
                  %
                </th>
              </Fragment>
            ))}
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

            // Pre-compute best margins per market for highlighting
            const bestMargins = computeBestMargins(event.bookmakers, visibleMarkets)

            // Pre-compute margin comparison data for color coding
            const marginComparisonByMarket: Record<string, MarginComparisonData> = {}
            visibleMarkets.forEach((marketId) => {
              marginComparisonByMarket[marketId] = getMarginComparisonData(
                event.bookmakers,
                marketId
              )
            })

            // Match name format: "Team A - Team B"
            const matchName = `${event.home_team} - ${event.away_team}`

            return bookmakerOrder.map((bookmakerSlug, bookmakerIndex) => {
              const isFirstRow = bookmakerIndex === 0
              const isLastRow = bookmakerIndex === rowsPerMatch - 1
              const bookmaker = event.bookmakers.find(
                (b) => b.bookmaker_slug === bookmakerSlug
              )

              return (
                <tr
                  key={`${event.id}-${bookmakerSlug}`}
                  className={cn(
                    'hover:bg-muted/50 transition-colors',
                    isLastRow && 'border-b',
                    isCompetitorOnly
                      ? 'border-l-2 border-l-orange-500/30'
                      : 'cursor-pointer'
                  )}
                  onClick={() => {
                    // Don't navigate for competitor-only events (no detail view)
                    if (!isCompetitorOnly) {
                      navigate(`/odds-comparison/${event.id}`)
                    }
                  }}
                  title={
                    isCompetitorOnly
                      ? 'Competitor-only event - no detail view'
                      : undefined
                  }
                >
                  {/* Rowspan cells - only render on first row */}
                  {isFirstRow && (
                    <>
                      <td
                        className="px-3 py-2 text-sm text-muted-foreground align-middle"
                        rowSpan={rowsPerMatch}
                      >
                        {event.tournament_country ?? '-'}
                      </td>
                      <td
                        className="px-3 py-2 text-sm text-muted-foreground align-middle"
                        rowSpan={rowsPerMatch}
                      >
                        {event.tournament_name}
                      </td>
                      <td
                        className="px-3 py-2 whitespace-nowrap text-sm align-middle"
                        rowSpan={rowsPerMatch}
                      >
                        {formatKickoff(event.kickoff)}
                      </td>
                      <td
                        className="px-3 py-2 font-medium align-middle"
                        rowSpan={rowsPerMatch}
                      >
                        {matchName}
                      </td>
                    </>
                  )}
                  {/* Bookmaker label with timestamp */}
                  <td className="px-2 py-2 text-center">
                    <div className="text-xs font-medium text-muted-foreground">
                      {BOOKMAKER_LABELS[bookmakerSlug] || bookmakerSlug}
                    </div>
                    {bookmaker?.snapshot_time && (
                      <div className="text-[10px] text-muted-foreground/70">
                        {formatRelativeTime(bookmaker.snapshot_time)}
                      </div>
                    )}
                  </td>
                  {/* Odds cells for all markets (with margin per market) */}
                  {visibleMarkets.map((marketId) => (
                    <Fragment key={marketId}>
                      {MARKET_CONFIG[marketId].outcomes.map((outcome) => {
                        const odds = bookmaker
                          ? getOutcomeOdds(bookmaker, marketId, outcome)
                          : null
                        const comparisonData = comparisonDataByMarket[marketId][outcome]

                        return (
                          <td key={`${marketId}-${outcome}`} className="px-2 py-2 text-center">
                            <OddsValue
                              odds={odds}
                              bookmakerSlug={bookmakerSlug}
                              comparisonData={comparisonData}
                              onClick={
                                odds !== null && bookmaker
                                  ? (e: React.MouseEvent) => {
                                      e.stopPropagation()
                                      // Get all bookmakers that have this market
                                      const allBookmakers = event.bookmakers
                                        .filter((b) => {
                                          const market = b.inline_odds?.find((m) => m.market_id === marketId)
                                          return market && market.outcomes.length > 0
                                        })
                                        .map((b) => ({
                                          slug: b.bookmaker_slug,
                                          name: BOOKMAKER_NAMES[b.bookmaker_slug] ?? b.bookmaker_slug,
                                        }))
                                      setHistoryDialog({
                                        eventId: event.id,
                                        marketId,
                                        bookmakerSlug,
                                        marketName: MARKET_CONFIG[marketId].label,
                                        bookmakerName: BOOKMAKER_NAMES[bookmakerSlug] ?? bookmakerSlug,
                                        allBookmakers,
                                      })
                                    }
                                  : undefined
                              }
                            />
                          </td>
                        )
                      })}
                      {/* Margin cell for this market */}
                      <td key={`${marketId}-margin`} className="px-2 py-2 text-center border-r border-r-border/50">
                        <MarginValue
                          margin={bookmaker ? getMargin(bookmaker, marketId) : null}
                          bookmakerSlug={bookmakerSlug}
                          comparisonData={marginComparisonByMarket[marketId]}
                          isBestMargin={
                            bookmaker
                              ? getMargin(bookmaker, marketId) === bestMargins[marketId] &&
                                bestMargins[marketId] !== null
                              : false
                          }
                          onClick={
                            bookmaker && getMargin(bookmaker, marketId) !== null
                              ? (e: React.MouseEvent) => {
                                  e.stopPropagation()
                                  // Get all bookmakers that have this market
                                  const allBookmakers = event.bookmakers
                                    .filter((b) => {
                                      const market = b.inline_odds?.find((m) => m.market_id === marketId)
                                      return market && market.outcomes.length > 0
                                    })
                                    .map((b) => ({
                                      slug: b.bookmaker_slug,
                                      name: BOOKMAKER_NAMES[b.bookmaker_slug] ?? b.bookmaker_slug,
                                    }))
                                  setHistoryDialog({
                                    eventId: event.id,
                                    marketId,
                                    bookmakerSlug,
                                    marketName: MARKET_CONFIG[marketId].label,
                                    bookmakerName: BOOKMAKER_NAMES[bookmakerSlug] ?? bookmakerSlug,
                                    allBookmakers,
                                  })
                                }
                              : undefined
                          }
                        />
                      </td>
                    </Fragment>
                  ))}
                </tr>
              )
            })
          })}
        </tbody>
      </table>

      <HistoryDialog
        open={historyDialog !== null}
        onOpenChange={(open) => !open && setHistoryDialog(null)}
        eventId={historyDialog?.eventId ?? 0}
        marketId={historyDialog?.marketId ?? ''}
        bookmakerSlug={historyDialog?.bookmakerSlug ?? ''}
        marketName={historyDialog?.marketName ?? ''}
        bookmakerName={historyDialog?.bookmakerName ?? ''}
        allBookmakers={historyDialog?.allBookmakers}
      />
    </div>
  )
}
