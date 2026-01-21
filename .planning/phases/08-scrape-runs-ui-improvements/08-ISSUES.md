# UAT Issues: Phase 8

**Tested:** 2026-01-21
**Source:** .planning/phases/08-scrape-runs-ui-improvements/08-01-SUMMARY.md, 08-02-SUMMARY.md, 08-03-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None - all issues resolved]

## Resolved Issues

### UAT-001: Progress bars missing platform-specific colors

**Discovered:** 2026-01-21
**Resolved:** 2026-01-21
**Phase/Plan:** 08-01
**Severity:** Minor
**Feature:** Live Progress Visualization
**Description:** Progress bars don't show different colors per platform. All bars appear the same color instead of Betpawa=green, SportyBet=blue, Bet9ja=orange as designed.
**Fix:** Added PLATFORM_PROGRESS_COLORS map to recent-runs.tsx and applied dynamic color classes to Progress component based on activeProgress.platform.
**Commit:** 383c2ea

### UAT-002: Status sync delay between progress bar and list

**Discovered:** 2026-01-21
**Resolved:** 2026-01-21
**Phase/Plan:** 08-01
**Severity:** Minor
**Feature:** Live Progress Visualization
**Description:** When progress bar shows completed status, the run still appears as "running" in the Recent Runs list for several seconds before updating to "completed" badge.
**Fix:** Changed from invalidateQueries to refetchQueries for immediate data sync on scrape completion.
**Commit:** 383c2ea

### UAT-003: Detail page missing live progress bars

**Discovered:** 2026-01-21
**Resolved:** 2026-01-21
**Phase/Plan:** 08-01
**Severity:** Minor
**Feature:** Detail Page Running Status
**Description:** The scrape run detail page only shows "in progress" text indicator but doesn't display the actual progress bars like the dashboard widget does. User wants consistency - progress bars should appear on detail page as well.
**Fix:** Replaced simple text indicator with visual per-platform progress bars showing all 3 platforms with completion status, active indicators, and pending state based on platform_timings.
**Commit:** 40bdc11

---

*Phase: 08-scrape-runs-ui-improvements*
*Tested: 2026-01-21*
