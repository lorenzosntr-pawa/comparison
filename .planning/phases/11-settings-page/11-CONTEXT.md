# Phase 11: Settings Page - Context

**Gathered:** 2026-01-21
**Status:** Ready for planning

<vision>
## How This Should Work

A dedicated settings page focused on scraping configuration. Users can control the scheduler behavior — adjust how frequently scraping runs, start/stop the scheduler, and toggle individual platforms (SportyBet, Bet9ja, BetPawa) on or off.

The page provides full control over the scraping pipeline without needing to touch code or restart the server. Changes should take effect immediately or on the next scrape cycle.

</vision>

<essential>
## What Must Be Nailed

- **Scheduler interval control** - Adjust scraping frequency (e.g., every 5/10/15/30 minutes)
- **Platform toggles** - Enable/disable specific bookmakers for scraping
- **Start/stop control** - Easy pause and resume of the scheduler

All three are equally important — this is the complete scraping control panel.

</essential>

<boundaries>
## What's Out of Scope

- User accounts/authentication - No login, multi-user settings, or permissions
- Alert notifications - No email/push alerts for odds thresholds (future feature)
- Display preferences - Theme, column settings, filters can wait for UI Polish phase

This phase is purely about scraping configuration.

</boundaries>

<specifics>
## Specific Ideas

- Use existing shadcn components to match the rest of the app's UI style
- Keep it consistent with the established design patterns

</specifics>

<notes>
## Additional Context

The settings page already exists in the app but is currently empty. This phase fills it with functional scraping controls.

Settings should persist (either localStorage or database-backed) so they survive page refreshes and server restarts.

</notes>

---

*Phase: 11-settings-page*
*Context gathered: 2026-01-21*
