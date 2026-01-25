# Phase 21: Settings Persistence Integration - Context

**Gathered:** 2026-01-25
**Status:** Ready for planning

<vision>
## How This Should Work

Settings page already exists, but it's currently decorative — changing values doesn't persist and behavior is driven by hardcoded values buried in code.

After this phase, every setting visible on the settings page actually controls something. When you change a setting, the change persists and the entire app immediately sees the new value. Settings are cached for performance but refresh instantly when modified — like flipping a switch.

The hybrid approach: load settings once, cache them, but when a user changes something the update propagates immediately throughout the app. No page refresh required, no "save and restart" — just change it and it works.

</vision>

<essential>
## What Must Be Nailed

- **Settings actually drive behavior** - The history_retention_days and any other settings must actually control what happens, not just sit in the database
- **No hardcoded values** - Eliminate all magic numbers and buried constants. Everything configurable should come from settings
- **Immediate propagation** - When a user changes a setting, all components see the new value instantly. Smooth, responsive UX

</essential>

<boundaries>
## What's Out of Scope

- New settings types — don't add new configuration options, that's Phase 22+ (History Retention)
- Settings page UI changes — the UI already exists, this phase just wires it to actually work
- The actual history cleanup job — that's Phase 22, this phase just makes the setting readable

</boundaries>

<specifics>
## Specific Ideas

No specific requirements — open to whatever approach fits the existing codebase patterns. The app already uses TanStack Query and React context, so leverage whichever pattern makes sense for reactive settings propagation.

</specifics>

<notes>
## Additional Context

Current pain: settings page exists but doesn't actually control anything. Both persistence (settings reset on refresh) and behavior (hardcoded values) need fixing.

The core transformation: from "settings page that looks nice" to "settings that actually work."

</notes>

---

*Phase: 21-settings-persistence-integration*
*Context gathered: 2026-01-25*
