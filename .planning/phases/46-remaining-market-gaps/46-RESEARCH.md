# Phase 46: Remaining Market Mapping Gaps - Research

**Researched:** 2026-02-03
**Domain:** Sports betting market mapping (internal codebase analysis)
**Confidence:** HIGH

<research_summary>
## Summary

Researched the remaining high-priority UNKNOWN_MARKET gaps identified in Phase 45 audit. This is internal investigation focused on:
1. Understanding what each unknown market type means in betting terminology
2. Analyzing existing codebase architecture to understand mapping failures
3. Cross-referencing with BetPawa market structure for possible mappings

**Key findings:**
- **OUA** is likely "Over/Under Away" (Away team goals O/U) - BetPawa has equivalent (5003)
- **CHANCEMIX*** are combination bets (BTTS + O/U combos) - may not have BetPawa equivalent
- **60180** is Early Goals O/U - may need time-based handler addition
- **CAH/CAHH/CAH2** are Corner Asian Handicap variants - BetPawa has equivalents (1096785/1096786)
- **NO_MATCHING_OUTCOMES** issues (818, HTFTOU, 551) require outcome structure analysis

**Primary recommendation:** Focus on OUA and CAH variants first (highest ROI - clear BetPawa equivalents exist). Skip CHANCEMIX* as likely UNSUPPORTED_PLATFORM.

</research_summary>

<codebase_architecture>
## Codebase Architecture

### Market Mapping Pipeline

```
Source API (bet9ja/sportybet)
    ↓
Parser (bet9ja_parser.py / sportybet.py types)
    ↓
Grouper (by market_key + param)
    ↓
Mapping Lookup (find_by_bet9ja_key / find_by_sportybet_id)
    ↓
Handler Routing (simple / over_under / handicap)
    ↓
Outcome Mapping (match by suffix/desc/position)
    ↓
MappedMarket output
```

### Key Files

| File | Purpose |
|------|---------|
| [market_ids.py](src/market_mapping/mappings/market_ids.py) | Static MarketMapping definitions |
| [bet9ja.py](src/market_mapping/mappers/bet9ja.py) | Bet9ja → BetPawa mapper |
| [sportybet.py](src/market_mapping/mappers/sportybet.py) | SportyBet → BetPawa mapper |
| [normalized.py](src/market_mapping/types/normalized.py) | MarketMapping, OutcomeMapping types |

### Handler Routing Logic (Bet9ja)

```python
# bet9ja.py:519-539
if grouped.market_key in BET9JA_OVER_UNDER_KEYS:
    return _map_over_under_market(grouped, mapping)
if grouped.market_key in BET9JA_HANDICAP_KEYS:
    return _map_handicap_market(grouped, mapping)
if grouped.param is not None:
    raise MappingError(code=UNKNOWN_PARAM_MARKET, ...)
return _map_simple_market(grouped, mapping)
```

### Why Markets Fail

| Error Code | Cause | Fix Path |
|------------|-------|----------|
| UNKNOWN_MARKET | No entry in MARKET_MAPPINGS tuple | Add MarketMapping |
| UNKNOWN_PARAM_MARKET | Has param but not in O/U or Handicap key sets | Add to appropriate set + add MarketMapping |
| NO_MATCHING_OUTCOMES | MarketMapping exists but outcomes don't match | Fix OutcomeMapping entries |
| UNSUPPORTED_PLATFORM | MarketMapping exists but betpawa_id is None | Intentional - no BetPawa equivalent |

</codebase_architecture>

<market_analysis>
## Priority Market Analysis

### 1. OUA (bet9ja) - 1,928 occurrences - HIGH PRIORITY

**What it is:** "Over/Under Away" - betting on the Away team's total goals

**Structure analysis:**
- Bet9ja key format: `S_OUA@{line}_{O|U}` (e.g., `S_OUA@0.5_O`, `S_OUA@1.5_U`)
- Parameterized market with O/U line

**BetPawa equivalent:** EXISTS
- Away Team Over/Under - Full Time: `betpawa_id="5003"`
- Already mapped from other sources (sportybet_id="900010")

**Fix approach:**
1. Add `"S_OUA"` to existing `away_team_over_under_ft` MarketMapping
2. Add `"OUA"` to `BET9JA_OVER_UNDER_KEYS` set

**Impact:** ~1,900 markets should map immediately

---

### 2. CHANCEMIX* (bet9ja) - ~740 combined - INVESTIGATE

**What it is:** "Chance Mix" - combination bets

| Market | Meaning | Frequency |
|--------|---------|-----------|
| CHANCEMIXOU | Chance Mix + Over/Under | 386 |
| CHANCEMIX | Base Chance Mix | 95 |
| CHANCEMIXN | Chance Mix + No Goal | 65 |

