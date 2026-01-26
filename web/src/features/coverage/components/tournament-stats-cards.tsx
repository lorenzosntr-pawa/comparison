import { useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import type { TournamentGroup } from '@/types/api'
import {
  Trophy,
  CheckCircle2,
  Building2,
  AlertTriangle,
} from 'lucide-react'

interface TournamentStatsCardsProps {
  tournaments: TournamentGroup[]
  isLoading?: boolean
}

interface TournamentStats {
  total: number
  matched: number
  betpawaOnly: number
  sportyBetGaps: number
  bet9jaGaps: number
}

function computeTournamentStats(tournaments: TournamentGroup[]): TournamentStats {
  let total = 0
  let matched = 0
  let betpawaOnly = 0
  let sportyBetGaps = 0
  let bet9jaGaps = 0

  for (const tournament of tournaments) {
    total++

    // Check platform coverage across all events in this tournament
    let hasBetPawa = false
    let hasSportyBet = false
    let hasBet9ja = false

    for (const event of tournament.events) {
      for (const platform of event.platforms) {
        const p = platform.toLowerCase()
        if (p === 'betpawa') hasBetPawa = true
        if (p === 'sportybet') hasSportyBet = true
        if (p === 'bet9ja') hasBet9ja = true
      }
    }

    // Categorize tournament
    const hasCompetitor = hasSportyBet || hasBet9ja

    if (hasBetPawa && hasCompetitor) {
      matched++
    } else if (hasBetPawa && !hasCompetitor) {
      betpawaOnly++
    }

    // Gaps: competitor has it but BetPawa doesn't
    if (hasSportyBet && !hasBetPawa) {
      sportyBetGaps++
    }
    if (hasBet9ja && !hasBetPawa) {
      bet9jaGaps++
    }
  }

  return { total, matched, betpawaOnly, sportyBetGaps, bet9jaGaps }
}

export function TournamentStatsCards({
  tournaments,
  isLoading,
}: TournamentStatsCardsProps) {
  const stats = useMemo(
    () => computeTournamentStats(tournaments),
    [tournaments]
  )

  if (isLoading) {
    return (
      <div className="grid gap-4 grid-cols-2 md:grid-cols-4 lg:grid-cols-5">
        {[...Array(5)].map((_, i) => (
          <Card key={i}>
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-24" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16" />
              <Skeleton className="h-3 w-20 mt-1" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="grid gap-4 grid-cols-2 md:grid-cols-4 lg:grid-cols-5">
      {/* Total Tournaments */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Total Tournaments
          </CardTitle>
          <Trophy className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.total}</div>
          <p className="text-xs text-muted-foreground">Across all platforms</p>
        </CardContent>
      </Card>

      {/* Matched Tournaments */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Matched
          </CardTitle>
          <CheckCircle2 className="h-4 w-4 text-green-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">{stats.matched}</div>
          <p className="text-xs text-muted-foreground">
            On BetPawa + competitors
          </p>
        </CardContent>
      </Card>

      {/* BetPawa Only Tournaments */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            BetPawa Only
          </CardTitle>
          <Building2 className="h-4 w-4 text-blue-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-blue-600">
            {stats.betpawaOnly}
          </div>
          <p className="text-xs text-muted-foreground">Not on competitors</p>
        </CardContent>
      </Card>

      {/* SportyBet Gaps */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            SportyBet Gaps
          </CardTitle>
          <AlertTriangle className="h-4 w-4 text-orange-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-orange-600">
            {stats.sportyBetGaps}
          </div>
          <p className="text-xs text-muted-foreground">Missing from BetPawa</p>
        </CardContent>
      </Card>

      {/* Bet9ja Gaps */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Bet9ja Gaps
          </CardTitle>
          <AlertTriangle className="h-4 w-4 text-orange-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-orange-600">
            {stats.bet9jaGaps}
          </div>
          <p className="text-xs text-muted-foreground">Missing from BetPawa</p>
        </CardContent>
      </Card>
    </div>
  )
}
