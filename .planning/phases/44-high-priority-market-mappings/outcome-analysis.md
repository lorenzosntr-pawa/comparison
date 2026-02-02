# Outcome Analysis for NO_MATCHING_OUTCOMES Markets

*Generated: 2026-02-02*

Analysis of actual API outcome structures vs current mappings for 6 HIGH priority markets with NO_MATCHING_OUTCOMES errors.

## Executive Summary

| Market | Platform | Current Issue | Fix Required |
|--------|----------|---------------|--------------|
| HAOU | bet9ja | Duplicate bet9ja_key, need combined market | Create single HAOU mapping with all 4 outcomes |
| HTFTOU | bet9ja | Position-based placeholder | Add all combo outcome suffixes |
| TMGHO | bet9ja | Wrong suffixes | Fix: HO12, HO13, HO23 |
| TMGAW | bet9ja | Wrong suffixes | Fix: AW12, AW13, AW23 |
| HTFTCS | bet9ja | Position-based placeholder | Add all score combo suffixes |
| 551 | sportybet | Position-based placeholder | Add actual outcome descriptions |
| 46 | sportybet | Position-based placeholder | Add HT/FT score descriptions |

---

## 1. HAOU - Home/Away Over/Under (bet9ja)

**Frequency:** 50 occurrences

### Actual API Data
```
Suffixes: ['OA', 'OH', 'UA', 'UH']

Sample keys:
  - S_HAOU@0.5_UH = 6.3
  - S_HAOU@0.5_UA = 4.35
  - S_HAOU@0.5_OH = 1.06
  - S_HAOU@0.5_OA = 1.14
```

### Current Mapping
```python
# TWO separate mappings with SAME bet9ja_key:
MarketMapping(
    canonical_id="home_over_under_ft",
    bet9ja_key="S_HAOU",  # <-- duplicate key
    outcome_mapping=(
        OutcomeMapping(bet9ja_suffix="OH", ...),
        OutcomeMapping(bet9ja_suffix="UH", ...),
    ),
)
MarketMapping(
    canonical_id="away_over_under_ft",
    bet9ja_key="S_HAOU",  # <-- same key!
    outcome_mapping=(
        OutcomeMapping(bet9ja_suffix="OA", ...),
        OutcomeMapping(bet9ja_suffix="UA", ...),
    ),
)
```

### Issue
Two mappings share the same `bet9ja_key="S_HAOU"`. The `find_by_bet9ja_key` function returns only the first match. When mapping HAOU market:
- Gets home_over_under_ft mapping (has OH, UH)
- Sees 4 outcomes: OH, UH, OA, UA
- OH → maps
- UH → maps
- OA → NO MATCH (not in home mapping)
- UA → NO MATCH (not in home mapping)

2/4 outcomes fail to map but 2 succeed, so likely the actual issue is that the AWAY outcomes get looked up separately but find the wrong first mapping.

### Fix
**Option A:** Create a NEW combined HAOU market with all 4 outcomes (preferred - cleaner)
**Option B:** Change away market to use different key (but bet9ja only sends one key)

Going with Option A - create dedicated HAOU mapping.

---

## 2. HTFTOU - Half Time/Full Time and Over/Under (bet9ja)

**Frequency:** 248 occurrences

### Actual API Data
```
HTFTOU@1.5 suffixes: ['1/1O', '1/1U', '1/2O', '1/XO', '2/1O', '2/2O', '2/2U', '2/XO', 'X/1O', 'X/1U', 'X/2O', 'X/2U', 'X/XO', 'X/XU']
HTFTOU@2.5 suffixes: ['1/1O', '1/1U', '1/2O', '1/XO', '1/XU', '2/1O', '2/2O', '2/2U', '2/XO', '2/XU', 'X/1O', 'X/1U', 'X/2O', 'X/2U', 'X/XO', 'X/XU']
HTFTOU@3.5 suffixes: All 18 combos (1/1, 1/2, 1/X, 2/1, 2/2, 2/X, X/1, X/2, X/X with O/U)

Sample keys:
  - S_HTFTOU@1.5_X/XU = 18
  - S_HTFTOU@1.5_1/1O = 3.35
  - S_HTFTOU@2.5_X/1O = 8.5
```

