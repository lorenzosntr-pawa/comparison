# UAT Issues: Phase 42 Plan 01

**Tested:** 2026-01-29
**Source:** .planning/phases/42-validation-cleanup/42-01-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None]

## Resolved Issues

### UAT-001: ScrapeProgress UnboundLocalError causes scrape failure ✓

**Discovered:** 2026-01-29
**Resolved:** 2026-01-29 (42-01-FIX)
**Phase/Plan:** 42-01
**Severity:** Blocker
**Feature:** Scheduled scraping / EventCoordinator integration
**Description:** When scraping runs, it fails with `UnboundLocalError: cannot access local variable 'ScrapeProgress' where it is not associated with a value` at jobs.py line 143.
**Root Cause:** Redundant local import of `ScrapeProgress` at line 208 inside exception handler caused Python to treat all references as local variables.
**Fix:** Removed redundant import. Module-level import at line 15 is sufficient.
**Commit:** bc1a67d

### UAT-002: BetPawa events not discovered (betpawa=0) ✓

**Discovered:** 2026-01-29
**Resolved:** 2026-01-29 (42-01-FIX)
**Phase/Plan:** 42-01
**Severity:** Blocker
**Feature:** Event discovery
**Description:** Tournament discovery shows betpawa=0 events while bet9ja=1149 and sportybet=1227.
**Root Cause:** BetPawa API structure changed from `regions[]` to `withRegions[0].regions[]`, and competition ID is now nested at `competition.id` instead of direct `id`.
**Fix:** Updated `_discover_betpawa()` to parse the new API structure. Added info-level logging for discovery tracing.
**Commit:** 84b7995

### UAT-003: Batch processing slow (~30-40 seconds per batch) ✓

**Discovered:** 2026-01-29
**Resolved:** 2026-01-29 (42-01-FIX)
**Phase/Plan:** 42-01
**Severity:** Major
**Feature:** Batch storage performance
**Description:** Each batch of 50 events takes ~30-40 seconds between batch completions.
**Root Cause:** Individual `db.flush()` calls per snapshot (100+ round trips per batch).
**Fix:** Optimized to single-flush pattern: add all snapshots, single flush, then add all markets. Expected 3-4x improvement.
**Commit:** 73b1cfd

---

*Phase: 42-validation-cleanup*
*Plan: 01*
*Tested: 2026-01-29*
*Fixed: 2026-01-29*
