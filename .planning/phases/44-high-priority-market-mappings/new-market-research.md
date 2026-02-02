# New Market Research - Phase 44-02

Research findings for HIGH priority UNKNOWN_MARKET errors.

## Summary

Based on analysis of audit_raw_data.json, the following markets can be mapped. Markets are grouped by type.

---

## Group A: Clear Mappings (Draw No Bet variants)

### Home No Bet
- **SportyBet ID:** 12
- **Bet9ja Key:** S_HOMENOBET
- **Description:** Home team wins or void (refund if draw)
- **Frequency:** 66 (sportybet), 99 (bet9ja)
- **Outcomes:** Yes/No (betting home team wins, void on draw)
- **BetPawa equivalent:** None (market doesn't exist on BetPawa as separate market)
- **Proposed canonical_id:** `home_no_bet_ft`
- **Outcome structure:** 2 outcomes - Yes, No

### Away No Bet
- **SportyBet ID:** 13
- **Bet9ja Key:** S_AWAYNOBET
- **Description:** Away team wins or void (refund if draw)
- **Frequency:** 66 (sportybet), 99 (bet9ja)
- **Outcomes:** Yes/No
- **BetPawa equivalent:** None
- **Proposed canonical_id:** `away_no_bet_ft`
- **Outcome structure:** 2 outcomes - Yes, No

### 1st Goal (Who Scores First)
- **SportyBet ID:** 8
- **Bet9ja Key:** S_1STGOAL
- **Description:** Which team scores the first goal
- **Frequency:** 48 (sportybet), 65 (bet9ja)
- **Outcomes:** Home, None (no goal), Away
- **BetPawa equivalent:** None directly mappable
- **Proposed canonical_id:** `first_goal_ft`
- **Outcome structure:** 3 outcomes - Home, None, Away

### Last Goal (Who Scores Last)
- **Bet9ja Key:** S_LASTSCORE
- **Description:** Which team scores the last goal
- **Frequency:** 65 (bet9ja only)
- **Outcomes:** Home, None, Away
- **BetPawa equivalent:** None
- **Proposed canonical_id:** `last_goal_ft`
- **Outcome structure:** 3 outcomes - Home, None, Away

---

## Group B: Time-Based Markets

### 1X2 from 1 to 5 minute (Early Result)
- **SportyBet ID:** 900069
- **Bet9ja Key:** S_1X21ST5MIN
- **Description:** Match result in first 5 minutes
- **Frequency:** 312 (sportybet), 62 (bet9ja)
- **Outcomes:** Home, Draw, Away
- **BetPawa equivalent:** None
- **Proposed canonical_id:** `1x2_5min`
- **Outcome structure:** 3 outcomes - 1, X, 2

### 1X2 - 1UP (Home to win by 1+ goals)
- **SportyBet ID:** 60200
- **Description:** Home team to win by at least 1 goal
- **Frequency:** 76 (sportybet only)
- **Outcomes:** Yes/No
- **BetPawa equivalent:** None
- **Proposed canonical_id:** `home_win_1plus_ft`
- **Outcome structure:** 2 outcomes - Yes, No

### 1X2 - 2UP (Home to win by 2+ goals)
- **SportyBet ID:** 60100
- **Description:** Home team to win by at least 2 goals
- **Frequency:** 76 (sportybet only)
- **Outcomes:** Yes/No
- **BetPawa equivalent:** None
- **Proposed canonical_id:** `home_win_2plus_ft`
- **Outcome structure:** 2 outcomes - Yes, No

### 1X2 Period 1 (First Half 1X2)
- **Bet9ja Key:** S_1X21
- **Description:** 1X2 for period 1 (already have 1x2_1h mapping)
- **Frequency:** 62 (bet9ja)
- **Note:** SKIP - This is the same as existing 1x2_1h but different key format

### 1X2 Period 2 (Second Half 1X2)
- **Bet9ja Key:** S_1X22
- **Description:** 1X2 for period 2 (already have 1x2_2h mapping)
- **Frequency:** 62 (bet9ja)
- **Note:** SKIP - Same as existing 1x2_2h

---

## Group C: Clean Sheet and Result Combos

### Home Team or Any Clean Sheet
- **SportyBet ID:** 863
- **Description:** Home team wins OR any team keeps clean sheet
- **Frequency:** 66 (sportybet only)
- **Outcomes:** Yes, No
- **BetPawa equivalent:** None
- **Proposed canonical_id:** `home_or_clean_sheet_ft`
- **Outcome structure:** 2 outcomes

### Draw or Any Clean Sheet
- **SportyBet ID:** 864
- **Description:** Draw OR any team keeps clean sheet
- **Frequency:** 66 (sportybet only)
- **Outcomes:** Yes, No
- **BetPawa equivalent:** None
- **Proposed canonical_id:** `draw_or_clean_sheet_ft`
- **Outcome structure:** 2 outcomes

### Away Team or Any Clean Sheet
- **SportyBet ID:** 865
- **Description:** Away team wins OR any team keeps clean sheet
- **Frequency:** 66 (sportybet only)
- **Outcomes:** Yes, No
- **BetPawa equivalent:** None
- **Proposed canonical_id:** `away_or_clean_sheet_ft`
- **Outcome structure:** 2 outcomes

---

## Group D: Goal Scoring Markets

### Home Team To Score Yes/No
- **SportyBet ID:** 900015
- **Description:** Will the home team score at least 1 goal
- **Frequency:** 61 (sportybet only)
- **Outcomes:** Yes, No
- **BetPawa equivalent:** None
- **Proposed canonical_id:** `home_to_score_ft`
- **Outcome structure:** 2 outcomes - Yes, No

### Away Team To Score Yes/No
- **SportyBet ID:** 900014
- **Description:** Will the away team score at least 1 goal
- **Frequency:** 61 (sportybet only)
- **Outcomes:** Yes, No
- **BetPawa equivalent:** None
- **Proposed canonical_id:** `away_to_score_ft`
- **Outcome structure:** 2 outcomes - Yes, No

### Home Team Exact Goals (GOALSHOME)
- **Bet9ja Key:** S_GOALSHOME
- **Description:** Exact number of goals scored by home team
- **Frequency:** 95 (bet9ja)
- **Note:** SKIP - Already have home_exact_goals_ft mapping with S_HOMEGOALS

### Away Team Exact Goals (GOALSAWAY)
- **Bet9ja Key:** S_GOALSAWAY
- **Description:** Exact number of goals scored by away team
- **Frequency:** 95 (bet9ja)
- **Note:** SKIP - Already have away_exact_goals_ft mapping with S_AWAYGOALS

---

## Group E: BTTS Variants

### GG/NG 2+ (Both Teams Score 2+ Goals)
- **SportyBet ID:** 60000
- **Bet9ja Key:** S_GGNG2PLUS
- **Description:** Both teams to score 2+ goals each
- **Frequency:** 92 (sportybet), 99 (bet9ja)
- **Outcomes:** Yes, No
- **BetPawa equivalent:** None
- **Proposed canonical_id:** `btts_2plus_ft`
- **Outcome structure:** 2 outcomes - Yes, No

### Both Teams Score in Both Halves
- **SportyBet ID:** 900027
- **Description:** Both teams score in 1st AND 2nd half
- **Frequency:** 55 (sportybet only)
- **Outcomes:** Yes, No
- **BetPawa equivalent:** None
- **Proposed canonical_id:** `btts_both_halves`
- **Outcome structure:** 2 outcomes - Yes, No

### No Draw Both Teams To Score
- **SportyBet ID:** 900041
- **Description:** Home/Away win and both teams score
- **Frequency:** 61 (sportybet only)
- **Outcomes:** Yes, No
- **BetPawa equivalent:** None
- **Proposed canonical_id:** `no_draw_btts_ft`
- **Outcome structure:** 2 outcomes - Yes, No

---

## Group F: Result + Over/Under Combos

### Home Team or Over 2.5
- **SportyBet ID:** 854
- **Description:** Home wins OR over 2.5 goals
- **Frequency:** 66 (sportybet only)
- **Outcomes:** Yes, No
- **Proposed canonical_id:** `home_or_over_25_ft`

### Home Team or Under 2.5
- **SportyBet ID:** 855
- **Description:** Home wins OR under 2.5 goals
- **Frequency:** 66 (sportybet only)
- **Outcomes:** Yes, No
- **Proposed canonical_id:** `home_or_under_25_ft`

### Draw or Over 2.5
- **SportyBet ID:** 856
- **Description:** Draw OR over 2.5 goals
- **Frequency:** 66 (sportybet only)
- **Outcomes:** Yes, No
- **Proposed canonical_id:** `draw_or_over_25_ft`

### Draw or Under 2.5
- **SportyBet ID:** 857
- **Description:** Draw OR under 2.5 goals
- **Frequency:** 66 (sportybet only)
- **Outcomes:** Yes, No
- **Proposed canonical_id:** `draw_or_under_25_ft`

### Away or Over 2.5
- **SportyBet ID:** 858
- **Description:** Away wins OR over 2.5 goals
- **Frequency:** 66 (sportybet only)
- **Outcomes:** Yes, No
- **Proposed canonical_id:** `away_or_over_25_ft`

### Away or Under 2.5
- **SportyBet ID:** 859
- **Description:** Away wins OR under 2.5 goals
- **Frequency:** 66 (sportybet only)
- **Outcomes:** Yes, No
- **Proposed canonical_id:** `away_or_under_25_ft`

---

## Group G: Result + GG Combos

### Home Team or GG
- **SportyBet ID:** 860
- **Description:** Home wins OR both teams score
- **Frequency:** 66 (sportybet only)
- **Outcomes:** Yes, No
- **Proposed canonical_id:** `home_or_btts_ft`

### Draw or GG
- **SportyBet ID:** 861
- **Description:** Draw OR both teams score
- **Frequency:** 66 (sportybet only)
- **Outcomes:** Yes, No
- **Proposed canonical_id:** `draw_or_btts_ft`

### Away Team or GG
- **SportyBet ID:** 862
- **Description:** Away wins OR both teams score
- **Frequency:** 66 (sportybet only)
- **Outcomes:** Yes, No
- **Proposed canonical_id:** `away_or_btts_ft`

---

## Group H: Half-Based Over/Under

### Both Halves Over 1.5
- **SportyBet ID:** 58
- **Description:** Over 1.5 goals in BOTH halves
- **Frequency:** 76 (sportybet only)
- **Outcomes:** Yes, No
- **Proposed canonical_id:** `both_halves_over_15`

### Both Halves Under 1.5
- **SportyBet ID:** 59
- **Description:** Under 1.5 goals in BOTH halves
- **Frequency:** 76 (sportybet only)
- **Outcomes:** Yes, No
- **Proposed canonical_id:** `both_halves_under_15`

---

## Group I: Goal Range

### Goal Range
- **SportyBet ID:** 25
- **Description:** Total goals fall within a range (e.g., 0-1, 2-3, 4-5, 6+)
- **Frequency:** 34 (sportybet only)
- **Outcomes:** Multiple ranges (0-1, 2-3, 4-5, 6+)
- **Proposed canonical_id:** `goal_range_ft`
- **Note:** Similar to multigoals_ft but different structure

---

## Markets NOT Added (Deferred or Skipped)

1. **1X21 / 1X22 (Bet9ja)** - Already covered by existing 1x2_1h / 1x2_2h mappings
2. **GOALSHOME / GOALSAWAY (Bet9ja)** - Already covered by existing home_exact_goals_ft / away_exact_goals_ft
3. **Player props** - Out of scope per plan
4. **Parameterized markets (UNKNOWN_PARAM_MARKET)** - Deferred to plan 44-03

---

## Mappings to Add (20 total)

| # | canonical_id | SportyBet ID | Bet9ja Key | BetPawa ID |
|---|-------------|--------------|------------|------------|
| 1 | home_no_bet_ft | 12 | S_HOMENOBET | None |
| 2 | away_no_bet_ft | 13 | S_AWAYNOBET | None |
| 3 | first_goal_ft | 8 | S_1STGOAL | None |
| 4 | last_goal_ft | None | S_LASTSCORE | None |
| 5 | 1x2_5min | 900069 | S_1X21ST5MIN | None |
| 6 | home_win_1plus_ft | 60200 | None | None |
| 7 | home_win_2plus_ft | 60100 | None | None |
| 8 | home_or_clean_sheet_ft | 863 | None | None |
| 9 | draw_or_clean_sheet_ft | 864 | None | None |
| 10 | away_or_clean_sheet_ft | 865 | None | None |
| 11 | home_to_score_ft | 900015 | None | None |
| 12 | away_to_score_ft | 900014 | None | None |
| 13 | btts_2plus_ft | 60000 | S_GGNG2PLUS | None |
| 14 | btts_both_halves | 900027 | None | None |
| 15 | no_draw_btts_ft | 900041 | None | None |
| 16 | home_or_over_25_ft | 854 | None | None |
| 17 | draw_or_over_25_ft | 856 | None | None |
| 18 | away_or_over_25_ft | 858 | None | None |
| 19 | home_or_btts_ft | 860 | None | None |
| 20 | both_halves_over_15 | 58 | None | None |

**Estimated Impact:** ~1,800+ market occurrences now mappable
