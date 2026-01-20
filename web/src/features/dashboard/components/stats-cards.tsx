import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useEventsStats, useSchedulerStatus } from '../hooks'
import { Activity, Calendar, CheckCircle, Clock } from 'lucide-react'

export function StatsCards() {
  const { totalEvents, matchedEvents, isPending: statsLoading } = useEventsStats()
  const { data: scheduler, isPending: schedulerLoading } = useSchedulerStatus()

  const isPending = statsLoading || schedulerLoading
  const nextRun = scheduler?.jobs[0]?.next_run
  const interval = scheduler?.jobs[0]?.interval_minutes

  if (isPending) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
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
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Events</CardTitle>
          <Calendar className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{totalEvents}</div>
          <p className="text-xs text-muted-foreground">Across all platforms</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Matched Events</CardTitle>
          <CheckCircle className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{matchedEvents}</div>
          <p className="text-xs text-muted-foreground">
            {totalEvents > 0
              ? `${Math.round((matchedEvents / totalEvents) * 100)}% coverage`
              : 'No events yet'}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Scrape Interval</CardTitle>
          <Clock className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {interval ? `${interval}m` : '-'}
          </div>
          <p className="text-xs text-muted-foreground">Between scrapes</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Scheduler</CardTitle>
          <Activity className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {scheduler?.running ? 'Active' : 'Stopped'}
          </div>
          <p className="text-xs text-muted-foreground">
            {nextRun
              ? `Next: ${new Date(nextRun).toLocaleTimeString()}`
              : 'No scheduled runs'}
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
