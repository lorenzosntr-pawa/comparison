/**
 * Hooks for fetching storage metrics and cleanup history.
 *
 * @module use-storage
 * @description TanStack Query hooks for storage size APIs.
 */

import { useQuery } from '@tanstack/react-query'
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
      const res = await api.get('/storage/sizes')
      return res.data
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
      const res = await api.get(`/storage/history?days=${days}`)
      return res.data
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
      const res = await api.get(`/cleanup/history?limit=${limit}`)
      return res.data
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}
