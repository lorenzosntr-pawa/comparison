# Phase 1: Market Mapping Port - Research

**Researched:** 2025-01-20
**Domain:** Python/Pydantic port of TypeScript market mapping library
**Confidence:** HIGH

<research_summary>
## Summary

Researched patterns for porting a TypeScript library with discriminated unions, Result types, and 108 market mappings to Pythonic Pydantic v2 models.

The TypeScript library uses discriminated unions (`{ source: "sportybet"; data: SportybetInput } | { source: "bet9ja"; data: Bet9jaInput }`) and Result types (`{ success: true; data: T } | { success: false; error: E }`). Pydantic v2 natively supports discriminated unions with `Field(discriminator='...')` and `Literal` type discriminators, implemented in Rust for high performance.

For the 108 market mappings registry, use a list of Pydantic models with frozen config for immutability. The existing TypeScript structure maps cleanly to Python: interfaces → Pydantic BaseModel, enums → StrEnum, Sets → frozensets.

**Primary recommendation:** Use Pydantic v2 discriminated unions with `Literal` type discriminators. Model the market registry as a frozen list of Pydantic models. Use StrEnum for error codes. Standard Python exceptions for error handling (skip Result pattern).
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic | 2.10+ | Data validation and serialization | Native discriminated unions, Rust-powered validation, JSON serialization built-in |
| typing | stdlib | Type hints | `Literal`, `Union`, `Optional`, `TypedDict` |
| enum | stdlib | Enumerations | `StrEnum` for error codes (Python 3.11+) |
| re | stdlib | Regex parsing | Specifier and Bet9ja key parsing |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| typing_extensions | 4.0+ | Backports | If targeting Python <3.11 for StrEnum |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pydantic BaseModel | dataclasses | dataclasses lighter but no validation/serialization |
| Pydantic BaseModel | TypedDict | TypedDict for pure dicts, but loses validation |
| StrEnum | string literals | StrEnum gives autocomplete and type safety |

**Installation:**
```bash
pip install pydantic>=2.10
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```
src/market_mapping/
├── __init__.py              # Public API exports
├── types/
│   ├── __init__.py
│   ├── betpawa.py           # Betpawa API response types
│   ├── sportybet.py         # Sportybet API response types
│   ├── bet9ja.py            # Bet9ja types and key format
│   ├── normalized.py        # Platform-agnostic intermediate types
│   ├── mapped.py            # Output types (MappedMarket, MappedOutcome)
│   └── errors.py            # MappingError enum and exception
├── mappings/
│   ├── __init__.py
│   └── market_ids.py        # 108 market mappings registry
├── mappers/
│   ├── __init__.py
│   ├── sportybet.py         # Sportybet → Betpawa mapper
│   ├── bet9ja.py            # Bet9ja → Betpawa mapper
│   └── unified.py           # Multi-platform unified API
└── utils/
    ├── __init__.py
    ├── specifier_parser.py  # Parse Sportybet specifiers
    └── bet9ja_parser.py     # Parse Bet9ja key format
```

### Pattern 1: Pydantic Discriminated Union (Multi-Platform Input)
**What:** Type-safe union where Pydantic auto-selects the right model based on discriminator field
**When to use:** Multi-source input handling (SportyBet vs Bet9ja)
**Example:**
```python
from pydantic import BaseModel, Field
from typing import Literal, Union, Annotated

class SportybetInput(BaseModel):
    source: Literal["sportybet"] = "sportybet"
    market: SportybetMarket
    event: SportybetEvent

class Bet9jaInput(BaseModel):
    source: Literal["bet9ja"] = "bet9ja"
    odds: dict[str, str]  # Key-value format

CompetitorInput = Annotated[
    Union[SportybetInput, Bet9jaInput],
    Field(discriminator="source")
]

# Usage - Pydantic auto-selects correct model:
def map_to_betpawa(input_data: CompetitorInput) -> MappedMarket | None:
    if input_data.source == "sportybet":
        return map_sportybet(input_data.market, input_data.event)
    else:
        return map_bet9ja(input_data.odds)
```

### Pattern 2: Frozen Model for Market Registry
**What:** Immutable Pydantic models for the 108 market mappings
**When to use:** Static configuration data that shouldn't change at runtime
**Example:**
```python
from pydantic import BaseModel, ConfigDict

