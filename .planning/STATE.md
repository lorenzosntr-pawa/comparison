# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-12)

**Core value:** Accurate cross-platform market matching and real-time odds comparison that enables Betpawa to understand its competitive position in the Nigerian market.
**Current focus:** Project feature-complete through v2.6

## Current Position

Phase: 99 of 99 (Availability Tracking Fix)
Plan: Not started
Status: Ready to plan
Last activity: 2026-02-12 — Milestone v2.7 created

Progress: ░░░░░░░░░░ 0%

## Milestones

- **v1.0 MVP** — SHIPPED 2026-01-23 (15 phases, 46 plans)
- **v1.1 Palimpsest Comparison** — SHIPPED 2026-01-24 (7 phases, 11 plans)
- **v1.2 Settings & Retention** — SHIPPED 2026-01-26 (4 phases, 8 plans)
- **v1.3 Coverage Improvements** — SHIPPED 2026-01-26 (5 phases, 5 plans)
- **v1.4 Odds Comparison UX** — SHIPPED 2026-01-26 (3 phases, 3 plans)
- **v1.5 Scraping Observability** — SHIPPED 2026-01-28 (4 phases, 4 plans)
- **v1.6 Event Matching Accuracy** — SHIPPED 2026-01-29 (3 phases, 3 plans)
- **v1.7 Scraping Architecture Overhaul** — SHIPPED 2026-02-02 (7 phases, 16 plans)
- **v1.8 Market Matching Accuracy** — SHIPPED 2026-02-03 (5 phases, 9 plans)
- **v1.9 Event Details UX** — SHIPPED 2026-02-05 (5 phases, 10 plans)
- **v2.0 Real-Time Scraping Pipeline** — SHIPPED 2026-02-06 (7 phases, 17 plans)
- **v2.1 Historical Odds Tracking** — SHIPPED 2026-02-08 (9 phases, 12 plans)
- **v2.2 Odds Freshness** — SHIPPED 2026-02-09 (3 phases, 3 plans)
- **v2.3 Code Quality & Reliability** — SHIPPED 2026-02-09 (7 phases, Phase 72-78)
- **v2.4 Historical Analytics** — SHIPPED 2026-02-11 (11 phases, Phase 79-86, 19 plans)
- **v2.5 Odds Availability Tracking** — SHIPPED 2026-02-11 (6 phases, Phase 87-92)
- **v2.6 UX Polish & Navigation** — SHIPPED 2026-02-12 (6 phases, Phase 93-98)
- **v2.7 Availability Tracking Bugfix** — IN PROGRESS (1 phase, Phase 99)

## Performance Metrics

**Velocity:**
- Total plans completed: 158 (91 original + 14 FIX + 9 v1.8 + 10 v1.9 + 17 v2.0 + 17 additional)
- Average duration: 6 min
- Total execution time: ~12 hours

**v1.0 Summary:**
- 15 phases completed (including decimal phases)
- 4 days from start to ship
- 18,595 lines of code

**v1.1 Summary:**
- 7 phases completed
- 2 days from v1.0 to v1.1
- ~8,500 lines added

**v1.2 Summary:**
- 4 phases completed (including decimal)
- 2 days from v1.1 to v1.2
- ~3,800 lines added

**v1.3 Summary:**
- 5 phases completed
- Same day as v1.2 ship
- ~385 lines added

**v1.4 Summary:**
- 3 phases completed
- Same day as v1.3 ship
- +986 / -159 lines (net +827)

**v1.5 Summary:**
- 4 phases completed (including 1 decimal)
- 2 days from v1.4 to v1.5
- +2,243 / -88 lines (net +2,155)

**v1.6 Summary:**
- 3 phases completed (including 1 decimal)
- 2 days from v1.5 to v1.6
- +2,194 / -12 lines (net +2,182)

