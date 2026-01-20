# Phase 1: Market Mapping Port - Context

**Gathered:** 2025-01-20
**Status:** Ready for planning

<vision>
## How This Should Work

A Pythonic redesign of the existing TypeScript market mapping library. Rather than a literal translation, adapt the concepts to Python idioms — use Pydantic models for validated, typed structures that are ready for API serialization.

The library takes raw market data from each bookmaker (SportyBet, BetPawa, Bet9ja) and transforms it into a unified format. Each bookmaker has different naming conventions and data structures, and this library normalizes everything.

</vision>

<essential>
## What Must Be Nailed

- **Complete coverage** — All 111+ markets from the TypeScript library must be mapped correctly. No gaps, no missing markets. This is the foundation everything else builds on.

</essential>

<boundaries>
## What's Out of Scope

- Database integration — that's Phase 2
- API endpoints — no FastAPI routes yet
- Keep it pure library code with no infrastructure concerns

</boundaries>

<specifics>
## Specific Ideas

No specific requirements — open to standard Pythonic approaches for error handling and structure. The TypeScript Result pattern doesn't need to be preserved; Python exceptions or standard error handling is fine.

</specifics>

<notes>
## Additional Context

The existing TypeScript library is a zero-dependency implementation with discriminated unions. The Python version should leverage Pydantic's strengths: validation, serialization, and type safety through dataclass-like models.

</notes>

---

*Phase: 01-market-mapping-port*
*Context gathered: 2025-01-20*