class OutcomeMapping(BaseModel):
    model_config = ConfigDict(frozen=True)

    canonical_id: str
    betpawa_name: str | None
    sportybet_desc: str | None
    bet9ja_suffix: str | None
    position: int

class MarketMapping(BaseModel):
    model_config = ConfigDict(frozen=True)

    canonical_id: str
    name: str
    betpawa_id: str | None
    sportybet_id: str | None
    bet9ja_key: str | None
    outcome_mapping: tuple[OutcomeMapping, ...]  # tuple for immutability

# Registry as module-level frozen data
MARKET_MAPPINGS: tuple[MarketMapping, ...] = (
    MarketMapping(
        canonical_id="1x2_ft",
        name="1X2 - Full Time",
        betpawa_id="3743",
        sportybet_id="1",
        bet9ja_key="S_1X2",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home", betpawa_name="1", sportybet_desc="Home", bet9ja_suffix="1", position=0),
            OutcomeMapping(canonical_id="draw", betpawa_name="X", sportybet_desc="Draw", bet9ja_suffix="X", position=1),
            OutcomeMapping(canonical_id="away", betpawa_name="2", sportybet_desc="Away", bet9ja_suffix="2", position=2),
        ),
    ),
    # ... 107 more mappings
)
```

### Pattern 3: StrEnum for Error Codes
**What:** String enum that can be used directly as string values
**When to use:** Error codes that need to be serializable and type-safe
**Example:**
```python
from enum import StrEnum

class MappingErrorCode(StrEnum):
    UNKNOWN_MARKET = "UNKNOWN_MARKET"
    UNSUPPORTED_PLATFORM = "UNSUPPORTED_PLATFORM"
    INVALID_SPECIFIER = "INVALID_SPECIFIER"
    UNKNOWN_PARAM_MARKET = "UNKNOWN_PARAM_MARKET"
    NO_MATCHING_OUTCOMES = "NO_MATCHING_OUTCOMES"
    INVALID_ODDS = "INVALID_ODDS"
    INVALID_KEY_FORMAT = "INVALID_KEY_FORMAT"

# Can be used directly as string:
error_code = MappingErrorCode.UNKNOWN_MARKET
print(error_code)  # "UNKNOWN_MARKET"
```

### Pattern 4: Lookup Functions with frozenset for O(1) Classification
**What:** Use frozenset for set-based market classification
**When to use:** Checking if a market ID belongs to a category (over/under, handicap, variant)
**Example:**
```python
OVER_UNDER_MARKET_IDS: frozenset[str] = frozenset({
    "18", "68", "90", "19", "20", "21", "70", "72", "76", "91", "92"
})

HANDICAP_MARKET_IDS: frozenset[str] = frozenset({
    "14", "16", "65", "66", "87", "88", "15", "17"
})

def is_over_under_market(sportybet_id: str) -> bool:
    return sportybet_id in OVER_UNDER_MARKET_IDS
