# Phase 22: History Retention - Context

**Gathered:** 2026-01-25
**Status:** Ready for planning

<vision>
## How This Should Work

Both automatic background cleanup AND manual control over data retention.

**Background Automation:**
- Scheduled cleanup job runs on a configurable frequency
- Waits for any active scraping to finish before running
- Shows status indicator when cleanup is in progress
- Logs detailed history of what was deleted (records per table, date ranges)

**Manual Control:**
- "Manage Data" button on Settings opens a dialog
- Dialog shows full data overview: breakdown by platform, dates, record counts, storage size
- Manual "Clean Now" with ability to specify date or range to clean
- Preview before delete showing exactly what will be removed

</vision>

<essential>
## What Must Be Nailed

- **Two retention settings**: Odds retention (by snapshot timestamp) and Match retention (by kickoff time)
- **Background automation**: Scheduled cleanup that runs reliably without intervention
- **Manual control + visibility**: Ability to see data breakdown and clean up on demand
- **Deletion preview**: Show what will be deleted before committing

</essential>

<boundaries>
## What's Out of Scope

- Selective deletion by platform/tournament - just by date
- Data archiving/backup before delete - no undo, just delete
- Special guardrails - trust user settings, no minimum retention limits

</boundaries>

<specifics>
## Specific Ideas

**Retention Logic:**
- `odds_retention_days`: Delete odds snapshots older than X days (by snapshot timestamp). Also applies to scrape run history.
- `match_retention_days`: Delete matches older than Y days (by kickoff time). Cascades to their odds.
- Tournaments auto-delete when they have no remaining matches
- Default values: 30 days for both

**Settings Page Layout Redesign (4 rows, compact cards):**
- Row 1: Scheduler control | Scraping interval (2 compact cards)
- Row 2: Platform selection (full-width card, bookmakers displayed horizontally in a row)
- Row 3: Odds retention | Match retention (2 compact cards)
- Row 4: Cleanup frequency | Manage Data button

**Manage Data Dialog:**
- Full data overview (breakdown by platform, dates, counts, storage)
- Manual cleanup controls with date/range selection
- Cleanup history log with detailed breakdown

**Cleanup Behavior:**
- Wait for scraping to finish before cleanup runs
- Status indicator when cleanup is in progress
- Detailed logging: records deleted per table, date range cleaned

</specifics>

<notes>
## Additional Context

This phase includes a Settings page UI redesign to make the layout more compact and organized. Current cards are too large; new layout uses smaller cards in a 2-column grid with platform selection as a full-width row.

The deletion process should be technically sound (batched if needed to avoid long locks), but no user-facing preference on this - figure out what works best.

</notes>

---

*Phase: 22-history-retention*
*Context gathered: 2026-01-25*
