/**
 * Hook for monitoring platform health status.
 *
 * @module use-health
 * @description Provides real-time health check data from the backend API.
 * Used on dashboards and status pages to show whether the backend services
 * (database, scrapers, scheduler) are operational.
 *
 * @example
 * ```typescript
 * import { useHealth } from '@/features/dashboard/hooks/use-health'
 *
 * function HealthIndicator() {
 *   const { data, isPending, error } = useHealth()
 *
 *   if (error) return <Badge variant="destructive">Unhealthy</Badge>
 *   if (data?.status === 'healthy') return <Badge variant="success">Healthy</Badge>
 *   return <Badge variant="warning">Degraded</Badge>
 * }
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

/**
 * Fetches backend health status.
 *
 * @description Polls the /api/health endpoint every 30 seconds to monitor
 * backend health. Returns status information about database connectivity,
 * scheduler state, and any error conditions.
 *
 * @returns TanStack Query result with HealthResponse containing status and details
 *
 * @example
 * ```typescript
 * const { data, isPending, error, refetch } = useHealth()
 *
 * // Check specific components
 * if (data?.database?.connected) {
 *   console.log('Database is connected')
 * }
 * ```
 */
export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => api.getHealth(),
    refetchInterval: 30000, // Poll every 30s
  })
}
