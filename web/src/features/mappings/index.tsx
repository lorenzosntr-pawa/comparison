import { useMappingStats } from './hooks'
import { MappingStatsCards, RecentChanges, PlatformCoverageChart, HighPriorityUnmapped } from './components'

export function MappingDashboard() {
  const { data: stats, isPending, error } = useMappingStats()

  if (error) {
    return (
      <div className="p-4 text-red-500 bg-red-50 rounded-md">
        Failed to load mapping stats: {error.message}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Market Mappings</h1>
        {stats && (
          <span className="text-sm text-muted-foreground">
            {stats.totalMappings} total mappings
          </span>
        )}
      </div>

      {/* Stats Cards */}
      <MappingStatsCards stats={stats} isLoading={isPending} />

      {/* Charts & Recent Changes - 2-column grid on large screens */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left: Platform Coverage Chart */}
        <PlatformCoverageChart
          data={stats?.byPlatform}
          totalMappings={stats?.totalMappings ?? 0}
          isLoading={isPending}
        />

        {/* Right: Recent Changes */}
        <RecentChanges />
      </div>

      {/* High Priority Unmapped Markets */}
      <HighPriorityUnmapped />
    </div>
  )
}
