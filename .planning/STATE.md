# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-05)

**Core value:** Accurate cross-platform market matching and real-time odds comparison that enables Betpawa to understand its competitive position in the Nigerian market.
**Current focus:** v2.0 Real-Time Scraping Pipeline

## Current Position

Phase: 54 of 59 (In-Memory Cache Layer)
Plan: 2 of 3 in current phase
Status: In progress
Last activity: 2026-02-05 — Completed 54-02-PLAN.md

Progress: ███░░░░░░░ 33%

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
- **v1.9 Event Details UX** — SHIPPED 2026-02-05 (5 phases, 10 plans)
- **v2.0 Real-Time Scraping Pipeline** — IN PROGRESS (7 phases, Phase 53-59)

## Performance Metrics

**Velocity:**
- Total plans completed: 129 (91 original + 12 FIX plans + 9 v1.8 plans + 10 v1.9 plans + 4 additional + 3 v2.0)
- Average duration: 6 min
- Total execution time: ~11 hours

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
- SportyBet 47.3%->52.2%, Bet9ja 36.1%->40.5% mapping success
- +13,290 / -57 lines (net +13,233)
- ~30,647 total LOC

**v1.9 Summary:**
- 5 phases completed (10 plans including 5 FIX plans)
- 2 days from v1.8 to v1.9 (2026-02-03 to 2026-02-04)
- Event detail summary cards, tabbed market navigation, fuzzy search, sticky header
- +3,599 / -205 lines (net +3,394)
- ~31,116 total LOC

## Accumulated Context

### Key Patterns (v1.0 through v1.9)

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
- **Factory method for configurable initialization** - EventCoordinator.from_settings() (v1.7)
- **Event-centric parallel scraping** - scrape all platforms simultaneously per event (v1.7)
- **Single-flush batch insert pattern** - add all records, single flush to get IDs, link FKs, commit (v1.7)
- **Market group extraction from tabs** - BetPawa tabs array contains categories; extract non-"all" tabs (v1.9)
- **Multi-group array storage** - JSON array so markets appear in multiple category tabs (v1.9)
- **Fuzzy subsequence matching** - query chars in order for intuitive partial matching (v1.9)
- **Dynamic column reordering** - selected competitor adjacent to Betpawa (v1.9)
- **Scroll container-aware fixed positioning** - fixed positioning with dynamic bounds for overflow containers (v1.9)
- **data-scroll-container attribute** - reliable scroll element targeting in nested layouts (v1.9)
- **Shared market utilities** - deduplicated code in lib/market-utils.ts (v1.9)
- **perf_counter timing on progress events** - additive timing fields on existing dict events, backward-compatible (v2.0)
- **Benchmark script pattern** - real scrape cycle + API latency + memory profiling for repeatable measurements (v2.0)
- **Frozen dataclass cache entries** - immutable, hashable, no ORM session dependency for in-memory caching (v2.0)
- **Cache warmup in app lifespan** - async DB load with perf_counter timing at startup (v2.0)
- **Cache population from ORM models** - extract data from flushed models post-commit, convert via snapshot_to_cached_from_models (v2.0)
- **Piggyback eviction on scrape schedule** - no separate background task, evict expired events after each scrape cycle (v2.0)

### Key Decisions

- Metadata priority: sportybet > bet9ja (v1.1)
- SportRadar ID as primary cross-platform matching key
- Store competitor data independently, match at query time
- Negative IDs distinguish competitor-only events from BetPawa events
- Default 7-day retention, 1-90 day range (v1.2)
- Daily cleanup at 2 AM UTC (v1.2)
- Empty selection = all countries (v1.3)
- Default includeStarted OFF for pre-match focus (v1.3)
- Event matching is 99.9% accurate (v1.6 audit)
- Event-centric parallel scraping architecture (v1.7)
- Audit-driven market mapping approach (v1.8)
- Market groups as JSON arrays for multi-category membership (v1.9)
- Categories from data not heuristics (v1.9)
- Scraping is dominant bottleneck at 61.3% of pipeline — Phase 56 highest priority (v2.0 baseline)
- Storage secondary at 37.4% — Processing and Commit sub-phases dominate (v2.0 baseline)
- Event list API p50=903ms justifies cache layer (v2.0 baseline)
- Frozen dataclasses for cache entries — avoids detached ORM instance issues (v2.0 Phase 54)
- Duck-type compatible CachedSnapshot — no adapter layer for existing _build_inline_odds() (v2.0 Phase 54)
- snapshot_to_cached_from_models() for in-memory ORM objects — avoids re-querying DB after commit (v2.0 Phase 54)
- Eviction 2-hour grace period — keeps recently started matches visible for users (v2.0 Phase 54)
- Piggyback eviction on scrape schedule — no separate task, runs once per cycle (v2.0 Phase 54)

### Blockers/Concerns

- Memory usage for cache must stay reasonable (<100MB for active events)
- WebSocket must run alongside SSE initially — no breaking changes during migration
- Keep current fixed scrape interval schedule (no change to refresh timing)

### Roadmap Evolution

- v1.0 MVP shipped 2026-01-23 with 15 phases
- v1.1 Palimpsest Comparison shipped 2026-01-24 with 7 phases
- v1.2 Settings & Retention shipped 2026-01-26 with 4 phases
- v1.3 Coverage Improvements shipped 2026-01-26 with 5 phases
- v1.4 Odds Comparison UX shipped 2026-01-26 with 3 phases
- v1.5 Scraping Observability shipped 2026-01-28 with 4 phases
- v1.6 Event Matching Accuracy shipped 2026-01-29 with 3 phases
- v1.7 Scraping Architecture Overhaul shipped 2026-02-02 with 7 phases
- v1.8 Market Matching Accuracy shipped 2026-02-03 with 5 phases
- v1.9 Event Details UX shipped 2026-02-05 with 5 phases
- All milestones archived to .planning/milestones/
- Milestone v2.0 created: Real-Time Scraping Pipeline, 7 phases (Phase 53-59)

## Session Continuity

Last session: 2026-02-05
Stopped at: Completed 54-02-PLAN.md (2 of 3 plans in Phase 54)
Resume file: None
Next action: Execute 54-03-PLAN.md (API cache integration & latency verification)
