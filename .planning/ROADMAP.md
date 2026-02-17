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
- ✅ [v1.7 Scraping Architecture Overhaul](milestones/v1.7-ROADMAP.md) — Phases 36-42 (shipped 2026-02-02)
- ✅ [v1.8 Market Matching Accuracy](milestones/v1.8-ROADMAP.md) — Phases 43-47 (shipped 2026-02-03)
- ✅ [v1.9 Event Details UX](milestones/v1.9-ROADMAP.md) — Phases 48-52 (shipped 2026-02-05)
- ✅ [v2.0 Real-Time Scraping Pipeline](milestones/v2.0-ROADMAP.md) — Phases 53-59 (shipped 2026-02-06)
- ✅ [v2.1 Historical Odds Tracking](milestones/v2.1-ROADMAP.md) — Phases 60-68 (shipped 2026-02-08)
- ✅ [v2.2 Odds Freshness](milestones/v2.2-ROADMAP.md) — Phases 69-71 (shipped 2026-02-09)
- ✅ [v2.3 Code Quality & Reliability](milestones/v2.3-ROADMAP.md) — Phases 72-78 (shipped 2026-02-09)
- ✅ [v2.4 Historical Analytics](milestones/v2.4-ROADMAP.md) — Phases 79-86 (shipped 2026-02-11)
- ✅ [v2.5 Odds Availability Tracking](milestones/v2.5-ROADMAP.md) — Phases 87-92 (shipped 2026-02-11)
- ✅ [v2.6 UX Polish & Navigation](milestones/v2.6-ROADMAP.md) — Phases 93-98 (shipped 2026-02-12)
- ✅ [v2.7 Availability Tracking Bugfix](milestones/v2.7-ROADMAP.md) — Phases 99-99.1 (shipped 2026-02-12)
- 🚧 **v2.8 Storage Optimization** — Phases 100-104 (in progress)

---

### 🚧 v2.8 Storage Optimization (In Progress)

**Milestone Goal:** Reduce database from 20+ GB to under 10 GB through schema optimization, compression, and proper retention policies while preserving all current features.

#### Phase 100: Investigation & Analysis ✓

**Goal**: Profile all tables to measure sizes and growth patterns, identify growth drivers, design optimized schema strategy (TimescaleDB hypertables, partitioning, normalization, or combination)
**Depends on**: Previous milestone complete
**Research**: Unlikely (SQL profiling, internal patterns)
**Plans**: 1/1 complete

Plans:
- [x] 100-01: Database profiling and storage analysis (2026-02-17)

**Key Findings:**
- Database: 63 GB (3x larger than expected)
- Primary driver: raw_response columns (33 GB, 53%)
- raw_response is UNUSED after scraping completes
- Recommended: Remove raw_response + 7-day retention = 78% reduction

#### Phase 101: Schema Implementation ✓

**Goal**: Remove raw_response columns from snapshot tables to reclaim 33 GB (53% of database) based on Phase 100 findings
**Depends on**: Phase 100
**Research**: Unlikely (internal code patterns, straightforward column removal)
**Plans**: 1/1 complete

Plans:
- [x] 101-01: Remove raw_response columns from models, DTOs, scraping code, and database (2026-02-17)

#### Phase 102: Scraping Verification & Testing ✓

**Goal**: Verify scraping still works correctly after raw_response removal, add any necessary tests, run end-to-end validation
**Depends on**: Phase 101
**Research**: Unlikely (internal testing patterns)
**Plans**: 1/1 complete

Plans:
- [x] 102-01: Scraping verification (2026-02-17)

#### Phase 103: Data Migration & Validation

**Goal**: Migrate essential recent data to new schema (user accepts losing historical data for fresh start), validate all features work correctly with new database
**Depends on**: Phase 102
**Research**: Unlikely (internal patterns)
**Plans**: TBD

Plans:
- [ ] 103-01: TBD

#### Phase 104: Monitoring & Prevention

**Goal**: Add database size tracking dashboard, implement automated retention policies, set up alerts for abnormal growth to prevent future issues
**Depends on**: Phase 103
**Research**: Unlikely (internal patterns)
**Plans**: TBD

