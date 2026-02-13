# Project Milestones: Betpawa Odds Comparison Tool

## v2.7 Availability Tracking Bugfix (Shipped: 2026-02-12)

**Delivered:** Complete availability tracking pipeline: fixed DB persistence, added reconciliation for dropped events, consistent unavailable styling, and alerts filter for monitoring.

**Phases completed:** 99-99.1 (5 plans total: 2 main + 3 FIX plans)

**Key accomplishments:**

- Fixed availability detection pipeline — markets that disappear from scrapes now persist `unavailable_at` timestamp to DB
- Added reconciliation for events dropped from discovery — events no longer offered by platforms get marked unavailable
- Consistent unavailable styling on Odds Comparison page — strikethrough odds/margins with tooltips
- Added "Alerts" toggle filtering events with unavailable markets (with count badge)
- Fixed alerts filter to query only latest snapshot per event (not historical data)

**Stats:**

- 30 files changed
- +2,664 / -56 lines (net +2,608)
- 2 phases, 5 plans
- Same day (2026-02-12, ~2.3 hours)
- ~41,395 total LOC

**Git range:** `77a7dc0` → `85d4071`

**What's next:** Project feature-complete. Use `/gsd:discuss-milestone` if additional features needed.

---

## v2.6 UX Polish & Navigation (Shipped: 2026-02-12)

**Delivered:** App-wide UX improvements including tournament/country filters, resizable columns, navigation restructure with Odds Comparison as landing page, sidebar status widgets, and real-time sidebar updates.

**Phases completed:** 93-98 (15+ plans total including 6 FIX plans, 1 decimal phase)

**Key accomplishments:**

- Tournament & country filters on Odds Comparison page with full tournament list access and availability-scoped filtering
- Resizable table columns with localStorage persistence for user customization
- Tournament data integrity fix (BUG-016) with composite unique constraint preventing cross-country collisions
- Coverage page improvements: stable summary cards, pagination, navigation shortcuts to related pages
- Historical Analysis polish: professional bookmaker pills with brand colors, tournament search, country filter
- Navigation overhaul: Odds Comparison as default landing page, compact sidebar status widgets
- Dashboard removed, sidebar reorganized into three sections (Analysis/Status/Utilities)
- Real-time sidebar updates via WebSocket query invalidation when scrapes complete

**Stats:**

- 64 files changed
- +4,695 / -908 lines (net +3,787)
- 6 phases (including 1 decimal), 15+ plans
- Same day (2026-02-12, ~4.5 hours)
- ~41,395 total LOC

**Git range:** `94780b3` → `e2dd0d7`

**What's next:** Project feature-complete. Use `/gsd:discuss-milestone` if additional features needed.

---

## v2.5 Odds Availability Tracking (Shipped: 2026-02-11)

**Delivered:** Track when odds/events become unavailable across platforms, display appropriately with strikethrough styling and tooltips, and visualize availability transitions in history charts.

**Phases completed:** 87-92 (6 plans total)

**Key accomplishments:**

- Investigated availability patterns: 15-56% market presence over time, designed unavailable_at timestamp approach with cache-level detection
- Backend availability tracking with schema migration, cache dataclass updates, and detection integrated into scraping pipeline
- API availability responses with `available` and `unavailable_since` fields on all market objects
- Odds Comparison UI with three-state display: normal odds, strikethrough dash with tooltip for unavailable, plain dash for never offered
- Event Details UI with consistent availability patterns in OddsBadge component
- History Charts with dashed line visualization for unavailable periods and "(unavailable)" tooltip suffix

**Stats:**

- 34 files changed
- +3,184 / -136 lines (net +3,048)
- 6 phases, 6 plans, 28 commits
- Same day (2026-02-11, ~2 hours)
- ~40,949 total LOC

**Git range:** `ed69f41` → `949881f`

**What's next:** Use `/gsd:discuss-milestone` to plan v2.6 features.

---

## v2.4 Historical Analytics (Shipped: 2026-02-11)

**Delivered:** Historical Analysis page with tournament-level margin analytics, interactive charts, time-to-kickoff analysis, and multi-bookmaker competitive comparison views.

**Phases completed:** 79-86 (19 plans total: 15 original + 4 FIX plans, including 84.1, 84.2, 85.1 decimal phases)

**Key accomplishments:**

