# Market Mapping Improvement Report

*Generated: 2026-02-03*
*Comparing Phase 43 baseline to Phase 45 post-fix audit*

## Executive Summary

**Phase 44 fixes have improved mapping success rates:**
- SportyBet: 47.3% → 52.2% (+4.9 percentage points)
- Bet9ja: 36.1% → 40.5% (+4.4 percentage points)

**Key wins:**
- UNKNOWN_PARAM_MARKET nearly eliminated (97.7% reduction for SportyBet, 100% for Bet9ja)
- TMGHO/TMGAW outcome mapping issues fully resolved
- 1X2OU, DCOU, 37, 547 combo markets now mapping correctly

**Recommendation:** Phase 46 needed for remaining HIGH priority UNKNOWN_MARKET gaps

---

## 1. Platform Success Rate Changes

| Platform | Phase 43 Baseline | Phase 45 Current | Change |
|----------|------------------|------------------|--------|
| SportyBet | 47.3% (8,323/17,605) | 52.2% (19,962/38,247) | **+4.9%** |
| Bet9ja | 36.1% (5,580/15,465) | 40.5% (13,371/33,048) | **+4.4%** |

*Note: Phase 45 analyzed 199 events (vs 100 in Phase 43) for a larger, more representative sample.*

---

## 2. Error Code Improvements

### SportyBet Error Breakdown

| Error Code | Phase 43 | Phase 45 | Per-100-Events* | Change |
|------------|----------|----------|-----------------|--------|
| UNKNOWN_MARKET | 8,305 | 13,627 | ~6,800 | Slight improvement |
| UNKNOWN_PARAM_MARKET | 834 | 38 | ~19 | **-97.7%** |
| NO_MATCHING_OUTCOMES | 128 | 846 | ~423 | More markets encountered |
| UNSUPPORTED_PLATFORM | 15 | 3,774 | ~1,890 | Markets now properly classified |

### Bet9ja Error Breakdown

| Error Code | Phase 43 | Phase 45 | Per-100-Events* | Change |
|------------|----------|----------|-----------------|--------|
| UNKNOWN_MARKET | 8,553 | 17,235 | ~8,600 | Stable (larger sample) |
| UNKNOWN_PARAM_MARKET | 690 | 0 | 0 | **-100%** |
| NO_MATCHING_OUTCOMES | 615 | 800 | ~400 | **-35%** |
| UNSUPPORTED_PLATFORM | 27 | 1,642 | ~820 | Markets now properly classified |

*\*Normalized to 100 events for fair comparison*

**Key insight:** UNKNOWN_PARAM_MARKET completely eliminated for Bet9ja and reduced by 97.7% for SportyBet. This validates that Phase 44-03's combo market parameter handling was highly effective.

---

## 3. Phase 44 Fix Verification

### 44-01: TMGHO/TMGAW NO_MATCHING_OUTCOMES Fix

| Market | Phase 43 Status | Phase 45 Status | Result |
|--------|-----------------|-----------------|--------|
| TMGHO | NO_MATCHING_OUTCOMES (99 occurrences) | Not in error list | **FIXED** |
| TMGAW | NO_MATCHING_OUTCOMES (99 occurrences) | Not in error list | **FIXED** |

**Verification:** Team goals home/away markets now mapping correctly to BetPawa equivalents.

### 44-02: 20 New MarketMapping Entries

| Market | Phase 43 Error | Phase 45 Error | Result |
|--------|----------------|----------------|--------|
| HOMENOBET (bet9ja) | UNKNOWN_MARKET | UNSUPPORTED_PLATFORM | **Recognized** (no BetPawa equivalent) |
| AWAYNOBET (bet9ja) | UNKNOWN_MARKET | UNSUPPORTED_PLATFORM | **Recognized** (no BetPawa equivalent) |
| 1STGOAL (bet9ja) | UNKNOWN_MARKET | UNSUPPORTED_PLATFORM | **Recognized** (no BetPawa equivalent) |
| Home No Bet `12` (sportybet) | UNKNOWN_MARKET | UNSUPPORTED_PLATFORM | **Recognized** (no BetPawa equivalent) |
| Away No Bet `13` (sportybet) | UNKNOWN_MARKET | UNSUPPORTED_PLATFORM | **Recognized** (no BetPawa equivalent) |
| 1st Goal `8` (sportybet) | UNKNOWN_MARKET | UNSUPPORTED_PLATFORM | **Recognized** (no BetPawa equivalent) |

**Verification:** Markets are now correctly classified. Those showing UNSUPPORTED_PLATFORM are intentionally not mapped because BetPawa doesn't offer equivalent markets - this is correct behavior.

### 44-03: Combo Market Parameter Handling

| Market | Phase 43 Error | Phase 45 Status | Result |
|--------|----------------|-----------------|--------|
| 1X2OU (bet9ja) | UNKNOWN_PARAM_MARKET (348) | Not in error list | **FIXED** |
| DCOU (bet9ja) | UNKNOWN_PARAM_MARKET (342) | Not in error list | **FIXED** |
| 37 (sportybet) | UNKNOWN_PARAM_MARKET (264) | Not in error list | **FIXED** |
| 547 (sportybet) | UNKNOWN_PARAM_MARKET (264) | Not in error list | **FIXED** |
| 36 (sportybet) | UNKNOWN_PARAM_MARKET (66) | Not in error list | **FIXED** |

