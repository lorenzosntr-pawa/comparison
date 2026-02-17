/**
 * Storage dashboard page for monitoring database sizes and cleanup history.
 *
 * @module storage
 * @description Provides visibility into database health and growth patterns.
 */

import { format, formatDistanceToNow } from 'date-fns'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useStorageSizes, useStorageHistory, useCleanupHistory, useStorageAlerts, useResolveAlert } from './hooks'
import type { CleanupRun } from './hooks'
import { AlertsBanner, SizeTrendChart } from './components'

/**
 * Format bytes to human-readable size string.
 */
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const k = 1024
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  const value = bytes / Math.pow(k, i)
  return `${value.toFixed(i > 1 ? 2 : 0)} ${units[i]}`
}

/**
 * Format number with commas for readability.
 */
function formatNumber(n: number): string {
  return n.toLocaleString()
}

/**
 * Get size color based on bytes value.
 */
function getSizeColor(bytes: number): string {
  const gb = bytes / (1024 * 1024 * 1024)
  if (gb >= 5) return 'text-red-600'
  if (gb >= 1) return 'text-yellow-600'
  return 'text-green-600'
}

/**
 * Get status badge variant for cleanup run.
 */
function getStatusBadge(run: CleanupRun) {
  switch (run.status) {
    case 'completed':
      return <Badge variant="default" className="bg-green-600">Completed</Badge>
    case 'failed':
      return <Badge variant="destructive">Failed</Badge>
    case 'running':
      return <Badge variant="secondary">Running</Badge>
    default:
      return <Badge variant="outline">{run.status}</Badge>
  }
}

/**
 * Format duration in milliseconds to human-readable string.
 */
function formatDuration(ms: number | null): string {
  if (ms === null) return '-'
  if (ms < 1000) return `${ms}ms`
  const seconds = ms / 1000
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSecs = Math.round(seconds % 60)
  return `${minutes}m ${remainingSecs}s`
}

export function StoragePage() {
  const { data: sizes, isLoading: sizesLoading, error: sizesError } = useStorageSizes()
  const { data: history, isLoading: historyLoading } = useStorageHistory(30)
  const { data: cleanup, isLoading: cleanupLoading, error: cleanupError } = useCleanupHistory(10)
  const { data: alertsData } = useStorageAlerts()
  const resolveAlert = useResolveAlert()

  const alerts = alertsData?.alerts ?? []
  const alertCount = alerts.length

  // Show error state
  if (sizesError || cleanupError) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Storage</h1>
        <Card>
          <CardContent className="pt-6">
            <p className="text-destructive">
              Failed to load storage data. Please try again later.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Show loading state
  if (sizesLoading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Storage</h1>
        {/* Total size skeleton */}
        <Card>
          <CardHeader className="pb-2">
            <Skeleton className="h-5 w-32" />
            <Skeleton className="h-3 w-48" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-12 w-24" />
          </CardContent>
        </Card>
        {/* Table sizes skeleton */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i}>
              <CardHeader className="pb-2 pt-4 px-4">
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent className="px-4 pb-4 pt-0">
                <Skeleton className="h-6 w-16" />
                <Skeleton className="h-3 w-20 mt-1" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  // Get top 6 tables by size
  const topTables = sizes?.tables
    .slice()
    .sort((a, b) => b.size_bytes - a.size_bytes)
    .slice(0, 6) ?? []

  return (
    <div className="space-y-6">
      {/* Alerts Banner */}
      <AlertsBanner
        alerts={alerts}
        onDismiss={(id) => resolveAlert.mutate(id)}
        dismissingId={resolveAlert.isPending ? (resolveAlert.variables as number) : null}
      />

      <h1 className="text-2xl font-bold">
        Storage{alertCount > 0 && (
          <Badge variant="destructive" className="ml-2 align-middle">
            {alertCount} {alertCount === 1 ? 'alert' : 'alerts'}
          </Badge>
        )}
      </h1>

      {/* Total Database Size Card */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle>Total Database Size</CardTitle>
          <CardDescription>
            Last sampled {sizes?.sampled_at
              ? formatDistanceToNow(new Date(sizes.sampled_at), { addSuffix: true })
              : '-'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className={cn(
            'text-4xl font-bold',
            sizes ? getSizeColor(sizes.total_bytes) : ''
          )}>
            {sizes ? formatBytes(sizes.total_bytes) : '-'}
          </div>
        </CardContent>
      </Card>

      {/* Table Size Cards */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Tables by Size</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {topTables.map((table) => (
            <Card key={table.table_name}>
              <CardHeader className="pb-2 pt-4 px-4">
                <CardTitle className="text-sm font-medium truncate" title={table.table_name}>
                  {table.table_name}
                </CardTitle>
              </CardHeader>
              <CardContent className="px-4 pb-4 pt-0">
                <div className={cn('text-xl font-bold', getSizeColor(table.size_bytes))}>
                  {formatBytes(table.size_bytes)}
                </div>
                <div className="text-xs text-muted-foreground">
                  {formatNumber(table.row_count)} rows
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Size Trend Chart */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle>Size Trend (Last 30 Days)</CardTitle>
          <CardDescription>
            Database size over time
          </CardDescription>
        </CardHeader>
        <CardContent>
          {historyLoading ? (
            <Skeleton className="h-[250px] w-full" />
          ) : (
            <SizeTrendChart data={history?.samples ?? []} />
          )}
        </CardContent>
      </Card>

      {/* Cleanup History Table */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Cleanup History</h2>
        <Card>
          <CardContent className="pt-4">
            {cleanupLoading ? (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : cleanup?.runs.length === 0 ? (
              <p className="text-muted-foreground text-center py-4">
                No cleanup runs recorded yet
              </p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Trigger</TableHead>
                    <TableHead>Duration</TableHead>
                    <TableHead className="text-right">Records Deleted</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {cleanup?.runs.map((run) => (
                    <TableRow key={run.id}>
                      <TableCell className="font-medium">
                        {format(new Date(run.started_at), 'MMM d, yyyy HH:mm')}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="capitalize">
                          {run.trigger}
                        </Badge>
                      </TableCell>
                      <TableCell>{formatDuration(run.duration_ms)}</TableCell>
                      <TableCell className="text-right">
                        {run.records_deleted !== null
                          ? formatNumber(run.records_deleted)
                          : '-'}
                      </TableCell>
                      <TableCell>{getStatusBadge(run)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
