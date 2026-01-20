import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { StatsCards, PlatformHealth, RecentRuns, StatusCard } from './components'
import { useHealth, useSchedulerStatus } from './hooks'

export function Dashboard() {
  const { data: health, isPending: healthLoading } = useHealth()
  const { data: scheduler, isPending: schedulerLoading } = useSchedulerStatus()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          System status and scraping overview
        </p>
      </div>

      {/* Quick Stats */}
      <StatsCards />

      {/* Status Cards Row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <StatusCard
          title="System Status"
          status={health?.status ?? 'unhealthy'}
          subtitle={
            health?.status === 'healthy'
              ? 'All systems operational'
              : health?.status === 'degraded'
                ? 'Some platforms unavailable'
                : 'System offline'
          }
          isPending={healthLoading}
        />
        <StatusCard
          title="Scheduler"
          status={scheduler?.running ? 'running' : 'stopped'}
          subtitle={
            scheduler?.jobs[0]?.interval_minutes
              ? `Every ${scheduler.jobs[0].interval_minutes} minutes`
              : 'No jobs configured'
          }
          isPending={schedulerLoading}
        />
        <PlatformHealth />
      </div>

      {/* Recent Activity */}
      <div className="grid gap-4 lg:grid-cols-2">
        <RecentRuns />
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-sm font-medium">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Scheduler controls will be available in Phase 7 Settings page.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