**Pattern:** `{HT_result}/{FT_result}{O|U}` where results are 1, X, 2

### Current Mapping
```python
MarketMapping(
    canonical_id="htft_over_under",
    bet9ja_key="S_HTFTOU",
    outcome_mapping=(
        # Many outcomes - position-based matching
        OutcomeMapping(canonical_id="pos_0", betpawa_name=None, sportybet_desc=None, bet9ja_suffix=None, position=0),
    ),
)
```

### Issue
Position-based placeholder with no actual outcome suffixes. Need to add all 18 possible combo outcomes.

### Fix
Add all valid outcome suffixes. Since there's no direct Betpawa equivalent for this combo market, set `betpawa_name=None` for all outcomes (or map to closest Betpawa equivalents if they exist).

---

## 3. TMGHO - Team Multigoals Home (bet9ja)

**Frequency:** 99 occurrences

### Actual API Data
```
Suffixes: ['HO12', 'HO13', 'HO23']

Sample keys:
  - S_TMGHO_HO13 = 1.23
  - S_TMGHO_HO12 = 1.63
  - S_TMGHO_HO23 = 1.96
```

**Meaning:**
- HO12 = Home team 1-2 goals
- HO13 = Home team 1-3 goals
- HO23 = Home team 2-3 goals

### Current Mapping
```python
MarketMapping(
    canonical_id="home_multigoals_ft",
    bet9ja_key="S_TMGHO",
    outcome_mapping=(
        OutcomeMapping(canonical_id="0", bet9ja_suffix=None, ...),     # WRONG
        OutcomeMapping(canonical_id="1_2", bet9ja_suffix=None, ...),   # WRONG
        OutcomeMapping(canonical_id="3+", bet9ja_suffix=None, ...),    # WRONG
    ),
)
```

### Issue
All bet9ja_suffix values are `None` instead of actual suffixes. The canonical_ids suggest ranges (0, 1_2, 3+) but bet9ja uses different ranges (1-2, 1-3, 2-3).

### Fix
Update outcome mappings with correct suffixes:
- `HO12` → 1-2 goals
- `HO13` → 1-3 goals
- `HO23` → 2-3 goals

---

## 4. TMGAW - Team Multigoals Away (bet9ja)

**Frequency:** 99 occurrences

### Actual API Data
```
Suffixes: ['AW12', 'AW13', 'AW23']

Sample keys:
  - S_TMGAW_AW23 = 2.22
  - S_TMGAW_AW13 = 1.23
  - S_TMGAW_AW12 = 1.52
```

**Meaning:**
- AW12 = Away team 1-2 goals
- AW13 = Away team 1-3 goals
- AW23 = Away team 2-3 goals

### Current Mapping
Same issue as TMGHO - `bet9ja_suffix=None` for all outcomes.

### Fix
Update outcome mappings with correct suffixes:
- `AW12` → 1-2 goals
- `AW13` → 1-3 goals
- `AW23` → 2-3 goals

---

## 5. HTFTCS - HT/FT Correct Score (bet9ja)

**Frequency:** 54 occurrences

