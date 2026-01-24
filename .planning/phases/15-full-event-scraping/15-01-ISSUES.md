# UAT Issues: Phase 15 Plan 01

**Tested:** 2026-01-24
**Source:** .planning/phases/15-full-event-scraping/15-01-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

### UAT-002: Bet9ja competitor events have 0 markets captured

**Discovered:** 2026-01-24
**Phase/Plan:** 15-01
**Severity:** Major
**Feature:** Bet9ja event scraping
**Description:** Despite scraping 667 Bet9ja event snapshots successfully, the response shows 0 markets and 0 events_with_full_odds. SportyBet captured 39,690 markets from 674 events, but Bet9ja has none.
**Expected:** Bet9ja events should have market odds captured similar to SportyBet (50-100+ markets per event)
**Actual:** bet9ja.markets = 0, bet9ja.events_with_full_odds = 0 in API response
**Repro:**
1. Call POST /api/scheduler/scrape-competitor-events
2. Observe bet9ja results in response
3. Check competitor_market_odds table for bet9ja snapshots

**Root Cause Identified:**
Bug in `src/scraping/clients/bet9ja.py:96` - the `fetch_event` method expects `"R": "D"` for success, but the Bet9ja API actually returns `"R": "OK"`. This causes every individual event fetch to fail with ApiError (silently caught at debug level).

**Fix:** Change `if result_code == "D":` to `if result_code in ("D", "OK"):`

### UAT-003: SportyBet SR ID linking less complete than Bet9ja

**Discovered:** 2026-01-24
**Phase/Plan:** 15-01
**Severity:** Minor
**Feature:** SportRadar ID cross-platform matching
**Description:** SportyBet events have fewer betpawa_event_id links than Bet9ja, even when the same event (same SportRadar ID) is linked in Bet9ja but not in SportyBet.
**Expected:** If an event has a SportRadar ID that matches a betpawa event, both platforms should link to it
**Actual:** Bet9ja links more events to betpawa than SportyBet for same SR IDs
**Repro:**
1. Query competitor_events WHERE betpawa_event_id IS NOT NULL GROUP BY source
2. Compare counts between sportybet and bet9ja
3. Find specific SR IDs linked in bet9ja but not sportybet

**Investigation Result (15-01-FIX2):**
Code analysis shows correct format handling:
- SportyBet: Extracts numeric ID from `sr:match:XXXXX` → stores just `XXXXX`
- Bet9ja: Uses `EXTID` directly → stores numeric string
- Betpawa: Uses `widgets[SPORTRADAR].id` → stores numeric string
- Lookup query is correct: `Event.sportradar_id == sportradar_id`

**Root Cause:** Timing-related. Linking happens at scrape time via `_get_betpawa_event_by_sr_id()`. If betpawa events don't exist yet when competitor events are scraped, no link is created. This explains the discrepancy if SportyBet/Bet9ja are scraped in different order relative to betpawa scraping.

**Status:** Expected behavior, not a bug. Consider re-linking on subsequent scrapes in Phase 16 (Cross-Platform Matching Enhancement).

## Resolved Issues

### UAT-001: Competitor event scraping only captures main markets from tournament listings

**Discovered:** 2026-01-24
**Resolved:** 2026-01-24 (15-01-FIX)
**Phase/Plan:** 15-01
**Severity:** Major
**Feature:** Competitor Event Scraping / Odds Capture
**Description:** Current implementation scrapes odds from tournament listing pages, which only include main markets (1X2, Over/Under, BTTS). Individual event pages contain many more markets that are not being captured.
**Expected:** All available markets from competitor events should be scraped, matching the depth of data available on individual event pages.
**Actual:** Only main markets from tournament listings are captured. Dozens of other market types (player props, correct score, halftime/fulltime, etc.) are missing.
**Repro:**
1. Call POST /api/scheduler/scrape-competitor-events
2. Check competitor_odds_snapshots for any event
3. Note only main markets present vs. viewing same event on competitor website
**Resolution:** Added full market depth fetching via individual event endpoints. After tournament listing scrape, service now calls fetch_event() for each event to get complete market data (50-100+ markets vs 3-8).

---

*Phase: 15-full-event-scraping*
*Plan: 01*
*Tested: 2026-01-24*
