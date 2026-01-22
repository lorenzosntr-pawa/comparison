# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2025-01-20)

**Core value:** Accurate cross-platform market matching and real-time odds comparison that enables Betpawa to understand its competitive position in the Nigerian market.
**Current focus:** Phase 14 in progress — Scraping Logging & Workflow

## Current Position

Phase: 14 of 14 (Scraping Logging & Workflow)
Plan: 2 of 4 in current phase
Status: In progress
Last activity: 2026-01-22 — Completed 14-02-PLAN.md (Orchestrator Logging Integration)

Progress: ██████████░░ 95% (41 of 43 plans complete)

## Performance Metrics

**Velocity:**
- Total plans completed: 41
- Average duration: 6 min
- Total execution time: 3.7 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 Market Mapping Port | 6 | 45 min | 8 min |
| 02 Database Schema | 3 | 21 min | 7 min |
| 03 Scraper Integration | 6 | 16 min | 3 min |
| 04 Event Matching | 2 | 6 min | 3 min |
| 05 Scheduled Scraping | 2 | 10 min | 5 min |
| 06 React Foundation | 4 | 20 min | 5 min |
| 06.1 Cross-Platform Scraping | 1 | 8 min | 8 min |
| 07 Match Views | 3+2fix | 32 min | 6 min |
| 07.1 Complete Odds Pipeline | 1 | 8 min | 8 min |
| 07.2 Scraping Performance | 3 | 16 min | 5.3 min |
| 08 Scrape Runs UI Improvements | 3+2fix | 41 min | 8 min |
| 10 Matches Page Improvements | 2 | 20 min | 10 min |
| 11 Settings Page | 2 | 16 min | 8 min |
| 14 Scraping Logging | 2 | 13 min | 6.5 min |

**Recent Trend:**
- Last 5 plans: 15 min, 12 min, 4 min, 5 min, 8 min
- Trend: Stable

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Use StrEnum for error codes (Python 3.11+) instead of regular Enum
- Use MappingError exception class instead of TypeScript Result pattern
- Use tuple instead of list for immutable sequences in frozen models
- Use ConfigDict with alias_generator for camelCase API field mapping
- Use frozen dataclasses (not Pydantic) for simple parsed value objects
- Pre-compile regex patterns at module level for performance

### Patterns Established

