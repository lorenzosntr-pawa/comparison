import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export interface HighPriorityItem {
  id: number
  source: string
  externalMarketId: string
  marketName: string | null
  firstSeenAt: string
  lastSeenAt: string
  occurrenceCount: number
  status: string
  priorityScore: number
}

export interface HighPriorityUnmappedResponse {
  items: HighPriorityItem[]
}

async function fetchHighPriorityUnmapped(): Promise<HighPriorityUnmappedResponse> {
  const response = await api.get<HighPriorityUnmappedResponse>('/unmapped/high-priority')
  return response
}

export function useHighPriorityUnmapped() {
  return useQuery({
    queryKey: ['unmapped-high-priority'],
    queryFn: fetchHighPriorityUnmapped,
  })
}
