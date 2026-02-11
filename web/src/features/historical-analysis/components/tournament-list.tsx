import { useNavigate } from 'react-router'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { TRACKED_MARKETS, type TournamentWithCount, type MarginMetrics } from '../hooks'
import { BOOKMAKER_COLORS } from './bookmaker-filter'

// Country flag emoji mapping (basic set for common countries)
const countryFlags: Record<string, string> = {
  England: 'England',
  Spain: 'Spain',
  Germany: 'Germany',
  Italy: 'Italy',
  France: 'France',
  Netherlands: 'Netherlands',
  Portugal: 'Portugal',
  Brazil: 'Brazil',
  Argentina: 'Argentina',
  Kenya: 'Kenya',
  Nigeria: 'Nigeria',
  Ghana: 'Ghana',
  'South Africa': 'South Africa',
  Uganda: 'Uganda',
  Tanzania: 'Tanzania',
}

interface TournamentListProps {
  tournaments: TournamentWithCount[]
  isLoading: boolean
  selectedBookmakers: string[]
}

/**
 * Renders a plain margin value.
 * Simplified version: no colors, no deltas, no trends.
 */
function MarginBadge({
  avgMargin,
}: {
  avgMargin: number | null
}) {
  // Negative margins indicate bad data - treat as no data
  if (avgMargin === null || avgMargin < 0) {
    return <span className="text-muted-foreground">—</span>
  }

  return (
    <span className="font-medium">
      {avgMargin.toFixed(1)}%
    </span>
  )
}

/**
 * Competitive indicator badge showing +/- vs best competitor.
 * Green if Betpawa is better (lower), red if worse (higher).
 */
function CompetitiveBadge({
  betpawaMargin,
  competitorMargin,
}: {
  betpawaMargin: number
  competitorMargin: number
}) {
  const diff = betpawaMargin - competitorMargin
  const absDiff = Math.abs(diff)

  // Don't show badge for negligible differences
  if (absDiff < 0.1) return null

  const isBetter = diff < 0
  const sign = diff > 0 ? '+' : ''

  return (
    <Badge
      variant="secondary"
      className={`ml-1 text-[10px] px-1 py-0 ${
        isBetter
          ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
          : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
      }`}
    >
      {sign}{diff.toFixed(1)}%
    </Badge>
  )
}

/**
 * Renders a per-market breakdown table showing Betpawa vs Best Competitor columns.
 * Shows competitive indicator badge for 1X2 market.
 * Always shows Best Comp. column (competitor data is always present).
 */
function MarketBreakdown({
  marginsByMarket,
  selectedBookmakers,
}: {
  marginsByMarket: Record<string, MarginMetrics>
  selectedBookmakers: string[]
}) {
  // Determine competitor column header based on selection
  const selectedCompetitors = selectedBookmakers.filter(b => b !== 'betpawa')
  const competitorCount = selectedCompetitors.length

  // Determine header text
  let competitorHeader = 'Best Comp.'
  if (competitorCount === 1) {
    // Show specific competitor name
    const competitor = selectedCompetitors[0]
    competitorHeader = competitor === 'sportybet' ? 'SportyBet' : 'Bet9ja'
  } else if (competitorCount === 0) {
    competitorHeader = '' // Will hide column
  }
  // Check if any market has data
  const hasAnyData = TRACKED_MARKETS.some(
    (market) => marginsByMarket[market.id]?.avgMargin !== null
  )

  if (!hasAnyData) {
    return (
      <span className="text-sm text-muted-foreground">No margin data</span>
    )
  }

  return (
    <div className="text-sm">
      {/* Header row */}
      <div className="flex items-center gap-2 mb-1 text-xs text-muted-foreground border-b pb-1">
        <span className="flex-1">Market</span>
        <span className="w-16 text-right flex items-center justify-end gap-1">
          <span
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: BOOKMAKER_COLORS.betpawa }}
          />
          Betpawa
        </span>
        {competitorCount > 0 && (
          <span className="w-20 text-right">{competitorHeader}</span>
        )}
      </div>

      {/* Data rows */}
      {TRACKED_MARKETS.map((market) => {
        const metrics = marginsByMarket[market.id]
        if (!metrics?.avgMargin) return null // Skip markets with no data

        // Show badge on all markets when competitors are selected
        const showCompetitiveBadge =
          competitorCount > 0 &&
          metrics.competitorAvgMargin !== null &&
          metrics.competitorAvgMargin > 0

        return (
          <div
            key={market.id}
            className="flex items-center gap-2 py-0.5"
          >
            <span className="flex-1 text-muted-foreground">
              {market.label}
              {showCompetitiveBadge && (
                <CompetitiveBadge
                  betpawaMargin={metrics.avgMargin!}
                  competitorMargin={metrics.competitorAvgMargin!}
                />
              )}
            </span>
            <span className="w-16 text-right font-medium">
              <MarginBadge avgMargin={metrics.avgMargin} />
            </span>
            {competitorCount > 0 && (
              <span className="w-20 text-right">
                <MarginBadge avgMargin={metrics.competitorAvgMargin} />
              </span>
            )}
          </div>
        )
      })}
    </div>
  )
}

function TournamentCard({
  tournament,
  selectedBookmakers,
}: {
  tournament: TournamentWithCount
  selectedBookmakers: string[]
}) {
  const navigate = useNavigate()

  const handleViewDetails = () => {
    navigate(`/historical-analysis/${tournament.id}`)
  }

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <h3 className="font-medium truncate">{tournament.name}</h3>
            <p className="text-sm text-muted-foreground">
              {tournament.country
                ? countryFlags[tournament.country] || tournament.country
                : 'International'}
            </p>
          </div>
          <Badge variant="secondary" className="shrink-0">
            {tournament.eventCount} event{tournament.eventCount !== 1 ? 's' : ''}
          </Badge>
        </div>

        {/* Metrics row */}
        <div className="mt-3">
          {/* Per-market margin breakdown */}
          <MarketBreakdown
            marginsByMarket={tournament.marginsByMarket}
            selectedBookmakers={selectedBookmakers}
          />
        </div>

        {/* View Details button */}
        <div className="mt-3 pt-3 border-t">
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            onClick={handleViewDetails}
          >
            View Details
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

function SkeletonCard() {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 space-y-2">
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
          </div>
          <Skeleton className="h-5 w-16" />
        </div>
      </CardContent>
    </Card>
  )
}

export function TournamentList({
  tournaments,
  isLoading,
  selectedBookmakers,
}: TournamentListProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    )
  }

  if (tournaments.length === 0) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <p className="text-muted-foreground">
            No tournaments with data in selected period
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {tournaments.map((tournament) => (
        <TournamentCard
          key={tournament.id}
          tournament={tournament}
          selectedBookmakers={selectedBookmakers}
        />
      ))}
    </div>
  )
}
