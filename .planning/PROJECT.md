# Betpawa Odds Comparison Tool

## What This Is

A comparative analysis tool (branded "pawaRisk") for Betpawa to analyze and compare its football markets and odds with competitors (SportyBet, Bet9ja). The tool scrapes odds data on a schedule, matches events across platforms using SportRadar IDs, and displays side-by-side comparisons with margin analysis through a React web interface.

## Core Value

Accurate cross-platform market matching and real-time odds comparison that enables Betpawa to understand its competitive position in the Nigerian market.

## Current State (v2.9 Market-Level Storage Architecture)

**Shipped:** 2026-02-24

**Tech Stack:**
- Backend: Python 3.11+, FastAPI, SQLAlchemy 2.0, PostgreSQL, APScheduler
- Frontend: React 19, Vite, TanStack Query v5, Tailwind CSS v4, shadcn/ui, recharts
- ~45,000 lines of code

**Capabilities:**
- 128 market mappings from SportyBet and Bet9ja to Betpawa format (20 new in v1.8)
- Cross-platform event matching via SportRadar IDs (99.9% accuracy confirmed)
- **Event-centric parallel scraping** - all platforms scraped simultaneously per event
- EventCoordinator with priority queue (kickoff urgency + coverage value)
- Configurable concurrency limits via Settings API
- On-demand single-event refresh POST /api/scrape/event/{sr_id}
- **In-memory cache layer** - 97.3% API latency reduction (903ms → 24ms for event list)
- **Async write pipeline** - change detection for incremental upserts, only persist changed odds
- **Intra-batch concurrent scraping** - 10 parallel events reducing pipeline time 65% (24 min → 8.5 min)
- **WebSocket real-time updates** - /api/ws endpoint with topic subscriptions (scrape_progress, odds_updates)
- **WebSocket-only frontend** - SSE infrastructure removed, all progress via WebSocket
- Dashboard with scheduler controls, platform health, and live coverage metrics
- Match list and detail views with color-coded odds comparison
- Full competitor palimpsest scraping (~200+ tournaments per platform)
- Coverage Comparison page with accurate tournament/event availability analysis
- Searchable multi-select country filter with type-to-filter UX
- Include Started toggle to filter out in-play events
- Tournament gaps cards showing coverage by competitor
- Mode toggle on Matches page for competitor-only events
- Configurable history retention (1-90 days)
- Automatic cleanup scheduler with daily execution
- Settings persistence across server restarts
- Manage Data dialog for manual cleanup and data overview
- Bookmakers-as-rows table layout for vertical odds comparison
- Double Chance market (1X, X2, 12) with per-market margins
- Comparative margin color coding (Betpawa vs competitors)
- Renamed page to "Odds Comparison" with /odds-comparison route
- Stale run detection watchdog with auto-fail for hung scrapes
- Startup recovery for stale runs after server crashes
- Connection loss detection with CONNECTION_FAILED status and auto-rescrape
- Accurate coverage statistics with DISTINCT SportRadar ID counting
- **Event detail summary cards** - Market Coverage, Mapping Quality, Competitive Position with category breakdowns
- **Tabbed market navigation** - BetPawa categories (Popular, Goals, Handicaps, Corners, Cards, Specials, Combos, Halves, Other)
- **Market groups as JSON arrays** - markets appear in all their category tabs
- **Fuzzy market search** - subsequence matching (e.g., "o25" matches "Over 2.5 Goals")
- **Competitor comparison mode** - dynamic column reordering with selected competitor adjacent to Betpawa
- **Sticky navigation header** - fixed positioning with scroll-to-top button for long market lists
- **Shared market utilities** - deduplicated code in lib/market-utils.ts
- **Context-aware empty states** - messages explaining which filters cause zero results
- **Historical Data API** - 3 endpoints for snapshot history, odds time-series, margin time-series
- **Freshness timestamps** - "last updated" display on odds in Odds Comparison and Event Details pages
- **HistoryDialog component** - tabbed Odds/Margin views with conditional data fetching
- **Clickable odds/margins** - click any odds or margin value to open history dialog
- **Multi-bookmaker comparison** - overlay charts comparing odds/margins across BetPawa, SportyBet, Bet9ja
- **Small-multiples MarketHistoryPanel** - view all outcomes × all bookmakers simultaneously
- **Accurate odds freshness timestamps** - uses `last_confirmed_at` for correct freshness display
- **Real-time timestamp updates** - WebSocket odds_updates subscription with automatic query invalidation
- **WebSocket connection indicator** - visual status (green/yellow/gray/red) with manual retry button
- **WebSocket reconnection callbacks** - automatic query invalidation on reconnect for fresh data
- **Comprehensive documentation** - PEP 257 docstrings for backend, JSDoc for frontend
- **README.md** - project overview, architecture, setup, API endpoints, development workflow
- **Historical Analysis page** - tournament-level margin analytics with date range filters and drill-down
- **Interactive timeline charts** - OddsLineChart and MarginLineChart with click-through navigation
- **Tournament detail view** - ALL unique markets with avg/min/max margin stats and search
- **Time-to-kickoff analysis** - bucket breakdown dialog showing margin trends by time period
- **Multi-bookmaker comparison** - overlay charts and difference bar charts for competitive analysis
- **Odds availability tracking** - `unavailable_at` timestamp detecting when markets disappear
- **Three-state availability display** - normal odds, strikethrough+tooltip for unavailable, dash for never offered
- **History charts availability** - dashed lines for unavailable periods with "(unavailable)" tooltip suffix
- **Tournament & country filters** - full tournament list access with availability-scoped filtering on Odds Comparison page
- **Resizable table columns** - drag-to-resize with localStorage persistence for user customization
- **Tournament data integrity** - composite unique constraint (sport_id, name, country) preventing cross-country collisions
- **Coverage page improvements** - stable summary cards, client-side pagination, navigation shortcuts
- **Historical Analysis filters** - professional bookmaker pills with brand colors, tournament search, country multi-select
- **Navigation overhaul** - Odds Comparison as default landing page, compact sidebar status widgets
- **Sidebar reorganization** - three sections (Analysis/Status/Utilities), Dashboard page removed
- **Real-time sidebar updates** - WebSocket query invalidation for sidebar widgets on scrape completion
- **Database reduced 81%** - 63 GB → 12 GB through raw_response removal and 7-day retention (v2.8)
- **Storage dashboard** - table sizes, growth charts, and alerting for abnormal expansion (v2.8)
- **Market-level storage** - market_odds_current (upsert) + market_odds_history (append) for 95% row reduction (v2.9)
- **Market-level change detection** - only persist individual markets that changed, not full snapshots (v2.9)
- **14-day retention** - increased from 7 days with market_odds_history cleanup (v2.9)
- **Dual-query history API** - queries both new market_odds_history and legacy tables for complete data (v2.9)

