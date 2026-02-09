/**
 * Hooks for controlling the scrape scheduler.
 *
 * @module use-scheduler-control
 * @description Provides mutation hooks for pausing and resuming the automatic
 * scrape scheduler. Used in the settings page to temporarily stop scheduled
 * scrapes (e.g., during maintenance or debugging).
 *
 * ## Query Invalidation
 *
 * Both mutations use `refetchQueries` (not `invalidateQueries`) on success
 * to immediately update the scheduler status across all mounted components.
 *
 * @example
 * ```typescript
 * import { usePauseScheduler, useResumeScheduler } from '@/features/settings/hooks/use-scheduler-control'
 *
 * function SchedulerToggle({ isPaused }) {
 *   const { mutate: pause, isPending: isPausing } = usePauseScheduler()
 *   const { mutate: resume, isPending: isResuming } = useResumeScheduler()
 *
 *   return (
 *     <Button
 *       onClick={() => isPaused ? resume() : pause()}
 *       disabled={isPausing || isResuming}
 *     >
 *       {isPaused ? 'Resume Scheduler' : 'Pause Scheduler'}
 *     </Button>
 *   )
 * }
 * ```
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

/**
 * Creates a mutation for pausing the scheduler.
 *
 * @description Sends a pause request to the scheduler API. On success,
 * immediately refetches scheduler status to update all components.
 *
 * @returns TanStack Mutation with mutate, isPending, error
 *
 * @example
 * ```typescript
 * const { mutate: pause, isPending } = usePauseScheduler()
 *
 * pause(undefined, {
 *   onSuccess: () => toast.success('Scheduler paused'),
 *   onError: (err) => toast.error(err.message),
 * })
 * ```
 */
export function usePauseScheduler() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => api.pauseScheduler(),
    onSuccess: () => {
      // Use refetchQueries for immediate update across all components
      queryClient.refetchQueries({ queryKey: ['scheduler', 'status'] })
    },
  })
}

/**
 * Creates a mutation for resuming the scheduler.
 *
 * @description Sends a resume request to the scheduler API. On success,
 * immediately refetches scheduler status to update all components.
 *
 * @returns TanStack Mutation with mutate, isPending, error
 *
 * @example
 * ```typescript
 * const { mutate: resume, isPending } = useResumeScheduler()
 *
 * resume(undefined, {
 *   onSuccess: () => toast.success('Scheduler resumed'),
 *   onError: (err) => toast.error(err.message),
 * })
 * ```
 */
export function useResumeScheduler() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => api.resumeScheduler(),
    onSuccess: () => {
      // Use refetchQueries for immediate update across all components
      queryClient.refetchQueries({ queryKey: ['scheduler', 'status'] })
    },
  })
}
