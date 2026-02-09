/**
 * Hooks for monitoring the scrape scheduler.
 *
 * @module use-scheduler
 * @description Provides TanStack Query hooks for monitoring scheduler status,
 * execution history, and health metrics. The scheduler runs periodic scrapes
 * to keep odds data fresh across all platforms.
 *
 * @example
 * ```typescript
 * import {
 *   useSchedulerStatus,
 *   useSchedulerHistory,
 *   useSchedulerHealth,
 * } from '@/features/dashboard/hooks/use-scheduler'
 *
 * function SchedulerPanel() {
 *   const { data: status } = useSchedulerStatus()
 *   const { data: history } = useSchedulerHistory(5)
 *   const { data: health } = useSchedulerHealth()
 *
 *   return (
 *     <div>
 *       <p>State: {status?.state}</p>
 *       <p>Next run: {status?.next_run_at}</p>
 *       <p>Recent runs: {history?.runs.length}</p>
 *     </div>
 *   )
 * }
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

/**
 * Fetches current scheduler status.
 *
 * @description Returns the scheduler's current state (running, paused, idle),
 * next scheduled run time, and active job information. Polls every 10 seconds
 * to keep the status display current.
 *
 * @returns TanStack Query result with SchedulerStatus containing state and timing info
 *
 * @example
 * ```typescript
 * const { data, isPending } = useSchedulerStatus()
 *
 * if (data?.state === 'running') {
 *   console.log('Scrape in progress')
 * } else if (data?.next_run_at) {
 *   console.log(`Next scrape at ${data.next_run_at}`)
 * }
 * ```
 */
export function useSchedulerStatus() {
  return useQuery({
    queryKey: ['scheduler', 'status'],
    queryFn: () => api.getSchedulerStatus(),
    refetchInterval: 10000, // Poll every 10s
  })
}

/**
 * Fetches scheduler execution history.
 *
 * @description Returns a list of recent scrape runs triggered by the scheduler,
 * including start/end times, status, and any errors. Useful for showing recent
 * activity and identifying patterns in scrape failures.
 *
 * @param limit - Maximum number of history entries to fetch (default: 5)
 * @returns TanStack Query result with RunHistoryResponse containing runs array
 *
 * @example
 * ```typescript
 * const { data } = useSchedulerHistory(10)
 *
 * // Show success rate
 * const successRate = data?.runs.filter(r => r.status === 'completed').length / data?.runs.length
 * ```
 */
export function useSchedulerHistory(limit = 5) {
  return useQuery({
    queryKey: ['scheduler', 'history', limit],
    queryFn: () => api.getSchedulerHistory({ limit }),
    refetchInterval: 30000,
  })
}

/**
 * Fetches scheduler health metrics.
 *
 * @description Returns detailed health information about the scheduler and
 * individual platform scrapers. Includes metrics like last successful run,
 * failure counts, and platform-specific status.
 *
 * @returns TanStack Query result with SchedulerPlatformHealth containing platform health data
 *
 * @example
 * ```typescript
 * const { data } = useSchedulerHealth()
 *
 * // Check if any platform is unhealthy
 * const unhealthyPlatforms = data?.platforms.filter(p => p.status !== 'healthy')
 * if (unhealthyPlatforms?.length) {
 *   console.warn('Some platforms are unhealthy:', unhealthyPlatforms)
 * }
 * ```
 */
export function useSchedulerHealth() {
  return useQuery({
    queryKey: ['scheduler', 'health'],
    queryFn: () => api.getSchedulerHealth(),
    refetchInterval: 30000,
  })
}