- Pydantic v2 syntax: `model_config = ConfigDict(frozen=True)`
- Discriminated unions with `Field(discriminator='source')`
- Module-level `_to_camel()` function for alias generation
- Module-level `_build_lookups()` pattern for initialization
- Expose `find_by_*` functions, keep lookup dicts private
- `_map_*` private helpers for market-type-specific logic
- frozenset for constant market ID classifications
- GroupedBet9jaMarket dataclass for grouping flat odds by market/param
- SQLAlchemy: DeclarativeBase with MetaData(naming_convention=convention)
- SQLAlchemy: Mapped[] + mapped_column() for all columns
- SQLAlchemy: back_populates for bidirectional relationships
- BigInteger PK for tables that will be partitioned by timestamp
- JSONB (via JSON type) for variable-structure data like API responses
- StrEnum for status fields (type safety + string storage)
- Async Alembic: async_engine_from_config + run_sync wrapper
- Partitioned tables: raw SQL in migrations, SQLAlchemy model as regular table
- Optional extensions: IF EXISTS check for pg_partman
- Lifespan context manager: @asynccontextmanager async def lifespan(app)
- HTTP client dependencies: get_*_client(request: Request) -> httpx.AsyncClient
- Async client class with injected httpx.AsyncClient
- Module-level _retry decorator creation for consistency
- check_health() method for API connectivity testing
- ScrapingOrchestrator accepts all clients in constructor
- Platform enum for type-safe platform references
- asyncio.gather(return_exceptions=True) for partial failure tolerance
- asyncio.Semaphore(10) pattern for parallel API fetching across all platforms
- Static Tailwind class lookup for JIT-compatible dynamic styling (COLOR_CLASSES map)
- Query param validation: ge=, le= for bounds checking
- Optional request body with `| None = None` pattern
- Concurrent health checks with asyncio.gather for per-platform status
- Filter pass-through from endpoint to orchestrator (sport_id, competition_id)
- DB session pass-through to orchestrator for error logging
- Bookmaker auto-creation on first use via _get_bookmaker_id
- insert().on_conflict_do_update(index_elements=[...]) for sportradar_id upserts
- Betpawa-first metadata priority: Betpawa updates, competitors insert-only (except kickoff)
- Tournament cache dict in batch processing for efficiency
- selectinload chain for multi-level relationships (bookmaker_links.bookmaker)
- Subquery with HAVING for count-based filters
- Route ordering: specific paths before parameterized paths (/unmatched before /{id})
- set_app_state() to share FastAPI app.state with scheduled jobs
- configure_scheduler() + start_scheduler() + shutdown_scheduler() lifecycle
- Deferred imports in configure_scheduler() to avoid circular deps
- IntervalTrigger with coalesce=True for missed run handling
- Schemas package: src/api/schemas/ with __init__.py re-exporting all models
- Query param pagination: limit with ge=/le= bounds, offset with ge=0
- Vite: path alias via resolve.alias + tsconfig paths (both needed)
- Vite: API proxy via server.proxy for backend communication
- TanStack Query v5: use gcTime (not cacheTime), isPending (not isLoading)
- TanStack Query: staleTime=5min, gcTime=10min for dashboard-appropriate caching
- Feature-based folder structure: components/ui/layout, features/{name}, hooks, lib, types
- cn() utility from clsx + tailwind-merge for class merging (shadcn requirement)
- Tailwind v4: @import "tailwindcss" + @theme inline for CSS variable mapping
- shadcn/ui: --yes flag for non-interactive component installation
- ThemeProvider pattern: context + localStorage + system media query
- Theme flash prevention: inline script in <head> before React hydration
- React Router v7: import from 'react-router' (not 'react-router-dom')
- shadcn Sidebar: collapsible="icon" for compact mode
- SidebarProvider must wrap entire layout (not just sidebar)
- Feature pages in features/{name}/index.tsx pattern
- API client: explicit property declaration for TypeScript erasableSyntaxOnly
- TanStack Query polling: 10s (scheduler), 30s (health), 60s (events) based on volatility
- Feature hooks in features/{name}/hooks/ with index.ts re-export
- Feature components in features/{name}/components/ with index.ts re-export
- Margin calculation: (sum(1/odds) - 1) * 100
- Subquery for latest snapshot per (event_id, bookmaker_id) pair
- Inline odds for list views: fixed 3 key markets (1X2, O/U 2.5, BTTS)
- OddsCell color coding: green = Betpawa better (higher odds), red = Betpawa worse
- Tolerance 0.02 for neutral odds display
- localStorage persistence for match list column settings
- Client-side tournament sorting (API sorts by kickoff)
- AsyncGenerator pattern for SSE streaming from FastAPI
- EventSource API for browser SSE consumption in React hooks
- Three-column bookmaker comparison grid: Market | Betpawa | SportyBet | Bet9ja
- OddsBadge component: green=best odds, red=worst (>3% worse)
- MarginIndicator: percentage with comparison coloring (lower margin = better)
- Competitive position metric: "X/Y best odds (Z%)" for quick assessment
- Retry endpoint creates new run with trigger="retry:{original_id}" for audit trail
- Failed platform detection from errors + missing platform_timings
- PLATFORM_PROGRESS_COLORS map for dynamic Tailwind classes
- refetchQueries for immediate data sync vs invalidateQueries
- Platform completion detection via platform_timings presence
- Case-insensitive ILIKE search on multiple columns (home_team OR away_team)
- Nullable string fields display as dash in table cells (tournament_country ?? '-')
- Multi-select filter using Popover + Command pattern with checkboxes
- Date preset helper functions for common date ranges (today, tomorrow, weekend, 7 days)
- Array query parameters passed as repeated params for FastAPI list support
- Single-row singleton pattern for settings table (id=1 default row inserted in migration)
- get_settings_from_db() async helper for fetching settings in jobs
- reschedule_job() for runtime APScheduler interval changes
- structlog: configure_logging() with JSON/console output modes
- ScrapePhase StrEnum for workflow state (INITIALIZING → COMPLETED/FAILED)
- PlatformStatus StrEnum for per-platform state (PENDING → COMPLETED/FAILED)
- ScrapePhaseLog model for audit trail of phase transitions
- _emit_phase() for combined DB update + structlog + SSE emission
- _log_phase_history() for audit trail persistence
- structlog.contextvars.bind_contextvars() at scrape start for async context
- ScrapeErrorContext for categorized errors (timeout, network, storage, unknown)

### Roadmap Evolution

- Phase 6.1 inserted after Phase 6: Cross-Platform Scraping (URGENT) - SportyBet/Bet9ja scraping was stubbed out, blocking cross-platform comparison
- Phase 7.1 inserted after Phase 7: Complete Odds Pipeline (URGENT) - BetPawa odds not stored, UI showing no odds
- Phase 7.2 inserted after Phase 7.1: Scraping Performance (URGENT) - ~5min scrape time too slow, poor terminal logging
- Phase 8 (Real-time Updates) removed — renumbered phases 9-13 to 8-12
- Phase 13 added: Competitor Event Import — Import SportyBet/Bet9ja events not in BetPawa for coverage comparison
- Phase 14 added: Scraping Logging & Workflow — Restructure backend scraping with proper logging and state tracking

### Deferred Issues

See: .planning/ISSUES.md (ISS-001 resolved in Phase 6.1)

### Blockers/Concerns

None.

## Session Continuity

Last session: 2026-01-22
Stopped at: Completed 14-02-PLAN.md (Orchestrator Logging Integration) — Phase 14 in progress
Resume file: .planning/phases/14-scraping-logging-workflow/14-02-SUMMARY.md
