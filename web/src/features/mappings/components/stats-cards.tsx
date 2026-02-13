import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Layers, Code, Database, AlertCircle, PieChart } from 'lucide-react'
import type { MappingStats } from '../hooks'

interface MappingStatsCardsProps {
  stats: MappingStats | undefined
  isLoading?: boolean
}

export function MappingStatsCards({ stats, isLoading }: MappingStatsCardsProps) {
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

  // Calculate coverage % (mapped / (mapped + unmapped NEW))
  const totalSeen = (stats?.totalMappings ?? 0) + (stats?.unmappedCounts.new ?? 0)
  const coveragePercent = totalSeen > 0
    ? ((stats?.totalMappings ?? 0) / totalSeen) * 100
    : 0

  return (
    <div className="grid gap-4 grid-cols-2 md:grid-cols-4 lg:grid-cols-5">
      {/* Total Mappings */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Total Mappings
          </CardTitle>
          <Layers className="h-4 w-4 text-green-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">
            {stats?.totalMappings ?? 0}
          </div>
          <p className="text-xs text-muted-foreground">Active in cache</p>
        </CardContent>
      </Card>

      {/* Code Mappings */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Code Mappings
          </CardTitle>
          <Code className="h-4 w-4 text-green-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">
            {stats?.codeMappings ?? 0}
          </div>
          <p className="text-xs text-muted-foreground">Built-in</p>
        </CardContent>
      </Card>

      {/* User Mappings */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            User Mappings
          </CardTitle>
          <Database className="h-4 w-4 text-blue-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-blue-600">
            {stats?.dbMappings ?? 0}
          </div>
          <p className="text-xs text-muted-foreground">Custom overrides</p>
        </CardContent>
      </Card>

      {/* Unmapped NEW */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Unmapped NEW
          </CardTitle>
          <AlertCircle className="h-4 w-4 text-orange-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-orange-600">
            {stats?.unmappedCounts.new ?? 0}
          </div>
          <p className="text-xs text-muted-foreground">Needs attention</p>
        </CardContent>
      </Card>

      {/* Coverage % */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Coverage
          </CardTitle>
          <PieChart className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {coveragePercent.toFixed(1)}%
          </div>
          <p className="text-xs text-muted-foreground">Mapped / Total seen</p>
        </CardContent>
      </Card>
    </div>
  )
}