- Fixed specifier bug in history API - now filters by market line parameter to prevent mixing Over 2.5 with Over 1.5 data
- Historical Analysis page with date range filters, tournament list from events API, and drill-down navigation
- Interactive OddsLineChart and MarginLineChart with click-through from tournament cards
- Comparison table with best/worst highlighting (green for best odds, red for >3% worse than Betpawa)
- Tournament detail page extracting ALL unique markets with avg/min/max margin stats and search
- Time-to-kickoff charts with bucket breakdown dialog (24h+, 12-24h, 6-12h, etc.)
- Opening vs closing margin comparison cards for primary markets (1X2, O/U 2.5, BTTS, DC)
- Multi-bookmaker comparison with overlay charts and difference bar charts showing competitive advantage

**Stats:**

- 97 files changed
- +11,858 / -177 lines (net +11,681)
- 11 phases (8 original + 3 decimal), 19 plans, 37 commits
- 2 days (2026-02-10 to 2026-02-11)
- ~40,000 total LOC

**Git range:** `1f1360a` → `032c39e`

**What's next:** Use `/gsd:discuss-milestone` to plan v2.5 features.

---

## v2.3 Code Quality & Reliability (Shipped: 2026-02-09)

**Delivered:** Stabilized WebSocket implementation, removed 1,256 LOC of dead code, added comprehensive documentation across frontend and backend, and improved type safety with annotations and error handling.

**Phases completed:** 72-78 (11 plans total)

**Key accomplishments:**

- Fixed WebSocket "always in progress" bug with compound isObserving state check (requires both activeScrapeId and connection)
- Added WebSocket reconnection callbacks with query invalidation and connection status indicator with manual retry
- Removed 1,256 LOC of dead backend code (unused imports, dependency functions, one-off audit scripts)
- Removed dead frontend code (empty types barrel, duplicate type definitions) with documented deferred items
- Added PEP 257 compliant docstrings to 19 backend API layer files (routes, schemas, WebSocket, core)
- Added JSDoc documentation to 29 frontend files (API client, types, shared hooks, feature hooks, utilities)
- Created comprehensive README.md documenting architecture, setup, API endpoints, and development workflow
- Added return type annotations to 10 functions and JSONDecodeError handling to 9 scraper API calls

**Stats:**

- 132 files changed
- +9,035 / -1,808 lines (net +7,227)
- 7 phases, 11 plans, 48 commits
- 1 day (2026-02-09)
- ~40,000 total LOC

**Git range:** `5b63b84` → `b273091`

**What's next:** Use `/gsd:discuss-milestone` to plan v2.4 features.

---

## v2.2 Odds Freshness (Shipped: 2026-02-09)

**Delivered:** Accurate real-time odds timestamps with WebSocket-based query invalidation, fixing staleness issues across the entire data flow from scraping to display.

**Phases completed:** 69-71 (3 plans total)

**Key accomplishments:**

- Complete data flow audit identifying 7 staleness sources (2 CRITICAL, 2 HIGH, 2 MEDIUM, 1 LOW)
- Root cause identified: API used `captured_at` (when odds changed) instead of `last_confirmed_at` (when last verified)
- Added `last_confirmed_at` to CachedSnapshot with `_get_snapshot_time()` helper pattern for consistent handling
- Created `useOddsUpdates` hook subscribing to WebSocket odds_updates topic with automatic query invalidation
- Real-time timestamp updates now work end-to-end without waiting for polling interval

**Stats:**

- 20 files changed
- +1,517 / -26 lines (net +1,491)
- 3 phases, 3 plans, 15 commits
- 1 day (2026-02-08 to 2026-02-09)
- ~40,000 total LOC

**Git range:** `8cfabdf` → `5b63b84`

**What's next:** Use `/gsd:discuss-milestone` to plan v2.3 features.

---

## v2.1 Historical Odds Tracking (Shipped: 2026-02-08)

**Delivered:** Interactive historical odds and margin visualization with clickable cells, tabbed dialogs, multi-bookmaker comparison mode, and small-multiples full market view.

**Phases completed:** 60-68 (12 plans total: 10 original + 2 FIX plans, Phase 61 skipped)

**Key accomplishments:**