## Requirements

### Validated

- ✓ Port TypeScript mapping library to Python — v1.0
- ✓ FastAPI backend service orchestrating scrapers — v1.0
- ✓ PostgreSQL database with timestamped odds snapshots — v1.0
- ✓ Scheduled scraping with configurable interval — v1.0
- ✓ Event matching by SportRadar ID across all platforms — v1.0
- ✓ Market mapping for 108 supported markets — v1.0
- ✓ React frontend with match list view (1X2, O/U 2.5, BTTS) — v1.0
- ✓ Match detail view with all markets (Betpawa grouping) — v1.0
- ✓ Side-by-side odds display for each market — v1.0
- ✓ Margin percentage calculation per bookmaker — v1.0
- ✓ Value delta showing Betpawa vs competitors — v1.0
- ✓ Color-coded indicators (green/red) for better/worse odds — v1.0
- ✓ Filtering by league, date/time — v1.0
- ✓ N/A indicators when competitor lacks a market — v1.0
- ✓ Per-event data freshness timestamps — v1.0
- ✓ Competitor tournament discovery scraping — v1.1
- ✓ Full competitor event scraping with parallel execution — v1.1
- ✓ Competitor-only event visibility on Matches page — v1.1
- ✓ Coverage Comparison page with tournament/event availability — v1.1
- ✓ Palimpsest API with coverage stats and event filtering — v1.1
- ✓ Configurable history retention (1-90 days) — v1.2
- ✓ Automatic cleanup scheduler — v1.2
- ✓ Settings persistence across restarts — v1.2
- ✓ Manage Data dialog with cleanup controls — v1.2
- ✓ Searchable multi-select country filter — v1.3
- ✓ Include Started toggle for pre-match focus — v1.3
- ✓ Tournament gaps cards per competitor — v1.3
- ✓ Dashboard coverage widgets with live data — v1.3
- ✓ Bookmakers-as-rows table layout for vertical comparison — v1.4
- ✓ Double Chance market (1X, X2, 12) as selectable column — v1.4
- ✓ Per-market margin display with comparative color coding — v1.4
- ✓ Renamed page to "Odds Comparison" with new URL route — v1.4
- ✓ Stale run detection watchdog with auto-fail for hung scrapes — v1.5
- ✓ Startup recovery for stale runs after server crashes — v1.5
- ✓ Connection loss detection with CONNECTION_FAILED status and auto-rescrape — v1.5
- ✓ Per-platform progress events with real counts and timing — v1.5
- ✓ Correct scheduler interval display (ISS-003 fix) — v1.5
- ✓ Event matching accuracy audit with SQL evidence — v1.6
- ✓ Coverage statistics using DISTINCT SportRadar IDs (API-001 fix) — v1.6
- ✓ Event-centric parallel scraping architecture (EventCoordinator) — v1.7
- ✓ Priority queue with kickoff urgency and coverage value — v1.7
- ✓ Configurable concurrency limits via Settings API — v1.7
- ✓ On-demand single-event refresh endpoint — v1.7
- ✓ Competitor odds in event detail page — v1.7
- ✓ Comprehensive market mapping audit with categorized gap analysis — v1.8
- ✓ 20 new market mappings covering ~1,800 occurrences — v1.8
- ✓ Combo market parameter handling (1X2OU, DCOU, etc.) — v1.8
- ✓ Handicap market line field fix for competitor odds display — v1.8
- ✓ Cross-bookmaker outcome name normalization — v1.8
- ✓ Mapping success rates: SportyBet 52.2%, Bet9ja 40.5% — v1.8
- ✓ Event detail summary cards (Market Coverage, Mapping Quality, Competitive Position) — v1.9
- ✓ Tabbed market navigation by BetPawa categories with multi-group support — v1.9
- ✓ Fuzzy market search with subsequence matching — v1.9
- ✓ Competitor comparison mode with dynamic column reordering — v1.9
- ✓ Sticky navigation header with scroll-to-top button — v1.9
- ✓ Shared market utilities eliminating code duplication — v1.9
- ✓ Context-aware empty state messages — v1.9
- ✓ In-memory cache layer with 97.3% API latency reduction — v2.0
- ✓ Async write pipeline with change detection for incremental upserts — v2.0
- ✓ Intra-batch concurrent event scraping (10 parallel, 65% pipeline reduction) — v2.0
- ✓ WebSocket real-time updates (/api/ws with topic subscriptions) — v2.0
- ✓ WebSocket-only frontend (SSE removed) — v2.0
- ✓ Historical Data API with snapshot, odds, and margin history endpoints — v2.1
- ✓ Freshness timestamps on odds display — v2.1
- ✓ HistoryDialog with tabbed Odds/Margin chart views — v2.1
- ✓ Clickable odds/margins in Odds Comparison and Event Details pages — v2.1
- ✓ Multi-bookmaker comparison mode with overlay charts — v2.1
- ✓ Small-multiples MarketHistoryPanel for full market view — v2.1
- ✓ Accurate odds freshness timestamps using `last_confirmed_at` — v2.2
- ✓ Real-time timestamp updates via WebSocket odds_updates subscription — v2.2
- ✓ Automatic query invalidation on odds changes without polling — v2.2
- ✓ WebSocket "always in progress" bug fix with compound isObserving state — v2.3
- ✓ WebSocket reconnection callbacks with query invalidation — v2.3
- ✓ Connection status indicator with manual retry button — v2.3
- ✓ Dead code removal (1,256 LOC backend, duplicate types frontend) — v2.3
- ✓ PEP 257 docstrings for backend API, data, and orchestration layers — v2.3
- ✓ JSDoc documentation for frontend API client, types, and hooks — v2.3
- ✓ Comprehensive README.md with architecture and setup guide — v2.3
- ✓ Return type annotations for 10 functions — v2.3
- ✓ JSONDecodeError handling for 9 scraper API calls — v2.3
- ✓ Historical Analysis page with tournament list and date range filters — v2.4
- ✓ Interactive timeline charts with click-through from tournament cards — v2.4
- ✓ Tournament detail page with ALL market cards and margin stats — v2.4
- ✓ Time-to-kickoff bucket analysis with breakdown dialog — v2.4
- ✓ Opening vs closing margin comparison cards — v2.4
- ✓ Multi-bookmaker comparison with overlay and difference charts — v2.4
- ✓ Line parameter in history API for specifier-based market filtering — v2.4
- ✓ Availability tracking with `unavailable_at` timestamp column — v2.5
- ✓ Cache-level availability detection comparing previous to current scrape — v2.5
- ✓ API availability responses with `available` and `unavailable_since` fields — v2.5
- ✓ Three-state availability display in Odds Comparison (normal/strikethrough/dash) — v2.5
- ✓ Three-state availability display in Event Details (OddsBadge) — v2.5
- ✓ History charts with dashed lines for unavailable periods — v2.5
- ✓ Tournament & country filters on Odds Comparison page with full list access — v2.6
- ✓ Resizable table columns with localStorage persistence — v2.6
- ✓ Tournament data integrity fix with composite unique constraint (BUG-016) — v2.6
- ✓ Coverage page stable summary cards with client-side pagination — v2.6
- ✓ Coverage page navigation shortcuts to related pages — v2.6
- ✓ Historical Analysis professional bookmaker pills with brand colors — v2.6
- ✓ Historical Analysis tournament search and country filter — v2.6
- ✓ Odds Comparison as default landing page — v2.6
- ✓ Sidebar status widgets with event count and health indicators — v2.6
- ✓ Dashboard removal and sidebar reorganization into three sections — v2.6
- ✓ Real-time sidebar updates via WebSocket query invalidation — v2.6
- ✓ Availability detection pipeline persisting unavailable_at to database — v2.7
- ✓ Reconciliation for events dropped from platform discovery — v2.7
- ✓ Consistent unavailable styling on Odds Comparison (strikethrough + tooltip) — v2.7
- ✓ Alerts toggle filtering events with unavailable markets — v2.7
- ✓ Alerts filter querying only latest snapshot per event — v2.7
- ✓ Database profiling identifying raw_response as primary storage driver — v2.8
- ✓ raw_response column removal reclaiming 33 GB (53% of database) — v2.8
- ✓ VACUUM FULL for space reclamation after column drop — v2.8
- ✓ Storage size API with history tracking for trend analysis — v2.8
- ✓ Storage dashboard with table sizes and growth charts — v2.8
- ✓ Growth alerting for abnormal database expansion — v2.8
- ✓ Market-level schema design achieving 95% storage reduction — v2.9
- ✓ market_odds_current table with UPSERT pattern for current state — v2.9
- ✓ market_odds_history table with append-only storage for charts — v2.9
- ✓ Market-level change detection replacing snapshot-level detection — v2.9
- ✓ Cache warmup and API fallback migrated to new schema — v2.9
- ✓ History API migrated to market_odds_history (42% code reduction) — v2.9
- ✓ 14-day retention with market_odds_history cleanup — v2.9
- ✓ Dual-query history API for legacy and new data sources — v2.9

