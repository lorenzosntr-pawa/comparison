# Project Issues

## Open Enhancements

None

---

## Open Bugs

None

---

## Closed Bugs

### BUG-032: Storage page shows blank — CleanupRun schema mismatch (RESOLVED)
**Discovered:** 2026-02-24 (user report during issue review)
**Type:** Schema Mismatch Bug
**Root Cause:** Frontend `CleanupRun` interface used snake_case field names (`started_at`, `duration_ms`, `records_deleted`) but backend `/cleanup/history` API returns camelCase (`startedAt`, `durationSeconds`, individual deletion fields). When the component tried to access `run.started_at`, it was `undefined`, causing `format(new Date(undefined))` to throw and crash the component → blank page.
**Resolution:** Fixed 2026-02-24 - Updated `CleanupRun` interface in `use-storage.ts` to match backend camelCase response. Updated `CleanupHistory.total_count` to `total`. Updated `StoragePage` component to use `startedAt`, `durationSeconds`. Added `getTotalDeleted()` helper to sum all deletion count fields. Files modified: `web/src/features/storage/hooks/use-storage.ts`, `web/src/features/storage/index.tsx`.

### BUG-031: SAWarning about MarketOddsHistory.id autoincrement (RESOLVED)
**Discovered:** 2026-02-24 (warning in logs on every market_odds_history INSERT)
**Type:** Schema Warning
**Root Cause:** `MarketOddsHistory` has a composite primary key `(id, captured_at)` for partitioning support. SQLAlchemy requires `autoincrement=True` on the `id` column to recognize that PostgreSQL's BIGSERIAL will generate values.
**Impact:** Warning spam in logs: `SAWarning: Column 'market_odds_history.id' is marked as a member of the primary key... but has no Python-side or server-side default generator indicated, nor does it indicate 'autoincrement=True'`
**Resolution:** Fixed 2026-02-24 - Added `autoincrement=True` to the `id` column: `id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)`. File modified: `src/db/models/market_odds.py`.

### BUG-030: unchanged_bp=0 due to warmup bookmaker_id mismatch (RESOLVED)
**Discovered:** 2026-02-24 (logs showing unchanged_bp=0 while unchanged_comp showed values)
**Type:** Cache Bug
**Root Cause:** The warmup in `src/caching/warmup.py` hardcoded `bookmaker_id=1` when putting BetPawa snapshots into the cache, but the coordinator queries the actual bookmaker_id from the Bookmaker table. When change detection ran, the cache lookup with the real bookmaker_id (e.g., 4) failed to find data stored under bookmaker_id=1.
**Impact:** BetPawa change detection always saw cache miss → all snapshots marked as "changed" → no storage savings for BetPawa data.
**Resolution:** Fixed 2026-02-24 - Modified warmup to query the Bookmaker table and build a slug→id mapping, then use `bookmaker_id_map.get("betpawa")` instead of hardcoded `1`. Also fixed CachedSnapshot.bookmaker_id to use the lookup map. File modified: `src/caching/warmup.py`.

### BUG-029: market_odds_current UPSERT fails — expression index ON CONFLICT (RESOLVED)
**Discovered:** 2026-02-24 (logs during v2.9 deployment)
**Type:** Critical Database Bug
**Severity:** BLOCKER (was)
**Root Cause:** Two PostgreSQL limitations collided:
1. SQLAlchemy's `on_conflict_do_update(index_elements=..., index_where=...)` is for **partial indexes**, not **expression indexes**
2. Expression indexes (like `COALESCE(line, 0)`) cannot be promoted to UNIQUE CONSTRAINTs, so `ON CONFLICT ON CONSTRAINT name` doesn't work
3. SQLAlchemy's ORM doesn't support expression-based ON CONFLICT targets
**Resolution:** Fixed 2026-02-24 - Replaced SQLAlchemy's `on_conflict_do_update()` with raw SQL using `text()`. The raw SQL properly specifies the expression index columns: `ON CONFLICT (event_id, bookmaker_slug, betpawa_market_id, COALESCE(line, 0))`. File modified: `src/storage/write_handler.py`.

