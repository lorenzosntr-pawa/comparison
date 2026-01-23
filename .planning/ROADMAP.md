# Roadmap: Betpawa Odds Comparison Tool

## Overview

Build a comparative analysis tool that scrapes odds from SportyBet, BetPawa, and Bet9ja, matches events across platforms using SportRadar IDs, stores timestamped snapshots in PostgreSQL, and displays side-by-side comparisons with margin analysis through a React web interface.

## Milestones

- ✅ [v1.0 MVP](milestones/v1.0-ROADMAP.md) — Phases 1-12 (shipped 2026-01-23)
- 🚧 **v1.1 Palimpsest Comparison** — Phases 13-20 (in progress)

## Completed Milestones

<details>
<summary>v1.0 MVP (Phases 1-12) — SHIPPED 2026-01-23</summary>

- [x] Phase 1: Market Mapping Port (6/6 plans) — 2026-01-20
- [x] Phase 2: Database Schema (3/3 plans) — 2026-01-20
- [x] Phase 3: Scraper Integration (6/6 plans) — 2026-01-20
- [x] Phase 4: Event Matching Service (2/2 plans) — 2026-01-20
- [x] Phase 5: Scheduled Scraping (2/2 plans) — 2026-01-20
- [x] Phase 6: React Foundation (4/4 plans) — 2026-01-20
- [x] Phase 6.1: Cross-Platform Scraping (1/1 plans) — 2026-01-21
- [x] Phase 7: Match Views (3/3 plans) — 2026-01-21
- [x] Phase 7.1: Complete Odds Pipeline (1/1 plans) — 2026-01-21
- [x] Phase 7.2: Scraping Performance (3/3 plans) — 2026-01-21
- [x] Phase 8: Scrape Runs UI Improvements (3/3 plans) — 2026-01-21
- [x] Phase 9: Matches Page Improvements (2/2 plans) — 2026-01-21
- [x] Phase 10: Settings Page (2/2 plans) — 2026-01-22
- [x] Phase 11: UI Polish (3/3 plans) — 2026-01-22
- [x] Phase 12: Scraping Logging & Workflow (4/4 plans) — 2026-01-22

</details>

### 🚧 v1.1 Palimpsest Comparison (In Progress)

**Milestone Goal:** Enable full competitor palimpsest comparison by scraping all tournaments/events from competitors, matching across platforms by SportRadar ID, and displaying availability differences alongside odds comparison.

#### Phase 13: Database Schema Extension

**Goal**: Add tables for competitor tournaments/events with source tracking and metadata priority
**Depends on**: v1.0 MVP complete
**Research**: Unlikely (extending existing schema patterns)
**Plans**: 2

Plans:
- [x] 13-01: Competitor Models (CompetitorSource, CompetitorTournament, CompetitorEvent, odds snapshots)
- [x] 13-02: Migration (ScrapeBatch model, Alembic migration for all tables)

#### Phase 14: Tournament Discovery Scraping

**Goal**: Scrape full tournament lists from SportyBet and Bet9ja APIs
**Depends on**: Phase 13
**Research**: Likely (need to explore competitor API structures for tournament listing)
**Research topics**: SportyBet/Bet9ja tournament listing endpoints, pagination, data structures
**Plans**: TBD

Plans:
- [ ] 14-01: TBD

#### Phase 15: Full Event Scraping

**Goal**: Get all events from competitor tournaments, not limited to betpawa-matched events
**Depends on**: Phase 14
**Research**: Unlikely (extending existing scraping patterns)
**Plans**: TBD

Plans:
- [ ] 15-01: TBD

#### Phase 16: Cross-Platform Matching Enhancement

**Goal**: Match events by SR ID across all three platforms with priority chain (betpawa > sportybet > bet9ja)
**Depends on**: Phase 15
**Research**: Unlikely (extending existing matching logic)
**Plans**: TBD

Plans:
- [ ] 16-01: TBD

#### Phase 17: Metadata Priority System

**Goal**: Implement display logic to show metadata from best available source
**Depends on**: Phase 16
**Research**: Unlikely (internal business logic)
**Plans**: TBD

Plans:
- [ ] 17-01: TBD

#### Phase 18: Palimpsest API Endpoints

**Goal**: Create new API endpoints for tournament/event availability comparison data
**Depends on**: Phase 17
**Research**: Unlikely (following existing API patterns)
**Plans**: TBD

Plans:
- [ ] 18-01: TBD

#### Phase 19: Matches Page Filter

**Goal**: Add "Competitor Only" filter to existing odds comparison page
**Depends on**: Phase 18
**Research**: Unlikely (UI work with existing patterns)
**Plans**: TBD

Plans:
- [ ] 19-01: TBD

#### Phase 20: Palimpsest Comparison Page

**Goal**: New page showing tournament and event coverage comparison across platforms
**Depends on**: Phase 19
**Research**: Unlikely (following existing React patterns)
**Plans**: TBD

Plans:
- [ ] 20-01: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Market Mapping Port | v1.0 | 6/6 | Complete | 2026-01-20 |
| 2. Database Schema | v1.0 | 3/3 | Complete | 2026-01-20 |
| 3. Scraper Integration | v1.0 | 6/6 | Complete | 2026-01-20 |
| 4. Event Matching Service | v1.0 | 2/2 | Complete | 2026-01-20 |
| 5. Scheduled Scraping | v1.0 | 2/2 | Complete | 2026-01-20 |
| 6. React Foundation | v1.0 | 4/4 | Complete | 2026-01-20 |
| 6.1 Cross-Platform Scraping | v1.0 | 1/1 | Complete | 2026-01-21 |
| 7. Match Views | v1.0 | 3/3 | Complete | 2026-01-21 |
| 7.1 Complete Odds Pipeline | v1.0 | 1/1 | Complete | 2026-01-21 |
| 7.2 Scraping Performance | v1.0 | 3/3 | Complete | 2026-01-21 |
| 8. Scrape Runs UI Improvements | v1.0 | 3/3 | Complete | 2026-01-21 |
| 9. Matches Page Improvements | v1.0 | 2/2 | Complete | 2026-01-21 |
| 10. Settings Page | v1.0 | 2/2 | Complete | 2026-01-22 |
| 11. UI Polish | v1.0 | 3/3 | Complete | 2026-01-22 |
| 12. Scraping Logging & Workflow | v1.0 | 4/4 | Complete | 2026-01-22 |
| 13. Database Schema Extension | v1.1 | 2/2 | Complete | 2026-01-23 |
| 14. Tournament Discovery Scraping | v1.1 | 0/? | Not started | - |
| 15. Full Event Scraping | v1.1 | 0/? | Not started | - |
| 16. Cross-Platform Matching Enhancement | v1.1 | 0/? | Not started | - |
| 17. Metadata Priority System | v1.1 | 0/? | Not started | - |
| 18. Palimpsest API Endpoints | v1.1 | 0/? | Not started | - |
| 19. Matches Page Filter | v1.1 | 0/? | Not started | - |
| 20. Palimpsest Comparison Page | v1.1 | 0/? | Not started | - |
