import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function useSchedulerStatus() {
  return useQuery({
    queryKey: ['scheduler', 'status'],
    queryFn: () => api.getSchedulerStatus(),
    refetchInterval: 10000, // Poll every 10s
  })
}

export function useSchedulerHistory(limit = 5) {
  return useQuery({
    queryKey: ['scheduler', 'history', limit],
    queryFn: () => api.getSchedulerHistory({ limit }),
    refetchInterval: 30000,
  })
}

export function useSchedulerHealth() {
  return useQuery({
    queryKey: ['scheduler', 'health'],
    queryFn: () => api.getSchedulerHealth(),
    refetchInterval: 30000,
  })
}
