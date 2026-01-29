# Roadmap: Betpawa Odds Comparison Tool

## Overview

Build a comparative analysis tool that scrapes odds from SportyBet, BetPawa, and Bet9ja, matches events across platforms using SportRadar IDs, stores timestamped snapshots in PostgreSQL, and displays side-by-side comparisons with margin analysis through a React web interface.

## Milestones

- ✅ [v1.0 MVP](milestones/v1.0-ROADMAP.md) — Phases 1-12 (shipped 2026-01-23)
- ✅ [v1.1 Palimpsest Comparison](milestones/v1.1-ROADMAP.md) — Phases 13-19 (shipped 2026-01-24)
- ✅ [v1.2 Settings & Retention](milestones/v1.2-ROADMAP.md) — Phases 19.1-22 (shipped 2026-01-26)
- ✅ [v1.3 Coverage Improvements](milestones/v1.3-ROADMAP.md) — Phases 23-27 (shipped 2026-01-26)
- ✅ [v1.4 Odds Comparison UX](milestones/v1.4-ROADMAP.md) — Phases 28-30 (shipped 2026-01-26)
- ✅ [v1.5 Scraping Observability](milestones/v1.5-ROADMAP.md) — Phases 31-33.1 (shipped 2026-01-28)
- ✅ [v1.6 Event Matching Accuracy](milestones/v1.6-ROADMAP.md) — Phases 34-35 (shipped 2026-01-29)
- 🚧 **v1.7 Scraping Architecture Overhaul** — Phases 36-42 (in progress)

### 🚧 v1.7 Scraping Architecture Overhaul (In Progress)

**Milestone Goal:** Redesign scraping to capture odds simultaneously across all bookmakers for reliable trader comparison

#### Phase 36: Investigation & Architecture Design ✓

**Goal**: Profile current bottlenecks, design new coordination layer
**Depends on**: v1.6 complete
**Research**: Unlikely (internal profiling and design)
**Plans**: 1/1

Plans:
- [x] 36-01: Profile bottlenecks, investigate rate limits, design EventCoordinator — 2026-01-29

#### Phase 37: Event Coordination Layer ✓

**Goal**: New EventCoordinator with SR ID collection and priority queue
**Depends on**: Phase 36
**Research**: Unlikely (internal patterns)
**Plans**: 1/1

Plans:
- [x] 37-01: Create EventCoordinator with discovery and priority queue — 2026-01-29

#### Phase 38: SR ID Parallel Scraping ✓

**Goal**: Simultaneous multi-bookmaker scraping with batch processing
**Depends on**: Phase 37
**Research**: Unlikely (established async patterns)
**Plans**: 1/1

Plans:
- [x] 38-01: Extend EventTarget and implement parallel scraping — 2026-01-29

#### Phase 39: Batch DB Storage ✓

**Goal**: Bulk inserts, per-event status tracking table
**Depends on**: Phase 38
**Research**: Unlikely (SQLAlchemy bulk patterns)
**Plans**: 1/1

Plans:
- [x] 39-01: EventScrapeStatus model, store_batch_results(), run_full_cycle() — 2026-01-29

#### Phase 40: Concurrency Tuning & Metrics

**Goal**: Optimize semaphores, add performance tracking
**Depends on**: Phase 39
**Research**: Unlikely (internal optimization)
**Plans**: TBD

Plans:
- [ ] 40-01: TBD

#### Phase 41: On-Demand API

**Goal**: Single-event refresh endpoint POST /api/scrape/{sr_id}
**Depends on**: Phase 40
**Research**: Unlikely (existing FastAPI patterns)
**Plans**: TBD

Plans:
- [ ] 41-01: TBD

#### Phase 42: Validation & Cleanup

**Goal**: Side-by-side testing, remove legacy flow
**Depends on**: Phase 41
**Research**: Unlikely (internal testing)
**Plans**: TBD

Plans:
- [ ] 42-01: TBD

## Completed Milestones

<details>
<summary>✅ v1.5 Scraping Observability (Phases 31-33.1) — SHIPPED 2026-01-28</summary>

