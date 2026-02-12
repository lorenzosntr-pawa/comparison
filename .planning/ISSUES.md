# Project Issues

## Open Enhancements

### ISS-002: Comprehensive market mapping needed
**Discovered:** Phase 7 UAT - 2026-01-21
**Updated:** 2026-02-05 (issue review)
**Type:** Enhancement
**Effort:** Medium (diminishing returns)

**Description:**
Market mapping library covers core markets but many exotic/niche market types remain unmapped across SportyBet and Bet9ja.

**Impact:**
- Missing markets in event detail view for exotic market types
- Incomplete odds comparison for niche markets
- Limits analysis for corners, cards, player props

**Current state (post-v1.8):**
- 129 market mappings exist in `market_mapping/mappings/market_ids.py`
- SportyBet mapping success: 52.2% (up from 47.3%)
- Bet9ja mapping success: 40.5% (up from 36.1%)
- v1.8 added 20 new mappings, combo market parameter handling, handicap line fix, outcome normalization
- ~380 unmapped market types identified (Phase 45 audit), many are platform-specific with no BetPawa equivalent

**Remaining work (if pursued):**
1. Corner range markets (169, 182) — UNKNOWN_PARAM_MARKET errors
2. HT/FT combo markets — moderate frequency
3. Player prop markets — low priority (BetPawa may not offer equivalents)
4. Remaining combo variants (818, 551) — outcome structure mismatches

**Resolution:** Diminishing returns — most high-impact mappings addressed in v1.8. Remaining gaps are niche markets. Revisit if business need arises.

---

## Open Bugs

None

---

## Closed Bugs

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
