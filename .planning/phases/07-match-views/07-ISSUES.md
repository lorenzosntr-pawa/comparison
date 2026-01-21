# UAT Issues: Phase 7 Match Views

**Tested:** 2026-01-21
**Source:** .planning/phases/07-match-views/07-02-FIX2-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

### UAT-005: BetPawa scraper returns 0 events

**Discovered:** 2026-01-21
**Phase/Plan:** 07-02-FIX2
**Severity:** Blocker
**Feature:** BetPawa scraping
**Description:** After FIX2 changes, BetPawa scraper completes quickly but returns 0 events. The parallel fetching refactor appears to have broken the data retrieval entirely.
**Expected:** BetPawa scraper returns events with odds data
**Actual:** POST /api/scrape returns `{"events_count": 0}` for betpawa platform, while SportyBet and Bet9ja work correctly
**Repro:**
1. Call POST /api/scrape via Swagger UI (/docs)
2. Observe response shows betpawa `events_count: 0`
3. SportyBet and Bet9ja return events correctly

**Previous state:** Before FIX2, BetPawa scraper was slow but did return some events (timed out partway through).

### UAT-006: Color coding applied to wrong columns

**Discovered:** 2026-01-21
**Phase/Plan:** 07-02-FIX2
**Severity:** Major
**Feature:** Odds comparison color coding
**Description:** The green/red color coding is now visible but applied to competitor odds (SportyBet/Bet9ja columns) instead of the Betpawa column. Colors should indicate Betpawa's competitive position, so they should be on Betpawa's odds.
**Expected:** Betpawa odds cells colored green (when higher/better) or red (when lower/worse) compared to competitors
**Actual:** Competitor columns show colors instead of Betpawa column
**Repro:**
1. Navigate to Matches page
2. Find events with odds from multiple bookmakers
3. Observe colors appear on SportyBet/Bet9ja columns, not Betpawa

### UAT-002: Most Betpawa events missing odds

**Discovered:** 2026-01-21
**Phase/Plan:** 07-02-FIX
**Severity:** Blocker
**Feature:** Betpawa odds display
**Description:** Betpawa shows odds for very few events (<20%) while SportyBet and Bet9ja show odds correctly. Since Betpawa is the primary bookmaker for comparison, this blocks the core purpose of the tool.
**Expected:** Betpawa odds visible for all/most events in match list
**Actual:** Most Betpawa events show no odds (dashes)
**Repro:**
1. Navigate to Matches page
2. Observe most rows have no Betpawa odds despite SportyBet/Bet9ja having data

**Root Cause (Investigated):**
BetPawa scraper times out before completing full scrape.

The scraper flow:
1. Discovers ~40 competitions
2. For EACH competition, fetches event list
3. For EACH event, makes individual API call to fetch full event + markets
4. Has 0.1s rate-limit delay per event

With 1090+ events × (API call + 0.1s) = exceeds 300s default timeout.

Database evidence:
- BetPawa: 1090 event links, only 40 snapshots (one competition worth)
- SportyBet/Bet9ja: 50k+ snapshots each
- ScrapeError table shows `TimeoutError` for betpawa

**Fix Required:**
Batch the BetPawa market fetching or use competition-level events endpoint with markets included (if available), or increase timeout and reduce rate limiting.

### UAT-004: Scraper significantly slower after Phase 7.1

**Discovered:** 2026-01-21
**Phase/Plan:** 07.1-01
**Severity:** Major
**Feature:** Scraping performance
**Description:** The scraper became significantly slower after Phase 7.1 changes. Before 7.1, scraping completed reasonably fast. Now it times out on BetPawa.
**Expected:** Scraping completes within reasonable time (similar to pre-7.1)
**Actual:** BetPawa scraping times out, overall scraping is much slower
**Repro:**
1. Trigger a scrape via the scheduler or API
2. Observe BetPawa times out

**Root Cause (Investigated):**
Phase 7.1 added individual event fetching to get full market data:
- `_scrape_betpawa_competition()` now calls `client.fetch_event(event_id)` for EACH event
- 0.1s delay per event for rate limiting
- With 1000+ events across competitions: 1000+ API calls + 100+ seconds in delays

Before 7.1, only the events list was fetched (one API call per competition), not individual event details.

**Fix Required:**
Either:
1. Use parallel fetching with semaphore (like SportyBet) instead of sequential
2. Check if events list endpoint can include markets data
3. Skip individual fetches for events already in DB with recent snapshot

### UAT-003: Color coding not displaying

**Discovered:** 2026-01-21
**Phase/Plan:** 07-02-FIX
**Severity:** Major
**Feature:** Odds comparison color coding
**Description:** Cells do not show green/red color coding to indicate where Betpawa is better or worse than competitors. All cells appear neutral.
**Expected:** Green background when Betpawa odds are higher (better), red when lower (worse)
**Actual:** No color differentiation visible
**Repro:**
1. Navigate to Matches page
2. Find event with Betpawa odds visible
3. Observe cell backgrounds are neutral (no green/red)

**Root Cause (Investigated):**
Dynamic Tailwind class names not compiled by JIT.

The code at `match-table.tsx:86-89` uses:
```tsx
bgClass = `bg-green-500/${opacityLevel}`  // e.g., bg-green-500/10
```

Tailwind's JIT compiler needs **full class names at build time**. String interpolation creates dynamic classes that are never included in the CSS output.

**Fix Required:**
Use a static lookup object with pre-defined opacity classes, or use inline styles for dynamic opacity values.

## Resolved Issues

### UAT-001: Match list table doesn't display inline odds columns

**Discovered:** 2026-01-21 during Phase 7.1 verification
**Resolved:** 2026-01-21 via 07-02-FIX.md
**Phase/Plan:** 07-02
**Severity:** Major
**Feature:** Match list view inline odds display
**Description:** The match list table did not display inline odds columns (1X2, O/U 2.5, BTTS) even though the API returned `inline_odds` data correctly.
**Root cause:** Frontend MARKET_CONFIG used incorrect market IDs (1, 18, 29) instead of Betpawa taxonomy IDs (3743, 5000, 3795).
**Resolution:** Updated frontend MARKET_CONFIG and AVAILABLE_COLUMNS in match-table.tsx and use-column-settings.ts to use Betpawa market IDs.
**Commit:** da806ee

---

*Phase: 07-match-views*
*Plan: 02*
*Tested: 2026-01-21*
