# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-02)

**Core value:** Accurate cross-platform market matching and real-time odds comparison that enables Betpawa to understand its competitive position in the Nigerian market.
**Current focus:** v1.8 Market Matching Accuracy — systematic audit of all market mapping issues

## Current Position

Phase: 47 of 47 (Combo Market Display Fix)
Plan: 1 of 1 (complete)
Status: Complete
Last activity: 2026-02-03 — Completed 47-01-PLAN.md (BUG-004 fix)

Progress: ██████████ 100% (Phase 47)
**Next:** Evaluate remaining market mapping gaps (OUA, CHANCEMIX, other non-handicap issues) for Phase 48

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
- **v1.8 Market Matching Accuracy** — IN PROGRESS (audit-driven phases)

## Performance Metrics

**Velocity:**
- Total plans completed: 106 (91 original + 11 FIX plans + 2 audits + 1 handicap fix + 1 combo market fix)
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
- **Merge split market outcomes** - Frontend merges outcomes when same market appears multiple times (different outcome subsets) (v1.8 FIX)
- **Combined market splitting** - Bet9ja HAOU splits into separate Home O/U (5006) and Away O/U (5003) markets (v1.8 FIX)
- **Iterate deduplicated maps** - UI buildUnifiedMarkets must iterate bookmakerMaps (deduplicated) not raw API data (v1.8 FIX2)
- **Combo market O/U routing** - Markets like 1X2OU, DCOU must be in BET9JA_OVER_UNDER_KEYS and OVER_UNDER_MARKET_IDS to use O/U handler with line parameter (v1.8 44-03)
- **Handicap line field fallback** - Competitor handicap markets use `line = mapped.line ?? mapped.handicap.home` for frontend matching (v1.8 46-01)
- **Outcome presence check for fallback** - `getUnifiedOutcomes()` must check `outcomes.length > 0`, not just market existence (v1.8 47-01)
- **Outcome name normalization** - `normalizeOutcomeName()` converts " - " to " & " for cross-bookmaker matching (Betpawa uses dash, others use ampersand) (v1.8 47-01)

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
- v1.8 Market Matching Accuracy created 2026-02-02: audit-driven approach with Phase 43 audit, then TBD fix phases
- Phase 45 added 2026-02-03: Market Mapping Improvement Audit (analyze Phase 44 improvements, discover next steps)
- Phase 46 added 2026-02-03: Handicap Market Mapping Fix (line field population for 3-Way and Asian Handicap)
- Phase 47 added 2026-02-03: Combo Market Display Fix (BUG-004 - getUnifiedOutcomes checks outcomes.length)

## Session Continuity

Last session: 2026-02-03
Stopped at: Phase 47 complete
Resume file: N/A
Next action: Evaluate remaining market gaps (OUA, CHANCEMIX) for Phase 48