### BUG-028: Historical data missing after v2.9 migration — no data migration performed (RESOLVED)
**Discovered:** 2026-02-24 (user report during issue review)
**Type:** Critical Bug (Data Regression)
**Severity:** BLOCKER
**Root Cause:** v2.9 migration (Phases 105-110) performed schema-only migration without migrating historical data. Phase 109 updated history.py to query ONLY new MarketOddsHistory table, but no data existed there for pre-v2.9 events. Old data remained orphaned in odds_snapshots + market_odds tables.
**Resolution:** Fixed 2026-02-24 (Phase 110.1-01) - Implemented dual-query strategy in `src/api/routes/history.py`. Both `get_odds_history()` and `get_margin_history()` now query:
1. New `market_odds_history` table (post-v2.9 data)
2. Legacy `odds_snapshots` + `market_odds` tables (pre-v2.9 BetPawa data)
3. Legacy `competitor_odds_snapshots` + `competitor_market_odds` tables (pre-v2.9 competitor data)
Results are deduplicated by timestamp and merged chronologically. Added `_query_legacy_betpawa_history()` and `_query_legacy_competitor_history()` helper functions.

### BUG-027: Odds highlighting lacks visual distinction between BetPawa and competitors (RESOLVED)
**Discovered:** 2026-02-17 (user report during issue review)
**Type:** UX Enhancement
**Resolution:** Fixed 2026-02-17 - Implemented visual distinction between BetPawa and competitor odds highlighting. BetPawa rows use emphatic filled backgrounds (green when better, red when worse). Competitor rows use subtle green borders ONLY when competitor beats BetPawa (no red on competitors - focus is on BetPawa row). Added `isBetpawa` prop to OddsBadge component. Files modified: `match-table.tsx` (BETPAWA_COLOR_CLASSES vs COMPETITOR_COLOR_CLASSES), `odds-badge.tsx` (isBetpawa prop), `market-row.tsx` (pass isBetpawa prop).

### BUG-026: Availability state not cleared when odds return (RESOLVED)
**Discovered:** 2026-02-17 (user report during issue review)
**Root Cause:** In `event_coordinator.py`, the `detect_availability_changes()` function correctly detected `became_available` markets (odds that returned after being unavailable), but these were only counted for logging - never persisted to the database. The `UnavailableMarketUpdate` objects were only created for `became_unavailable` markets, not for markets that needed their `unavailable_at` cleared.
**Impact:** Alert mode stuck showing events after odds returned; history charts showed "became unavailable" but never "became available"; cache/DB mismatch with correct cache but stale DB data.
**Resolution:** Fixed 2026-02-17 - Added code to create `UnavailableMarketUpdate` objects for `became_available` markets with `unavailable_at=None` in both async and sync versions of `_detect_and_log_availability_changes()`. The write_handler already supports setting `unavailable_at=NULL` via UPDATE statements. Files modified: `src/scraping/event_coordinator.py` (4 locations - async BetPawa, async competitor, sync BetPawa, sync competitor).

### BUG-025: Coverage page navigation to Historical Analysis uses wrong tournament ID (RESOLVED)
**Discovered:** 2026-02-13 (user report during issue review)
**Root Cause:** Palimpsest API used synthetic counter-based `tournament_id` (1, 2, 3...) instead of real database IDs. Coverage page navigated to `/historical-analysis/3` (synthetic) but Historical Analysis filtered by actual DB tournament_id, causing mismatch.
**Resolution:** Fixed 2026-02-13 - Modified `palimpsest.py` to populate `tournament_id` from `event.tournament_id` for matched/betpawa-only events. Competitor-only tournaments now use negative IDs (-1, -2...) since they have no BetPawa data. Updated `tournament-table.tsx` to hide Historical Analysis button for competitor-only tournaments (negative IDs). Files modified: `palimpsest.py`, `palimpsest.py` schema, `tournament-table.tsx`, `api.ts` types.

