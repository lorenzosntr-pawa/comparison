# Phase 44: High-Priority Market Mappings - Context

**Gathered:** 2026-02-02
**Status:** Ready for planning

<vision>
## How This Should Work

Fix the highest-impact unmapped markets systematically. The Phase 43 audit identified 380 unique unmapped market types with a prioritized list by frequency. We tackle all HIGH priority markets, starting with NO_MATCHING_OUTCOMES errors (we're closest to working there), then moving to UNKNOWN_MARKET and UNKNOWN_PARAM_MARKET errors.

Both platforms (SportyBet and Bet9ja) are worked on together — when fixing a market type, add mappings for both if applicable. Each mapping is verified individually, not batched, to ensure accuracy.

The work is split into 2-3 sub-phases by error type:
- 44-01: NO_MATCHING_OUTCOMES (outcome alignment fixes)
- 44-02: UNKNOWN_MARKET (new market mappings)
- 44-03: UNKNOWN_PARAM_MARKET (parameter handling)

Validation happens at two levels: spot-check in UI during development, then re-run the full audit at the end to measure improvement.

</vision>

<essential>
## What Must Be Nailed

- **All HIGH priority markets addressed** — Every market flagged HIGH in the audit (minus exclusions) gets a mapping attempt
- **Verify each mapping individually** — No batching similar markets; each one confirmed to work
- **Don't break existing mappings** — Modify carefully, verify existing mappings still work
- **Clear stopping points** — Stick to HIGH priority, don't get pulled into MEDIUM/LOW scope creep
- **Data accuracy** — New mappings must be correct, not just present

</essential>

<boundaries>
## What's Out of Scope

- **Player prop markets** — Complex, need special handling (goals, shots, assists, bookings by player)
- **Platform-specific markets** — Markets that only exist on one competitor with no Betpawa equivalent
- **MEDIUM and LOW priority markets** — Strictly HIGH priority only for this phase
- **Major refactoring** — Can improve organization, but not a full mapping system rewrite

</boundaries>

<specifics>
## Specific Ideas

- **Error type priority:** NO_MATCHING_OUTCOMES first (closest to working), then UNKNOWN_MARKET, then UNKNOWN_PARAM_MARKET
- **Trust the audit ranking:** Work through frequency order from the prioritized list
- **Unmappable markets:** Handle case-by-case based on why they can't be mapped
- **Code organization:** Improve structure if needed, document complex mappings with comments
- **Verification:** Spot-check in UI during work, full audit re-run at phase end

</specifics>

<notes>
## Additional Context

**Audit baseline (Phase 43-01 results):**
- SportyBet: 47.3% mapping success (8,323/17,605 markets)
- Bet9ja: 36.1% mapping success (5,580/15,465 markets)
- 380 unique unmapped market types identified

**Key concerns raised:**
1. Breaking existing mappings — must verify existing mappings still work after changes
2. Scope creep — strict boundaries, clear stopping points between sub-phases
3. Data accuracy — each mapping verified individually, not assumed from patterns

**Sub-phase structure:**
| Sub-phase | Error Type | Focus |
|-----------|------------|-------|
| 44-01 | NO_MATCHING_OUTCOMES | Outcome alignment — markets we recognize but outcomes don't match |
| 44-02 | UNKNOWN_MARKET | New mappings — markets we don't recognize at all |
| 44-03 | UNKNOWN_PARAM_MARKET | Parameter handling — markets with parameterized variants |

</notes>

---

*Phase: 44-high-priority-market-mappings*
*Context gathered: 2026-02-02*
