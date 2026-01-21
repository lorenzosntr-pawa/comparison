// Health endpoint types
export interface PlatformHealth {
  platform: string
  status: 'healthy' | 'unhealthy'
  response_time_ms?: number
  error?: string
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy'
  database: 'connected' | 'disconnected'
  platforms: PlatformHealth[]
}

// Scheduler types
export interface JobStatus {
  id: string
  next_run: string | null
  trigger_type: string
  interval_minutes: number | null
}

export interface SchedulerStatus {
  running: boolean
  paused: boolean
  jobs: JobStatus[]
}

// Settings types
export interface SettingsResponse {
  scrapeIntervalMinutes: number
  enabledPlatforms: string[]
  updatedAt: string | null
}

export interface SettingsUpdate {
  scrapeIntervalMinutes?: number
  enabledPlatforms?: string[]
}

export interface RunHistoryEntry {
  id: number
  status: 'pending' | 'running' | 'completed' | 'partial' | 'failed'
  started_at: string
  completed_at: string | null
  events_scraped: number
  events_failed: number
  trigger: string
  duration_seconds: number | null
}

export interface RunHistoryResponse {
  runs: RunHistoryEntry[]
  total: number
}

export interface SchedulerPlatformHealth {
  platform: string
  healthy: boolean
  last_success: string | null
}

// Events types
export interface OutcomeOdds {
  name: string
  odds: number
}

export interface InlineOdds {
  market_id: string
  market_name: string
  line: number | null
  outcomes: OutcomeOdds[]
}

export interface BookmakerOdds {
  bookmaker_slug: string
  bookmaker_name: string
  external_event_id: string
  event_url: string | null
  has_odds: boolean
  inline_odds: InlineOdds[]
}

export interface MatchedEvent {
  id: number
  sportradar_id: string
  name: string
  home_team: string
  away_team: string
  kickoff: string
  tournament_id: number
  tournament_name: string
  tournament_country: string | null
  sport_name: string
  bookmakers: BookmakerOdds[]
  created_at: string
}

export interface MatchedEventList {
  events: MatchedEvent[]
  total: number
  page: number
  page_size: number
}

// Event detail types
export interface MarketOutcome {
  name: string
  odds: number
  is_active: boolean
}

export interface MarketOddsDetail {
  betpawa_market_id: string
  betpawa_market_name: string
  line: number | null
  outcomes: MarketOutcome[]
  margin: number
}

export interface BookmakerMarketData {
  bookmaker_slug: string
  bookmaker_name: string
  snapshot_time: string
  markets: MarketOddsDetail[]
}

export interface EventDetailResponse extends MatchedEvent {
  markets_by_bookmaker: BookmakerMarketData[]
}
