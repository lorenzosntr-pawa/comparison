# UAT Issues: Phase 94 Plan 01

**Tested:** 2026-02-12
**Source:** .planning/phases/94-coverage-page/94-01-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[All issues resolved]

## Resolved Issues

### UAT-001: Summary cards change values when country filter is applied

**Discovered:** 2026-02-12
**Phase/Plan:** 94-01
**Severity:** Major
**Feature:** Stable Tournament Summary Cards
**Description:** Summary cards show values that update when the country filter is changed, instead of showing stable totals for all tournaments.
**Expected:** Summary card totals should remain constant regardless of country filter selection
**Actual:** Card values change when country filter is applied
**Repro:**
1. Go to Coverage page
2. Note the summary card totals
3. Change the country filter
4. Observe card totals changing

**Resolved:** 2026-02-12 - Fixed in 94-01-FIX.md
**Commit:** 2624392
**Fix:** Added stable useMemo reference for allTournaments to prevent re-computation

### UAT-002: Bookmaker column values not aligned in tournament table

**Discovered:** 2026-02-12
**Phase/Plan:** 94-01
**Severity:** Minor
**Feature:** Tournament Table
**Description:** Values per tournament are not well aligned in the bookmakers column in the table.
**Expected:** Values should be properly aligned for visual consistency
**Actual:** Values appear misaligned
**Repro:**
1. Go to Coverage page
2. Look at tournament table bookmaker columns
3. Notice misalignment of values

**Resolved:** 2026-02-12 - Fixed in 94-01-FIX.md
**Commit:** 2102f73
**Fix:** Added justify-center and tabular-nums to PlatformCell for consistent alignment

---

*Phase: 94-coverage-page*
*Plan: 01*
*Tested: 2026-02-12*
