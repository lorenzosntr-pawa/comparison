import { useMappingStats } from './hooks'

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

      {/* Stats Cards - placeholder until Task 2 */}
      <div className="text-muted-foreground">
        {isPending ? 'Loading stats...' : `${stats?.totalMappings ?? 0} mappings loaded`}
      </div>
    </div>
  )
}
