# Roadmap: Betpawa Odds Comparison Tool

## Overview

Build a comparative analysis tool that scrapes odds from SportyBet, BetPawa, and Bet9ja, matches events across platforms using SportRadar IDs, stores timestamped snapshots in PostgreSQL, and displays side-by-side comparisons with margin analysis through a React web interface.

## Milestones

- ✅ [v1.0 MVP](milestones/v1.0-ROADMAP.md) — Phases 1-12 (shipped 2026-01-23)
- ✅ [v1.1 Palimpsest Comparison](milestones/v1.1-ROADMAP.md) — Phases 13-19 (shipped 2026-01-24)
- ✅ [v1.2 Settings & Retention](milestones/v1.2-ROADMAP.md) — Phases 19.1-22 (shipped 2026-01-26)
- 🚧 **v1.3 Coverage Improvements** — Phases 23-27 (in progress)

## Current Milestone

### 🚧 v1.3 Coverage Improvements (In Progress)

**Milestone Goal:** Enhance Coverage Comparison page UX and bring key metrics to dashboard

#### Phase 23: Fix Match Rate Bug

**Goal**: Fix match rate calculation showing 8774% instead of ~87.7%
**Depends on**: Previous milestone complete
**Research**: Unlikely (bug fix)
**Plans**: 1

Plans:
- [x] 23-01: Fix match rate double multiplication

#### Phase 24: Country Filters UX

**Goal**: Make country filter list scrollable with type-to-filter and scroll-to-match highlighting
**Depends on**: Phase 23
**Research**: Unlikely (internal UI patterns)
**Plans**: TBD

Plans:
- [ ] 24-01: Searchable multi-select country filter

#### Phase 25: Include Started Toggle

**Goal**: Add toggle to exclude in-play/started events with filtered summary cards
**Depends on**: Phase 24
**Research**: Unlikely (internal patterns)
**Plans**: TBD

Plans:
- [ ] 25-01: TBD

#### Phase 26: Tournament Gaps Cards

**Goal**: Add summary cards showing tournament coverage gaps per competitor
**Depends on**: Phase 25
**Research**: Unlikely (internal patterns)
**Plans**: TBD

Plans:
- [ ] 26-01: TBD

#### Phase 27: Dashboard Coverage Widgets

**Goal**: Replace dashboard widgets with Total Events and Matched Events cards using live DB data
**Depends on**: Phase 26
**Research**: Unlikely (reusing existing components)
**Plans**: TBD

Plans:
- [ ] 27-01: TBD

## Completed Milestones

<details>
<summary>✅ v1.0 MVP (Phases 1-12) — SHIPPED 2026-01-23</summary>

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

<details>
<summary>✅ v1.1 Palimpsest Comparison (Phases 13-19) — SHIPPED 2026-01-24</summary>

- [x] Phase 13: Database Schema Extension (2/2 plans) — 2026-01-23
- [x] Phase 14: Tournament Discovery Scraping (1/1 plans) — 2026-01-23
- [x] Phase 15: Full Event Scraping (2/2 plans) — 2026-01-24
- [x] Phase 16: Cross-Platform Matching Enhancement (0/0 plans) — 2026-01-24
- [x] Phase 17: Palimpsest API Endpoints (2/2 plans) — 2026-01-24
- [x] Phase 18: Matches Page Filter + Metadata Priority (1/1 plans) — 2026-01-24
- [x] Phase 19: Palimpsest Comparison Page (3/3 plans) — 2026-01-24

</details>

<details>
<summary>✅ v1.2 Settings & Retention (Phases 19.1-22) — SHIPPED 2026-01-26</summary>

- [x] Phase 19.1: Fix Sidebar Menu (1/1 plans) — 2026-01-25
- [x] Phase 20: Settings Schema & API (1/1 plans) — 2026-01-25
- [x] Phase 21: Settings Persistence Integration (1/1 plans) — 2026-01-25
- [x] Phase 22: History Retention (5/5 plans) — 2026-01-26

</details>

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
| 14. Tournament Discovery Scraping | v1.1 | 1/1 | Complete | 2026-01-23 |
| 15. Full Event Scraping | v1.1 | 2/2 | Complete | 2026-01-24 |
| 16. Cross-Platform Matching Enhancement | v1.1 | 0/0 | Complete | 2026-01-24 |
| 17. Palimpsest API Endpoints | v1.1 | 2/2 | Complete | 2026-01-24 |
| 18. Matches Page Filter + Metadata Priority | v1.1 | 1/1 | Complete | 2026-01-24 |
| 19. Palimpsest Comparison Page | v1.1 | 3/3 | Complete | 2026-01-24 |
| 19.1 Fix Sidebar Menu (INSERTED) | v1.2 | 1/1 | Complete | 2026-01-25 |
| 20. Settings Schema & API | v1.2 | 1/1 | Complete | 2026-01-25 |
| 21. Settings Persistence Integration | v1.2 | 1/1 | Complete | 2026-01-25 |
| 22. History Retention | v1.2 | 5/5 | Complete | 2026-01-26 |
| 23. Fix Match Rate Bug | v1.3 | 1/1 | Complete | 2026-01-26 |
| 24. Country Filters UX | v1.3 | 0/1 | Not started | - |
| 25. Include Started Toggle | v1.3 | 0/? | Not started | - |
| 26. Tournament Gaps Cards | v1.3 | 0/? | Not started | - |
| 27. Dashboard Coverage Widgets | v1.3 | 0/? | Not started | - |
