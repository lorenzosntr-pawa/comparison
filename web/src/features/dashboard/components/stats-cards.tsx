import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useCoverage } from '@/features/coverage/hooks'
import { BarChart3, CheckCircle } from 'lucide-react'

export function StatsCards() {
  const { data: coverage, isPending } = useCoverage()

  if (isPending) {
    return (
      <div className="grid gap-4 md:grid-cols-2">
        {[1, 2].map((i) => (
          <Card key={i}>
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-24" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Events</CardTitle>
          <BarChart3 className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{coverage?.total_events ?? 0}</div>
          <p className="text-xs text-muted-foreground">Across all platforms</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Matched Events</CardTitle>
          <CheckCircle className="h-4 w-4 text-green-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">{coverage?.matched_count ?? 0}</div>
          <p className="text-xs text-muted-foreground">
            {coverage ? `${coverage.match_rate.toFixed(1)}% match rate` : 'No data'}
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