### Actual API Data
```
Suffixes (46 total): ['0-0/0-0', '0-0/0-1', '0-0/0-2', '0-0/0-3', '0-0/1-0', '0-0/1-1',
                      '0-0/1-2', '0-0/2-0', '0-0/2-1', '0-0/3-0', '0-0/4+', '0-1/0-1',
                      '0-1/0-2', '0-1/0-3', '0-1/1-1', '0-1/1-2', '0-1/2-1', '0-1/4+',
                      '0-2/0-2', '0-2/0-3', '0-2/1-2', '0-2/4+', '0-3/0-3', '0-3/4+',
                      '1-0/1-0', '1-0/1-1', '1-0/1-2', '1-0/2-0', '1-0/2-1', '1-0/3-0',
                      '1-0/4+', '1-1/1-1', '1-1/1-2', '1-1/2-1', '1-1/4+', '1-2/1-2',
                      '1-2/4+', '2-0/2-0', '2-0/2-1', '2-0/3-0', '2-0/4+', '2-1/2-1',
                      '2-1/4+', '3-0/3-0', '3-0/4+', '4+/4+']

Sample keys:
  - S_HTFTCS_3-0/4+ = 32
  - S_HTFTCS_0-0/2-0 = 35
  - S_HTFTCS_0-1/0-3 = 64
```

**Pattern:** `{HT_score}/{FT_score}` where scores are like "0-0", "1-0", "4+"

### Current Mapping
```python
MarketMapping(
    canonical_id="htft_correct_score",
    bet9ja_key="S_HTFTCS",
    outcome_mapping=(
        OutcomeMapping(canonical_id="pos_0", bet9ja_suffix=None, ...),  # Placeholder
    ),
)
```

### Fix
Add all 46 valid HT/FT correct score combinations as outcomes.

---

## 6. SportyBet 551 - Multiscores

**Frequency:** 66 occurrences

### Actual API Data
```
Outcome descriptions (11 total):
  - "1:0, 2:0 or 3:0"
  - "0:1, 0:2 or 0:3"
  - "4:0, 5:0 or 6:0"
  - "0:4, 0:5 or 0:6"
  - "2:1, 3:1 or 4:1"
  - "1:2, 1:3 or 1:4"
  - "3:2, 4:2, 4:3 or 5:1"
  - "2:3, 2:4, 3:4 or 1:5"
  - "Draw"
  - "Other Homewin"
  - "Other Awaywin"
```

### Current Mapping
```python
MarketMapping(
    canonical_id="multiscores_ft",
    sportybet_id="551",
    outcome_mapping=(
        # Position-based matching for score ranges
        OutcomeMapping(canonical_id="pos_0", sportybet_desc=None, ...),
    ),
)
```

### Fix
Add all 11 outcome descriptions for proper matching.

---

## 7. SportyBet 46 - HT/FT Correct Score

**Frequency:** 56 occurrences

### Actual API Data
```
Outcome descriptions (46 total):
  - "0:0 0:0"
  - "0:0 0:1"
  - "0:0 0:2"
  - "0:0 0:3"
  - "0:0 1:0"
  - "0:0 1:1"
  - ... (similar pattern)
  - "3:0 4+"
  - "4+ 4+"
```

**Pattern:** `{HT_score} {FT_score}` (space-separated)

### Current Mapping
```python
MarketMapping(
    canonical_id="htft_correct_score",
    sportybet_id="46",
    bet9ja_key="S_HTFTCS",  # Shares with bet9ja
    outcome_mapping=(
        OutcomeMapping(canonical_id="pos_0", sportybet_desc=None, ...),
    ),
)
```

### Fix
Add all 46 HT/FT correct score descriptions for both bet9ja and sportybet in the same mapping.

---

## Summary of Required Changes

### market_ids.py Changes

1. **HAOU:** Create new combined mapping with all 4 outcomes (OH, UH, OA, UA)
2. **TMGHO:** Fix bet9ja_suffix: `HO12`, `HO13`, `HO23`
3. **TMGAW:** Fix bet9ja_suffix: `AW12`, `AW13`, `AW23`
4. **HTFTOU:** Add 18 combo outcomes: `{1|X|2}/{1|X|2}{O|U}`
5. **HTFTCS:** Add 46 HT/FT score outcomes for both bet9ja and sportybet
6. **551 (Multiscores):** Add 11 outcome descriptions

### Note on Betpawa Equivalents

For markets like HTFTOU, HTFTCS, and Multiscores, there may not be direct Betpawa equivalents. In those cases, set `betpawa_name=None` for outcomes - the mapping still captures competitor data correctly for comparison purposes.