**Verification:** All combo markets with O/U line parameters now correctly routing through the over/under handler. The 97.7-100% reduction in UNKNOWN_PARAM_MARKET errors validates this fix.

---

## 4. Remaining Gap Analysis

### Top 10 UNKNOWN_MARKET by Frequency

| Rank | Market | Platform | Frequency | Category | Notes |
|------|--------|----------|-----------|----------|-------|
| 1 | OUA | bet9ja | 1,928 | Uncategorized | Needs investigation - high impact |
| 2 | 800117 | sportybet | 952 | Player To Be Booked | Player prop - may not have BetPawa equiv |
| 3 | 3COMBO1 | bet9ja | 472 | Combo Markets | Multi-result combo |
| 4 | 60180 | sportybet | 464 | Early Goals O/U | May have BetPawa equivalent |
| 5 | 819 | sportybet | 405 | HT/FT & 1H O/U | Complex combo market |
| 6 | CHANCEMIXOU | bet9ja | 386 | Uncategorized | Needs investigation |
| 7 | 1X2MULTI* | bet9ja | 197 each | Match Result Combos | Multiple result combinations |
| 8 | DCMULTI* | bet9ja | 197 each | DC Combos | Double chance combinations |
| 9 | 775/776/777 | sportybet | 295 each | Player Props | Player goals/shots/SOG |
| 10 | 1191 | sportybet | 198 | Player Carded | Player prop |

### UNKNOWN_PARAM_MARKET Status

| Platform | Count | Status |
|----------|-------|--------|
| SportyBet | 38 | Only corner range markets (169, 182) |
| Bet9ja | 0 | **Fully resolved** |

Corner range markets (169, 182) are the only remaining UNKNOWN_PARAM_MARKET errors - these are niche markets with limited impact.

### NO_MATCHING_OUTCOMES Analysis

| Market | Platform | Frequency | Issue |
|--------|----------|-----------|-------|
| 818 | sportybet | 540 | HT/FT & O/U - outcome structure mismatch |
| HTFTOU | bet9ja | 540 | HT/FT & O/U - same as above |
| 551 | sportybet | 148 | Multiscores - complex outcome structure |
| HTFTCS | bet9ja | 124 | HT/FT Correct Score - outcome mapping |
| HA1HOU/HA2HOU | bet9ja | 50/41 | Half Asian O/U - outcome structure |
| 46 | sportybet | 138 | HT/FT Correct Score - outcome mapping |
| NCORN | bet9ja | 35 | Corner markets - outcome structure |

These markets are RECOGNIZED but have outcome structure mismatches. Some may be fixable by analyzing outcome formats.

### UNSUPPORTED_PLATFORM (Correct Behavior)

Many markets now correctly show as UNSUPPORTED_PLATFORM:
- Markets that BetPawa doesn't offer (home no bet, away no bet, 1st goal)
- Platform-specific prop markets
- Combo markets without BetPawa equivalents

These are NOT bugs - they're correctly classified as markets we can't map.

---

## 5. Assessment & Recommendation

### Current State
- **SportyBet:** 52.2% mapped (above 50% threshold)
- **Bet9ja:** 40.5% mapped (below 50% threshold)
- **Combined improvement:** +4.6% average

### Recommendation: Phase 46 for Remaining HIGH Priority Gaps

**Rationale:**
- Success rates in 50-70% range indicate more work needed
- Several high-frequency UNKNOWN_MARKET gaps remain
- NO_MATCHING_OUTCOMES issues may be fixable with outcome analysis

**Phase 46 Priorities:**

1. **OUA (bet9ja)** - 1,928 occurrences - investigate what market this represents
2. **CHANCEMIXOU/CHANCEMIX/CHANCEMIXN (bet9ja)** - ~740 combined - investigate
3. **60180 (sportybet)** - 464 occurrences - Early Goals O/U - likely mappable
4. **NO_MATCHING_OUTCOMES fixes** - 818, HTFTOU, 551 - analyze outcome structures
5. **CAH/CAHH/CAH2 (bet9ja)** - ~300 combined - investigate Asian handicap variants

**Skip for Phase 46:**
- Player props (800117, 775-780, 1191) - BetPawa likely doesn't offer these
- Multi/Combo markets (1X2MULTI*, DCMULTI*) - platform-specific bet builders
- UNSUPPORTED_PLATFORM markets - correctly classified, no fix needed

### v1.8 Milestone Status

**Not ready to ship.** Bet9ja at 40.5% is below acceptable threshold. Phase 46 should target:
- Bet9ja improvement to 50%+
- SportyBet improvement to 55%+

---

## Summary

Phase 44 was successful:
- UNKNOWN_PARAM_MARKET virtually eliminated
- TMGHO/TMGAW fixed
- Success rates improved by ~4.5%

But work remains:
- Bet9ja still below 50%
- High-frequency UNKNOWN_MARKET gaps (OUA, CHANCEMIX*, etc.)
- NO_MATCHING_OUTCOMES issues for HT/FT combo markets

**Next:** Create Phase 46 plan targeting top 5 remaining gaps.
