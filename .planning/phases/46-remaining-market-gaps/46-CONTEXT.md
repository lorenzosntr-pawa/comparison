# Phase 46: Remaining Market Mapping Gaps - Context

**Gathered:** 2026-02-03
**Status:** Ready for planning

<vision>
## How This Should Work

Handicap markets (3-Way Handicap and 2-Way/Asian Handicap) should show odds from all three bookmakers when viewing match details. Currently BetPawa shows odds but SportyBet and Bet9ja columns show "-" despite having the data.

The root cause is a mismatch in how handicap values are stored:
- **BetPawa** extracts `formattedHandicap` from the API and stores it in the `line` field (e.g., `line = -1`)
- **Competitors** store handicap values in separate fields (`handicap_home = -1`) but leave `line = None`

Frontend matching uses `${market_id}_${line}` as the key, so BetPawa's `4724_-1` doesn't match competitor's `4724_null`.

Fix: Populate competitor market `line` field with `handicap_home` value at storage time so matching works.

</vision>

<essential>
## What Must Be Nailed

- **Line population fix** — Competitor handicap markets must have `line` populated from `handicap_home` so frontend matching works
- **Both handicap types** — Fix applies to both 3-Way (European) and 2-Way (Asian) handicaps across all periods (Full Time, First Half, Second Half)
- **Full handicap audit** — Verify all handicap market IDs are correctly mapped and check actual data for any other handicap-related issues

</essential>

<boundaries>
## What's Out of Scope

- **OUA markets** — Defer to future phase
- **CHANCEMIX markets** — Defer to future phase
- **Other non-handicap gaps** — Focus purely on handicap markets (3-Way, 2-Way/Asian)
- **Player props** — Skip player-specific markets
- **UNSUPPORTED_PLATFORM markets** — Don't try to map markets BetPawa doesn't support

</boundaries>

<specifics>
## Specific Ideas

**Handicap market types to cover:**
- 3-Way Handicap Full Time (BetPawa 4724, SportyBet 14, Bet9ja S_1X2HND)
- 3-Way Handicap First Half (BetPawa 4716, SportyBet 65, Bet9ja S_1X2HNDHT)
- 3-Way Handicap Second Half (BetPawa 4720, SportyBet 87, Bet9ja S_1X2HND2TN)
- Asian Handicap Full Time (BetPawa 3774, SportyBet 16, Bet9ja S_AH)
- Asian Handicap First Half (BetPawa 3747, SportyBet 66, Bet9ja S_AH1T)
- Asian Handicap Second Half (BetPawa 3756, SportyBet 88, Bet9ja S_AH2T)

**Technical approach:**
- Modify competitor market storage to set `line = handicap_home` when `handicap` object is present
- Applies to both SportyBet and Bet9ja parsing in event_coordinator.py and competitor_events.py
- No frontend changes needed — matching will work once data is correct

</specifics>

<notes>
## Additional Context

The mapping logic already correctly handles handicap specifiers:
- SportyBet: `hcp=0:1` (European) → `handicap_home = -1, away = 1`
- SportyBet: `hcp=-0.5` (Asian) → `handicap_home = -0.5, away = 0.5`
- Bet9ja: Param-based (e.g., `@-1`) → parsed correctly

The issue is purely in how the `line` field is populated for competitor markets — BetPawa uses it for matching, competitors don't.

</notes>

---

*Phase: 46-remaining-market-gaps*
*Context gathered: 2026-02-03*