**Structure analysis:**
- Combination of BTTS and O/U markets
- e.g., "NG or Over 1.5" = "BTTS=No OR Total Goals > 1.5"

**BetPawa equivalent:** UNLIKELY
- These are platform-specific combo markets
- BetPawa likely offers individual markets, not combinations

**Recommendation:** Mark as UNSUPPORTED_PLATFORM (add MarketMapping with `betpawa_id=None`)

**Impact:** ~740 markets correctly classified (not mapped)

---

### 3. 60180 (sportybet) - 464 occurrences - MEDIUM PRIORITY

**What it is:** Early Goals Over/Under

**Structure analysis:**
- SportyBet market ID: 60180
- Time-based goal betting (e.g., "2 goals by 30th minute")
- Has specifier with time range parameters

**BetPawa equivalent:** UNCLEAR
- May require investigation of BetPawa's early goal markets
- Time-based markets may not have direct mapping

**Recommendation:** Investigate BetPawa's market catalog for early goal equivalents

---

### 4. NO_MATCHING_OUTCOMES Markets - MEDIUM PRIORITY

| Market | Platform | Frequency | Issue |
|--------|----------|-----------|-------|
| 818 | sportybet | 540 | HT/FT & O/U combo - outcome structure |
| HTFTOU | bet9ja | 540 | Same as 818 |
| 551 | sportybet | 148 | Multiscores - complex outcomes |

**Analysis:**
- These markets ARE in MARKET_MAPPINGS (hence not UNKNOWN_MARKET)
- But outcome descriptions don't match OutcomeMapping entries
- Need to analyze raw API responses for actual outcome formats

**Fix approach:**
1. Fetch raw API samples for these markets
2. Compare outcome descriptions to OutcomeMapping entries
3. Update sportybet_desc or bet9ja_suffix as needed

---

### 5. CAH/CAHH/CAH2 (bet9ja) - ~300 combined - HIGH PRIORITY

**What it is:** Corner Asian Handicap variants

| Market | Meaning | Frequency |
|--------|---------|-----------|
| CAH2 | Corner AH - 2nd Half | 76 |
| CAHH | Corner AH - 1st Half | 74 |
| CAH | Corner AH - Full Time | 52 |
| CAH1 | Corner AH - 1st Half (alt) | 3 |

**BetPawa equivalent:** EXISTS
- Corner Asian Handicap - Full Time: `betpawa_id="1096785"`
- Corner Asian Handicap - First Half: `betpawa_id="1096786"`

**Current state:**
- MarketMappings exist (bet9ja_key mapped from SportyBet IDs 165, 176)
- But NO bet9ja_key entries for CAH/CAHH/CAH2

**Fix approach:**
1. Add `bet9ja_key="S_CAH"` to existing `corner_handicap_ft` mapping
2. Add `bet9ja_key="S_CAHH"` to existing `corner_handicap_1h` mapping
3. Add `"CAH"`, `"CAHH"` to `BET9JA_HANDICAP_KEYS` set
4. Handle CAH2 (2nd half) - may need new mapping or skip

**Impact:** ~205 markets should map immediately (CAH + CAHH + CAH1)

</market_analysis>

<implementation_priorities>
## Implementation Priorities

### HIGH ROI (Clear BetPawa equivalents)

| Priority | Market | Platform | Occurrences | Fix Complexity |
|----------|--------|----------|-------------|----------------|
| 1 | OUA | bet9ja | 1,928 | LOW - add key to existing mapping |
| 2 | CAH/CAHH | bet9ja | ~200 | LOW - add keys to existing mappings |

**Expected impact:** +2,100 mapped markets = ~6% Bet9ja improvement

### MEDIUM ROI (Outcome fixes)

| Priority | Market | Platform | Occurrences | Fix Complexity |
|----------|--------|----------|-------------|----------------|
| 3 | 818/HTFTOU | sportybet/bet9ja | ~1,000 | MEDIUM - analyze outcomes |
| 4 | 551 | sportybet | 148 | MEDIUM - complex outcomes |

**Expected impact:** +1,100 mapped markets if fixable

### LOW ROI (Platform-specific)

| Priority | Market | Platform | Occurrences | Action |
|----------|--------|----------|-------------|--------|
| 5 | CHANCEMIX* | bet9ja | ~740 | Mark UNSUPPORTED_PLATFORM |
| 6 | 60180 | sportybet | 464 | Investigate - may be unsupported |

**Expected impact:** Better classification, no mapping improvement

</implementation_priorities>

<outcome_analysis>
## Outcome Structure Analysis Needed

