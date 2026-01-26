import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import type { CoverageStats } from '@/types/api'
import { BarChart3, CheckCircle, Building2, AlertTriangle } from 'lucide-react'

interface CoverageStatsCardsProps {
  coverage: CoverageStats | undefined
  isLoading?: boolean
}

function getUnmatchedByPlatform(
  coverage: CoverageStats | undefined,
  platform: string
): number {
  if (!coverage) return 0
  const platformData = coverage.by_platform.find(
    (p) => p.platform.toLowerCase() === platform.toLowerCase()
  )
  return platformData?.unmatched_events ?? 0
}

export function CoverageStatsCards({
  coverage,
  isLoading,
}: CoverageStatsCardsProps) {
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

  const sportyGaps = getUnmatchedByPlatform(coverage, 'sportybet')
  const bet9jaGaps = getUnmatchedByPlatform(coverage, 'bet9ja')

  return (
    <div className="grid gap-4 grid-cols-2 md:grid-cols-4 lg:grid-cols-5">
      {/* Total Events */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Total Events
          </CardTitle>
          <BarChart3 className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {coverage?.total_events ?? 0}
          </div>
          <p className="text-xs text-muted-foreground">Across all platforms</p>
        </CardContent>
      </Card>

      {/* Matched */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Matched
          </CardTitle>
          <CheckCircle className="h-4 w-4 text-green-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">
            {coverage?.matched_count ?? 0}
          </div>
          <p className="text-xs text-muted-foreground">
            {coverage ? `${coverage.match_rate.toFixed(1)}% match rate` : 'No data'}
          </p>
        </CardContent>
      </Card>

      {/* BetPawa Only */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            BetPawa Only
          </CardTitle>
          <Building2 className="h-4 w-4 text-blue-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-blue-600">
            {coverage?.betpawa_only_count ?? 0}
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
          <div className="text-2xl font-bold text-orange-600">{sportyGaps}</div>
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
          <div className="text-2xl font-bold text-orange-600">{bet9jaGaps}</div>
          <p className="text-xs text-muted-foreground">Missing from BetPawa</p>
        </CardContent>
      </Card>
    </div>
  )
}
