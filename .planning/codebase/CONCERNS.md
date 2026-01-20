# Codebase Concerns

**Analysis Date:** 2026-01-20

## Tech Debt

**Large monolithic market mappings file:**
- Issue: 62,737 bytes of flat, repetitive market mapping data in single file
- File: `mapping_markets/src/mappings/market-ids.ts`
- Why: Rapid development, single source of truth approach
- Impact: Maintaining 111+ mappings in one file becomes unwieldy
- Fix approach: Consider splitting by market category or auto-generating from structured data

**Duplicate mapper logic across platforms:**
- Issue: Over/Under and Handicap mapping logic duplicated between mappers
- Files: `mapping_markets/src/mappers/bet9ja-to-betpawa.ts`, `mapping_markets/src/mappers/sportybet-to-betpawa.ts`
- Why: Each platform developed independently
- Impact: Bug fixes must be applied in multiple places, ~60% logic repeated
- Fix approach: Extract common mapping patterns into shared utility functions

**Detailed error versions duplicate main logic:**
- Issue: Each mapper has both simple and detailed versions with duplicated logic
- Files: `mapping_markets/src/mappers/bet9ja-to-betpawa.ts` (~200 LOC), `mapping_markets/src/mappers/sportybet-to-betpawa.ts` (~200 LOC)
- Why: Added detailed versions later without refactoring
- Impact: Changes must be made in two places per mapper
- Fix approach: Refactor to single implementation that always captures details, with simple wrapper

## Known Bugs

**No known bugs at time of analysis.**

## Security Considerations

**Hardcoded browser User-Agents:**
- Risk: User-Agents may become outdated, potentially affecting API access
- Files: `scraper/src/sportybet_scraper/config.py:13`, `scraper/src/betpawa_scraper/config.py:11`, `scraper/src/bet9ja_scraper/config.py:11`
- Current mitigation: Chrome User-Agent string is commonly accepted
- Recommendations: Document why this is necessary; consider making configurable

**Missing .env.example:**
- Risk: If credentials ever need to be added, no template exists
- File: Would need to be created at `scraper/.env.example`
- Current mitigation: No secrets currently needed
- Recommendations: Create placeholder .env.example for future extensibility

## Performance Bottlenecks

**O(n) market lookup:**
- Problem: Linear search through MARKET_MAPPINGS array for every lookup
- File: `mapping_markets/src/mappings/market-ids.ts`
- Measurement: n = 111 markets, repeated for each market in event
- Cause: Array.find() instead of indexed data structure
- Improvement path: Create Map/object indices for O(1) lookup by ID/key

**O(n*m) outcome mapping:**
- Problem: For each outcome, searches outcomeMapping array
- File: `mapping_markets/src/mappers/sportybet-to-betpawa.ts:192-196`
- Measurement: n = outcomes per market (2-30), m = outcome mappings (3-30)
- Cause: Array iteration for each outcome match
- Improvement path: Pre-index outcome mappings by source identifier

## Fragile Areas

**Market key format detection (Bet9ja):**
- File: `mapping_markets/src/mappers/bet9ja-to-betpawa.ts:156, 561`
- Why fragile: String-based detection of European vs Asian handicap (`includes("1X2HND")`)
- Common failures: New market key formats could be misclassified
- Safe modification: Add explicit market type flags in mapping data
- Test coverage: Covered by unit tests, but edge cases may exist

**Specifier parsing:**
- File: `mapping_markets/src/utils/specifier-parser.ts`
- Why fragile: Complex regex and parsing logic for Sportybet specifiers
- Common failures: Unexpected specifier formats
- Safe modification: Has ReDoS protection (length limits), add new formats carefully
- Test coverage: Good test coverage for known formats

## Scaling Limits

**Market mapping array size:**
- Current capacity: 111 markets, fast enough
- Limit: O(n) lookup becomes noticeable at 1000+ markets
- Symptoms at limit: Slight slowdown in bulk transformations
- Scaling path: Index data structures for O(1) lookup

## Dependencies at Risk

**Future TypeScript/Jest versions:**
- Risk: package.json specifies `^5.9.3` TypeScript, `^30.2.0` Jest (major versions)
- File: `mapping_markets/package.json`
- Impact: Breaking changes in major versions could require updates
- Migration plan: Pin to specific versions if stability issues arise

**Permissive Python dependency versions:**
- Risk: `>=0.27` httpx, `>=8.2` tenacity allow future breaking changes
- File: `scraper/pyproject.toml`
- Impact: Future pip install could pull incompatible version
- Migration plan: Add upper bounds (e.g., `httpx>=0.27,<1.0`)

## Missing Critical Features

**No unified pipeline orchestration:**
- Problem: Scrapers run independently, no unified workflow
- Current workaround: Manual CLI invocation or external scripting
- Blocks: Automated cross-platform comparison pipeline
- Implementation complexity: Medium (orchestration script or workflow tool)

## Test Coverage Gaps

**Scraper exception handling:**
- What's not tested: NetworkError, InvalidEventIdError scenarios in Python scrapers
- File: `scraper/src/*/client.py`
- Risk: Edge cases in error handling could fail silently
- Priority: Medium
- Difficulty to test: Requires mocking HTTP responses

**Missing response.json() error handling:**
- What's not tested: Invalid JSON responses from APIs
- Files: `scraper/src/betpawa_scraper/client.py:86`, `scraper/src/sportybet_scraper/client.py:80`
- Risk: JSONDecodeError crashes scraper instead of graceful error
- Priority: Medium
- Difficulty to test: Easy to add try/catch

**Input validation not enforced at runtime:**
- What's not tested: Runtime validation that inputs match expected types
- File: `mapping_markets/src/mappers/sportybet-to-betpawa.ts:144`
- Risk: API response changes could cause unexpected behavior
- Priority: Low (TypeScript provides compile-time safety)
- Difficulty to test: Type guards exist but not called by default

---

*Concerns audit: 2026-01-20*
*Update as issues are fixed or new ones discovered*
