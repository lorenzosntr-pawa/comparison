# UAT Issues: Phase 96 Plan 01

**Tested:** 2026-02-12
**Source:** .planning/phases/96-navigation-overhaul/96-01-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

### UAT-001: Status section health indicator inconsistency with Dashboard

**Discovered:** 2026-02-12
**Phase/Plan:** 96-01
**Severity:** Major
**Feature:** Sidebar Status Section
**Description:** Database health indicator shows error in sidebar but green in Dashboard. Additionally, WebSocket connection status is missing from sidebar status section.
**Expected:** Sidebar status indicators should match Dashboard health indicators, and WS connection status should be visible
**Actual:** Database shows error (red/yellow) in sidebar but green in Dashboard; no WebSocket connection indicator in sidebar
**Repro:**
1. Observe sidebar Status section health dots
2. Navigate to /dashboard
3. Compare health indicators - they don't match
4. Note missing WebSocket connection status in sidebar

### UAT-002: Missing current scrape run info in sidebar

**Discovered:** 2026-02-12
**Phase/Plan:** 96-01
**Severity:** Major
**Feature:** Sidebar Status Section
**Description:** Sidebar status section doesn't show information about currently running scrape (if one is in progress). This info is available on Dashboard but not in sidebar.
**Expected:** When a scrape is running, sidebar should show scrape progress/status
**Actual:** No scrape run information in sidebar
**Context:** Needed to eventually remove Dashboard page - all key info should be in sidebar

### UAT-003: Missing manual scrape run button in sidebar

**Discovered:** 2026-02-12
**Phase/Plan:** 96-01
**Severity:** Major
**Feature:** Sidebar Status Section
**Description:** No way to trigger a manual scrape from the sidebar. Currently requires navigating to Dashboard or Scrape Runs.
**Expected:** Quick action button in sidebar to trigger manual scrape
**Actual:** No manual scrape trigger in sidebar
**Context:** Needed to eventually remove Dashboard page - key actions should be accessible from sidebar

### UAT-004: Missing countdown to next scrape in sidebar

**Discovered:** 2026-02-12
**Phase/Plan:** 96-01
**Severity:** Major
**Feature:** Sidebar Status Section
**Description:** Sidebar doesn't show countdown/time until next scheduled scrape. This info is available on Dashboard but not in sidebar.
**Expected:** Sidebar should show when next scrape will run (e.g., "Next: 2m 30s")
**Actual:** No countdown to next scrape in sidebar
**Context:** Needed to eventually remove Dashboard page - schedule info should be in sidebar

## Resolved Issues

[None yet]

---

*Phase: 96-navigation-overhaul*
*Plan: 01*
*Tested: 2026-02-12*
