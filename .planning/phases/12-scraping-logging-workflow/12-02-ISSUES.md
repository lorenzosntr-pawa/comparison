# UAT Issues: Phase 14 Plan 02

**Tested:** 2026-01-22
**Source:** .planning/phases/14-scraping-logging-workflow/14-02-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None - all issues resolved]

## Resolved Issues

### UAT-003: SSE disconnect causes scrape to hang permanently
**Resolved:** 2026-01-22 - Fixed in 14-02-FIX2.md
**Commit:** 07ce8fa

**Discovered:** 2026-01-22
**Phase/Plan:** 14-02
**Severity:** Blocker
**Feature:** SSE streaming during scrape
**Description:** When the SSE connection is interrupted during a scrape, the scrape gets stuck in "running" state forever.
**Fix:** Spawn scrape as asyncio background task with independent DB session. SSE endpoint subscribes to progress_registry broadcaster.

### UAT-004: SportyBet scraping should use SportRadar IDs from current scrape session
**Resolved:** 2026-01-22 - Fixed in 14-02-FIX2.md
**Commit:** 766a325

**Discovered:** 2026-01-22
**Phase/Plan:** 14-02
**Severity:** Major
**Feature:** Cross-platform scraping workflow
**Description:** SportyBet scraping should use fresh SportRadar IDs from current BetPawa scrape session.
**Fix:** Collect SportRadar IDs during BetPawa scrape, pass to _scrape_sportybet() and _scrape_bet9ja() via new parameter.

### UAT-001: Phase sequence shows SportyBet before BetPawa
**Resolved:** 2026-01-22 - Fixed in 14-02-FIX.md
**Commit:** 2d47cb6

**Discovered:** 2026-01-22
**Phase/Plan:** 14-02
**Severity:** Minor
**Feature:** Phase emissions/logging
**Description:** The scrape logs show SportyBet processing before BetPawa, but the expected order should be BetPawa first (since it's the canonical source for SportRadar IDs).
**Expected:** Phase sequence: INITIALIZING → BETPAWA → SPORTYBET → BET9JA → COMPLETED
**Actual:** Phase sequence starts with SPORTYBET before BETPAWA
**Fix:** Reordered Platform enum to put BETPAWA first

### UAT-002: SportyBet market parsing validation errors spam logs
**Resolved:** 2026-01-22 - Fixed in 14-02-FIX.md
**Commit:** ae0d1c3

**Discovered:** 2026-01-22
**Phase/Plan:** 14-02
**Severity:** Minor
**Feature:** Structured logging output
**Description:** Many warning logs about SportyBet market parsing failures due to missing `lastOddsChangeTime` field (and sometimes `group`, `groupId`, `title`, `name`). These warnings obscure useful log output.
**Expected:** Clean log output with minimal noise, or suppressed/aggregated warnings for known schema mismatches
**Actual:** Dozens of individual warning lines for each market that fails validation, making logs hard to read
**Fix:** Made group, group_id, title, name, last_odds_change_time optional in SportybetMarket schema

---

*Phase: 14-scraping-logging-workflow*
*Plan: 02*
*Tested: 2026-01-22*