**v1.7 Summary:**
- 7 phases completed (16 plans including 9 FIX plans)
- 4 days from v1.6 to v1.7 (2026-01-29 to 2026-02-02)
- Event-centric parallel scraping architecture
- +8,941 / -2,059 lines (net +6,882)
- ~28,458 total LOC

**v1.8 Summary:**
- 5 phases completed (9 plans including 2 FIX plans)
- 2 days from v1.7 to v1.8 (2026-02-02 to 2026-02-03)
- Comprehensive market mapping audit and targeted fixes
- 20 new market mappings, combo market parameter handling
- Handicap line fix, outcome name normalization
- SportyBet 47.3%->52.2%, Bet9ja 36.1%->40.5% mapping success
- +13,290 / -57 lines (net +13,233)
- ~30,647 total LOC

**v1.9 Summary:**
- 5 phases completed (10 plans including 5 FIX plans)
- 2 days from v1.8 to v1.9 (2026-02-03 to 2026-02-04)
- Event detail summary cards, tabbed market navigation, fuzzy search, sticky header
- +3,599 / -205 lines (net +3,394)
- ~31,116 total LOC

**v2.0 Summary:**
- 8 phases completed (17 plans including 1 FIX plan + 1 inserted phase)
- 2 days from v1.9 to v2.0 (2026-02-05 to 2026-02-06)
- In-memory cache (97.3% API latency reduction), async write pipeline, concurrent scraping (65% pipeline reduction)
- WebSocket real-time updates replacing SSE entirely
- +4,097 / -1,117 lines (net +2,980)
- ~34,096 total LOC

**v2.1 Summary:**
- 9 phases completed (12 plans including 2 FIX plans, 1 phase skipped)
- 3 days from v2.0 to v2.1 (2026-02-06 to 2026-02-08)
- Historical Data API with 3 endpoints for snapshot, odds, and margin history
- recharts integration with HistoryDialog, multi-bookmaker comparison mode
- Small-multiples MarketHistoryPanel for full market view
- +4,505 / -51 lines (net +4,454)
- ~38,550 total LOC

**v2.2 Summary:**
- 3 phases completed (3 plans)
- 1 day from v2.1 to v2.2 (2026-02-08 to 2026-02-09)
- Data flow audit identified 7 staleness sources (2 CRITICAL, 2 HIGH)
- Added `last_confirmed_at` to cache and API for accurate freshness
- Created `useOddsUpdates` hook for real-time query invalidation
- +1,517 / -26 lines (net +1,491)
- ~40,000 total LOC

**v2.3 Summary:**
- 7 phases completed (11 plans)
- 1 day (2026-02-09)
- Fixed WebSocket "always in progress" bug with compound isObserving state
- Added reconnection callbacks with query invalidation and connection status indicator
- Removed 1,256 LOC dead backend code (unused imports, dependencies, audit scripts)
- Added PEP 257 docstrings to 19 backend files, JSDoc to 29 frontend files
- Created comprehensive README.md documenting architecture and setup
- Added return type annotations to 10 functions, JSONDecodeError handling to 9 API calls
- +9,035 / -1,808 lines (net +7,227)
- ~40,000 total LOC (net after dead code removal)

**v2.4 Summary:**
- 11 phases completed (19 plans including 4 FIX plans, 3 decimal phases)
- 2 days (2026-02-10 to 2026-02-11)
- Fixed specifier bug in history API (line parameter)
- Historical Analysis page with tournament list and date range filters
- Tournament detail page with ALL market cards
- Time-to-kickoff bucket analysis with breakdown dialog
- Multi-bookmaker comparison with overlay and difference charts
- +11,858 / -177 lines (net +11,681)
- ~40,000 total LOC

**v2.5 Summary:**
- 6 phases completed (6 plans)
- Same day (2026-02-11, ~2 hours)
- Availability tracking with unavailable_at timestamp
- Cache-level detection comparing previous to current scrape
- Three-state display in Odds Comparison and Event Details
- History charts with dashed lines for unavailable periods
- +3,184 / -136 lines (net +3,048)
- ~40,949 total LOC

