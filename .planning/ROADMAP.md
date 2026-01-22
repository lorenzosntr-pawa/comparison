# Roadmap: Betpawa Odds Comparison Tool

## Overview

Build a comparative analysis tool that scrapes odds from SportyBet, BetPawa, and Bet9ja, matches events across platforms using SportRadar IDs, stores timestamped snapshots in PostgreSQL, and displays side-by-side comparisons with margin analysis through a React web interface.

## Domain Expertise

None

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Market Mapping Port** - Port TypeScript mapping library to Python
- [x] **Phase 2: Database Schema** - PostgreSQL schema for odds snapshots and events
- [x] **Phase 3: Scraper Integration** - Integrate existing scrapers with FastAPI orchestration
- [x] **Phase 4: Event Matching Service** - Cross-platform event matching via SportRadar IDs
- [x] **Phase 5: Scheduled Scraping** - Background scheduler with configurable intervals
- [x] **Phase 6: React Foundation** - React app with TanStack Query and Tailwind setup
- [x] **Phase 6.1: Cross-Platform Scraping** - Complete SportyBet/Bet9ja scraping via SportRadar IDs (INSERTED)
- [x] **Phase 7: Match Views** - Match list and detail views with odds comparison
- [x] **Phase 7.1: Complete Odds Pipeline** - Add BetPawa odds storage and fix UI display (INSERTED)
- [x] **Phase 7.2: Scraping Performance** - Improve scraping speed and logging (INSERTED)
- [x] **Phase 8: Scrape Runs UI Improvements** - Improve scrape runs page and widget
- [ ] **Phase 9: Market Mapping Expansion** - Expand market mappings for better cross-platform coverage
- [x] **Phase 10: Matches Page Improvements** - Fix filters, add region/league display, add search
- [x] **Phase 11: Settings Page** - Build functional settings page for tool configuration
- [ ] **Phase 12: UI Polish** - Fix sidebar, widgets, and general UI issues
- [ ] **Phase 13: Competitor Event Import** - Import SportyBet/Bet9ja events not in BetPawa for coverage comparison
- [x] **Phase 14: Scraping Logging & Workflow** - Restructure backend scraping with proper logging and state tracking

## Phase Details

### Phase 1: Market Mapping Port
**Goal**: Port the 111+ market mappings from TypeScript to Python with equivalent type safety and Result patterns
**Depends on**: Nothing (first phase)
**Research**: Unlikely (internal port of existing TypeScript code)
**Plans**:
- Plan 01: Type definitions (COMPLETE - 01-01-SUMMARY.md)
- Plan 02: Market mappings registry (COMPLETE - 01-02-SUMMARY.md)
- Plan 03: Parser utilities (COMPLETE - 01-03-SUMMARY.md)
- Plan 04: Sportybet mapper (COMPLETE - 01-04-SUMMARY.md)
- Plan 05: Bet9ja mapper (COMPLETE - 01-05-SUMMARY.md)
- Plan 06: Unified API & Tests (COMPLETE - 01-06-SUMMARY.md)

### Phase 2: Database Schema
**Goal**: Design and implement PostgreSQL schema for events, odds snapshots, and cross-platform matching
**Depends on**: Phase 1 (needs market types defined)
**Research**: Complete (02-RESEARCH.md)
**Plans**:
- Plan 01: Database foundation (COMPLETE - 02-01-SUMMARY.md)
- Plan 02: Odds snapshot models (COMPLETE - 02-02-SUMMARY.md)
- Plan 03: Alembic migrations setup (COMPLETE - 02-03-SUMMARY.md)

### Phase 3: Scraper Integration
**Goal**: Integrate existing Python scrapers into FastAPI service with unified data models
**Depends on**: Phase 2 (needs database to store results)
**Research**: Complete (03-RESEARCH.md)
**Plans**:
- Plan 01: FastAPI Foundation (COMPLETE - 03-01-SUMMARY.md)
- Plan 02: Async scraper clients (COMPLETE - 03-02-SUMMARY.md)
- Plan 03: Bet9ja client & orchestrator (COMPLETE - 03-03-SUMMARY.md)
- Plan 04: Scrape endpoint (COMPLETE - 03-04-SUMMARY.md)
- Plan 05: Health & filtering (COMPLETE - 03-05-SUMMARY.md)
- Plan 06: Persistence layer (COMPLETE - 03-06-SUMMARY.md)

### Phase 4: Event Matching Service
**Goal**: Implement cross-platform event matching using SportRadar IDs from all three bookmakers
**Depends on**: Phase 3 (needs scraped data available)
**Research**: Complete (04-RESEARCH.md)
**Plans**:
- Plan 01: Event matching service (COMPLETE - 04-01-SUMMARY.md)
- Plan 02: Events API endpoints (COMPLETE - 04-02-SUMMARY.md)