Plans:
- [ ] 104-01: TBD

---

## Completed Milestones

<details>
<summary>✅ v2.7 Availability Tracking Bugfix (Phases 99-99.1) — SHIPPED 2026-02-12</summary>

- [x] Phase 99: Availability Tracking Fix (1/1 + 2 FIX plans) — 2026-02-12
- [x] Phase 99.1: Availability Filters (1/1 + 1 FIX plans) — 2026-02-12

</details>

<details>
<summary>✅ v2.6 UX Polish & Navigation (Phases 93-98) — SHIPPED 2026-02-12</summary>

- [x] Phase 93: Odds Comparison Page (5/5 plans) — 2026-02-12
- [x] Phase 93.1: Tournament Data Integrity Fix (2/2 plans) — 2026-02-12
- [x] Phase 94: Coverage Page (3/3 plans) — 2026-02-12
- [x] Phase 95: Historical Analysis (1/1 plans) — 2026-02-12
- [x] Phase 96: Navigation Overhaul (2/2 plans) — 2026-02-12
- [x] Phase 97: Last Fixes (1/1 plans) — 2026-02-12
- [x] Phase 98: Real-Time Sidebar Widget (1/1 plans) — 2026-02-12

</details>

<details>
<summary>✅ v2.5 Odds Availability Tracking (Phases 87-92) — SHIPPED 2026-02-11</summary>

- [x] Phase 87: Investigation & Schema Design (1/1 plans) — 2026-02-11
- [x] Phase 88: Backend Availability Tracking (1/1 plans) — 2026-02-11
- [x] Phase 89: API & Cache Changes (1/1 plans) — 2026-02-11
- [x] Phase 90: Odds Comparison UI (1/1 plans) — 2026-02-11
- [x] Phase 91: Event Details UI (1/1 plans) — 2026-02-11
- [x] Phase 92: History Charts (1/1 plans) — 2026-02-11

</details>

<details>
<summary>✅ v2.4 Historical Analytics (Phases 79-86) — SHIPPED 2026-02-11</summary>

- [x] Phase 79: Investigation (1/1 plans) — 2026-02-10
- [x] Phase 80: Specifier Bug Fix (2/2 plans) — 2026-02-10
- [x] Phase 81: Interactive Chart (1/1 + 1 FIX plans) — 2026-02-10
- [x] Phase 82: Comparison Table (1/1 plans) — 2026-02-10
- [x] Phase 83: Historical Analysis Page Foundation (1/1 plans) — 2026-02-10
- [x] Phase 84: Tournament Summary Metrics (1/1 + 1 FIX plans) — 2026-02-10
- [x] Phase 84.1: Fix Tournament Metrics Design (1/1 + 1 FIX plans) — 2026-02-10
- [x] Phase 84.2: Tournament Detail Page (1/1 + 1 FIX plans) — 2026-02-11
- [x] Phase 85: Time-to-Kickoff Charts (2/2 plans) — 2026-02-11
- [x] Phase 85.1: Historical Analysis Card Margins (1/1 plans) — 2026-02-11
- [x] Phase 86: Betpawa vs Competitor Comparison (4/4 plans) — 2026-02-11

</details>

<details>
<summary>✅ v2.3 Code Quality & Reliability (Phases 72-78) — SHIPPED 2026-02-09</summary>

- [x] Phase 72: WebSocket Investigation & Bug Fixes (1/1 plans) — 2026-02-09
- [x] Phase 73: WebSocket Reliability (1/1 plans) — 2026-02-09
- [x] Phase 74: Dead Code Audit & Removal (Backend) (1/1 plans) — 2026-02-09
- [x] Phase 75: Dead Code Audit & Removal (Frontend) (1/1 plans) — 2026-02-09
- [x] Phase 76: Documentation (Backend) (3/3 plans) — 2026-02-09
- [x] Phase 77: Documentation (Frontend) + README (3/3 plans) — 2026-02-09
- [x] Phase 78: Type Annotations & Error Handling (1/1 plans) — 2026-02-09

</details>

<details>
<summary>✅ v2.2 Odds Freshness (Phases 69-71) — SHIPPED 2026-02-09</summary>

