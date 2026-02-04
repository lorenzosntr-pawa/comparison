# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-03)

**Core value:** Accurate cross-platform market matching and real-time odds comparison that enables Betpawa to understand its competitive position in the Nigerian market.
**Current focus:** Event Details UX improvements

## Current Position

Phase: 51 of 52 (Navigation UX)
Plan: 01-FIX complete
Status: Phase 51 complete (including FIX)
Last activity: 2026-02-04 — Phase 51-01-FIX complete

Progress: ████████░░ 80% (v1.9: 4/5 phases)

### Phase 51-01-FIX Results
- Fixed root cause: scroll listener targeting wrong element (outer SidebarInset instead of inner scrollable main)
- Added `data-scroll-container` attribute to correct main element for unique targeting
- Updated all querySelector('main') calls to use [data-scroll-container]
- Repositioned scroll-to-top button (bottom-20) to avoid API icon overlap
- All 5 UAT issues resolved (UAT-001 through UAT-005)

### Phase 51-01 Results
- Sticky navigation header that remains visible when scrolling markets
- Scroll-to-top floating button appears after scrolling 400px
- Fixed positioning with scroll container-aware bounds (not CSS sticky)
- Placeholder div pattern prevents layout shift when header becomes fixed

### Phase 50-01 Results
- Added MarketFilterBar component with search input and competitor dropdown
- Implemented fuzzy subsequence matching for market search
- Dynamic column reordering places selected competitor adjacent to Betpawa
- Search, competitor filter, and tab filtering work together

### Phase 49-01-FIX2 Results
- Fixed UAT-002: Markets now appear in ALL their category tabs (not just primary)
- Fixed UAT-003: Unknown market groups handled dynamically
- Changed `market_group` (string) to `market_groups` (JSON array)
- Frontend filtering uses array membership check

### Phase 49-01-FIX Results
- Fixed UAT-001: Missing market category tabs
- Updated TAB_ORDER to include all BetPawa groups: popular, combos, specials
- Replaced 'main' with 'popular' to match BetPawa's actual taxonomy
- All market categories now visible as tabs

### Phase 49-01 Results
- Added `market_group` column to MarketOdds and CompetitorMarketOdds
- Extract market group from BetPawa tabs array during scraping
- Created tabbed navigation component with pill-style buttons
- Filter markets by category (Popular, Goals, Handicaps, Combos, Halves, Corners, Cards, Specials, Other)
- Show market count badges in each tab
- Hide empty category tabs automatically

### Phase 48-01-FIX2 Results
- Applied market deduplication logic to summary-section.tsx
- Added `mergeMarketOutcomes()` helper (copied from market-grid.tsx)
- Added `buildDeduplicatedMarkets()` for consistent counting
- All summary cards now use deduplicated markets
- UAT-006 resolved

### Phase 48-01-FIX Results
- Fixed Betpawa market count to only count markets with actual odds
- Improved category breakdown text size and layout (2-column grid)
- Improved Mapping Quality card with badges for bookmaker counts
- Removed Key Markets card, changed to 3-column layout
- All 5 UAT issues resolved

### Phase 48-01 Results
- Added "Market Coverage" card with per-bookmaker market counts and visual bars
- Added "Mapping Quality" card showing matched competitor markets
- Enhanced "Competitive Position" with category breakdown (Main/Goals/Handicaps/Other)
- Fixed pre-existing TypeScript build error in recent-runs.tsx (connection_failed status cast)

### Phase 47-01 Results
- Fixed BUG-004: combo markets (1X2OU, DCOU, etc.) now display outcomes correctly
- `getUnifiedOutcomes()` now checks `outcomes.length > 0` before using reference bookmaker
- Margin only displays when `outcomeNames.length > 0`
- Added `normalizeOutcomeName()` to handle cross-bookmaker outcome name differences (Betpawa "1X - Under" ↔ SportyBet/Bet9ja "1X & Under")

### Phase 46-01 Results
- Handicap markets (3-Way and Asian) now display competitor odds correctly
- Fixed `line` field population from `handicap_home` in event_coordinator.py
- Markets fixed: 4724, 4716, 4720 (3-Way), 3774, 3747, 3756 (Asian)

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

## Performance Metrics

**Velocity:**
- Total plans completed: 116 (91 original + 12 FIX plans + 9 v1.8 plans + 4 additional)
- Average duration: 6 min
- Total execution time: ~10 hours

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
- SportyBet 47.3%→52.2%, Bet9ja 36.1%→40.5% mapping success
- +13,290 / -57 lines (net +13,233)
- ~30,647 total LOC

## Accumulated Context