### Phase 5: Scheduled Scraping
**Goal**: Implement background scheduler for periodic scraping with configurable intervals and failure handling
**Depends on**: Phase 4 (needs full scraping pipeline working)
**Research**: Complete (05-RESEARCH.md)
**Plans**:
- Plan 01: Scheduler infrastructure (COMPLETE - 05-01-SUMMARY.md)
- Plan 02: Scheduler status & control (COMPLETE - 05-02-SUMMARY.md)

### Phase 6: React Foundation
**Goal**: Set up React application with TanStack Query, Tailwind CSS, and basic layout structure
**Depends on**: Phase 3 (needs API endpoints to connect to)
**Research**: Complete (06-RESEARCH.md)
**Plans**:
- Plan 01: Project Setup (COMPLETE - 06-01-SUMMARY.md)
- Plan 02: UI Foundation (COMPLETE - 06-02-SUMMARY.md)
- Plan 03: Layout & Routing (COMPLETE - 06-03-SUMMARY.md)
- Plan 04: API Integration & Dashboard (COMPLETE - 06-04-SUMMARY.md)

### Phase 6.1: Cross-Platform Scraping (INSERTED)
**Goal**: Complete SportyBet and Bet9ja scraping using SportRadar IDs from BetPawa base events
**Depends on**: Phase 6 (needs events in database from BetPawa scraping)
**Research**: None (clients already built, just need orchestrator integration)
**Plans**:
- Plan 01: Cross-platform scraping (COMPLETE - 06.1-01-SUMMARY.md)

**Details:**
- SportyBet: Use `fetch_event(sportradar_id)` for each BetPawa event's SportRadar ID
- Bet9ja: Extract SportRadar ID from `EXTID` field, match to existing events
- All three platforms use SportRadar IDs for cross-platform matching

### Phase 7: Match Views
**Goal**: Implement match list view (1X2, O/U 2.5, BTTS) and match detail view with all markets, margins, and color-coded indicators
**Depends on**: Phase 6.1 (needs cross-platform data for comparison)
**Research**: Unlikely (internal UI using established patterns)
**Plans**:
- Plan 01: Events API Odds Enhancement (COMPLETE - 07-01-SUMMARY.md)
- Plan 02: Match List View Component (COMPLETE - 07-02-SUMMARY.md)
- Plan 03: Match Detail View Component (COMPLETE - 07-03-SUMMARY.md)

### Phase 7.1: Complete Odds Pipeline (INSERTED)
**Goal**: Fix BetPawa odds storage, ensure all markets are mapped, and fix UI to display odds correctly
**Depends on**: Phase 7 (needs match views structure in place)
**Research**: Complete (07.1-RESEARCH.md)
**Plans**:
- Plan 01: Complete Odds Pipeline (COMPLETE - 07.1-01-SUMMARY.md)

**Details:**
- BetPawa odds now stored in OddsSnapshot/MarketOdds tables
- BetPawa is canonical format — direct extraction, no mapping needed
- All three bookmakers display side-by-side with color coding

### Phase 7.2: Scraping Performance (INSERTED)
**Goal**: Improve scraping speed (currently ~5min) and enhance terminal logging quality
**Depends on**: Phase 7.1 (needs complete odds pipeline working)
**Research**: Complete (07.2-RESEARCH.md)
**Plans**:
- Plan 01: Backend Performance & Timing (COMPLETE - 07.2-01-SUMMARY.md)
- Plan 02: SSE Progress Streaming (COMPLETE - 07.2-02-SUMMARY.md)
- Plan 03: Frontend Scrape Runs UI (COMPLETE - 07.2-03-SUMMARY.md)

**Details:**
- Bet9ja scraping parallelized with asyncio.gather + Semaphore(10)
- Per-platform timing metrics stored in ScrapeRun.platform_timings
- Bet9ja scrape time reduced from ~60s to ~7.5s
- SSE streaming endpoint for real-time scrape progress
- Complete scrape runs UI with history page and detail view

### Phase 8: Scrape Runs UI Improvements
**Goal**: Improve scrape runs page and dashboard widget with enhanced UX and additional features
**Depends on**: Phase 7.2 (needs scrape runs UI foundation)
**Research**: None (internal UI, uses existing SSE infrastructure)
**Plans**:
- Plan 01: Live Progress Visualization (COMPLETE - 08-01-SUMMARY.md)
- Plan 02: Historical Analytics (COMPLETE - 08-02-SUMMARY.md)
- Plan 03: Platform-Specific Retry (COMPLETE - 08-03-SUMMARY.md)

**Details:**
- Per-platform progress bars on detail page during active scrapes
- Overall progress indicator on dashboard widget
- Analytics charts: duration trends, success rates, event volume
- Platform-specific retry for failed scrapes (not whole-run retry)
- POST /api/scrape/{run_id}/retry with platform selection

### Phase 9: Market Mapping Expansion
**Goal**: Expand market mappings to correctly match more markets between SportyBet/Bet9ja and BetPawa by analyzing DB data and improving existing mappings
**Depends on**: Phase 1 (extends market mapping port)
**Research**: Required (analyze DB to identify unmapped markets and mapping gaps)
**Plans**: TBD