- [x] Phase 69: Investigation & Freshness Audit (1/1 plans) — 2026-02-09
- [x] Phase 70: Backend Freshness Fixes (1/1 plans) — 2026-02-09
- [x] Phase 71: Frontend Freshness Fixes (1/1 plans) — 2026-02-09

</details>

<details>
<summary>✅ v1.9 Event Details UX (Phases 48-52) — SHIPPED 2026-02-05</summary>

- [x] Phase 48: Event Summary Redesign (1/1 + 2 FIX plans) — 2026-02-03
- [x] Phase 49: Market Grouping System (1/1 + 2 FIX plans) — 2026-02-04
- [x] Phase 50: Market Filtering (1/1 plans) — 2026-02-04
- [x] Phase 51: Navigation UX (1/1 + 1 FIX plan) — 2026-02-04
- [x] Phase 52: Polish & Integration (1/1 plans) — 2026-02-04

</details>

<details>
<summary>✅ v1.8 Market Matching Accuracy (Phases 43-47) — SHIPPED 2026-02-03</summary>

- [x] Phase 43: Comprehensive Market Mapping Audit (1/1 plans) — 2026-02-02
- [x] Phase 44: High-Priority Market Mappings (3/3 + 2 FIX plans) — 2026-02-02
- [x] Phase 45: Market Mapping Improvement Audit (1/1 plans) — 2026-02-03
- [x] Phase 46: Handicap Market Mapping Fix (1/1 plans) — 2026-02-03
- [x] Phase 47: Combo Market Display Fix (1/1 plans) — 2026-02-03

</details>

<details>
<summary>✅ v1.7 Scraping Architecture Overhaul (Phases 36-42) — SHIPPED 2026-02-02</summary>

- [x] Phase 36: Investigation & Architecture Design (1/1 plans) — 2026-01-29
- [x] Phase 37: Event Coordination Layer (1/1 plans) — 2026-01-29
- [x] Phase 38: SR ID Parallel Scraping (1/1 plans) — 2026-01-29
- [x] Phase 39: Batch DB Storage (1/1 plans) — 2026-01-29
- [x] Phase 40: Concurrency Tuning & Metrics (1/1 plans) — 2026-01-29
- [x] Phase 41: On-Demand API (1/1 plans) — 2026-01-29
- [x] Phase 42: Validation & Cleanup (1/1 + 9 FIX plans) — 2026-02-02

</details>

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

<details>
<summary>✅ v2.0 Real-Time Scraping Pipeline (Phases 53-59) — SHIPPED 2026-02-06</summary>

- [x] Phase 53: Investigation & Benchmarking (1/1 plans) — 2026-02-05
- [x] Phase 54: In-Memory Cache Layer (3/3 plans) — 2026-02-05
- [x] Phase 55: Async Write Pipeline + Incremental Upserts (4/4 plans) — 2026-02-05
- [x] Phase 55.1: Fix Phase 55 Bugs (1/1 plans) — 2026-02-05
- [x] Phase 56: Concurrency Tuning (1/1 plans) — 2026-02-05
- [x] Phase 57: WebSocket Infrastructure (3/3 plans) — 2026-02-06
- [x] Phase 58: WebSocket UI Migration (2/2 plans) — 2026-02-06
- [x] Phase 59: SSE Removal & Cleanup (2/2 plans) — 2026-02-06

</details>

<details>
<summary>✅ v2.1 Historical Odds Tracking (Phases 60-68) — SHIPPED 2026-02-08</summary>

