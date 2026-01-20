import type {
  HealthResponse,
  SchedulerStatus,
  RunHistoryResponse,
  SchedulerPlatformHealth,
  MatchedEventList,
} from '@/types/api'

const API_BASE = '/api'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!response.ok) {
    throw new ApiError(response.status, `API error: ${response.status}`)
  }

  return response.json()
}

export const api = {
  // Health
  getHealth: () => fetchJson<HealthResponse>('/health'),

  // Scheduler
  getSchedulerStatus: () => fetchJson<SchedulerStatus>('/scheduler/status'),

  getSchedulerHistory: (params?: {
    limit?: number
    offset?: number
    status?: string
  }) => {
    const searchParams = new URLSearchParams()
    if (params?.limit) searchParams.set('limit', params.limit.toString())
    if (params?.offset) searchParams.set('offset', params.offset.toString())
    if (params?.status) searchParams.set('status', params.status)
    const query = searchParams.toString()
    return fetchJson<RunHistoryResponse>(
      `/scheduler/history${query ? `?${query}` : ''}`
    )
  },

  getSchedulerHealth: () =>
    fetchJson<SchedulerPlatformHealth[]>('/scheduler/health'),

  // Events
  getEvents: (params?: {
    page?: number
    page_size?: number
    min_bookmakers?: number
  }) => {
    const searchParams = new URLSearchParams()
    if (params?.page) searchParams.set('page', params.page.toString())
    if (params?.page_size)
      searchParams.set('page_size', params.page_size.toString())
    if (params?.min_bookmakers)
      searchParams.set('min_bookmakers', params.min_bookmakers.toString())
    const query = searchParams.toString()
    return fetchJson<MatchedEventList>(`/events${query ? `?${query}` : ''}`)
  },
}
