# Betpawa Odds Comparison Tool

## What This Is

A comparative analysis tool (branded "pawaRisk") for Betpawa to analyze and compare its football markets and odds with competitors (SportyBet, Bet9ja). The tool scrapes odds data on a schedule, matches events across platforms using SportRadar IDs, and displays side-by-side comparisons with margin analysis through a React web interface.

## Core Value

Accurate cross-platform market matching and real-time odds comparison that enables Betpawa to understand its competitive position in the Nigerian market.

## Current State (v1.8 Market Matching Accuracy)

**Shipped:** 2026-02-03

**Tech Stack:**
- Backend: Python 3.11+, FastAPI, SQLAlchemy 2.0, PostgreSQL, APScheduler
- Frontend: React 19, Vite, TanStack Query v5, Tailwind CSS v4, shadcn/ui
- ~30,647 lines of code

**Capabilities:**
- 128 market mappings from SportyBet and Bet9ja to Betpawa format (20 new in v1.8)
- Cross-platform event matching via SportRadar IDs (99.9% accuracy confirmed)
- **Event-centric parallel scraping** - all platforms scraped simultaneously per event
- EventCoordinator with priority queue (kickoff urgency + coverage value)
- Configurable concurrency limits via Settings API
- On-demand single-event refresh POST /api/scrape/event/{sr_id}
- Real-time progress streaming via SSE with per-platform event counts and timing
- Dashboard with scheduler controls, platform health, and live coverage metrics
- Match list and detail views with color-coded odds comparison
- Full competitor palimpsest scraping (~200+ tournaments per platform)
- Coverage Comparison page with accurate tournament/event availability analysis
- Searchable multi-select country filter with type-to-filter UX
- Include Started toggle to filter out in-play events
- Tournament gaps cards showing coverage by competitor
- Mode toggle on Matches page for competitor-only events
- Configurable history retention (1-90 days)
- Automatic cleanup scheduler with daily execution
- Settings persistence across server restarts
- Manage Data dialog for manual cleanup and data overview
- Bookmakers-as-rows table layout for vertical odds comparison
- Double Chance market (1X, X2, 12) with per-market margins
- Comparative margin color coding (Betpawa vs competitors)
- Renamed page to "Odds Comparison" with /odds-comparison route
- Stale run detection watchdog with auto-fail for hung scrapes
- Startup recovery for stale runs after server crashes
- Connection loss detection with CONNECTION_FAILED status and auto-rescrape
- Per-platform progress events with real counts and elapsed time
- Accurate coverage statistics with DISTINCT SportRadar ID counting

## Requirements

### Validated