- [x] Phase 60: Investigation & Schema Design (1/1 plans) — 2026-02-06
- [x] Phase 61: Historical Snapshot Retention — SKIPPED (existing setting sufficient)
- [x] Phase 62: Historical Data API (2/2 plans) — 2026-02-06
- [x] Phase 63: Freshness Timestamps (1/1 plans) — 2026-02-06
- [x] Phase 64: Chart Library Integration (1/1 plans) — 2026-02-06
- [x] Phase 65: History Dialog Component (1/1 plans) — 2026-02-06
- [x] Phase 66: Odds Comparison History (2/2 plans) — 2026-02-08
- [x] Phase 67: Event Details History (2/2 plans) — 2026-02-08
- [x] Phase 68: Market-Level History View (1/1 plans) — 2026-02-08

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
| 40. Concurrency Tuning & Metrics | v1.7 | 1/1 | Complete | 2026-01-29 |
| 41. On-Demand API | v1.7 | 1/1 | Complete | 2026-01-29 |
| 42. Validation & Cleanup | v1.7 | 10/10 | Complete | 2026-02-02 |
| **v1.7 SHIPPED** | | | **2026-02-02** | |
| 43. Comprehensive Market Mapping Audit | v1.8 | 1/1 | Complete | 2026-02-02 |
| 44. High-Priority Market Mappings | v1.8 | 3/3 | Complete | 2026-02-02 |
| 45. Market Mapping Improvement Audit | v1.8 | 1/1 | Complete | 2026-02-03 |
| 46. Handicap Market Mapping Fix | v1.8 | 1/1 | Complete | 2026-02-03 |
| 47. Combo Market Display Fix | v1.8 | 1/1 | Complete | 2026-02-03 |
| **v1.8 SHIPPED** | | | **2026-02-03** | |
| 48. Event Summary Redesign | v1.9 | 1/1 | Complete | 2026-02-03 |
| 49. Market Grouping System | v1.9 | 1/1 | Complete | 2026-02-04 |
| 50. Market Filtering | v1.9 | 1/1 | Complete | 2026-02-04 |
| 51. Navigation UX | v1.9 | 2/2 | Complete | 2026-02-04 |
| 52. Polish & Integration | v1.9 | 1/1 | Complete | 2026-02-04 |
| **v1.9 SHIPPED** | | | **2026-02-05** | |
| 53. Investigation & Benchmarking | v2.0 | 1/1 | Complete | 2026-02-05 |
| 54. In-Memory Cache Layer | v2.0 | 3/3 | Complete | 2026-02-05 |
| 55. Async Write Pipeline + Incremental Upserts | v2.0 | 4/4 | Complete | 2026-02-05 |
| 55.1 Fix Phase 55 Bugs (INSERTED) | v2.0 | 1/1 | Complete | 2026-02-05 |
| 56. Concurrency Tuning | v2.0 | 1/1 | Complete | 2026-02-05 |
| 57. WebSocket Infrastructure | v2.0 | 3/3 | Complete | 2026-02-06 |
| 58. WebSocket UI Migration | v2.0 | 2/2 | Complete | 2026-02-06 |
| 59. SSE Removal & Cleanup | v2.0 | 2/2 | Complete | 2026-02-06 |
| **v2.0 SHIPPED** | | | **2026-02-06** | |
| 60. Investigation & Schema Design | v2.1 | 1/1 | Complete | 2026-02-06 |
| 61. Historical Snapshot Retention | v2.1 | - | Skipped | 2026-02-06 |
| 62. Historical Data API | v2.1 | 2/2 | Complete | 2026-02-06 |
| 63. Freshness Timestamps | v2.1 | 1/1 | Complete | 2026-02-06 |
| 64. Chart Library Integration | v2.1 | 1/1 | Complete | 2026-02-06 |
| 65. History Dialog Component | v2.1 | 1/1 | Complete | 2026-02-06 |
| 66. Odds Comparison History | v2.1 | 2/2 | Complete | 2026-02-08 |
| 67. Event Details History | v2.1 | 2/2 | Complete | 2026-02-08 |
| 68. Market-Level History View | v2.1 | 1/1 | Complete | 2026-02-08 |
| **v2.1 SHIPPED** | | | **2026-02-08** | |
| 69. Investigation & Freshness Audit | v2.2 | 1/1 | Complete | 2026-02-09 |
| 70. Backend Freshness Fixes | v2.2 | 1/1 | Complete | 2026-02-09 |
| 71. Frontend Freshness Fixes | v2.2 | 1/1 | Complete | 2026-02-09 |
| **v2.2 SHIPPED** | | | **2026-02-09** | |
| 72. WebSocket Investigation & Bug Fixes | v2.3 | 1/1 | Complete | 2026-02-09 |
| 73. WebSocket Reliability | v2.3 | 1/1 | Complete | 2026-02-09 |
| 74. Dead Code Audit & Removal (Backend) | v2.3 | 1/1 | Complete | 2026-02-09 |
| 75. Dead Code Audit & Removal (Frontend) | v2.3 | 1/1 | Complete | 2026-02-09 |
| 76. Documentation (Backend) | v2.3 | 3/3 | Complete | 2026-02-09 |
| 77. Documentation (Frontend) + README | v2.3 | 3/3 | Complete | 2026-02-09 |
| 78. Type Annotations & Error Handling | v2.3 | 1/1 | Complete | 2026-02-09 |
| **v2.3 SHIPPED** | | | **2026-02-09** | |
| 79. Investigation | v2.4 | 1/1 | Complete | 2026-02-10 |
| 80. Specifier Bug Fix | v2.4 | 2/2 | Complete | 2026-02-10 |
| 81. Interactive Chart | v2.4 | 1/1 + 1 FIX | Complete | 2026-02-10 |
| 82. Comparison Table | v2.4 | 1/1 | Complete | 2026-02-10 |
| 83. Historical Analysis Page Foundation | v2.4 | 1/1 | Complete | 2026-02-10 |
| 84. Tournament Summary Metrics | v2.4 | 1/1 | Complete | 2026-02-10 |
| 84.1 Fix Tournament Metrics Design (INSERTED) | v2.4 | 1/1 | Complete | 2026-02-10 |
| 84.2 Tournament Detail Page (INSERTED) | v2.4 | 1/1 + 1 FIX | Complete | 2026-02-11 |
| 85. Time-to-Kickoff Charts | v2.4 | 2/2 | Complete | 2026-02-11 |
| 85.1 Historical Analysis Card Margins (INSERTED) | v2.4 | 1/1 | Complete | 2026-02-11 |
| 86. Betpawa vs Competitor Comparison | v2.4 | 4/4 | Complete | 2026-02-11 |
| **v2.4 SHIPPED** | | | **2026-02-11** | |
| 87. Investigation & Schema Design | v2.5 | 1/1 | Complete | 2026-02-11 |
| 88. Backend Availability Tracking | v2.5 | 1/1 | Complete | 2026-02-11 |
| 89. API & Cache Changes | v2.5 | 1/1 | Complete | 2026-02-11 |
| 90. Odds Comparison UI | v2.5 | 1/1 | Complete | 2026-02-11 |
| 91. Event Details UI | v2.5 | 1/1 | Complete | 2026-02-11 |
| 92. History Charts | v2.5 | 1/1 | Complete | 2026-02-11 |
| **v2.5 SHIPPED** | | | **2026-02-11** | |
| 93. Odds Comparison Page | v2.6 | 5/5 | Complete | 2026-02-12 |
| 93.1 Tournament Data Integrity Fix (INSERTED) | v2.6 | 2/2 | Complete | 2026-02-12 |
| 94. Coverage Page | v2.6 | 3/3 | Complete | 2026-02-12 |
| 95. Historical Analysis | v2.6 | 1/1 | Complete | 2026-02-12 |
| 96. Navigation Overhaul | v2.6 | 2/2 | Complete | 2026-02-12 |
| 97. Last Fixes | v2.6 | 1/1 | Complete | 2026-02-12 |
| 98. Real-Time Sidebar Widget | v2.6 | 1/1 | Complete | 2026-02-12 |
| **v2.6 SHIPPED** | | | **2026-02-12** | |
| 99. Availability Tracking Fix | v2.7 | 1/1 + 2 FIX | Complete | 2026-02-12 |
| 99.1 Availability Filters (INSERTED) | v2.7 | 1/1 | Complete | 2026-02-12 |
| **v2.7 SHIPPED** | | | **2026-02-12** | |
| 100. Investigation & Analysis | v2.8 | 1/1 | Complete | 2026-02-17 |
| 101. Schema Implementation | v2.8 | 1/1 | Complete | 2026-02-17 |
| 102. Scraping Verification | v2.8 | 1/1 | Complete | 2026-02-17 |
| 103. Data Migration & Validation | v2.8 | 0/? | Not started | - |
| 104. Monitoring & Prevention | v2.8 | 0/? | Not started | - |
