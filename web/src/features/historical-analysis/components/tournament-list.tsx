import { useNavigate } from 'react-router'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { TRACKED_MARKETS, type TournamentWithCount, type MarginMetrics } from '../hooks'

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
 * Format margin delta with sign and color.
 */
function DeltaDisplay({ delta }: { delta: number }) {
  // Color: green if negative (improved), red if positive (worsened), muted if ~zero
  const isImproved = delta < -0.1
  const isWorsened = delta > 0.1
  const sign = delta > 0 ? '+' : ''

  return (
    <span
      className={
        isImproved
          ? 'text-green-600 dark:text-green-400'
          : isWorsened
            ? 'text-red-600 dark:text-red-400'
            : 'text-muted-foreground'
      }
    >
      ({sign}{delta.toFixed(1)}%)
    </span>
  )
}

/**
 * Renders a per-market breakdown grid showing metrics for each tracked market.
 */
function MarketBreakdown({
  marginsByMarket,
}: {
  marginsByMarket: Record<string, MarginMetrics>
}) {
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
    <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
      {TRACKED_MARKETS.map((market) => {
        const metrics = marginsByMarket[market.id]
        if (!metrics?.avgMargin) return null // Skip markets with no data

        const hasOpeningClosing =
          metrics.openingMargin !== null &&
          metrics.closingMargin !== null &&
          metrics.marginDelta !== null

        return (
          <div key={market.id} className="space-y-0.5">
            <div className="flex items-center justify-between gap-2">
              <span className="text-muted-foreground">{market.label}:</span>
              <MarginBadge avgMargin={metrics.avgMargin} />
            </div>
            {hasOpeningClosing && (
              <div className="text-xs text-muted-foreground flex items-center gap-1">
                <span>
                  {metrics.openingMargin!.toFixed(1)}% → {metrics.closingMargin!.toFixed(1)}%
                </span>
                <DeltaDisplay delta={metrics.marginDelta!} />
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

function TournamentCard({ tournament }: { tournament: TournamentWithCount }) {
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
          <MarketBreakdown marginsByMarket={tournament.marginsByMarket} />
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

export function TournamentList({ tournaments, isLoading }: TournamentListProps) {
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
        <TournamentCard key={tournament.id} tournament={tournament} />
      ))}
    </div>
  )
}
