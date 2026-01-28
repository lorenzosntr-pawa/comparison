# UAT Issues: Phase 33 Plan 1

**Tested:** 2026-01-28
**Source:** .planning/phases/33-detailed-per-platform-progress/33-01-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

### UAT-001: SSE stream closes prematurely on first platform completion

**Discovered:** 2026-01-28
**Phase/Plan:** 33-01
**Severity:** Blocker
**Feature:** Per-platform progress events
**Description:** The frontend closes the EventSource connection when it receives the first `completed` phase event — which is now BetPawa's per-platform completion, not the overall scrape completion. This kills the stream before competitors even start scraping.
**Expected:** Stream stays open until the final overall completion event (platform=null, phase=completed, current=total)
**Actual:** Stream closes as soon as BetPawa completes, so SportyBet and Bet9ja progress is never received
**Repro:**
1. Start a scrape
2. Watch live progress — BetPawa completes
3. Stream closes immediately, competitor scraping never shown
**Root cause:** `live-progress.tsx:109` checks `data.phase === 'completed'` without distinguishing per-platform (`data.platform !== null`) from overall (`data.platform === null`) completion events

### UAT-002: Dashboard widget shows "complete" after BetPawa finishes

**Discovered:** 2026-01-28
**Phase/Plan:** 33-01
**Severity:** Major
**Feature:** Live progress display
**Description:** The dashboard widget reports the scrape as complete once BetPawa finishes, because the premature stream closure (UAT-001) means `overallPhase` is set to `completed` from BetPawa's per-platform event.
**Expected:** Widget shows ongoing progress through all three platforms, only "complete" after final event
**Actual:** Shows complete after ~1/3 of the scrape is done
**Repro:** Same as UAT-001 — consequence of the same root cause

### UAT-003: Completed platform progress lost from display during scraping

**Discovered:** 2026-01-28
**Phase/Plan:** 33-01
**Severity:** Major
**Feature:** Per-platform progress rows
**Description:** When competitors are scraping one at a time, the completed platform's details disappear or are not visible. The `platformProgress` Map should retain completed entries, but because the stream closes early (UAT-001), only BetPawa's data is ever captured.
**Expected:** All three platforms shown simultaneously — completed ones with counts/duration, active one with spinner, pending ones as "pending"
**Actual:** Only shows one competitor at a time; completed ones lose their logged info
**Repro:** Start scrape and watch live progress panel

## Resolved Issues

[None yet]

---

*Phase: 33-detailed-per-platform-progress*
*Plan: 01*
*Tested: 2026-01-28*