**v2.6 Summary:**
- 6 phases completed (including 1 decimal, 15+ plans with FIX plans)
- Same day (2026-02-12, ~4.5 hours)
- Tournament & country filters on Odds Comparison page
- Resizable columns with localStorage persistence
- Tournament data integrity fix (BUG-016)
- Coverage page improvements and stable stats
- Historical Analysis bookmaker pills, search, country filter
- Navigation overhaul: Odds Comparison as landing, sidebar status widgets
- Dashboard removed, sidebar reorganized into three sections
- Real-time sidebar updates via WebSocket query invalidation
- +4,695 / -908 lines (net +3,787)
- ~41,395 total LOC

## Accumulated Context

### Key Patterns (v1.0 through v2.0)

- Pydantic v2 with frozen models and ConfigDict
- SQLAlchemy 2.0 async with Mapped[] columns
- TanStack Query v5 with polling intervals
- SSE streaming for real-time progress
- structlog for structured logging
- shadcn/ui with Tailwind v4
- **Fetch-then-store pattern** for async scraping (Phase 1: API parallel, Phase 2: DB sequential)
- **AsyncSession cannot be shared** across concurrent asyncio tasks - use explicit commits between phases
- **Preview-before-delete pattern** for destructive operations (v1.2)
- **Startup sync pattern** - load DB settings and apply after services start (v1.2)
- **Command + Popover pattern** for searchable multi-select comboboxes (v1.3)
- **Cross-feature hook sharing** - reuse hooks across features for consistent data (v1.3)
- **Bookmakers-as-rows layout** - rowspan for match info, stacked rows per bookmaker (v1.4)
- **Comparative margin color coding** - green/red based on Betpawa vs competitors, not absolute values (v1.4)
- **APScheduler watchdog pattern** - background job auto-fails stale runs (v1.5)
- **CONNECTION_FAILED as distinct status** - enables specific UI treatment and auto-rescrape (v1.5)
- **Per-platform SSE events** - real counts and timing per bookmaker in progress stream (v1.5)
- **SQL-based audit methodology** - comprehensive SQL diagnostics to verify data quality (v1.6)
- **DISTINCT SR ID for counts** - use unique sportradar_id, not duplicate rows across runs (v1.6)
- **Factory method for configurable initialization** - EventCoordinator.from_settings() (v1.7)
- **Event-centric parallel scraping** - scrape all platforms simultaneously per event (v1.7)
- **Single-flush batch insert pattern** - add all records, single flush to get IDs, link FKs, commit (v1.7)
- **Market group extraction from tabs** - BetPawa tabs array contains categories; extract non-"all" tabs (v1.9)
- **Multi-group array storage** - JSON array so markets appear in multiple category tabs (v1.9)
- **Fuzzy subsequence matching** - query chars in order for intuitive partial matching (v1.9)
- **Dynamic column reordering** - selected competitor adjacent to Betpawa (v1.9)
- **Scroll container-aware fixed positioning** - fixed positioning with dynamic bounds for overflow containers (v1.9)
- **data-scroll-container attribute** - reliable scroll element targeting in nested layouts (v1.9)
- **Shared market utilities** - deduplicated code in lib/market-utils.ts (v1.9)
- **perf_counter timing on progress events** - additive timing fields on existing dict events, backward-compatible (v2.0)
- **Benchmark script pattern** - real scrape cycle + API latency + memory profiling for repeatable measurements (v2.0)
- **Frozen dataclass cache entries** - immutable, hashable, no ORM session dependency for in-memory caching (v2.0)
- **Cache warmup in app lifespan** - async DB load with perf_counter timing at startup (v2.0)
- **Cache population from ORM models** - extract data from flushed models post-commit, convert via snapshot_to_cached_from_models (v2.0)
- **Piggyback eviction on scrape schedule** - no separate background task, evict expired events after each scrape cycle (v2.0)
- **Cache-first API pattern** - check OddsCache first, fall back to DB for misses, log hit/miss stats (v2.0)
- **Change detection via normalized outcome tuples** - sort outcomes by name, compare as tuples for order-independent equality (v2.0)
- **Classify batch changes pattern** - separate changed (INSERT) vs unchanged (UPDATE last_confirmed_at) snapshots using cache comparison (v2.0)
- **Frozen dataclass DTOs for write queue** - plain data objects decouple scraping from DB persistence, no ORM dependency across async boundaries (v2.0)
- **Isolated session per write batch** - handler opens own session from session_factory, never shares with scraping (v2.0)
- **Dual-path store_batch_results** - async write queue path for scheduled scraping, sync fallback for on-demand (v2.0)
- **Cache-before-persist** - update cache immediately for all data, persist changed data asynchronously via write queue (v2.0)
- **snapshot_to_cached_from_data()** - DTO-to-cache conversion parallel to ORM-based helper, uses snapshot_id=0 for unsaved (v2.0)
- **Event-level semaphore for intra-batch concurrency** - asyncio.Semaphore(max_concurrent_events) limits parallel events within each batch (v2.0)
- **scrape_batch() returns list instead of AsyncGenerator** - collect concurrent results then yield progress, cleaner than parallel async generators (v2.0)
- **gather(return_exceptions=True) over TaskGroup** - partial failure tolerance, no cascading cancellation (v2.0)
- **ConnectionManager with dual-dict topic tracking** - ws->topics and topic->ws reverse index for O(1) lookups (v2.0)
- **Snapshot iteration for WebSocket broadcast** - copy subscriber set before iteration, clean dead connections after (v2.0)
- **WebSocket try/except/finally lifecycle** - always disconnect in finally block, catch WebSocketDisconnect separately (v2.0)
- **WebSocket message envelope pattern** - all messages have {type, timestamp, data} shape for consistent parsing (v2.0)
- **ProgressBroadcaster-to-WebSocket bridge** - async bridge task subscribes to broadcaster, forwards to ws_manager.broadcast (v2.0)
- **OddsCache on_update callback pattern** - sync callbacks fire on cache mutations, use loop.create_task() for async broadcast scheduling (v2.0)
- **WebSocket-first with SSE fallback** - useWebSocketScrapeProgress as primary, fall back to SSE after 3 failures (v2.0 Phase 58)
- **WebSocket-only frontend** - SSE code removed, all progress via WebSocket, POST API for manual scrape trigger (v2.0 Phase 59)
- **Historical snapshots already kept** - Current schema stores ~52 snapshots per event on average, not overwriting (v2.1 Phase 60)
- **Change-based retention** - Option C strategy: existing change detection naturally creates history without schema overhaul (v2.1 Phase 60)
- **Historical data schemas** - Separate full-data (OddsHistoryResponse) from chart-only (MarginHistoryResponse) for API flexibility (v2.1 Phase 62)
- **Composite index for history queries** - idx_market_odds_snapshot_market on (snapshot_id, betpawa_market_id) optimizes JOIN pattern (v2.1 Phase 62)
- **recharts Tooltip formatter type guard** - (value) => typeof value === 'number' ? ... : '-' handles undefined values (v2.1 Phase 64)
- **History hooks with full filter queryKey** - include all params (eventId, marketId, bookmakerSlug, fromTime, toTime) for proper cache invalidation (v2.1 Phase 64)
- **Tab-conditional data fetching** - enabled=open && activeTab prevents API calls for inactive tabs in tabbed dialogs (v2.1 Phase 65)
- **Cell click with stopPropagation** - onClick on nested elements uses e.stopPropagation() to prevent row navigation while enabling cell-specific actions (v2.1 Phase 66)
- **Reusable onClick on value components** - OddsBadge and MarginIndicator accept optional onClick prop for clickable behavior across any page (v2.1 Phase 67)
- **Small-multiples for multi-outcome visualization** - Grid of mini-charts (one per outcome) with synchronized time axes, cleaner than one chart with many lines (v2.1 Phase 68)
- **`captured_at` vs `last_confirmed_at` distinction** - `captured_at` = when odds changed, `last_confirmed_at` = when last verified; use latter for freshness display (v2.2 Phase 69)
- **`_get_snapshot_time()` helper pattern** - consistent timestamp extraction with fallback to `captured_at` for backward compatibility (v2.2 Phase 70)
- **Global WebSocket subscription via App hook** - useOddsUpdates in App root for automatic query invalidation on odds_update messages (v2.2 Phase 71)
- **Inner component for QueryClient context** - hooks requiring useQueryClient must be inside QueryClientProvider children (v2.2 Phase 71)
- **Compound boolean for observing state** - `isObserving` requires both `activeScrapeId !== null` AND `ws.isConnected`; connection alone insufficient (v2.3 Phase 72)
- **wasConnectedRef pattern for reconnection detection** - track first connection via ref, fire onReconnect only on disconnected→connected transition (v2.3 Phase 73)
- **Stable connection timeout before retry reset** - delay 30s before resetting retry counter to prevent premature reset on flaky networks (v2.3 Phase 73)
- **Ref-based state for stable callbacks** - use useRef to track state in useCallback handlers to avoid stale closures and allow empty dependency arrays (v2.4 Phase 81)
- **Click handler debounce** - ignore clicks within 100ms of last click to prevent rapid double-fire issues (v2.4 Phase 81)
- **oddsDataByOutcome prop for multi-outcome comparison** - pass outcome -> { bookmaker -> odds } for tables with multiple rows (v2.4 Phase 82)
- **ComparisonTable best/worst highlighting** - green for best odds per row, red for >3% worse than Betpawa, Betpawa column never colored (v2.4 Phase 82)
- **TournamentAccumulator pattern** - aggregate multiple metrics (margins, coverage counts, event list) during single iteration over events, then compute averages/trends from accumulated data (v2.4 Phase 84)
- **First-half vs second-half trend calculation** - compare average margin of first half of events to second half; 0.5% threshold, minimum 4 events for meaningful comparison (v2.4 Phase 84)
- **Coverage bar with proportional bookmaker segments** - horizontal bar with colored segments (blue/green/orange) proportional to coverage %, tooltip shows exact percentages (v2.4 Phase 84)
- **Pagination loop for API with limits** - fetch all pages until response.events.length < pageSize; respects API maximum page_size of 100 (v2.4 Phase 84-FIX)
- **Per-market accumulator with Record<marketId, data> structure** - keyed by market ID (3743/5000/3795/4693) for 1X2/OU/BTTS/DC; each entry has betpawaMargins[], competitorMargins[], eventMargins[] (v2.4 Phase 84.1)
- **TRACKED_MARKETS constant for shared market configuration** - exported from hooks for reuse in components; array of { id, label } for consistent iteration (v2.4 Phase 84.1)
- **Simplify over explain pattern** - when UX confuses users, remove complexity rather than add tooltips/labels; less is more (v2.4 Phase 84.1-FIX)
- **getMarketKey(id, line) pattern** - unique market identification using id:line combination to distinguish Over 2.5 from Over 1.5 etc.; markets without specifiers use id only (v2.4 Phase 84.2)
- **useTournamentMarkets hook** - extracts ALL unique markets from tournament events (not just tracked 4); computes avg/min/max margin and marginHistory for timeline charts (v2.4 Phase 84.2)
- **Dialog-based timeline pattern** - on-demand timeline visualization in dialog instead of inline chart; keeps main page cleaner while providing detailed stats, bucket breakdown, and chart (v2.4 Phase 85)
- **TRACKED_MARKET_IDS Set for card display** - only show opening/closing margin for main 4 markets (1X2, O/U 2.5, BTTS, DC) to reduce visual noise on cards (v2.4 Phase 85)
- **BOOKMAKER_COLORS constant for brand styling** - exported from bookmaker-filter.tsx for consistent blue/green/orange bookmaker indicators (v2.4 Phase 86)
- **CompetitiveBadge for margin comparison** - green/red badge showing +/- difference vs best competitor, shown only for primary market (1X2) (v2.4 Phase 86)
- **Dialog-specific filter state pattern** - dialog maintains own state for bookmaker filter, resets on open; independent from page-level filter (v2.4 Phase 86)
- **MergedDataPoint for multi-bookmaker charts** - merge hoursToKickoff data with 1 decimal precision, each bookmaker as optional key (v2.4 Phase 86)
- **DifferenceBarChart for margin gap visualization** - bar chart showing Betpawa minus competitor per time bucket, green=Betpawa better, red=competitor better (v2.4 Phase 86)
- **calculateBucketStats helper** - convert timeline points to bucket statistics on-demand in dialog component (v2.4 Phase 86)
- **Availability extraction pattern** - `unavailable_at = getattr(market, 'unavailable_at', None); available = unavailable_at is None` for safe access across cache/DB paths (v2.5 Phase 89)
- **Three-state availability rendering** - available (normal odds), unavailable (strikethrough dash + tooltip), never_offered (plain dash); getMarketAvailabilityState centralizes logic (v2.5 Phase 90)
- **OutcomeOddsResult pattern** - getOutcomeOdds returns { odds, available, unavailableSince } object for single function call per cell efficiency (v2.5 Phase 90)
- **OutcomeDisplay availability extension** - extend existing display interface with available/unavailableSince fields for prop drilling to OddsBadge (v2.5 Phase 91)
- **splitByAvailability helper for chart rendering** - separate data points into available/unavailable arrays for dual-line approach (v2.5 Phase 92)
- **Dashed overlay line for unavailable periods** - strokeDasharray="5 5" on secondary line, solid primary line; connectNulls bridges gaps (v2.5 Phase 92)
- **Tooltip unavailable suffix pattern** - append "(unavailable)" to tooltip values when available=false for clear UX (v2.5 Phase 92)
- **Resize handle pattern** - absolute positioned div at column edge with cursor-col-resize, mouse tracking via document events (v2.6 Phase 93)
- **Separate localStorage keys for related settings** - use distinct keys (column-widths vs column-visibility) to avoid conflicts (v2.6 Phase 93)
- **Sidebar compact status widgets** - event count badge and health indicator dots (green/yellow/red) for at-a-glance system monitoring (v2.6 Phase 96)
- **Sidebar query invalidation on scrape completion** - invalidate ['coverage'] and ['scrape-runs'] queries when scrape completes for instant sidebar refresh (v2.6 Phase 98)

