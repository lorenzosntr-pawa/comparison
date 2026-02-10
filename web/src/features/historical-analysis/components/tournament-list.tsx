import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import type { TournamentWithCount } from '../hooks'

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

/** Bookmaker color configuration for coverage bar */
const BOOKMAKER_COLORS: Record<string, { bg: string; label: string }> = {
  betpawa: { bg: 'bg-blue-500', label: 'Betpawa' },
  sportybet: { bg: 'bg-green-500', label: 'SportyBet' },
  bet9ja: { bg: 'bg-orange-500', label: 'Bet9ja' },
}

/** Ordered list of bookmakers for consistent display */
const BOOKMAKER_ORDER = ['betpawa', 'sportybet', 'bet9ja']

interface TournamentListProps {
  tournaments: TournamentWithCount[]
  isLoading: boolean
}

/**
 * Renders a trend arrow indicator.
 */
function TrendIndicator({ trend }: { trend: 'up' | 'down' | 'stable' | null }) {
  if (trend === null) return null

  if (trend === 'up') {
    // Worsening - red arrow up
    return (
      <span className="text-red-500 text-xs" title="Margins increasing">
        ▲
      </span>
    )
  }
  if (trend === 'down') {
    // Improving - green arrow down
    return (
      <span className="text-green-500 text-xs" title="Margins decreasing">
        ▼
      </span>
    )
  }
  // Stable - gray dash
  return (
    <span className="text-muted-foreground text-xs" title="Stable margins">
      —
    </span>
  )
}

/**
 * Renders a coverage bar showing bookmaker coverage percentages.
 */
function CoverageBar({
  coverageByBookmaker,
}: {
  coverageByBookmaker: Record<string, number>
}) {
  const hasAnyCoverage = BOOKMAKER_ORDER.some(
    (slug) => (coverageByBookmaker[slug] ?? 0) > 0
  )

  if (!hasAnyCoverage) return null

  const tooltipContent = BOOKMAKER_ORDER.map((slug) => {
    const coverage = coverageByBookmaker[slug] ?? 0
    const config = BOOKMAKER_COLORS[slug]
    return `${config?.label ?? slug}: ${coverage.toFixed(0)}%`
  }).join(' | ')

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div className="flex h-2 w-full overflow-hidden rounded-full bg-muted">
          {BOOKMAKER_ORDER.map((slug) => {
            const coverage = coverageByBookmaker[slug] ?? 0
            if (coverage === 0) return null
            const config = BOOKMAKER_COLORS[slug]
            return (
              <div
                key={slug}
                className={`${config?.bg ?? 'bg-gray-500'} h-full`}
                style={{ width: `${Math.min(coverage, 100) / 3}%` }}
              />
            )
          })}
        </div>
      </TooltipTrigger>
      <TooltipContent>
        <p className="text-xs">{tooltipContent}</p>
      </TooltipContent>
    </Tooltip>
  )
}

/**
 * Renders a margin badge with comparison coloring.
 */
function MarginBadge({
  avgMargin,
  competitorAvgMargin,
  trend,
}: {
  avgMargin: number | null
  competitorAvgMargin: number | null
  trend: 'up' | 'down' | 'stable' | null
}) {
  if (avgMargin === null) {
    return (
      <span className="text-sm text-muted-foreground flex items-center gap-1">
        BP: —
      </span>
    )
  }

  // Determine color based on comparison
  let colorClass = 'text-foreground' // neutral
  if (competitorAvgMargin !== null) {
    if (avgMargin < competitorAvgMargin) {
      colorClass = 'text-green-600 dark:text-green-400' // Better than competitors
    } else if (avgMargin > competitorAvgMargin) {
      colorClass = 'text-red-600 dark:text-red-400' // Worse than competitors
    }
  }

  // Calculate delta if competitor data available
  const delta =
    competitorAvgMargin !== null ? avgMargin - competitorAvgMargin : null

  return (
    <span className={`text-sm font-medium flex items-center gap-1 ${colorClass}`}>
      <span>BP: {avgMargin.toFixed(1)}%</span>
      {delta !== null && (
        <span className="text-xs opacity-75">
          ({delta > 0 ? '+' : ''}
          {delta.toFixed(1)}%)
        </span>
      )}
      <TrendIndicator trend={trend} />
    </span>
  )
}

function TournamentCard({ tournament }: { tournament: TournamentWithCount }) {
  const handleClick = () => {
    // Placeholder for future drill-down
    console.log('Tournament clicked:', tournament.id, tournament.name)
  }

  return (
    <Card
      className="cursor-pointer transition-colors hover:bg-muted/50"
      onClick={handleClick}
    >
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
        <div className="mt-3 space-y-2">
          {/* Margin with trend */}
          <MarginBadge
            avgMargin={tournament.avgMargin}
            competitorAvgMargin={tournament.competitorAvgMargin}
            trend={tournament.trend}
          />

          {/* Coverage bar */}
          <CoverageBar coverageByBookmaker={tournament.coverageByBookmaker} />
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
    <TooltipProvider>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {tournaments.map((tournament) => (
          <TournamentCard key={tournament.id} tournament={tournament} />
        ))}
      </div>
    </TooltipProvider>
  )
}
