import { useMappingStats } from './hooks'
import { MappingStatsCards, RecentChanges } from './components'

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
        {/* Left: Charts (will be added in Task 2) */}
        <div>{/* PlatformCoverageChart placeholder */}</div>

        {/* Right: Recent Changes */}
        <RecentChanges />
      </div>
    </div>
  )
}
