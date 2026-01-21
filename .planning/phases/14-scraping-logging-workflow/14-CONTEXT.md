# Phase 14: Scraping Logging & Workflow - Context

**Gathered:** 2026-01-22
**Status:** Ready for research

<vision>
## How This Should Work

The scraping workflow should provide complete visibility at every level — real-time progress in both terminal and UI, clear error diagnosis without investigation, and a predictable state machine that never leaves you guessing about current state.

**Workflow Structure:**
BetPawa scrapes first (to get SportRadar IDs), then SportyBet and Bet9ja run in parallel since they just need those IDs. The workflow follows strict phases with clear transitions.

**Terminal Logging:**
Structured logs with timestamp precision, rich context (IDs, counts, data involved), and easy filtering by platform/error type/operation. When debugging, you can quickly trace what happened.

**UI Visibility:**
- **Dashboard widget:** Remove Quick Actions widget. Make Recent Scrape Runs widget full page width. Show 5-6 runs with rich row info: status, timing, per-platform status icons, live step info for active runs (e.g., "BetPawa: storing 48 events"), and error summary for failed runs. Click navigates to detail page.
- **Detail page:** Timeline view showing when each phase started/ended, live log stream like a terminal, and progress breakdown with cards/sections per bookmaker showing steps and status.
- **Errors:** Show errors both inline where they happened AND collected in a summary section.

**State Management:**
- Persisted state — if backend restarts, know exactly where it stopped
- Real-time sync — UI always reflects true backend state, never stale
- State history — can see how state transitioned during a run (audit trail)

**Timing:**
Clear visibility into how long each phase and step takes, not just that they completed.

</vision>

<essential>
## What Must Be Nailed

- **State clarity** — Always know exactly what state each scrape is in, no ambiguity
- **Error transparency** — When failures happen, the cause is immediately obvious without investigation
- **Debugging speed** — When something goes wrong, quickly trace what happened and fix it
- **Real-time sync** — UI never shows stale state, always reflects true backend status

</essential>

<boundaries>
## What's Out of Scope

- No new scraping features — this is about logging/state, not adding new platforms or markets
- No alerts/notifications — just visibility into state, alerting can come later
- No changes to other dashboard widgets — just remove Quick Actions and expand Scrape Runs

</boundaries>

<specifics>
## Specific Ideas

**Current pain points to fix:**
- State gets out of sync — UI shows wrong status (says running when done, or vice versa)
- Hard to tell what failed — when errors happen, not clear which platform or why
- Missing intermediate states — jumps from "running" to "done" without showing what's happening
- Timing information unclear — hard to tell how long things take

**Detail level:**
- Per-bookmaker phases: BetPawa: fetching events → storing → done, then SportyBet, etc.
- Per-operation steps within each: "Fetching 50 events", "Stored 48/50", "Mapping markets"...

**Dashboard widget row content:**
- Run status, duration, per-platform status icons
- For active runs: current operation text
- For failed runs: error count or brief error message

</specifics>

<notes>
## Additional Context

User wants both terminal and UI visibility — terminal for dev/debugging, UI for monitoring. The expanded scrape runs widget with full-width layout will accommodate the richer per-run information needed to show all the new logging detail.

Widget priority: dashboard widget and detail page are equally important — both need the improved state/logging.

</notes>

---

*Phase: 14-scraping-logging-workflow*
*Context gathered: 2026-01-22*