- SQL analysis discovered existing schema already stores ~52 snapshots/event — no major schema changes needed
- Historical Data API with 3 endpoints for snapshot browsing, odds time-series, and margin time-series
- Freshness timestamps showing "last updated" on odds displays in Odds Comparison and Event Details pages
- recharts integration with OddsLineChart and MarginLineChart components with responsive sizing
- HistoryDialog component with tabbed Odds/Margin views and conditional data fetching
- Clickable odds/margins in both Odds Comparison and Event Details pages opening history dialogs
- Multi-bookmaker comparison mode with useQueries parallel fetch and overlay charts
- Small-multiples MarketHistoryPanel for viewing all outcomes × all bookmakers simultaneously

**Stats:**

- 44 files changed
- +4,505 / -51 lines (net +4,454)
- 9 phases (1 skipped), 12 plans, 37 commits
- 3 days (2026-02-06 to 2026-02-08)
- ~38,550 total LOC

**Git range:** `94d1825` → `7fb6d37`

**What's next:** Use `/gsd:discuss-milestone` to plan v2.2 features.

---

## v2.0 Real-Time Scraping Pipeline (Shipped: 2026-02-06)

**Delivered:** Eliminated storage bottleneck with in-memory caching, async write pipeline with change detection, concurrent event scraping, and WebSocket real-time updates replacing SSE entirely.

**Phases completed:** 53-59 + 55.1 (17 plans total: 16 original + 1 FIX plan)

**Key accomplishments:**

- In-memory cache layer achieving 97.3% API latency reduction (903ms → 24ms for event list endpoint)
- Async write pipeline with change detection for incremental upserts — only persist changed odds
- Intra-batch concurrent event scraping (10 parallel) reducing total pipeline time 65% (24 min → 8.5 min)
- WebSocket infrastructure with connection manager, message protocol, and real-time odds change notifications
- Complete SSE removal — WebSocket-only frontend for scrape progress and manual scrape triggers

**Stats:**

- 38 files changed
- +4,097 / -1,117 lines (net +2,980)
- 8 phases (7 original + 1 inserted), 17 plans, 60 commits
- 2 days (2026-02-05 to 2026-02-06)
- ~34,096 total LOC

**Git range:** `ebac67c` → `3021f9b`

**What's next:** Use `/gsd:discuss-milestone` to plan v2.1 features.

---

## v1.9 Event Details UX (Shipped: 2026-02-05)

**Delivered:** Transformed event details page into a powerful market exploration tool with category tabs, fuzzy search, competitor comparison mode, sticky navigation, and actionable summary metrics.

**Phases completed:** 48-52 (10 plans total: 5 original + 5 FIX plans)

**Key accomplishments:**

- Redesigned event summary with Market Coverage, Mapping Quality, and Competitive Position cards with category breakdowns
- Tabbed market navigation organized by BetPawa categories (Popular, Goals, Handicaps, Corners, Cards, Specials, Combos, Halves, Other) with multi-group support
- Fuzzy market search with subsequence matching and competitor selector with dynamic column reordering
- Sticky navigation header with scroll-to-top button for long market lists
- Shared market utilities (`lib/market-utils.ts`) eliminating ~80 lines of code duplication
- Context-aware empty state messages explaining which filters cause zero results

**Stats:**

- 40 files changed
- +3,599 / -205 lines (net +3,394)
- 5 phases, 10 plans, 38 commits
- 2 days (2026-02-03 to 2026-02-04)
- ~31,116 total LOC

**Git range:** `fdec213` → `1c6547d`

**What's next:** Use `/gsd:discuss-milestone` to plan v2.0 features.

---

## v1.8 Market Matching Accuracy (Shipped: 2026-02-03)

**Delivered:** Comprehensive market mapping audit and targeted fixes — 20 new mappings covering ~1,800 occurrences, combo market parameter handling, handicap line fix, and outcome name normalization.

**Phases completed:** 43-47 (9 plans total: 7 original + 2 FIX plans)

**Key accomplishments:**

- Comprehensive audit identifying 380 unmapped market types across platforms
- 20 new market mappings covering high-priority gaps (~1,800 occurrences)
- Combo market parameter handling (1X2OU, DCOU, etc.)
- Handicap market line field fix for competitor odds display
- Cross-bookmaker outcome name normalization
- Mapping success rates improved: SportyBet 47.3%→52.2%, Bet9ja 36.1%→40.5%

**Stats:**

- 28 files changed
- +13,290 / -57 lines (net +13,233)
- 5 phases, 9 plans
- 2 days (2026-02-02 to 2026-02-03)

**Git range:** `feat(43-01)` → `feat(47-01)`

**What's next:** Use `/gsd:discuss-milestone` to plan next milestone.

---

