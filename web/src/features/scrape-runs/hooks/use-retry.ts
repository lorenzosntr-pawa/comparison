import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

interface RetryParams {
  runId: number
  platforms: string[]
}

interface RetryResponse {
  new_run_id: number
  platforms_retried: string[]
  message: string
}

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
