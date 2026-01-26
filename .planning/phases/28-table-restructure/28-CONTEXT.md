# Phase 28: Table Restructure - Context

**Gathered:** 2026-01-26
**Status:** Ready for planning

<vision>
## How This Should Work

The Matches table transforms from bookmakers-as-columns to bookmakers-as-rows. Each match displays 3 stacked rows (one per bookmaker), making it easy to compare odds vertically — scan down to see which bookmaker offers the best odds for each outcome.

The match information (Region, Tournament, Kickoff, Match name) sits in rowspan cells on the left, visually anchoring all 3 bookmaker rows as one unit. The bookmaker name and odds columns appear to the right, repeating for each bookmaker.

Match names display as "Team A - Team B" format.

</vision>

<essential>
## What Must Be Nailed

- **Easy odds comparison** — At a glance, user can see which bookmaker has the best odds for each outcome (1, X, 2)
- **Clean visual grouping** — The 3 rows per match must feel like one cohesive unit, not 3 separate table rows
- **Column order and flow** — Information hierarchy must be right: Region → Tournament → Kickoff → Match → Bookmaker → Odds

</essential>

<boundaries>
## What's Out of Scope

- Double Chance market columns (1X, X2, 12) — that's Phase 29
- Per-market margin calculations — that's Phase 29
- This phase is purely layout/structure work, no new data columns

</boundaries>

<specifics>
## Specific Ideas

**Column order (left to right):**
1. Region (rowspan all 3)
2. Tournament (rowspan all 3)
3. Kickoff (rowspan all 3)
4. Match - "Team A - Team B" format (rowspan all 3)
5. Bookmaker (per row)
6. 1 (Home odds, per row)
7. X (Draw odds, per row)
8. 2 (Away odds, per row)

**Rowspan structure:**
- First 4 columns span all 3 bookmaker rows vertically
- Bookmaker + odds columns repeat for each of the 3 rows

</specifics>

<notes>
## Additional Context

Current table has bookmakers as columns — this flips the axis so bookmakers stack vertically per match, enabling easier vertical scanning for best odds.

</notes>

---

*Phase: 28-table-restructure*
*Context gathered: 2026-01-26*
