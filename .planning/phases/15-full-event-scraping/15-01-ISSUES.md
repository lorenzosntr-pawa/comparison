# UAT Issues: Phase 15 Plan 01

**Tested:** 2026-01-24
**Source:** .planning/phases/15-full-event-scraping/15-01-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None]

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
