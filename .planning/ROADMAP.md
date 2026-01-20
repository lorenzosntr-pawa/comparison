# Roadmap: Betpawa Odds Comparison Tool

## Overview

Build a comparative analysis tool that scrapes odds from SportyBet, BetPawa, and Bet9ja, matches events across platforms using SportRadar IDs, stores timestamped snapshots in PostgreSQL, and displays side-by-side comparisons with margin analysis through a React web interface with real-time WebSocket updates.

## Domain Expertise

None

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [ ] **Phase 1: Market Mapping Port** - Port TypeScript mapping library to Python
- [ ] **Phase 2: Database Schema** - PostgreSQL schema for odds snapshots and events
- [ ] **Phase 3: Scraper Integration** - Integrate existing scrapers with FastAPI orchestration
- [ ] **Phase 4: Event Matching Service** - Cross-platform event matching via SportRadar IDs
- [ ] **Phase 5: Scheduled Scraping** - Background scheduler with configurable intervals
- [ ] **Phase 6: React Foundation** - React app with TanStack Query and Tailwind setup
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
- Plan 03: Sportybet mapper (TBD)
- Plan 04: Bet9ja mapper (TBD)
- Plan 05: TBD
- Plan 06: TBD

### Phase 2: Database Schema
**Goal**: Design and implement PostgreSQL schema for events, odds snapshots, and cross-platform matching
**Depends on**: Phase 1 (needs market types defined)
**Research**: Unlikely (standard PostgreSQL schema design)
**Plans**: TBD

### Phase 3: Scraper Integration
**Goal**: Integrate existing Python scrapers into FastAPI service with unified data models
**Depends on**: Phase 2 (needs database to store results)
**Research**: Unlikely (integrating existing Python scrapers)
**Plans**: TBD

### Phase 4: Event Matching Service
**Goal**: Implement cross-platform event matching using SportRadar IDs from all three bookmakers
**Depends on**: Phase 3 (needs scraped data available)
**Research**: Unlikely (logic already defined in brief)
**Plans**: TBD

### Phase 5: Scheduled Scraping
**Goal**: Implement background scheduler for periodic scraping with configurable intervals and failure handling
**Depends on**: Phase 4 (needs full scraping pipeline working)
**Research**: Likely (scheduler library choice)
**Research topics**: APScheduler vs Celery vs native asyncio for FastAPI, retry patterns, stale data handling
**Plans**: TBD

### Phase 6: React Foundation
**Goal**: Set up React application with TanStack Query, Tailwind CSS, and basic layout structure
**Depends on**: Phase 3 (needs API endpoints to connect to)
**Research**: Unlikely (standard React + TanStack Query + Tailwind setup)
**Plans**: TBD

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
| 1. Market Mapping Port | 2/6 | In progress | - |
| 2. Database Schema | 0/TBD | Not started | - |
| 3. Scraper Integration | 0/TBD | Not started | - |
| 4. Event Matching Service | 0/TBD | Not started | - |
| 5. Scheduled Scraping | 0/TBD | Not started | - |
| 6. React Foundation | 0/TBD | Not started | - |
| 7. Match Views | 0/TBD | Not started | - |
| 8. Real-time Updates | 0/TBD | Not started | - |
