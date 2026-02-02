# UAT Issues: Phase 42 Plan 01-FIX5

**Tested:** 2026-02-02
**Source:** FIX5 (bookmakers auto-creation + competitor tournament field fixes)
**Tester:** User via /gsd:verify-work

## Backend Status

Backend appears to be working correctly:
- Bookmakers auto-created: BetPawa, SportyBet, Bet9ja
- Event discovery: BetPawa=943, SportyBet=1010, Bet9ja=945, merged=1022
- Batch storage: events_stored=50 per batch, snapshots_created=100-150 per batch

## Open Issues

### UAT-001: Coverage Comparison - Multiple display problems

**Discovered:** 2026-02-02
**Phase/Plan:** 42-01-FIX5
**Severity:** Blocker
**Feature:** Coverage Comparison page
**Description:** Coverage Comparison page shows incorrect data despite backend logging successful event storage.
**Problems:**
1. Match rate shows 0% or very low (should be ~86% based on merged=1022 vs 3_platforms=886)
2. Tournament/country fields missing for events
3. Event counts don't match backend logs (943 BetPawa events discovered, but UI shows far fewer)
**Expected:** Coverage page should show ~943 BetPawa events, ~1010 SportyBet, ~945 Bet9ja with proper tournaments and high match rate
**Actual:** Few BetPawa events shown, incorrect data, low match rate
**Repro:**
1. Start application, trigger scrape
2. Wait for scrape to complete (logs show ~20 batches with snapshots)
3. Navigate to Coverage Comparison page
4. Observe incorrect counts and missing data

### UAT-002: Odds Comparison - No BetPawa odds displayed

**Discovered:** 2026-02-02
**Phase/Plan:** 42-01-FIX5
**Severity:** Blocker
**Feature:** Odds Comparison page
**Description:** Odds Comparison page shows no BetPawa odds at all. Only the "Competitors Only" tab displays data.
**Expected:** Events should show odds from all 3 bookmakers (BetPawa, SportyBet, Bet9ja) side-by-side
**Actual:** BetPawa odds completely missing, only competitor-only events display data
**Repro:**
1. Navigate to Odds Comparison page
2. Check the main view - no BetPawa odds visible
3. Only "Competitors Only" tab shows any data

## Root Cause - CONFIRMED

**Missing `betpawa_event_id` assignment in EventCoordinator**

The new `EventCoordinator._create_competitor_event_from_raw()` method (lines 1668-1677) creates CompetitorEvent records **without** setting the `betpawa_event_id` field.

**Old code** (competitor_events.py:119-136):
```python
betpawa_event_id = await self._get_betpawa_event_by_sr_id(db, sportradar_id)
...
CompetitorEvent(..., betpawa_event_id=betpawa_event_id, ...)
```

**New code** (event_coordinator.py:1668-1677):
```python
CompetitorEvent(
    source=source.value,
    tournament_id=tournament_id,
    sportradar_id=sr_id,
    external_id=platform_id,
    # betpawa_event_id NOT SET!
)
```

**Impact:**
1. **Coverage stats broken** - `/api/palimpsest/coverage` counts matched events via `WHERE betpawa_event_id IS NOT NULL` which is always false
2. **Odds Comparison broken** - `EventBookmaker` links for competitors only created if BetPawa Event was processed first in same batch (ordering dependent)

**Fix required:**
1. In `_create_competitor_event_from_raw()`: Look up the BetPawa Event by SR ID and set `betpawa_event_id`
2. Alternative: After batch storage, run a reconciliation pass to link CompetitorEvents to Events by matching sportradar_id

## Resolved Issues

### UAT-001: Coverage Comparison - Multiple display problems
**Resolved:** 2026-02-02 - Fixed in FIX6 (commit 0064b1b)
**Fix:** Added `betpawa_event_id` lookup in `_create_competitor_event_from_raw()` and post-batch reconciliation pass
**Result:** Coverage now shows correct match rates (82% linked)

## Open Issues (Discovered During FIX6 Testing)

### UAT-003: Odds Comparison - API doesn't load competitor odds

**Discovered:** 2026-02-02
**Phase/Plan:** 42-01-FIX6
**Severity:** Blocker
**Feature:** Odds Comparison page
**Description:** The `/api/events` endpoint's `_load_latest_snapshots_for_events()` only queries `OddsSnapshot` table, but v1.7 EventCoordinator stores competitor odds in `CompetitorOddsSnapshot` table (separate from BetPawa odds).
**Root Cause:** Architectural mismatch - v1.7 stores competitor odds in separate tables, but API expects all odds in OddsSnapshot.
**Evidence:**
```
OddsSnapshots: 238 (all BetPawa)
CompetitorOddsSnapshots: 562
```
**Expected:** Odds Comparison page should show BetPawa + competitor odds side-by-side
**Actual:** Only BetPawa odds displayed (from OddsSnapshot), competitor odds not loaded
**Fix Required:** Modify `_load_latest_snapshots_for_events()` to also load CompetitorOddsSnapshot for events that have competitor matches via CompetitorEvent.betpawa_event_id

**Resolved:** 2026-02-02 - Fixed in FIX7 (commit 7492ad5) + FIX8 (commit cc805f9)
**Fix:**
1. Added `_load_competitor_snapshots_for_events()` function to load CompetitorOddsSnapshot
2. Updated `_build_matched_event()` to use competitor snapshots for sportybet/bet9ja
3. Added reconciliation to create EventBookmaker links for competitors

## All Issues Resolved - API Verified Working

### API Test Results (2026-02-02)

```bash
curl "http://localhost:8000/api/events?page=1&page_size=3&min_bookmakers=2"
```

**Response:** All events return with 3 bookmakers (betpawa, sportybet, bet9ja), each with `has_odds: true` and populated `inline_odds`.

**Database state:**
- Events: 577 BetPawa events
- EventBookmakers: 1703 total (577 betpawa, 572 sportybet, 554 bet9ja)
- CompetitorEvents with betpawa_event_id: 1126/1244 (90.5% linked)

### UAT-004: Event Detail Page - Only BetPawa odds displayed

**Discovered:** 2026-02-02
**Phase/Plan:** 42-01-FIX8
**Severity:** Major
**Feature:** Event Detail page
**Description:** Event Detail page only showed BetPawa odds, not competitor odds (SportyBet, Bet9ja).
**Root Cause:** The `get_event()` endpoint and `_build_event_detail_response()` function didn't load or use CompetitorOddsSnapshot data.
**Expected:** Event detail page should show all bookmaker markets side-by-side
**Actual:** Only BetPawa markets displayed

**Resolved:** 2026-02-02 - Fixed in FIX9 (commit 20b1f87)
**Fix:**
1. Added `_build_competitor_market_detail()` and `_build_competitor_bookmaker_market_data()` helpers
2. Updated `_build_event_detail_response()` to accept and use competitor snapshots
3. Updated `get_event()` to load CompetitorOddsSnapshots via `_load_competitor_snapshots_for_events()`
**Result:** Event detail page now shows all 3 bookmakers with their full market data

---

*Phase: 42-validation-cleanup*
*Plan: 01-FIX5 through FIX9*
*Tested: 2026-02-02*
