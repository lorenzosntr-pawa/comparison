# UAT Issues: Phase 51 Plan 01

**Tested:** 2026-02-04
**Source:** .planning/phases/51-navigation-ux/51-01-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None - all issues resolved]

## Resolved Issues

### UAT-001: Sticky header does not stick

**Discovered:** 2026-02-04
**Resolved:** 2026-02-04 - Fixed in 51-01-FIX.md
**Commit:** 5ff2367, f368261
**Phase/Plan:** 51-01
**Severity:** Blocker
**Feature:** Sticky navigation header
**Description:** Header scrolls away with content instead of staying fixed at top of viewport
**Root cause:** `document.querySelector('main')` returned wrong element (outer SidebarInset instead of inner scrollable main)
**Fix:** Added `data-scroll-container` attribute to correct main element, updated all queries

### UAT-002: Scroll-to-top button does not appear

**Discovered:** 2026-02-04
**Resolved:** 2026-02-04 - Fixed in 51-01-FIX.md
**Commit:** f368261
**Phase/Plan:** 51-01
**Severity:** Major
**Feature:** Scroll-to-top floating button
**Description:** After scrolling 400+ pixels, no floating button appears
**Root cause:** Scroll listener attached to wrong element, so scrollTop was always 0
**Fix:** Updated querySelector to use `[data-scroll-container]`

### UAT-003: Scroll-to-top button position conflicts with API icon

**Discovered:** 2026-02-04
**Resolved:** 2026-02-04 - Fixed in 51-01-FIX.md
**Commit:** f368261
**Phase/Plan:** 51-01
**Severity:** Minor
**Feature:** Scroll-to-top floating button
**Description:** Button should be positioned higher because the API icon in the bottom-right corner would cover it
**Fix:** Changed button class from `bottom-6` to `bottom-20`

### UAT-004: Content layout shift when scrolling

**Discovered:** 2026-02-04
**Resolved:** 2026-02-04 - Fixed in 51-01-FIX.md
**Commit:** f368261
**Phase/Plan:** 51-01
**Severity:** Major
**Feature:** Layout stability
**Description:** Content jumps noticeably when scrolling, possibly related to placeholder mechanism failure
**Root cause:** Scroll listener not firing, so isHeaderStuck never became true, placeholder never rendered
**Fix:** Correct scroll container targeting enables placeholder mechanism to work

### UAT-005: No shadow effect on header

**Discovered:** 2026-02-04
**Resolved:** 2026-02-04 - Fixed in 51-01-FIX.md
**Commit:** f368261
**Phase/Plan:** 51-01
**Severity:** Cosmetic
**Feature:** Sticky header visual
**Description:** No shadow appears under the header for visual separation
**Root cause:** isHeaderStuck never became true because scroll events not received
**Fix:** Correct scroll container targeting enables shadow to appear when header is stuck

---

*Phase: 51-navigation-ux*
*Plan: 01*
*Tested: 2026-02-04*
*All issues resolved: 2026-02-04*
