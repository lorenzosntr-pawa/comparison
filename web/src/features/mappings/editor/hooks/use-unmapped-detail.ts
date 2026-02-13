import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

/**
 * Unmapped market detail response matching backend schema.
 */
export interface UnmappedMarketDetail {
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

async function fetchUnmappedDetail(id: number): Promise<UnmappedMarketDetail> {
  return api.get<UnmappedMarketDetail>(`/unmapped/${id}`)
}

/**
 * Hook to fetch unmapped market detail by ID.
 *
 * @param id - The unmapped market ID
 * @returns Query result with unmapped market details
 */
export function useUnmappedDetail(id: number | undefined) {
  return useQuery({
    queryKey: ['unmapped-detail', id],
    queryFn: () => fetchUnmappedDetail(id!),
    enabled: id !== undefined,
  })
}