## v1.7 Scraping Architecture Overhaul (Shipped: 2026-02-02)

**Delivered:** Redesigned scraping from sequential platform-by-platform execution to event-centric parallel architecture, reducing timing gaps from minutes to milliseconds for reliable cross-platform odds comparison.

**Phases completed:** 36-42 (16 plans total: 7 original + 9 FIX plans)

**Key accomplishments:**

- Designed and implemented EventCoordinator with priority queue (kickoff urgency + coverage value)
- Simultaneous multi-bookmaker scraping per event with semaphore-based rate limiting
- Batch database storage with single-flush pattern for optimal performance
- Configurable concurrency limits via Settings API (betpawa_concurrency, sportybet_concurrency, etc.)
- On-demand single-event refresh endpoint POST /api/scrape/event/{sr_id}
- Removed ~1,884 lines of legacy ScrapingOrchestrator code
- Fixed 9 UAT bugs during validation (BetPawa discovery, SR ID extraction, competitor tournaments, EventBookmaker linking)

**Stats:**

- 55 files changed
- +8,941 / -2,059 lines (net +6,882)
- 7 phases, 16 plans, 51 commits
- 4 days (2026-01-29 to 2026-02-02)

**Git range:** `b93b6ff` → `c330646`

**What's next:** Use `/gsd:new-milestone` to plan additional features (WebSocket real-time, historical trends, etc.).

---

## v1.6 Event Matching Accuracy (Shipped: 2026-01-29)

**Delivered:** Investigated and fixed event matching accuracy issues — audit confirmed 99.9% backend accuracy, fixed API-001 coverage inflation bug, and remediated 2 timing-affected events.

**Phases completed:** 34, 34.1, 35 (3 plans total)

**Key accomplishments:**

- Comprehensive audit of SportRadar ID matching across all 3 platforms — confirmed 99.9% accuracy
- Identified 23-26% unmatched rate is correct behavior (competitor-only events, not bugs)
- Discovered only 2 events affected by timing edge case (scraped before BetPawa existed)
- Identified 2 API bugs: coverage inflation (API-001) and legacy odds architecture (API-002)
- Fixed API-001: Coverage stats now use DISTINCT SR ID counting (92% reduction in inflated count)
- Remediated 2 timing-orphaned events with one-time SQL query

**Stats:**

- 18 files modified
- +2,194 / -12 lines of Python
- 3 phases (including 1 decimal), 3 plans
- 2 days (2026-01-28 to 2026-01-29)

**Git range:** `3bf13d5` → `ec8c1c0`

**What's next:** Use `/gsd:new-milestone` to plan additional features (API-002 fix, WebSocket real-time, historical trends).

---

## v1.5 Scraping Observability (Shipped: 2026-01-28)

**Delivered:** Made scraping progress transparent with stale run detection, connection loss recovery, per-platform progress events, and scheduler interval display fix.

**Phases completed:** 31-33.1 (4 plans total)

**Key accomplishments:**

- Background watchdog that auto-fails scrape runs stuck in RUNNING status
- Startup recovery for runs left stale after server crashes
- SSE connection loss detection with CONNECTION_FAILED status and auto-rescrape on recovery
- Per-platform progress events showing real event counts and timing per bookmaker
- Fixed scheduler interval display showing correct scrape interval instead of watchdog interval

**Stats:**

- 32 files modified
- +2,243 / -88 lines of Python + TypeScript
- 4 phases (including 1 decimal), 4 plans
- 2 days (2026-01-27 to 2026-01-28)

**Git range:** `4bc1260` → `ad7a74a`

**What's next:** Use `/gsd:new-milestone` to plan additional features.

---

## v1.4 Odds Comparison UX (Shipped: 2026-01-26)

**Delivered:** Redesigned Matches page with bookmakers-as-rows table layout, Double Chance market with per-market margins, and renamed to "Odds Comparison" with new URL route.

**Phases completed:** 28-30 (3 plans total)

**Key accomplishments:**

- Restructured table to bookmakers-as-rows layout with rowspan for match grouping
- Added Double Chance market (1X, X2, 12) as selectable column
- Added per-market margin display with comparative color coding
- Renamed page from "Matches" to "Odds Comparison"
- Changed URL route from /matches to /odds-comparison
- Updated navigation icon to BarChart3

**Stats:**

- 17 files modified
- +986 / -159 lines of TypeScript
- 3 phases, 3 plans
- Same day as v1.3 (2026-01-26, ~38 min execution)

