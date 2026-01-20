# Coding Conventions

**Analysis Date:** 2026-01-20

## Naming Patterns

**Files:**
- TypeScript: kebab-case (`bet9ja-to-betpawa.ts`, `specifier-parser.ts`)
- Python: snake_case (`sportybet_scraper`, `logging_config.py`)
- Tests: `*.test.ts` co-located with source
- Integration tests: `*.integration.test.ts`

**Functions:**
- TypeScript: camelCase (`mapToBetpawa()`, `parseBet9jaKey()`, `findByBetpawaId()`)
- Python: snake_case (`create_client()`, `fetch_event()`, `from_dict()`)
- No special prefix for async functions

**Variables:**
- TypeScript: camelCase for variables
- TypeScript: UPPER_SNAKE_CASE for constants (`BET9JA_OVER_UNDER_KEYS`, `MAX_KEY_LENGTH`)
- Python: snake_case for variables
- Python: UPPER_SNAKE_CASE for constants (`BASE_URL`, `DEFAULT_TIMEOUT`, `MAX_RETRIES`)

**Types:**
- TypeScript interfaces: PascalCase, no I prefix (`SportybetMarket`, `MappedMarket`)
- TypeScript type aliases: PascalCase (`MappingResult`, `CompetitorInput`)
- TypeScript enums: PascalCase name, UPPER_SNAKE_CASE values (`MappingErrorCode.UNKNOWN_MARKET`)
- Python dataclasses: PascalCase (`Tournament`, `SportGroup`, `Sport`)

## Code Style

**TypeScript Formatting:**
- 2 spaces indentation
- Double quotes for strings
- Semicolons required
- Line length: ~80-100 characters

**Python Formatting:**
- 4 spaces indentation (PEP 8)
- Double quotes for strings
- No trailing commas in single-line structures
- Line length: ~80-100 characters

**Linting:**
- TypeScript: No ESLint/Prettier config committed (uses defaults)
- Python: No linting config committed (follows PEP 8)

## Import Organization

**TypeScript Order:**
1. External packages (none in this pure library)
2. Internal modules (`../types/`, `../mappings/`)
3. Relative imports (`./unified`)
4. Type imports (`import type { }`)

**Python Order:**
1. Standard library (`time`, `dataclasses`)
2. External packages (`httpx`, `click`, `tenacity`)
3. Internal modules (`sportybet_scraper.config`, `sportybet_scraper.exceptions`)

**Grouping:**
- Blank line between groups
- Alphabetical within groups (approximately)

## Error Handling

**TypeScript Patterns:**
- Return `MappingResult<T>` discriminated union for expected failures
- Never throw exceptions from mapper functions
- Use helper functions: `success()`, `failure()`, `createMappingError()`
- Include context in error objects (market ID, key, etc.)

**TypeScript Error Types:**
```typescript
MappingErrorCode.UNKNOWN_MARKET       // No mapping exists
MappingErrorCode.UNSUPPORTED_PLATFORM // Market not on Betpawa
MappingErrorCode.INVALID_SPECIFIER    // Unparseable specifier
MappingErrorCode.INVALID_ODDS         // Unparseable odds value
MappingErrorCode.INVALID_KEY_FORMAT   // Invalid Bet9ja key
```

**Python Patterns:**
- Custom exceptions extend base Exception
- Raise at client boundary for API/network errors
- Let tenacity handle retry-able errors
- Include context in exception messages

**Python Error Types:**
- `ApiError` - Generic API response error
- `InvalidEventIdError` - Bad event ID format
- `NetworkError` - Connection/timeout failures

## Logging

**TypeScript:**
- No logging in library (pure transformation)
- Errors returned as data, not logged

**Python:**
- Structured logging via `logging_config.py`
- Logger per module: `get_logger(__name__)`
- Levels: debug, info, warn, error
- CLI verbosity flag controls log level

## Comments

**When to Comment:**
- Explain business logic (market key formats, handicap semantics)
- Document non-obvious algorithms (specifier parsing)
- Explain "why" not "what"

**JSDoc/TSDoc (TypeScript):**
- Required for exported functions
- Use `@param`, `@returns`, `@example`, `@throws` tags
- Include usage examples in complex functions

**Docstrings (Python):**
- Module docstring at file start
- Function docstrings with `Args:`, `Returns:`, `Raises:` sections
- Follow PEP 257 conventions

**TODO Comments:**
- Minimal use in codebase
- Format: `// TODO: description`

## Function Design

**Size:**
- Keep functions focused (single responsibility)
- Extract helpers for complex logic
- Mappers are larger due to market-specific handling

**Parameters:**
- TypeScript: Use typed objects for complex params
- Python: Use type hints for all parameters
- Destructure in parameter list when appropriate

**Return Values:**
- TypeScript: Explicit returns, use `MappingResult<T>` for failures
- Python: Type hints for return types
- Return early for guard clauses

## Module Design

**TypeScript Exports:**
- Named exports preferred
- Barrel files (`index.ts`) re-export public API
- Internal helpers not exported from index

**Python Exports:**
- `__init__.py` defines package exports
- `__main__.py` enables `python -m` invocation
- CLI entry points in `pyproject.toml`

**Co-location:**
- Tests alongside source files
- Integration tests with `.integration.test.ts` suffix
- Each scraper is self-contained package

---

*Convention analysis: 2026-01-20*
*Update when patterns change*
