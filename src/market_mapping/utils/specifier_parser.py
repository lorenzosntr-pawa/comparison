"""Specifier Parser Utility.

Parses Sportybet specifier strings into structured data for parameterized markets.
Sportybet uses specifiers like "total=2.5" for Over/Under lines and "hcp=0:1" for handicaps.

Specifier formats:
- Simple: "total=2.5"
- Compound: "minsnr=10|total=1.5"
"""

from dataclasses import dataclass
from typing import Literal


# Maximum specifier length to prevent ReDoS attacks
MAX_SPECIFIER_LENGTH = 1000


@dataclass(frozen=True)
class ParsedHandicap:
    """Parsed handicap data structure.

    Attributes:
        type: Handicap type - 'european' for X:Y format, 'asian' for single value.
        home: Home team handicap value.
        away: Away team handicap value (derived: opposite of home for Asian).
        raw: Original hcp value string for traceability.
    """

    type: Literal["european", "asian"]
    home: float
    away: float
    raw: str


@dataclass(frozen=True)
class ParsedSpecifier:
    """Parsed specifier data structure.

    Attributes:
        raw: Original specifier string for traceability.
        total: Total/line value for Over/Under markets (e.g., 2.5).
        hcp: Parsed handicap for handicap markets.
        variant: Variant identifier (e.g., "sr:exact_goals:2+").
        goalnr: Goal number for multi-goal markets.
        score: Score specifier for correct score markets.
    """

    raw: str
    total: float | None = None
    hcp: ParsedHandicap | None = None
    variant: str | None = None
    goalnr: int | None = None
    score: str | None = None


def _parse_handicap_value(value: str) -> ParsedHandicap | None:
    """Parse a handicap value string into structured data.

    Handles two formats:
    - European (3-way): "X:Y" where X is home goals, Y is away goals
      - hcp=0:1 means away starts with +1, so home=-1, away=+1
      - hcp=2:0 means home starts with +2, so home=+2, away=-2
    - Asian (2-way): single number like "-0.5" or "1.5"
      - Value is home handicap, away is opposite

    Edge cases handled:
    - Empty values or just whitespace -> None
    - Missing value on one side (":1", "1:") -> None
    - Just colon with no values (":") -> None
    - NaN/Infinity values -> None

    Args:
        value: The handicap value (e.g., "0:1", "-0.5")

    Returns:
        ParsedHandicap or None if invalid.
    """
    if not value or value.strip() == "":
        return None

    trimmed = value.strip()

    # Check for European format (contains colon)
    if ":" in trimmed:
        parts = trimmed.split(":")

        # Handle edge cases: ":", ":1", "1:", multiple colons
        if len(parts) != 2:
            return None

        home_str, away_str = parts

        # Handle missing values: ":1" or "1:" or ":"
        if home_str.strip() == "" or away_str.strip() == "":
            return None

        try:
            home_goals = float(home_str)
            away_goals = float(away_str)
        except ValueError:
            return None

        # Reject Infinity values
        if not (
            home_goals != float("inf")
            and home_goals != float("-inf")
            and away_goals != float("inf")
            and away_goals != float("-inf")
        ):
            return None

        # European handicap: home handicap = homeGoals - awayGoals
        # e.g., 0:1 means home=-1, away=+1 (away starts with advantage)
        # e.g., 2:0 means home=+2, away=-2 (home starts with advantage)
        return ParsedHandicap(
            type="european",
            home=home_goals - away_goals,
            away=away_goals - home_goals,
            raw=trimmed,
        )

    # Asian format: single number
    try:
        home_hcp = float(trimmed)
    except ValueError:
        return None

    # Reject Infinity values
    if home_hcp == float("inf") or home_hcp == float("-inf"):
        return None

    return ParsedHandicap(
        type="asian",
        home=home_hcp,
        away=-home_hcp,
        raw=trimmed,
    )


def parse_specifier(specifier: str | None) -> ParsedSpecifier | None:
    """Parse a Sportybet specifier string into structured data.

    Args:
        specifier: The specifier string (e.g., "total=2.5", "hcp=0:1")

    Returns:
        ParsedSpecifier object with extracted values, or None if invalid/empty.

    Edge cases handled:
    - None, or empty specifiers -> None
    - Extra whitespace in compound parts -> trimmed
    - Empty parts (e.g., "total=|hcp=1") -> skipped
    - Infinity/-Infinity numeric values -> ignored
    - Extremely long specifiers (>1000 chars) -> None (ReDoS prevention)

    Examples:
        >>> parse_specifier("total=2.5")
        ParsedSpecifier(raw='total=2.5', total=2.5, ...)

        >>> parse_specifier("minsnr=10|total=1.5")
        ParsedSpecifier(raw='minsnr=10|total=1.5', total=1.5, ...)

        >>> parse_specifier(None)
        None
    """
    # Return None for empty or None specifiers
    if not specifier or specifier.strip() == "":
        return None

    # Guard against extremely long specifiers to prevent ReDoS
    if len(specifier) > MAX_SPECIFIER_LENGTH:
        return None

    # Initialize result values
    total: float | None = None
    hcp: ParsedHandicap | None = None
    variant: str | None = None
    goalnr: int | None = None
    score: str | None = None

    # Split on "|" for compound specifiers (e.g., "minsnr=10|total=1.5")
    parts = specifier.split("|")

    for part in parts:
        # Skip empty parts (handles cases like "total=|hcp=1")
        trimmed_part = part.strip()
        if trimmed_part == "":
            continue

        # Split on "=" to get key-value pairs
        eq_split = trimmed_part.split("=", 1)
        if len(eq_split) != 2:
            continue

        key, value = eq_split

        if not key or value is None:
            continue

        trimmed_key = key.strip().lower()
        trimmed_value = value.strip()

        # Skip empty keys or values
        if trimmed_key == "" or trimmed_value == "":
            continue

        if trimmed_key == "total":
            # Parse as number for Over/Under lines
            try:
                num_value = float(trimmed_value)
                # Reject Infinity values
                if num_value != float("inf") and num_value != float("-inf"):
                    total = num_value
            except ValueError:
                pass

        elif trimmed_key == "hcp":
            # Parse handicap value into structured format
            parsed_hcp = _parse_handicap_value(trimmed_value)
            if parsed_hcp:
                hcp = parsed_hcp

        elif trimmed_key == "variant":
            # Store variant identifier (e.g., "sr:exact_goals:2+")
            variant = trimmed_value

        elif trimmed_key == "goalnr":
            # Parse goal number
            try:
                goalnr = int(trimmed_value)
            except ValueError:
                pass

        elif trimmed_key == "score":
            # Store score specifier
            score = trimmed_value

    return ParsedSpecifier(
        raw=specifier,
        total=total,
        hcp=hcp,
        variant=variant,
        goalnr=goalnr,
        score=score,
    )
