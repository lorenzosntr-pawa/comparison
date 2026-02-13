import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ApiError } from '@/lib/api'

const API_BASE = '/api'

/**
 * Parameters for updating an unmapped market status.
 */
export interface UpdateUnmappedStatusParams {
  id: number
  status: 'NEW' | 'ACKNOWLEDGED' | 'MAPPED' | 'IGNORED'
  notes?: string
}

/**
 * Response from updating an unmapped market.
 */
export interface UnmappedMarketResponse {
  id: number
  source: string
  externalMarketId: string
  marketName: string | null
  sampleOutcomes: Array<Record<string, unknown>> | null
  firstSeenAt: string
  lastSeenAt: string
  occurrenceCount: number
  status: string
  notes: string | null
}

/**
 * Update unmapped market status via PATCH /api/unmapped/:id.
 */
async function updateUnmappedStatus(
  params: UpdateUnmappedStatusParams
): Promise<UnmappedMarketResponse> {
  const body: Record<string, unknown> = { status: params.status }
  if (params.notes !== undefined) {
    body.notes = params.notes
  }

  const response = await fetch(`${API_BASE}/unmapped/${params.id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new ApiError(response.status, errorText || `API error: ${response.status}`)
  }

  return response.json()
}

/**
 * Hook for updating unmapped market status.
 *
 * Typically used after successful mapping creation to mark the source
 * market as MAPPED.
 *
 * Invalidates unmapped-related queries on success.
 */
export function useUpdateUnmappedStatus() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: updateUnmappedStatus,
    onSuccess: (_data, variables) => {
      // Invalidate unmapped queries to refresh lists
      queryClient.invalidateQueries({ queryKey: ['unmapped'] })
      queryClient.invalidateQueries({ queryKey: ['high-priority-unmapped'] })
      queryClient.invalidateQueries({
        queryKey: ['unmapped-detail', variables.id],
      })
      // Also refresh mapping stats since unmapped counts change
      queryClient.invalidateQueries({ queryKey: ['mapping-stats'] })
    },
  })
}