### Active

(No active requirements — project feature-complete for v2.9)

### Out of Scope

- User accounts/authentication — internal tool, no access control needed
- Alerts/notifications to admins — deferred, add after MVP
- Data export (CSV/PDF) — view only for now
- Sports other than football — focus on football only
- Regions other than Nigeria — Nigeria focus
- Mobile-first design — desktop-first, basic mobile usability

## Context

**Existing codebase:**
- `src/market_mapping/`: Python library for market transformation (128 mappings)
- `src/scraping/`: Async clients for SportyBet, BetPawa, Bet9ja with EventCoordinator
- `src/caching/`: In-memory OddsCache with async write queue
- `src/api/`: FastAPI backend with scheduler and WebSocket streaming
- `web/`: React frontend with TanStack Query and shadcn/ui

**Technical decisions:**
- Betpawa is canonical format — competitors mapped to Betpawa taxonomy
- SportRadar IDs enable reliable cross-platform matching
- WebSocket for real-time progress and odds updates (/api/ws)
- In-memory cache with frozen dataclasses for fast API responses
- Async write queue with change detection for efficient DB persistence
- structlog for structured logging with JSON/console modes

## Constraints

- **Region**: Nigeria — scrapers configured for Nigerian market APIs
- **Data retention**: 14 days — balance storage costs with analysis needs (updated v2.9)
- **Match confidence**: SportRadar ID only — no fuzzy name matching

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Port TypeScript mapping to Python | Single-language backend simplifies deployment | ✓ Good — 108 mappings working |
| FastAPI for backend | Modern async Python framework, handles SSE well | ✓ Good — clean architecture |
| PostgreSQL for storage | Robust, handles time-series well, supports complex queries | ✓ Good — performant |
| React for frontend | Popular ecosystem, good for data-heavy dashboards | ✓ Good — maintainable |
| TanStack Query for state | Server-state focused, handles caching/refetching | ✓ Good — reduced boilerplate |
| Tailwind for styling | Fast prototyping, utility-first | ✓ Good — consistent styling |
| SSE for real-time | Simpler than WebSocket for one-way streaming | ✓ Good — works well for progress |
| StrEnum for status fields | Type safety + string storage in DB | ✓ Good — clean enums |
| Betpawa-first metadata | Competitors insert-only except kickoff | ✓ Good — consistent data |
| Separate competitor tables | Independent tournament/event storage, match at query time | ✓ Good — v1.1 clean schema |
| Metadata priority sportybet > bet9ja | SportyBet has better SR ID coverage | ✓ Good — v1.1 consistent display |
| Fetch-then-store pattern | API parallel, DB sequential avoids session conflicts | ✓ Good — v1.1 solved async issues |
| Negative IDs for competitor events | Distinguish competitor-only from BetPawa events in API | ✓ Good — v1.1 simple frontend check |
| Default 7-day retention | Balance storage vs analysis needs for frequently changing odds | ✓ Good — v1.2 sensible default |
| 1-90 day retention range | Prevent extremes (immediate deletion or excessive storage) | ✓ Good — v1.2 reasonable bounds |
| Preview-before-delete pattern | Prevent accidental data loss with confirmation | ✓ Good — v1.2 safe UX |
| Daily cleanup at 2 AM UTC | Off-peak hours, consistent scheduling | ✓ Good — v1.2 minimal disruption |
| Command + Popover for multi-select | Consistent with shadcn/ui patterns | ✓ Good — v1.3 searchable combobox |
| Empty selection = all countries | No explicit "All" option needed | ✓ Good — v1.3 intuitive UX |
| Default includeStarted OFF | Pre-match focus for odds comparison | ✓ Good — v1.3 sensible default |
| Reuse useCoverage across features | Single data source, consistent metrics | ✓ Good — v1.3 reduced API calls |
| Bookmakers-as-rows layout | Vertical comparison easier to read than horizontal | ✓ Good — v1.4 better UX |
| Comparative margin colors | vs competitors more useful than absolute thresholds | ✓ Good — v1.4 clear comparison |
| Text color for margins | Better readability than background colors | ✓ Good — v1.4 cleaner UI |
| BarChart3 navigation icon | Better visual representation of odds comparison | ✓ Good — v1.4 intuitive |
| URL route /odds-comparison | Full naming consistency with page title | ✓ Good — v1.4 coherent |
| 2-min watchdog interval | Balance responsiveness vs overhead for stale detection | ✓ Good — v1.5 catches hangs quickly |
| CONNECTION_FAILED as distinct status | Different from FAILED, enables specific UI treatment | ✓ Good — v1.5 clear UX |
| Auto-rescrape on connection recovery | User doesn't need to manually retry after disconnect | ✓ Good — v1.5 seamless recovery |
| Per-platform SSE events | Reuse existing SSE infrastructure, no WebSocket needed | ✓ Good — v1.5 minimal complexity |
| SQL-based audit methodology | Comprehensive SQL diagnostics to verify data quality | ✓ Good — v1.6 found real issues |
| DISTINCT SR ID for coverage | Count unique events, not duplicate rows across runs | ✓ Good — v1.6 fixed 92% inflation |
| One-time SQL for timing fix | Data fix, not migration - edge case won't recur | ✓ Good — v1.6 clean remediation |
| Event-centric parallel scraping | Scrape all platforms per event vs sequential by platform | ✓ Good — v1.7 timing gaps reduced to ms |
| Priority queue composite key | (urgency_tier, kickoff, -coverage, not_has_betpawa) | ✓ Good — v1.7 optimal scrape ordering |
| EventCoordinator factory method | from_settings() creates instances with configurable tuning | ✓ Good — v1.7 flexible initialization |
| Single-flush batch insert | Add all records, single flush, link FKs, commit | ✓ Good — v1.7 100x fewer DB round trips |
| BetPawa widget.id for SR ID | SR ID is in widget["id"], 8-digit numeric string | ✓ Good — v1.7 correct extraction |
| Competitor tournament from raw | Extract tournament/country from competitor API responses | ✓ Good — v1.7 proper metadata |
| Audit-driven market mapping | Comprehensive audit before targeted fixes | ✓ Good — v1.8 identified 380 unmapped types |
| Fix handicap line at storage | Populate line from handicap.home in event_coordinator | ✓ Good — v1.8 minimal code change |
| Normalize outcome names at match time | Keep raw data intact, fix display layer | ✓ Good — v1.8 preserves debugging ability |
| Combo market O/U routing | Add combo keys to O/U parameter handling sets | ✓ Good — v1.8 eliminated UNKNOWN_PARAM_MARKET |
| Market group from BetPawa tabs | Extract non-"all" tabs as market categories | ✓ Good — v1.9 accurate grouping |
| Multi-group JSON array | Store all tabs per market for multi-category membership | ✓ Good — v1.9 markets appear in all relevant tabs |
| Fuzzy subsequence matching | Query chars must appear in target in order | ✓ Good — v1.9 intuitive partial matching |
| Dynamic column reordering | Selected competitor moves adjacent to Betpawa | ✓ Good — v1.9 focused comparison |
| Fixed positioning over CSS sticky | App uses overflow-auto on main, breaking CSS sticky | ✓ Good — v1.9 works with overflow containers |
| data-scroll-container attribute | Target correct scroll element in nested main elements | ✓ Good — v1.9 reusable pattern |
| Shared market utilities module | Extract duplicated logic to lib/market-utils.ts | ✓ Good — v1.9 eliminated ~80 lines duplication |
| Categories from data not heuristics | Use actual market_groups from API, not keyword matching | ✓ Good — v1.9 perfect alignment with tabs |
| Frozen dataclasses for cache entries | Immutable, hashable, no ORM session dependency | ✓ Good — v2.0 avoids detached instance issues |
| Cache-before-persist pattern | Update cache immediately, persist asynchronously | ✓ Good — v2.0 API always serves fresh data |
| asyncio.gather over TaskGroup | Partial failure tolerance, no cascading cancellation | ✓ Good — v2.0 one event failure doesn't stop batch |
| Dual-layer semaphore design | Event-level (10) + platform-level (50/50/15) throttling | ✓ Good — v2.0 fine-grained concurrency control |
| WebSocket endpoint at /api/ws | Topic-based pub/sub with ConnectionManager | ✓ Good — v2.0 clean real-time infrastructure |
| WebSocket-only frontend | SSE removed after WebSocket migration complete | ✓ Good — v2.0 eliminates transport complexity |
| Change detection via normalized tuples | Sort outcomes by name for order-independent comparison | ✓ Good — v2.0 only persist changed odds |
| No schema changes for history | Current architecture with odds_snapshots + market_odds already stores history | ✓ Good — v2.1 avoided overhaul |
| Skip Phase 61 | Existing odds_retention_days setting already provides configurable retention | ✓ Good — v2.1 no duplicate functionality |
| Tab-conditional data fetching | enabled=open && activeTab prevents API calls for inactive tabs | ✓ Good — v2.1 optimal performance |
| Reusable onClick on value components | OddsBadge/MarginIndicator accept optional onClick for any page | ✓ Good — v2.1 code reuse |
| Small-multiples for multi-outcome viz | One mini-chart per outcome cleaner than one chart with many lines | ✓ Good — v2.1 readable charts |
| useQueries for parallel multi-bookmaker | TanStack Query useQueries for concurrent API calls | ✓ Good — v2.1 efficient fetching |
| `last_confirmed_at` for freshness | Separate "when changed" from "when verified" — use latter for display | ✓ Good — v2.2 accurate timestamps |
| `_get_snapshot_time()` helper | DRY timestamp extraction with fallback for backward compatibility | ✓ Good — v2.2 consistent handling |
| Global WebSocket subscription in App | useOddsUpdates hook at root for automatic query invalidation | ✓ Good — v2.2 real-time updates |
| Inner AppContent component | Hooks needing QueryClient must be inside QueryClientProvider | ✓ Good — v2.2 proper React context |
| Compound boolean for isObserving | Requires both activeScrapeId !== null AND ws.isConnected | ✓ Good — v2.3 fixed false progress |
| wasConnectedRef pattern | Track first connection to distinguish reconnection from initial connect | ✓ Good — v2.3 correct callback timing |
| Stable connection timeout | Delay 30s before resetting retry counter to prevent premature reset | ✓ Good — v2.3 handles flaky networks |
| Remove HIGH confidence dead code only | Defer LOW confidence items as documented concerns | ✓ Good — v2.3 safe cleanup |
| JSDoc format matching PEP 257 style | Consistency between frontend and backend documentation | ✓ Good — v2.3 unified style |
| TypeVar for generic decorator | Simple T = TypeVar("T") instead of complex protocol types | ✓ Good — v2.3 readable annotations |
| Line parameter as optional query param | Backward compatibility with existing history API consumers | ✓ Good — v2.4 fixed specifier mixing |
| Extract ALL unique markets from Betpawa | Full visibility into any market type, not just tracked 4 | ✓ Good — v2.4 complete analytics |
| getMarketKey(id, line) pattern | Unique identification distinguishing specifier variants | ✓ Good — v2.4 correct market grouping |
| Simplify over explain pattern | Remove complexity rather than add tooltips/labels | ✓ Good — v2.4 cleaner UX |
| Option B unavailable_at timestamp | Timestamp tells us WHEN, not just IF unavailable | ✓ Good — v2.5 enables tooltips |
| Detection at cache layer | Compare previous cache to new scrape for availability changes | ✓ Good — v2.5 efficient detection |
| UI distinction dash vs strikethrough | Differentiate never_offered from became_unavailable | ✓ Good — v2.5 clear UX |
| Dashed overlay line approach | Simpler than gradient masking, no SVG complexity | ✓ Good — v2.5 clean charts |
| Separate localStorage keys for settings | Use distinct keys for column-widths vs column-visibility | ✓ Good — v2.6 avoids conflicts |
| Resize handle pattern | Absolute positioned div at column edge with cursor-col-resize | ✓ Good — v2.6 standard interaction |
| Composite unique constraint (sport_id, name, country) | Prevent cross-country tournament collisions | ✓ Good — v2.6 data integrity |
| Odds Comparison as default landing | Reflects primary user workflow of competitive analysis | ✓ Good — v2.6 intuitive navigation |
| Compact sidebar status widgets | Event count badge and health dots for at-a-glance monitoring | ✓ Good — v2.6 reduced visual noise |
| Sidebar query invalidation on scrape | Invalidate coverage and scrape-runs queries for instant refresh | ✓ Good — v2.6 real-time updates |
| Three-section sidebar layout | Analysis/Status/Utilities for logical grouping | ✓ Good — v2.6 clear navigation |
| UnavailableMarketUpdate pattern | Separate INSERT (new markets) from UPDATE (unavailable existing) | ✓ Good — v2.7 correct DB operations |
| Dual-path availability persistence | Both async (WriteBatch) and sync (direct query) handle unavailability | ✓ Good — v2.7 complete coverage |
| Reconciliation for dropped events | Post-cycle pass marks events not in discovery as unavailable | ✓ Good — v2.7 catches platform removal |
| Cache update after DB update | Update cache immediately after DB for instant API effect | ✓ Good — v2.7 consistent state |
| Latest snapshot for alerts filter | Query only latest snapshot per event, not historical | ✓ Good — v2.7 accurate filtering |
| raw_response columns unused | Remove unused data columns to reclaim 33 GB | ✓ Good — v2.8 81% DB reduction |
| VACUUM FULL after column drop | Required to actually reclaim disk space | ✓ Good — v2.8 freed 35 GB |
| Combined optimization strategy | raw_response removal + 7-day retention = maximum impact | ✓ Good — v2.8 exceeded 78% target |
| Market-level upsert schema | Replace snapshot-level with market-level change detection | ✓ Good — v2.9 95% row reduction |
| COALESCE in unique constraint | Allow NULL line values in uniqueness check | ✓ Good — v2.9 handles all markets |
| Composite PK for partitioned tables | PostgreSQL requires partition key in primary key | ✓ Good — v2.9 correct schema |
| Expression index ON CONFLICT raw SQL | SQLAlchemy doesn't support expression index constraints | ✓ Good — v2.9 works with COALESCE |
| Dual-query history API | Query both new and legacy tables for complete data | ✓ Good — v2.9 no data migration needed |

---
*Last updated: 2026-02-24 after v2.9 milestone*
