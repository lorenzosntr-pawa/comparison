# Project Issues

## Open Enhancements

### ISS-002: Comprehensive market mapping needed
**Discovered:** Phase 7 UAT - 2026-01-21
**Type:** Enhancement
**Effort:** Large (dedicated phase)

**Description:**
Current market mapping library handles basic markets (1X2, O/U, BTTS, Handicaps) but many SportyBet and Bet9ja markets fail to map to Betpawa taxonomy. Console shows many "Could not map market" warnings.

**Impact:**
- Missing markets in event detail view
- Incomplete odds comparison for exotic markets
- Limits analysis capabilities

**Current state:**
- ~108 basic market mappings exist in `market_mapping/`
- Many market types still unmapped (Corners, Cards, Player Props, etc.)
- Mapping logic may need refinement for edge cases

**Required work:**
1. Audit all market types from each platform
2. Document Betpawa canonical market taxonomy
3. Expand mapping rules for missing market categories
4. Add unit tests for each mapped market type
5. Handle parameter variations (different line values, etc.)

**Resolution:** Create dedicated phase for comprehensive market mapping improvement.

---

## Open Bugs

None.

---

## Closed Bugs

### BUG-004: Combo markets show margins but no odds (RESOLVED)
**Discovered:** Phase 46 UAT - 2026-02-03
**Resolution:** Fixed 2026-02-03 (Phase 47-01) - `getUnifiedOutcomes()` now checks `outcomes.length > 0` before using reference bookmaker; margin only displays when `outcomeNames.length > 0`.

---

## Closed Enhancements

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
