/**
 * Hooks for fetching storage metrics and cleanup history.
 *
 * @module use-storage
 * @description TanStack Query hooks for storage size APIs.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

/** Table size information */
export interface TableSize {
  table_name: string
  size_bytes: number
  row_count: number
}

/** Storage sizes response */
export interface StorageSizes {
  total_bytes: number
  tables: TableSize[]
  sampled_at: string
}

/** Storage history sample */
export interface StorageSample {
  id: number
  total_bytes: number
  sampled_at: string
}

/** Storage history response */
export interface StorageHistory {
  samples: StorageSample[]
  sample_count: number
  date_range: {
    from: string | null
    to: string | null
  }
}

/** Cleanup run record */
export interface CleanupRun {
  id: number
  trigger: 'manual' | 'scheduled'
  started_at: string
  completed_at: string | null
  duration_ms: number | null
  records_deleted: number | null
  status: 'running' | 'completed' | 'failed'
  error_message: string | null
}

/** Cleanup history response */
export interface CleanupHistory {
  runs: CleanupRun[]
  total_count: number
}

/**
 * Fetch current storage sizes.
 */
export function useStorageSizes() {
  return useQuery({
    queryKey: ['storage', 'sizes'],
    queryFn: async (): Promise<StorageSizes> => {
      return api.get<StorageSizes>('/storage/sizes')
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

/**
 * Fetch storage history samples.
 */
export function useStorageHistory(days: number = 30) {
  return useQuery({
    queryKey: ['storage', 'history', days],
    queryFn: async (): Promise<StorageHistory> => {
      return api.get<StorageHistory>(`/storage/history?days=${days}`)
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

/**
 * Fetch cleanup run history.
 */
export function useCleanupHistory(limit: number = 10) {
  return useQuery({
    queryKey: ['cleanup', 'history', limit],
    queryFn: async (): Promise<CleanupHistory> => {
      return api.get<CleanupHistory>(`/cleanup/history?limit=${limit}`)
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

/** Storage alert record */
export interface StorageAlert {
  id: number
  createdAt: string
  alertType: 'growth_warning' | 'size_critical'
  message: string
  currentBytes: number
  previousBytes: number
  growthPercent: number
  resolvedAt: string | null
}

/** Storage alerts response */
export interface StorageAlertsResponse {
  alerts: StorageAlert[]
  count: number
}

/**
 * Fetch active storage alerts.
 */
export function useStorageAlerts() {
  return useQuery({
    queryKey: ['storage', 'alerts'],
    queryFn: async (): Promise<StorageAlertsResponse> => {
      return api.get<StorageAlertsResponse>('/storage/alerts')
    },
    staleTime: 1000 * 60, // 1 minute
  })
}

/**
 * Mutation to resolve (dismiss) a storage alert.
 */
export function useResolveAlert() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (alertId: number): Promise<StorageAlert> => {
      return api.post<StorageAlert>(`/storage/alerts/${alertId}/resolve`)
    },
    onSuccess: () => {
      // Invalidate alerts query to refresh list
      queryClient.invalidateQueries({ queryKey: ['storage', 'alerts'] })
    },
  })
}
