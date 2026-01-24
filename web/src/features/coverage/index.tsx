import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useCoverage, usePalimpsestEvents } from './hooks'

export function CoveragePage() {
  const { data: coverage, isPending: coveragePending, error: coverageError } = useCoverage()
  const { data: eventsData, isPending: eventsPending, error: eventsError } = usePalimpsestEvents()

  const isPending = coveragePending || eventsPending
  const error = coverageError || eventsError

  if (error) {
    return (
      <div className="p-4 text-red-500 bg-red-50 rounded-md">
        Failed to load coverage data: {error.message}
      </div>
    )
  }

  if (isPending) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Coverage Comparison</h1>
        <div className="grid gap-4 md:grid-cols-4">
          {[...Array(4)].map((_, i) => (
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
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-48" />
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Coverage Comparison</h1>

      {coverage && eventsData && (
        <Card>
          <CardHeader>
            <CardTitle>Coverage Data</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              Coverage data will appear here. Total events: {coverage.total_events},
              Matched: {coverage.matched_count},
              Tournaments: {eventsData.tournaments.length}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
