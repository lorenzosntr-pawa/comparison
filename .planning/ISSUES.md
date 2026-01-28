# Project Issues

## Open Enhancements

### ISS-002: Comprehensive market mapping needed
**Discovered:** Phase 7 UAT - 2026-01-21
**Type:** Enhancement
**Effort:** Large (dedicated phase)

**Description:**
Current market mapping library handles basic markets (1X2, O/U, BTTS, Handicaps) but many SportyBet and Bet9ja markets fail to map to Betpawa taxonomy. Console shows many "Could not map market" warnings.

**Impact:**
- Missing markets in event detail view
- Incomplete odds comparison for exotic markets
- Limits analysis capabilities

**Current state:**
- ~108 basic market mappings exist in `market_mapping/`
- Many market types still unmapped (Corners, Cards, Player Props, etc.)
- Mapping logic may need refinement for edge cases

**Required work:**
1. Audit all market types from each platform
2. Document Betpawa canonical market taxonomy
3. Expand mapping rules for missing market categories
4. Add unit tests for each mapped market type
5. Handle parameter variations (different line values, etc.)

**Resolution:** Create dedicated phase for comprehensive market mapping improvement.

---

## Closed Enhancements

### ISS-001: SportyBet/Bet9ja scraping not implemented (RESOLVED)
**Resolution:** Fixed in Phase 6.1 - Cross-platform scraping implemented

### ISS-003: Scheduler interval displays 2 minutes instead of settings value (RESOLVED)
**Resolution:** Fixed in Phase 33.1 - Job ID corrected from `scrape_odds` to `scrape_all_platforms`, index access replaced with named lookup
