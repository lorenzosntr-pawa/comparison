/**
 * API client for communicating with the FastAPI backend.
 *
 * @module api
 * @description Provides typed fetch wrappers for all backend endpoints including
 * health checks, scheduler management, event browsing, settings, palimpsest coverage,
 * data cleanup, and historical odds/margin data. Uses a centralized fetchJson helper
 * for consistent error handling and JSON parsing across all API calls.
 *
 * @example
 * ```typescript
 * import { api, ApiError } from '@/lib/api'
 *
 * // Fetch health status
 * const health = await api.getHealth()
 *
 * // Handle API errors
 * try {
 *   const events = await api.getEvents({ page: 1 })
 * } catch (error) {
 *   if (error instanceof ApiError && error.status === 404) {
 *     console.log('Not found')
 *   }
 * }
 * ```
 */

import type {
  HealthResponse,
  SchedulerStatus,
  RunHistoryResponse,
  SchedulerPlatformHealth,
  MatchedEventList,
  EventDetailResponse,
  SettingsResponse,
  SettingsUpdate,
  CoverageStats,
  PalimpsestEventsResponse,
  DataStats,
  CleanupPreview,
  CleanupResult,
  CleanupHistoryResponse,
  OddsHistoryResponse,
  MarginHistoryResponse,
} from '@/types/api'

/** Base URL prefix for all API endpoints */
const API_BASE = '/api'

/**
 * Custom error class for API response errors.
 *
 * @description Thrown when the API returns a non-2xx status code.
 * Includes the HTTP status code for conditional error handling in calling code.
 *
 * @example
 * ```typescript
 * try {
 *   await api.getEventDetail(123)
 * } catch (error) {
 *   if (error instanceof ApiError) {
 *     if (error.status === 404) {
 *       // Handle not found
 *     } else if (error.status >= 500) {
 *       // Handle server error
 *     }
 *   }
 * }
 * ```
 */
export class ApiError extends Error {
  /** HTTP status code from the failed response */
  status: number