For NO_MATCHING_OUTCOMES fixes, need to fetch raw API samples:

### Market 818 (SportyBet) / HTFTOU (Bet9ja)
**Current mapping:** `htft_over_under` (ID: 28000209)
**Issue:** Outcome descriptions not matching

Sample needed:
```python
# Fetch raw API response for event with market 818
# Compare outcome.desc values to OutcomeMapping.sportybet_desc
```

### Market 551 (SportyBet) - Multiscores
**Current mapping:** Exists (need to verify)
**Issue:** Complex outcome structure with score ranges

Sample needed:
```python
# Fetch raw API response for event with market 551
# Analyze outcome structure (likely: "1-0", "2-0", "2-1", etc.)
```

### HTFTOU (Bet9ja)
**Current mapping:** Same as 818
**Issue:** Bet9ja outcome suffixes not matching

Sample needed:
```python
# Fetch raw API response for Bet9ja event with HTFTOU market
# Analyze outcome suffix patterns
```

</outcome_analysis>

<don't_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead |
|---------|-------------|-------------|
| Market key parsing | Custom regex | Existing `parse_bet9ja_key()` function |
| Outcome matching | New matching logic | Existing `_match_outcome()` function |
| Market routing | Custom conditionals | Existing handler sets (BET9JA_OVER_UNDER_KEYS, etc.) |

**Key insight:** The existing architecture is well-designed. Fixes should be configuration changes (adding to sets, adding mappings) not logic changes.

</don't_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Missing Bet9ja Key Format
**What goes wrong:** Adding market key without "S_" prefix
**Why it happens:** Bet9ja uses `S_{KEY}` format, easy to forget
**How to avoid:** Always use `bet9ja_key="S_{KEY}"` format

### Pitfall 2: Forgetting Handler Set
**What goes wrong:** Adding MarketMapping but not adding to handler set
**Why it happens:** Two places to update for parameterized markets
**How to avoid:** Checklist: (1) Add MarketMapping (2) Add to OVER_UNDER_KEYS or HANDICAP_KEYS

### Pitfall 3: Outcome Suffix Case Sensitivity
**What goes wrong:** Bet9ja suffixes are uppercase, mapping fails
**Why it happens:** Mismatch between raw data and OutcomeMapping
**How to avoid:** Always verify case matches (e.g., "O" not "o", "1H" not "1h")

### Pitfall 4: Missing 2nd Half Variants
**What goes wrong:** Full Time and 1st Half mapped, 2nd Half fails
**Why it happens:** Bet9ja uses different keys for 2nd half (e.g., CAH2)
**How to avoid:** Always check for `*1T` (1st half), `*2T` (2nd half), and base (full time)

</common_pitfalls>

<sources>
## Sources

### Primary (HIGH confidence)
- Existing codebase analysis (100% reliable for current architecture)
- Phase 43/45 audit findings (verified with production data)
- [market_ids.py](src/market_mapping/mappings/market_ids.py) - existing mappings

### Secondary (MEDIUM confidence)
- [Bet9ja Help - Available Betting Markets](https://help.bet9ja.com/available-betting-markets/) - official market documentation
- [Bet9ja Blog - Over/Under](https://blog.bet9ja.com/all/bet9ja-explainer-how-to-bet-on-the-over-under-market/) - market explanations
- [GhanaSoccerNet - Bet9ja Codes](https://ghanasoccernet.com/ng/wiki/bet9ja-codes-meaning-in-nigeria/) - market code meanings
- [PinnacleOddsDropper - Asian Corners](https://www.pinnacleoddsdropper.com/blog/asian-corners) - CAH explanation
- [Wikipedia - Asian Handicap](https://en.wikipedia.org/wiki/Asian_handicap) - handicap betting

### Tertiary (LOW confidence - needs validation)
- Chance Mix interpretation (based on community sources)
- 60180 Early Goals interpretation (based on SportyBet promo page)

</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: Python market mapping pipeline
- Ecosystem: Bet9ja and SportyBet API structures
- Patterns: Handler routing, outcome matching
- Pitfalls: Key format, handler set membership

**Confidence breakdown:**
- OUA analysis: HIGH - clear pattern match to existing O/U markets
- CAH analysis: HIGH - verified BetPawa equivalents exist
- CHANCEMIX analysis: MEDIUM - may have edge cases
- 60180 analysis: LOW - needs live API investigation
- Outcome fixes: MEDIUM - requires raw data analysis

**Research date:** 2026-02-03
**Valid until:** 2026-03-03 (30 days - internal codebase stable)

</metadata>

---

*Phase: 46-remaining-market-gaps*
*Research completed: 2026-02-03*
*Ready for planning: yes*
