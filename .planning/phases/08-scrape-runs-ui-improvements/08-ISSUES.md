# UAT Issues: Phase 8

**Tested:** 2026-01-21
**Source:** .planning/phases/08-scrape-runs-ui-improvements/08-01-SUMMARY.md, 08-02-SUMMARY.md, 08-03-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

None.

## Resolved Issues

### UAT-004: Dashboard widget progress bar not showing platform colors

**Discovered:** 2026-01-21
**Resolved:** 2026-01-21
**Phase/Plan:** 08-FIX2
**Severity:** Minor
**Feature:** Live Progress Visualization
**Description:** On the dashboard widget, the progress bar doesn't change color based on which platform is currently scraping (green→blue→orange). The detail page shows correct colors but the widget doesn't.
**Fix:** Changed color condition to only exclude overall completion (platform=null), allowing per-platform completion events to show platform colors.
**Commit:** 4fd4e60

### UAT-005: Dashboard widget status badge still has delay

**Discovered:** 2026-01-21
**Resolved:** 2026-01-21
**Phase/Plan:** 08-FIX2
**Severity:** Minor
**Feature:** Live Progress Visualization
**Description:** Status badge in the Recent Runs list still takes some time to update from "running" to "completed" after the progress bar shows completion.
**Fix:** Added optimistic cache update via queryClient.setQueryData() before refetch for instant UI update.
**Commit:** 4fd4e60

### UAT-006: SSE streaming doesn't save platform_timings

**Discovered:** 2026-01-21
**Resolved:** 2026-01-21
**Phase/Plan:** 08-FIX2
**Severity:** Major
**Feature:** Platform Breakdown on Detail Page
**Description:** SSE streaming endpoint didn't save platform_timings, causing "Platform Breakdown" card to show no data.
**Fix:** Added duration_ms to ScrapeProgress schema, accumulate platform_timings in /stream endpoint, save complete data in finally block.
**Commit:** cf152d8

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
