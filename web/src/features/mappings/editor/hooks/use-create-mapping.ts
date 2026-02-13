import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ApiError } from '@/lib/api'
import type { OutcomeFormItem } from '../utils/outcome-suggest'

const API_BASE = '/api'

/**
 * Parameters for creating a new mapping.
 */
export interface CreateMappingParams {
  canonicalId: string
  name: string
  betpawaId: string | null
  sportybetId: string | null
  bet9jaKey: string | null
  outcomeMapping: OutcomeFormItem[]
  priority: number
  reason: string
}

/**
 * Parameters for updating an existing mapping.
 */
export interface UpdateMappingParams {
  canonicalId: string
  name?: string
  betpawaId?: string | null
  sportybetId?: string | null
  bet9jaKey?: string | null
  outcomeMapping?: OutcomeFormItem[]
  priority?: number
  reason: string
}

/**
 * Response from creating/updating a mapping.
 */
export interface MappingResponse {
  canonicalId: string
  name: string
  betpawaId: string | null
  sportybetId: string | null
  bet9jaKey: string | null
  outcomeMapping: Array<{
    canonicalId: string
    betpawaName: string | null
    sportybetDesc: string | null
    bet9jaSuffix: string | null
    position: number
  }>
  source: 'db' | 'code'
  isActive: boolean
  priority: number
  createdAt: string | null
  updatedAt: string | null
}

/**
 * Create a new mapping via POST /api/mappings.
 */
async function createMapping(params: CreateMappingParams): Promise<MappingResponse> {
  const response = await fetch(`${API_BASE}/mappings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      canonicalId: params.canonicalId,
      name: params.name,
      betpawaId: params.betpawaId,
      sportybetId: params.sportybetId,
      bet9jaKey: params.bet9jaKey,
      outcomeMapping: params.outcomeMapping.map((o) => ({
        canonicalId: o.canonicalId,
        betpawaName: o.betpawaName,
        sportybetDesc: o.sportybetDesc,
        bet9jaSuffix: o.bet9jaSuffix,
        position: o.position,
      })),
      priority: params.priority,
      reason: params.reason,
    }),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new ApiError(response.status, errorText || `API error: ${response.status}`)
  }

  return response.json()
}

/**
 * Update an existing mapping via PATCH /api/mappings/:canonicalId.
 */
async function updateMapping(params: UpdateMappingParams): Promise<MappingResponse> {
  const body: Record<string, unknown> = { reason: params.reason }

  if (params.name !== undefined) body.name = params.name
  if (params.betpawaId !== undefined) body.betpawaId = params.betpawaId
  if (params.sportybetId !== undefined) body.sportybetId = params.sportybetId
  if (params.bet9jaKey !== undefined) body.bet9jaKey = params.bet9jaKey
  if (params.priority !== undefined) body.priority = params.priority
  if (params.outcomeMapping !== undefined) {
    body.outcomeMapping = params.outcomeMapping.map((o) => ({
      canonicalId: o.canonicalId,
      betpawaName: o.betpawaName,
      sportybetDesc: o.sportybetDesc,
      bet9jaSuffix: o.bet9jaSuffix,
      position: o.position,
    }))
  }

  const response = await fetch(
    `${API_BASE}/mappings/${encodeURIComponent(params.canonicalId)}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }
  )

  if (!response.ok) {
    const errorText = await response.text()
    throw new ApiError(response.status, errorText || `API error: ${response.status}`)
  }

  return response.json()
}

/**
 * Hook for creating a new mapping.
 *
 * Invalidates mapping-related queries on success.
 */
export function useCreateMapping() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: createMapping,
    onSuccess: () => {
      // Invalidate mapping queries to refresh lists
      queryClient.invalidateQueries({ queryKey: ['mappings'] })
      queryClient.invalidateQueries({ queryKey: ['mapping-stats'] })
      queryClient.invalidateQueries({ queryKey: ['mapping-detail'] })
    },
  })
}

/**
 * Hook for updating an existing mapping.
 *
 * Invalidates mapping-related queries on success.
 */
export function useUpdateMapping() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: updateMapping,
    onSuccess: (_data, variables) => {
      // Invalidate mapping queries to refresh lists
      queryClient.invalidateQueries({ queryKey: ['mappings'] })
      queryClient.invalidateQueries({ queryKey: ['mapping-stats'] })
      queryClient.invalidateQueries({
        queryKey: ['mapping-detail', variables.canonicalId],
      })
    },
  })
}
