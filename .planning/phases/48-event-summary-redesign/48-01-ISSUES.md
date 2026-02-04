# UAT Issues: Phase 48 Plan 01

**Tested:** 2026-02-04
**Source:** .planning/phases/48-event-summary-redesign/48-01-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[All issues resolved]

## Resolved Issues

### UAT-006: Betpawa market count still includes markets without odds
**Resolved:** 2026-02-04 - Fixed in 48-01-FIX2.md
**Commit:** 0fce350
**Fix:** Added `buildDeduplicatedMarkets()` helper to merge split market records before counting. Summary section now uses same deduplication logic as market-grid.tsx.

---

### UAT-001: Betpawa market count too high in Market Coverage card
**Resolved:** 2026-02-04 - Fixed in 48-01-FIX.md
**Commit:** 423bfec
**Fix:** Added `marketHasOdds()` helper to filter markets before counting

---

### UAT-002: Category breakdown text too small in Competitive Position card
**Resolved:** 2026-02-04 - Fixed in 48-01-FIX.md
**Commit:** d10e0fb
**Fix:** Changed from `text-xs` to `text-sm` with 2-column grid layout

---

### UAT-003: Mapping Quality card UX could be improved
**Resolved:** 2026-02-04 - Fixed in 48-01-FIX.md
**Commit:** d10e0fb
**Fix:** Added badges for bookmaker counts with clearer visual hierarchy

---

### UAT-004: Font inconsistency across summary cards
**Resolved:** 2026-02-04 - Fixed in 48-01-FIX.md
**Commit:** d10e0fb
**Fix:** Applied consistent typography across all cards

---

### UAT-005: Remove Key Markets card
**Resolved:** 2026-02-04 - Fixed in 48-01-FIX.md
**Commit:** 9ca6924
**Fix:** Removed card and changed to 3-column layout

---

*Phase: 48-event-summary-redesign*
*Plan: 01*
*Tested: 2026-02-04*
*Re-verified: 2026-02-04 (1 new issue found)*
*UAT-006 resolved: 2026-02-04*
