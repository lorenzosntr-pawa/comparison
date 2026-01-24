# Fix Summary: 15-01-FIX2 Bet9ja Response Code + SR ID Investigation

**Plan:** 15-01-FIX2
**Type:** Fix
**Status:** Complete
**Duration:** ~15 min

## Issues Addressed

### UAT-002: Bet9ja fetch_event accepts wrong response code (FIXED)

**Root Cause:** Multiple issues discovered:

1. **Response code check** - Bug in `src/scraping/clients/bet9ja.py:96` - the `fetch_event` method checked for `"R": "D"` but the Bet9ja API returns `"R": "OK"` for the GetEvent endpoint.

2. **Event ID field mismatch** - The `_parse_bet9ja_event` was storing `event_data.get("C")` (short code like "1680") as `external_id`, but the GetEvent API requires `event_data.get("ID")` (full ID like "707096003").

3. **Existing data issue** - Even after fixing #2, existing database records still had the old "C" values, causing all fetch_event calls to fail.

**Fixes Applied:**

1. Changed response code check from `if result_code == "D":` to `if result_code in ("D", "OK"):` in `bet9ja.py:96`

2. Changed event ID parsing from `event_data.get("C", "")` to `event_data.get("ID", "")` in `competitor_events.py:230`

3. Modified `scrape_full_odds_for_events` to extract the correct event ID from `snapshot.raw_response["ID"]` for Bet9ja events, and update `event.external_id` with the correct value after successful fetch.

**Commits:**
- `e4eca77` fix(15-01-FIX2): accept "OK" response code in Bet9ja fetch_event
- `a963c9d` docs(15-01-FIX2): complete UAT fix plan (includes competitor_events.py parse fix)
- `d26d46e` fix(15-01-FIX2): use raw_response ID for Bet9ja full odds fetch

### UAT-003: SportyBet SR ID linking less complete than Bet9ja (INVESTIGATED)

**Investigation Result:** Not a code bug. Format handling is correct for all platforms:
- SportyBet: Extracts numeric ID from `sr:match:XXXXX` → stores just `XXXXX`
- Bet9ja: Uses `EXTID` directly → stores numeric string
- Betpawa: Uses `widgets[SPORTRADAR].id` → stores numeric string

**Root Cause:** Timing-related. The linking happens at scrape time via `_get_betpawa_event_by_sr_id()`. If betpawa events don't exist yet when competitor events are scraped, no link is created.

**Status:** Expected behavior given current architecture. Recommend addressing in Phase 16 (Cross-Platform Matching Enhancement) by re-linking events on subsequent scrapes.

### Additional Fix: SportyBet sourceType validation error

**Discovered during testing:** SportyBet market parsing was failing with Pydantic validation error:
```
sourceType Field required [type=missing, ...]
```

**Root Cause:** Some SportyBet markets don't include the `sourceType` field in their API response.

**Fix:** Made `source_type` field optional in `src/market_mapping/types/sportybet.py`:
```python
source_type: str | None = None
```

**Commit:** `d175081` fix(15-01-FIX2): make SportyBet sourceType field optional

## Files Modified

- `src/scraping/clients/bet9ja.py` (+3, -3) - Accept "OK" response code
- `src/scraping/competitor_events.py` (+15, -3) - Use raw_response ID for Bet9ja, update external_id
- `src/market_mapping/types/sportybet.py` (+2, -2) - Make sourceType optional

## Verification Results

After running `POST /api/scheduler/scrape-competitor-events`:
- **Bet9ja:** `events_with_full_odds=749, total_markets=55658, errors=0` ✓
- **SportyBet:** `events_with_full_odds=1060, markets=88297` ✓ (some tournaments failed due to session flushing - separate issue)

## Known Issues (Not Blocking)

**SQLAlchemy "Session is already flushing" warnings:** Some tournaments fail during concurrent scraping due to SQLAlchemy async session handling. This affects a subset of tournaments but doesn't prevent the main functionality from working. Should be addressed in a future phase with proper session management.

## Next Steps

1. Phase 15-01 verification should now pass for Bet9ja market capture
2. Phase 16 can address the SR ID re-linking for improved cross-platform matching
3. Future phase should address SQLAlchemy session concurrency for tournament scraping

---

*Phase: 15-full-event-scraping*
*Completed: 2026-01-24*
