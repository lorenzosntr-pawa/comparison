# Plan: 96-01-FIX — Sidebar Status Widget Improvements

**Phase:** 96 (Navigation Overhaul)
**Type:** UAT Fix
**Issue:** Phase 96 UAT revealed sidebar status section is confusing and incomplete

## Problem Statement

Phase 96 added sidebar status widgets but UAT revealed:
1. Status dots are confusing — tiny colored dots with hover-only tooltips aren't understandable
2. Events only shows total — should show total AND matched count
3. Missing scrape runs widget — was in spec but not delivered

## Tasks

### Task 1: Replace status dots with readable labels
**File:** `web/src/components/layout/app-sidebar.tsx`

Change from confusing dots to clear labeled status:
- Database: Show "DB" with checkmark/x icon
- Scheduler: Show "Scheduler" with status text (Running/Paused/Stopped)

### Task 2: Show total AND matched event counts
**File:** `web/src/components/layout/app-sidebar.tsx`

Change from:
```
Events    523
```
To:
```
Events    523 total
          489 matched
```

Or compact: `523 / 489`

### Task 3: Add recent scrape runs widget
**File:** `web/src/components/layout/app-sidebar.tsx`

Add section showing:
- Last scrape run time (relative, e.g., "2m ago")
- Last run status indicator
- Brief stats (events scraped)

Uses existing `useScrapeRuns` hook.

## Implementation

Single file edit to `app-sidebar.tsx` with improved Status section.

## Verification

1. Visual inspection of sidebar
2. Status displays correctly for DB healthy/unhealthy
3. Scheduler shows Running/Paused/Stopped correctly
4. Events shows both total and matched
5. Scrape runs shows recent activity