### Key Decisions

- Metadata priority: sportybet > bet9ja (v1.1)
- SportRadar ID as primary cross-platform matching key
- Store competitor data independently, match at query time
- Negative IDs distinguish competitor-only events from BetPawa events
- Default 7-day retention, 1-90 day range (v1.2)
- Daily cleanup at 2 AM UTC (v1.2)
- Empty selection = all countries (v1.3)
- Default includeStarted OFF for pre-match focus (v1.3)
- Event matching is 99.9% accurate (v1.6 audit)
- Event-centric parallel scraping architecture (v1.7)
- Audit-driven market mapping approach (v1.8)
- Market groups as JSON arrays for multi-category membership (v1.9)
- Categories from data not heuristics (v1.9)
- Scraping is dominant bottleneck at 61.3% of pipeline — Phase 56 highest priority (v2.0 baseline)
- Storage secondary at 37.4% — Processing and Commit sub-phases dominate (v2.0 baseline)
- Event list API p50=903ms justifies cache layer (v2.0 baseline)
- Frozen dataclasses for cache entries — avoids detached ORM instance issues (v2.0 Phase 54)
- Duck-type compatible CachedSnapshot — no adapter layer for existing _build_inline_odds() (v2.0 Phase 54)
- snapshot_to_cached_from_models() for in-memory ORM objects — avoids re-querying DB after commit (v2.0 Phase 54)
- Eviction 2-hour grace period — keeps recently started matches visible for users (v2.0 Phase 54)
- Piggyback eviction on scrape schedule — no separate task, runs once per cycle (v2.0 Phase 54)
- Cache-first with DB fallback via _load_snapshots_cached() — getattr for safe cache access (v2.0 Phase 54)
- GET /api/events p50 reduced from 903ms to 24ms (97.3% improvement) with cache layer (v2.0 Phase 54)
- Nullable last_confirmed_at column — no backfill needed, only new pipeline writes set it (v2.0 Phase 55)
- Normalized outcome comparison — sort by name for order-independent market equality (v2.0 Phase 55)
- Bounded asyncio.Queue (maxsize=50) for write backpressure — blocks scraping if writes fall behind (v2.0 Phase 55)
- 3 retry attempts with exponential backoff (1s, 2s, 4s) — drop batch on final failure to avoid infinite loops (v2.0 Phase 55)
- IntegrityError skips batch, OperationalError retries — different error classes get appropriate handling (v2.0 Phase 55)
- Dual-path persistence: async when write_queue present, sync when None — backward compat for on-demand scrape (v2.0 Phase 55)
- Cache updated for ALL data before enqueue — API always serves freshest odds regardless of write queue latency (v2.0 Phase 55)
- Write queue lifecycle: created after cache warmup, stopped before scheduler shutdown (v2.0 Phase 55)
- Default max_concurrent_events=10 — 10 events × 3 platforms = 30 concurrent HTTP requests, within pool limit (v2.0 Phase 56)
- HTTP pool increased to 200/100 — headroom for concurrent events with retries (v2.0 Phase 56)
- Batch scrape time reduced 67.1% (35s→11.5s), total pipeline 65.2% faster (24.4min→8.5min) (v2.0 Phase 56)
- Concurrency parameters exposed via settings API — all 6 fields writable via PATCH /api/settings (v2.0 Phase 56)
- ConnectionManager on app.state.ws_manager — topic-based pub/sub for real-time WebSocket broadcasting (v2.0 Phase 57)
- WebSocket endpoint at /api/ws — runs alongside SSE, no breaking changes (v2.0 Phase 57)
- Dict builders over Pydantic models for WebSocket messages — faster serialization on hot path (v2.0 Phase 57)
- Bridge task gated on ws_manager.active_count — avoid creating task when no clients connected (v2.0 Phase 57)
- WS_FAIL_THRESHOLD = 3 — WebSocket failures before SSE fallback (v2.0 Phase 58)
- Transport indicator in hooks — expose 'websocket' | 'sse' for debugging (v2.0 Phase 58)
- SSE endpoints removed, WebSocket-only frontend — no fallback complexity (v2.0 Phase 59)
- Manual scrapes via POST /api/scrape + WebSocket observation (v2.0 Phase 59)
- No major schema changes required — current architecture with odds_snapshots + market_odds already stores history (v2.1 Phase 60)
- Storage budget: 500 events × 90 days = ~139 GB (acceptable with partitioning) (v2.1 Phase 60)
- Phase 61 SKIPPED — existing `odds_retention_days` setting already provides configurable retention (v2.1)
- Availability tracking via unavailable_at timestamp (not boolean, not separate table) — cache-level detection comparing previous state to new scrape (v2.5 Phase 87)

