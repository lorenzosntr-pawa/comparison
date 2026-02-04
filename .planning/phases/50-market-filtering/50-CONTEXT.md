# Phase 50: Market Filtering - Context

**Gathered:** 2026-02-04
**Status:** Ready for planning

<vision>
## How This Should Work

A compact filter bar sits above the market grid, giving quick access to all filtering controls in one horizontal row. When I pick a competitor (SportyBet or Bet9ja), the columns rearrange to put Betpawa right next to them for easy side-by-side comparison - no scrolling or mental mapping needed.

The search box filters markets instantly as I type. If I'm looking for "over 2.5 goals" I should be able to type "o25" or "over 2.5" and see matching markets immediately. The filtering happens live without needing to press a button.

Both features work together - I can select SportyBet as my comparison target AND search for "handicap" to find exactly the handicap markets where I want to compare Betpawa vs SportyBet odds.

</vision>

<essential>
## What Must Be Nailed

- **Competitor side-by-side comparison** - When selecting a competitor, reorder columns to place Betpawa adjacent to them for immediate visual comparison
- **Instant fuzzy search** - Markets filter as you type, with fuzzy matching that finds partial matches (typing "o25" finds "Over 2.5 Goals")
- **Compact unified bar** - All controls in one minimal-height row, not scattered or stacked

</essential>

<boundaries>
## What's Out of Scope

- Saved filters/presets - no ability to save filter combinations for reuse
- Multi-competitor selection - pick only one competitor at a time, not multiple
- Advanced filter operators - no AND/OR logic, range filters, or complex queries

</boundaries>

<specifics>
## Specific Ideas

- Compact inline bar with all controls in one horizontal row, minimal height
- Competitor selector as dropdown or toggle buttons
- Search input with instant filtering (no search button)
- Fuzzy matching that handles partial market names and common abbreviations

</specifics>

<notes>
## Additional Context

This builds on Phase 49's tabbed market grouping. The filter bar should work alongside the category tabs - filters apply within the currently selected tab, or across all tabs if viewing "All".

</notes>

---

*Phase: 50-market-filtering*
*Context gathered: 2026-02-04*
