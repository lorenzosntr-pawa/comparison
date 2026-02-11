/**
 * API response type definitions for the betpawa comparison system.
 *
 * @module types/api
 * @description Defines TypeScript interfaces for all API responses from the FastAPI backend.
 * Types are organized by endpoint category: health, scheduler, settings, events,
 * palimpsest coverage, cleanup, and historical data.
 *
 * These types ensure type safety between the frontend and backend, providing
 * autocomplete and compile-time error checking for API responses.
 */

// ─────────────────────────────────────────────────────────────────────────────
// Health Endpoint Types
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Health status for an individual scraping platform.
 *
 * @description Reports whether a specific bookmaker platform is reachable
 * and responding within acceptable time limits.
 */
export interface PlatformHealth {
  /** Platform identifier/slug (e.g., "betpawa", "sportybet") */
  platform: string
  /** Current health status */
  status: 'healthy' | 'unhealthy'
  /** Response time in milliseconds (only when healthy) */
  response_time_ms?: number
  /** Error message (only when unhealthy) */
  error?: string
}

/**
 * Overall system health response.
 *
 * @description Aggregates health status from database and all platforms
 * to provide a single system-wide health indicator.
 */
export interface HealthResponse {
  /** Aggregate system health: healthy (all ok), degraded (some issues), unhealthy (critical) */
  status: 'healthy' | 'degraded' | 'unhealthy'
  /** Database connection status */
  database: 'connected' | 'disconnected'
  /** Individual platform health statuses */
  platforms: PlatformHealth[]
}

// ─────────────────────────────────────────────────────────────────────────────
// Scheduler Types
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Status of a scheduled job.
 *
 * @description Represents a single APScheduler job with its scheduling configuration.
 */
export interface JobStatus {
  /** Unique job identifier */
  id: string
  /** ISO timestamp of next scheduled run, or null if not scheduled */
  next_run: string | null
  /** Type of trigger (e.g., "interval", "cron") */
  trigger_type: string
  /** Interval in minutes for interval triggers */
  interval_minutes: number | null
}

/**
 * Overall scheduler status.
 *
 * @description Reports whether the scheduler is running and lists all configured jobs.
 */
export interface SchedulerStatus {
  /** Whether the scheduler is currently running */
  running: boolean
  /** Whether the scheduler is paused (not executing jobs) */
  paused: boolean
  /** List of all configured jobs */
  jobs: JobStatus[]
}

// ─────────────────────────────────────────────────────────────────────────────
// Settings Types
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Application settings response.
 *
 * @description Contains all configurable settings for the scraping system
 * including intervals, enabled platforms, and data retention policies.
 */
export interface SettingsResponse {
  /** Minutes between automatic scrape runs */
  scrapeIntervalMinutes: number
  /** List of enabled platform slugs for scraping */
  enabledPlatforms: string[]
  /** Days to retain odds snapshot data */
  oddsRetentionDays: number
  /** Days to retain match/event data */
  matchRetentionDays: number
  /** Hours between automatic cleanup runs */
  cleanupFrequencyHours: number
  /** ISO timestamp of last settings update, or null if never updated */
  updatedAt: string | null
}

/**
 * Partial settings update request.
 *
 * @description All fields are optional - only provided fields will be updated.
 */
export interface SettingsUpdate {
  /** Minutes between automatic scrape runs */
  scrapeIntervalMinutes?: number
  /** List of enabled platform slugs for scraping */
  enabledPlatforms?: string[]
  /** Days to retain odds snapshot data */
  oddsRetentionDays?: number
  /** Days to retain match/event data */
  matchRetentionDays?: number
  /** Hours between automatic cleanup runs */
  cleanupFrequencyHours?: number
}

/**
 * Single scrape run history entry.
 *
 * @description Records details of a completed or in-progress scrape run
 * including timing, success counts, and per-platform performance.
 */
