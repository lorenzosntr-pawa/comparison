# UAT Issues: Phase 81 Interactive Chart

**Tested:** 2026-02-10
**Source:** .planning/phases/81-interactive-chart/81-01-FIX-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None]

## Resolved Issues

### UAT-001: Click-to-lock doesn't persist on any chart type

**Discovered:** 2026-02-10
**Resolved:** 2026-02-10
**Commit:** be6342e
**Phase/Plan:** 81
**Severity:** Blocker
**Feature:** Click-to-lock crosshair on OddsLineChart, MarginLineChart, MarketHistoryPanel

**Root Cause:** recharts onClick event provides `activeTooltipIndex` as a STRING (e.g., `'82'`), not a number as expected. The original code checked `typeof data.activeTooltipIndex === 'number'` which always returned false. Additionally, `activePayload` was undefined in onClick events.

**Fix:** Updated `use-chart-lock.ts` to parse `activeTooltipIndex` from either string or number format, and get the time value from chartData array using the parsed index instead of relying on activePayload.

### UAT-002: Comparison mode doesn't show all bookmakers

**Discovered:** 2026-02-10
**Resolved:** 2026-02-10
**Commit:** 37dc109
**Phase/Plan:** 81
**Severity:** Blocker
**Feature:** Multi-bookmaker tooltip comparison

**Root Cause:** Each bookmaker's data has different `captured_at` timestamps since scraping happens at different times. Without forward-fill, most time points only had data for one bookmaker.

**Fix:** Added forward-fill logic to both `OddsLineChart` and `MarginLineChart`. Now carries forward the last known value for each bookmaker so all lines are visible at every time point. Timestamps are bucketed to the nearest minute for merging.

---

*Phase: 81-interactive-chart*
*Tested: 2026-02-10*
*All issues resolved: 2026-02-10*
