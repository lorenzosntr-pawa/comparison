import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

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
