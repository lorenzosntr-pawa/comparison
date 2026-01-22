---
phase: 12-ui-polish
plan: 01
subsystem: ui
tags: [react, shadcn, tailwind, branding, layout]

# Dependency graph
requires:
  - phase: 06-react-foundation
    provides: React app with shadcn sidebar component
provides:
  - pawaRisk branding across application
  - Sidebar collapse behavior without content overlay
affects: [all-ui-pages]

# Tech tracking
tech-stack:
  added: []
  patterns: [peer-selector-responsive-layout]

key-files:
  created: []
  modified:
    - web/index.html
    - web/src/components/layout/app-sidebar.tsx
    - web/src/components/ui/sidebar.tsx
    - web/src/components/layout/app-layout.tsx

key-decisions:
  - "Use peer selectors to apply responsive margins based on sidebar state"
  - "Set sidebar to start collapsed by default for better initial UX"
  - "Keep Activity icon for pawaRisk branding (works for risk/comparison tool)"

patterns-established:
  - "Peer data attribute selectors for component state-based styling"
  - "CSS variable usage for dynamic spacing (--sidebar-width-icon)"

issues-created: []

# Metrics
duration: 14min
completed: 2026-01-22
---

# Phase 12 Plan 01: Rebrand & Sidebar Fix Summary

**pawaRisk branding established with collapsed-by-default sidebar that properly manages content spacing in both expanded and collapsed states**

## Performance

- **Duration:** 14 min
- **Started:** 2026-01-22T11:52:36Z
- **Completed:** 2026-01-22T12:06:50Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- Complete rebrand from "Betpawa Odds Comparison" to "pawaRisk" across all UI touchpoints
- Navigation item renamed from "Matches" to "Odds Comparison" for clarity
- Sidebar now starts in collapsed (icon-only) mode by default
- Fixed sidebar overlay issue with state-aware margin control

## Task Commits

Each task was committed atomically:

1. **Task 1: Rebrand to pawaRisk** - `873f3de` (feat)
2. **Task 2: Fix sidebar collapse behavior** - `8ae9e5a` (fix)
3. **Task 2 refinement: Prevent overlay in both states** - `6d2ecda` (fix)

**Plan metadata:** (committed below)

## Files Created/Modified

- `web/index.html` - Updated title and localStorage theme key to "pawaRisk"
- `web/src/components/layout/app-sidebar.tsx` - Changed header text and nav item names
- `web/src/components/layout/app-layout.tsx` - Set SidebarProvider defaultOpen to false
- `web/src/components/ui/sidebar.tsx` - Added peer selector margin control for SidebarInset

## Decisions Made

**Sidebar collapse state management:**
- Used peer data attribute selectors (`peer-data-[state=collapsed]`) to apply responsive margins
- Expanded state: `ml-0` (no extra margin, layout spacer handles positioning)
- Collapsed state: `ml-[var(--sidebar-width-icon)]` (explicit margin to prevent overlay)
- This approach allows the sidebar component to control main content positioning without JavaScript

**Branding approach:**
- Kept Activity icon (works well for risk/comparison dashboard context)
- Used consistent "pawaRisk" casing across all touchpoints
- Updated localStorage key to "pawarisk-theme" for consistency

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

**Sidebar overlay on collapsed state:**
- Initial implementation had sidebar starting collapsed but main content was being overlaid
- shadcn Sidebar uses fixed positioning with a transparent spacer div for layout
- The spacer div width changes based on state, but SidebarInset wasn't responding to collapsed state
- Fixed by adding explicit margin-left to SidebarInset using peer selectors to detect sidebar state
- Refined to ensure both expanded (no extra margin) and collapsed (icon-width margin) states work correctly

## Next Phase Readiness

- Branding complete - all UI now consistently shows "pawaRisk"
- Sidebar behavior fixed - ready for remaining Phase 12 UI polish tasks
- No blockers for Phase 12 Plans 02 and 03

---
*Phase: 12-ui-polish*
*Completed: 2026-01-22*
