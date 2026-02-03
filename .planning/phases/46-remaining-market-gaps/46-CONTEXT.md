# Phase 46: Remaining Market Mapping Gaps - Context

**Gathered:** 2026-02-03
**Status:** Ready for research

<vision>
## How This Should Work

Investigate before committing to mappings. The phase starts with comprehensive research to understand what these unknown market types actually are:

1. **API sample analysis** — Fetch raw API responses for unknown market types and decode their structure
2. **Cross-platform comparison** — Check if these markets exist on multiple platforms under different names
3. **Existing code review** — Understand why current mapping logic fails for these specific markets

Only after investigation do we decide what to map. The goal is informed decisions, not blind mapping attempts.

</vision>

<essential>
## What Must Be Nailed

- **Mapping success rate gains** — Push SportyBet past 55% and Bet9ja past 50%
- **Understanding the gaps** — Know exactly what each unknown market type is, even if we don't map all of them
- **Prioritized action list** — Clear determination of which markets to map vs skip vs defer, based on investigation findings

All three outcomes matter equally — we need the gains, the understanding, and the prioritization.

</essential>

<boundaries>
## What's Out of Scope

- **Player props** — Skip player-specific markets (goal scorers, cards, etc.)
- **UNSUPPORTED_PLATFORM markets** — Don't try to map markets that BetPawa doesn't support
- **Multi/combo bet builders** — Skip bet builder and accumulator-only markets

Focus only on markets that can actually be mapped to BetPawa equivalents.

</boundaries>

<specifics>
## Specific Ideas

- **Mix of SQL and live API** — Use stored data (SQL queries) for occurrence counts and patterns; use live API sampling for understanding actual market structures
- **Similar methodology to Phase 43/45** — SQL-based audit approach has worked well for discovery

**Priority targets from Phase 45 audit:**
1. OUA (bet9ja) - 1,928 occurrences
2. CHANCEMIXOU/CHANCEMIX/CHANCEMIXN (bet9ja) - ~740 combined
3. 60180 (sportybet) - 464 occurrences - Early Goals O/U
4. NO_MATCHING_OUTCOMES fixes (818, HTFTOU, 551)
5. CAH/CAHH/CAH2 (bet9ja) - ~300 combined - Asian handicap variants

</specifics>

<notes>
## Additional Context

Building on Phase 45's success (+4.9% SportyBet, +4.4% Bet9ja). Current rates are 52.2% SportyBet and 40.5% Bet9ja — targets are 55%+ and 50%+ respectively.

383 unique unmapped market types remain, but most are UNSUPPORTED_PLATFORM or player props which are explicitly out of scope.

</notes>

---

*Phase: 46-remaining-market-gaps*
*Context gathered: 2026-02-03*
