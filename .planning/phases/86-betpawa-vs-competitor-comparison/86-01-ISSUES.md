# UAT Issues: Phase 86 Plan 01

**Tested:** 2026-02-11
**Source:** .planning/phases/86-betpawa-vs-competitor-comparison/86-01-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None]

## Deferred Issues

### UAT-002: Missing 1X2 margin data for Betpawa on many tournaments

**Discovered:** 2026-02-11
**Phase/Plan:** 86-01
**Severity:** Major
**Feature:** Multi-column margin table
**Status:** Deferred - Backend fix out of scope for UI fix plan

**Description:** Many tournaments show missing/blank 1X2 margin data in the Betpawa column.
**Expected:** Betpawa 1X2 margin should display for tournaments where 1X2 market data exists.
**Actual:** Betpawa 1X2 column is blank for a significant number of tournaments.
**Repro:** Navigate to Historical Analysis page and observe tournament cards - many have empty Betpawa 1X2 cells.

**Root Cause (Investigated):**
The Historical Analysis page uses `inline_odds` from the events list API, while the Tournament Detail page uses `markets_by_bookmaker` from the event detail API. The backend's `_build_inline_odds()` function at `src/api/routes/events.py:157` has a stricter filter:

```python
if outcomes:  # Only include if outcomes non-empty
    inline_odds.append(...)
```

When some events have 1X2 markets with empty/malformed outcomes JSON, they're skipped in `inline_odds` but included in the full market list. This causes a discrepancy between the two pages.

**Fix Options:**
1. Change `useTournaments` hook to fetch event details (like `useTournamentMarkets`) - expensive but consistent
2. Fix backend: include markets in `inline_odds` even if outcomes empty, with null margin
3. Fix data: investigate why some events have empty outcomes for 1X2

**Deferral Reason:** This requires backend changes to `_build_inline_odds()` in src/api/routes/events.py. Out of scope for the current UI fix plan. Will be addressed separately.

## Resolved Issues

### UAT-003: Bookmaker toggle buttons missing from Historical Analysis page

**Discovered:** 2026-02-11
**Resolved:** 2026-02-11
**Phase/Plan:** 86-01
**Severity:** Blocker
**Feature:** BookmakerFilter toggle component
**Resolution:** Integrated BookmakerFilter into FilterBar component and wired selectedBookmakers state through the page.
**Commit:** 717fa18

### UAT-001: Best Comp column doesn't change with bookmaker toggle selection

**Discovered:** 2026-02-11
**Resolved:** 2026-02-11
**Phase/Plan:** 86-01
**Severity:** Major
**Feature:** BookmakerFilter toggle + Multi-column margin table
**Resolution:** Made toggle selection visible by:
- Dynamic column header based on selected bookmakers (shows specific name when 1 selected)
- Hide competitor column entirely when no competitors selected
- Badge visibility tied to competitor selection
**Commit:** 717fa18

### UAT-004: Competitive badge only on 1X2 - user wants on all markets

**Discovered:** 2026-02-11
**Resolved:** 2026-02-11
**Phase/Plan:** 86-01
**Severity:** Minor
**Type:** Enhancement Request
**Feature:** CompetitiveBadge component
**Resolution:** Removed 1X2-only restriction. Competitive badge now appears on all market rows (1X2, O/U 2.5, BTTS, DC).
**Commit:** 717fa18

---

*Phase: 86-betpawa-vs-competitor-comparison*
*Plan: 01*
*Tested: 2026-02-11*
