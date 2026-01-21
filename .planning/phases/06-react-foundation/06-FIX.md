---
phase: 06-react-foundation
plan: 06-FIX
type: fix
---

<objective>
Fix 1 UAT issue from Phase 6 user acceptance testing.

Source: 06-ISSUES.md
Priority: 0 critical, 1 major, 0 minor

The sidebar overlay issue (UAT-001) needs to be fixed so the main content expands when the sidebar collapses.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-phase.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/ROADMAP.md

**Issues being fixed:**
@.planning/phases/06-react-foundation/06-ISSUES.md

**Original plan for reference:**
@.planning/phases/06-react-foundation/06-03-PLAN.md

**Relevant source files:**
@web/src/components/layout/app-layout.tsx
@web/src/components/layout/app-sidebar.tsx
@web/src/components/ui/sidebar.tsx
@web/src/index.css
</context>

<tasks>
<task type="auto">
  <name>Fix UAT-001: Sidebar overlay on collapse</name>
  <files>web/src/index.css, web/src/components/layout/app-layout.tsx</files>
  <action>
The shadcn sidebar with `collapsible="icon"` creates a spacer div that shrinks when collapsed, but the main content needs proper margin/padding to respect the sidebar width.

Two fixes needed:

1. **Add sidebar CSS variables for the SidebarInset margin:**
   In `web/src/index.css`, add to `:root`:
   ```css
   --sidebar-width: 16rem;
   --sidebar-width-icon: 3rem;
   ```

2. **Update SidebarInset wrapper to use peer-based margin:**
   The SidebarInset uses `peer-data-[state=collapsed]` selectors. The parent wrapper needs to properly transfer the margin.

   In `web/src/components/layout/app-layout.tsx`, add explicit margin-left handling for the main container that responds to the sidebar state via CSS. The peer selector should make the main content shift when sidebar is collapsed vs expanded.

Alternative approach: Wrap the SidebarInset content in a div that uses `ml-[--sidebar-width]` transitioning to `ml-[--sidebar-width-icon]` based on collapsed state.

Test by collapsing sidebar - main content should expand to fill the vacated space.
  </action>
  <verify>
1. Run `pnpm run dev` in web directory
2. Open http://localhost:3000
3. Click sidebar collapse button (or Ctrl+B)
4. Verify: main content expands to fill space, sidebar shows only icons
5. Click again to expand - content shrinks back, sidebar shows full labels
  </verify>
  <done>
- Collapsed sidebar shows only icons (no labels)
- Main content area expands to fill vacated space
- No overlay/covering of main content
- Smooth transition between states
  </done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>Fixed sidebar collapse behavior so main content expands</what-built>
  <how-to-verify>
    1. Run: cd web && pnpm run dev
    2. Open: http://localhost:3000
    3. Click the collapse button (left side of header) or press Ctrl+B
    4. Verify: Sidebar shrinks to icons only, main content expands to fill the space
    5. Click collapse button again or Ctrl+B to expand
    6. Verify: Sidebar shows full labels, main content adjusts
    7. Check: No overlay, no content hidden behind sidebar
  </how-to-verify>
  <resume-signal>Type "approved" if sidebar collapses correctly, or describe remaining issues</resume-signal>
</task>
</tasks>

<verification>
Before declaring plan complete:
- [ ] Sidebar collapses to icons-only mode
- [ ] Main content expands when sidebar collapses
- [ ] No overlay or content hidden behind sidebar
- [ ] Smooth CSS transition between states
- [ ] Works in both light and dark themes
</verification>

<success_criteria>
- UAT-001 from 06-ISSUES.md resolved
- Sidebar collapse behavior matches expected UX
- Build passes without errors
- Ready for re-verification
</success_criteria>

<output>
After completion, create `.planning/phases/06-react-foundation/06-FIX-SUMMARY.md`
</output>