- [x] Phase 31: Backend Heartbeat & Stale Run Detection (1/1 plans) — 2026-01-27
- [x] Phase 32: Connection Loss Logging (1/1 plans) — 2026-01-27
- [x] Phase 33: Detailed Per-Platform Progress Messages (1/1 plans) — 2026-01-28
- [x] Phase 33.1: Fix Scheduler Interval Display (1/1 plans) — 2026-01-28

</details>

<details>
<summary>✅ v1.4 Odds Comparison UX (Phases 28-30) — SHIPPED 2026-01-26</summary>

- [x] Phase 28: Table Restructure (1/1 plans) — 2026-01-26
- [x] Phase 29: Double Chance & Margins (1/1 plans) — 2026-01-26
- [x] Phase 30: Page Rename & Polish (1/1 plans) — 2026-01-26

</details>

<details>
<summary>✅ v1.3 Coverage Improvements (Phases 23-27) — SHIPPED 2026-01-26</summary>

- [x] Phase 23: Fix Match Rate Bug (1/1 plans) — 2026-01-26
- [x] Phase 24: Country Filters UX (1/1 plans) — 2026-01-26
- [x] Phase 25: Include Started Toggle (1/1 plans) — 2026-01-26
- [x] Phase 26: Tournament Gaps Cards (1/1 plans) — 2026-01-26
- [x] Phase 27: Dashboard Coverage Widgets (1/1 plans) — 2026-01-26

</details>

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

<details>
<summary>✅ v1.6 Event Matching Accuracy (Phases 34-35) — SHIPPED 2026-01-29</summary>

- [x] Phase 34: Investigation & Matching Audit Report (1/1 plans) — 2026-01-28
- [x] Phase 34.1: API/UI Data Flow Audit (1/1 plans) — 2026-01-28
- [x] Phase 35: Apply Remediation Query (1/1 plans) — 2026-01-28

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
| 24. Country Filters UX | v1.3 | 1/1 | Complete | 2026-01-26 |
| 25. Include Started Toggle | v1.3 | 1/1 | Complete | 2026-01-26 |
| 26. Tournament Gaps Cards | v1.3 | 1/1 | Complete | 2026-01-26 |
| 27. Dashboard Coverage Widgets | v1.3 | 1/1 | Complete | 2026-01-26 |
| **v1.3 SHIPPED** | | | **2026-01-26** | |
| 28. Table Restructure | v1.4 | 1/1 | Complete | 2026-01-26 |
| 29. Double Chance & Margins | v1.4 | 1/1 | Complete | 2026-01-26 |
| 30. Page Rename & Polish | v1.4 | 1/1 | Complete | 2026-01-26 |
| **v1.4 SHIPPED** | | | **2026-01-26** | |
| 31. Backend Heartbeat & Stale Run Detection | v1.5 | 1/1 | Complete | 2026-01-27 |
| 32. Connection Loss Logging | v1.5 | 1/1 | Complete | 2026-01-27 |
| 33. Detailed Per-Platform Progress Messages | v1.5 | 1/1 | Complete | 2026-01-28 |
| 33.1 Fix Scheduler Interval Display (INSERTED) | v1.5 | 1/1 | Complete | 2026-01-28 |
| **v1.5 SHIPPED** | | | **2026-01-28** | |
| 34. Investigation & Matching Audit Report | v1.6 | 1/1 | Complete | 2026-01-28 |
| 34.1 API/UI Data Flow Audit (INSERTED) | v1.6 | 1/1 | Complete | 2026-01-28 |
| 35. Apply Remediation Query | v1.6 | 1/1 | Complete | 2026-01-29 |
| **v1.6 SHIPPED** | | | **2026-01-29** | |
| 36. Investigation & Architecture Design | v1.7 | 1/1 | Complete | 2026-01-29 |
| 37. Event Coordination Layer | v1.7 | 1/1 | Complete | 2026-01-29 |
| 38. SR ID Parallel Scraping | v1.7 | 1/1 | Complete | 2026-01-29 |
| 39. Batch DB Storage | v1.7 | 1/1 | Complete | 2026-01-29 |
| 40. Concurrency Tuning & Metrics | v1.7 | 0/? | Not started | - |
| 41. On-Demand API | v1.7 | 0/? | Not started | - |
| 42. Validation & Cleanup | v1.7 | 0/? | Not started | - |