export interface RunHistoryEntry {
  /** Unique run identifier */
  id: number
  /** Current status of the run */
  status: 'pending' | 'running' | 'completed' | 'partial' | 'failed'
  /** ISO timestamp when run started */
  started_at: string
  /** ISO timestamp when run completed, or null if still running */
  completed_at: string | null
  /** Number of events successfully scraped */
  events_scraped: number
  /** Number of events that failed to scrape */
  events_failed: number
  /** What triggered the run (e.g., "scheduled", "manual") */
  trigger: string
  /** Total run duration in seconds, or null if still running */
  duration_seconds: number | null
  /** Per-platform timing and event counts, or null if not available */
  platform_timings: Record<string, { duration_ms: number; events_count: number }> | null
}

/**
 * Paginated run history response.
 */
export interface RunHistoryResponse {
  /** List of run history entries */
  runs: RunHistoryEntry[]
  /** Total number of runs in database */
  total: number
}

/**
 * Platform health status from scheduler perspective.
 *
 * @description Tracks whether recent scrapes for a platform have been successful.
 */
export interface SchedulerPlatformHealth {
  /** Platform identifier/slug */
  platform: string
  /** Whether the platform is considered healthy based on recent scrapes */
  healthy: boolean
  /** ISO timestamp of last successful scrape, or null if never succeeded */
  last_success: string | null
}

// ─────────────────────────────────────────────────────────────────────────────
// Events Types
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Single betting outcome with its odds.
 *
 * @description Represents one selection in a market (e.g., "Home" at 2.10 odds).
 */
export interface OutcomeOdds {
  /** Outcome name (e.g., "Home", "Draw", "Away", "Over", "Under") */
  name: string
  /** Decimal odds value */
  odds: number
}

/**
 * Market odds displayed inline in event lists.
 *
 * @description Compact representation of a market's odds for list views,
 * including calculated margin.
 *
 * Availability states:
 * - `available=true, unavailable_since=null`: Market is currently offered
 * - `available=false, unavailable_since=timestamp`: Market became unavailable at that time
 * - Market not in response at all: Never offered (shown as dash in UI)
 */
export interface InlineOdds {
  /** Unique market identifier (e.g., "1x2", "over_under_2.5") */
  market_id: string
  /** Human-readable market name */
  market_name: string
  /** Line value for handicap/total markets, or null for non-line markets */
  line: number | null
  /** List of outcomes with their odds */
  outcomes: OutcomeOdds[]
  /** Calculated bookmaker margin percentage, or null if not calculable */
  margin: number | null
  /** Whether this market is currently available for betting (default true) */
  available?: boolean
  /** ISO timestamp when market became unavailable, or null if available (default null) */
  unavailable_since?: string | null
}

/**
 * Bookmaker's odds data for an event.
 *
 * @description Contains all odds data from a single bookmaker for an event,
 * including identification info and market odds.
 */
export interface BookmakerOdds {
  /** Unique bookmaker identifier */
  bookmaker_slug: string
  /** Display name for the bookmaker */
  bookmaker_name: string
  /** Bookmaker's internal event ID */
  external_event_id: string
  /** Direct URL to the event on bookmaker's site, or null if not available */
  event_url: string | null
  /** Whether this bookmaker has odds for this event */
  has_odds: boolean
  /** List of market odds for inline display */
  inline_odds: InlineOdds[]
  /** ISO timestamp when odds were captured, or null if no snapshot */
  snapshot_time: string | null
}

/**
 * Matched event with bookmaker odds.
 *
 * @description An event that has been matched across bookmakers via Sportradar ID,
 * with odds data from each bookmaker that covers the event.
 */
export interface MatchedEvent {
  /** Internal event ID */
  id: number
  /** Sportradar unique identifier for cross-bookmaker matching */
  sportradar_id: string
  /** Event name (typically "Home vs Away") */
  name: string
  /** Home team name */
  home_team: string
  /** Away team name */
  away_team: string
  /** ISO timestamp of event kickoff */
  kickoff: string
  /** Tournament ID this event belongs to */
  tournament_id: number
  /** Tournament name */
  tournament_name: string
  /** Tournament country, or null if international */
  tournament_country: string | null
  /** Sport name (e.g., "Soccer", "Basketball") */
  sport_name: string
  /** Odds data from each bookmaker */
  bookmakers: BookmakerOdds[]
  /** ISO timestamp when event was first created */
  created_at: string
}

/**
 * Paginated list of matched events.
 */