### BUG-024: Historical Analysis page shows only past events, missing tournaments from Odds Comparison (RESOLVED)
**Discovered:** 2026-02-13 (user report during issue review)
**Root Cause:** Default date range was set to "last 7 days" (past only), while users expected to see the same tournaments/events visible on Odds Comparison page (which shows upcoming events).
**Resolution:** Fixed 2026-02-13 - Extended default date range to 30 days past + 7 days future. Added "All + Upcoming" quick select button. Updated `useTournamentMarkets` hook to use same extended range. Files modified: `index.tsx`, `filter-bar.tsx`, `use-tournament-markets.ts`.

### BUG-023: Country and tournament filters not applying to Odds Comparison table (RESOLVED)
**Discovered:** 2026-02-13 (user report during issue review)
**Resolution:** Fixed 2026-02-13 - The `queryKey` in `use-matches.ts:94` was modified to exclude `tournamentIds`, `countries`, `kickoffFrom`, and `kickoffTo`. This prevented TanStack Query from detecting filter changes and caused cached data to be returned instead of re-fetching. Fixed by restoring complete queryKey with all filter parameters. Also removed debug console.log statements.

### BUG-022: Scheduled scrapings appear not to start (RESOLVED)
**Discovered:** 2026-02-12 (user report during Phase 96 UAT)
**Resolution:** Fixed 2026-02-12 (Phase 96-02-FIX) - Root cause was BUG-021 (wrong countdown). User was watching the `detect_stale_runs` job countdown (2 min interval) expecting a scrape to start, but that's a background watchdog job, not the actual scrape job. After fixing BUG-021 to show the correct `scrape_all_platforms` countdown, the issue is resolved.

### BUG-021: Next scrape countdown shows wrong job interval (RESOLVED)
**Discovered:** 2026-02-12 (user report during Phase 96 UAT)
**Resolution:** Fixed 2026-02-12 (Phase 96-02-FIX) - Changed `app-sidebar.tsx:60` from blindly taking `scheduler?.jobs?.[0]?.next_run` to finding the correct job with `.find(job => job.id === 'scrape_all_platforms')`. Also added scrape interval display to sidebar for user clarity.

### BUG-020: Sidebar scrape runs widget missing (RESOLVED)
**Discovered:** 2026-02-12 (user report during Phase 96 UAT)
**Resolution:** Fixed 2026-02-12 (Phase 96-01-FIX) - Added "Last Scrape" section to sidebar showing relative time, status, and events scraped. Uses `useScrapeRuns(1, 0)` hook to fetch most recent run.

### BUG-019: Sidebar event count incomplete (RESOLVED)
**Discovered:** 2026-02-12 (user report during Phase 96 UAT)
**Resolution:** Fixed 2026-02-12 (Phase 96-01-FIX) - Events section now shows both total events AND matched count on separate lines instead of just total.

### BUG-018: Sidebar status dots confusing and ugly (RESOLVED)
**Discovered:** 2026-02-12 (user report during Phase 96 UAT)
**Resolution:** Fixed 2026-02-12 (Phase 96-01-FIX) - Replaced tiny colored dots with readable labeled text. Database shows "OK" or "Error" with icons. Scheduler shows "Running", "Paused", or "Stopped" with color coding.

### BUG-017: Coverage page summary cards recalculate on filter toggle (RESOLVED)
**Discovered:** 2026-02-12 (user report during Phase 94 review)
**Resolution:** Fixed 2026-02-12 (Phase 94-01-FIX2) - Added separate `usePalimpsestEvents` call with `availability: undefined` for stats cards. Stats now use unfiltered `statsData`, table uses filtered `eventsData`. Data sources are independent so toggling availability filter no longer affects stats cards.

### BUG-016: Tournament collision — same-name tournaments from different countries share single ID (RESOLVED)
**Discovered:** 2026-02-12 (user report during Phase 93)
**Resolution:** Fixed 2026-02-12 (Phase 93.1) - Added composite unique constraint `UNIQUE(sport_id, name, country)` on Tournament table, updated tournament lookup to include country in WHERE clause, updated API queries to filter by country + name, and performed data cleanup to split existing tournaments by country.

