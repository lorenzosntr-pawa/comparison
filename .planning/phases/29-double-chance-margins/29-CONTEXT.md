# Phase 29: Double Chance & Margins - Context

**Gathered:** 2026-01-26
**Status:** Ready for planning

<vision>
## How This Should Work

Double Chance is added as another available column option alongside the existing markets (1X2, BTTS, O/U 2.5). When selected, it displays three columns: 1X, X2, and 12.

Each market gets its own margin column showing the bookmaker's margin percentage for that specific market. So if you're viewing 1X2 odds, you see the 1X2 margin. If viewing Double Chance, you see the Double Chance margin. This gives clear visibility into how competitive each bookmaker is on each market type.

</vision>

<essential>
## What Must Be Nailed

- **Double Chance columns** - Display 1X, X2, 12 odds correctly as a selectable market option
- **Per-market margin display** - Each market shows its own margin percentage per bookmaker row
- Both features are equally important to this phase

</essential>

<boundaries>
## What's Out of Scope

- Additional markets beyond Double Chance (Asian handicap, correct score, etc.) - only Double Chance in this phase
- Historical margin tracking - just show current snapshot margins, no trend data
- Margin history or analytics

</boundaries>

<specifics>
## Specific Ideas

- **Color-coded margins** - Green for low/competitive margins, red for high margins
- **Best margin highlighting** - Highlight which bookmaker has the best (lowest) margin for each market
- Double Chance follows the same column toggle pattern as existing markets (1X2, BTTS, O/U 2.5)

</specifics>

<notes>
## Additional Context

This builds on the Phase 28 table restructure with bookmakers-as-rows layout. Each bookmaker row will show odds for selected markets plus margin columns.

The margin calculation for Double Chance: 1/(1X odds) + 1/(X2 odds) + 1/(12 odds) should equal >1, with the excess being the margin.

</notes>

---

*Phase: 29-double-chance-margins*
*Context gathered: 2026-01-26*