export interface MatchedEventList {
  /** List of events on this page */
  events: MatchedEvent[]
  /** Total number of matching events */
  total: number
  /** Current page number (1-indexed) */
  page: number
  /** Number of events per page */
  page_size: number
}

// ─────────────────────────────────────────────────────────────────────────────
// Event Detail Types
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Market outcome with active status.
 *
 * @description Extended outcome including whether the selection is currently active/available.
 */
export interface MarketOutcome {
  /** Outcome name */
  name: string
  /** Decimal odds value */
  odds: number
  /** Whether this outcome is currently active/available for betting */
  is_active: boolean
}

/**
 * Detailed market odds data.
 *
 * @description Full market information including grouping metadata for display.
 *
 * Availability states:
 * - `available=true, unavailable_since=null`: Market is currently offered
 * - `available=false, unavailable_since=timestamp`: Market became unavailable at that time
 * - Market not in response at all: Never offered (shown as dash in UI)
 */
export interface MarketOddsDetail {
  /** Betpawa's market identifier (used as canonical market ID) */
  betpawa_market_id: string
  /** Display name for the market */
  betpawa_market_name: string
  /** Line value for handicap/total markets, or null */
  line: number | null
  /** List of outcomes with odds and active status */
  outcomes: MarketOutcome[]
  /** Calculated bookmaker margin percentage */
  margin: number
  /** Market group categories for organization (e.g., ["Main", "Goals"]), or null */
  market_groups: string[] | null
  /** Whether this market is currently available for betting (default true) */
  available?: boolean
  /** ISO timestamp when market became unavailable, or null if available (default null) */
  unavailable_since?: string | null
}

/**
 * All market data from a single bookmaker.
 *
 * @description Contains the complete set of markets offered by a bookmaker for an event.
 */
export interface BookmakerMarketData {
  /** Bookmaker identifier */
  bookmaker_slug: string
  /** Bookmaker display name */
  bookmaker_name: string
  /** ISO timestamp when this data was captured */
  snapshot_time: string
  /** List of all markets offered */
  markets: MarketOddsDetail[]
}

/**
 * Full event detail response.
 *
 * @description Extends MatchedEvent with complete market data organized by bookmaker.
 */
export interface EventDetailResponse extends MatchedEvent {
  /** Complete market data grouped by bookmaker */
  markets_by_bookmaker: BookmakerMarketData[]
}

// ─────────────────────────────────────────────────────────────────────────────
// Palimpsest Coverage Types
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Coverage statistics for a single platform.
 *
 * @description Shows how well a competitor platform's events match with betpawa's palimpsest.
 */
export interface PlatformCoverage {
  /** Platform identifier */
  platform: string
  /** Total events on this platform */
  total_events: number
  /** Events matched with betpawa */
  matched_events: number
  /** Events not matched with betpawa */
  unmatched_events: number
  /** Match rate as decimal (0-1) */
  match_rate: number
}

/**
 * Coverage breakdown for a tournament.
 */
export interface TournamentCoverage {
  /** Total events in tournament */
  total: number
  /** Events available on both betpawa and competitors */
  matched: number
  /** Events only on betpawa */
  betpawa_only: number
  /** Events only on competitors */
  competitor_only: number
}

/**
 * Overall palimpsest coverage statistics.
 *
 * @description Aggregate statistics showing how betpawa's event coverage
 * compares to competitor platforms.
 */
export interface CoverageStats {
  /** Total unique events across all platforms */
  total_events: number
  /** Events matched between betpawa and at least one competitor */
  matched_count: number
  /** Events only available on betpawa */
  betpawa_only_count: number
  /** Events only available on competitors */
  competitor_only_count: number
  /** Overall match rate as decimal (0-1) */
  match_rate: number
  /** Per-platform coverage breakdown */
  by_platform: PlatformCoverage[]
}

/**
 * Event in palimpsest view with availability status.
 *
 * @description Simplified event representation showing which platforms have the event.
 */
