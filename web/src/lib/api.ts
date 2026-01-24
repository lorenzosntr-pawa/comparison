import type {
  HealthResponse,
  SchedulerStatus,
  RunHistoryResponse,
  SchedulerPlatformHealth,
  MatchedEventList,
  EventDetailResponse,
  SettingsResponse,
  SettingsUpdate,
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
  // Generic GET for simple endpoints
  get: <T>(url: string) => fetchJson<T>(url),

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
    tournament_ids?: number[]
    sport_id?: number
    kickoff_from?: string
    kickoff_to?: string
    search?: string
    availability?: 'betpawa' | 'competitor'
  }) => {
    const searchParams = new URLSearchParams()
    if (params?.page) searchParams.set('page', params.page.toString())
    if (params?.page_size)
      searchParams.set('page_size', params.page_size.toString())
    if (params?.min_bookmakers)
      searchParams.set('min_bookmakers', params.min_bookmakers.toString())
    if (params?.tournament_ids && params.tournament_ids.length > 0) {
      // FastAPI expects repeated query params for lists
      params.tournament_ids.forEach((id) =>
        searchParams.append('tournament_ids', id.toString())
      )
    }
    if (params?.sport_id)
      searchParams.set('sport_id', params.sport_id.toString())
    if (params?.kickoff_from)
      searchParams.set('kickoff_from', params.kickoff_from)
    if (params?.kickoff_to)
      searchParams.set('kickoff_to', params.kickoff_to)
    if (params?.search) searchParams.set('search', params.search)
    if (params?.availability)
      searchParams.set('availability', params.availability)
    const query = searchParams.toString()
    return fetchJson<MatchedEventList>(`/events${query ? `?${query}` : ''}`)
  },

  getEventDetail: (id: number) =>
    fetchJson<EventDetailResponse>(`/events/${id}`),

  // Tournaments
  getTournaments: () =>
    fetchJson<Array<{ id: number; name: string; country: string | null }>>(
      '/events/tournaments'
    ),

  // Settings
  getSettings: () => fetchJson<SettingsResponse>('/settings'),

  updateSettings: (data: SettingsUpdate) =>
    fetchJson<SettingsResponse>('/settings', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  pauseScheduler: () =>
    fetchJson<void>('/scheduler/pause', { method: 'POST' }),

  resumeScheduler: () =>
    fetchJson<void>('/scheduler/resume', { method: 'POST' }),
}