### Blockers/Concerns

- Memory usage for cache must stay reasonable (<100MB for active events)
- Keep current fixed scrape interval schedule (no change to refresh timing)

### Roadmap Evolution

- v1.0 MVP shipped 2026-01-23 with 15 phases
- v1.1 Palimpsest Comparison shipped 2026-01-24 with 7 phases
- v1.2 Settings & Retention shipped 2026-01-26 with 4 phases
- v1.3 Coverage Improvements shipped 2026-01-26 with 5 phases
- v1.4 Odds Comparison UX shipped 2026-01-26 with 3 phases
- v1.5 Scraping Observability shipped 2026-01-28 with 4 phases
- v1.6 Event Matching Accuracy shipped 2026-01-29 with 3 phases
- v1.7 Scraping Architecture Overhaul shipped 2026-02-02 with 7 phases
- v1.8 Market Matching Accuracy shipped 2026-02-03 with 5 phases
- v1.9 Event Details UX shipped 2026-02-05 with 5 phases
- All milestones archived to .planning/milestones/
- Milestone v2.0 created: Real-Time Scraping Pipeline, 7 phases (Phase 53-59)
- Phase 55.1 inserted after Phase 55: Fix Phase 55 Bugs — BUG-005 write_ms duplicate keyword (blocker), BUG-006 stale detection timezone, BUG-007 on-demand cache bypass (URGENT)
- v2.0 Real-Time Scraping Pipeline shipped 2026-02-06 with 7 phases (17 plans)
- Milestone v2.1 created: Historical Odds Tracking, 9 phases (Phase 60-68)
- Phase 61 skipped: existing odds_retention_days setting already provides configurable retention
- v2.1 Historical Odds Tracking shipped 2026-02-08 with 9 phases (12 plans)
- v2.2 Odds Freshness shipped 2026-02-09 with 3 phases (3 plans)
- Milestone v2.3 created: Code Quality & Reliability, 7 phases (Phase 72-78)
- v2.3 Code Quality & Reliability shipped 2026-02-09 with 7 phases (11 plans)
- v2.3 archived to .planning/milestones/v2.3-ROADMAP.md
- Milestone v2.4 created: Historical Analytics, 10 phases (Phase 79-88)
- Phase 84.1 inserted after Phase 84: Fix Tournament Metrics Design (URGENT) - BUG-013/014/015
- Phase 84.2 inserted after Phase 84.1: Tournament Detail Page - ISS-005 (user requested feature)
- Phase 85.1 inserted after Phase 85: Historical Analysis Card Margins - add opening/closing margins per market to cards, fix margin inconsistencies (URGENT)
- Phase 87 removed: Polish phase skipped, features complete as-is
- v2.4 Historical Analytics shipped 2026-02-11 with 11 phases (19 plans)
- v2.4 archived to .planning/milestones/v2.4-ROADMAP.md
- Milestone v2.5 created: Odds Availability Tracking, 6 phases (Phase 87-92)
- v2.5 Odds Availability Tracking shipped 2026-02-11 with 6 phases (6 plans)
- v2.5 archived to .planning/milestones/v2.5-ROADMAP.md
- Milestone v2.6 created: UX Polish & Navigation, 4 phases (Phase 93-96)
- v2.6 UX Polish & Navigation shipped 2026-02-12 with 4 phases (10+ plans)
- Phase 97 added: Last Fixes - remove Dashboard, fix navigation links, reorganize sidebar
- Phase 97 planned: 1 plan with 3 tasks defined
- Phase 98 added: Real-Time Sidebar Widget - WebSocket updates for sidebar status widgets
- Phase 98 executed: 1 plan completed
- v2.6 UX Polish & Navigation shipped 2026-02-12 with 6 phases (15+ plans)
- v2.6 archived to .planning/milestones/v2.6-ROADMAP.md
- Milestone v2.7 created: Availability Tracking Bugfix, 1 phase (Phase 99)

## Session Continuity

Last session: 2026-02-12
Stopped at: Milestone v2.7 initialization
Resume file: None
Next action: /gsd:plan-phase 99
