# Testing Patterns

**Analysis Date:** 2026-01-20

## Test Framework

**TypeScript (mapping_markets):**
- Runner: Jest 30.2.0
- Config: `mapping_markets/jest.config.js`
- TypeScript support: ts-jest 29.4.6 preset

**Python (scraper):**
- No automated test framework
- Manual testing via CLI commands
- `test-connection` command for connectivity verification

**Run Commands:**
```bash
# TypeScript
cd mapping_markets
npm test                              # Run all tests
npm test -- --watch                   # Watch mode
npm test -- path/to/file.test.ts     # Single file

# Python (manual)
sportybet-scraper test-connection    # Verify API connectivity
betpawa-scraper test-connection
bet9ja-scraper test-connection
```

## Test File Organization

**Location:**
- `*.test.ts` co-located with source files
- `*.integration.test.ts` for integration tests
- No separate tests/ directory

**Naming:**
- Unit tests: `{module-name}.test.ts`
- Integration tests: `{module-name}.integration.test.ts`

**Structure:**
```
mapping_markets/src/
├── mappers/
│   ├── unified.ts
│   ├── unified.test.ts
│   ├── sportybet-to-betpawa.ts
│   ├── sportybet-to-betpawa.test.ts
│   ├── sportybet-to-betpawa.integration.test.ts
│   ├── bet9ja-to-betpawa.ts
│   ├── bet9ja-to-betpawa.test.ts
│   ├── bet9ja-to-betpawa.integration.test.ts
│   └── cross-platform.integration.test.ts
├── utils/
│   ├── specifier-parser.ts
│   ├── specifier-parser.test.ts
│   ├── bet9ja-parser.ts
│   ├── bet9ja-parser.test.ts
│   └── validate-input.test.ts
├── types/
│   └── errors.test.ts
└── mappings/
    ├── market-ids.ts
    └── market-ids.test.ts
```

**Test file count:** 13 test files

## Test Structure

**Suite Organization:**
```typescript
import { describe, it, expect, beforeEach } from '@jest/globals';

describe('ModuleName', () => {
  describe('functionName', () => {
    it('should handle success case', () => {
      // arrange
      const input = createTestInput();

      // act
      const result = functionName(input);

      // assert
      expect(result).toEqual(expectedOutput);
    });

    it('should return error for invalid input', () => {
      const result = functionNameDetailed(invalidInput);
      expect(result.success).toBe(false);
      expect(result.error.code).toBe(MappingErrorCode.INVALID_KEY_FORMAT);
    });
  });
});
```

**Patterns:**
- `describe()` blocks for category grouping
- `it()` statements test individual scenarios
- Arrange/act/assert pattern
- Error code assertions for failure cases

## Mocking

**Framework:**
- Jest built-in mocking
- Not heavily used (pure functions don't need mocks)

**Patterns:**
- Integration tests load real JSON files instead of mocking
- No external service mocking needed (library is pure transformation)

**What to Mock:**
- Not applicable (library has no external dependencies)

**What NOT to Mock:**
- Internal functions (test through public API)
- Type definitions

## Fixtures and Factories

**Test Data:**
```typescript
// Inline test data in test files
const sportybetMarket: SportybetMarket = {
  id: "1",
  desc: "1X2",
  specifier: "",
  outcomes: [
    { id: "1", desc: "Home", odds: "1.85", isActive: 1 },
    { id: "2", desc: "Draw", odds: "3.40", isActive: 1 },
    { id: "3", desc: "Away", odds: "4.20", isActive: 1 },
  ],
};
```

**Integration Test Data:**
```typescript
// Load real API responses
function loadBet9jaJson(filename: string) {
  const filePath = path.join(__dirname, '../../jsons_examples/bet9ja', filename);
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
}

function getBet9jaFiles(): string[] {
  const dir = path.join(__dirname, '../../jsons_examples/bet9ja');
  return fs.readdirSync(dir).filter(f => f.endsWith('.json'));
}
```

**Location:**
- `mapping_markets/jsons_examples/sportybet/Football/` - SportyBet samples
- `mapping_markets/jsons_examples/betpawa/Football/` - BetPawa samples
- `mapping_markets/jsons_examples/bet9ja/` - Bet9ja samples

## Coverage

**Requirements:**
- No enforced coverage target
- Focus on critical paths (mappers, parsers)

**Configuration:**
- Jest built-in coverage
- No specific configuration in jest.config.js

**View Coverage:**
```bash
npm test -- --coverage
```

## Test Types

**Unit Tests:**
- Test single function in isolation
- Inline test data
- Fast execution (<100ms per test)
- Examples: `bet9ja-parser.test.ts`, `specifier-parser.test.ts`

**Integration Tests:**
- Test multiple modules together
- Load real JSON fixtures
- Test end-to-end mapping pipeline
- Examples: `bet9ja-to-betpawa.integration.test.ts`, `cross-platform.integration.test.ts`

**E2E Tests:**
- Not present (library is consumed by other applications)
- CLI scrapers tested manually

## Common Patterns

**Simple Market Testing:**
```typescript
it('should map 1X2 market', () => {
  const result = mapSportybetToBetpawa(market1X2);
  expect(result).not.toBeNull();
  expect(result?.betpawaMarketId).toBe('3743');
  expect(result?.betpawaMarketName).toBe('1X2 - Full Time');
});
```

**Parameterized Market Testing:**
```typescript
it('should map Over/Under with line', () => {
  const result = mapBet9jaToBetpawa('S_OU@2.5_O', '1.85');
  expect(result).not.toBeNull();
  expect(result?.betpawaMarketId).toBe('3744');
  expect(result?.outcomes[0].betpawaName).toBe('Over 2.5');
});
```

**Error Testing:**
```typescript
it('should return UNKNOWN_MARKET for unmapped market', () => {
  const result = mapBet9jaToBetpawaDetailed('S_UNKNOWN_1', '1.50');
  expect(result.success).toBe(false);
  expect(result.error.code).toBe(MappingErrorCode.UNKNOWN_MARKET);
});
```

**Detailed Result Testing:**
```typescript
it('should include context in error', () => {
  const result = mapBet9jaToBetpawaDetailed('S_INVALID', '1.50');
  expect(result.success).toBe(false);
  expect(result.error.context).toHaveProperty('key', 'S_INVALID');
});
```

---

*Testing analysis: 2026-01-20*
*Update when test patterns change*
