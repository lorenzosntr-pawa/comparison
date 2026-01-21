# Project Issues

## Open Enhancements

### ISS-001: SportyBet/Bet9ja scraping not implemented
**Discovered:** Phase 6 - 2026-01-21
**Type:** Critical Bug / Missing Feature
**Effort:** Medium

**Description:**
The scraping orchestrator has stub implementations for SportyBet and Bet9ja that return empty arrays. Only BetPawa scraping is functional.

**Impact:**
- No cross-platform event matching possible
- Dashboard shows 0 events for SportyBet and Bet9ja
- Core value proposition (odds comparison) blocked

**Location:** `src/scraping/orchestrator.py:188-199`

**Required work:**
1. SportyBet: Query DB for events with SportRadar IDs, fetch from SportyBet API via `fetch_event(sportradar_id)`
2. Bet9ja: Use EXTID field (contains SportRadar IDs) - can fetch by tournament then match via EXTID
3. Store competitor events and link to base events via SportRadar ID

**Key insight:** All three platforms use SportRadar IDs:
- BetPawa: `widgets[type=SPORTRADAR].id`
- SportyBet: `eventId` parameter accepts SportRadar ID directly
- Bet9ja: `EXTID` field contains SportRadar ID

**Resolution:** Will be addressed in Phase 6.1 (inserted urgent phase)

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
- ~111 basic market mappings exist in `market_mapping/`
- Many market types still unmapped (Corners, Cards, Player Props, etc.)
- Mapping logic may need refinement for edge cases

**Required work:**
1. Audit all market types from each platform
2. Document Betpawa canonical market taxonomy
3. Expand mapping rules for missing market categories
4. Add unit tests for each mapped market type
5. Handle parameter variations (different line values, etc.)

**Resolution:** Create Phase 9 (or later) for comprehensive market mapping improvement.

---

## Closed Enhancements

### ISS-001: SportyBet/Bet9ja scraping not implemented (RESOLVED)
**Resolution:** Fixed in Phase 6.1 - Cross-platform scraping implemented
