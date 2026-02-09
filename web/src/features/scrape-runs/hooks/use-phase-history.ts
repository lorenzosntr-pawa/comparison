/**
 * Hook for fetching phase-level history of a scrape run.
 *
 * @module use-phase-history
 * @description Provides detailed phase transition history for a single scrape run.
 * Each scrape goes through multiple phases (fetching events, scraping odds, matching, etc.)
 * and this hook returns timing and status for each phase.
 *
 * @example
 * ```typescript
 * import { usePhaseHistory } from '@/features/scrape-runs/hooks/use-phase-history'
 *
 * function PhaseTimeline({ runId }: { runId: number }) {
 *   const { data: phases, isPending } = usePhaseHistory(runId)
 *
 *   if (isPending) return <Spinner />
 *
 *   return (
 *     <ul>
 *       {phases?.map(phase => (
 *         <li key={phase.id}>
 *           {phase.phase}: {phase.events_processed} events ({phase.message})
 *         </li>
 *       ))}
 *     </ul>
 *   )
 * }
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

/**
 * A single phase log entry from a scrape run.
 *
 * @description Represents one phase of execution within a scrape run,
 * with timing information and event counts.
 */
export interface ScrapePhaseLog {
  /** Unique phase log ID */
  id: number
  /** Platform this phase ran on, or null for cross-platform phases */
  platform: string | null
  /** Phase name (e.g., 'fetching_events', 'scraping_odds', 'matching') */
  phase: string
  /** ISO timestamp when phase started */
  started_at: string
  /** ISO timestamp when phase ended, or null if still running */
  ended_at: string | null
  /** Number of events processed in this phase */
  events_processed: number | null
  /** Human-readable status message */
  message: string | null
}

/**
 * Fetches phase-level execution history for a scrape run.
 *
 * @description Returns an array of phase log entries showing how the scrape
 * progressed through its execution stages. Useful for debugging failed runs
 * and understanding timing bottlenecks.
 *
 * Uses a 30-second stale time for near-real-time updates on running scrapes.
 * Query is disabled if runId is NaN.
 *
 * @param runId - The scrape run ID to fetch phases for
 * @returns TanStack Query result with array of ScrapePhaseLog entries
 *
 * @example
 * ```typescript
 * const { data: phases } = usePhaseHistory(runId)
 *
 * // Calculate total duration
 * const firstPhase = phases?.[0]
 * const lastPhase = phases?.[phases.length - 1]
 * const totalMs = new Date(lastPhase.ended_at).getTime() - new Date(firstPhase.started_at).getTime()
 * ```
 */
export function usePhaseHistory(runId: number) {
  return useQuery({
    queryKey: ['scrape-run-phases', runId],
    queryFn: () => api.get<ScrapePhaseLog[]>(`/scrape/runs/${runId}/phases`),
    staleTime: 30_000, // Refresh every 30s
    enabled: !isNaN(runId),
  })
}
