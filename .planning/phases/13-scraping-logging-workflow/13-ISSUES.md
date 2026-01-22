# UAT Issues: Phase 14

**Tested:** 2026-01-22
**Source:** .planning/phases/14-scraping-logging-workflow/14-04-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None - all issues resolved in 14-FIX]

## Resolved Issues

### UAT-001: Platform status icons show wrong status for SportyBet and Bet9ja
**Resolved:** 2026-01-22 in 14-FIX
**Resolution:** No code change needed - root cause was UAT-002 cascade scrapes corrupting platform_timings data. Fix to UAT-002 resolves this.

### UAT-002: Detail page triggers unintended new scrapes causing cascade failures
**Resolved:** 2026-01-22 in 14-FIX
**Resolution:** Changed useScrapeProgress hook to use observe endpoint `/api/scrape/runs/{id}/progress` instead of `/api/scrape/stream` which creates new scrapes.
**Commit:** bbcace7

### UAT-003: SportyBet Pydantic schema validation errors
**Resolved:** 2026-01-22 in 14-FIX
**Resolution:** Made `far_near_odds`, `root_market_id`, `node_market_id` optional in SportyBet Pydantic schemas to handle API format changes.
**Commit:** f096612

---

*Phase: 14-scraping-logging-workflow*
*Tested: 2026-01-22*
