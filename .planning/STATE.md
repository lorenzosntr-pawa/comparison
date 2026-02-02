# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-29)

**Core value:** Accurate cross-platform market matching and real-time odds comparison that enables Betpawa to understand its competitive position in the Nigerian market.
**Current focus:** Milestone complete - ready for next milestone

## Current Position

Phase: 42 of 42 (Validation & Cleanup)
Plan: 1 of 1 + FIX + FIX2 + FIX3 + FIX4 + FIX5 + FIX6 + FIX7 + FIX8 + FIX9 plans
Status: FIX9 complete (Event detail page showing all bookmakers)
Last activity: 2026-02-02 — Completed FIX9 (competitor odds in event detail page)

Progress: ██████████ 100% (All fixes complete)

## Milestones

- **v1.0 MVP** — SHIPPED 2026-01-23 (15 phases, 46 plans)
- **v1.1 Palimpsest Comparison** — SHIPPED 2026-01-24 (7 phases, 11 plans)
- **v1.2 Settings & Retention** — SHIPPED 2026-01-26 (4 phases, 8 plans)
- **v1.3 Coverage Improvements** — SHIPPED 2026-01-26 (5 phases, 5 plans)
- **v1.4 Odds Comparison UX** — SHIPPED 2026-01-26 (3 phases, 3 plans)
- **v1.5 Scraping Observability** — SHIPPED 2026-01-28 (4 phases, 4 plans)
- **v1.6 Event Matching Accuracy** — SHIPPED 2026-01-29 (3 phases, 3 plans)
- **v1.7 Scraping Architecture Overhaul** — SHIPPED 2026-01-29 (7 phases, 7 plans)

## Performance Metrics

**Velocity:**
- Total plans completed: 91
- Average duration: 6 min
- Total execution time: ~9 hours

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
- 7 phases completed
- 1 day from v1.6 to v1.7
- Event-centric parallel scraping architecture
- ~1,884 lines removed (legacy orchestrator deleted)

## Accumulated Context

### Key Patterns (v1.0 + v1.1 + v1.2 + v1.3 + v1.4 + v1.5 + v1.6 + v1.7)

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
- v1.7 Scraping Architecture Overhaul shipped 2026-01-29 with 7 phases
- All milestones archived to .planning/milestones/

## Session Continuity

Last session: 2026-02-02
Stopped at: Completed FIX6-8 (API verified working via curl, all 3 bookmakers showing odds)
Resume file: None
