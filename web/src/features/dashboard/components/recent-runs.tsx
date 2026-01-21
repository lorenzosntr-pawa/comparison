import { Link } from 'react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useSchedulerHistory } from '../hooks'
import { cn } from '@/lib/utils'
import { formatDistanceToNow } from 'date-fns'
import { ArrowRight } from 'lucide-react'

function formatDuration(
  startedAt: string,
  completedAt: string | null
): string | null {
  if (!completedAt) return null
  const start = new Date(startedAt).getTime()
  const end = new Date(completedAt).getTime()
  const seconds = Math.round((end - start) / 1000)
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes}m ${secs}s`
}

const statusVariants: Record<
  string,
  'default' | 'destructive' | 'secondary' | 'outline'
> = {
  completed: 'default',
  partial: 'secondary',
  failed: 'destructive',
  running: 'outline',
  pending: 'outline',
}

export function RecentRuns() {
  const { data, isPending, error } = useSchedulerHistory(5)

  if (isPending) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">
            Recent Scrape Runs
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">
            Recent Scrape Runs
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">Failed to load run history</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">Recent Scrape Runs</CardTitle>
        <Button variant="ghost" size="sm" asChild>
          <Link to="/scrape-runs">
            View All <ArrowRight className="ml-1 h-4 w-4" />
          </Link>
        </Button>
      </CardHeader>
      <CardContent>
        {data?.runs.length === 0 ? (
          <p className="text-sm text-muted-foreground">No scrape runs yet</p>
        ) : (
          <div className="space-y-3">
            {data?.runs.map((run) => {
              const duration = formatDuration(run.started_at, run.completed_at)
              return (
                <div
                  key={run.id}
                  className="flex items-center justify-between py-2 border-b last:border-0"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={statusVariants[run.status]}
                        className={cn(
                          run.status === 'completed' &&
                            'bg-green-500 hover:bg-green-600'
                        )}
                      >
                        {run.status}
                      </Badge>
                      {duration && (
                        <span className="text-xs text-muted-foreground">
                          {duration}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {formatDistanceToNow(new Date(run.started_at), {
                        addSuffix: true,
                      })}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">
                      {run.events_scraped} events
                    </p>
                    {run.events_failed > 0 && (
                      <p className="text-xs text-destructive">
                        {run.events_failed} failed
                      </p>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
