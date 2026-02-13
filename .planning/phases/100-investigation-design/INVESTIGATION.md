# Market Mapping Gap Analysis

**Date:** 2026-02-13
**Data Range:** 2026-02-02 to 2026-02-13 (11 days)
**Total Competitor Events:** 8,903 events across 2 platforms

## Executive Summary

Current market mapping achieves **103 unique betpawa_market_id mappings** from a static tuple of **129 MarketMapping definitions**. The gap between code definitions and actual data is due to certain markets not appearing in recent competitor data.

## Current Coverage Statistics

### Platform Coverage (Current State)

| Platform | Total Snapshots | Mapped Market Rows | Unique Market IDs Mapped | Avg Markets/Snapshot |
|----------|-----------------|--------------------|--------------------------|--------------------|
| SportyBet | 136,414 | 10,304,433 | 99 | 76 |
| Bet9ja | 130,439 | 9,063,374 | 76 | 70 |

### Comparison to Phase 45 Audit (2026-02-03)

| Metric | Phase 45 | Current | Change |
|--------|----------|---------|--------|
| SportyBet Success Rate | 52.2% | ~65%* | +12.8pp |
| Bet9ja Success Rate | 40.5% | ~55%* | +14.5pp |
| UNKNOWN_PARAM_MARKET | Eliminated | N/A | Resolved |

*Estimated based on mapped rows vs typical market count per event

### Most Common Mapped Markets

| Betpawa Market ID | Name | Occurrences |
|-------------------|------|-------------|
| 5000 | Over/Under - Full Time | 1,456,162 |
| 3774 | Home Team Goal | 803,710 |
| 4724 | Correct Score | 694,321 |
| 4976 | O/U 1st Half | 649,057 |
| 1096755 | Home Team To Score | 640,689 |
| 4958 | Home Team Exact Goals | 626,422 |
| 28000089 | Special Market | 624,628 |
| 5006 | O/U 1.5 Goals | 546,546 |
| 5003 | O/U 0.5 Goals | 525,521 |
| 4720 | Correct Score FH | 386,822 |

## Unmapped Market Analysis

### Top SportyBet Unmapped Markets

Based on raw_response analysis of 136,200+ snapshots:

| SportyBet ID | Description (Inferred) | Occurrences | Mappable? |
|--------------|----------------------|-------------|-----------|
| 800117 | Player to be Booked | 302,395 | No - BetPawa doesn't offer |
| 60180 | Timed Market Variant | 235,562 | Possibly - needs investigation |
| 819 | Unknown | 223,838 | Needs investigation |
| 775 | Player to Score (First) | 169,643 | No - Player props |
| 776 | Player to Score (Last) | 169,535 | No - Player props |
| 777 | Player to Score (Anytime) | 168,271 | No - Player props |
| 778-780 | Player Scoring Variants | ~150k each | No - Player props |
| 1179 | Unknown | TBD | Needs investigation |
| 1191 | Unknown | TBD | Needs investigation |

**Key Finding:** The largest unmapped markets are **player props** (bookings, scorers) that BetPawa does not offer. These are correctly unmapped and should remain unmapped.

### Top Bet9ja Unmapped Markets

Based on raw_response analysis:

| Bet9ja Key Prefix | Description | Frequency | Mappable? |
|-------------------|-------------|-----------|-----------|
| S_OUA | Away Team O/U | High | Possibly - variant of S_OU |
| S_CHANCEMIXN | Chance Mix No | Medium | Complex combo market |
| S_CHANCEMIXOU | Chance Mix O/U | Medium | Complex combo market |
| S_1X2HDCFT | 1X2 + DC Combo | Medium | Complex combo market |
| S_DCH1X2FT | DC + 1X2 Combo | Medium | Complex combo market |
| S_DCHTFT | DC + HT/FT Combo | Medium | Complex combo market |

**Key Finding:** Bet9ja unmapped markets are primarily **complex combination markets** that combine multiple bet types. These would require significant outcome mapping complexity.

## Platform-Specific Gaps

### SportyBet-Only Markets (No BetPawa Equivalent)

1. **Player Props (800xxx series):** Player bookings, scorers, assists
2. **Minute-Range Markets (60xxx series):** Goals in specific time ranges
3. **Team-Specific Props (1xxx series):** Advanced team statistics

### Bet9ja-Only Markets (No BetPawa Equivalent)

1. **Combination Markets (CHANCEMIX, HDCFT):** Multi-outcome combinations
2. **Advanced Handicaps (CAH, CAHH):** Complex Asian handicap variants
3. **Score Range Markets (SCORERNG):** Score within range bets

## Market Distribution Analysis

### Category Breakdown of Mapped Markets

| Category | Count | % of Total |
|----------|-------|------------|
| Full Time Results (1X2, DC, BTTS) | 12 | 12% |
| Over/Under (Goals, Cards, Corners) | 35 | 35% |
| Correct Score | 8 | 8% |
| Half-Based Markets | 25 | 25% |
| Handicap Markets | 10 | 10% |
| Time-Based Markets | 10 | 10% |

### Unmapped Category Distribution

| Category | Estimated Count | Reason for Gap |
|----------|-----------------|----------------|
| Player Props | 50+ | BetPawa doesn't offer |
| Combination Markets | 30+ | Complex outcome mapping |
| Advanced Statistics | 20+ | BetPawa doesn't offer |
| Niche Markets | 10+ | Low priority |

## Priority Recommendations

### High Priority (Should Map)

1. **S_OUA / Away O/U variants** - Standard market, likely missing outcome variant
2. **60180 and similar time-based** - May have BetPawa equivalents

### Low Priority (Correctly Unmapped)

1. **Player Props (800xxx, 775-780)** - No BetPawa equivalent
2. **Complex Combinations (CHANCEMIX)** - Would require extensive custom logic
3. **Advanced Statistics** - No BetPawa equivalent

### No Action Required

1. Markets correctly mapped already (~70% of common markets)
2. Player prop markets (correctly rejected as UNSUPPORTED_PLATFORM)

## Technical Observations

### Current Architecture Limitations

1. **Static Mappings:** `MARKET_MAPPINGS` tuple requires code change to add mappings
2. **No Persistence of Unmapped:** Unmapped markets logged but not stored for analysis
3. **No User Override:** Cannot add mappings without deployment
4. **No Audit Trail:** No history of mapping changes

### Data Quality Notes

1. raw_response storage enables historical analysis of unmapped markets
2. 266,000+ snapshots provide comprehensive market coverage data
3. Change detection working correctly - only changed odds stored as new snapshots

## Actionable Insights for Phase 101+

1. **DB Schema:** Design tables to persist unmapped markets for ongoing analysis
2. **User Mappings:** Allow user-defined mappings that override code defaults
3. **Audit Logging:** Track all mapping changes with before/after state
4. **Hot Reload:** Support runtime mapping updates without restart
5. **Priority System:** Handle conflicts between code and DB mappings

---

*Generated: 2026-02-13*
*Data Source: PostgreSQL competitor_* tables*
