import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export interface PlatformCounts {
  betpawaCount: number
  sportybetCount: number
  bet9JaCount: number
}

export interface UnmappedCounts {
  new: number
  acknowledged: number
  mapped: number
  ignored: number
}

export interface MappingStats {
  totalMappings: number
  codeMappings: number
  dbMappings: number
  byPlatform: PlatformCounts
  unmappedCounts: UnmappedCounts
  cacheLoadedAt: string | null
}

async function fetchMappingStats(): Promise<MappingStats> {
  const response = await api.get<MappingStats>('/mappings/stats')
  return response
}

export function useMappingStats() {
  return useQuery({
    queryKey: ['mapping-stats'],
    queryFn: fetchMappingStats,
  })
}
