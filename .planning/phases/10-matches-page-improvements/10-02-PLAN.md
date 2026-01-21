---
phase: 10-matches-page-improvements
plan: 02
type: execute
---

<objective>
Improve match filters with date presets, team search input, and searchable multi-select league filter.

Purpose: Make filtering practical — quick date selection, instant team search, easy league browsing.
Output: Enhanced MatchFilters component with all three filter improvements working.
</objective>

<execution_context>
~/.claude/get-shit-done/workflows/execute-phase.md
~/.claude/get-shit-done/templates/summary.md
~/.claude/get-shit-done/references/checkpoints.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/10-matches-page-improvements/10-CONTEXT.md

**Key files:**
@web/src/features/matches/components/match-filters.tsx
@web/src/features/matches/hooks/use-matches.ts
@web/src/features/matches/hooks/use-tournaments.ts
@web/src/features/matches/index.tsx
@web/src/lib/api.ts
@web/src/types/api.ts

**Prior phase context:**
- Phase 07-02: Created MatchFilters with basic tournament select, date inputs, min bookmakers
- useTournaments hook extracts unique tournaments from events
- Filter state managed in parent MatchList component
- shadcn components available: select, popover, checkbox, button, input, skeleton

**From 10-CONTEXT.md:**
- Date filter: both quick presets AND custom date picker
- Team search: part of filter row, not separate prominent search box
- Competition dropdown: must be searchable and scrollable
- Default sort by kickoff time, sortable columns via header clicks
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add date filter presets</name>
  <files>web/src/features/matches/components/match-filters.tsx</files>
  <action>
Add date preset buttons row above or integrated with the date range inputs:

1. Create helper functions for date calculation:
   ```typescript
   function getDatePreset(preset: 'today' | 'tomorrow' | 'weekend' | 'next7days'): { from: string; to: string } {
     const now = new Date()
     const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())

     switch (preset) {
       case 'today': {
         const end = new Date(today)
         end.setDate(end.getDate() + 1)
         return { from: today.toISOString(), to: end.toISOString() }
       }
       case 'tomorrow': {
         const start = new Date(today)
         start.setDate(start.getDate() + 1)
         const end = new Date(start)
         end.setDate(end.getDate() + 1)
         return { from: start.toISOString(), to: end.toISOString() }
       }
       case 'weekend': {
         // Find next Saturday
         const saturday = new Date(today)
         saturday.setDate(saturday.getDate() + ((6 - saturday.getDay() + 7) % 7 || 7))
         const monday = new Date(saturday)
         monday.setDate(monday.getDate() + 2)
         return { from: saturday.toISOString(), to: monday.toISOString() }
       }
       case 'next7days': {
         const end = new Date(today)
         end.setDate(end.getDate() + 7)
         return { from: today.toISOString(), to: end.toISOString() }
       }
     }
   }
   ```

2. Add preset buttons with `variant="outline"` and `size="sm"`:
   - Today, Tomorrow, Weekend, Next 7 Days
   - On click, convert to datetime-local format for the inputs and update filters

3. Style as a row of small toggle-like buttons before the From/To inputs.

Keep existing custom date inputs for manual selection.
  </action>
  <verify>
Clicking "Today" button sets date range to today only.
Clicking "Weekend" sets Saturday-Sunday range.
Custom date inputs still work independently.
  </verify>
  <done>Date presets (Today, Tomorrow, Weekend, Next 7 Days) work alongside custom date range inputs.</done>
</task>

<task type="auto">
  <name>Task 2: Add team search input to filter row</name>
  <files>web/src/features/matches/components/match-filters.tsx, web/src/features/matches/index.tsx, web/src/features/matches/hooks/use-matches.ts, web/src/lib/api.ts</files>
  <action>
1. Update `MatchFiltersState` interface to add `search: string` field.

2. Update `DEFAULT_FILTERS` in `index.tsx` to include `search: ''`.

3. In `MatchFilters` component, add search input field:
   ```tsx
   <div className="flex flex-col gap-1.5">
     <label className="text-xs font-medium text-muted-foreground">Team</label>
     <Input
       type="text"
       placeholder="Search team..."
       value={filters.search}
       onChange={(e) => updateFilter('search', e.target.value)}
       className="w-[160px]"
     />
   </div>
   ```
   Position it as first filter (before Tournament dropdown).

