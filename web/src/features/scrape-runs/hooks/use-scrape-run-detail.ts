/**
 * Hook for fetching detailed information about a single scrape run.
 *
 * @module use-scrape-run-detail
 * @description Provides comprehensive data about a scrape run including
 * status, timing, event counts, platform breakdowns, and any errors.
 * Used on the scrape run detail page to show full execution information.
 *
 * @example
 * ```typescript
 * import { useScrapeRunDetail } from '@/features/scrape-runs/hooks/use-scrape-run-detail'
 *
 * function ScrapeRunPage({ runId }: { runId: number }) {
 *   const { data: run, isPending } = useScrapeRunDetail(runId, {
 *     pollWhileRunning: true, // Auto-refresh while scrape is active
 *   })
 *
 *   if (isPending) return <Spinner />
 *
 *   return (
 *     <div>
 *       <h1>Run #{run.scrape_run_id}</h1>
 *       <p>Status: {run.status}</p>
 *       <p>Events: {run.events_scraped} scraped, {run.events_failed} failed</p>
 *       {run.errors?.length > 0 && <ErrorList errors={run.errors} />}
 *     </div>
 *   )
 * }
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

/**
 * An error that occurred during a scrape run.
 */
export interface ScrapeError {
  /** Unique error ID */
  id: number
  /** Error classification (e.g., 'timeout', 'parse_error', 'network') */
  error_type: string
  /** Detailed error message */
  error_message: string
  /** ISO timestamp when error occurred */
  occurred_at: string
  /** Platform where error occurred, or null for cross-platform errors */
  platform: string | null
}

/**
 * Detailed information about a single scrape run.
 *
 * @description Complete execution data including status, timing, counts,
 * per-platform breakdowns, and error details.
 */
export interface ScrapeRunDetail {
  /** Unique scrape run ID */
  scrape_run_id: number
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
  /** Array of errors encountered during the run */
  errors: ScrapeError[] | null
}

/**
 * Options for the useScrapeRunDetail hook.
 */
interface UseScrapeRunDetailOptions {
  /** Enable auto-refresh every 5s while run status is 'running' (default: false) */
  pollWhileRunning?: boolean
}

/**
 * Fetches detailed information about a single scrape run.
 *
 * @description Returns full run data from `/api/scrape/{id}`. Optionally polls
 * every 5 seconds while the run is active, useful for real-time status updates
 * on the detail page.
 *
 * Query is disabled if id is NaN. Uses 1-minute stale time for completed runs.
 *
 * @param id - The scrape run ID to fetch
 * @param options - Optional configuration for polling behavior
 * @returns TanStack Query result with ScrapeRunDetail
 *
 * @example
 * ```typescript
 * // Static fetch (no polling)
 * const { data } = useScrapeRunDetail(runId)
 *
 * // With polling for live updates
 * const { data, isPending } = useScrapeRunDetail(runId, { pollWhileRunning: true })
 *
 * // Check if still running
 * const isActive = data?.status === 'running'
 * ```
 */
export function useScrapeRunDetail(id: number, options?: UseScrapeRunDetailOptions) {
  const { pollWhileRunning = false } = options ?? {}

  return useQuery({
    queryKey: ['scrape-run', id],
    queryFn: () => api.get<ScrapeRunDetail>(`/scrape/${id}`),
    staleTime: 60_000,
    enabled: !isNaN(id),
    // Poll every 5 seconds when running (if enabled)
    refetchInterval: (query) => {
      if (!pollWhileRunning) return false
      const data = query.state.data
      return data?.status === 'running' ? 5000 : false
    },
  })
}
