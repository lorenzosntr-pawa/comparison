# Fix Summary: 15-01-FIX2 Bet9ja Response Code + SR ID Investigation

**Plan:** 15-01-FIX2
**Type:** Fix
**Status:** Complete
**Duration:** ~5 min

## Issues Addressed

### UAT-002: Bet9ja fetch_event accepts wrong response code (FIXED)

**Root Cause:** Bug in `src/scraping/clients/bet9ja.py:96` - the `fetch_event` method checked for `"R": "D"` but the Bet9ja API returns `"R": "OK"` for the GetEvent endpoint.

**Fix:** Changed line 96 from:
```python
if result_code == "D":
```
to:
```python
if result_code in ("D", "OK"):
```

Also updated error message on line 113 to reflect both valid codes.

**Commit:** `e4eca77` fix(15-01-FIX2): accept "OK" response code in Bet9ja fetch_event

### UAT-003: SportyBet SR ID linking less complete than Bet9ja (INVESTIGATED)

**Investigation Result:** Not a code bug. Format handling is correct for all platforms:
- SportyBet: Extracts numeric ID from `sr:match:XXXXX` → stores just `XXXXX`
- Bet9ja: Uses `EXTID` directly → stores numeric string
- Betpawa: Uses `widgets[SPORTRADAR].id` → stores numeric string

**Root Cause:** Timing-related. The linking happens at scrape time via `_get_betpawa_event_by_sr_id()`. If betpawa events don't exist yet when competitor events are scraped, no link is created.

**Status:** Expected behavior given current architecture. Recommend addressing in Phase 16 (Cross-Platform Matching Enhancement) by re-linking events on subsequent scrapes.

## Files Modified

- `src/scraping/clients/bet9ja.py` (+3, -3) - Accept "OK" response code

## Verification

After running `POST /api/scheduler/scrape-competitor-events`:
- Bet9ja should now return non-zero `markets` and `events_with_full_odds`
- Market data should be populated in `competitor_market_odds` table for Bet9ja

## Next Steps

1. Re-run `/gsd:verify-work 15-01` to confirm Bet9ja markets are now captured
2. Phase 16 can address the SR ID re-linking for improved cross-platform matching

---

*Phase: 15-full-event-scraping*
*Completed: 2026-01-24*
