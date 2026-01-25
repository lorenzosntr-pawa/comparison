# Phase 20: Settings Schema & API - Context

**Gathered:** 2026-01-25
**Status:** Ready for planning

<vision>
## How This Should Work

A single-row settings table with typed columns stores all application configuration. When the app starts, it reads settings from the database. When a setting changes via the API, the new value takes effect immediately and persists across restarts.

Fresh installs get sensible defaults that work out of the box — no configuration required to get started.

</vision>

<essential>
## What Must Be Nailed

- **Survives restarts** — Settings persist across server restarts and page refreshes. No more losing configuration.
- **Immediate effect** — When a setting changes, the system uses the new value right away without restart.
- **Sensible defaults** — Fresh install works out of the box with good default values.

</essential>

<boundaries>
## What's Out of Scope

- No settings history — don't track when settings changed or previous values
- No settings import/export — no JSON export or file-based backup
- No per-user settings — this is a single-user tool, no user accounts or profiles
- Keep it simple: persist, read, update — that's it

</boundaries>

<specifics>
## Specific Ideas

No specific requirements — standard CRUD patterns are fine.

</specifics>

<notes>
## Additional Context

Approach confirmed: single-row typed settings table with dedicated columns for each setting. One row is all that's needed for this single-user tool.

The existing Settings page (Phase 10) already displays settings with in-memory/hardcoded values. This phase creates the database layer; Phase 21 will integrate it with the existing UI.

</notes>

---

*Phase: 20-settings-schema-api*
*Context gathered: 2026-01-25*
