/**
 * Hooks for fetching scrape run history and statistics.
 *
 * @module use-scrape-runs
 * @description Provides data fetching hooks for the scrape runs list view.
 * Includes hooks for fetching the run history list and aggregate statistics.
 *
 * @example
 * ```typescript
 * import { useScrapeRuns, useScrapeStats } from '@/features/scrape-runs/hooks/use-scrape-runs'
 *
 * function ScrapeRunsPage() {
 *   const { data: runs } = useScrapeRuns(20, 0)
 *   const { data: stats } = useScrapeStats()
 *
 *   return (
 *     <div>
 *       <p>Total runs: {stats?.total_runs}</p>
 *       <p>Last 24h: {stats?.runs_24h}</p>
 *       <RunList runs={runs} />
 *     </div>
 *   )
 * }
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

/**
 * Summary information about a scrape run.
 *
 * @description Contains key metrics for displaying in list views.
 * For full details, use useScrapeRunDetail.
 */
export interface ScrapeRun {
  /** Unique scrape run ID */
  id: number
  /** Run status: 'running', 'completed', 'failed', 'partial' */
  status: string
  /** ISO timestamp when run started */
  started_at: string
  /** ISO timestamp when run completed, or null if still running */
  completed_at: string | null
  /** Total events successfully scraped */
  events_scraped: number
  /** Total events that failed to scrape */
  events_failed: number
  /** What triggered the run: 'scheduled', 'manual', 'retry' */
  trigger: string | null
  /** Per-platform timing and count breakdown */
  platform_timings: Record<
    string,
    { duration_ms: number; events_count: number }
  > | null
}

/**
 * Aggregate statistics about scrape runs.
 */
export interface ScrapeStats {
  /** Total number of scrape runs in the database */
  total_runs: number
  /** Number of runs in the last 24 hours */
  runs_24h: number
  /** Average run duration in seconds, or null if no data */
  avg_duration_seconds: number | null
}

/**
 * Fetches a paginated list of scrape runs.
 *
 * @description Returns recent scrape runs for the history list view.
 * Uses a 30-second stale time for near-real-time updates.
 *
 * @param limit - Maximum number of runs to return (default: 20)
 * @param offset - Number of runs to skip for pagination (default: 0)
 * @returns TanStack Query result with array of ScrapeRun objects
 *
 * @example
 * ```typescript
 * // First page of 20 runs
 * const { data: runs } = useScrapeRuns()
 *
 * // Second page
 * const { data: page2 } = useScrapeRuns(20, 20)
 * ```
 */
export function useScrapeRuns(limit = 20, offset = 0) {
  return useQuery({
    queryKey: ['scrape-runs', limit, offset],
    queryFn: () =>
      api.get<ScrapeRun[]>(`/scrape/runs?limit=${limit}&offset=${offset}`),
    staleTime: 30_000,
  })
}

/**
 * Fetches aggregate scrape statistics.
 *
 * @description Returns summary metrics about scrape activity, useful for
 * dashboard displays showing system health and activity levels.
 *
 * Uses a 1-minute stale time since aggregate stats change slowly.
 *
 * @returns TanStack Query result with ScrapeStats
 *
 * @example
 * ```typescript
 * const { data: stats } = useScrapeStats()
 *
 * // Display in dashboard
 * <p>Runs today: {stats?.runs_24h}</p>
 * <p>Avg duration: {Math.round(stats?.avg_duration_seconds / 60)} min</p>
 * ```
 */
export function useScrapeStats() {
  return useQuery({
    queryKey: ['scrape-stats'],
    queryFn: () => api.get<ScrapeStats>('/scrape/stats'),
    staleTime: 60_000,
  })
}