4. Update `hasActiveFilters` check to include `filters.search !== ''`.

5. Update `clearFilters` to reset `search: ''`.

6. In `useMatches` hook, add `search?: string` to params and pass to api.getEvents.

7. In `api.ts`, add `search?: string` parameter to `getEvents` method and include in query string.

Use debouncing consideration: For simplicity, trigger on change (not debounced). If performance is an issue, can add debounce later.
  </action>
  <verify>
Typing "Arsenal" in search input filters events to show only matches with Arsenal.
Clearing search shows all matches again.
Search works in combination with other filters.
  </verify>
  <done>Team search input in filter row, filters events by team name as user types.</done>
</task>

<task type="auto">
  <name>Task 3: Create searchable multi-select league filter</name>
  <files>web/src/features/matches/components/match-filters.tsx, web/src/features/matches/index.tsx, web/src/features/matches/hooks/use-matches.ts, web/src/lib/api.ts, src/api/routes/events.py</files>
  <action>
**Backend:**

1. In `src/api/routes/events.py`, update `tournament_id` parameter to accept multiple values:
   ```python
   tournament_ids: list[int] | None = Query(default=None, description="Filter by tournament IDs"),
   ```
   Update query to use `Event.tournament_id.in_(tournament_ids)` when list is provided.

**Frontend:**

2. Update `MatchFiltersState` to use `tournamentIds: number[]` instead of single `tournamentId`.

3. Install shadcn Command component for combobox pattern:
   ```bash
   cd web && npx shadcn@latest add command --yes
   ```

4. Replace tournament Select with a Popover + Command pattern:
   - Trigger button shows "X leagues selected" or "All leagues"
   - Command component with search input and scrollable list
   - Checkboxes for multi-select behavior
   - "Clear all" and "Select all" at bottom
   - Max height with scroll (max-h-[300px])

   Pattern:
   ```tsx
   <Popover>
     <PopoverTrigger asChild>
       <Button variant="outline" className="w-[200px] justify-between">
         {filters.tournamentIds.length === 0
           ? "All leagues"
           : `${filters.tournamentIds.length} leagues`}
         <ChevronsUpDown className="ml-2 h-4 w-4" />
       </Button>
     </PopoverTrigger>
     <PopoverContent className="w-[300px] p-0">
       <Command>
         <CommandInput placeholder="Search leagues..." />
         <CommandList className="max-h-[300px]">
           <CommandEmpty>No leagues found.</CommandEmpty>
           <CommandGroup>
             {tournaments?.map((t) => (
               <CommandItem
                 key={t.id}
                 onSelect={() => toggleTournament(t.id)}
               >
                 <Checkbox checked={filters.tournamentIds.includes(t.id)} />
                 <span className="ml-2">{t.name}</span>
               </CommandItem>
             ))}
           </CommandGroup>
         </CommandList>
       </Command>
     </PopoverContent>
   </Popover>
   ```

5. Update `useMatches` and `api.ts` to pass `tournament_ids` as comma-separated list or repeated params.

6. Update DEFAULT_FILTERS to use `tournamentIds: []`.
  </action>
  <verify>
League filter shows searchable dropdown with checkboxes.
Can select multiple leagues and filter shows count.
Search within dropdown filters league list.
API receives tournament_ids parameter correctly.
  </verify>
  <done>Searchable multi-select league filter with scrollable list and search within dropdown.</done>
</task>

</tasks>

<verification>
Before declaring plan complete:
- [ ] Date presets work (Today/Tomorrow/Weekend/Next 7 Days)
- [ ] Team search filters by home/away team name
- [ ] League filter is searchable and multi-select
- [ ] All filters work in combination
- [ ] No TypeScript errors: `cd web && npm run build`
- [ ] Backend accepts new query parameters
</verification>

<success_criteria>
- All three filter improvements working
- Filters can be combined (search + date + leagues)
- Clear filters resets all to defaults
- Build passes without errors
- Phase 10 complete
</success_criteria>

<output>
After completion, create `.planning/phases/10-matches-page-improvements/10-02-SUMMARY.md`
</output>