export interface PalimpsestEvent {
  /** Internal event ID */
  id: number
  /** Sportradar unique identifier */
  sportradar_id: string
  /** Event name */
  name: string
  /** Home team name */
  home_team: string
  /** Away team name */
  away_team: string
  /** ISO timestamp of kickoff */
  kickoff: string
  /** Tournament name */
  tournament_name: string
  /** Tournament country, or null if international */
  tournament_country: string | null
  /** Sport name */
  sport_name: string
  /** Availability classification */
  availability: 'betpawa-only' | 'competitor-only' | 'matched'
  /** List of platform slugs that have this event */
  platforms: string[]
}

/**
 * Tournament with its events grouped together.
 *
 * @description Groups events by tournament for organized display in coverage views.
 */
export interface TournamentGroup {
  /** Tournament ID */
  tournament_id: number
  /** Tournament name */
  tournament_name: string
  /** Tournament country, or null if international */
  tournament_country: string | null
  /** Sport name */
  sport_name: string
  /** Coverage stats for this tournament */
  coverage: TournamentCoverage
  /** Events in this tournament */
  events: PalimpsestEvent[]
}

/**
 * Full palimpsest events response.
 *
 * @description Contains overall coverage stats and events organized by tournament.
 */
export interface PalimpsestEventsResponse {
  /** Overall coverage statistics */
  coverage: CoverageStats
  /** Events grouped by tournament */
  tournaments: TournamentGroup[]
}

// ─────────────────────────────────────────────────────────────────────────────
// Cleanup Types
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Statistics for a database table.
 *
 * @description Provides count and date range for records in a table.
 */
export interface TableStats {
  /** Total number of records */
  count: number
  /** ISO timestamp of oldest record, or null if table is empty */
  oldest: string | null
  /** ISO timestamp of newest record, or null if table is empty */
  newest: string | null
}

/**
 * Event count for a specific platform.
 */
export interface PlatformCount {
  /** Platform identifier */
  platform: string
  /** Number of events */
  count: number
}

/**
 * Current data statistics across all tables.
 *
 * @description Provides overview of data volume and age for cleanup planning.
 */
export interface DataStats {
  /** Stats for betpawa odds snapshots */
  oddsSnapshots: TableStats
  /** Stats for competitor odds snapshots */
  competitorOddsSnapshots: TableStats
  /** Stats for betpawa events */
  events: TableStats
  /** Stats for competitor events */
  competitorEvents: TableStats
  /** Stats for betpawa tournaments */
  tournaments: TableStats
  /** Stats for competitor tournaments */
  competitorTournaments: TableStats
  /** Stats for scrape runs */
  scrapeRuns: TableStats
  /** Stats for scrape batches */
  scrapeBatches: TableStats
  /** Betpawa event counts by platform */
  eventsByPlatform: PlatformCount[]
  /** Competitor event counts by source */
  competitorEventsBySource: PlatformCount[]
}

/**
 * Preview of what a cleanup operation would delete.
 *
 * @description Shows record counts that would be affected by cleanup
 * without actually deleting anything.
 */
export interface CleanupPreview {
  /** ISO date for odds retention cutoff */
  oddsCutoffDate: string
  /** ISO date for match retention cutoff */
  matchCutoffDate: string
  /** Betpawa odds snapshots that would be deleted */
  oddsSnapshotsCount: number
  /** Competitor odds snapshots that would be deleted */
  competitorOddsSnapshotsCount: number
  /** Scrape runs that would be deleted */
  scrapeRunsCount: number
  /** Scrape batches that would be deleted */
  scrapeBatchesCount: number
  /** Betpawa events that would be deleted */
  eventsCount: number
  /** Competitor events that would be deleted */
  competitorEventsCount: number
  /** Betpawa tournaments that would be deleted */
  tournamentsCount: number
  /** Competitor tournaments that would be deleted */
  competitorTournamentsCount: number
}

/**
 * Result of an executed cleanup operation.
 *
 * @description Reports actual deletion counts and remaining data age.
 */
