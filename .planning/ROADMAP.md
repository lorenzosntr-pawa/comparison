# Roadmap: Betpawa Odds Comparison Tool

## Overview

Build a comparative analysis tool that scrapes odds from SportyBet, BetPawa, and Bet9ja, matches events across platforms using SportRadar IDs, stores timestamped snapshots in PostgreSQL, and displays side-by-side comparisons with margin analysis through a React web interface with real-time WebSocket updates.

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
- [ ] **Phase 7: Match Views** - Match list and detail views with odds comparison
- [ ] **Phase 8: Real-time Updates** - WebSocket integration for live data push

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

### Phase 7: Match Views
**Goal**: Implement match list view (1X2, O/U 2.5, BTTS) and match detail view with all markets, margins, and color-coded indicators
**Depends on**: Phase 6 (needs React app foundation)
**Research**: Unlikely (internal UI using established patterns)
**Plans**: TBD

### Phase 8: Real-time Updates
**Goal**: Implement WebSocket connection for real-time odds updates and stale data indicators
**Depends on**: Phase 7 (needs UI to receive updates)
**Research**: Likely (WebSocket patterns)
**Research topics**: FastAPI WebSocket patterns, TanStack Query WebSocket integration, reconnection handling
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Market Mapping Port | 6/6 | Complete | 2026-01-20 |
| 2. Database Schema | 3/3 | Complete | 2026-01-20 |
| 3. Scraper Integration | 6/6 | Complete | 2026-01-20 |
| 4. Event Matching Service | 2/2 | Complete | 2026-01-20 |
| 5. Scheduled Scraping | 2/2 | Complete | 2026-01-20 |
| 6. React Foundation | 4/4 | Complete | 2026-01-20 |
| 7. Match Views | 0/TBD | Not started | - |
| 8. Real-time Updates | 0/TBD | Not started | - |