### Key Patterns (v1.0 + v1.1 + v1.2 + v1.3 + v1.4 + v1.5 + v1.6 + v1.7 + v1.8)

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
- **Factory method for configurable initialization** - EventCoordinator.from_settings() creates instances with tuning from Settings (v1.7)
- **Event-centric parallel scraping** - scrape all platforms simultaneously per event, not sequentially by platform (v1.7)
- **Dict-based SSE progress events** - EventCoordinator yields dict events, mapped to ScrapeProgress for broadcaster (v1.7)
- **Single-flush batch insert pattern** - add all records, single flush to get IDs, link FKs, commit (v1.7 FIX)
- **BetPawa SPORTRADAR widget.id** - SR ID is in widget["id"], an 8-digit numeric string (v1.7 FIX3)
- **Competitor tournament from raw data** - Extract tournament name and country from competitor raw responses via `_get_or_create_competitor_tournament_from_raw()` (v1.7 FIX4)
- **Bookmaker auto-creation** - `_get_bookmaker_ids()` creates missing bookmakers on first run (v1.7 FIX5)
- **Competitor tournament field mapping** - SportyBet: `sport.category.tournament.name` + `sport.category.name`; Bet9ja: `GN` + `SG` (v1.7 FIX5)
- **betpawa_event_id linking** - Look up BetPawa Event by SR ID when creating CompetitorEvent (v1.7 FIX6)
- **Competitor odds API loading** - `_load_competitor_snapshots_for_events()` loads from CompetitorOddsSnapshot table (v1.7 FIX7)
- **EventBookmaker reconciliation** - Post-batch pass creates EventBookmaker links for competitors with matching BetPawa events (v1.7 FIX8)
- **Merge split market outcomes** - Frontend merges outcomes when same market appears multiple times (different outcome subsets) (v1.8 FIX)
- **Combined market splitting** - Bet9ja HAOU splits into separate Home O/U (5006) and Away O/U (5003) markets (v1.8 FIX)
- **Iterate deduplicated maps** - UI buildUnifiedMarkets must iterate bookmakerMaps (deduplicated) not raw API data (v1.8 FIX2)
- **Combo market O/U routing** - Markets like 1X2OU, DCOU must be in BET9JA_OVER_UNDER_KEYS and OVER_UNDER_MARKET_IDS to use O/U handler with line parameter (v1.8 44-03)
- **Handicap line field fallback** - Competitor handicap markets use `line = mapped.line ?? mapped.handicap.home` for frontend matching (v1.8 46-01)
- **Outcome presence check for fallback** - `getUnifiedOutcomes()` must check `outcomes.length > 0`, not just market existence (v1.8 47-01)
- **Outcome name normalization** - `normalizeOutcomeName()` converts " - " to " & " for cross-bookmaker matching (Betpawa uses dash, others use ampersand) (v1.8 47-01)
- **Market group extraction from tabs** - BetPawa tabs array contains market categories; extract first non-"all" tab as market_group (v1.9 49-01)
- **Tabbed filtering with useMemo** - React useMemo for filtered markets and available groups to avoid unnecessary recalculation (v1.9 49-01)
- **Multi-group array storage** - Store all non-"all" tabs as JSON array so markets appear in multiple category tabs (v1.9 49-01-FIX2)
- **Dynamic unknown group handling** - Unknown groups inserted alphabetically before 'other' in tab order (v1.9 49-01-FIX2)
- **Fuzzy subsequence matching** - Query chars must appear in target in order for intuitive partial matching (e.g., "o25" matches "Over 2.5 Goals") (v1.9 50-01)
- **Dynamic column reordering** - Selected competitor moves adjacent to Betpawa (always first), others follow (v1.9 50-01)
- **Scroll container-aware fixed positioning** - Listen to main element scroll (not window), use fixed positioning with dynamic bounds when CSS sticky doesn't work with overflow containers (v1.9 51-01)
- **Placeholder div for fixed headers** - Reserve space with placeholder when header becomes fixed to prevent layout shift (v1.9 51-01)
- **data-scroll-container attribute** - Use this data attribute to target the app's scrollable container from any component, avoiding ambiguity with nested main elements (v1.9 51-01-FIX)

### Key Decisions

- Metadata priority: sportybet > bet9ja (v1.1)
- SportRadar ID as primary cross-platform matching key
- Store competitor data independently, match at query time
- Negative IDs distinguish competitor-only events from BetPawa events
- Default 7-day retention, 1-90 day range (v1.2)
- Daily cleanup at 2 AM UTC (v1.2)
- Empty selection = all countries (v1.3)
- Default includeStarted OFF for pre-match focus (v1.3)
- Reuse useCoverage hook across dashboard and coverage features (v1.3)
- 2-min watchdog interval for stale detection (v1.5)
- Auto-rescrape on connection recovery (v1.5)
- Event matching is 99.9% accurate (v1.6 audit) — 23-26% unmatched are competitor-only events
- Only 2 events affected by timing edge case, fixable with 1 SQL query (v1.6 audit)
- API-001: Coverage count must use DISTINCT sportradar_id (v1.6 audit 34.1)
- API-002: Event detail uses legacy odds tables, missing ~50% competitor data (v1.6 audit 34.1)
- Frontend has no bugs — UI correctly displays what API provides (v1.6 audit 34.1)

### Blockers/Concerns

None.

### Roadmap Evolution

- v1.0 MVP shipped 2026-01-23 with 15 phases
- v1.1 Palimpsest Comparison shipped 2026-01-24 with 7 phases
- v1.2 Settings & Retention shipped 2026-01-26 with 4 phases
- v1.3 Coverage Improvements shipped 2026-01-26 with 5 phases
- v1.4 Odds Comparison UX shipped 2026-01-26 with 3 phases
- v1.5 Scraping Observability shipped 2026-01-28 with 4 phases
- v1.6 Event Matching Accuracy shipped 2026-01-29 with 3 phases
- All milestones archived to .planning/milestones/
- v1.7 Scraping Architecture Overhaul shipped 2026-02-02 with 7 phases + 9 FIX plans
- All milestones archived to .planning/milestones/
- v1.8 Market Matching Accuracy shipped 2026-02-03 with 5 phases (audit-driven approach)
- All milestones archived to .planning/milestones/
- Milestone v1.9 Event Details UX created: event details page improvements, 5 phases (Phase 48-52)

## Session Continuity

Last session: 2026-02-04
Stopped at: Phase 51-01-FIX complete
Resume file: None
Next action: Plan Phase 52 (Polish & Integration)
