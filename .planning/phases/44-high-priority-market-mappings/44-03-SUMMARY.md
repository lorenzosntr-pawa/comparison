# Phase 44-03 Summary: Fix UNKNOWN_PARAM_MARKET for Combo Markets

## Objective

Fix UNKNOWN_PARAM_MARKET errors for 6 HIGH priority combo markets (~1,500 occurrences) by adding them to the O/U parameter handling sets.

## Target Markets

| Platform | Market Key/ID | Market Name | Occurrences |
|----------|---------------|-------------|-------------|
| bet9ja | 1X2OU | 1X2 + Over/Under | 348 |
| bet9ja | DCOU | Double Chance + Over/Under | 342 |
| sportybet | 37 | 1X2 & Over/Under | 264 |
| sportybet | 547 | Double Chance & Over/Under | 264 |
| sportybet | 818 | HT/FT & Over/Under | 216 |
| sportybet | 36 | Over/Under & GG/NG | 66 |

## Root Cause

These combo markets use a line parameter (e.g., `param="2.5"` or `specifier="total=2.5"`) but were not included in the parameter handling sets:
- `BET9JA_OVER_UNDER_KEYS` in `bet9ja.py`
- `OVER_UNDER_MARKET_IDS` in `market_ids.py`

The market mappings themselves already existed with valid `betpawa_id` values - they just weren't being routed through the O/U handler.

## Solution

### 1. Bet9ja Keys Added

Added to `BET9JA_OVER_UNDER_KEYS`:
- `1X2OU` - 1X2 + Over/Under combo
- `DCOU` - Double Chance + Over/Under combo

### 2. SportyBet IDs Added

Added to `OVER_UNDER_MARKET_IDS`:
- `37` - 1X2 & Over/Under
- `547` - Double Chance & Over/Under
- `818` - HT/FT & Over/Under
- `36` - Over/Under & GG/NG

## Files Modified

- `src/market_mapping/mappers/bet9ja.py` - Added combo keys to BET9JA_OVER_UNDER_KEYS
- `src/market_mapping/mappings/market_ids.py` - Added combo IDs to OVER_UNDER_MARKET_IDS, removed duplicate entries
- `tests/test_bet9ja_mapper.py` - Added TestComboMarketMapping class (4 tests)
- `tests/test_sportybet_mapper.py` - Added TestComboMarketMapping class (5 tests)

## Verification

- **41 tests pass** in mapper test suites
- Combo market keys confirmed in O/U sets:
  - `1X2OU` in BET9JA_OVER_UNDER_KEYS: True
  - `DCOU` in BET9JA_OVER_UNDER_KEYS: True
  - `37` in OVER_UNDER_MARKET_IDS: True
  - `547` in OVER_UNDER_MARKET_IDS: True

## Impact

- ~1,500 market occurrences now map correctly with line parameters
- These markets will now produce `MappedMarket` objects with `line` field populated
- htft_over_under (818) has pre-existing incomplete outcome mapping data (separate issue)

## Notes

The original mappings in `market_ids.py` already had:
- `1x2_over_under_ft` with `betpawa_id="1096755"`
- `over_under_btts_ft` with `betpawa_id="4613062"`
- `double_chance_over_under_ft` with `betpawa_id="28000089"`
- `htft_over_under` with `betpawa_id="28000279"`

The fix was purely routing - adding market keys/IDs to the parameter handling sets so they use the O/U handler with line extraction.