### BUG-015: No per-market margin breakdown per tournament (RESOLVED)
**Discovered:** Phase 84 UAT - 2026-02-10
**Resolution:** Fixed 2026-02-10 (Phase 84.1-01) - `MarketBreakdown` component added to `tournament-list.tsx` displaying per-market margins (1X2, O/U 2.5, BTTS, DC) in 2-column grid layout.

### BUG-014: Tournament metrics only show 1X2 market margins (RESOLVED)
**Discovered:** Phase 84 UAT - 2026-02-10
**Resolution:** Fixed 2026-02-10 (Phase 84.1-01) - `TRACKED_MARKETS` constant with 4 market types (1X2, O/U 2.5, BTTS, DC) replaces hardcoded `MARKET_1X2_ID`. All markets now processed.

### BUG-013: Tournament metrics exclude started events (RESOLVED)
**Discovered:** Phase 84 UAT - 2026-02-10
**Resolution:** Fixed 2026-02-10 (Phase 84.1-01) - API request now includes `include_started: true` to fetch completed matches for historical analysis.

### BUG-012: No multi-bookmaker comparison capability (RESOLVED)
**Discovered:** Phase 66 UAT - 2026-02-08
**Resolution:** Fixed 2026-02-10 (Phase 66-67 implementation) - Full comparison mode implemented with toggle, `useMultiOddsHistory` hook, multi-bookmaker chart rendering, and outcome selector.

### BUG-011: Odds tab redundantly shows margin line (RESOLVED)
**Discovered:** Phase 66 UAT - 2026-02-08
**Resolution:** Fixed 2026-02-10 - `OddsLineChart` now called with `showMargin={false}` in history dialog Odds tab (line 311).

### BUG-010: Competitor odds history not working (RESOLVED)
**Discovered:** Phase 66 UAT - 2026-02-08
**Resolution:** Fixed 2026-02-10 - Backend `src/api/routes/history.py` now queries `CompetitorOddsSnapshot` and `CompetitorMarketOdds` tables for competitor bookmakers (sportybet, bet9ja).

### BUG-009: /api/scrape/stream returns 422 instead of 404 (RESOLVED)
**Discovered:** Post-Phase 59 verification - 2026-02-06
**Root Cause:** After SSE removal in Phase 59, the `/{scrape_run_id}` route was catching `/stream` requests and trying to parse "stream" as an integer, resulting in validation error 422.
**Resolution:** Fixed 2026-02-06 - Added explicit `/stream` route returning 410 Gone with message to use WebSocket instead. Route placed before dynamic `/{scrape_run_id}` for proper matching.

### BUG-008: Cache eviction crashes with timezone mismatch (RESOLVED)
**Discovered:** Post-Phase 59 verification - 2026-02-06
**Root Cause:** `evict_expired()` compared naive `cutoff` against potentially timezone-aware kickoffs in `_event_kickoffs`. BetPawa API returns kickoffs with `Z` suffix parsed as UTC-aware datetime.
**Impact:** All scheduled scrapes failed at the end during cache eviction step.
**Resolution:** Fixed 2026-02-06 - Normalize both `cutoff` and `kickoff` to naive UTC before comparison in `evict_expired()`.

### BUG-007: On-demand scrapes bypass cache and async write pipeline (RESOLVED)
**Discovered:** Phase 55 issue review - 2026-02-05
**Resolution:** Fixed 2026-02-05 (Phase 55.1-01) - Added `odds_cache` and `write_queue` params from `request.app.state` to all 3 `EventCoordinator.from_settings()` calls in `src/api/routes/scrape.py`.

### BUG-006: Stale detection fails — timezone mismatch (RESOLVED)
**Discovered:** Phase 55 re-verification - 2026-02-05
**Resolution:** Fixed 2026-02-05 (Phase 55.1-01) - Applied `.replace(tzinfo=None)` pattern to `last_activity` and `started_at` in `mark_run_stale()`.

