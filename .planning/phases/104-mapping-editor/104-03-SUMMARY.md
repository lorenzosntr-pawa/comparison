---
phase: 104-mapping-editor
plan: 03
subsystem: ui
tags: [react, mapping-editor, outcome-mapping, auto-suggest]

# Dependency graph
requires:
  - phase: 104-mapping-editor
    plan: 01
    provides: Editor foundation with source market panel
  - phase: 104-mapping-editor
    plan: 02
    provides: Target market form and mapping picker
provides:
  - Outcome auto-suggest algorithm with pattern matching
  - OutcomeMappingTable component for editing outcomes
  - Integrated outcome editing in target market panel
  - Auto-suggest button for regenerating outcome suggestions
affects: [104-04]

# Tech tracking
tech-stack:
  added: []
  patterns: [auto-suggest-algorithm, editable-table]

key-files:
  created:
    - web/src/features/mappings/editor/utils/outcome-suggest.ts
    - web/src/features/mappings/editor/components/outcome-mapping-table.tsx
  modified:
    - web/src/features/mappings/editor/components/target-market-panel.tsx
    - web/src/features/mappings/editor/index.tsx

key-decisions:
  - "Pattern-based canonical ID suggestion with confidence levels (high/medium/low)"
  - "Platform-specific column highlighting for visual clarity"
  - "Up/down buttons for reordering instead of drag-drop (simpler implementation)"

patterns-established:
  - "Utils directory under editor/ for pure business logic functions"
  - "Outcome form item type shared between suggestion and table components"

issues-created: []

# Metrics
duration: 8min
completed: 2026-02-13
---

# Phase 104 Plan 03: Outcome Mapping Table Summary

**Create outcome mapping table with auto-suggest from source market sample outcomes**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-13T14:00:00Z
- **Completed:** 2026-02-13T14:08:00Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- Created `suggestOutcomes` algorithm that analyzes sample_outcomes and generates canonical mappings
- Pattern matching for common outcome types (1X2, Over/Under, Yes/No, Double Chance, Odd/Even)
- Built OutcomeMappingTable with shadcn Table for full CRUD operations
- Integrated outcome mapping into editor with auto-suggest on create mode
- Load existing outcome mappings on extend mode
- Visual indicators for auto-suggested vs manually entered outcomes
- Auto-Suggest button to regenerate suggestions if needed

## Task Commits

Each task was committed atomically:

1. **Task 1: Create auto-suggest algorithm for outcomes** - `e6d4237` (feat)
2. **Task 2: Create outcome mapping table component** - `362b8a7` (feat)
3. **Task 3: Integrate outcome mapping into editor** - `0e8a2f8` (feat)

## Files Created/Modified

### Created
- `web/src/features/mappings/editor/utils/outcome-suggest.ts` - Auto-suggest algorithm with pattern matching
- `web/src/features/mappings/editor/components/outcome-mapping-table.tsx` - Editable outcome table

### Modified
- `web/src/features/mappings/editor/components/target-market-panel.tsx` - Added OutcomeMappingTable and auto-suggest logic
- `web/src/features/mappings/editor/index.tsx` - Lifted outcome state for future submit functionality

## Decisions Made

- Pattern-based matching with confidence levels:
  - High: exact match to known patterns (home, draw, over, etc.)
  - Medium: partial/fuzzy match
  - Low: no match, use sanitized original value
- Platform-specific field population based on source (sportybet_desc or bet9ja_suffix)
- Simple up/down buttons for reordering instead of drag-drop
- Minimum 1 outcome row enforced (delete disabled when only 1 row)

## Verification Checklist

- [x] `npm run build` succeeds without errors
- [x] Auto-suggest generates reasonable canonical IDs from sample outcomes
- [x] Outcome table allows add/remove/edit/reorder
- [x] Extend mode loads existing outcome mappings
- [x] Create mode auto-suggests from source market
- [x] Platform-specific fields highlighted appropriately

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- Outcome mapping editor fully functional with auto-suggest
- Form state and outcome state lifted to editor index, ready for submit in Plan 04
- All data structures aligned with API schema (OutcomeMappingSchema)

---
*Phase: 104-mapping-editor*
*Completed: 2026-02-13*
