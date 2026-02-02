# UAT Issues: Phase 44 Plan 02

**Tested:** 2026-02-02
**Source:** .planning/phases/44-high-priority-market-mappings/44-02-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

### UAT-001: Bet9ja Home/Away O/U First Half markets not mapped

**Discovered:** 2026-02-02
**Phase/Plan:** 44-02
**Severity:** Major
**Feature:** Market mapping for Bet9ja
**Description:** Markets like "Total Score Over/Under | First Half | {home} 0.5" show BetPawa and SportyBet odds but Bet9ja shows "-" (missing). User confirmed these markets ARE available on Bet9ja's website.
**Expected:** Bet9ja odds should appear in the comparison view for these markets
**Actual:** Bet9ja column shows "-" while BetPawa and SportyBet show odds
**Markets affected:**
- Total Score Over/Under | First Half | {home} 0.5
- Total Score Over/Under | First Half | {home} 1.5
- Total Score Over/Under | First Half | {away} 0.5
- Total Score Over/Under | First Half | {away} 1.5

**ROOT CAUSE IDENTIFIED:**
Bet9ja uses **inconsistent suffix patterns** for HAOU markets:
- Full Time (HAOU): `OH`, `UH`, `OA`, `UA` (Over Home, Under Home, etc.)
- Half Time (HA1HOU, HA2HOU): `HO`, `HU`, `AO`, `AU` (Home Over, Home Under, etc.)

**FIX:** Modified `_map_haou_combined_market()` to check for **both** suffix patterns and use whichever is present.

### UAT-002: Bet9ja Home/Away O/U Second Half markets not mapped

**Discovered:** 2026-02-02
**Phase/Plan:** 44-02
**Severity:** Major
**Feature:** Market mapping for Bet9ja
**Description:** Same issue as UAT-001 but for second half markets. User confirmed these markets ARE available on Bet9ja's website.
**Expected:** Bet9ja odds should appear in the comparison view for these markets
**Actual:** Bet9ja column shows "-" while BetPawa and SportyBet show odds
**Markets affected:**
- Total Score Over/Under | Second Half | {home} 0.5
- Total Score Over/Under | Second Half | {home} 1.5
- Total Score Over/Under | Second Half | {away} 0.5
- Total Score Over/Under | Second Half | {away} 1.5
- Total Score Over/Under | Second Half | {away} 2.5

**ROOT CAUSE:** Same as UAT-001 - reversed outcome suffixes in `_map_haou_combined_market()`

### UAT-003: Duplicate market rows with single-bookmaker odds (NEW)

**Discovered:** 2026-02-02
**Phase/Plan:** 44-02 (discovered after HAOU fix)
**Severity:** Major
**Feature:** Market comparison display
**Description:** After fixing HAOU mapping, some markets appear as multiple duplicate rows, each showing odds from only one bookmaker instead of being merged into a single row with all bookmakers.
**Expected:** Each market should appear once with odds from all bookmakers side-by-side
**Actual:** Same market appears multiple times, each row showing odds from different bookmaker
**Example:** Home O/U Full Time 0.5 shows as 3 separate rows instead of 1 merged row
**Likely cause:** Frontend market merging logic not recognizing these as the same market across bookmakers
**Note:** This is a UI merging issue, not a mapping issue. The data is correct in the database.

### UAT-004: New 44-02 markets not visible in UI (inconclusive)

**Discovered:** 2026-02-02
**Phase/Plan:** 44-02
**Severity:** Minor
**Feature:** New market mappings visibility
**Description:** User checked multiple events but couldn't find the new markets added in 44-02 (Home No Bet, Away No Bet, First Goal, BTTS 2+, etc.). Uncertain if this is a mapping bug or simply that current scraped events don't include these market types.
**Expected:** New markets should appear when events have them
**Actual:** Markets not found in checked events
**Note:** Automated tests pass (32 mapper tests, 25 lookup tests), suggesting code is correct. May need investigation to determine if issue is data availability vs mapping bug.

## Resolved Issues

### UAT-001 & UAT-002: Bet9ja Home/Away O/U Half markets not mapped

**Resolved:** 2026-02-02
**Fix:** Modified `_map_haou_combined_market()` to check for **both** suffix patterns (OH/UH/OA/UA and HO/HU/AO/AU) and use whichever is present
**Commit:** `a8a783c`
**Verification:** Unit tests pass (83/83), manual mapping test confirms HAOU, HA1HOU, HA2HOU all map correctly

---

*Phase: 44-high-priority-market-mappings*
*Plan: 02*
*Tested: 2026-02-02*