**Details:**
- Review scraped data in database to identify unmapped markets
- Analyze current mapping coverage gaps between platforms
- Add new market mappings for commonly-missed markets
- Improve existing mappings where matches are incorrect

### Phase 10: Matches Page Improvements
**Goal**: Improve matches page UX with working filters, region/league display, and match search
**Depends on**: Phase 7 (extends match views)
**Research**: Unlikely (internal UI improvements)
**Plans**:
- Plan 01: Search and Region Column (COMPLETE - 10-01-SUMMARY.md)
- Plan 02: Enhanced Match Filters (COMPLETE - 10-02-SUMMARY.md)

**Details:**
- Fix all filters on top of matches page (especially date filters)
- Add region column to each match for easier filtering
- Add league/competition display for each match
- Add search functionality to find specific matches by team name

### Phase 11: Settings Page
**Goal**: Build functional settings page for tool configuration and preferences
**Depends on**: Phase 6 (extends React foundation)
**Research**: Unlikely (internal UI development)
**Plans**:
- Plan 01: Settings Backend (COMPLETE - 11-01-SUMMARY.md)
- Plan 02: Settings UI (COMPLETE - 11-02-SUMMARY.md)

**Details:**
- Settings page currently exists but is empty
- Add configuration options for the comparison tool
- Persist settings (localStorage or database)
- Potential settings: scraping intervals, display preferences, notification thresholds, etc.

### Phase 12: UI Polish
**Goal**: Fix general UI issues, ensure all widgets work correctly, fix sidebar behavior
**Depends on**: Phase 6 (extends React foundation)
**Research**: Unlikely (bug fixes and UI improvements)
**Plans**: TBD

**Details:**
- Fix sidebar collapse behavior (currently covers part of page content)
- Verify all dashboard widgets work correctly
- General UI consistency and polish pass
- Fix any layout/spacing issues across pages

### Phase 13: Competitor Event Import
**Goal**: Import events from SportyBet/Bet9ja that don't exist in BetPawa, enabling full market coverage comparison
**Depends on**: Phase 6.1 (extends cross-platform scraping)
**Research**: Required (understand SportyBet full event listing API, Bet9ja event discovery)
**Plans**: TBD

**Details:**
- Fetch all events from SportyBet (not just by SportRadar ID lookup)
- Import Bet9ja events via SportyBet SportRadar ID matching
- Store competitor-only events with metadata from the competitor source (tournament, region)
- Enable comparison of event coverage between BetPawa and competitors
- Execution order: BetPawa scrape first, then competitor-only event discovery

### Phase 14: Scraping Logging & Workflow
**Goal**: Restructure backend scraping workflow with proper logging, state tracking, and UI display for each bookmaker phase
**Depends on**: Phase 8 (fixes scrape runs UI issues)
**Research**: Complete (14-RESEARCH.md)
**Plans**:
- Plan 01: Scraping Infrastructure (COMPLETE - 14-01-SUMMARY.md)
- Plan 02: Orchestrator Logging Integration (COMPLETE - 14-02-SUMMARY.md)
- Plan 03: Dashboard Redesign (COMPLETE - 14-03-SUMMARY.md)
- Plan 04: Frontend Phase Display (COMPLETE - 14-04-SUMMARY.md)

**Details:**
- Backend scraping workflow restructure for better state management
- Per-bookmaker phase logging (BetPawa first, then competitors)
- Fix bugs in scrape runs UI that stem from backend structure issues
- Structured logging for scraping state transitions
- Clear workflow: BetPawa → SportyBet → Bet9ja with status per phase
- Improve error handling and reporting per platform

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Market Mapping Port | 6/6 | Complete | 2026-01-20 |
| 2. Database Schema | 3/3 | Complete | 2026-01-20 |
| 3. Scraper Integration | 6/6 | Complete | 2026-01-20 |
| 4. Event Matching Service | 2/2 | Complete | 2026-01-20 |
| 5. Scheduled Scraping | 2/2 | Complete | 2026-01-20 |
| 6. React Foundation | 4/4 | Complete | 2026-01-20 |
| 6.1 Cross-Platform Scraping | 1/1 | Complete | 2026-01-21 |
| 7. Match Views | 3/3 | Complete | 2026-01-21 |
| 7.1 Complete Odds Pipeline | 1/1 | Complete | 2026-01-21 |
| 7.2 Scraping Performance | 3/3 | Complete | 2026-01-21 |
| 8. Scrape Runs UI Improvements | 3/3 | Complete | 2026-01-21 |
| 9. Market Mapping Expansion | 0/TBD | Not started | - |
| 10. Matches Page Improvements | 2/2 | Complete | 2026-01-21 |
| 11. Settings Page | 2/2 | Complete | 2026-01-22 |
| 12. UI Polish | 0/TBD | Not started | - |
| 13. Competitor Event Import | 0/TBD | Not started | - |
| 14. Scraping Logging & Workflow | 4/4 | Complete | 2026-01-22 |