- ✓ Port TypeScript mapping library to Python — v1.0
- ✓ FastAPI backend service orchestrating scrapers — v1.0
- ✓ PostgreSQL database with timestamped odds snapshots — v1.0
- ✓ Scheduled scraping with configurable interval — v1.0
- ✓ Event matching by SportRadar ID across all platforms — v1.0
- ✓ Market mapping for 108 supported markets — v1.0
- ✓ React frontend with match list view (1X2, O/U 2.5, BTTS) — v1.0
- ✓ Match detail view with all markets (Betpawa grouping) — v1.0
- ✓ Side-by-side odds display for each market — v1.0
- ✓ Margin percentage calculation per bookmaker — v1.0
- ✓ Value delta showing Betpawa vs competitors — v1.0
- ✓ Color-coded indicators (green/red) for better/worse odds — v1.0
- ✓ Filtering by league, date/time — v1.0
- ✓ N/A indicators when competitor lacks a market — v1.0
- ✓ Per-event data freshness timestamps — v1.0
- ✓ Competitor tournament discovery scraping — v1.1
- ✓ Full competitor event scraping with parallel execution — v1.1
- ✓ Competitor-only event visibility on Matches page — v1.1
- ✓ Coverage Comparison page with tournament/event availability — v1.1
- ✓ Palimpsest API with coverage stats and event filtering — v1.1
- ✓ Configurable history retention (1-90 days) — v1.2
- ✓ Automatic cleanup scheduler — v1.2
- ✓ Settings persistence across restarts — v1.2
- ✓ Manage Data dialog with cleanup controls — v1.2
- ✓ Searchable multi-select country filter — v1.3
- ✓ Include Started toggle for pre-match focus — v1.3
- ✓ Tournament gaps cards per competitor — v1.3
- ✓ Dashboard coverage widgets with live data — v1.3
- ✓ Bookmakers-as-rows table layout for vertical comparison — v1.4
- ✓ Double Chance market (1X, X2, 12) as selectable column — v1.4
- ✓ Per-market margin display with comparative color coding — v1.4
- ✓ Renamed page to "Odds Comparison" with new URL route — v1.4
- ✓ Stale run detection watchdog with auto-fail for hung scrapes — v1.5
- ✓ Startup recovery for stale runs after server crashes — v1.5
- ✓ Connection loss detection with CONNECTION_FAILED status and auto-rescrape — v1.5
- ✓ Per-platform progress events with real counts and timing — v1.5
- ✓ Correct scheduler interval display (ISS-003 fix) — v1.5
- ✓ Event matching accuracy audit with SQL evidence — v1.6
- ✓ Coverage statistics using DISTINCT SportRadar IDs (API-001 fix) — v1.6
- ✓ Event-centric parallel scraping architecture (EventCoordinator) — v1.7
- ✓ Priority queue with kickoff urgency and coverage value — v1.7
- ✓ Configurable concurrency limits via Settings API — v1.7
- ✓ On-demand single-event refresh endpoint — v1.7
- ✓ Competitor odds in event detail page — v1.7
- ✓ Comprehensive market mapping audit with categorized gap analysis — v1.8
- ✓ 20 new market mappings covering ~1,800 occurrences — v1.8
- ✓ Combo market parameter handling (1X2OU, DCOU, etc.) — v1.8
- ✓ Handicap market line field fix for competitor odds display — v1.8
- ✓ Cross-bookmaker outcome name normalization — v1.8
- ✓ Mapping success rates: SportyBet 52.2%, Bet9ja 40.5% — v1.8

### Active

- [ ] WebSocket real-time updates on new scrape data
- [ ] Historical trend visualization (data stored, UI deferred)

### Out of Scope

- User accounts/authentication — internal tool, no access control needed
- Alerts/notifications to admins — deferred, add after MVP
- Data export (CSV/PDF) — view only for now
- Sports other than football — focus on football only
- Regions other than Nigeria — Nigeria focus
- Mobile-first design — desktop-first, basic mobile usability

## Context

**Existing codebase:**
- `src/market_mapping/`: Python library for market transformation (108 mappings)
- `src/scraping/`: Async clients for SportyBet, BetPawa, Bet9ja
- `src/api/`: FastAPI backend with scheduler and SSE streaming
- `web/`: React frontend with TanStack Query and shadcn/ui

**Technical decisions:**
- Betpawa is canonical format — competitors mapped to Betpawa taxonomy
- SportRadar IDs enable reliable cross-platform matching
- SSE streaming for scrape progress (WebSocket deferred)
- structlog for structured logging with JSON/console modes

## Constraints

