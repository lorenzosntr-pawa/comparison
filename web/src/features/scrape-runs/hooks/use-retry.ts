/**
 * Hook for retrying failed scrape runs.
 *
 * @module use-retry
 * @description Provides a mutation hook for retrying a failed scrape run on
 * specific platforms. When a scrape fails partway through, this allows
 * re-running just the failed platforms instead of a full re-scrape.
 *
 * ## Query Invalidation
 *
 * On successful retry, invalidates:
 * - `['scrape-runs']` - Refreshes the run list to show new retry run
 * - `['scrape-stats']` - Updates aggregate statistics
 * - `['scrape-run']` - Refreshes individual run details
 *
 * @example
 * ```typescript
 * import { useRetry } from '@/features/scrape-runs/hooks/use-retry'
 *
 * function RetryButton({ runId, failedPlatforms }) {
 *   const { mutate: retry, isPending } = useRetry()
 *
 *   return (
 *     <Button
 *       onClick={() => retry({ runId, platforms: failedPlatforms })}
 *       disabled={isPending}
 *     >
 *       {isPending ? 'Retrying...' : 'Retry Failed Platforms'}
 *     </Button>
 *   )
 * }
 * ```
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'

/**
 * Parameters for the retry mutation.
 */
interface RetryParams {
  /** ID of the failed scrape run to retry */
  runId: number
  /** Array of platform slugs to retry (e.g., ['sportybet', 'betway']) */
  platforms: string[]
}

/**
 * Response from a successful retry request.
 */
interface RetryResponse {
  /** ID of the newly created retry run */
  new_run_id: number
  /** Platforms that were included in the retry */
  platforms_retried: string[]
  /** Human-readable success message */
  message: string
}

/**
 * Creates a mutation for retrying failed scrape platforms.
 *
 * @description Returns a TanStack Query mutation hook for POSTing retry requests.
 * The mutation:
 * 1. Sends POST to `/api/scrape/{runId}/retry` with platform list
 * 2. On success, invalidates scrape-related queries to refresh UI
 * 3. Returns the new run ID for navigation/tracking
 *
 * @returns TanStack Mutation with mutate, isPending, error, and data
 *
 * @example
 * ```typescript
 * const { mutate, isPending, error, data } = useRetry()
 *
 * // Trigger retry
 * mutate({ runId: 123, platforms: ['sportybet'] }, {
 *   onSuccess: (result) => {
 *     toast.success(`Retry started: Run #${result.new_run_id}`)
 *     navigate(`/scrape-runs/${result.new_run_id}`)
 *   },
 *   onError: (error) => {
 *     toast.error(error.message)
 *   },
 * })
 * ```
 */
export function useRetry() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ runId, platforms }: RetryParams) => {
      const response = await fetch(`/api/scrape/${runId}/retry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ platforms }),
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Retry failed' }))
        throw new Error(error.detail || 'Retry failed')
      }

      return response.json() as Promise<RetryResponse>
    },
    onSuccess: () => {
      // Invalidate all scrape-related queries to refresh lists
      queryClient.invalidateQueries({ queryKey: ['scrape-runs'] })
      queryClient.invalidateQueries({ queryKey: ['scrape-stats'] })
      queryClient.invalidateQueries({ queryKey: ['scrape-run'] })
    },
  })
}

export type { RetryParams, RetryResponse }