### BUG-005: Async write handler crashes on every batch — duplicate `write_ms` keyword (RESOLVED)
**Discovered:** Phase 55 re-verification - 2026-02-05
**Resolution:** Fixed 2026-02-05 (Phase 55.1-01) - Removed duplicate `write_ms` explicit kwarg from success log in `_process_with_retry()`. `**stats` already provides it.

### BUG-004: Combo markets show margins but no odds (RESOLVED)
**Discovered:** Phase 46 UAT - 2026-02-03
**Resolution:** Fixed 2026-02-03 (Phase 47-01) - `getUnifiedOutcomes()` now checks `outcomes.length > 0` before using reference bookmaker; margin only displays when `outcomeNames.length > 0`.

---

## Closed Enhancements

### ISS-002: Comprehensive market mapping needed (RESOLVED)
**Discovered:** Phase 7 UAT - 2026-01-21
**Resolution:** 2026-02-24 (issue review) - Closed with diminishing returns. v1.8 addressed high-impact mappings (129 total). SportyBet 52.2%, Bet9ja 40.5% mapping success. Remaining ~380 unmapped markets are platform-specific with no BetPawa equivalent. Revisit if business need arises.

### ISS-005: Tournament detail page with margin timeline (RESOLVED)
**Discovered:** Phase 84.1 UAT - 2026-02-10
**Resolution:** Fixed 2026-02-10 (Phase 84.2-01) - Added `/historical-analysis/:tournamentId` route with TournamentDetailPage component. useTournamentMarkets hook extracts ALL unique markets with avg/min/max margin and marginHistory. Market cards grid with timeline chart on card click.

### ISS-001: SportyBet/Bet9ja scraping not implemented (RESOLVED)
**Resolution:** Fixed in Phase 6.1 - Cross-platform scraping implemented

### ISS-003: Scheduler interval displays 2 minutes instead of settings value (RESOLVED)
**Resolution:** Fixed in Phase 33.1 - Job ID corrected from `scrape_odds` to `scrape_all_platforms`, index access replaced with named lookup

### ISS-004: Tournament discovery not included in scheduled scrape cycle (RESOLVED)
**Discovered:** Phase 35 UAT - 2026-01-28
**Resolution:** Fixed 2026-01-29 - Added `TournamentDiscoveryService.discover_all()` call at start of `scrape_all_platforms` job. Competitors' new tournaments are now discovered on each scrape run.

### BUG-001: BetPawa events not matching with competitors (RESOLVED)
**Discovered:** v1.7 UAT - 2026-02-02
**Resolution:** Fixed 2026-02-02 - Debugging confirmed `widget.id` IS the correct SportRadar ID (8-digit numeric, same format as competitors). Cleaned up SR ID extraction code to use `widget.id` directly without unnecessary fallback to `widget.data.matchId` (which doesn't exist in the API response).

### BUG-002: Tournament/region missing for competitors (RESOLVED)
**Discovered:** v1.7 UAT - 2026-02-02
**Resolution:** Fixed 2026-02-02 (FIX5) - Corrected field extraction in `_get_or_create_competitor_tournament_from_raw()`:
- SportyBet: tournament/country are nested in `sport.category.tournament.name` and `sport.category.name` (not top-level fields)
- Bet9ja: country is in `SG` field (not `SGN`)
Competitor events now created with proper tournaments containing `country_raw`.

### BUG-003: Bookmakers table not seeded - BetPawa events not stored (RESOLVED)
**Discovered:** v1.7 UAT - 2026-02-02
**Root Cause:** v1.7 EventCoordinator's `_get_bookmaker_ids()` only fetched existing bookmakers. Unlike v1.6's `_get_bookmaker_id()` which created bookmakers on first run, the new code expected them to already exist.
**Impact:** `bookmaker_ids.get("betpawa")` returned None, causing all BetPawa event storage to be skipped.
**Resolution:** Fixed 2026-02-02 (FIX5) - Restored auto-create logic in `_get_bookmaker_ids()` to create missing bookmakers (betpawa, sportybet, bet9ja) on first run.