```

### Anti-Patterns to Avoid
- **Using Pydantic v1 syntax:** v2 uses `model_config = ConfigDict(...)` not `class Config:`
- **Mutable registry:** Don't use `list` for market mappings; use `tuple` with `frozen=True`
- **Complex Result types:** Python convention is exceptions, not Result monads. Skip the TS Result pattern.
- **Bare Literal comparisons:** Always use `input_data.source == "sportybet"` not bare string comparisons
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Data validation | Custom validation functions | Pydantic validators | Pydantic handles edge cases, serialization, errors |
| JSON serialization | `json.dumps` with custom encoder | Pydantic `.model_dump_json()` | Handles nested models, enums, optional fields |
| Type discrimination | if/elif chains on dict keys | Pydantic discriminated unions | Type-safe, auto-validates, Rust-fast |
| Enum string conversion | Custom string enums | `StrEnum` (stdlib) | Native since Python 3.11, no .value needed |
| Immutable data | `@dataclass(frozen=True)` | Pydantic `ConfigDict(frozen=True)` | Gets validation + serialization + immutability |

**Key insight:** Pydantic v2's Rust core is ~17x faster than v1. Use Pydantic for everything data-shaped; don't reimplement validation logic.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Pydantic v1 vs v2 Syntax
**What goes wrong:** Code uses deprecated v1 syntax that fails silently or throws cryptic errors
**Why it happens:** Training data and old tutorials show v1 patterns
**How to avoid:** Always use v2 patterns:
- `model_config = ConfigDict(...)` not `class Config:`
- `model_dump()` not `.dict()`
- `model_validate()` not `.parse_obj()`
- `Field(discriminator=...)` not validator hacks
**Warning signs:** `DeprecationWarning` messages, unexpected validation behavior

### Pitfall 2: Mutable Default in Model Fields
**What goes wrong:** Shared mutable state between model instances
**Why it happens:** Using `list` or `dict` as default value
**How to avoid:** Use `Field(default_factory=list)` or immutable defaults like `tuple`
**Warning signs:** Tests pass individually but fail together

### Pitfall 3: Case-Sensitive String Matching
**What goes wrong:** Outcome mapping fails because "Home" != "home"
**Why it happens:** Bookmaker APIs inconsistent with casing
**How to avoid:** Always `.lower()` both sides when matching outcome descriptions
**Warning signs:** Missing outcomes that should match

### Pitfall 4: Regex Compilation in Hot Path
**What goes wrong:** Performance degrades when parsing many specifiers
**Why it happens:** `re.match(pattern, ...)` compiles pattern each call
**How to avoid:** Pre-compile patterns at module level: `SPECIFIER_PATTERN = re.compile(r"...")`
**Warning signs:** Profiler shows regex as bottleneck

### Pitfall 5: Optional Field Handling
**What goes wrong:** `None` values cause AttributeError or KeyError
**Why it happens:** Not handling null Betpawa/Sportybet IDs in mappings
**How to avoid:** Check `if mapping.betpawa_id is not None` before use
**Warning signs:** Random crashes on certain markets
</common_pitfalls>

<code_examples>
## Code Examples

### Pydantic Model for Mapped Market Output
```python
# Source: Pydantic v2 docs pattern
from pydantic import BaseModel, ConfigDict

class MappedOutcome(BaseModel):
    model_config = ConfigDict(frozen=True)

    betpawa_outcome_name: str
    sportybet_outcome_desc: str | None
    odds: float

class MappedHandicap(BaseModel):
    model_config = ConfigDict(frozen=True)

    home: float
    away: float

class MappedMarket(BaseModel):
    model_config = ConfigDict(frozen=True)

    betpawa_market_id: str
    betpawa_market_name: str
    sportybet_market_id: str | None
    line: float | None = None          # For Over/Under
    handicap: MappedHandicap | None = None  # For Handicap
    outcomes: tuple[MappedOutcome, ...]
```

### Specifier Parser
```python
# Source: Adapted from TypeScript implementation
import re
from dataclasses import dataclass

# Pre-compile for performance
SPECIFIER_PATTERN = re.compile(r"([a-z]+)=([^|]+)")

@dataclass(frozen=True)
class ParsedSpecifier:
    total: float | None = None
    hcp: str | None = None
    variant: str | None = None
    raw: str = ""

def parse_specifier(specifier: str | None) -> ParsedSpecifier:
    if not specifier or len(specifier) > 1000:  # ReDoS prevention
        return ParsedSpecifier()

    result = {"raw": specifier}
    for match in SPECIFIER_PATTERN.finditer(specifier):
        key, value = match.groups()
        if key == "total":
            try:
                result["total"] = float(value)
            except ValueError:
                pass
        elif key == "hcp":
            result["hcp"] = value
        elif key == "variant":
            result["variant"] = value

    return ParsedSpecifier(**result)
```

### Bet9ja Key Parser
```python
# Source: Adapted from TypeScript implementation
import re
from dataclasses import dataclass

BET9JA_KEY_PATTERN = re.compile(r"^S_([A-Z0-9_\-]+?)(?:@([^_]+))?_(.+)$")

@dataclass(frozen=True)
class ParsedBet9jaKey:
    market: str
    param: str | None
    outcome: str

def parse_bet9ja_key(key: str) -> ParsedBet9jaKey | None:
    match = BET9JA_KEY_PATTERN.match(key)
    if not match:
        return None

    market, param, outcome = match.groups()
    return ParsedBet9jaKey(market=market, param=param, outcome=outcome)

# Examples:
# parse_bet9ja_key("S_1X2_1") → ParsedBet9jaKey(market="1X2", param=None, outcome="1")
# parse_bet9ja_key("S_OU@2.5_O") → ParsedBet9jaKey(market="OU", param="2.5", outcome="O")
```

### Market Lookup Functions
```python
# Source: Standard Python dict-based lookup pattern
from functools import lru_cache