  /**
   * Creates a new ApiError instance.
   *
   * @param status - The HTTP status code from the response
   * @param message - Error message describing the failure
   */
  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/**
 * Generic JSON fetch helper with error handling.
 *
 * @description Performs a fetch request to the API, automatically handling
 * JSON content-type headers and parsing. Throws ApiError for non-2xx responses.
 *
 * @template T - The expected response type
 * @param url - The API endpoint path (without base URL)
 * @param options - Optional fetch request configuration
 * @returns Promise resolving to the parsed JSON response
 * @throws {ApiError} When the response status is not ok (non-2xx)
 *
 * @internal This function is used internally by the api object methods
 */
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

/**
 * API client object containing typed methods for all backend endpoints.
 *
 * @description Organized by endpoint category: health, scheduler, events,
 * tournaments, settings, scrape, palimpsest coverage, cleanup, and history.
 * All methods return Promises that resolve to typed response objects.
 */
export const api = {
  // ─────────────────────────────────────────────────────────────────────────────
  // Generic
  // ─────────────────────────────────────────────────────────────────────────────

  /**
   * Generic GET request for simple endpoints.
   *
   * @template T - The expected response type
   * @param url - The API endpoint path
   * @returns Promise resolving to the typed response
   */
  get: <T>(url: string) => fetchJson<T>(url),

  // ─────────────────────────────────────────────────────────────────────────────
  // Health
  // ─────────────────────────────────────────────────────────────────────────────

  /**
   * Fetches the overall system health status.
   *
   * @returns Promise resolving to health status including database and platform health
   */
  getHealth: () => fetchJson<HealthResponse>('/health'),

  // ─────────────────────────────────────────────────────────────────────────────
  // Scheduler
  // ─────────────────────────────────────────────────────────────────────────────

  /**
   * Fetches the current scheduler status.
   *
   * @returns Promise resolving to scheduler running state and job information
   */
  getSchedulerStatus: () => fetchJson<SchedulerStatus>('/scheduler/status'),

  /**
   * Fetches paginated scrape run history.
   *
   * @param params - Optional pagination and filter parameters
   * @param params.limit - Maximum number of runs to return
   * @param params.offset - Number of runs to skip
   * @param params.status - Filter by run status
   * @returns Promise resolving to run history with pagination info
   */
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

  /**
   * Fetches health status for each scraping platform.
   *
   * @returns Promise resolving to array of platform health statuses
   */
  getSchedulerHealth: () =>
    fetchJson<SchedulerPlatformHealth[]>('/scheduler/health'),

  // ─────────────────────────────────────────────────────────────────────────────
  // Events
  // ─────────────────────────────────────────────────────────────────────────────

  /**
   * Fetches paginated list of matched events with optional filters.
   *
   * @param params - Optional pagination and filter parameters
   * @param params.page - Page number (1-indexed)
   * @param params.page_size - Number of events per page
   * @param params.min_bookmakers - Minimum number of bookmakers with odds
   * @param params.tournament_ids - Filter by tournament IDs
   * @param params.sport_id - Filter by sport ID
   * @param params.kickoff_from - Filter by minimum kickoff time (ISO string)
   * @param params.kickoff_to - Filter by maximum kickoff time (ISO string)
   * @param params.search - Search string for event/team names
   * @param params.availability - Filter by platform availability
   * @param params.countries - Filter by country/region names
   * @param params.include_started - Whether to include already-started events
   * @returns Promise resolving to paginated event list
   */
  getEvents: (params?: {
    page?: number
    page_size?: number
    min_bookmakers?: number
    tournament_ids?: number[]
    sport_id?: number
    kickoff_from?: string
    kickoff_to?: string
    search?: string
    availability?: 'betpawa' | 'competitor' | 'alerts'
    countries?: string[]
    include_started?: boolean
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
    if (params?.countries && params.countries.length > 0) {
      // FastAPI expects repeated query params for lists
      params.countries.forEach((country) =>
        searchParams.append('countries', country)
      )
    }
    if (params?.include_started)
      searchParams.set('include_started', 'true')
    const query = searchParams.toString()
    return fetchJson<MatchedEventList>(`/events${query ? `?${query}` : ''}`)
  },

  /**
   * Fetches detailed information for a single event.
   *
   * @param id - The event ID
   * @returns Promise resolving to event details including all markets by bookmaker
   */
  getEventDetail: (id: number) =>
    fetchJson<EventDetailResponse>(`/events/${id}`),

  /**
   * Fetches the count of events with availability alerts.
   *
   * @returns Promise resolving to object with count of events with unavailable markets
   */
  getAlertsCount: () => fetchJson<{ count: number }>('/events/alerts/count'),

  // ─────────────────────────────────────────────────────────────────────────────
  // Tournaments
  // ─────────────────────────────────────────────────────────────────────────────

  /**
   * Fetches list of tournaments for filter dropdowns.
   *
   * @param params - Optional filter parameters
   * @param params.availability - Filter by platform availability
   * @returns Promise resolving to array of tournament objects with id, name, and country
   */
  getTournaments: (params?: {
    availability?: 'betpawa' | 'competitor'
  }) => {
    const searchParams = new URLSearchParams()
    if (params?.availability)
      searchParams.set('availability', params.availability)
    const query = searchParams.toString()
    return fetchJson<Array<{ id: number; name: string; country: string | null }>>(
      `/events/tournaments${query ? `?${query}` : ''}`
    )
  },

  /**
   * Fetches list of countries for filter dropdowns.
   *
   * @param params - Optional filter parameters
   * @param params.availability - Filter by platform availability
   * @returns Promise resolving to array of country names
   */
  getCountries: (params?: {
    availability?: 'betpawa' | 'competitor'
  }) => {
    const searchParams = new URLSearchParams()
    if (params?.availability)
      searchParams.set('availability', params.availability)
    const query = searchParams.toString()
    return fetchJson<string[]>(
      `/events/countries${query ? `?${query}` : ''}`
    )
  },

  // ─────────────────────────────────────────────────────────────────────────────
  // Settings
  // ─────────────────────────────────────────────────────────────────────────────

  /**
   * Fetches current application settings.
   *
   * @returns Promise resolving to all settings including scrape interval and retention periods
   */
  getSettings: () => fetchJson<SettingsResponse>('/settings'),

  /**
   * Updates application settings.
   *
   * @param data - Partial settings object with fields to update
   * @returns Promise resolving to the updated settings
   */
  updateSettings: (data: SettingsUpdate) =>
    fetchJson<SettingsResponse>('/settings', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  /**
   * Pauses the scheduler, preventing automatic scrapes.
   *
   * @returns Promise resolving when scheduler is paused
   */
  pauseScheduler: () =>
    fetchJson<void>('/scheduler/pause', { method: 'POST' }),

  /**
   * Resumes the scheduler after being paused.
   *
   * @returns Promise resolving when scheduler is resumed
   */
  resumeScheduler: () =>
    fetchJson<void>('/scheduler/resume', { method: 'POST' }),

  // ─────────────────────────────────────────────────────────────────────────────
  // Scrape
  // ─────────────────────────────────────────────────────────────────────────────

  /**
   * Triggers a manual scrape run.
   *
   * @returns Promise resolving to object containing the new scrape_run_id
   */
  triggerScrape: () =>
    fetchJson<{ scrape_run_id: number }>('/scrape', { method: 'POST' }),

  // ─────────────────────────────────────────────────────────────────────────────
  // Palimpsest Coverage
  // ─────────────────────────────────────────────────────────────────────────────

  /**
   * Fetches palimpsest coverage statistics.
   *
   * @param params - Optional parameters
   * @param params.includeStarted - Whether to include already-started events
   * @returns Promise resolving to coverage stats by platform
   */
  getCoverage: (params?: { includeStarted?: boolean }) => {
    const searchParams = new URLSearchParams()
    if (params?.includeStarted) searchParams.set('include_started', 'true')
    const query = searchParams.toString()
    return fetchJson<CoverageStats>(`/palimpsest/coverage${query ? `?${query}` : ''}`)
  },

  /**
   * Fetches palimpsest events grouped by tournament.
   *
   * @param params - Optional filter and sort parameters
   * @param params.availability - Filter by event availability status
   * @param params.platforms - Filter by platform slugs
   * @param params.sport_id - Filter by sport ID
   * @param params.search - Search string for event/team names
   * @param params.sort - Sort by kickoff time or tournament
   * @param params.include_started - Whether to include already-started events
   * @returns Promise resolving to coverage stats and tournament groups with events
   */
  getPalimpsestEvents: (params?: {
    availability?: 'betpawa-only' | 'competitor-only' | 'matched'
    platforms?: string[]
    sport_id?: number
    search?: string
    sort?: 'kickoff' | 'tournament'
    include_started?: boolean
  }) => {
    const searchParams = new URLSearchParams()
    if (params?.availability)
      searchParams.set('availability', params.availability)
    if (params?.platforms && params.platforms.length > 0) {
      params.platforms.forEach((p) => searchParams.append('platforms', p))
    }
    if (params?.sport_id)
      searchParams.set('sport_id', params.sport_id.toString())
    if (params?.search) searchParams.set('search', params.search)
    if (params?.sort) searchParams.set('sort', params.sort)
    if (params?.include_started) searchParams.set('include_started', 'true')
    const query = searchParams.toString()
    return fetchJson<PalimpsestEventsResponse>(
      `/palimpsest/events${query ? `?${query}` : ''}`
    )
  },

  // ─────────────────────────────────────────────────────────────────────────────
  // Cleanup
  // ─────────────────────────────────────────────────────────────────────────────

  /**
   * Fetches current data statistics for cleanup planning.
   *
   * @returns Promise resolving to counts and date ranges for all data tables
   */
  getCleanupStats: () => fetchJson<DataStats>('/cleanup/stats'),

  /**
   * Previews what data would be deleted with given retention settings.
   *
   * @param params - Optional retention period overrides
   * @param params.oddsDays - Days of odds data to retain
   * @param params.matchDays - Days of match data to retain
   * @returns Promise resolving to preview of records that would be deleted
   */
  getCleanupPreview: (params?: { oddsDays?: number; matchDays?: number }) => {
    const searchParams = new URLSearchParams()
    if (params?.oddsDays)
      searchParams.set('odds_days', params.oddsDays.toString())
    if (params?.matchDays)
      searchParams.set('match_days', params.matchDays.toString())
    const query = searchParams.toString()
    return fetchJson<CleanupPreview>(`/cleanup/preview${query ? `?${query}` : ''}`)
  },

  /**
   * Executes data cleanup with given retention settings.
   *
   * @param params - Optional retention period overrides
   * @param params.oddsDays - Days of odds data to retain
   * @param params.matchDays - Days of match data to retain
   * @returns Promise resolving to cleanup result with deletion counts
   */
  executeCleanup: (params?: { oddsDays?: number; matchDays?: number }) =>
    fetchJson<CleanupResult>('/cleanup/execute', {
      method: 'POST',
      body: JSON.stringify({
        oddsRetentionDays: params?.oddsDays,
        matchRetentionDays: params?.matchDays,
      }),
    }),

  /**
   * Fetches history of past cleanup runs.
   *
   * @param limit - Maximum number of runs to return (default: 10)
   * @returns Promise resolving to list of cleanup runs with stats
   */
  getCleanupHistory: (limit = 10) =>
    fetchJson<CleanupHistoryResponse>(`/cleanup/history?limit=${limit}`),

  // ─────────────────────────────────────────────────────────────────────────────
  // History
  // ─────────────────────────────────────────────────────────────────────────────

  /**
   * Fetches historical odds data for a specific market.
   *
   * @param params - Query parameters
   * @param params.eventId - The event ID
   * @param params.marketId - The market ID (e.g., "1x2", "over_under_2.5")
   * @param params.bookmakerSlug - The bookmaker slug
   * @param params.fromTime - Optional start time filter (ISO string)
   * @param params.toTime - Optional end time filter (ISO string)
   * @param params.line - Optional line value for specifier markets (e.g., 2.5 for Over/Under)
   * @returns Promise resolving to odds history timeline
   */
  getOddsHistory: (params: {
    eventId: number
    marketId: string
    bookmakerSlug: string
    fromTime?: string
    toTime?: string
    line?: number | null
  }) => {
    const searchParams = new URLSearchParams()
    searchParams.set('bookmaker_slug', params.bookmakerSlug)
    if (params.fromTime) searchParams.set('from_time', params.fromTime)
    if (params.toTime) searchParams.set('to_time', params.toTime)
    if (params.line != null) searchParams.set('line', params.line.toString())
    return fetchJson<OddsHistoryResponse>(
      `/events/${params.eventId}/markets/${encodeURIComponent(params.marketId)}/history?${searchParams}`
    )
  },

  /**
   * Fetches historical margin data for a specific market.
   *
   * @param params - Query parameters
   * @param params.eventId - The event ID
   * @param params.marketId - The market ID (e.g., "1x2", "over_under_2.5")
   * @param params.bookmakerSlug - The bookmaker slug
   * @param params.fromTime - Optional start time filter (ISO string)
   * @param params.toTime - Optional end time filter (ISO string)
   * @param params.line - Optional line value for specifier markets (e.g., 2.5 for Over/Under)
   * @returns Promise resolving to margin history timeline
   */
  getMarginHistory: (params: {
    eventId: number
    marketId: string
    bookmakerSlug: string
    fromTime?: string
    toTime?: string
    line?: number | null
  }) => {
    const searchParams = new URLSearchParams()
    searchParams.set('bookmaker_slug', params.bookmakerSlug)
    if (params.fromTime) searchParams.set('from_time', params.fromTime)
    if (params.toTime) searchParams.set('to_time', params.toTime)
    if (params.line != null) searchParams.set('line', params.line.toString())
    return fetchJson<MarginHistoryResponse>(
      `/events/${params.eventId}/markets/${encodeURIComponent(params.marketId)}/margin-history?${searchParams}`
    )
  },
}
