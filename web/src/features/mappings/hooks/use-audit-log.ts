import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export interface AuditLogItem {
  id: number
  canonicalId: string
  action: string
  reason: string | null
  createdAt: string
  createdBy: string | null
}

export interface AuditLogResponse {
  items: AuditLogItem[]
  total: number
  page: number
  pageSize: number
}

interface UseAuditLogOptions {
  page?: number
  pageSize?: number
  action?: string
}

async function fetchAuditLog(options: UseAuditLogOptions): Promise<AuditLogResponse> {
  const params = new URLSearchParams()
  params.set('page', String(options.page ?? 1))
  params.set('page_size', String(options.pageSize ?? 10))
  if (options.action) {
    params.set('action', options.action)
  }
  return api.get<AuditLogResponse>(`/mappings/audit-log?${params.toString()}`)
}

export function useAuditLog(options: UseAuditLogOptions = {}) {
  const { page = 1, pageSize = 10, action } = options

  return useQuery({
    queryKey: ['mapping-audit-log', { page, pageSize, action }],
    queryFn: () => fetchAuditLog({ page, pageSize, action }),
  })
}
