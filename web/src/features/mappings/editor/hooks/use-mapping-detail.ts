import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { MappingDetailResponse } from '../components/target-market-form'

/**
 * Fetch mapping detail by canonical ID.
 */
async function fetchMappingDetail(canonicalId: string): Promise<MappingDetailResponse> {
  return api.get<MappingDetailResponse>(`/mappings/${encodeURIComponent(canonicalId)}`)
}

/**
 * Hook to fetch mapping detail by canonical ID.
 *
 * @param canonicalId - The mapping canonical ID
 * @returns Query result with mapping details
 */
export function useMappingDetail(canonicalId: string | undefined) {
  return useQuery({
    queryKey: ['mapping-detail', canonicalId],
    queryFn: () => fetchMappingDetail(canonicalId!),
    enabled: !!canonicalId,
  })
}