- **Region**: Nigeria — scrapers configured for Nigerian market APIs
- **Data retention**: 30 days — balance storage costs with analysis needs
- **Match confidence**: SportRadar ID only — no fuzzy name matching

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Port TypeScript mapping to Python | Single-language backend simplifies deployment | ✓ Good — 108 mappings working |
| FastAPI for backend | Modern async Python framework, handles SSE well | ✓ Good — clean architecture |
| PostgreSQL for storage | Robust, handles time-series well, supports complex queries | ✓ Good — performant |
| React for frontend | Popular ecosystem, good for data-heavy dashboards | ✓ Good — maintainable |
| TanStack Query for state | Server-state focused, handles caching/refetching | ✓ Good — reduced boilerplate |
| Tailwind for styling | Fast prototyping, utility-first | ✓ Good — consistent styling |
| SSE for real-time | Simpler than WebSocket for one-way streaming | ✓ Good — works well for progress |
| StrEnum for status fields | Type safety + string storage in DB | ✓ Good — clean enums |
| Betpawa-first metadata | Competitors insert-only except kickoff | ✓ Good — consistent data |
| Separate competitor tables | Independent tournament/event storage, match at query time | ✓ Good — v1.1 clean schema |
| Metadata priority sportybet > bet9ja | SportyBet has better SR ID coverage | ✓ Good — v1.1 consistent display |
| Fetch-then-store pattern | API parallel, DB sequential avoids session conflicts | ✓ Good — v1.1 solved async issues |
| Negative IDs for competitor events | Distinguish competitor-only from BetPawa events in API | ✓ Good — v1.1 simple frontend check |
| Default 7-day retention | Balance storage vs analysis needs for frequently changing odds | ✓ Good — v1.2 sensible default |
| 1-90 day retention range | Prevent extremes (immediate deletion or excessive storage) | ✓ Good — v1.2 reasonable bounds |
| Preview-before-delete pattern | Prevent accidental data loss with confirmation | ✓ Good — v1.2 safe UX |
| Daily cleanup at 2 AM UTC | Off-peak hours, consistent scheduling | ✓ Good — v1.2 minimal disruption |
| Command + Popover for multi-select | Consistent with shadcn/ui patterns | ✓ Good — v1.3 searchable combobox |
| Empty selection = all countries | No explicit "All" option needed | ✓ Good — v1.3 intuitive UX |
| Default includeStarted OFF | Pre-match focus for odds comparison | ✓ Good — v1.3 sensible default |
| Reuse useCoverage across features | Single data source, consistent metrics | ✓ Good — v1.3 reduced API calls |
| Bookmakers-as-rows layout | Vertical comparison easier to read than horizontal | ✓ Good — v1.4 better UX |
| Comparative margin colors | vs competitors more useful than absolute thresholds | ✓ Good — v1.4 clear comparison |
| Text color for margins | Better readability than background colors | ✓ Good — v1.4 cleaner UI |
| BarChart3 navigation icon | Better visual representation of odds comparison | ✓ Good — v1.4 intuitive |
| URL route /odds-comparison | Full naming consistency with page title | ✓ Good — v1.4 coherent |
| 2-min watchdog interval | Balance responsiveness vs overhead for stale detection | ✓ Good — v1.5 catches hangs quickly |
| CONNECTION_FAILED as distinct status | Different from FAILED, enables specific UI treatment | ✓ Good — v1.5 clear UX |
| Auto-rescrape on connection recovery | User doesn't need to manually retry after disconnect | ✓ Good — v1.5 seamless recovery |
| Per-platform SSE events | Reuse existing SSE infrastructure, no WebSocket needed | ✓ Good — v1.5 minimal complexity |
| SQL-based audit methodology | Comprehensive SQL diagnostics to verify data quality | ✓ Good — v1.6 found real issues |
| DISTINCT SR ID for coverage | Count unique events, not duplicate rows across runs | ✓ Good — v1.6 fixed 92% inflation |
| One-time SQL for timing fix | Data fix, not migration - edge case won't recur | ✓ Good — v1.6 clean remediation |
| Event-centric parallel scraping | Scrape all platforms per event vs sequential by platform | ✓ Good — v1.7 timing gaps reduced to ms |
| Priority queue composite key | (urgency_tier, kickoff, -coverage, not_has_betpawa) | ✓ Good — v1.7 optimal scrape ordering |
| EventCoordinator factory method | from_settings() creates instances with configurable tuning | ✓ Good — v1.7 flexible initialization |
| Single-flush batch insert | Add all records, single flush, link FKs, commit | ✓ Good — v1.7 100x fewer DB round trips |
| BetPawa widget.id for SR ID | SR ID is in widget["id"], 8-digit numeric string | ✓ Good — v1.7 correct extraction |
| Competitor tournament from raw | Extract tournament/country from competitor API responses | ✓ Good — v1.7 proper metadata |
| Audit-driven market mapping | Comprehensive audit before targeted fixes | ✓ Good — v1.8 identified 380 unmapped types |
| Fix handicap line at storage | Populate line from handicap.home in event_coordinator | ✓ Good — v1.8 minimal code change |
| Normalize outcome names at match time | Keep raw data intact, fix display layer | ✓ Good — v1.8 preserves debugging ability |
| Combo market O/U routing | Add combo keys to O/U parameter handling sets | ✓ Good — v1.8 eliminated UNKNOWN_PARAM_MARKET |

---
*Last updated: 2026-02-03 after v1.8 milestone*