# Build lookup dicts at module load time for O(1) access
_BY_BETPAWA_ID: dict[str, MarketMapping] = {}
_BY_SPORTYBET_ID: dict[str, MarketMapping] = {}
_BY_CANONICAL_ID: dict[str, MarketMapping] = {}

def _build_lookups() -> None:
    for mapping in MARKET_MAPPINGS:
        _BY_CANONICAL_ID[mapping.canonical_id] = mapping
        if mapping.betpawa_id:
            _BY_BETPAWA_ID[mapping.betpawa_id] = mapping
        if mapping.sportybet_id:
            _BY_SPORTYBET_ID[mapping.sportybet_id] = mapping

_build_lookups()

def find_by_betpawa_id(market_id: str) -> MarketMapping | None:
    return _BY_BETPAWA_ID.get(market_id)

def find_by_sportybet_id(market_id: str) -> MarketMapping | None:
    return _BY_SPORTYBET_ID.get(market_id)

def find_by_canonical_id(canonical_id: str) -> MarketMapping | None:
    return _BY_CANONICAL_ID.get(canonical_id)
```
</code_examples>

<sota_updates>
## State of the Art (2024-2025)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pydantic v1 `class Config:` | Pydantic v2 `model_config = ConfigDict()` | June 2023 | Must use v2 syntax |
| `@validator` decorator | `@field_validator` decorator | Pydantic v2 | Different import path |
| `str` with validation | `StrEnum` (stdlib) | Python 3.11 | Native enum strings |
| `Optional[X]` | `X \| None` | Python 3.10+ | Cleaner syntax |

**New tools/patterns to consider:**
- **Pydantic v2.10+ `model_config`:** Use `ConfigDict(frozen=True)` for immutable models
- **Python 3.11 StrEnum:** Native string enums without `.value` access

**Deprecated/outdated:**
- **Pydantic v1 patterns:** `class Config:`, `.dict()`, `.parse_obj()` — all deprecated
- **typing_extensions for Literal:** Now in stdlib `typing` module
</sota_updates>

<open_questions>
## Open Questions

1. **Error handling strategy**
   - What we know: TypeScript uses Result pattern, Python convention is exceptions
   - What's unclear: Should we preserve detailed error context or use simple exceptions?
   - Recommendation: Use custom `MappingError` exception with error code and context, skip Result pattern

2. **Market registry storage format**
   - What we know: TypeScript uses inline array, Python could use tuple or load from JSON
   - What's unclear: Performance tradeoff of 108 inline model definitions vs JSON load
   - Recommendation: Inline tuple for type safety and IDE autocomplete; JSON only if registry becomes external config
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- [Pydantic Unions Documentation](https://docs.pydantic.dev/latest/concepts/unions/) - discriminated unions syntax and patterns
- [Pydantic Performance Guide](https://docs.pydantic.dev/latest/concepts/performance/) - v2 is 17x faster than v1
- [Python Enum HOWTO](https://docs.python.org/3/howto/enum.html) - StrEnum patterns

### Secondary (MEDIUM confidence)
- [Pydantic v2 Best Practices](https://medium.com/algomart/working-with-pydantic-v2-the-best-practices-i-wish-i-had-known-earlier-83da3aa4d17a) - verified against official docs
- [StrEnum Introduction](https://sandeepnarayankv.medium.com/python-3-11s-game-changing-strenum-and-intenum-say-goodbye-to-value-forever-778bcf5b8034) - verified against stdlib docs

### Tertiary (LOW confidence - needs validation)
- None - all findings verified against official sources
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: Pydantic v2, Python 3.11+ typing
- Ecosystem: stdlib typing, enum, re
- Patterns: Discriminated unions, frozen models, lookup registries
- Pitfalls: v1/v2 migration, mutable defaults, case sensitivity

**Confidence breakdown:**
- Standard stack: HIGH - Pydantic v2 is well-documented
- Architecture: HIGH - patterns from official docs
- Pitfalls: HIGH - common migration issues documented
- Code examples: HIGH - verified against Pydantic v2 docs

**Research date:** 2025-01-20
**Valid until:** 2025-02-20 (30 days - Pydantic ecosystem stable)
</metadata>

---

*Phase: 01-market-mapping-port*
*Research completed: 2025-01-20*
*Ready for planning: yes*
