# Phase 07-02 Summary: Match List View

## Completed Tasks

### Task 1: Create match list table with odds columns
- Updated TypeScript types in `web/src/types/api.ts`:
  - Added `OutcomeOdds` interface with name and odds
  - Added `InlineOdds` interface with market_id, market_name, and outcomes
  - Extended `BookmakerOdds` with `inline_odds: InlineOdds[]`
- Extended `api.getEvents` with full filter parameter support
- Created `useMatches` hook with TanStack Query (60s polling, 30s stale, 60s gcTime)
- Created `OddsCell` and `ComparisonOddsCell` components for odds display
- Created `MatchTable` component with:
  - Native HTML table with Tailwind styling
  - Match, Kickoff, Tournament fixed columns
  - Dynamic market columns grouped by bookmaker (BP, SB, B9)
  - Green/red color coding based on Betpawa vs competitor odds
  - Gradient intensity based on delta magnitude
  - Row click navigation to match detail
  - Loading skeleton and empty states

### Task 2: Add filters and sorting controls
- Installed shadcn `select` component
- Created `useTournaments` hook (extracts unique tournaments from events)
- Created `MatchFilters` component with:
  - Tournament dropdown filter
  - Kickoff date range (from/to) inputs
  - Min bookmakers selector (1+/2+/3)
  - Sort by dropdown (Kickoff, Tournament)
  - Clear filters button
- Added pagination with:
  - Previous/Next buttons
  - Page X of Y display
  - Page size selector (25/50/100)
- Integrated with `useMatches` hook filter params

### Task 3: Column configuration with localStorage persistence
- Installed shadcn `popover` and `checkbox` components
- Created `useColumnSettings` hook with:
  - Default visible columns: 1X2, O/U 2.5, BTTS
  - Load/save from localStorage key `match-list-columns`
  - toggleColumn, isColumnVisible, showAll, hideAll functions
- Created `ColumnSettings` popover component with:
  - Column visibility checkboxes
  - Show all / Hide all quick actions
  - Prevents hiding all columns (at least one required)
- Integrated with MatchTable `visibleColumns` prop

## Files Created
- `web/src/features/matches/hooks/use-matches.ts`
- `web/src/features/matches/hooks/use-tournaments.ts`
- `web/src/features/matches/hooks/use-column-settings.ts`
- `web/src/features/matches/hooks/index.ts`
- `web/src/features/matches/components/match-table.tsx`
- `web/src/features/matches/components/odds-cell.tsx`
- `web/src/features/matches/components/match-filters.tsx`
- `web/src/features/matches/components/column-settings.tsx`
- `web/src/features/matches/components/index.ts`
- `web/src/components/ui/select.tsx`
- `web/src/components/ui/popover.tsx`
- `web/src/components/ui/checkbox.tsx`

## Files Modified
- `web/src/types/api.ts` - Added inline odds types
- `web/src/lib/api.ts` - Extended getEvents with filter params
- `web/src/features/matches/index.tsx` - Wired up components and hooks

## Technical Notes
- Color coding logic: green when Betpawa odds > competitor (better for punter), red when lower
- Tolerance of 0.02 for neutral display (odds considered equal within tolerance)
- Gradient intensity: `Math.min(Math.abs(delta) * 25, 1)` mapped to Tailwind opacity levels
- Client-side sorting for tournament (API sorts by kickoff by default)
- React Router v7 used (not react-router-dom)
- TanStack Query caching: staleTime 30s, gcTime 60s, refetchInterval 60s

## Deviations
None - all tasks completed as specified.