export interface CleanupResult {
  /** Betpawa odds snapshots deleted */
  oddsDeleted: number
  /** Competitor odds snapshots deleted */
  competitorOddsDeleted: number
  /** Scrape runs deleted */
  scrapeRunsDeleted: number
  /** Scrape batches deleted */
  scrapeBatchesDeleted: number
  /** Betpawa events deleted */
  eventsDeleted: number
  /** Competitor events deleted */
  competitorEventsDeleted: number
  /** Betpawa tournaments deleted */
  tournamentsDeleted: number
  /** Competitor tournaments deleted */
  competitorTournamentsDeleted: number
  /** ISO timestamp of oldest remaining odds, or null if all deleted */
  oldestOddsDate: string | null
  /** ISO timestamp of oldest remaining match, or null if all deleted */
  oldestMatchDate: string | null
  /** Time taken for cleanup in seconds */
  durationSeconds: number
}

/**
 * Historical cleanup run record.
 *
 * @description Full details of a past cleanup operation.
 */
export interface CleanupRun {
  /** Unique run ID */
  id: number
  /** ISO timestamp when cleanup started */
  startedAt: string
  /** ISO timestamp when cleanup completed, or null if still running */
  completedAt: string | null
  /** What triggered the cleanup (e.g., "scheduled", "manual") */
  trigger: string
  /** Odds retention setting used */
  oddsRetentionDays: number
  /** Match retention setting used */
  matchRetentionDays: number
  /** Betpawa odds snapshots deleted */
  oddsDeleted: number
  /** Competitor odds snapshots deleted */
  competitorOddsDeleted: number
  /** Scrape runs deleted */
  scrapeRunsDeleted: number
  /** Scrape batches deleted */
  scrapeBatchesDeleted: number
  /** Betpawa events deleted */
  eventsDeleted: number
  /** Competitor events deleted */
  competitorEventsDeleted: number
  /** Betpawa tournaments deleted */
  tournamentsDeleted: number
  /** Competitor tournaments deleted */
  competitorTournamentsDeleted: number
  /** ISO timestamp of oldest remaining odds after cleanup */
  oldestOddsDate: string | null
  /** ISO timestamp of oldest remaining match after cleanup */
  oldestMatchDate: string | null
  /** Run status (e.g., "completed", "failed") */
  status: string
  /** Error message if failed, or null */
  errorMessage: string | null
  /** Duration in seconds, or null if still running */
  durationSeconds: number | null
}

/**
 * Paginated cleanup history response.
 */
export interface CleanupHistoryResponse {
  /** List of cleanup runs */
  runs: CleanupRun[]
  /** Total number of cleanup runs */
  total: number
}

// ─────────────────────────────────────────────────────────────────────────────
// Historical Data Types
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Single point in odds history timeline.
 *
 * @description Represents odds values at a specific point in time for charting.
 */
export interface OddsHistoryPoint {
  /** ISO timestamp when odds were captured */
  captured_at: string
  /** Outcome odds at this point in time */
  outcomes: OutcomeOdds[]
  /** Calculated margin at this point, or null if not calculable */
  margin: number | null
}

/**
 * Complete odds history for a market.
 *
 * @description Timeline of odds changes for visualization in charts.
 */
export interface OddsHistoryResponse {
  /** Event ID */
  event_id: number
  /** Bookmaker identifier */
  bookmaker_slug: string
  /** Bookmaker display name */
  bookmaker_name: string
  /** Market identifier */
  market_id: string
  /** Market display name */
  market_name: string
  /** Line value for handicap/total markets, or null */
  line: number | null
  /** Chronological list of odds snapshots */
  history: OddsHistoryPoint[]
}

/**
 * Single point in margin history timeline.
 *
 * @description Represents margin value at a specific point in time for charting.
 */
export interface MarginHistoryPoint {
  /** ISO timestamp when margin was calculated */
  captured_at: string
  /** Margin percentage at this point, or null if not calculable */
  margin: number | null
}

/**
 * Complete margin history for a market.
 *
 * @description Timeline of margin changes for visualization in charts.
 */
export interface MarginHistoryResponse {
  /** Event ID */
  event_id: number
  /** Bookmaker identifier */
  bookmaker_slug: string
  /** Bookmaker display name */
  bookmaker_name: string
  /** Market identifier */
  market_id: string
  /** Market display name */
  market_name: string
  /** Line value for handicap/total markets, or null */
  line: number | null
  /** Chronological list of margin snapshots */
  history: MarginHistoryPoint[]
}