**Git range:** `0b005ce` → `54a23eb`

**What's next:** Use `/gsd:new-milestone` to plan additional features (WebSocket real-time, historical trends, etc.).

---

## v1.3 Coverage Improvements (Shipped: 2026-01-26)

**Delivered:** Enhanced Coverage Comparison page UX with searchable multi-select filters, tournament-level gap analysis, and unified dashboard coverage metrics.

**Phases completed:** 23-27 (5 plans total)

**Key accomplishments:**

- Fixed match rate bug showing 8774% instead of ~87.7%
- Searchable multi-select country filter with type-to-filter UX
- Include Started toggle to hide in-play events
- Tournament gaps cards showing coverage analysis by competitor
- Dashboard stats cards using live coverage data via useCoverage hook

**Stats:**

- 10 files modified
- ~385 lines of TypeScript added
- 5 phases, 5 plans
- 1 day (same day as v1.2: 2026-01-26)

**Git range:** `dc9ddde` → `f1a0bbc`

**What's next:** Use `/gsd:new-milestone` to plan additional features (WebSocket real-time, historical trends, etc.).

---

## v1.2 Settings & Retention (Shipped: 2026-01-26)

**Delivered:** Persistent configuration with configurable data retention, automatic cleanup scheduling, and improved settings UI with data management controls.

**Phases completed:** 19.1-22 (8 plans total)

**Key accomplishments:**

- Desktop sidebar overlay with backdrop dimming and click-to-close
- History retention settings (1-90 day configurable, default 7 days)
- Settings persistence at startup (scheduler syncs interval from DB)
- Cleanup service with preview-before-delete pattern
- Automatic cleanup scheduler running daily at 2 AM UTC
- Settings UI redesign with compact 4-row layout
- Manage Data dialog with overview, cleanup, and history tabs

**Stats:**

- 47 files modified
- ~3,800 lines of Python + TypeScript added
- 4 phases (including decimal), 8 plans
- 2 days from v1.1 to v1.2 (2026-01-25 to 2026-01-26)

**Git range:** `docs(19.1)` → `chore: remove phase 23`

**What's next:** Use `/gsd:new-milestone` to plan additional features (WebSocket real-time, historical trends, etc.).

---

## v1.1 Palimpsest Comparison (Shipped: 2026-01-24)

**Delivered:** Full competitor palimpsest comparison enabling visibility into tournaments and events available on SportyBet/Bet9ja but not BetPawa.

**Phases completed:** 13-19 (11 plans total)

**Key accomplishments:**

- Extended database with 5 competitor tables for independent tournament/event/odds storage
- Tournament discovery service scraping ~200+ tournaments per platform from SportyBet and Bet9ja
- Full competitor event scraping with parallel execution and SportRadar ID matching
- Palimpsest API with coverage statistics and comprehensive event filtering
- Matches page mode toggle for viewing competitor-only events alongside BetPawa matches
- Coverage Comparison page with stat cards, filters, and expandable tournament table

**Stats:**

- 71 files modified
- ~8,500 lines of Python + TypeScript added
- 7 phases, 11 plans
- 2 days from v1.0 to v1.1 (2026-01-23 to 2026-01-24)

**Git range:** `feat(13-01)` → `docs(19-03)`

**What's next:** Additional competitor analysis features, WebSocket real-time updates, or historical trend visualization.

---

## v1.0 MVP (Shipped: 2026-01-23)

**Delivered:** Complete odds comparison tool with cross-platform market matching, real-time scraping, and React dashboard for competitive analysis.

**Phases completed:** 1-12 (46 plans total)

**Key accomplishments:**

- 108 market mappings from SportyBet and Bet9ja to Betpawa canonical format
- Cross-platform event matching via SportRadar IDs across all three bookmakers
- Side-by-side odds comparison with color-coded indicators (green=better, red=worse)
- Real-time scraping with SSE progress streaming and per-platform status tracking
- React dashboard with scheduler controls, platform health, and scrape run history
- Settings page for configurable scraping intervals and system preferences

**Stats:**

- 18,595 lines of Python + TypeScript
- 15 phases, 46 plans
- 235 commits
- 4 days from start to ship (2026-01-20 to 2026-01-23)

**Git range:** `feat(01-01)` to `fix(api): add /api prefix`

**What's next:** Use `/gsd:new-milestone` to plan the next version when new features are needed.

---
