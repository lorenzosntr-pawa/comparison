# UAT Issues: Phase 104 Mapping Editor

**Tested:** 2026-02-13
**Source:** .planning/phases/104-mapping-editor/104-01-SUMMARY.md through 104-04-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

### UAT-001: MappingCache not integrated with mappers (BLOCKER)

**Discovered:** 2026-02-13
**Phase/Plan:** 104 (all plans affected)
**Severity:** Blocker
**Feature:** Market mapping runtime integration
**Description:** The MappingCache created in Phase 101 merges code + DB mappings but is never used during actual scraping. The mappers (`map_sportybet_to_betpawa`, `map_bet9ja_odds_to_betpawa`) directly use hardcoded mappings from `market_mapping/mappings/market_ids.py` via `find_by_sportybet_id()` and `find_by_bet9ja_key()`.
**Expected:** User-created mappings in `user_market_mappings` table should be applied during scraping via the MappingCache lookup.
**Actual:** Mappers bypass MappingCache entirely, only using hardcoded MARKET_MAPPINGS. User mappings created via the editor are never applied.
**Repro:**
1. Create a mapping via POST /api/mappings
2. Verify it exists in user_market_mappings table
3. Run a scrape
4. Observe that the user mapping is not used - scraper still uses hardcoded mappings

**Impact:** The entire Phase 104 Mapping Editor creates mappings that have no effect on the system. User effort is wasted.

**Fix Required:**
- Refactor mappers to use MappingCache.find_by_sportybet_id() and MappingCache.find_by_bet9ja_key() instead of the module-level hardcoded lookup functions
- Ensure MappingCache is passed to or accessible from the mapping functions
- Alternative: Replace the module-level lookup functions to delegate to MappingCache singleton

---

### UAT-002: No way to edit existing mappings (BLOCKER)

**Discovered:** 2026-02-13
**Phase/Plan:** 104 (all plans affected)
**Severity:** Blocker
**Feature:** Mapping Editor access
**Description:** The Mapping Editor is only accessible from the High-Priority Unmapped section on the dashboard. There is no way to browse, view, or edit existing mappings (either code or user-created).
**Expected:** Users should be able to:
1. Browse all existing mappings
2. Click any mapping to view/edit it
3. Edit user-created mappings
4. Potentially override code mappings with user mappings
**Actual:** Editor requires an unmapped market ID to function. No navigation path to edit existing mappings.
**Repro:**
1. Go to /mappings dashboard
2. Observe no list of existing mappings
3. Try to access /mappings/editor without an unmapped ID - fails with 404

**Impact:** Users cannot review or fix existing mappings through the UI.

---

### UAT-003: UnmappedLogger ineffective due to comprehensive hardcoded mappings

**Discovered:** 2026-02-13
**Phase/Plan:** 102 (but affects 104 testing)
**Severity:** Major
**Feature:** Unmapped market discovery
**Description:** The unmapped_market_log table is empty because all markets being scraped from SportyBet/Bet9ja are covered by the 129 hardcoded mappings in MARKET_MAPPINGS. The UnmappedLogger (Phase 102) correctly captures markets that raise MappingError, but MappingError is never raised because the hardcoded mappings are comprehensive.
**Expected:** With 129 mappings covering major markets, this may be expected behavior. However, combined with UAT-001, even if new unmapped markets were discovered, the user-created fix would never be applied.
**Actual:** Empty unmapped_market_log, no high-priority items to test with.
**Repro:**
1. Query `SELECT COUNT(*) FROM unmapped_market_log` - returns 0
2. Check scrape runs completing successfully - 1680+ events scraped
3. No MappingError raised = no unmapped markets logged

---

## Resolved Issues

[None yet]

---

*Phase: 104-mapping-editor*
*Tested: 2026-02-13*
